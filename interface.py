import os
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import subprocess

# Global variables for cycling through synthetic images
synth_images = []
current_image_index = 0

# Create the main application window first
root = tk.Tk()
root.title("Main Interface")
root.geometry("1200x600")  # Width x Height

# Initialize the auto_refresh variable after the root window is created
auto_refresh = tk.BooleanVar(value=False)

# Function to call extract1.py
def run_extract_script():
    subprocess.run(['python', 'interface/extract1.py'])
    check_auto_refresh()
def run_extract_image_script():
    subprocess.run(['python', 'interface/extract_image.py'])
    check_auto_refresh()
def run_testing_script():
    subprocess.run(['python', 'interface/model-test.py'])
    check_auto_refresh()

def run_className_script():
    subprocess.run(['python', 'interface/ClassName1.py'])


def run_synthetic_script():
    subprocess.run(['python', 'interface/synthetic.py'])
    check_auto_refresh()

def run_training_script():
    subprocess.run(['python', 'interface/train.py'])
    check_auto_refresh()


# Function to refresh directories and update dropdowns
def refresh_directories():
    icon_dropdown['values'] = populate_dropdown('icon_captures')
    synth_dropdown['values'] = ["None"]  # Reset synth dropdown
    icon_dropdown_var.set("None")
    synth_dropdown_var.set("None")
    icon_canvas.delete("all")
    synth_canvas.delete("all")

def check_auto_refresh():
    if auto_refresh.get():
        refresh_directories()

# Function to update the canvas with icons from the selected directory
def update_icon_canvas(canvas, dropdown_var, base_dir, synth_dropdown):
    selected_dir = dropdown_var.get()
    canvas.delete("all")  # Clear the canvas
    synth_dropdown['values'] = ["None"]  # Reset synth dropdown

    if selected_dir != "None":
        icon_path = os.path.join(base_dir, selected_dir)
        icons = [f for f in os.listdir(icon_path) if f.endswith('.png')]

        # Update synth dropdown based on the selected icon directory
        synth_gens_path = os.path.join(icon_path, 'synth_gens')
        if os.path.exists(synth_gens_path):
            synth_dirs = [d for d in os.listdir(synth_gens_path) if os.path.isdir(os.path.join(synth_gens_path, d))]
            synth_dropdown['values'] = ["None"] + synth_dirs
        else:
            synth_dropdown['values'] = ["None"]

        # Display icons in a grid
        rows, cols = 5, 5
        icon_size = 50
        for index, icon in enumerate(icons):
            try:
                img_path = os.path.join(icon_path, icon)
                img = Image.open(img_path)
                img.thumbnail((icon_size, icon_size))
                img_tk = ImageTk.PhotoImage(img)
                row, col = divmod(index, cols)
                canvas.create_image(col * icon_size, row * icon_size, anchor='nw', image=img_tk)
                canvas.image = img_tk  # Keep a reference to avoid garbage collection
            except Exception as e:
                print(f"Error loading image {img_path}: {e}")

# Function to update synthetic canvas with images from the selected subdirectory
def update_synth_canvas(canvas, dropdown_var, base_dir, icon_dir):
    global synth_images, current_image_index
    selected_dir = dropdown_var.get()
    canvas.delete("all")  # Clear the canvas

    if selected_dir != "None":
        synth_path = os.path.join(icon_dir, 'synth_gens', selected_dir)
        synth_images = [os.path.join(synth_path, f) for f in os.listdir(synth_path) if f.endswith('.png')]
        synth_images.sort()
        current_image_index = 0
        display_synth_image(canvas)

def display_synth_image(canvas):
    global synth_images, current_image_index
    if synth_images:
        canvas.delete("all")
        try:
            img_path = synth_images[current_image_index]
            img = Image.open(img_path)
            img.thumbnail((500, 300))
            img_tk = ImageTk.PhotoImage(img)
            canvas.create_image(0, 0, anchor='nw', image=img_tk)
            canvas.image = img_tk  # Keep a reference to avoid garbage collection
        except Exception as e:
            print(f"Error loading image {img_path}: {e}")

def show_next_image(canvas):
    global current_image_index, synth_images
    if synth_images and current_image_index < len(synth_images) - 1:
        current_image_index += 1
        display_synth_image(canvas)

def show_previous_image(canvas):
    global current_image_index
    if synth_images and current_image_index > 0:
        current_image_index -= 1
        display_synth_image(canvas)

# Function to populate dropdown with directories from a base folder
def populate_dropdown(base_dir):
    if not os.path.exists(base_dir):
        return ["None"]
    dirs = [d for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d))]
    dirs.sort()
    return ["None"] + dirs

# Configure the grid layout for the main window
root.columnconfigure(0, weight=1)
root.rowconfigure(0, weight=1)

# Frame for the main content area
content_frame = tk.Frame(root, bg="white")
content_frame.grid(row=1, column=0, sticky="nsew")

# Frame for the navigation panel
nav_frame = tk.Frame(root, height=100, bg="lightgray")
nav_frame.grid(row=2, column=0, sticky="ew")
nav_frame.grid_columnconfigure(0, weight=1)

# Frame for the refresh button and auto-refresh checkbox
refresh_frame = tk.Frame(root, bg="lightgray")
refresh_frame.grid(row=0, column=0, sticky="ew", pady=5)

refresh_button = tk.Button(refresh_frame, text="Refresh Directories", command=refresh_directories)
refresh_button.pack(side='left', padx=5)

auto_refresh_check = tk.Checkbutton(refresh_frame, text="Auto Refresh", variable=auto_refresh)
auto_refresh_check.pack(side='left')

# Adding navigation buttons
nav_button1 = tk.Button(nav_frame, text="Extract Icons", relief="flat", command=run_extract_script)
nav_button1.grid(row=0, column=0, padx=10, pady=10)
nav_button1 = tk.Button(nav_frame, text="Extract Icons from image", relief="flat", command=run_extract_image_script)
nav_button1.grid(row=1, column=0, padx=10, pady=10)
nav_button2 = tk.Button(nav_frame, text="Class Editor", relief="flat", command=run_className_script)
nav_button2.grid(row=0, column=1, padx=10, pady=10)

nav_button3 = tk.Button(nav_frame, text="Synthetic Generator", relief="flat", command=run_synthetic_script)
nav_button3.grid(row=0, column=2, padx=10, pady=10)

nav_button3 = tk.Button(nav_frame, text="Train Model", relief="flat", command=run_training_script)
nav_button3.grid(row=0, column=3, padx=10, pady=10)

nav_button3 = tk.Button(nav_frame, text="Test Models", relief="flat", command=run_testing_script)
nav_button3.grid(row=0, column=4, padx=10, pady=10)
# Canvas and dropdown for icon_captures
icon_canvas_frame = tk.Frame(content_frame)
icon_canvas_frame.pack(side='left', padx=10, pady=10)

icon_canvas = tk.Canvas(icon_canvas_frame, width=500, height=300, bg="white")
icon_canvas.pack()

icon_dropdown_var = tk.StringVar(value="None")
icon_dropdown = ttk.Combobox(icon_canvas_frame, textvariable=icon_dropdown_var, state="readonly")
icon_dropdown['values'] = populate_dropdown('icon_captures')
icon_dropdown.pack()

# Canvas and dropdown for synth_gens
synth_canvas_frame = tk.Frame(content_frame)
synth_canvas_frame.pack(side='right', padx=10, pady=10)

synth_canvas = tk.Canvas(synth_canvas_frame, width=500, height=300, bg="white")
synth_canvas.pack()

synth_controls_frame = tk.Frame(synth_canvas_frame)
synth_controls_frame.pack()

prev_button = tk.Button(synth_controls_frame, text="<<", command=lambda: show_previous_image(synth_canvas))
prev_button.grid(row=0, column=0)

synth_dropdown_var = tk.StringVar(value="None")
synth_dropdown = ttk.Combobox(synth_controls_frame, textvariable=synth_dropdown_var, state="readonly")
synth_dropdown.grid(row=0, column=1)

next_button = tk.Button(synth_controls_frame, text=">>", command=lambda: show_next_image(synth_canvas))
next_button.grid(row=0, column=2)

# Update dropdowns and canvases based on selections
icon_dropdown.bind("<<ComboboxSelected>>", lambda e: update_icon_canvas(icon_canvas, icon_dropdown_var, 'icon_captures', synth_dropdown))
synth_dropdown.bind("<<ComboboxSelected>>", lambda e: update_synth_canvas(synth_canvas, synth_dropdown_var, 'synth_gens', os.path.join('icon_captures', icon_dropdown_var.get())))

# Positioning the main content area
root.grid_rowconfigure(0, weight=1)
root.grid_rowconfigure(1, weight=3)
root.grid_rowconfigure(2, weight=1)

# Start the Tkinter main loop
root.mainloop()
