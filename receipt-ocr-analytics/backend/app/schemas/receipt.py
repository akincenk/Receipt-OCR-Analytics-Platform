from pydantic import BaseModel
from datetime import date
from decimal import Decimal

class ReceiptItemOut(BaseModel):
    id: int
    name: str
    qty: int
    unit_price: Decimal
    line_total: Decimal
    category: str
    class Config:
        from_attributes = True

class ReceiptOut(BaseModel):
    id: int
    d: date
    currency: str
    total: Decimal
    raw_text: str | None = None
    image_path: str | None = None
    class Config:
        from_attributes = True
