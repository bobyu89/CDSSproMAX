"""PE fusion — Layer 1 (markers) × Layer 2 (V-Agent) weighting."""

from src.agents.pe_fusion import fuse
from src.agents.v_agent import VAgentOutput


def _v(action=True, technique=0.8, duration=True):
    return VAgentOutput(
        agent_name="V-Agent",
        model_version="gemini-3.5-flash",
        rubric_item_id="pe.x",
        action_correct=action,
        technique_score=technique,
        duration_adequate=duration,
        evidence_frames=[],
        notes="",
    )


def test_perfect_score():
    r = fuse(
        target_region="right_lower_lung",
        detected_regions=["right_lower_lung"],
        v_agent=_v(),
    )
    # position 1.0 * 0.8 + technique 0.8 * 0.2 = 0.96 + duration bonus → clamp 1.0 → 5
    assert r.score_0_5 == 5
    assert r.position_correct is True


def test_wrong_position_caps_score():
    r = fuse(
        target_region="right_lower_lung",
        detected_regions=["left_upper_lung"],
        v_agent=_v(),
    )
    # position 0.5 * 0.8 + technique 0.8 * 0.2 = 0.56 + 0.10 bonus = 0.66 → 3
    assert r.position_correct is False
    assert r.score_0_5 == 3


def test_no_position_no_score():
    r = fuse(
        target_region="right_lower_lung",
        detected_regions=[],
        v_agent=_v(technique=0.0, duration=False),
    )
    assert r.score_0_5 == 0


def test_position_only_no_v_agent():
    """If V-Agent is unavailable, position alone can still yield 0.8 * 5 = 4."""
    r = fuse(
        target_region="pmi",
        detected_regions=["pmi"],
        v_agent=None,
    )
    # 1.0 * 0.8 + 0 * 0.2 = 0.8 → 4
    assert r.score_0_5 == 4
    assert r.position_correct is True


def test_duration_bonus_lifts_borderline():
    r_no_bonus = fuse(
        target_region="pmi",
        detected_regions=["pmi"],
        v_agent=_v(technique=0.4, duration=False),
    )
    r_with_bonus = fuse(
        target_region="pmi",
        detected_regions=["pmi"],
        v_agent=_v(technique=0.4, duration=True),
    )
    assert r_with_bonus.score_0_5 >= r_no_bonus.score_0_5


def test_rationale_contains_percentages():
    r = fuse(
        target_region="pmi",
        detected_regions=["pmi"],
        v_agent=_v(technique=0.7, duration=True),
    )
    assert "100%" in r.rationale  # position
    assert "70%" in r.rationale   # technique
    assert "持續時間達標" in r.rationale
