"""initial schema with participant_code

Revision ID: 0001_initial
Revises:
Create Date: 2026-05-27

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from pgvector.sqlalchemy import Vector


revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # pgvector extension (idempotent — the docker-compose initdb already creates it)
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # ── participants ──
    op.create_table(
        "participants",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("participant_code", sa.String(40), nullable=False, unique=True),
        sa.Column(
            "role",
            sa.Enum("student", "teacher", "admin", name="participant_role"),
            nullable=False,
        ),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("email", sa.String(200), unique=True, nullable=True),
        sa.Column("hashed_password", sa.String(200), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # ── cases ──
    op.create_table(
        "cases",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("code", sa.String(60), nullable=False, unique=True),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("chief_complaint", sa.Text(), nullable=False),
        sa.Column("scenario_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # ── rubrics ──
    op.create_table(
        "rubrics",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("case_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("cases.id", ondelete="CASCADE"), nullable=False),
        sa.Column("type", sa.Enum("lqqopera", "pe", name="rubric_type"), nullable=False),
        sa.Column("schema_version", sa.String(20), nullable=False, server_default="1.0.0"),
        sa.Column("items_json", sa.JSON(), nullable=False),
    )

    # ── sessions ──
    op.create_table(
        "sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("participant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("participants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("case_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("cases.id"), nullable=False),
        sa.Column("mode", sa.Enum("practice", "exam", name="session_mode"), nullable=False),
        sa.Column(
            "phase",
            sa.Enum(
                "scenario", "inquiry", "transition", "examination", "diagnosis", "review",
                name="session_phase",
            ),
            nullable=False,
        ),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
    )

    # ── transcripts ──
    op.create_table(
        "transcripts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("speaker", sa.Enum("student", "patient", name="transcript_speaker"), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("audio_path", sa.String(500), nullable=True),
        sa.Column("started_ms", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("ended_ms", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # ── duat_scores ──
    op.create_table(
        "duat_scores",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("rubric_item_id", sa.String(120), nullable=False),
        sa.Column("e_evidence_json", sa.JSON(), nullable=True),
        sa.Column("e_confidence", sa.Float(), nullable=True),
        sa.Column("s_score", sa.Integer(), nullable=True),
        sa.Column("s_cot_json", sa.JSON(), nullable=True),
        sa.Column("a_advocate_json", sa.JSON(), nullable=True),
        sa.Column("a_advocate_score", sa.Float(), nullable=True),
        sa.Column("arbiter_decision", sa.Enum("accept", "flag", "force_human", name="arbiter_decision"), nullable=True),
        sa.Column("arbiter_confidence", sa.Enum("high", "medium", "low", name="arbiter_confidence"), nullable=True),
        sa.Column("final_score", sa.Integer(), nullable=True),
        sa.Column("grader_action", sa.Enum("accept", "modify", "reject", name="grader_action"), nullable=True),
        sa.Column("grader_reason", sa.Text(), nullable=True),
        sa.Column("grader_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("participants.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # ── audit_events ──
    op.create_table(
        "audit_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("event_type", sa.String(60), nullable=False),
        sa.Column("event_json", sa.JSON(), nullable=False),
        sa.Column("prompt_hash", sa.String(80), nullable=True),
        sa.Column("model_version", sa.String(80), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # ── bibliotheke_chunks (pgvector 768 = BAAI/bge-base-zh-v1.5) ──
    op.create_table(
        "bibliotheke_chunks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("source", sa.String(300), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("embedding", Vector(768), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # HNSW index on the embedding for fast cosine similarity search.
    op.execute(
        "CREATE INDEX bibliotheke_chunks_embedding_hnsw "
        "ON bibliotheke_chunks USING hnsw (embedding vector_cosine_ops)"
    )


def downgrade() -> None:
    op.drop_index("bibliotheke_chunks_embedding_hnsw", table_name="bibliotheke_chunks")
    op.drop_table("bibliotheke_chunks")
    op.drop_table("audit_events")
    op.drop_table("duat_scores")
    op.drop_table("transcripts")
    op.drop_table("sessions")
    op.drop_table("rubrics")
    op.drop_table("cases")
    op.drop_table("participants")
    # Drop enum types
    for enum_name in (
        "participant_role", "rubric_type", "session_mode", "session_phase",
        "transcript_speaker", "arbiter_decision", "arbiter_confidence", "grader_action",
    ):
        op.execute(f"DROP TYPE IF EXISTS {enum_name}")
