"""add eval_jobs table

Revision ID: 8f2c1a6e4d3b
Revises: 5d716f49b7ac
Create Date: 2026-06-25 09:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "8f2c1a6e4d3b"
down_revision: str | None = "5d716f49b7ac"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "eval_jobs",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("eval_type", sa.String(length=20), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("base_model_id", sa.String(length=255), nullable=False),
        sa.Column("finetuned_model_id", sa.String(length=255), nullable=True),
        sa.Column("prompts", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("benchmarks", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("num_fewshot", sa.Integer(), nullable=True),
        sa.Column("sample_limit", sa.Float(), nullable=True),
        sa.Column("max_new_tokens", sa.Integer(), nullable=True),
        sa.Column("result", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("error_message", sa.String(length=2048), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_eval_jobs_user_id", "eval_jobs", ["user_id"], unique=False)
    op.create_index("idx_eval_jobs_status", "eval_jobs", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index("idx_eval_jobs_status", table_name="eval_jobs")
    op.drop_index("idx_eval_jobs_user_id", table_name="eval_jobs")
    op.drop_table("eval_jobs")
