from fastapi import UploadFile, HTTPException, status
from config import MAX_UPLOAD_BYTES, ALLOWED_MIME_TYPES


async def validate_image(file: UploadFile) -> None:
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"File type '{file.content_type}' not allowed. Send jpeg, png, webp, or heif.",
        )
    contents = await file.read()
    if len(contents) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large — maximum is {MAX_UPLOAD_BYTES // (1024 * 1024)} MB.",
        )
    await file.seek(0)
