from pydantic import BaseModel
from decimal import Decimal

class SummaryOut(BaseModel):
    total_spend: Decimal
    receipts: int
    avg_per_receipt: Decimal
