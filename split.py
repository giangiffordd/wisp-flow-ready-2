import os
import random
import shutil

# 1. Point exactly to your folder setup
dataset_folder = 'WISP-FLOW_Dataset_V2.3'
source_dir = os.path.join(dataset_folder, 'obj_train_data') # Changed to your folder name!

train_img_dir = os.path.join(dataset_folder, 'train/images')
train_lbl_dir = os.path.join(dataset_folder, 'train/labels')
val_img_dir = os.path.join(dataset_folder, 'val/images')
val_lbl_dir = os.path.join(dataset_folder, 'val/labels')

# Build the YOLO folders automatically
for folder in [train_img_dir, train_lbl_dir, val_img_dir, val_lbl_dir]:
    os.makedirs(folder, exist_ok=True)

# 2. Find files that are IMAGES (Files that do NOT end in .txt)
ignored_files = ['classes.txt', 'obj.names', 'desktop.ini', 'data.yaml']
images = [
    f for f in os.listdir(source_dir) 
    if os.path.isfile(os.path.join(source_dir, f)) 
    and not f.endswith('.txt') 
    and f not in ignored_files
]

if len(images) == 0:
    print(f"CRITICAL ERROR: No image files found inside '{source_dir}'.")
    exit()

# Shuffle and split 80/20
random.seed(42) 
random.shuffle(images)

split_index = int(len(images) * 0.8)
train_images = images[:split_index]
val_images = images[split_index:]

def copy_files(file_list, dest_img_dir, dest_lbl_dir):
    count = 0
    for img_name in file_list:
        # Match the exact image name to its text file
        lbl_name = img_name + '.txt'
        
        img_src = os.path.join(source_dir, img_name)
        lbl_src = os.path.join(source_dir, lbl_name)
        
        if os.path.exists(lbl_src):
            shutil.copy(img_src, os.path.join(dest_img_dir, img_name))
            shutil.copy(lbl_src, os.path.join(dest_lbl_dir, lbl_name))
            count += 1
        else:
            # Fallback if the image actually had an extension
            alt_lbl_name = os.path.splitext(img_name)[0] + '.txt'
            alt_lbl_src = os.path.join(source_dir, alt_lbl_name)
            if os.path.exists(alt_lbl_src):
                shutil.copy(img_src, os.path.join(dest_img_dir, img_name))
                shutil.copy(alt_lbl_src, os.path.join(dest_lbl_dir, alt_lbl_name))
                count += 1
            else:
                print(f"Warning: {img_name} has no matching text file. Skipping.")
    return count

print(f"Starting split of {len(images)} total images from 'obj_train_data'...")
train_count = copy_files(train_images, train_img_dir, train_lbl_dir)
print(f"Successfully copied {train_count} images/labels to TRAIN.")

val_count = copy_files(val_images, val_img_dir, val_lbl_dir)
print(f"Successfully copied {val_count} images/labels to VAL.")
print("Data split complete! You are ready to run train.py.") 