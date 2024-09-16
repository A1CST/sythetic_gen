import os
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import json

# Define root and icon capture directory paths
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
ICON_BASE_DIR = os.path.normpath(os.path.join(ROOT_DIR, '..', 'icon_captures'))

# Load JSON data from selected directory
def load_json_data(label_json):
    if os.path.exists(label_json):
        with open(label_json, 'r') as f:
            try:
                return json.load(f) if os.stat(label_json).st_size > 0 else {}
            except json.JSONDecodeError:
                print("Error: JSON file is corrupt or empty. Initializing as an empty dictionary.")
                return {}
    else:
        return {}

# Function to save the current state of classes to JSON and TXT files
def save_class():
    current_image = icon_files[current_index]
    class_label = class_entry.get()
    icon_classes[current_image] = class_label

    with open(LABEL_JSON, 'w') as f:
        json.dump(icon_classes, f, indent=4)

    with open(LABEL_TXT, 'w') as f:
        for image, class_label in icon_classes.items():
            f.write(f"{image} {class_label}\n")

    print(f"Saved class for {current_image}: {class_label}")
    update_class_listbox()

# Function to load and display images
def load_image(index):
    if index < 0 or index >= len(icon_files):
        print(f"Error: Index {index} is out of range for icon_files.")
        return None

    image_path = os.path.join(selected_folder_path, icon_files[index])
    image = Image.open(image_path)
    image.thumbnail((600, 600))
    return ImageTk.PhotoImage(image)

# Function to update the display with the current image
def update_display():
    global current_index, img_display
    img_display = load_image(current_index)
    if img_display:
        img_label.configure(image=img_display)
        img_label.image = img_display  # Properly retain a reference to the image

        current_image = icon_files[current_index]
        class_entry.delete(0, tk.END)
        if current_image in icon_classes:
            class_entry.insert(0, icon_classes[current_image])

        update_class_listbox()

# Function to navigate to the next image
def next_image():
    global current_index
    if current_index < len(icon_files) - 1:
        current_index += 1
        update_display()
    save_progress()

# Function to navigate to the previous image
def prev_image():
    global current_index
    if current_index > 0:
        current_index -= 1
        update_display()
    save_progress()

# Function to update the class listbox
def update_class_listbox():
    class_listbox.delete(0, tk.END)
    unique_classes = set(icon_classes.values())
    for cls in sorted(unique_classes):
        class_listbox.insert(tk.END, cls)

# Function to handle double-click on a class in the listbox
def on_class_select(event):
    selected_class = class_listbox.get(class_listbox.curselection())
    class_entry.delete(0, tk.END)
    class_entry.insert(0, selected_class)

# Function to save and go to the next image
def save_and_next(event=None):
    save_class()
    next_image()

# Function to delete the current image
def delete_image():
    global current_index
    if 0 <= current_index < len(icon_files):
        current_image = icon_files[current_index]
        os.remove(os.path.join(selected_folder_path, current_image))
        print(f"Deleted {current_image}")

        if current_image in icon_classes:
            del icon_classes[current_image]
            with open(LABEL_JSON, 'w') as f:
                json.dump(icon_classes, f, indent=4)

            with open(LABEL_TXT, 'w') as f:
                for image, class_label in icon_classes.items():
                    f.write(f"{image} {class_label}\n")

        icon_files.pop(current_index)
        if current_index >= len(icon_files):
            current_index = max(0, len(icon_files) - 1)
        update_display()
        update_icon_grid()
        save_progress()

# Function to save the current progress
def save_progress():
    with open(PROGRESS_FILE, 'w') as f:
        json.dump({'current_index': current_index}, f)

# Function to handle icon clicks
def on_icon_click(event, index):
    global current_index
    current_index = index
    update_display()

# Function to update the grid display of icons
def update_icon_grid():
    for widget in icon_frame.winfo_children():
        widget.destroy()

    for index, icon_file in enumerate(icon_files):
        icon_path = os.path.join(selected_folder_path, icon_file)
        icon_image = Image.open(icon_path)
        icon_image.thumbnail((50, 50))
        icon_thumb = ImageTk.PhotoImage(icon_image)

        icon_label = tk.Label(icon_frame, image=icon_thumb, borderwidth=2, relief="solid")
        icon_label.image = icon_thumb  # Keep a reference to avoid garbage collection
        icon_label.grid(row=index // 6, column=index % 6, padx=2, pady=2)
        icon_label.bind("<Button-1>", lambda e, idx=index: on_icon_click(e, idx))

# Initialize Tkinter window
root = tk.Tk()
root.title("Icon Classifier")

# Dropdown to select a folder
def select_folder(event=None):
    global selected_folder_path, icon_files, LABEL_JSON, LABEL_TXT, PROGRESS_FILE, icon_classes, current_index
    selected = selected_folder.get()
    if selected:
        selected_folder_path = os.path.join(ICON_BASE_DIR, selected)

        # Set paths for JSON, TXT, and progress files
        LABEL_JSON = os.path.join(selected_folder_path, 'icon_classes.json')
        LABEL_TXT = os.path.join(selected_folder_path, 'icon_classes.txt')
        PROGRESS_FILE = os.path.join(selected_folder_path, 'progress.json')

        # Load or initialize JSON data
        icon_classes = load_json_data(LABEL_JSON)

        # List of images in the selected folder
        icon_files = [f for f in os.listdir(selected_folder_path) if f.endswith('.png')]
        icon_files.sort()

        # Load or initialize progress
        if os.path.exists(PROGRESS_FILE):
            with open(PROGRESS_FILE, 'r') as f:
                progress = json.load(f)
                current_index = progress.get('current_index', 0)
        else:
            current_index = 0

        # Update the display and grid
        update_display()
        update_icon_grid()

# Get available folders and set up dropdown
icon_folders = [f for f in os.listdir(ICON_BASE_DIR) if os.path.isdir(os.path.join(ICON_BASE_DIR, f))]
selected_folder = tk.StringVar()
ttk.Label(root, text="Select an Icon Folder:").pack(pady=10)
folder_dropdown = ttk.Combobox(root, textvariable=selected_folder, values=icon_folders, state='readonly')
folder_dropdown.pack(pady=10)
folder_dropdown.bind("<<ComboboxSelected>>", select_folder)

# Main display area for the image
img_label = tk.Label(root)
img_label.pack(side=tk.TOP)

# Text entry for class label
class_entry = tk.Entry(root, width=50)
class_entry.pack()
class_entry.bind('<Return>', save_and_next)

# Save class button
save_button = tk.Button(root, text="Save Class", command=save_class)
save_button.pack()

# Navigation buttons
prev_button = tk.Button(root, text="Back", command=prev_image)
prev_button.pack(side=tk.LEFT)

next_button = tk.Button(root, text="Next", command=next_image)
next_button.pack(side=tk.RIGHT)

# Delete button
delete_button = tk.Button(root, text="Delete Image", command=delete_image)
delete_button.pack()

# Listbox for existing classes
class_listbox = tk.Listbox(root, width=50, height=10)
class_listbox.pack()
class_listbox.bind('<Double-1>', on_class_select)

# Scrollable frame for icon grid
canvas = tk.Canvas(root)
icon_frame = tk.Frame(canvas)
scrollbar = ttk.Scrollbar(root, orient="vertical", command=canvas.yview)
canvas.configure(yscrollcommand=scrollbar.set)
scroll_frame = canvas.create_window((0, 0), window=icon_frame, anchor="nw")

def on_configure(event):
    canvas.configure(scrollregion=canvas.bbox("all"))

icon_frame.bind("<Configure>", on_configure)
canvas.pack(side=tk.LEFT, fill="both", expand=True)
scrollbar.pack(side=tk.RIGHT, fill="y")

# Run the Tkinter event loop
root.mainloop()
