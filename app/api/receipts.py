import io
import os
import uuid
from datetime import date

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from PIL import Image, UnidentifiedImageError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.settings import settings
from app.db.session import get_db
from app.models import Receipt, ReceiptItem, Vendor
from app.services.ocr import OCRUnavailable, ocr_image_to_text
from app.services.parser import parse_receipt_text

router = APIRouter()

# Pillow format name -> file extension. Anything else is rejected.
ALLOWED_FORMATS = {"PNG": ".png", "JPEG": ".jpg", "TIFF": ".tif", "WEBP": ".webp"}


def _read_limited(file: UploadFile) -> bytes:
    data = file.file.read(settings.max_upload_bytes + 1)
    if len(data) > settings.max_upload_bytes:
        raise HTTPException(status_code=413, detail=f"File larger than {settings.max_upload_bytes} bytes")
    return data


def _save_image(data: bytes) -> str:
    """Check the bytes really are an allowed image type, then store them under a random name."""
    try:
        with Image.open(io.BytesIO(data)) as img:
            fmt = img.format
            img.verify()
    except (UnidentifiedImageError, OSError, SyntaxError) as e:
        raise HTTPException(status_code=415, detail="File is not a valid image") from e
    if fmt not in ALLOWED_FORMATS:
        raise HTTPException(status_code=415, detail=f"Unsupported image type; allowed: {', '.join(ALLOWED_FORMATS)}")
    os.makedirs(settings.upload_dir, exist_ok=True)
    path = os.path.join(settings.upload_dir, uuid.uuid4().hex + ALLOWED_FORMATS[fmt])
    with open(path, "wb") as f:
        f.write(data)
    return path


@router.post("/upload", status_code=201)
def upload_receipt(file: UploadFile = File(...), db: Session = Depends(get_db)):
    path = _save_image(_read_limited(file))
    try:
        txt = ocr_image_to_text(path)
    except OCRUnavailable as e:
        os.remove(path)
        raise HTTPException(status_code=503, detail="OCR engine unavailable") from e

    data = parse_receipt_text(txt)
    vendor = db.execute(select(Vendor).where(Vendor.name == data["vendor_name"])).scalar()
    if not vendor:
        vendor = Vendor(name=data["vendor_name"])
        db.add(vendor)
        db.flush()

    rec = Receipt(
        vendor_id=vendor.id,
        # No date found on the receipt: use the upload date and report date_detected=False.
        d=data["date"] or date.today(),
        currency=data["currency"],
        total=data["total"],
        raw_text=data["raw_text"],
        image_path=path,
    )
    db.add(rec)
    db.flush()
    db.add_all(ReceiptItem(receipt_id=rec.id, **it) for it in data["items"])
    db.commit()

    return {
        "id": rec.id,
        "vendor": vendor.name,
        "date": rec.d.isoformat(),
        "date_detected": data["date"] is not None,
        "total": float(rec.total),
        "items": len(data["items"]),
    }


@router.get("/{receipt_id}")
def get_receipt(receipt_id: int, db: Session = Depends(get_db)):
    rec = db.get(Receipt, receipt_id)
    if not rec:
        raise HTTPException(status_code=404, detail="Receipt not found")
    items = db.execute(select(ReceiptItem).where(ReceiptItem.receipt_id == receipt_id).order_by(ReceiptItem.id)).scalars()
    return {
        "id": rec.id,
        "vendor_id": rec.vendor_id,
        "date": rec.d.isoformat(),
        "currency": rec.currency,
        "total": float(rec.total),
        "raw_text": rec.raw_text,
        "items": [
            {
                "id": it.id,
                "name": it.name,
                "qty": it.qty,
                "unit_price": float(it.unit_price),
                "line_total": float(it.line_total),
                "category": it.category,
            }
            for it in items
        ],
    }
