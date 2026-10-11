from datetime import date, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models import Vendor, Receipt, ReceiptItem

def run():
    db: Session = SessionLocal()
    try:
        v = Vendor(name="DemoMart")
        db.add(v); db.commit(); db.refresh(v)

        d0 = date.today() - timedelta(days=3)
        r = Receipt(vendor_id=v.id, d=d0, currency="USD", total=Decimal("21.50"), raw_text="Demo seed", image_path=None)
        db.add(r); db.commit(); db.refresh(r)

        items = [
            ReceiptItem(receipt_id=r.id, name="Drip Coffee 12oz", qty=1, unit_price=Decimal("3.50"), line_total=Decimal("3.50"), category="coffee"),
            ReceiptItem(receipt_id=r.id, name="Turkey Sandwich", qty=1, unit_price=Decimal("8.00"), line_total=Decimal("8.00"), category="deli"),
            ReceiptItem(receipt_id=r.id, name="Bagel", qty=2, unit_price=Decimal("5.00"), line_total=Decimal("10.00"), category="bakery"),
        ]
        db.add_all(items); db.commit()
        print("Seed completed.")
    finally:
        db.close()

if __name__ == "__main__":
    run()
