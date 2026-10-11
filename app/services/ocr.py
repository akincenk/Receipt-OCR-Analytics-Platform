import pytesseract
from PIL import Image, ImageOps


class OCRUnavailable(RuntimeError):
    """The Tesseract binary is missing or failed to run."""


def ocr_image_to_text(path: str) -> str:
    try:
        with Image.open(path) as img:
            gray = ImageOps.grayscale(img)
            # Tesseract misreads small text (e.g. the sample's vendor line); upscaling narrow images fixes that.
            # ponytail: fixed 2x below 1500px wide; switch to DPI-aware scaling if real scans vary a lot.
            if gray.width < 1500:
                gray = gray.resize((gray.width * 2, gray.height * 2), Image.LANCZOS)
            return pytesseract.image_to_string(gray) or ""
    except (pytesseract.TesseractNotFoundError, pytesseract.TesseractError) as e:
        raise OCRUnavailable(str(e)) from e
