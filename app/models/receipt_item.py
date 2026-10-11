from decimal import Decimal

from sqlalchemy import ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class ReceiptItem(Base):
    __tablename__ = "receipt_items"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    receipt_id: Mapped[int] = mapped_column(ForeignKey("receipts.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(255))
    qty: Mapped[int] = mapped_column(Integer, default=1, server_default="1")
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0, server_default="0")
    line_total: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0, server_default="0")
    category: Mapped[str] = mapped_column(String(64), default="other", server_default="other")
