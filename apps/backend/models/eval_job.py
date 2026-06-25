import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from core.database import Base
from sqlalchemy import DateTime, ForeignKey, Index, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from models.user import User


class EvalJob(Base):
    __tablename__ = "eval_jobs"
    __table_args__ = (
        Index("idx_eval_jobs_user_id", "user_id"),
        Index("idx_eval_jobs_status", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    eval_type: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    base_model_id: Mapped[str] = mapped_column(String(255), nullable=False)
    finetuned_model_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    prompts: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    benchmarks: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    num_fewshot: Mapped[int | None] = mapped_column(nullable=True)
    sample_limit: Mapped[float | None] = mapped_column(nullable=True)
    max_new_tokens: Mapped[int | None] = mapped_column(nullable=True)
    result: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    error_message: Mapped[str | None] = mapped_column(String(2048), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user: Mapped["User"] = relationship(back_populates="eval_jobs")
