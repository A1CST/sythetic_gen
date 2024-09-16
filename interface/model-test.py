import os
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import cv2
import numpy as np
import torch
import pyautogui
import yaml


# Function to capture a screenshot of the desktop
def capture_screenshot():
    screenshot = pyautogui.screenshot()
    screenshot = screenshot.convert("RGB")
    return screenshot


# Function to load class names from finalized_class.txt
def load_finalized_classes(filepath):
    class_mapping = {}
    finalized_class_file_path = os.path.join(os.path.dirname(filepath), 'finalized_class.txt')

    if os.path.exists(finalized_class_file_path):
        with open(finalized_class_file_path, 'r') as f:
            for line in f:
                parts = line.strip().split(maxsplit=1)
                if len(parts) == 2:
                    class_id = int(parts[0])
                    class_name = parts[1]
                    class_mapping[class_id] = class_name
        print(f"Loaded classes from finalized_class.txt: {class_mapping}")
    else:
        print("finalized_class.txt not found in the model directory.")

    return class_mapping


# Function to process the screenshot with YOLO model and filter results by confidence
def process_screenshot_with_yolo(screenshot, model, class_mapping, confidence_threshold=0.5):
    # Convert screenshot to numpy array and prepare it for YOLO model
    frame = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
    results = model(frame)  # YOLO model prediction

    # Filter out detections below the confidence threshold
    detections = results.xyxy[0]  # Get the detections
    filtered_detections = [d for d in detections if d[4] >= confidence_threshold]  # Confidence is at index 4

    # Draw bounding boxes on the frame
    for det in filtered_detections:
        x1, y1, x2, y2, conf, cls = det[:6]
        cls = int(cls)  # Ensure cls is an integer
        print(f"Detected class index: {cls}")  # Debugging

        # Get the class name from the finalized class mapping
        class_name = class_mapping.get(cls, "Unknown")  # Use the mapping to get the class name

        label = f"{class_name} {conf:.2f}"
        cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)
        cv2.putText(frame, label, (int(x1), int(y1) - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        print(f"Detection: {label} at [{x1}, {y1}, {x2}, {y2}]")  # Debugging output

    return frame


# Function to print classes from the data.yaml file
def print_yaml_classes(filepath):
    data_yaml_path = os.path.join(os.path.dirname(filepath), 'data.yaml')
    if os.path.exists(data_yaml_path):
        with open(data_yaml_path, 'r') as file:
            data = yaml.safe_load(file)
            class_names = data.get('names', [])
            print("Classes from data.yaml:", class_names)
            return class_names
    else:
        print("data.yaml not found in the model directory.")
        return []


# Function to load YOLO model from selected file and verify class names
def load_yolo_model(filepath):
    # Print classes from the data.yaml
    print_yaml_classes(filepath)

    # Load the YOLO model
    model = torch.hub.load('ultralytics/yolov5', 'custom', path=filepath, force_reload=True)

    # Verify that the model class names match the expected classes
    print("Model classes loaded in the model:", model.names)  # Check loaded class names
    if len(model.names) != len(set(model.names)):
        print("Warning: Duplicate class names detected in model!")
    return model


# Function to update display with processed image, resized to fit window
def update_display(frame):
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # Convert to RGB
    img = Image.fromarray(frame)

    # Resize the image to fit inside the Tkinter window
    window_width, window_height = root.winfo_width(), root.winfo_height()
    img.thumbnail((window_width - 20, window_height - 80))  # Leave space for borders and controls

    img_tk = ImageTk.PhotoImage(image=img)
    img_label.config(image=img_tk)
    img_label.image = img_tk


# Function to continuously capture, process, and update the display
def continuous_capture():
    if model and class_mapping:
        screenshot = capture_screenshot()
        processed_frame = process_screenshot_with_yolo(screenshot, model, class_mapping)
        update_display(processed_frame)
    # Schedule the next screenshot capture after 100 milliseconds (adjustable)
    root.after(100, continuous_capture)


# Function triggered when the load button is clicked
def on_load_button_click():
    global model, class_mapping
    model_path = filedialog.askopenfilename(title="Select YOLO Model File", filetypes=[("YOLO Model", "*.pt")])
    if model_path:
        model = load_yolo_model(model_path)
        class_mapping = load_finalized_classes(model_path)
        continuous_capture()  # Start the continuous capture loop


# Setup Tkinter window
root = tk.Tk()
root.title("YOLO Model Tester")
root.geometry("1200x800")  # Set the initial size of the window

# Setup UI Elements
load_button = tk.Button(root, text="Load Model and Start", command=on_load_button_click)
load_button.pack(pady=10)

img_label = tk.Label(root)
img_label.pack(padx=10, pady=10)

model = None  # Initialize model variable
class_mapping = None  # Initialize class mapping variable

root.mainloop()
