from sqlalchemy import String, Integer, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from app.db.session import Base

class Vendor(Base):
    __tablename__ = "vendors"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    created_at: Mapped = mapped_column(DateTime(timezone=True), server_default=func.now())
