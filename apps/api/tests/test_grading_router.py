"""Grading router — input validation (no DB)."""

from src.routers.grading import GradeRequest


def test_grade_request_accepts_valid_actions():
    GradeRequest(action="accept")
    GradeRequest(action="modify", final_score=3, reason="needs better evidence")
    GradeRequest(action="reject", reason="completely missed the point")


def test_final_score_bounds():
    import pydantic

    try:
        GradeRequest(action="modify", final_score=6, reason="ok")
    except pydantic.ValidationError:
        pass
    else:
        raise AssertionError("expected ValidationError for final_score > 5")

    try:
        GradeRequest(action="modify", final_score=-1, reason="ok")
    except pydantic.ValidationError:
        pass
    else:
        raise AssertionError("expected ValidationError for final_score < 0")
