import pandas as pd
import requests
import time
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

# --- Configuration ---
# Use the environment variable for the API URL if it exists, otherwise use the default.
API_URL = os.environ.get("API_URL", "http://advertext-tdh9dv.aictf.sg:7000")
TEAM_NAME = "toilet"
DATASET_PATH = "dataset.csv"
MAX_WORKERS = 10 # Number of parallel threads to run. Adjust based on your connection.

# A prioritized list of words to try for perturbations.
# Negations and strong sentiment words are most likely to work.
NEGATION_WORDS = ['not', 'no', 'never']
POSITIVE_WORDS = ['good', 'great', 'amazing', 'excellent', 'brilliant']
NEGATIVE_WORDS = ['bad', 'terrible', 'awful', 'horrible', 'poor']

ATTACK_WORDS = NEGATION_WORDS + POSITIVE_WORDS + NEGATIVE_WORDS

# --- API Communication ---

# Use a single session object for all threads for efficiency
session = requests.Session()

def query_sentiment(sentence):
    """Queries the server to get the sentiment of a sentence."""
    try:
        response = session.post(f"{API_URL}/query", json={"sentence": sentence}, timeout=5)
        response.raise_for_status()
        data = response.json()
        if data.get("valid"):
            return data["scores"]["label"]
    except requests.exceptions.RequestException as e:
        # Suppress error printing for speed, but you can re-enable for debugging
        # print(f"  [!] API query error: {e}")
        pass
    return None

def submit_adversarial(sentence_id, adversarial_sentence):
    """Submits the adversarial sentence to the server."""
    try:
        payload = {
            "id": str(sentence_id),
            "adv": adversarial_sentence,
            "user": TEAM_NAME
        }
        response = session.post(f"{API_URL}/submit", json=payload, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException:
        return None

# --- Adversarial Logic ---

def generate_candidates_prioritized(words, original_label):
    """
    Generates candidate sentences in a prioritized order.
    This greedy approach tries the most likely flips first.
    """
    
    # --- Priority 1: Insert negations ---
    for i in range(len(words) + 1):
        for neg_word in NEGATION_WORDS:
            yield " ".join(words[:i] + [neg_word] + words[i:])

    # --- Priority 2: Replace existing words with strong opposites ---
    target_attack_words = NEGATIVE_WORDS if original_label == "POSITIVE" else POSITIVE_WORDS
    for i, word in enumerate(words):
        # Don't replace a word with itself
        if word in target_attack_words:
            continue
        for new_word in target_attack_words:
            yield " ".join(words[:i] + [new_word] + words[i+1:])

    # --- Priority 3: Other insertions, replacements, and deletions ---
    for i, word in enumerate(words):
        # Replacements with any attack word
        for new_word in ATTACK_WORDS:
             if new_word != word:
                yield " ".join(words[:i] + [new_word] + words[i+1:])
    
    # Insertions of any attack word
    for i in range(len(words) + 1):
        for new_word in ATTACK_WORDS:
            if new_word not in NEGATION_WORDS: # Avoid re-trying negations
                yield " ".join(words[:i] + [new_word] + words[i:])

    # Deletions (lowest priority)
    if len(words) > 1:
        for i in range(len(words)):
            yield " ".join(words[:i] + words[i+1:])


def solve_sentence(sentence_id, original_sentence):
    """
    Attempts to find a 1-edit adversarial example for a single sentence.
    This is now a greedy function that returns the first success.
    """
    original_label = query_sentiment(original_sentence)
    if not original_label:
        return f"ID #{sentence_id}: Could not get original label. Skipping."

    target_label = "POSITIVE" if original_label == "NEGATIVE" else "NEGATIVE"
    
    words = original_sentence.split()
    tried_sentences = {original_sentence}

    # Greedily check all prioritized 1-edit candidates
    for candidate in generate_candidates_prioritized(words, original_label):
        if candidate in tried_sentences:
            continue
        
        tried_sentences.add(candidate)
        
        candidate_label = query_sentiment(candidate)
        
        if candidate_label == target_label:
            result = submit_adversarial(sentence_id, candidate)
            if result and result.get('success'):
                success_msg = (
                    f"ID #{sentence_id}: SUCCESS!\n"
                    f"  Original ({original_label}): '{original_sentence}'\n"
                    f"  Adversary ({target_label}): '{candidate}'\n"
                    f"  Solved: {result.get('solved')}, Rate: {result.get('current_success_rate')}"
                )
                if result.get("flag"):
                    success_msg += f"\n\n[***] FLAG FOUND: {result['flag']} [***]"
                return success_msg, result.get("flag")
            # If submission failed but label was correct, it might be a server issue. Stop trying.
            break 
            
    return f"ID #{sentence_id}: Failed to find a 1-edit solution.", None

# --- Main Execution ---

if __name__ == "__main__":
    print("--- Optimized Adversarial AI CTF Solver ---")
    try:
        df = pd.read_csv(DATASET_PATH)
    except FileNotFoundError:
        print(f"[!] Error: The dataset file '{DATASET_PATH}' was not found.")
        exit(1)

    tasks = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # Submit all sentences to the executor
        for _, row in df.iterrows():
            tasks.append(executor.submit(solve_sentence, row['id'], row['sentence']))
        
        # Process results as they complete
        for future in as_completed(tasks):
            try:
                result, flag = future.result()
                print(result)
                if flag:
                    print("\nFlag found! Shutting down...")
                    # This will cancel pending tasks and exit
                    executor.shutdown(wait=False, cancel_futures=True)
                    break
            except Exception as exc:
                print(f"A task generated an exception: {exc}")

    print("\n--- Script Finished ---")
