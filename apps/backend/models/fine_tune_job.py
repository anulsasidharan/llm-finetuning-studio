import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from core.database import Base
from sqlalchemy import DateTime, Float, ForeignKey, Index, Numeric, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from models.dataset import Dataset
    from models.experiment import ExperimentRun
    from models.model_registry import ModelRegistry
    from models.user import User


class FineTuneJob(Base):
    __tablename__ = "fine_tune_jobs"
    __table_args__ = (
        Index("idx_jobs_user_id", "user_id"),
        Index("idx_jobs_status", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    dataset_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("datasets.id"),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    base_model_id: Mapped[str] = mapped_column(String(255), nullable=False)
    methodology: Mapped[str] = mapped_column(String(50), nullable=False)
    training_config: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    gpu_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    cloud_vendor: Mapped[str | None] = mapped_column(String(50), nullable=True)

    train_loss: Mapped[float | None] = mapped_column(Float, nullable=True)
    eval_loss: Mapped[float | None] = mapped_column(Float, nullable=True)
    gpu_utilization_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    vram_used_gb: Mapped[float | None] = mapped_column(Float, nullable=True)
    tokens_per_second: Mapped[float | None] = mapped_column(Float, nullable=True)

    estimated_cost_usd: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    actual_cost_usd: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user: Mapped["User"] = relationship(back_populates="fine_tune_jobs")
    dataset: Mapped["Dataset | None"] = relationship(back_populates="fine_tune_jobs")
    experiment_runs: Mapped[list["ExperimentRun"]] = relationship(back_populates="fine_tune_job")
    model_registry_entries: Mapped[list["ModelRegistry"]] = relationship(
        back_populates="fine_tune_job"
    )
