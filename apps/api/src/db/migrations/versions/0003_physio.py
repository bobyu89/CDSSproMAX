"""wave 3 — physio_samples table (HRV skeleton)

Revision ID: 0003_physio
Revises: 0002_vision
Create Date: 2026-05-28

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "0003_physio"
down_revision: Union[str, None] = "0002_vision"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    physio_quality = sa.Enum(
        "good", "noisy", "gap", name="physio_quality_flag"
    )
    physio_quality.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "physio_samples",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "session_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("sessions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("device_id", sa.String(120), nullable=False),
        sa.Column("timestamp_ms", sa.BigInteger(), nullable=False),
        sa.Column("r_to_r_ms", sa.Integer(), nullable=False),
        sa.Column("heart_rate", sa.Integer(), nullable=True),
        sa.Column(
            "quality_flag",
            physio_quality,
            nullable=False,
            server_default="good",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index(
        "physio_samples_session_ts_idx",
        "physio_samples",
        ["session_id", "timestamp_ms"],
    )


def downgrade() -> None:
    op.drop_index("physio_samples_session_ts_idx", table_name="physio_samples")
    op.drop_table("physio_samples")
    sa.Enum(name="physio_quality_flag").drop(op.get_bind(), checkfirst=True)
