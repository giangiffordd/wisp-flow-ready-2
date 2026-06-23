import io
from fastapi import APIRouter, File, UploadFile, Depends
from fastapi.responses import JSONResponse
from PIL import Image, ImageEnhance
from Dependencies.auth import require_api_key
from Dependencies.upload import validate_image

router = APIRouter()


def try_pyzbar(image):
    try:
        from pyzbar import pyzbar
        results = pyzbar.decode(image)
        return results[0].data.decode("utf-8") if results else None
    except Exception:
        return None


def try_zxing(image):
    try:
        import zxingcpp
        results = zxingcpp.read_barcodes(image)
        return results[0].text if results else None
    except Exception:
        return None


@router.post("/decode_barcode", dependencies=[Depends(require_api_key)])
async def decode_barcode(file: UploadFile = File(...)):
    await validate_image(file)
    contents = await file.read()
    img = Image.open(io.BytesIO(contents)).convert("RGB")

    data = try_pyzbar(img) or try_zxing(img)

    if not data:
        gray = img.convert("L")
        enhanced = ImageEnhance.Contrast(ImageEnhance.Sharpness(gray).enhance(3.0)).enhance(3.0)
        processed = enhanced.convert("RGB")
        data = try_pyzbar(processed) or try_zxing(processed)

    if data:
        return JSONResponse({"data": data})
    return JSONResponse({"data": None, "error": "No barcode found"})
