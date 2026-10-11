from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from datetime import date
from decimal import Decimal

from app.db.session import get_db
from app.models import Receipt, Vendor, ReceiptItem

router = APIRouter()

@router.get("/summary")
def summary(
    date_from: str | None = Query(None, alias="from"),
    date_to: str | None = Query(None, alias="to"),
    db: Session = Depends(get_db),
):
    q = select(func.count(Receipt.id), func.coalesce(func.sum(Receipt.total), 0))
    if date_from:
        q = q.where(Receipt.d >= date.fromisoformat(date_from))
    if date_to:
        q = q.where(Receipt.d <= date.fromisoformat(date_to))
    count, total = db.execute(q).first()
    count = int(count or 0)
    total = Decimal(total or 0)
    avg = (total / count) if count else Decimal("0")
    return {"receipts": count, "total_spend": float(total), "avg_per_receipt": float(avg)}

@router.get("/by-vendor")
def by_vendor(db: Session = Depends(get_db)):
    rows = db.execute(
        select(Vendor.name, func.coalesce(func.sum(Receipt.total), 0)).join(Receipt, Receipt.vendor_id == Vendor.id).group_by(Vendor.name)
    ).all()
    return [{"vendor": r[0], "total_spend": float(r[1])} for r in rows]

@router.get("/by-category")
def by_category(db: Session = Depends(get_db)):
    rows = db.execute(
        select(ReceiptItem.category, func.coalesce(func.sum(ReceiptItem.line_total), 0)).group_by(ReceiptItem.category)
    ).all()
    return [{"category": r[0], "total_spend": float(r[1])} for r in rows]
