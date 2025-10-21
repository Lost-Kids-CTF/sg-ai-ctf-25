import os
import sys
import numpy as np
from PIL import Image, ImageDraw
from skimage.metrics import structural_similarity as ssim
from scipy.optimize import linear_sum_assignment  # For optimal assignment

# --- Configuration ---
SLICES_DIR = 'sliced_images'
REF_IMAGE_PATH = 'reference.jpg'
OUTPUT_IMAGE_PATH = 'solution_reconstructed.png'
OUTPUT_SCORES_PATH = 'match_scores.txt'
GRID_SIZE = 32

# --- Tunable Parameter ---
# We will highlight any piece whose final match score is *below* this.
HIGHLIGHT_THRESHOLD = 0.95
# ---------------------


def solve_and_reconstruct():
    print("Starting optimal reconstruction...")

    # --- PHASE 1: Load all 1024 puzzle pieces ---
    print(f"Phase 1: Loading {GRID_SIZE*GRID_SIZE} pieces...")
    all_pieces = []
    piece_w, piece_h = 0, 0

    for i in range(GRID_SIZE * GRID_SIZE):
        piece_path = os.path.join(SLICES_DIR, f'piece_{i:04d}.png')
        try:
            img = Image.open(piece_path).convert('RGB')
            if piece_w == 0:
                piece_w, piece_h = img.size
                print(f"Piece size detected: {piece_w}x{piece_h}")

            all_pieces.append({
                'id': i,
                'img': img,
                'data': np.array(img),
            })
        except FileNotFoundError:
            print(f"Error: Missing piece: {piece_path}")
            return

    if not all_pieces:
        print("Error: No pieces were loaded.")
        return

    # --- PHASE 2: Load reference image and create 1024 reference slots ---
    print("Phase 2: Loading reference image and splitting into slots...")
    all_slots = []
    try:
        ref_img = Image.open(REF_IMAGE_PATH).convert('RGB')

        final_img_w = piece_w * GRID_SIZE
        final_img_h = piece_h * GRID_SIZE
        ref_img_resized = ref_img.resize(
            (final_img_w, final_img_h), Image.LANCZOS)
        ref_np = np.array(ref_img_resized)

        # Split the resized reference into 1024 slots
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                slot_id = y * GRID_SIZE + x
                x1, y1 = x * piece_w, y * piece_h
                x2, y2 = x1 + piece_w, y1 + piece_h
                slot_data = ref_np[y1:y2, x1:x2]
                all_slots.append({
                    'id': slot_id,
                    'pos_xy': (x, y),  # Grid position
                    'data': slot_data
                })

    except FileNotFoundError:
        print(f"Error: Reference image not found: '{REF_IMAGE_PATH}'")
        return

    # --- PHASE 3: Build the SSIM Score Matrix (1024x1024) ---
    print("Phase 3: Building SSIM score matrix...")
    print("(This will take a few minutes as it's 1024x1024 = ~1 million comparisons)")

    num_items = GRID_SIZE * GRID_SIZE
    ssim_matrix = np.zeros((num_items, num_items))

    for i in range(num_items):  # Piece index
        piece_data = all_pieces[i]['data']

        for j in range(num_items):  # Slot index
            slot_data = all_slots[j]['data']

            score = ssim(piece_data, slot_data,
                         channel_axis=-1, data_range=255)
            ssim_matrix[i, j] = score

        sys.stdout.write(f"\rComparing piece {i+1}/{num_items}...")
        sys.stdout.flush()

    print("\nSSIM matrix built.")

    # --- PHASE 4: Solve the Assignment Problem ---
    print("Phase 4: Running optimal assignment algorithm...")

    # The Hungarian algorithm finds the *minimum* cost.
    # We want to *maximize* the SSIM score.
    # So, we use a cost matrix of (1.0 - SSIM).
    cost_matrix = 1.0 - ssim_matrix

    # This finds the optimal one-to-one pairing
    piece_indices, slot_indices = linear_sum_assignment(cost_matrix)

    print("Assignment complete.")

    # --- PHASE 5: Process results and save text file ---
    print("Phase 5: Saving scores and preparing image...")

    results = []

    with open(OUTPUT_SCORES_PATH, 'w') as f:
        f.write("Piece_ID | Slot_Position (y, x) | SSIM_Score\n")
        f.write("----------------------------------------------\n")

        for i in range(num_items):
            piece_idx = piece_indices[i]
            slot_idx = slot_indices[i]

            piece_id = all_pieces[piece_idx]['id']
            slot_pos = all_slots[slot_idx]['pos_xy']  # (x, y)
            final_score = ssim_matrix[piece_idx, slot_idx]

            results.append({
                'piece_id': piece_id,
                'piece_img': all_pieces[piece_idx]['img'],
                'slot_pos_xy': slot_pos,
                'score': final_score
            })

        # Sort results by piece_id for a clean text file
        results_sorted_by_piece = sorted(results, key=lambda r: r['piece_id'])

        for res in results_sorted_by_piece:
            y, x = res['slot_pos_xy'][1], res['slot_pos_xy'][0]
            f.write(
                f"{res['piece_id']:<8d} | ({y:02d}, {x:02d})             | {res['score']:.6f}\n")

    print(f"Scores saved to {OUTPUT_SCORES_PATH}")

    # --- PHASE 6: Create visualization image ---
    print("Phase 6: Assembling final image...")

    final_img_w = piece_w * GRID_SIZE
    final_img_h = piece_h * GRID_SIZE
    solution_image = Image.new('RGB', (final_img_w, final_img_h))
    draw = ImageDraw.Draw(solution_image)

    low_score_count = 0

    # Use the original (unsorted) results for pasting
    for res in results:
        piece_img = res['piece_img']
        x, y = res['slot_pos_xy']
        score = res['score']

        # Calculate pixel coordinates for pasting
        paste_x = x * piece_w
        paste_y = y * piece_h

        solution_image.paste(piece_img, (paste_x, paste_y))

        # Highlight if below threshold
        if score < HIGHLIGHT_THRESHOLD:
            low_score_count += 1
            draw.rectangle(
                [paste_x, paste_y, paste_x + piece_w - 1, paste_y + piece_h - 1],
                outline='red',
                width=2
            )

    solution_image.save(OUTPUT_IMAGE_PATH)

    print("--------------------------------------------------")
    print(f"✅ Success! Reconstructed image saved as: {OUTPUT_IMAGE_PATH}")
    print(
        f"Highlighted {low_score_count} pieces with SSIM < {HIGHLIGHT_THRESHOLD}.")
    print("--------------------------------------------------")


if __name__ == "__main__":
    solve_and_reconstruct()
