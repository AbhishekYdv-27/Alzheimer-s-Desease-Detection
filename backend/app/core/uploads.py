from io import BytesIO
from pathlib import Path
import tempfile
import warnings

from fastapi import HTTPException, UploadFile, status
from PIL import Image, UnidentifiedImageError
from backend.app.core.config import settings


MAX_UPLOAD_SIZE_BYTES = settings.max_upload_size_bytes
MAX_IMAGE_PIXELS = settings.max_image_pixels
if MAX_UPLOAD_SIZE_BYTES < 1 or MAX_IMAGE_PIXELS < 1:
    raise ValueError("Image upload limits must be positive integers")

SUPPORTED_FORMATS = {
    "JPEG": ".jpg",
    "PNG": ".png",
    "BMP": ".bmp",
    "TIFF": ".tiff",
}


async def save_validated_upload(file: UploadFile) -> str:
    content = await file.read(MAX_UPLOAD_SIZE_BYTES + 1)
    if not content:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded image is empty")
    if len(content) > MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail=f"Image exceeds the {MAX_UPLOAD_SIZE_BYTES}-byte upload limit",
        )

    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(BytesIO(content)) as image:
                image_format = image.format
                if image_format not in SUPPORTED_FORMATS:
                    raise HTTPException(
                        status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                        detail="Supported image formats are JPEG, PNG, BMP, and TIFF",
                    )
                if image.width <= 0 or image.height <= 0 or image.width * image.height > MAX_IMAGE_PIXELS:
                    raise HTTPException(
                        status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                        detail=f"Image dimensions exceed the {MAX_IMAGE_PIXELS}-pixel limit",
                    )
                image.verify()

            with Image.open(BytesIO(content)) as image:
                image.load()
    except HTTPException:
        raise
    except (Image.DecompressionBombError, Image.DecompressionBombWarning, UnidentifiedImageError, OSError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is not a valid, decodable image",
        ) from exc

    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=SUPPORTED_FORMATS[image_format],
        ) as temp_file:
            temp_file.write(content)
            temp_path = temp_file.name
        return temp_path
    except OSError:
        if temp_path:
            Path(temp_path).unlink(missing_ok=True)
        raise
