"""Sessions complete endpoint — enum sanity check (no DB)."""

from src.audit import AuditEventType


def test_session_completed_enum_exists():
    assert AuditEventType.SESSION_COMPLETED.value == "session.completed"


def test_session_completed_is_distinct_from_started():
    assert AuditEventType.SESSION_COMPLETED != AuditEventType.SESSION_STARTED
