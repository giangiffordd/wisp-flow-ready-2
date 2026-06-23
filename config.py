import os
from typing import Optional

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# No hardcoded fallback: a leaked default here would be a live credential
# sitting in a public repo. Falls back to None (not "") so an attacker
# sending an empty X-API-Key header -- a real string, never None -- can
# never match by accident; missing WISP_API_KEY means every request is
# rejected (fail closed) rather than silently falling back to a known value.
API_KEY: Optional[str] = os.environ.get("WISP_API_KEY")

MAX_UPLOAD_BYTES: int = 10 * 1024 * 1024  # 10 MB

ALLOWED_MIME_TYPES: set = {
    "image/jpeg",
    "image/png",
    "image/webp",
    "image/heif",
    "image/heic",
}

# Laplacian-variance cutoff below which a photo is rejected as "too blurry".
# Score is computed after resizing to SCORE_WIDTH, so it stays meaningful
# regardless of the uploading phone's camera resolution.
BLUR_THRESHOLD: float = 140.0
SCORE_WIDTH: int = 800
