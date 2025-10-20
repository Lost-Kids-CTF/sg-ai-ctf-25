import os
import hashlib
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image

# --- Configuration ---
data_folder = 'data'
progress_file = 'labeled_hashes.txt'  # Progress is now saved based on hashes

# --- Helper function to compute file hash ---
def get_file_hash(filepath):
    """Computes the MD5 hash of a file."""
    hasher = hashlib.md5()
    with open(filepath, 'rb') as f:
        buf = f.read()
        hasher.update(buf)
    return hasher.hexdigest()


# --- 1. Get sorted list of files and group them by hash ---
print("Scanning for duplicate images...")
try:
    image_files = sorted(
        [f for f in os.listdir(data_folder) if f.endswith('.jpg')])
except FileNotFoundError:
    print(f"Error: The directory '{data_folder}' was not found.")
    exit()

hashes_to_files = {}
file_to_hash = {}
for filename in image_files:
    path = os.path.join(data_folder, filename)
    file_hash = get_file_hash(path)
    file_to_hash[filename] = file_hash
    if file_hash not in hashes_to_files:
        hashes_to_files[file_hash] = []
    hashes_to_files[file_hash].append(filename)

unique_hashes = list(hashes_to_files.keys())
print(
    f"Found {len(image_files)} total images, with {len(unique_hashes)} unique images.")

# --- 2. Load progress from previously labeled hashes ---
labels = {}
if os.path.exists(progress_file):
    with open(progress_file, 'r') as f:
        for line in f:
            file_hash, label = line.strip().split(',')
            labels[file_hash] = int(label)
    print(
        f"Resuming session. Loaded {len(labels)} previously labeled unique images.")

# --- 3. Loop through and label only the unique, unlabeled images ---
unlabeled_hashes = [h for h in unique_hashes if h not in labels]
if unlabeled_hashes:
    print(
        f"\nStarting labeling for {len(unlabeled_hashes)} remaining unique images...")

for i, current_hash in enumerate(unlabeled_hashes):
    # Get the list of all files that are identical
    duplicate_files = hashes_to_files[current_hash]
    # Pick the first file in the group to display as an example
    example_filename = duplicate_files[0]
    img_path = os.path.join(data_folder, example_filename)

    plt.imshow(Image.open(img_path))
    title = f"Label unique image {i+1}/{len(unlabeled_hashes)} (applies to {len(duplicate_files)} files)"
    plt.title(title)
    plt.axis('off')
    plt.show(block=False)

    classification = ""
    while classification.lower() not in ['p', 'b', 'q']:
        classification = input(
            "Pedestrian (p) or Bicycle/PMD (b)? [q to save and quit]: ")

    plt.close()

    if classification.lower() == 'q':
        print("Progress saved. Run the script again to continue.")
        exit()

    label_val = 0 if classification.lower() == 'p' else 1
    labels[current_hash] = label_val

    with open(progress_file, 'a') as f:
        f.write(f"{current_hash},{label_val}\n")

# --- 4. Generate the final image if all unique images are labeled ---
if len(labels) == len(unique_hashes):
    print("\nAll unique images have been labeled!")
    print("Assembling final results in the correct order...")

    final_results = []
    for filename in image_files:
        # Look up the hash for the current filename
        file_hash = file_to_hash[filename]
        # Get the label you assigned for that hash group
        label = labels[file_hash]
        final_results.append(label)

    print("Generating final image...")
    results_arr = np.array(final_results)
    size = int(np.sqrt(len(results_arr)))

    plt.figure(figsize=(4, 4))
    plt.imshow(1 - results_arr.reshape((size, size)),
               cmap="gray", interpolation='nearest')
    plt.axis('off')

    output_filename = 'flag.png'
    plt.savefig(output_filename)
    print(f"Success! Final image saved as {output_filename}")
    plt.show()
else:
    print(
        f"\nProcess paused. {len(labels)} out of {len(unique_hashes)} unique images labeled.")
