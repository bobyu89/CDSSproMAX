"""Inter-rater agreement metrics for the ablation study.

ICC choice: **ICC(2,1)** — two-way random-effects, single rater/measurement,
*absolute agreement*. Rationale (Koo & Li, 2016, J Chiropr Med 15(2):155-163):

  - "Two-way random": both raters (human, model) are treated as a random sample
    from a larger population of possible raters — appropriate when we want to
    generalise beyond the specific model run.
  - "Single rater": each sample is scored once per group (no averaging).
  - "Absolute agreement": we care that the model produces the *same* number, not
    merely a number that is linearly related to the human — clinical scoring
    requires absolute scale match.

Cohen's κ uses **quadratic weights** because the 0-5 OSCE rubric is ordinal:
disagreement of 2 points is meaningfully worse than 1 point (Cohen, 1968).
"""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np
import pandas as pd
import pingouin as pg
from sklearn.metrics import cohen_kappa_score


def _validate(human: Sequence[float], model: Sequence[float]) -> tuple[list[float], list[float]]:
    h = list(human)
    m = list(model)
    if not h or not m:
        raise ValueError("Inputs must be non-empty.")
    if len(h) != len(m):
        raise ValueError(f"Length mismatch: human={len(h)} model={len(m)}.")
    return h, m


def compute_icc(human_scores: Sequence[float], model_scores: Sequence[float]) -> float:
    """ICC(2,1) absolute agreement between human and model raters.

    Returns NaN if there is zero variance (degenerate constant case).
    """
    h, m = _validate(human_scores, model_scores)
    n = len(h)
    # pingouin expects long-format dataframe: targets x raters.
    df = pd.DataFrame(
        {
            "target": list(range(n)) * 2,
            "rater": ["human"] * n + ["model"] * n,
            "score": list(h) + list(m),
        }
    )
    try:
        icc_df = pg.intraclass_corr(
            data=df, targets="target", raters="rater", ratings="score", nan_policy="omit"
        )
    except (ValueError, AssertionError):
        return float("nan")
    row = icc_df[icc_df["Type"] == "ICC2"]
    if row.empty:
        return float("nan")
    return float(row["ICC"].iloc[0])


def compute_kappa(human_scores: Sequence[float], model_scores: Sequence[float]) -> float:
    """Cohen's κ with quadratic weights for ordinal 0-5 scores."""
    h, m = _validate(human_scores, model_scores)
    return float(cohen_kappa_score(h, m, weights="quadratic"))


def compute_mae(human_scores: Sequence[float], model_scores: Sequence[float]) -> float:
    h, m = _validate(human_scores, model_scores)
    return float(np.mean(np.abs(np.asarray(h, dtype=float) - np.asarray(m, dtype=float))))


def compute_pct_agreement(
    human_scores: Sequence[float],
    model_scores: Sequence[float],
    exact: bool = True,
) -> float:
    """Percent agreement. exact=True → identical; exact=False → within ±1."""
    h, m = _validate(human_scores, model_scores)
    diffs = np.abs(np.asarray(h, dtype=float) - np.asarray(m, dtype=float))
    tol = 0.0 if exact else 1.0
    return float(np.mean(diffs <= tol))
