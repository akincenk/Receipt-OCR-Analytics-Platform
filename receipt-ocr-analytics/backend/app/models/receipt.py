from sqlalchemy import Integer, ForeignKey, Date, String, Numeric, Text, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from app.db.session import Base

class Receipt(Base):
    __tablename__ = "receipts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    vendor_id: Mapped[int] = mapped_column(ForeignKey("vendors.id", ondelete="SET NULL"))
    d: Mapped = mapped_column(Date, nullable=False)
    currency: Mapped[str] = mapped_column(String(8), default="USD")
    total: Mapped = mapped_column(Numeric(12,2), default=0)
    raw_text: Mapped[str] = mapped_column(Text)
    image_path: Mapped[str] = mapped_column(String(512), nullable=True)
    created_at: Mapped = mapped_column(DateTime(timezone=True), server_default=func.now())
