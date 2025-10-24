#!/usr/bin/env python3
"""
solve.py
Usage: python solve.py

This will:
 - load kv_cache.pt produced by gen.py
 - load the same model/tokenizer used by gen.py:
     "stabilityai/stablelm-3b-4e1t" with revision "fa4a6a9"
 - for each token position 0..T-1, try candidate tokens,
   compute the model's layer-0 'k' for that token, and compare
   cosine similarity to the saved K_rot for that position.
 - prints the best match and top-k options.

Notes:
 - Requires network to download the model (~several GB) unless cached locally.
 - GPU highly recommended. On CPU this will be slow.
"""

import torch
import math
from pathlib import Path
from transformers import AutoTokenizer, AutoModelForCausalLM, DynamicCache
from tqdm import tqdm
import numpy as np

KV_PATH = Path("kv_cache.pt")
CKPT = "stabilityai/stablelm-3b-4e1t"
REV = "fa4a6a9"
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
PRINT_TOPK = 5

# candidate characters to filter irrelevant tokens from the vocabulary
import string
candidates = list(string.ascii_letters + string.digits + "_" + "@" + "!" + "{" + "}")

def load_cache():
    data = torch.load(KV_PATH, map_location="cpu")
    K_rot = data["K_rot"]          # [H, T, Dh]
    T = int(data["T"])
    H = int(data["H"])
    Dh = int(data["Dh"])
    print(f"Loaded kv_cache: T={T}, H={H}, Dh={Dh}, K_rot shape {tuple(K_rot.shape)}", flush=True)
    return K_rot, T, H, Dh

def get_layer0_k_for_input(model, ids):
    # run model and return layer-0 key (k0)
    with torch.no_grad():
        out = model(input_ids=ids.to(DEVICE), use_cache=True, return_dict=True)
    # out.past_key_values is a tuple of length num_layers, each is (k, v)
    # k shape: (batch, heads, seq_len, head_dim)
    k0, v0 = out.past_key_values[0]
    # k0 shape (batch, heads, seq_len, head_dim)
    # take the last token's k (seq_len-1)
    k_last = k0[:, :, -1, :].squeeze(0).detach().cpu()  # shape [H, Dh]
    return k_last  # rotated keys as in gen.py

def cosine_sim(a, b):
    # a,b numpy arrays vectors
    a = a.ravel()
    b = b.ravel()
    na = np.linalg.norm(a)
    nb = np.linalg.norm(b)
    if na==0 or nb==0:
        return -1.0
    return float(np.dot(a, b) / (na*nb))

K_rot, T, H, Dh = load_cache()
# flatten token vectors for distance computations
K_rot_np = K_rot.numpy()  # shape [H, T, Dh]
K_rot_flat = K_rot_np.transpose(1,0,2).reshape(T, H*Dh)  # [T, H*Dh]

print("Loading tokenizer and model (this will download weights if not cached)...", flush=True)
tok = AutoTokenizer.from_pretrained(CKPT, revision=REV, use_fast=True)
model = AutoModelForCausalLM.from_pretrained(CKPT, revision=REV).to(DEVICE).eval()

discovered_tokens = []
discovered_token_strs = []

prefix_ids = []
prefix_tokens = []

current_prefix_ids = list(prefix_ids)
current_prefix_token_strs = list(prefix_tokens)

start_pos = len(current_prefix_ids)
print(f"Starting from position {start_pos} (0-based). Will recover positions {start_pos}..{T-1}", flush=True)

# We'll reconstruct the prompt greedily.
for pos in range(start_pos, T):
    print(f"\nRecovering token position {pos} (token #{pos+1}/{T})", flush=True)

    # ====== 1. Prepare the vocab list ======
    # vocab_items = list(tok.get_vocab().items()) # filter out irrelevant tokens
    vocab_items = [(t,i) for t,i in tok.get_vocab().items() if all(c in candidates for c in t)]
    vocab_ids = torch.tensor([vid for _, vid in vocab_items], dtype=torch.long, device=DEVICE)
    batch_size = 512  # adjust depending on your GPU memory
    sims_all = []

    # ====== 2. Run batches ======
    with torch.no_grad():
        for i in tqdm(range(0, len(vocab_ids), batch_size), desc="batching vocab", leave=False):
            batch_ids = vocab_ids[i:i+batch_size]

            # prefix + each candidate token
            prefix = torch.tensor(current_prefix_ids, dtype=torch.long, device=DEVICE)
            input_batch = torch.cat([
                prefix.repeat(batch_ids.shape[0], 1),
                batch_ids.unsqueeze(1)
            ], dim=1)  # shape [batch, len(prefix)+1]

            out = model(input_ids=input_batch, use_cache=True, return_dict=True)
            k0, v0 = out.past_key_values[0]  # k0 shape [batch, heads, seq_len, head_dim]
            k_last = k0[:, :, -1, :]  # [batch, H, Dh]

            # flatten to [batch, H*Dh]
            k_flat = k_last.reshape(batch_ids.shape[0], -1)

            # normalize for cosine
            k_norm = torch.nn.functional.normalize(k_flat, p=2, dim=1)
            target = torch.tensor(K_rot_flat[pos], device=DEVICE, dtype=k_norm.dtype)
            target_norm = torch.nn.functional.normalize(target, p=2, dim=0)

            sims = (k_norm @ target_norm).detach().cpu()  # [batch]
            sims_all.append(sims)

    sims_all = torch.cat(sims_all)
    sims_np = sims_all.numpy()
    topk_idx = sims_np.argsort()[::-1][:PRINT_TOPK]

    print(f"Top {PRINT_TOPK} candidates for position {pos}:", flush=True)
    for rank, idx in enumerate(topk_idx):
        token_str, token_id = vocab_items[idx]
        print(f"  {rank+1:>2}. {repr(token_str):<15} id={token_id:<6} cos={sims_np[idx]:.4f}")

    best_idx = topk_idx[0]
    best_token_str, best_token_id = vocab_items[best_idx]
    print(f"Best match: {best_token_str!r}  (id={best_token_id})", flush=True)

    # Update prefix
    current_prefix_ids.append(best_token_id)
    current_prefix_token_strs.append(best_token_str)

recovered = tok.decode(current_prefix_ids, clean_up_tokenization_spaces=False)
print("\nRecovered token strings (by tokenizer decode):", flush=True)
print(recovered, flush=True)
print("Recovered token-by-token:", current_prefix_token_strs, flush=True)