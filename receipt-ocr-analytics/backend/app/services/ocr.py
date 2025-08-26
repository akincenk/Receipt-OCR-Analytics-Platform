import pytesseract
from PIL import Image

def ocr_image_to_text(path: str) -> str:
    # Simple wrapper around Tesseract
    img = Image.open(path)
    txt = pytesseract.image_to_string(img)
    return txt or ""
