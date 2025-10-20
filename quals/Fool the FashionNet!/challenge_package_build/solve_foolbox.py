# solve_foolbox.py

import torch
import numpy as np
from PIL import Image
import torchvision.transforms as T
import foolbox as fb

# Import utilities and model from the challenge package
from model import SmallFashionCNN
from utils import linf, ssim_01

# --- Configuration ---
MODEL_PATH = "model.pt"
IMAGE_PATH = "seed.png"
SSIM_THRESHOLD = 0.85
LINF_THRESHOLD = 0.08

# Epsilon is the perturbation magnitude. We test a range of values
# to find one that satisfies all constraints.
EPSILON_CANDIDATES = np.arange(0.045, 0.055, 0.001)

# --- Define class names for Fashion-MNIST for clarity ---
FASHION_MNIST_CLASSES = {
    0: 'T-shirt/top', 1: 'Trouser', 2: 'Pullover', 3: 'Dress', 4: 'Coat',
    5: 'Sandal', 6: 'Shirt', 7: 'Sneaker', 8: 'Bag', 9: 'Ankle boot'
}


def solve_with_foolbox():
    """
    Generates the adversarial perturbation delta.npy using the Foolbox library.
    """
    # --- 1. Load PyTorch Model ---
    print(f"Loading PyTorch model from {MODEL_PATH}...")
    pytorch_model = SmallFashionCNN(num_classes=10)
    pytorch_model.load_state_dict(torch.load(MODEL_PATH)['model_state'])
    pytorch_model.eval()
    print("Model loaded successfully.")

    # --- 2. Load and Preprocess Image ---
    print(f"Loading and preprocessing image from {IMAGE_PATH}...")
    transform = T.ToTensor()
    image_pil = Image.open(IMAGE_PATH).convert("L")
    original_image_tensor = transform(image_pil).unsqueeze(0)

    # --- 3. Wrap Model and Get Original Prediction using Foolbox ---
    # Foolbox requires the model to be wrapped in its own class.
    # We must specify the bounds of the input data (0 to 1 for ToTensor).
    fmodel = fb.PyTorchModel(pytorch_model, bounds=(0, 1))

    # Get the original prediction to determine the ground-truth label for the attack
    original_pred_idx = fmodel(original_image_tensor).argmax(axis=-1)
    original_label = original_pred_idx.item()

    print("-" * 30)
    print(
        f"Original Prediction: Class {original_label} ({FASHION_MNIST_CLASSES[original_label]})")
    print("-" * 30)

    # --- 4. Instantiate the FGSM Attack ---
    attack = fb.attacks.FGSM()
    print("Searching for a valid solution using Foolbox FGSM...")
    
    solution_found = False
    for epsilon in EPSILON_CANDIDATES:
        print(f"\n--- Trying EPSILON = {epsilon:.4f} ---")

        # --- 5. Execute the Attack ---
        # The attack function takes the model, inputs, criterion (labels), and epsilons.
        # It returns the raw perturbation, the clipped adversarial image, and a success flag.
        raw_advs, clipped_advs, success = attack(
            fmodel,
            original_image_tensor,
            original_pred_idx,
            epsilons=epsilon
        )
        
        # --- 6. Validate the Results Against All Constraints ---
        # The 'success' flag from foolbox only indicates if the label was flipped.
        # We must manually check our custom SSIM and L-infinity constraints.
        
        # Calculate the actual delta and adversarial prediction
        delta_tensor = clipped_advs - original_image_tensor
        adversarial_label = fmodel(clipped_advs).argmax(axis=-1).item()

        # Convert to numpy for validation with provided utils
        original_image_np = original_image_tensor.squeeze().cpu().numpy()
        adversarial_image_np = clipped_advs.squeeze().detach().cpu().numpy()
        delta_np = delta_tensor.squeeze(0).detach().cpu().numpy()

        # Check constraints
        linf_norm, linf_valid = linf(delta_np, eps=LINF_THRESHOLD)
        ssim_score = ssim_01(original_image_np, adversarial_image_np)
        ssim_valid = ssim_score >= SSIM_THRESHOLD
        
        # Foolbox's `success` flag is a tensor, so we use .item()
        label_flipped = success.item()

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

            # --- 7. Save the Successful Perturbation ---
            output_filename = 'delta.npy'
            # Ensure shape is (1, 28, 28) and dtype is float32 for submission
            delta_to_save = delta_np.reshape(1, 28, 28).astype(np.float32)
            np.save(output_filename, delta_to_save)
            print(
                f"Perturbation saved to '{output_filename}'. You can now submit this file.")
            break

    if not solution_found:
        print("\n❌ Failure. Could not find a suitable EPSILON in the given range.")


if __name__ == "__main__":
    solve_with_foolbox()