"""Unit tests for evaluation.metrics."""

from __future__ import annotations

import math

import pytest

from evaluation.metrics import (
    compute_icc,
    compute_kappa,
    compute_mae,
    compute_pct_agreement,
)


# ---------------------------------------------------------------------------
# ICC
# ---------------------------------------------------------------------------

def test_icc_perfect_agreement_is_one() -> None:
    h = [0, 1, 2, 3, 4, 5, 2, 3]
    m = list(h)
    assert math.isclose(compute_icc(h, m), 1.0, abs_tol=1e-9)


def test_icc_constant_systematic_offset_is_below_perfect() -> None:
    # ICC2 (absolute agreement) penalises systematic offsets.
    h = [0, 1, 2, 3, 4, 5]
    m = [1, 2, 3, 4, 5, 6]  # every model score is +1
    icc = compute_icc(h, m)
    assert 0.0 < icc < 1.0


def test_icc_is_high_for_strong_agreement() -> None:
    h = [1, 2, 3, 4, 5, 2, 3, 4]
    m = [1, 2, 3, 4, 5, 2, 3, 4]
    assert compute_icc(h, m) > 0.9


# ---------------------------------------------------------------------------
# Cohen's kappa
# ---------------------------------------------------------------------------

def test_kappa_perfect_agreement_is_one() -> None:
    h = [0, 1, 2, 3, 4, 5, 2, 3]
    assert math.isclose(compute_kappa(h, list(h)), 1.0, abs_tol=1e-9)


def test_kappa_quadratic_weights_penalises_far_disagreement_more() -> None:
    # All disagreements are by 1 point.
    h1 = [1, 2, 3, 4]
    m1 = [2, 3, 4, 5]
    k_close = compute_kappa(h1, m1)
    # All disagreements are by 3 points.
    h2 = [1, 1, 2, 2]
    m2 = [4, 4, 5, 5]
    k_far = compute_kappa(h2, m2)
    assert k_close > k_far


# ---------------------------------------------------------------------------
# MAE
# ---------------------------------------------------------------------------

def test_mae_basic() -> None:
    assert compute_mae([1, 2, 3], [1, 2, 3]) == 0.0
    assert math.isclose(compute_mae([1, 2, 3], [2, 3, 4]), 1.0)
    assert math.isclose(compute_mae([0, 0], [3, 1]), 2.0)


# ---------------------------------------------------------------------------
# % agreement
# ---------------------------------------------------------------------------

def test_pct_agreement_exact() -> None:
    assert compute_pct_agreement([1, 2, 3, 4], [1, 2, 3, 4], exact=True) == 1.0
    assert compute_pct_agreement([1, 2, 3, 4], [1, 2, 3, 5], exact=True) == 0.75
    assert compute_pct_agreement([1, 2], [3, 4], exact=True) == 0.0


def test_pct_agreement_within_1() -> None:
    # Off-by-one all four → 100% within ±1.
    assert compute_pct_agreement([1, 2, 3, 4], [2, 3, 4, 5], exact=False) == 1.0
    # One off-by-two.
    assert compute_pct_agreement([1, 2, 3, 4], [3, 2, 3, 4], exact=False) == 0.75


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("fn", [compute_icc, compute_kappa, compute_mae, compute_pct_agreement])
def test_empty_raises(fn) -> None:
    with pytest.raises(ValueError):
        fn([], [])


@pytest.mark.parametrize("fn", [compute_icc, compute_kappa, compute_mae, compute_pct_agreement])
def test_length_mismatch_raises(fn) -> None:
    with pytest.raises(ValueError):
        fn([1, 2, 3], [1, 2])
