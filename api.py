import os
import io
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
from PIL import Image
from ultralytics import YOLO

app = Flask(__name__)
# Enable CORS so the React Native app can communicate with this API
CORS(app)

# Load the trained YOLOv8 model
MODEL_PATH = os.path.join("runs", "detect", "train-2", "weights", "best.pt")

try:
    print(f"Loading model from {MODEL_PATH}...")
    model = YOLO(MODEL_PATH)
    print("Model loaded successfully!")
except Exception as e:
    print(f"Error loading model: {e}")
    model = None

# ─── QA Routing Configuration ──────────────────────────────────────────────────
# Parent species that the model detects as whole-insect bounding boxes
PARENT_SPECIES = [
    'papilio_thoas', 'thysania_agripina', 'pomponia_imperatoria',
    'idea_lynceus', 'polyura_delphis_concha', 'papilio_palinurus',
    'papilio_karna', 'papilio_rumanzovia', 'papilio_blumei',
    'papilio_ulysses', 'phyllium_pulchrifolium', 'xylotrupes_gideon'
]

# Anatomical parts that get matched to parent specimens
PART_CLASSES = ['wing', 'antenna', 'leg', 'shell_wing', 'horn']

# Group 1: Standard Butterflies & Moths — require 4 wings + 2 antennae
GROUP_4W_2A = [
    'papilio_thoas', 'thysania_agripina', 'idea_lynceus',
    'polyura_delphis_concha', 'papilio_palinurus', 'papilio_karna',
    'papilio_rumanzovia', 'papilio_blumei'
]

# QA rules: species → required parts for PASS status
QA_RULES = {}
for sp in GROUP_4W_2A:
    QA_RULES[sp] = {'wing': 4, 'antenna': 2}

# Group 2: Pomponia Imperatoria — 4 wings + 4 legs
QA_RULES['pomponia_imperatoria'] = {'wing': 4, 'leg': 4}

# Group 3: Papilio Ulysses — 4 wings + 2 antennae (swallowtail butterfly, same wing/antenna count as GROUP_4W_2A)
QA_RULES['papilio_ulysses'] = {'wing': 4, 'antenna': 2}

# Group 4: Leaf Insect — 6 legs + 2 antennae
QA_RULES['phyllium_pulchrifolium'] = {'leg': 6, 'antenna': 2}

# Group 5: Rhino Beetle — 2 wings + 2 shell_wings + 4 legs + 1 horn
QA_RULES['xylotrupes_gideon'] = {'wing': 2, 'shell_wing': 2, 'leg': 4, 'horn': 1}


def is_center_inside(part_box, parent_box):
    """Check if the center of a part's bounding box falls inside a parent's bounding box."""
    px1, py1, px2, py2 = part_box
    bx1, by1, bx2, by2 = parent_box
    center_x = (px1 + px2) / 2
    center_y = (py1 + py2) / 2
    return (bx1 <= center_x <= bx2) and (by1 <= center_y <= by2)


def apply_qa_routing(species_name, found_parts):
    """Apply QA rules for a given species and return pass/flagged status."""
    rules = QA_RULES.get(species_name)
    if rules is None:
        # Unknown species — can't determine QA, mark as flagged
        return 'FLAGGED', {}

    is_pass = all(found_parts.get(part, 0) == count for part, count in rules.items())
    return ('PASS' if is_pass else 'FLAGGED'), rules


def format_species_name(class_name):
    """Convert underscore-separated YOLO class name to readable format.
    e.g. 'papilio_thoas' → 'Papilio thoas'
    """
    parts = class_name.split('_')
    if len(parts) >= 2:
        return parts[0].capitalize() + ' ' + ' '.join(parts[1:])
    return class_name.capitalize()


@app.route("/", methods=["GET"])
def health_check():
    return jsonify({"status": "running", "model_loaded": model is not None})


@app.route("/predict", methods=["POST"])
def predict():
    if model is None:
        return jsonify({"error": "Model not loaded"}), 500

    if "image" not in request.files:
        return jsonify({"error": "No image part in the request"}), 400

    file = request.files["image"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    try:
        # Read the image file from the request
        image_bytes = file.read()
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        width, height = image.size

        # Run inference using YOLOv8
        # conf=0.25 (minimum confidence threshold)
        results = model.predict(image, conf=0.25)

        # ── Step 1: Separate detections into parent species vs anatomical parts ──
        insects = []   # parent species bounding boxes
        parts = []     # anatomical part bounding boxes
        raw_detections = []

        for r in results:
            boxes = r.boxes
            for box in boxes:
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                conf = float(box.conf[0])
                cls_id = int(box.cls[0])
                cls_name = model.names[cls_id]

                detection = {
                    "class": cls_name,
                    "class_display": format_species_name(cls_name),
                    "confidence": conf,
                    "box": {
                        "x": x1 / width,
                        "y": y1 / height,
                        "w": (x2 - x1) / width,
                        "h": (y2 - y1) / height
                    },
                    "box_abs": {
                        "x1": x1, "y1": y1,
                        "x2": x2, "y2": y2
                    }
                }
                raw_detections.append(detection)

                if cls_name in PARENT_SPECIES:
                    insects.append({
                        "species": cls_name,
                        "confidence": conf,
                        "coords": [x1, y1, x2, y2],
                        "box_norm": detection["box"]
                    })
                elif cls_name in PART_CLASSES:
                    parts.append({
                        "name": cls_name,
                        "coords": [x1, y1, x2, y2]
                    })

        # ── Step 2: Match parts to parent species by bounding box containment ──
        specimens = []
        for insect in insects:
            found_parts = {p: 0 for p in PART_CLASSES}

            for part in parts:
                if is_center_inside(part["coords"], insect["coords"]):
                    part_name = part["name"]
                    if part_name in found_parts:
                        found_parts[part_name] += 1

            # ── Step 3: Apply QA routing rules ──
            qa_status, required_parts = apply_qa_routing(insect["species"], found_parts)

            specimens.append({
                "species": insect["species"],
                "species_display": format_species_name(insect["species"]),
                "confidence": insect["confidence"],
                "box": insect["box_norm"],
                "qa_status": qa_status,
                "parts_found": {k: v for k, v in found_parts.items() if v > 0},
                "parts_required": required_parts,
            })

        return jsonify({
            "status": "success",
            "specimens": specimens,
            "raw_detections": raw_detections,
            "total_specimens": len(specimens),
            "total_parts": len(parts),
            "image_size": {"width": width, "height": height}
        })

    except Exception as e:
        print(f"Prediction error: {e}")
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    print("Starting API server on port 5000...")
    print("QA Rules loaded for", len(QA_RULES), "species")
    # Run on all interfaces so it's accessible over the network (or Ngrok)
    app.run(host="0.0.0.0", port=5000, debug=False)
