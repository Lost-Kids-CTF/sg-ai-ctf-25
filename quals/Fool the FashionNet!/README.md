# Fool the FashionNet

Your greatest rival, FashionNET, has unveiled a state-of-the-art AI that "perfectly" organises wardrobes for millions-until someone left the model weights exposed on a public server. Now their classifier is laughably fragile: tiny, invisible tweaks can flip shirts into shoes, or trousers into dresses. As a trained AI hacker, craft a near-invisible perturbation, and prove you can outstyle their system. Steal the spotlight - and claim the flag.

Your mission: Craft a tiny delta.npy that flips FashionNET's AI model prediction, without changing how the image looks to humans. Respect the L-infinity and SSIM rules-stay stealthy, no wild makeovers! Submit to verify and claim the flag. Can you outsmart the AI (and look good doing it)? Bonus points for style, zero points for pixelated chaos.

<https://fool-the-fashionnet.aictf.sg>

## Solution

This is a classic adversarial machine learning problem. You are given a pre-trained model and an image, and your goal is to create a small, visually imperceptible perturbation that causes the model to misclassify the image. This is a **white-box attack** because you have full access to the model's architecture and weights.

### 1\. Understanding the Challenge

From the provided files, here's what we know:

- **Objective:** Create a perturbation file, `delta.npy`, which when added to the `seed.png` image, causes the model to predict a different class.
- **Model:** A `SmallFashionCNN` defined in `model.py` with weights provided in `model.pt`. It's a standard convolutional neural network for image classification.
- **Dataset:** The model was trained on Fashion-MNIST, which has 10 classes. The `seed.png` is an image of a T-shirt/top (Class 0).
- **Constraints:** The perturbation (`delta`) must satisfy two main conditions:
  1. **L-infinity Norm ($L_\infty$):** The absolute value of the largest change to any single pixel must be less than or equal to 0.08. This is checked with `||delta||_∞ ≤ 0.08`.
  2. **Structural Similarity (SSIM):** The perturbed image must be visually very similar to the original, with a score of at least 0.85. This is checked with `SSIM ≥ 0.85`.
- **File Format:** The output `delta.npy` must be a NumPy array with `shape=(1, 28, 28)` and `dtype=float32`.

### 2\. The Attack Strategy: Fast Gradient Sign Method (FGSM)

The most direct and effective method for this white-box scenario is the **Fast Gradient Sign Method (FGSM)**. The core idea is to leverage the model's own learning mechanism against it.

1. We calculate the **loss** of the model's prediction on the original image.
2. We then compute the **gradient** of this loss with respect to the input image's pixels. This gradient tells us the direction to change each pixel to _maximize_ the loss.
3. We take the **sign** of the gradient (either -1 or 1 for each pixel) and multiply it by a small number, $\epsilon$ (epsilon), which represents the attack's strength.

The formula for the perturbed image is:
$x_{adv} = x + \epsilon \cdot \text{sign}(\nabla_x J(\theta, x, y))$

Where:

- $x_{adv}$ is the new adversarial image.
- $x$ is the original input image.
- $\epsilon$ is the perturbation magnitude (we'll use the L∞ constraint of 0.08 here).
- $\text{sign}(\cdot)$ is the sign function.
- $\nabla_x J(\theta, x, y)$ is the gradient of the loss function $J$ with respect to the input image $x$.
