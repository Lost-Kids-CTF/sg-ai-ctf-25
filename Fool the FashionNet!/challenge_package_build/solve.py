# solve.py

import torch
import torch.nn as nn
import torchvision.transforms as T
from PIL import Image
import numpy as np

# Import utilities from the challenge package
from model import SmallFashionCNN
from utils import linf, ssim_01

# --- Configuration ---
MODEL_PATH = "model.pt"
IMAGE_PATH = "seed.png"
SSIM_THRESHOLD = 0.85
LINF_THRESHOLD = 0.08

# We will test a range of epsilon values to find one that works.
# This makes the solution robust to small changes.
EPSILON_CANDIDATES = np.arange(0.045, 0.055, 0.001)

# --- Define class names for Fashion-MNIST for clarity ---
FASHION_MNIST_CLASSES = {
    0: 'T-shirt/top', 1: 'Trouser', 2: 'Pullover', 3: 'Dress', 4: 'Coat',
    5: 'Sandal', 6: 'Shirt', 7: 'Sneaker', 8: 'Bag', 9: 'Ankle boot'
}


def solve():
    """
    Generates the adversarial perturbation delta.npy by searching for a valid epsilon.
    """
    # --- 1. Load Model ---
    print(f"Loading model from {MODEL_PATH}...")
    model = SmallFashionCNN(num_classes=10)
    model.load_state_dict(torch.load(MODEL_PATH)['model_state'])
    model.eval()
    print("Model loaded successfully.")

    # --- 2. Load and Preprocess Image ---
    print(f"Loading and preprocessing image from {IMAGE_PATH}...")
    transform = T.ToTensor()
    image_pil = Image.open(IMAGE_PATH).convert("L")
    original_image_tensor = transform(image_pil).unsqueeze(0)

    # --- 3. Determine Original Prediction ---
    with torch.no_grad():
        original_output = model(original_image_tensor)
        original_pred_idx = torch.max(original_output, 1)[1]
        original_label = original_pred_idx.item()

    print("-" * 30)
    print(
        f"Original Prediction: Class {original_label} ({FASHION_MNIST_CLASSES[original_label]})") # type: ignore
    print("-" * 30)

    # --- 4. Iteratively Search for the best EPSILON ---
    print("Searching for the best EPSILON value...")
    solution_found = False

    for epsilon in EPSILON_CANDIDATES:
        print(f"\n--- Trying EPSILON = {epsilon:.4f} ---")

        # We need to re-enable grad on a fresh tensor for each loop iteration
        img_for_attack = original_image_tensor.clone().detach().requires_grad_(True)

        # Perform the FGSM Attack
        output = model(img_for_attack)
        loss = nn.CrossEntropyLoss()(output, original_pred_idx)
        model.zero_grad()
        loss.backward()

        signed_gradient = torch.sign(img_for_attack.grad.data) # type: ignore
        adversarial_image_tensor = torch.clamp(
            img_for_attack + epsilon * signed_gradient, 0, 1) # type: ignore

        delta_tensor = adversarial_image_tensor - original_image_tensor

        # Verify the attack's success and constraints
        with torch.no_grad():
            adv_output = model(adversarial_image_tensor)
            adversarial_label = torch.max(adv_output, 1)[1].item()

        original_image_np = original_image_tensor.squeeze().cpu().numpy()
        adversarial_image_np = adversarial_image_tensor.squeeze().detach().cpu().numpy()
        delta_np = delta_tensor.squeeze(0).detach().cpu().numpy()

        linf_norm, linf_valid = linf(delta_np, eps=LINF_THRESHOLD)
        ssim_score = ssim_01(original_image_np, adversarial_image_np)
        ssim_valid = ssim_score >= SSIM_THRESHOLD
        label_flipped = adversarial_label != original_label

        print(
            f"[L∞ Norm]: {linf_norm:.6f} <= {LINF_THRESHOLD} -> {'✅ VALID' if linf_valid else '❌ INVALID'}")
        print(
            f"[SSIM Score]: {ssim_score:.4f} >= {SSIM_THRESHOLD} -> {'✅ VALID' if ssim_valid else '❌ INVALID'}")
        print(
            f"[Label Flip]: {original_label} -> {adversarial_label} -> {'✅ VALID' if label_flipped else '❌ INVALID'}")

        if linf_valid and ssim_valid and label_flipped:
            solution_found = True
            print("-" * 30)
            print(
                f"✅ Success! Found a valid solution with EPSILON = {epsilon:.4f}")

            # Save the successful delta with the correct shape and dtype
            output_filename = 'delta.npy'
            delta_to_save = delta_np.reshape(1, 28, 28).astype(np.float32)
            np.save(output_filename, delta_to_save)
            print(
                f"Perturbation saved to '{output_filename}'. You can now submit this file.")
            break

    if not solution_found:
        print("\n❌ Failure. Could not find a suitable EPSILON in the given range.")


if __name__ == "__main__":
    solve()
