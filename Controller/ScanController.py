from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from Repository.ScanRepository import save_scan_record

router = APIRouter()


class SaveScanRequest(BaseModel):
    annotated_image_base64: str
    species: str
    confidence: float
    qa_status: str


@router.post("/save_scan")
async def save_scan(scan_request: SaveScanRequest) -> dict:
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
