from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Request
from fastapi.responses import JSONResponse

from Service.DetectionService import detection_service
from Dependencies.auth import require_api_key
from Dependencies.upload import validate_image
from limiter import limiter

router = APIRouter()


@router.get("/")
async def health_check() -> dict:
    return {"status": "running", "model_loaded": detection_service.is_ready}


@router.post("/predict", dependencies=[Depends(require_api_key)])
@limiter.limit("30/minute")
async def predict(request: Request, image: UploadFile = File(...)) -> JSONResponse:
    await validate_image(image)
    if not detection_service.is_ready:
        raise HTTPException(status_code=500, detail="Model not loaded")
    try:
        image_bytes = await image.read()
        result = detection_service.run_detection(image_bytes)
        return JSONResponse(content=result)
    except ValueError as bad_image_error:
        raise HTTPException(status_code=400, detail=str(bad_image_error))
    except Exception as unexpected_error:
        print(f"Prediction error: {unexpected_error}")
        raise HTTPException(status_code=500, detail=str(unexpected_error))
