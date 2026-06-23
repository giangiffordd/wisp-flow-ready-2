import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

API_KEY: str = os.environ.get("WISP_API_KEY", "wf-K9mP3qR7nL2xZ8vB4j")

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
