import uuid
from datetime import datetime

from core.database import Base
from sqlalchemy import DateTime, Index, Integer, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column


class GpuPricing(Base):
    __tablename__ = "gpu_pricing"
    __table_args__ = (Index("idx_gpu_pricing_vendor_gpu_type", "vendor", "gpu_type", unique=True),)

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    vendor: Mapped[str] = mapped_column(String(50), nullable=False)
    gpu_type: Mapped[str] = mapped_column(String(100), nullable=False)
    vram_gb: Mapped[int] = mapped_column(Integer, nullable=False)
    price_per_hour_usd: Mapped[float] = mapped_column(Numeric(10, 4), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
