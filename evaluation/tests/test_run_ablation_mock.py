"""End-to-end test for run_ablation with all group runners mocked."""

from __future__ import annotations

import csv
import json
from pathlib import Path

from evaluation.groups import (
    GroupA_FullDuat,
    GroupB_NoAdversary,
    GroupC_SingleLlmBaseline,
)
from evaluation.run_ablation import Args, main


def _make_dataset(tmp_path: Path) -> Path:
    src = Path("evaluation/golden_sessions/example.jsonl")
    if src.exists():
        return src
    # Fallback inline dataset for environments where cwd differs.
    p = tmp_path / "ds.jsonl"
    p.write_text(
        "\n".join(
            [
                '{"sample_id":"s1","rubric_item_id":"r1","case_id":"c1","transcript_text":"t","human_score":5}',
                '{"sample_id":"s2","rubric_item_id":"r1","case_id":"c1","transcript_text":"t","human_score":3}',
                '{"sample_id":"s3","rubric_item_id":"r1","case_id":"c1","transcript_text":"t","human_score":1}',
            ]
        ),
        encoding="utf-8",
    )
    return p


def _fixed_score_fn(score: int, decision: str = "accept", confidence: str = "high"):
    async def _fn(sample):  # noqa: ARG001
        return {
            "predicted_score": score,
            "arbiter_decision": decision,
            "arbiter_confidence": confidence,
            "notes": "mock",
        }

    return _fn


def test_run_ablation_end_to_end(tmp_path: Path) -> None:
    dataset = _make_dataset(tmp_path)
    out = tmp_path / "reports"

    runners = {
        "A": GroupA_FullDuat(score_fn=_fixed_score_fn(5, "accept", "high")),
        "B": GroupB_NoAdversary(score_fn=_fixed_score_fn(3, "flag", "medium")),
        "C": GroupC_SingleLlmBaseline(score_fn=_fixed_score_fn(1, "accept", "high")),
    }
    args = Args(dataset=dataset, groups=["A", "B", "C"], out=out, runners=runners)

    report = main(args)

    assert report.n_samples == 3
    assert set(report.groups.keys()) == {"A", "B", "C"}
    # Three pairwise comparisons: A-B, A-C, B-C.
    assert len(report.pairwise_deltas) == 3

    json_files = list(out.glob("report_*.json"))
    csv_files = list(out.glob("report_*.csv"))
    assert len(json_files) == 1
    assert len(csv_files) == 1

    payload = json.loads(json_files[0].read_text(encoding="utf-8"))
    assert payload["n_samples"] == 3
    assert payload["groups"]["A"]["n"] == 3

    with csv_files[0].open(encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    # 3 samples × 3 groups = 9 rows.
    assert len(rows) == 9
    groups_seen = {r["group"] for r in rows}
    assert groups_seen == {"A", "B", "C"}
    # Group C should always be "accept" (no arbitration).
    c_rows = [r for r in rows if r["group"] == "C"]
    assert all(r["arbiter_decision"] == "accept" for r in c_rows)


def test_run_ablation_subset_of_groups(tmp_path: Path) -> None:
    dataset = _make_dataset(tmp_path)
    out = tmp_path / "reports"
    runners = {
        "A": GroupA_FullDuat(score_fn=_fixed_score_fn(4)),
        "C": GroupC_SingleLlmBaseline(score_fn=_fixed_score_fn(2)),
    }
    args = Args(dataset=dataset, groups=["A", "C"], out=out, runners=runners)
    report = main(args)
    assert set(report.groups.keys()) == {"A", "C"}
    assert len(report.pairwise_deltas) == 1
