"""wave 1.5 — pe_observations table

Revision ID: 0002_vision
Revises: 0001_initial
Create Date: 2026-05-28

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "0002_vision"
down_revision: Union[str, None] = "0001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "pe_observations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "session_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("sessions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("rubric_item_id", sa.String(120), nullable=False),
        sa.Column("student_intent", sa.Text(), nullable=True),
        sa.Column("target_region", sa.String(60), nullable=False),
        sa.Column("detected_regions", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("duration_seconds", sa.Float(), nullable=False, server_default="0"),
        sa.Column("v_action_correct", sa.Boolean(), nullable=True),
        sa.Column("v_technique_score", sa.Float(), nullable=True),
        sa.Column("v_duration_adequate", sa.Boolean(), nullable=True),
        sa.Column("v_notes", sa.Text(), nullable=True),
        sa.Column("keyframe_paths", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index(
        "pe_observations_session_idx",
        "pe_observations",
        ["session_id"],
    )


def downgrade() -> None:
    op.drop_index("pe_observations_session_idx", table_name="pe_observations")
    op.drop_table("pe_observations")
