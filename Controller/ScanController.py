from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from Repository.ScanRepository import save_scan_record
from Dependencies.auth import require_api_key
from config import MAX_UPLOAD_BYTES

router = APIRouter()


class SaveScanRequest(BaseModel):
    annotated_image_base64: str
    species: str
    confidence: float
    qa_status: str


@router.post("/save_scan", dependencies=[Depends(require_api_key)])
async def save_scan(scan_request: SaveScanRequest) -> dict:
    # Rough base64 -> raw byte size (4 chars ~= 3 bytes), checked before any
    # decode/write so an oversized payload can't be used to fill disk.
    if len(scan_request.annotated_image_base64) * 3 // 4 > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"Image too large — maximum is {MAX_UPLOAD_BYTES // (1024 * 1024)} MB.",
        )
    try:
        return save_scan_record(
            annotated_image_base64=scan_request.annotated_image_base64,
            species=scan_request.species,
            confidence=scan_request.confidence,
            qa_status=scan_request.qa_status,
        )
    except Exception as unexpected_error:
        print(f"Error saving scan: {unexpected_error}")
        raise HTTPException(status_code=500, detail=str(unexpected_error))
