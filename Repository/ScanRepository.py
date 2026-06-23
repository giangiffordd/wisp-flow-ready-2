import os
import uuid
import base64
import sqlite3
import datetime
from typing import Dict

DB_PATH: str = "scans.db"
SAVE_DIR: str = "saved_images"

os.makedirs(SAVE_DIR, exist_ok=True)


def init_db() -> None:
    conn = sqlite3.connect(DB_PATH)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS scan_history (
            id         TEXT PRIMARY KEY,
            species    TEXT,
            confidence REAL,
            timestamp  TEXT,
            image_path TEXT,
            qa_status  TEXT
        )
    ''')
    conn.commit()
    conn.close()


def save_scan_record(
    annotated_image_base64: str,
    species: str,
    confidence: float,
    qa_status: str,
) -> Dict[str, str]:
    image_data = base64.b64decode(annotated_image_base64)
    scan_id = str(uuid.uuid4())
    timestamp_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{scan_id}_{timestamp_str}.jpg"
    filepath = os.path.join(SAVE_DIR, filename)

    with open(filepath, "wb") as image_file:
        image_file.write(image_data)

    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT INTO scan_history (id, species, confidence, timestamp, image_path, qa_status) VALUES (?, ?, ?, ?, ?, ?)",
        (scan_id, species, confidence, datetime.datetime.now().isoformat(), filepath, qa_status),
    )
    conn.commit()
    conn.close()

    return {"status": "success", "id": scan_id, "filepath": filepath}
