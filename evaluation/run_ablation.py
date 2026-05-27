"""CLI entry point for Level 1b Ablation Study.

Example::

    python -m evaluation.run_ablation \
        --dataset evaluation/golden_sessions/example.jsonl \
        --groups A,B,C \
        --out evaluation/reports/
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import json
import sys
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from .groups import GROUP_REGISTRY, _BaseGroup
from .metrics import (
    compute_icc,
    compute_kappa,
    compute_mae,
    compute_pct_agreement,
)
from .schema import (
    AblationReport,
    EvalResult,
    GoldenSample,
    MetricsReport,
    PairwiseDelta,
)


@dataclass
class Args:
    dataset: Path
    groups: list[str]
    out: Path
    runners: dict[str, _BaseGroup] | None = None  # test injection hook


def load_dataset(path: Path) -> list[GoldenSample]:
    samples: list[GoldenSample] = []
    with path.open("r", encoding="utf-8") as fh:
        for line_num, raw in enumerate(fh, start=1):
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            try:
                samples.append(GoldenSample.model_validate_json(line))
            except Exception as exc:
                raise ValueError(f"{path}:{line_num} — invalid GoldenSample: {exc}") from exc
    if not samples:
        raise ValueError(f"No samples loaded from {path}.")
    return samples


def aggregate(
    group_name: str, samples: list[GoldenSample], results: list[EvalResult]
) -> MetricsReport:
    human = [s.human_score for s in samples]
    model = [r.predicted_score for r in results]
    return MetricsReport(
        group=group_name,  # type: ignore[arg-type]
        n=len(results),
        icc=compute_icc(human, model),
        kappa=compute_kappa(human, model),
        mae=compute_mae(human, model),
        pct_agree_exact=compute_pct_agreement(human, model, exact=True),
        pct_agree_within_1=compute_pct_agreement(human, model, exact=False),
        n_accept=sum(1 for r in results if r.arbiter_decision == "accept"),
        n_flag=sum(1 for r in results if r.arbiter_decision == "flag"),
        n_force_human=sum(1 for r in results if r.arbiter_decision == "force_human"),
    )


def _pairwise(groups: dict[str, MetricsReport]) -> list[PairwiseDelta]:
    keys = sorted(groups.keys())
    out: list[PairwiseDelta] = []
    for i, left in enumerate(keys):
        for right in keys[i + 1 :]:
            lhs = groups[left]
            rhs = groups[right]
            out.append(
                PairwiseDelta(
                    left=left,  # type: ignore[arg-type]
                    right=right,  # type: ignore[arg-type]
                    d_icc=lhs.icc - rhs.icc,
                    d_kappa=lhs.kappa - rhs.kappa,
                    d_mae=lhs.mae - rhs.mae,
                )
            )
    return out


async def _run_one_group(
    runner: _BaseGroup, samples: list[GoldenSample]
) -> list[EvalResult]:
    out: list[EvalResult] = []
    for sample in samples:  # sequential — LLM rate limits matter (Protocol §四.(六))
        out.append(await runner.score_sample(sample))
    return out


def _print_summary(report: AblationReport) -> None:
    print(f"\nAblation report — {report.timestamp}")
    print(f"Dataset: {report.dataset_path}   n={report.n_samples}\n")
    header = f"{'Group':<6}{'n':>4}{'ICC':>8}{'kappa':>8}{'MAE':>8}{'%exact':>10}{'%±1':>8}"
    print(header)
    print("-" * len(header))
    for name in sorted(report.groups):
        g = report.groups[name]
        print(
            f"{name:<6}{g.n:>4}{g.icc:>8.3f}{g.kappa:>8.3f}{g.mae:>8.3f}"
            f"{g.pct_agree_exact * 100:>9.1f}%{g.pct_agree_within_1 * 100:>7.1f}%"
        )
    if report.pairwise_deltas:
        print("\nPairwise deltas (left - right):")
        for d in report.pairwise_deltas:
            print(
                f"  {d.left} - {d.right}: ΔICC={d.d_icc:+.3f}  "
                f"Δκ={d.d_kappa:+.3f}  ΔMAE={d.d_mae:+.3f}"
            )


def main(args: Args) -> AblationReport:
    """Programmatic entry point — also used by tests."""
    samples = load_dataset(args.dataset)
    runners: dict[str, _BaseGroup] = args.runners or {
        name: GROUP_REGISTRY[name]() for name in args.groups
    }
    if set(runners.keys()) != set(args.groups):
        # Honour requested subset
        runners = {k: v for k, v in runners.items() if k in args.groups}

    all_rows: list[tuple[GoldenSample, EvalResult]] = []
    metrics_by_group: dict[str, MetricsReport] = {}
    for group_name in args.groups:
        runner = runners[group_name]
        results = asyncio.run(_run_one_group(runner, samples))
        for s, r in zip(samples, results, strict=True):
            all_rows.append((s, r))
        metrics_by_group[group_name] = aggregate(group_name, samples, results)

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    report = AblationReport(
        timestamp=ts,
        dataset_path=str(args.dataset),
        n_samples=len(samples),
        groups=metrics_by_group,
        pairwise_deltas=_pairwise(metrics_by_group),
    )

    args.out.mkdir(parents=True, exist_ok=True)
    json_path = args.out / f"report_{ts}.json"
    csv_path = args.out / f"report_{ts}.csv"

    json_path.write_text(
        report.model_dump_json(indent=2), encoding="utf-8"
    )
    with csv_path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(
            [
                "sample_id",
                "group",
                "rubric_item_id",
                "human_score",
                "predicted_score",
                "abs_error",
                "arbiter_decision",
                "arbiter_confidence",
                "latency_ms",
                "notes",
            ]
        )
        for s, r in all_rows:
            writer.writerow(
                [
                    s.sample_id,
                    r.group,
                    s.rubric_item_id,
                    s.human_score,
                    r.predicted_score,
                    abs(s.human_score - r.predicted_score),
                    r.arbiter_decision,
                    r.arbiter_confidence,
                    r.latency_ms,
                    r.notes,
                ]
            )

    _print_summary(report)
    print(f"\nWrote {json_path}")
    print(f"Wrote {csv_path}")
    return report


def _parse_cli(argv: Iterable[str]) -> Args:
    p = argparse.ArgumentParser(description="TICDSS Level 1b Ablation harness.")
    p.add_argument("--dataset", type=Path, required=True)
    p.add_argument(
        "--groups",
        type=str,
        default="A,B,C",
        help="Comma-separated subset of A,B,C.",
    )
    p.add_argument("--out", type=Path, default=Path("evaluation/reports"))
    ns = p.parse_args(list(argv))
    groups = [g.strip() for g in ns.groups.split(",") if g.strip()]
    unknown = set(groups) - set(GROUP_REGISTRY)
    if unknown:
        p.error(f"Unknown groups: {sorted(unknown)}")
    return Args(dataset=ns.dataset, groups=groups, out=ns.out)


if __name__ == "__main__":  # pragma: no cover
    main(_parse_cli(sys.argv[1:]))
