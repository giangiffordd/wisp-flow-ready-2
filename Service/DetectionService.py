import os
import base64
import cv2
import numpy as np
from typing import Optional
from ultralytics import YOLO

from Service.QAService import (
    PARENT_SPECIES, PART_CLASSES, apply_qa_routing, format_species_name,
)
from Service.ImageService import (
    PART_COLORS, SPECIES_COLOR,
    draw_rounded_rect, draw_label, is_center_inside,
)
from config import BLUR_THRESHOLD, SCORE_WIDTH

# Only checkpoint that actually exists on disk for this project copy.
MODEL_PATH: str = os.path.join("runs", "detect", "train-2", "weights", "best.pt")


def sharpness_score(frame: np.ndarray) -> float:
    """Laplacian-variance blur score, computed on a resized copy so it stays
    meaningful regardless of the uploading phone's camera resolution."""
    h, w = frame.shape[:2]
    scale = SCORE_WIDTH / w
    resized = cv2.resize(frame, (SCORE_WIDTH, int(h * scale)))
    gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
    return cv2.Laplacian(gray, cv2.CV_64F).var()


class DetectionService:
    def __init__(self) -> None:
        self.model: Optional[YOLO] = None
        self._load_model()

    def _load_model(self) -> None:
        try:
            print(f"Loading model from {MODEL_PATH}...")
            self.model = YOLO(MODEL_PATH)
            print("Model loaded successfully!")
        except Exception as load_error:
            print(f"Error loading model: {load_error}")
            self.model = None

    @property
    def is_ready(self) -> bool:
        return self.model is not None

    def run_detection(self, image_bytes: bytes) -> dict:
        np_arr = np.frombuffer(image_bytes, np.uint8)
        frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        if frame is None:
            raise ValueError("Invalid image file")

        blur_score = sharpness_score(frame)
        if blur_score < BLUR_THRESHOLD:
            return {
                "status": "retake",
                "reason": "Image too blurry, please retake the photo.",
                "sharpness": blur_score,
            }

        height, width = frame.shape[:2]
        annotated = frame.copy()
        yolo_results = self.model.predict(frame, conf=0.25)

        insects, parts, raw_detections = self._parse_detections(yolo_results, width, height)
        self._annotate_frame(annotated, insects, parts, width)
        specimens = self._build_specimens(insects, parts, width, height, annotated)

        _, buffer = cv2.imencode('.jpg', annotated, [cv2.IMWRITE_JPEG_QUALITY, 80])
        b64_image = base64.b64encode(buffer).decode('utf-8')

        return {
            "status": "success",
            "specimens": specimens,
            "raw_detections": raw_detections,
            "total_specimens": len(specimens),
            "total_parts": len(parts),
            "image_size": {"width": width, "height": height},
            "annotated_image_base64": b64_image,
        }

    def _parse_detections(self, yolo_results, width: int, height: int) -> tuple:
        insects, parts, raw_detections = [], [], []
        for result in yolo_results:
            for box in result.boxes:
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                conf = float(box.conf[0])
                # The trained model returns Title-Case-with-spaces for the
                # beetle classes (e.g. "Heteropteryx dilatata") but
                # lowercase_with_underscores for the butterfly/part classes —
                # normalize everything so it matches PARENT_SPECIES/PART_CLASSES.
                raw_cls_name = self.model.names[int(box.cls[0])]
                cls_name = raw_cls_name.lower().replace(' ', '_')

                raw_detections.append({
                    "class": cls_name,
                    "class_display": format_species_name(cls_name),
                    "confidence": conf,
                    "box": {"x": x1/width, "y": y1/height, "w": (x2-x1)/width, "h": (y2-y1)/height},
                    "box_abs": {"x1": x1, "y1": y1, "x2": x2, "y2": y2},
                })

                if cls_name in PARENT_SPECIES:
                    insects.append({"species": cls_name, "confidence": conf, "coords": [x1, y1, x2, y2]})
                elif cls_name in PART_CLASSES:
                    parts.append({"name": cls_name, "confidence": conf, "coords": [x1, y1, x2, y2]})
                # Anything matching neither list (e.g. graphium_weiskei) is
                # recorded in raw_detections only and ignored by QA routing.

        return insects, parts, raw_detections

    def _annotate_frame(self, annotated, insects: list, parts: list, width: int) -> None:
        font_scale_species = max(0.6, width / 1800.0)
        thickness_species = max(1, int(width / 900.0))
        font_scale_part = max(0.5, width / 2000.0)
        thickness_part = max(1, int(width / 1200.0))

        for insect in insects:
            bx1, by1, bx2, by2 = [int(c) for c in insect['coords']]
            draw_rounded_rect(annotated, (bx1, by1), (bx2, by2), SPECIES_COLOR, 3, radius=12)
            label = f"{format_species_name(insect['species'])} {insect['confidence']:.2f}"
            draw_label(annotated, label, (bx1, by1 - 4), SPECIES_COLOR, font_scale=font_scale_species, thickness=thickness_species)

        for part in parts:
            px1, py1, px2, py2 = [int(c) for c in part['coords']]
            color = PART_COLORS.get(part['name'], (200, 200, 200))
            cv2.rectangle(annotated, (px1, py1), (px2, py2), color, max(2, int(width / 600.0)))
            draw_label(annotated, f"{part['name']} {part['confidence']:.2f}", (px1, py1 - 2), color, font_scale=font_scale_part, thickness=thickness_part)

    def _build_specimens(self, insects: list, parts: list, width: int, height: int, annotated) -> list:
        specimens = []
        for insect in insects:
            found_parts = {p: 0 for p in PART_CLASSES}
            for part in parts:
                if is_center_inside(part["coords"], insect["coords"]):
                    found_parts[part["name"]] = found_parts.get(part["name"], 0) + 1

            qa_status, required_parts = apply_qa_routing(insect["species"], found_parts)

            bx1, by1, bx2, by2 = [int(c) for c in insect['coords']]
            status_color = (0, 200, 0) if qa_status == 'PASS' else (0, 0, 230)
            font_scale_status = max(0.8, width / 1200.0)
            thickness_status = max(2, int(width / 600.0))
            status_y = by2 + int(30 * font_scale_status)
            cv2.putText(annotated, f"STATUS: {qa_status}", (bx1, status_y),
                        cv2.FONT_HERSHEY_SIMPLEX, font_scale_status, status_color, thickness_status, cv2.LINE_AA)

            specimens.append({
                "species": insect["species"],
                "species_display": format_species_name(insect["species"]),
                "confidence": insect["confidence"],
                "box": {
                    "x": insect["coords"][0] / width,
                    "y": insect["coords"][1] / height,
                    "w": (insect["coords"][2] - insect["coords"][0]) / width,
                    "h": (insect["coords"][3] - insect["coords"][1]) / height,
                },
                "qa_status": qa_status,
                "parts_found": {k: v for k, v in found_parts.items() if v > 0},
                "parts_required": required_parts,
            })
        return specimens


detection_service = DetectionService()
