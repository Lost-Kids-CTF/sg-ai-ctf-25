import requests
import json
import base64
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# The base URL of the challenge website from the README file.
BASE_URL = "https://real-or-fake.aictf.sg"
# The API endpoint for the Gemini model used for image analysis.
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-05-20:generateContent?key="

def analyze_image_with_gemini(image_bytes):
    """
    Analyzes the provided image bytes using the Gemini API to determine
    if it is real or fake.
    """
    print("    > Analyzing image with AI...")
    base64_image = base64.b64encode(image_bytes).decode('utf-8')

    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": "Analyze this image. Is it a real photograph or is it AI-generated? Respond with only the single word: 'real' or 'fake'."
                    },
                    {
                        "inlineData": {
                            "mimeType": "image/jpeg",
                            "data": base64_image
                        }
                    }
                ]
            }
        ]
    }

    try:
        response = requests.post(GEMINI_API_URL, json=payload)
        response.raise_for_status()
        result = response.json()
        
        # Extract the text from the response.
        # It's better to check the response structure carefully.
        text_response = result.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', 'error').strip().lower()
        
        if 'fake' in text_response:
            print("    > AI Analysis Result: FAKE")
            return "fake"
        elif 'real' in text_response:
            print("    > AI Analysis Result: REAL")
            return "real"
        else:
            print(f"    > AI returned an unexpected response: {text_response}")
            # Default to 'real' if unsure, to avoid getting stuck.
            return "real"

    except requests.exceptions.RequestException as e:
        print(f"    [!] ERROR: Could not call Gemini API: {e}")
        return "error"
    except (KeyError, IndexError):
        print(f"    [!] ERROR: Unexpected JSON structure in Gemini response: {json.dumps(result)}")
        return "error"

def solve_challenge():
    """
    This script automates the "Real or Fake" deepfake detection challenge
    by controlling a web browser with Selenium. It uses the Gemini API
    to determine if each image is real or fake and submits the answer.
    """
    print("[*] Setting up the browser with Selenium...")
    # NOTE: Ensure you have chromedriver installed and in your PATH,
    # or use another webdriver compatible with your browser.
    try:
        driver = webdriver.Chrome()
    except Exception as e:
        print(f"\n[!] ERROR: Could not start WebDriver: {e}")
        print("[!] HINT: Make sure you have a webdriver (like chromedriver) installed and accessible in your system's PATH.")
        return

    try:
        # --- Step 1: Navigate and Start the Challenge ---
        print(f"[*] Navigating to {BASE_URL}")
        driver.get(BASE_URL)

        # Wait for the start button to be clickable and then click it.
        print("[*] Waiting for the challenge to load...")
        start_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "start-challenge"))
        )
        print("[*] Starting the challenge...")
        start_button.click()

        # --- Step 2: Loop Through Images and Solve ---
        # Wait for the challenge screen to appear and get the total number of images.
        WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.ID, "challenge-screen"))
        )
        total_images_element = driver.find_element(By.ID, "total-images")
        total_images = int(total_images_element.text)
        print(f"[+] Challenge started! There are {total_images} images to analyze.")

        for i in range(1, total_images + 1):
            print(f"\n--- Analyzing image {i}/{total_images} ---")

            # Wait for the current image number to be correct
            WebDriverWait(driver, 15).until(
                EC.text_to_be_present_in_element((By.ID, "current-image"), str(i))
            )

            # Get the image source URL
            image_element = driver.find_element(By.ID, "current-image-display")
            image_url = image_element.get_attribute('src')
            print(f"  > Found image URL: {image_url}")

            # Download the image
            print("  > Downloading image...")
            response = requests.get(image_url)
            response.raise_for_status()
            image_bytes = response.content

            # Analyze the image using our AI function
            decision = analyze_image_with_gemini(image_bytes)

            if decision == "fake":
                print("  > Clicking 'Fake' button.")
                driver.find_element(By.ID, "deepfake-btn").click()
            elif decision == "real":
                print("  > Clicking 'Real' button.")
                driver.find_element(By.ID, "legitimate-btn").click()
            else:
                print("  > Could not make a decision. Defaulting to 'Real'.")
                driver.find_element(By.ID, "legitimate-btn").click()
            
            # A small delay to allow the next image to load smoothly.
            time.sleep(1)

        # --- Step 3: Get the Flag ---
        print("\n[*] All images processed! Waiting for results screen...")
        results_screen = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.ID, "results-screen"))
        )
        
        print("[+] Results screen is visible. Extracting content.")
        results_content = driver.find_element(By.ID, "results-content").text
        
        print("\n--- ✅ Final Results ---")
        print(results_content)
        print("-----------------------\n")

        # The flag is usually within the results text.
        if "aictf{" in results_content.lower():
            print("🎉 FLAG FOUND!")
        else:
            print("[!] The flag was not found in the results text.")

    except Exception as e:
        print(f"\n[!] An unexpected error occurred during the process: {e}")
    finally:
        # --- Step 4: Cleanup ---
        print("[*] Closing the browser.")
        driver.quit()


if __name__ == "__main__":
    solve_challenge()

