import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from core.database import Base
from sqlalchemy import Boolean, DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from models.dataset import Dataset
    from models.eval_job import EvalJob
    from models.experiment import Experiment
    from models.fine_tune_job import FineTuneJob
    from models.model_registry import ModelRegistry


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    datasets: Mapped[list["Dataset"]] = relationship(back_populates="user")
    fine_tune_jobs: Mapped[list["FineTuneJob"]] = relationship(back_populates="user")
    experiments: Mapped[list["Experiment"]] = relationship(back_populates="user")
    model_registry_entries: Mapped[list["ModelRegistry"]] = relationship(back_populates="user")
    eval_jobs: Mapped[list["EvalJob"]] = relationship(back_populates="user")
