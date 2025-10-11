# StrideSafe

Singapore's lamp posts are getting smarter. They don't just light the way as they watch over the pavements.

Your next-gen chip has been selected for testing. Can your chip distinguish pedestrians from bicycles and PMDs (personal mobility devices)?

Pass the test, and your chip will earn deployment on Singapore's smart lamp posts. Fail, and hazards roam free on pedestrian walkways.

<https://stridesafe.aictf.sg>

## Solution

This is a binary image classification task. The goal is to classify 1089 images as either "pedestrian" or "bicycle/PMD". The results of this classification are then used to generate a final image which should contain the flag.

### Step-by-Step Solution

#### Step 1: Sort the Image Files

The `reshape` function in the deployment script will fill the 33x33 grid row by row from a flat list. To ensure the pixels are in the correct place, you must process the images in lexicographical (alphabetical/numerical) order of their filenames.

Make sure your list of files is sorted, from `"00000000000.jpg"` upwards.

#### Step 2: Classify Each Image

You need to go through each of the 1089 images and decide if it contains a pedestrian or a bicycle/PMD. This manual classification is the main part of the challenge.

Let's establish a convention:

- **0**: Pedestrian
- **1**: Bicycle or PMD

### Helper Script for Classification

Manually classifying 1089 images and tracking the results can be tedious. Here is a Python script to help you with the process. It will display each image one by one and ask for your input. It also saves your progress, so you can stop and resume later.

### Optimization

The most reliable way to check if files are identical is by computing a file hash. A hash function (like MD5 or SHA256) reads a file and generates a unique, fixed-length string. If two files have the exact same content, they will have the exact same hash.

Here is the updated script. It performs these steps:

Group Duplicates: First, it scans all 1089 images, calculates a hash for each one, and groups the filenames by their hash.

Load Progress: It checks a progress file to see which unique images you have already labeled.

Label Unique Images: It then iterates through only the unique images that haven't been labeled yet, shows you one example from each group, and asks for your input.

Apply Labels to All: When you label one image, that label is stored for all other files that are identical to it.

Build Final Result: Once all unique images are labeled, it builds the final 1089-item results list in the correct, sorted order and generates the flag image.

After running this script and classifying all the images, you will get a `flag.png` file. This will likely be a QR code.
