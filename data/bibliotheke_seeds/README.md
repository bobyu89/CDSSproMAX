# Bibliotheke Seeds

Source documents for the E-Agent's knowledge base (`bibliotheke_chunks` table).

## Format

- One `.md` file per source document.
- File **stem** (e.g. `seidel_2019_ch4.md`) becomes the `source` field in the DB.
- Paragraphs separated by blank lines (`\n\n`) are treated as candidate chunks.
- Long paragraphs are split into ≤ 400-character chunks (naive character window).
- Embeddings are computed with `BAAI/bge-base-zh-v1.5` (768 dims, cosine).

## Example layout

```
data/bibliotheke_seeds/
├── README.md                         ← this file
├── seidel_2019_ch04_pain_history.md  ← LQQOPERA reference
└── bates_2021_ch08_chest_exam.md     ← PE technique reference
```

## Running the seeder

```powershell
cd apps/api
uv run python scripts/seed_bibliotheke.py
```

The script is idempotent-friendly only at the file level — re-running will
insert duplicate chunks. For Wave 1, drop and re-create the table if you want
a clean reseed.
