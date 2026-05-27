"""wave 4 — handout tables + session.generated_handout_json cache

Revision ID: 0004_handout
Revises: 0003_physio
Create Date: 2026-05-28

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "0004_handout"
down_revision: Union[str, None] = "0003_physio"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "sessions",
        sa.Column("generated_handout_json", sa.JSON(), nullable=True),
    )

    op.create_table(
        "self_assessments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "session_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("sessions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "participant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("participants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("q_handled_stress", sa.Integer(), nullable=True),
        sa.Column("q_learned_from_mistakes", sa.Integer(), nullable=True),
        sa.Column("q_uncertainty_tolerance", sa.Integer(), nullable=True),
        sa.Column("q_recovery_speed", sa.Integer(), nullable=True),
        sa.Column("q_growth_orientation", sa.Integer(), nullable=True),
        sa.Column("narrative_strengths", sa.Text(), nullable=True),
        sa.Column("narrative_growth", sa.Text(), nullable=True),
        sa.Column("narrative_supervisor_question", sa.Text(), nullable=True),
    )
    op.create_index(
        "self_assessments_session_idx",
        "self_assessments",
        ["session_id"],
    )

    op.create_table(
        "confidence_calibrations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "session_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("sessions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "participant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("participants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("predicted_score_0_5", sa.Integer(), nullable=False),
        sa.Column("predicted_at_phase", sa.String(40), nullable=False),
        sa.Column("actual_score_0_5", sa.Integer(), nullable=True),
        sa.Column("calibration_gap", sa.Integer(), nullable=True),
    )
    op.create_index(
        "confidence_calibrations_session_idx",
        "confidence_calibrations",
        ["session_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "confidence_calibrations_session_idx",
        table_name="confidence_calibrations",
    )
    op.drop_table("confidence_calibrations")
    op.drop_index("self_assessments_session_idx", table_name="self_assessments")
    op.drop_table("self_assessments")
    op.drop_column("sessions", "generated_handout_json")
