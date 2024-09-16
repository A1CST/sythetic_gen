import os
import random
from PIL import Image
import cv2
import numpy as np
from concurrent.futures import ThreadPoolExecutor
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from threading import Thread, Lock
import shutil

# Adjustable variables
DESKTOP_SIZE = (1920, 1080)  # Size of the synthetic desktop
progress_lock = Lock()  # Lock for thread-safe progress updates

def remove_background(icon_path):
    # Load the icon using OpenCV
    icon = cv2.imread(icon_path, cv2.IMREAD_UNCHANGED)

    # Convert to RGBA if not already
    if icon.shape[2] == 3:
        icon = cv2.cvtColor(icon, cv2.COLOR_BGR2BGRA)

    # Convert icon to grayscale
    gray = cv2.cvtColor(icon, cv2.COLOR_BGR2GRAY)

    # Use thresholding to create a mask for the background
    _, mask = cv2.threshold(gray, 250, 255, cv2.THRESH_BINARY_INV)

    # Find contours to detect the icon shape
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if contours:
        # Create a new mask with the largest contour (assumed to be the icon)
        mask = np.zeros_like(gray)
        cv2.drawContours(mask, contours, -1, (255), thickness=cv2.FILLED)

        # Apply the mask to the icon
        icon[:, :, 3] = mask  # Set the alpha channel based on the mask

    # Convert the icon back to PIL for easier handling later
    icon_pil = Image.fromarray(cv2.cvtColor(icon, cv2.COLOR_BGRA2RGBA))
    return icon_pil

def renumber_classes(finalized_class_file_path):
    """
    Re-number the classes in finalized_class.txt to be sequential from 0 to N-1.
    """
    if os.path.exists(finalized_class_file_path):
        class_mapping = {}
        with open(finalized_class_file_path, 'r') as f:
            lines = f.readlines()
            for i, line in enumerate(lines):
                parts = line.strip().split(maxsplit=1)
                if len(parts) == 2:
                    _, class_name = parts
                    class_mapping[class_name] = i

        # Rewrite the file with re-numbered class IDs
        with open(finalized_class_file_path, 'w') as f:
            for class_id, class_name in enumerate(class_mapping.keys()):
                f.write(f"{class_id} {class_name}\n")
        print(f"Re-numbered classes and updated '{finalized_class_file_path}'.")
    else:
        print(f"Finalized class file not found at {finalized_class_file_path}.")

def load_class_mapping(icon_dir):
    class_mapping = {}
    finalized_class_file_path = os.path.join(icon_dir, 'finalized_class.txt')

    renumber_classes(finalized_class_file_path)  # Ensure classes are re-numbered before loading

    if os.path.exists(finalized_class_file_path):
        with open(finalized_class_file_path, 'r') as f:
            for line in f:
                parts = line.strip().split(maxsplit=1)
                if len(parts) == 2:
                    class_id = int(parts[0])
                    class_name = parts[1]
                    class_mapping[class_id] = class_name
                else:
                    print(f"Skipping malformed line in class file: {line}")
    else:
        print("Finalized class file not found. Make sure 'finalized_class.txt' exists in the icon directory.")

    print(f"Loaded class mapping from finalized_class.txt: {class_mapping}")
    return class_mapping

def generate_single_desktop(index, output_dir, icon_paths, class_mapping, background_paths, desktop_size,
                            use_background, progress_var, total_images):
    # Select a background or use a white background
    if use_background and background_paths:
        background_path = random.choice(background_paths)
        background = Image.open(background_path).convert('RGBA')
    else:
        background = Image.new('RGBA', desktop_size, (255, 255, 255, 255))  # White background

    background = background.resize(desktop_size)
    annotations = []

    # Determine the number of icons to place
    num_icons = random.randint(5, 15)  # Adjust range as needed

    for j in range(num_icons):
        # Select a random icon and remove its background
        icon_path = random.choice(icon_paths)
        icon_name = os.path.basename(icon_path).replace('.png', '')

        # Extract the numeric part from the icon name (e.g., 'icon_5' -> 5)
        try:
            icon_id = int(icon_name.split('_')[1])
        except (IndexError, ValueError):
            print(f"Error parsing icon ID from {icon_name}. Skipping this icon.")
            continue

        # Match the extracted ID with the class mapping
        if icon_id in class_mapping:
            class_id = icon_id  # Use the numeric ID directly as the class ID
        else:
            print(f"Warning: Icon ID '{icon_id}' not found in finalized_class.txt. Skipping.")
            continue

        icon = remove_background(icon_path)

        # Randomly resize the icon
        resize_factor = random.uniform(0.5, 1.5)
        icon = icon.resize((int(icon.width * resize_factor), int(icon.height * resize_factor)))

        # Check if the icon fits within the desktop size
        if icon.width > desktop_size[0] or icon.height > desktop_size[1]:
            continue  # Skip icons that are too large

        # Randomly place the icon on the desktop
        max_x = desktop_size[0] - icon.width
        max_y = desktop_size[1] - icon.height

        if max_x <= 0 or max_y <= 0:
            continue  # Skip this icon placement if it can't fit

        x = random.randint(0, max_x)
        y = random.randint(0, max_y)

        # Paste the icon onto the desktop
        background.paste(icon, (x, y), icon)

        # Calculate bounding box in YOLO format
        x_center = (x + icon.width / 2) / desktop_size[0]
        y_center = (y + icon.height / 2) / desktop_size[1]
        width = icon.width / desktop_size[0]
        height = icon.height / desktop_size[1]

        # Use the assigned class ID
        annotations.append(f"{class_id} {x_center} {y_center} {width} {height}")

    # Save the synthetic desktop image
    desktop_filename = os.path.join(output_dir, f"synthetic_desktop_{index}.png")
    background.convert('RGB').save(desktop_filename)

    # Save the annotation file
    annotation_filename = os.path.join(output_dir, f"synthetic_desktop_{index}.txt")
    with open(annotation_filename, 'w') as f:
        f.write('\n'.join(annotations))

    print(f"Generated synthetic desktop {index}")

    # Update progress bar
    with progress_lock:
        progress_var.set(progress_var.get() + (100 / total_images))

def get_next_output_directory(icon_dir):
    base_output_dir = os.path.join(icon_dir, 'synth_gens')
    os.makedirs(base_output_dir, exist_ok=True)

    existing_dirs = [d for d in os.listdir(base_output_dir) if
                     os.path.isdir(os.path.join(base_output_dir, d)) and d.startswith('synth_gen_images_')]
    if existing_dirs:
        existing_numbers = [int(d.split('_')[-1]) for d in existing_dirs if d.split('_')[-1].isdigit()]
        next_number = max(existing_numbers) + 1 if existing_numbers else 1
    else:
        next_number = 1

    new_output_dir = os.path.join(base_output_dir, f'synth_gen_images_{next_number}')
    os.makedirs(new_output_dir, exist_ok=True)
    return new_output_dir

def copy_class_files(icon_dir, output_dir):
    # Copy finalized_class.txt
    finalized_class_file_path = os.path.join(icon_dir, 'finalized_class.txt')
    if os.path.exists(finalized_class_file_path):
        shutil.copy(finalized_class_file_path, output_dir)
        print(f"Copied finalized class file to: {output_dir}")
    else:
        print("Finalized class file not found. Make sure 'finalized_class.txt' exists in the icon directory.")

def generate_synthetic_desktops(icon_dir, background_dir, num_images, num_threads, desktop_size, use_background,
                                progress_var):
    output_dir = get_next_output_directory(icon_dir)

    # Copy the finalized class file to the output directory
    copy_class_files(icon_dir, output_dir)

    icon_paths = [os.path.join(icon_dir, icon) for icon in os.listdir(icon_dir) if icon.endswith('.png')]

    class_mapping = load_class_mapping(icon_dir)

    background_paths = [os.path.join(background_dir, bg) for bg in os.listdir(background_dir) if
                        bg.endswith(('.png', '.jpg', '.jpeg'))]

    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        for i in range(num_images):
            executor.submit(generate_single_desktop, i, output_dir, icon_paths, class_mapping, background_paths,
                            desktop_size, use_background, progress_var, num_images)

def start_generation(icon_dir, background_dir, num_images, num_threads, use_background, progress_var):
    def run_generation():
        generate_synthetic_desktops(icon_dir, background_dir, num_images, num_threads, DESKTOP_SIZE, use_background,
                                    progress_var)
        messagebox.showinfo("Generation Complete", "Synthetic desktop generation is complete.")

    Thread(target=run_generation).start()

def open_directory_dialog(var):
    selected_dir = filedialog.askdirectory(initialdir=os.getcwd(), title="Select Directory")
    var.set(selected_dir)

# Tkinter UI
root = tk.Tk()
root.title("Synthetic Desktop Generator")

icon_dir_var = tk.StringVar()
background_dir_var = tk.StringVar()
use_background_var = tk.BooleanVar(value=True)
num_images_var = tk.IntVar(value=1000)
num_threads_var = tk.IntVar(value=10)
progress_var = tk.DoubleVar(value=0)

tk.Label(root, text="Icon Directory:").pack()
tk.Entry(root, textvariable=icon_dir_var, width=50).pack()
tk.Button(root, text="Select Icon Directory", command=lambda: open_directory_dialog(icon_dir_var)).pack()

tk.Label(root, text="Background Directory:").pack()
tk.Entry(root, textvariable=background_dir_var, width=50).pack()
tk.Button(root, text="Select Background Directory", command=lambda: open_directory_dialog(background_dir_var)).pack()

tk.Checkbutton(root, text="Use Backgrounds", variable=use_background_var).pack()

tk.Label(root, text="Number of Images:").pack()
tk.Scale(root, from_=1, to=5000, orient=tk.HORIZONTAL, variable=num_images_var).pack()

tk.Label(root, text="Number of Threads:").pack()
tk.Scale(root, from_=1, to=100, orient=tk.HORIZONTAL, variable=num_threads_var).pack()

tk.Button(root, text="Generate", command=lambda: start_generation(
    icon_dir_var.get(),
    background_dir_var.get(),
    num_images_var.get(),
    num_threads_var.get(),
    use_background_var.get(),
    progress_var
)).pack()

progress_bar = ttk.Progressbar(root, variable=progress_var, maximum=100)
progress_bar.pack(fill=tk.X, padx=10, pady=10)

root.mainloop()
