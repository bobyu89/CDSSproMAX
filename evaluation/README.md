# TICDSS Evaluation Harness

Pure-Python ablation harness for **Protocol §五.(二) Level 1b** (DUAT
Ablation Study). Lives outside `apps/api/` and treats the production code as
read-only. No live LLM calls in tests — group runners accept an injected
`score_fn` for hermetic execution.

## Layout

```
evaluation/
  schema.py            # Pydantic models (GoldenSample, EvalResult, ...)
  metrics.py           # ICC, Cohen's κ, MAE, % agreement
  groups.py            # GroupA_FullDuat / GroupB_NoAdversary / GroupC_SingleLlmBaseline
  run_ablation.py      # CLI + programmatic main(args)
  golden_sessions/     # JSONL of human-graded rubric items
  reports/             # JSON + CSV outputs (timestamped)
  tests/               # pytest, no network
```

## Adding golden samples

One JSON object per line in `golden_sessions/*.jsonl`. Required fields:

| field             | type    | notes                                    |
| ----------------- | ------- | ---------------------------------------- |
| `sample_id`       | str     | unique across the dataset                |
| `rubric_item_id`  | str     | e.g. `lqqopera.location`                 |
| `case_id`         | str     | maps back to `data/cases/`               |
| `transcript_text` | str     | the snippet the rater scored             |
| `case_context`    | str     | optional vignette (default `""`)         |
| `human_score`     | int 0-5 | ground truth                             |
| `human_rater_id`  | str?    | optional, useful for inter-rater audits  |

See `golden_sessions/example.jsonl` for three illustrative rows.

## Running the ablation

```powershell
python -m evaluation.run_ablation `
    --dataset evaluation/golden_sessions/example.jsonl `
    --groups A,B,C `
    --out evaluation/reports/
```

Outputs:
- `report_<UTC-timestamp>.json` — `AblationReport` (group metrics + pairwise deltas)
- `report_<UTC-timestamp>.csv`  — one row per (sample, group)

## Group definitions (Protocol §五.(二) Level 1b)

| Group | Composition                              | Arbiter input          |
| ----- | ---------------------------------------- | ---------------------- |
| **A** | Full DUAT: E + S + A + Arbiter           | real e_conf, real a_advocate |
| **B** | E + S only; A-Agent ablated              | real e_conf, `a_advocate = 0.0` |
| **C** | Single Claude Opus 4.7 + RAG, one shot   | n/a — `decision = "accept"` always |

Group C's prompt asks one LLM to do extraction + scoring in one call (see
docstring in `groups.py::GroupC_SingleLlmBaseline`). The exact prompt is open
for protocol-author review — see the unresolved-questions section below.

## Interpreting the metrics

| Metric              | Threshold for "good" agreement                                         |
| ------------------- | ---------------------------------------------------------------------- |
| **ICC(2,1)**        | ≥ 0.75 = good, ≥ 0.90 = excellent (Koo & Li 2016)                      |
| **Cohen's κ (quad)**| ≥ 0.61 = substantial, ≥ 0.81 = almost perfect (Landis & Koch 1977)     |
| **MAE**             | report descriptively; aim for ≤ 0.5 on a 0-5 scale                     |
| **% exact**         | descriptive                                                            |
| **% within ±1**     | descriptive — useful for ordinal scoring tolerance                     |

**ICC choice — ICC(2,1) absolute agreement.** Two-way random-effects, single
rater, absolute agreement. Rationale: we want generalisation to other model
runs (random effect) and we care that the model produces the *same* number,
not merely a correlated one (absolute, not consistency). Reference:
Koo TK, Li MY. *A Guideline of Selecting and Reporting Intraclass Correlation
Coefficients for Reliability Research.* J Chiropr Med. 2016;15(2):155-163.

**κ choice — quadratic weights.** OSCE scores are ordinal on 0-5; a 3-point
disagreement is meaningfully worse than 1-point. Quadratic weights penalise
distant disagreement quadratically (Cohen 1968).

## Adding a real Group C baseline

`GroupC_SingleLlmBaseline` ships without a default LLM call so tests stay
hermetic. To wire it up in production, instantiate with a `score_fn` that:

1. Embeds the transcript + rubric item + RAG snippets into a single prompt.
2. Calls `claude-opus-4-7` once.
3. Parses out a 0-5 integer.

Return shape::

    {"predicted_score": int, "arbiter_decision": "accept",
     "arbiter_confidence": "high", "notes": "..."}

## Running tests

```powershell
pytest evaluation/tests
```

All tests are offline. The end-to-end test in `test_run_ablation_mock.py`
exercises `main()` programmatically with injected mock runners.
