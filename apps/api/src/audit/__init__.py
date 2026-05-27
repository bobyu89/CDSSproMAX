"""Audit Log — JSONL persistent log + DB index for fast queries.

Protocol §四.(七): every scoring event is recorded with prompt_hash and
model_version. JSONL files are the source of truth; the audit_events table
is a denormalized index.
"""

from src.audit.logger import AuditLogger, get_audit_logger
from src.audit.schema import AuditEventType, AuditPayload

__all__ = ["AuditEventType", "AuditLogger", "AuditPayload", "get_audit_logger"]
