from ultralytics import YOLO
import albumentations as A
from ultralytics.data import augment as ultra_augment

# Ultralytics calls this Albumentations pipeline automatically on every training
# image, every epoch, but its defaults (Blur/MedianBlur at p=0.01) are too weak
# to matter and there's no train() kwarg to strengthen them. We patch the class
# defaults directly to target our two real failure modes: motion blur from
# shaky-hand capture, and glare from photographing a phone/monitor screen.
_original_albumentations_init = ultra_augment.Albumentations.__init__

def _patched_albumentations_init(self, p=1.0, transforms=None):
    if transforms is None:
        transforms = [
            A.MotionBlur(blur_limit=(3, 21), p=0.35),        # shaky-hand capture
            A.Defocus(radius=(1, 5), p=0.15),                # autofocus miss
            A.RandomSunFlare(p=0.2),                         # screen glare hotspot
            A.RandomBrightnessContrast(brightness_limit=0.3, contrast_limit=0.3, p=0.3),
            A.ImageCompression(quality_range=(60, 95), p=0.2),  # screen/webcam jpeg artifacts
            A.Blur(p=0.01),
            A.MedianBlur(p=0.01),
            A.ToGray(p=0.01),
            A.CLAHE(p=0.01),
            A.RandomGamma(p=0.01),
        ]
    _original_albumentations_init(self, p=p, transforms=transforms)

ultra_augment.Albumentations.__init__ = _patched_albumentations_init

# This is the Windows safety lock! Everything below it must be indented.
if __name__ == '__main__':
    
    model = YOLO('yolov8s.pt') 

    results = model.train(
        data='WISP-FLOW_Dataset_V2.3/data.yaml', 
        epochs=300,     
        patience=50,   
        imgsz=1024,
        
        batch=4,
        
        # Filters
        hsv_h=0.015,       
        hsv_s=0.7,         
        hsv_v=0.4,         
        
        # Geometry
        degrees=180,       
        flipud=0.5,        
        fliplr=0.5,        
        scale=0.5,       # ADDED: Helps with varying camera distance
        translate=0.1,
        
        perspective=0.0005, # Simulates the phone being tilted/angled instead of perfectly flat
        shear=2.0,          # Skews the image slightly, simulating weird camera angles
        
        # Advanced QA 
        mosaic=1.0,        
        erasing=0.2        
    )