from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
import os, uuid
from datetime import date
from decimal import Decimal

from app.db.session import get_db
from app.core.settings import settings
from app.models import Vendor, Receipt, ReceiptItem
from app.services.ocr import ocr_image_to_text
from app.services.parser import parse_receipt_text

router = APIRouter()

def ensure_upload_dir():
    os.makedirs(settings.upload_dir, exist_ok=True)

@router.post("/upload")
async def upload_receipt(file: UploadFile = File(...), db: Session = Depends(get_db)):
    ensure_upload_dir()
    ext = os.path.splitext(file.filename or "file")[1].lower() or ".png"
    fname = f"{uuid.uuid4().hex}{ext}"
    fpath = os.path.join(settings.upload_dir, fname)
    with open(fpath, "wb") as f:
        f.write(await file.read())

    try:
        txt = ocr_image_to_text(fpath)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"OCR failed: {e}")

    data = parse_receipt_text(txt)
    # Upsert vendor
    vendor = db.execute(select(Vendor).where(Vendor.name == data["vendor_name"])).scalar()
    if not vendor:
        vendor = Vendor(name=data["vendor_name"])
        db.add(vendor); db.commit(); db.refresh(vendor)

    rec = Receipt(vendor_id=vendor.id, d=data["date"], currency=data["currency"], total=data["total"], raw_text=data["raw_text"], image_path=fpath)
    db.add(rec); db.commit(); db.refresh(rec)

    for it in data["items"]:
        db.add(ReceiptItem(receipt_id=rec.id, name=it["name"], qty=it["qty"], unit_price=it["unit_price"], line_total=it["line_total"], category=it["category"]))
    db.commit()

    return {"id": rec.id, "vendor": vendor.name, "date": str(rec.d), "total": float(rec.total), "items": len(data["items"])}

@router.get("/{receipt_id}")
def get_receipt(receipt_id: int, db: Session = Depends(get_db)):
    rec = db.execute(select(Receipt).where(Receipt.id == receipt_id)).scalar()
    if not rec:
        raise HTTPException(status_code=404, detail="Receipt not found")
    items = list(db.execute(select(ReceiptItem).where(ReceiptItem.receipt_id == receipt_id)).scalars().all())
    return {
        "id": rec.id,
        "vendor_id": rec.vendor_id,
        "date": str(rec.d),
        "currency": rec.currency,
        "total": float(rec.total),
        "raw_text": rec.raw_text,
        "image_path": rec.image_path,
        "items": [
            {"id": it.id, "name": it.name, "qty": it.qty, "unit_price": float(it.unit_price), "line_total": float(it.line_total), "category": it.category}
            for it in items
        ]
    }
