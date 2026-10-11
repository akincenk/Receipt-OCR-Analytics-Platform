"""Insert one demo receipt (no OCR involved)."""
from datetime import date, timedelta
from decimal import Decimal

from app.db.session import SessionLocal
from app.models import Receipt, ReceiptItem, Vendor


def run():
    with SessionLocal() as db:
        v = Vendor(name="DemoMart")
        db.add(v)
        db.flush()
        r = Receipt(vendor_id=v.id, d=date.today() - timedelta(days=3), total=Decimal("21.50"), raw_text="Demo seed")
        db.add(r)
        db.flush()
        db.add_all([
            ReceiptItem(receipt_id=r.id, name="Drip Coffee 12oz", qty=1, unit_price=Decimal("3.50"),
                        line_total=Decimal("3.50"), category="coffee"),
            ReceiptItem(receipt_id=r.id, name="Turkey Sandwich", qty=1, unit_price=Decimal("8.00"),
                        line_total=Decimal("8.00"), category="deli"),
            ReceiptItem(receipt_id=r.id, name="Bagel", qty=2, unit_price=Decimal("5.00"),
                        line_total=Decimal("10.00"), category="bakery"),
        ])
        db.commit()
        print("Seed completed.")


if __name__ == "__main__":
    run()
