from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import Receipt, ReceiptItem, Vendor

router = APIRouter()


def _date_filter(q, date_from: date | None, date_to: date | None):
    if date_from and date_to and date_from > date_to:
        raise HTTPException(status_code=400, detail="'from' must not be after 'to'")
    if date_from:
        q = q.where(Receipt.d >= date_from)
    if date_to:
        q = q.where(Receipt.d <= date_to)
    return q


@router.get("/summary")
def summary(
    date_from: date | None = Query(None, alias="from"),
    date_to: date | None = Query(None, alias="to"),
    db: Session = Depends(get_db),
):
    q = _date_filter(select(func.count(Receipt.id), func.coalesce(func.sum(Receipt.total), 0)), date_from, date_to)
    count, total = db.execute(q).one()
    avg = total / count if count else 0
    return {"receipts": count, "total_spend": round(float(total), 2), "avg_per_receipt": round(float(avg), 2)}


@router.get("/by-vendor")
def by_vendor(
    date_from: date | None = Query(None, alias="from"),
    date_to: date | None = Query(None, alias="to"),
    db: Session = Depends(get_db),
):
    spend = func.sum(Receipt.total)
    q = select(Vendor.name, spend).join(Receipt, Receipt.vendor_id == Vendor.id).group_by(Vendor.name)
    rows = db.execute(_date_filter(q, date_from, date_to).order_by(spend.desc(), Vendor.name)).all()
    return [{"vendor": name, "total_spend": round(float(total), 2)} for name, total in rows]


@router.get("/by-category")
def by_category(
    date_from: date | None = Query(None, alias="from"),
    date_to: date | None = Query(None, alias="to"),
    db: Session = Depends(get_db),
):
    spend = func.sum(ReceiptItem.line_total)
    q = select(ReceiptItem.category, spend).join(Receipt, Receipt.id == ReceiptItem.receipt_id).group_by(ReceiptItem.category)
    rows = db.execute(_date_filter(q, date_from, date_to).order_by(spend.desc(), ReceiptItem.category)).all()
    return [{"category": cat, "total_spend": round(float(total), 2)} for cat, total in rows]
