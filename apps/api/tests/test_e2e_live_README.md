# Live LLM tests

These tests **hit real APIs** and are excluded from the default `pytest` run.

## Run

```bash
cd apps/api

# Single E-Agent live check
ANTHROPIC_API_KEY=... GOOGLE_API_KEY=... uv run pytest -m live -k e_agent -v

# Full DUAT pipeline one-item
ANTHROPIC_API_KEY=... GOOGLE_API_KEY=... uv run pytest -m live -k full_duat -v

# All live tests
ANTHROPIC_API_KEY=... GOOGLE_API_KEY=... uv run pytest -m live -v
```

## What's tested

| Test | LLM calls | Cost / run |
|---|---|---|
| `test_e_agent_extracts_location` | 1× Gemini 3.5 Flash | ~$0.001 |
| `test_s_agent_scores_location` | 1× Claude Opus 4.7 | ~$0.05 |
| `test_a_agent_reviews_independently` | 1× Gemini 3.5 Flash | ~$0.001 |
| `test_full_duat_pipeline_one_item` | 1× Gemini + 1× Claude + 1× Gemini | ~$0.05 |

Total cost per full run ≈ $0.10. Run sparingly during development.

## CI

Live tests do **not** run in default CI (no `-m live` flag). They should
only be triggered manually before a release or when a prompt template
changes meaningfully.

## What the tests assert

Structural correctness only:
- Field types and ranges (score 0-5, advocate_score 0-1, etc.)
- JSON parses
- Audit log JSONL contains the expected 5 events
- `prompt_hash` and `model_version` populated

We do NOT assert exact LLM text — that varies across calls.
