import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from Controller.PredictController import router as predict_router
from Controller.ScanController import router as scan_router
from Controller.UtilController import router as util_router
from Controller.BarcodeController import router as barcode_router
from Repository.ScanRepository import init_db
from limiter import limiter

app = FastAPI(
    title="WISP-FLOW AI Backend",
    description="FastAPI server for YOLOv8 object detection and QA routing with OpenCV rendering.",
    version="2.0.0",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(predict_router)
app.include_router(scan_router)
app.include_router(util_router)
app.include_router(barcode_router)

init_db()

if __name__ == "__main__":
    import uvicorn
    # Reload is for local dev only — it spawns a watcher + worker process,
    # which complicates pkill-based stop/restart in scripts/rollback.sh and
    # would trigger restarts on every `git pull` during deployment.
    reload_enabled = os.environ.get("WISP_RELOAD", "false").lower() == "true"
    print("Starting WISP-FLOW AI server on port 8000...")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=reload_enabled)
