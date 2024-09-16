import cv2
import numpy as np
from PIL import Image
import pyautogui
import os

def capture_screenshot():
    try:
        # Create a directory named 'icon_captures' above the 'interface' directory
        interface_dir = os.path.dirname(os.getcwd())  # Get the parent directory of the current working directory
        captures_dir = os.path.join(interface_dir, 'icon_captures')
        os.makedirs(captures_dir, exist_ok=True)

        # Capture a screenshot of the main monitor
        screenshot = pyautogui.screenshot()
        screenshot_path = os.path.join(captures_dir, 'screenshot.png')
        screenshot.save(screenshot_path)
        return screenshot_path
    except Exception as e:
        print(f"Error capturing screenshot: {e}")
        return None

def get_next_output_directory(base_dir):
    # Find the next available numbered directory in 'icon_captures'
    existing_dirs = [d for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d)) and d.startswith('icons_')]
    if existing_dirs:
        existing_numbers = [int(d.split('_')[1]) for d in existing_dirs if d.split('_')[1].isdigit()]
        next_number = max(existing_numbers) + 1 if existing_numbers else 1
    else:
        next_number = 1

    # Create the new output directory path
    new_output_dir = os.path.join(base_dir, f'icons_{next_number}')
    os.makedirs(new_output_dir, exist_ok=True)
    return new_output_dir

def extract_icons(screenshot_path, output_dir):
    try:
        # Load the screenshot
        img = cv2.imread(screenshot_path)

        if img is None:
            print(f"Error: Could not load image from {screenshot_path}")
            return

        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Use edge detection to find icons
        edges = cv2.Canny(gray, threshold1=30, threshold2=100)

        # Find contours (this will identify potential icon boundaries)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)

        # Path for the finalized_class.txt file
        class_file_path = os.path.join(output_dir, 'finalized_class.txt')
        with open(class_file_path, 'w') as class_file:
            icon_count = 0
            for contour in contours:
                # Get the bounding box for each contour
                x, y, w, h = cv2.boundingRect(contour)

                # Filter out small contours that are not icons
                if w > 20 and h > 20:  # Adjust size filter as needed
                    # Extract the icon using the bounding box
                    icon = img[y:y + h, x:x + w]

                    # Convert the icon to a PIL image and add transparency
                    icon_pil = Image.fromarray(cv2.cvtColor(icon, cv2.COLOR_BGR2RGBA))
                    transparent_icon = Image.new("RGBA", icon_pil.size, (0, 0, 0, 0))
                    transparent_icon.paste(icon_pil, (0, 0), icon_pil)

                    # Save the icon as PNG with transparency
                    icon_filename = os.path.join(output_dir, f"icon_{icon_count}.png")
                    transparent_icon.save(icon_filename)

                    # Write the icon's index and "un-labeled" to the finalized_class.txt file
                    class_file.write(f"{icon_count}    un-labeled\n")

                    icon_count += 1

        print(f"Extracted {icon_count} icons and saved to {output_dir}")
        print(f"Class file saved to: {class_file_path}")

    except Exception as e:
        print(f"Error extracting icons: {e}")

# Example usage
captures_dir = os.path.join(os.path.dirname(os.getcwd()),'Detection','icon_captures')  # Adjust to place above 'interface' directory
screenshot_path = capture_screenshot()
if screenshot_path:
    output_dir = get_next_output_directory(captures_dir)
    extract_icons(screenshot_path, output_dir)
