import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from core.database import Base
from sqlalchemy import DateTime, ForeignKey, Index, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from models.fine_tune_job import FineTuneJob
    from models.user import User


class ModelRegistry(Base):
    __tablename__ = "model_registry"
    __table_args__ = (Index("idx_registry_user", "user_id"),)

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    fine_tune_job_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("fine_tune_jobs.id"),
        nullable=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    base_model_id: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_path: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    hf_repo_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    gguf_export_path: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    vllm_endpoint: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user: Mapped["User"] = relationship(back_populates="model_registry_entries")
    fine_tune_job: Mapped["FineTuneJob | None"] = relationship(
        back_populates="model_registry_entries"
    )
