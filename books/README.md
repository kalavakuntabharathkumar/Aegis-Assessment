# ML Textbooks for Pinecone Knowledge Base

Place the following PDF textbooks in this folder before running `python backend/ingest.py`.

## Required Books

| Filename (recommended) | Title | Author(s) |
|---|---|---|
| `mitchell_ml.pdf` | Machine Learning | Tom M. Mitchell |
| `bishop_prml.pdf` | Pattern Recognition and Machine Learning (PRML) | Christopher M. Bishop |
| `burkov_100page.pdf` | The Hundred-Page Machine Learning Book | Andriy Burkov |

## Why these books?

These textbooks form the grounding knowledge base that Aegis Assessment uses to generate
interview questions rooted in real ML theory — not generic prompts.

- **Mitchell** covers the foundational algorithms: decision trees, neural networks, Bayesian
  learning, reinforcement learning, and computational learning theory.
- **Bishop (PRML)** is the canonical reference for probabilistic graphical models, kernel methods,
  SVMs, and EM algorithm.
- **Burkov** is concise and covers modern ML concepts efficiently — great signal density per page.

## After placing PDFs here

Run the ingestion script from the workspace root:

```bash
# Dry run first — shows chunk counts, no API calls
python backend/ingest.py --dry-run

# Full run — embeds and upserts everything to Pinecone
python backend/ingest.py
```

Requires env vars: `PINECONE_API_KEY`, `PINECONE_HOST`, `OPENROUTER_API_KEY`
