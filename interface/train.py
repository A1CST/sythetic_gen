import os
import shutil
from sklearn.model_selection import train_test_split
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinter import StringVar
import subprocess
import warnings

# Suppress libpng warnings about incorrect sRGB profiles
warnings.filterwarnings("ignore", message=".*iCCP: known incorrect sRGB profile.*")

# Create the main window
root = tk.Tk()
root.title("YOLOv5 Training Setup")

def check_annotation_files(annotation_dir, nc):
    errors_found = False
    for root, dirs, files in os.walk(annotation_dir):
        for file in files:
            if file.endswith('.txt'):
                with open(os.path.join(root, file), 'r') as f:
                    lines = f.readlines()
                    for line in lines:
                        class_id = int(line.split()[0])
                        if class_id >= nc:
                            print(f"Error: Class ID {class_id} in file {file} exceeds nc={nc - 1}")
                            errors_found = True
    if not errors_found:
        print("All annotation files are within the expected class ID range.")
    else:
        print("Errors found in annotation files.")

def browse_directory():
    dir_path = filedialog.askdirectory(initialdir=os.getcwd(), title="Select Dataset Directory")
    dataset_dir_var.set(dir_path)

def check_existing_split(dataset_dir):
    train_img_dir = os.path.join(dataset_dir, 'images', 'train')
    val_img_dir = os.path.join(dataset_dir, 'images', 'val')
    train_lbl_dir = os.path.join(dataset_dir, 'labels', 'train')
    val_lbl_dir = os.path.join(dataset_dir, 'labels', 'val')

    if all(os.path.exists(d) for d in [train_img_dir, val_img_dir, train_lbl_dir, val_lbl_dir]):
        train_images = [f for f in os.listdir(train_img_dir) if f.endswith('.png')]
        val_images = [f for f in os.listdir(val_img_dir) if f.endswith('.png')]
        train_labels = [f for f in os.listdir(train_lbl_dir) if f.endswith('.txt')]
        val_labels = [f for f in os.listdir(val_lbl_dir) if f.endswith('.txt')]
        if train_images and val_images and train_labels and val_labels:
            print("Existing train and val split found.")
            return train_img_dir, val_img_dir
    return None, None

def split_dataset(dataset_dir):
    image_dir = os.path.join(dataset_dir, 'images')
    label_dir = os.path.join(dataset_dir, 'labels')

    train_img_dir, val_img_dir = check_existing_split(dataset_dir)
    if train_img_dir and val_img_dir:
        return train_img_dir, val_img_dir

    all_images = [os.path.join(dataset_dir, f) for f in os.listdir(dataset_dir) if f.endswith('.png')]
    all_labels = [os.path.join(dataset_dir, f) for f in os.listdir(dataset_dir) if f.endswith('.txt')]

    if not all_images or not all_labels:
        messagebox.showerror("Error", "No images or labels found in the selected directory.")
        return None, None

    train_img_dir = os.path.join(image_dir, 'train')
    val_img_dir = os.path.join(image_dir, 'val')
    train_lbl_dir = os.path.join(label_dir, 'train')
    val_lbl_dir = os.path.join(label_dir, 'val')

    os.makedirs(train_img_dir, exist_ok=True)
    os.makedirs(val_img_dir, exist_ok=True)
    os.makedirs(train_lbl_dir, exist_ok=True)
    os.makedirs(val_lbl_dir, exist_ok=True)

    train_images, val_images = train_test_split(all_images, test_size=0.2, random_state=42)
    train_labels = [img.replace('.png', '.txt') for img in train_images]
    val_labels = [img.replace('.png', '.txt') for img in val_images]

    for img_path, lbl_path in zip(train_images, train_labels):
        shutil.move(img_path, os.path.join(train_img_dir, os.path.basename(img_path)))
        shutil.move(lbl_path, os.path.join(train_lbl_dir, os.path.basename(lbl_path)))

    for img_path, lbl_path in zip(val_images, val_labels):
        shutil.move(img_path, os.path.join(val_img_dir, os.path.basename(img_path)))
        shutil.move(lbl_path, os.path.join(val_lbl_dir, os.path.basename(lbl_path)))

    return train_img_dir, val_img_dir

def load_class_names(dataset_dir):
    # Correct the path to finalized_class.txt based on your structure
    class_file_path = os.path.join(dataset_dir, 'finalized_class.txt')

    class_names = []

    if os.path.exists(class_file_path):
        with open(class_file_path, 'r') as f:
            for line in f:
                parts = line.strip().split(maxsplit=1)
                if len(parts) == 2:
                    class_id, class_name = parts
                    class_names.append(class_name)
    else:
        print(f"Error: The file 'finalized_class.txt' does not exist at path: {class_file_path}")

    # Verify classes are not empty and add unique identifiers
    if not class_names:
        messagebox.showerror("Error", "No valid class names found in the finalized class file.")
        return ['icon']  # Default class name if no class file is found

    print(f"Loaded classes from finalized_class.txt: {class_names}")
    return class_names

def create_data_yaml(train_path, val_path, class_names):
    train_path = train_path.replace('\\', '/')
    val_path = val_path.replace('\\', '/')

    unique_class_names = list(set(class_names))  # Ensure class names are unique

    data_yaml_content = f"""
train: {train_path}
val: {val_path}

nc: {len(unique_class_names)}  # Number of classes
names: {unique_class_names}  # Class names
"""
    data_yaml_path = os.path.join(os.path.dirname(train_path), 'data.yaml').replace('\\', '/')
    with open(data_yaml_path, 'w') as f:
        f.write(data_yaml_content.strip())

    print(f"data.yaml created at: {data_yaml_path}")
    return data_yaml_path

def start_training():
    dataset_dir = dataset_dir_var.get()
    if not os.path.exists(dataset_dir):
        messagebox.showerror("Error", "Please select a valid dataset directory.")
        return

    class_names = load_class_names(dataset_dir)

    train_path, val_path = split_dataset(dataset_dir)
    if not train_path or not val_path:
        return

    data_yaml = create_data_yaml(train_path, val_path, class_names)

    command = [
        'python', os.path.join(YOLO_DIR, 'train.py'),
        '--img', img_size.get(),
        '--batch', batch_size.get(),
        '--epochs', epochs.get(),
        '--data', data_yaml,
        '--cfg', os.path.join(YOLO_DIR, 'models', f'{MODEL}.yaml'),
        '--weights', os.path.join(YOLO_DIR, 'weights', f'{MODEL}.pt'),
        '--name', 'icon_detection_test',
        '--device', '0',
    ]

    print(f"Running training command: {' '.join(command)}")
    result = subprocess.run(command, cwd=YOLO_DIR)

    runs_dir = os.path.join(YOLO_DIR, 'runs', 'train')
    latest_run = max([os.path.join(runs_dir, d) for d in os.listdir(runs_dir)], key=os.path.getmtime)

    best_pt_path = os.path.join(latest_run, 'weights', 'best.pt')
    if os.path.exists(best_pt_path):
        target_dir = os.path.join(dataset_dir, 'best_weights')
        os.makedirs(target_dir, exist_ok=True)
        shutil.copy(best_pt_path, target_dir)
        print(f"best.pt copied to: {target_dir}")
    else:
        print("best.pt not found. Check if the training completed successfully.")

    if result.returncode == 0:
        messagebox.showinfo("Training Complete", "Training has completed successfully.")
    else:
        messagebox.showerror("Error", "Training failed. Check the console for details.")

ROOT_DIR = os.getcwd()
YOLO_DIR = r'C:\Users\paytonmiller\PycharmProjects\Pyton\Detection\yolov5'
MODEL = 'yolov5s'
print(YOLO_DIR)

dataset_dir_var = StringVar()
img_size = StringVar(value="640")
batch_size = StringVar(value="4")
epochs = StringVar(value="2")

ttk.Label(root, text="Dataset Directory:").grid(row=0, column=0, padx=10, pady=5)
ttk.Entry(root, textvariable=dataset_dir_var, width=50).grid(row=0, column=1, padx=10, pady=5)
ttk.Button(root, text="Browse", command=browse_directory).grid(row=0, column=2, padx=10, pady=5)

ttk.Label(root, text="Image Size:").grid(row=1, column=0, padx=10, pady=5)
ttk.Entry(root, textvariable=img_size).grid(row=1, column=1, padx=10, pady=5)

ttk.Label(root, text="Batch Size:").grid(row=2, column=0, padx=10, pady=5)
ttk.Entry(root, textvariable=batch_size).grid(row=2, column=1, padx=10, pady=5)

ttk.Label(root, text="Epochs:").grid(row=3, column=0, padx=10, pady=5)
ttk.Entry(root, textvariable=epochs).grid(row=3, column=1, padx=10, pady=5)

ttk.Button(root, text="Start Training", command=start_training).grid(row=4, column=1, padx=10, pady=20)

root.mainloop()
