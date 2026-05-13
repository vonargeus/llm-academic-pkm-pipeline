# Reproducibility Guide

This document provides all information needed to reproduce the thesis experiments.

## System Requirements

- Python 3.11+
- Windows 10/11 or Linux
- ~4 GB disk space for PDFs + indexes
- LLM API key (see below)

## Installation

```bash
git clone https://github.com/[TBD]/thesis-obsidian-agent.git
cd thesis-obsidian-agent
python -m venv .venv
.venv\Scripts\activate   # Windows
pip install -r requirements.txt
```

## LLM Configuration

Set your API key as an environment variable:

```bash
# Google Gemini (default)
set GEMINI_API_KEY=your_key_here
set LLM_PROVIDER=gemini

# OpenAI (alternative)
set OPENAI_API_KEY=your_key_here
set LLM_PROVIDER=openai

# Anthropic (alternative)
set ANTHROPIC_API_KEY=your_key_here
set LLM_PROVIDER=anthropic
```

**Model versions used in the thesis:**

| Provider | Model | Version |
|----------|-------|---------|
| Google | Gemini 1.5 Flash | gemini-1.5-flash (2024-09) |
| OpenAI | GPT-4o-mini | gpt-4o-mini (2024-07-18) |
| Anthropic | Claude 3 Haiku | claude-3-haiku-20240307 |

## Reproducing the Full Experiment

```bash
# Step 1: Download papers
python scripts/download_papers.py --output data/raw_pdfs/

# Step 2: Extract text
python scripts/extract_pdfs.py --input data/raw_pdfs/ --output data/extracted_text/

# Step 3: Build baseline index
python scripts/build_baseline_index.py \
    --input data/raw_pdfs/ \
    --output data/results/baseline_index.json

# Step 4: Generate structured notes (requires LLM API key)
python scripts/generate_notes.py \
    --input data/extracted_text/ \
    --output data/generated_notes/ \
    --config configs/structured.yaml

# Step 5: Run full evaluation
python scripts/run_full_eval.py \
    --queries data/queries/queries.json \
    --gold data/gold_labels/gold_labels.json \
    --metadata-gold data/gold_labels/metadata_gold.json \
    --link-gold data/gold_labels/link_gold.json \
    --output data/results/
```

## Fixed Parameters

| Parameter | Value |
|-----------|-------|
| Embedding model | `all-MiniLM-L6-v2` |
| Chunk size | 800 characters |
| Chunk overlap | 120 characters |
| Retrieval similarity | Cosine |
| k values | 1, 3, 5, 10 |
| LLM temperature (metadata/links) | 0.0 |
| LLM temperature (notes/summaries) | 0.3 |
| LLM max output tokens (metadata) | 2048 |
| LLM max output tokens (notes) | 4096 |
| Link candidate pool | top-10 by cosine similarity |
| Min link confidence | 0.6 |

## Data Sharing

| Artefact | Shared? | Format | Location |
|----------|---------|--------|----------|
| Paper corpus (arXiv IDs) | ✅ Yes | JSON | `data/raw_pdfs/manifest.json` |
| Raw PDFs | ❌ No (copyright) | — | Download via `download_papers.py` |
| Extracted text | ✅ Yes | JSON | `data/extracted_text/` |
| Generated notes | ✅ Yes | Markdown | `data/generated_notes/` |
| Query set | ✅ Yes | JSON | `data/queries/queries.json` |
| Gold labels (retrieval) | ✅ Yes | JSON | `data/gold_labels/gold_labels.json` |
| Gold labels (metadata) | ✅ Yes | JSON | `data/gold_labels/metadata_gold.json` |
| Gold labels (links) | ✅ Yes | JSON | `data/gold_labels/link_gold.json` |
| Evaluation results | ✅ Yes | JSON | `data/results/` |
| Prompts | ✅ Yes | Markdown | `prompts/` |
| Configs | ✅ Yes | YAML | `configs/` |
| Code | ✅ Yes | Python | `src/`, `scripts/` |
| Thesis LaTeX | ✅ Yes | TeX | `thesis/` |

## Known Limitations Affecting Reproducibility

1. **LLM non-determinism:** Even at temperature=0.0, LLM outputs may vary slightly across API calls and model versions. Results are tied to the specific model version listed above.
2. **arXiv rate limits:** The download script includes a 3-second delay between requests. Do not remove this.
3. **PDF extraction quality:** Some PDFs (scanned, two-column, or with complex layouts) may extract poorly. See `data/extracted_text/_extraction_summary.json` for per-paper quality.
4. **Gold label subjectivity:** Metadata and link labels involve human judgment. Annotation decisions are documented in `docs/annotation_guidelines.md` and `docs/annotation_notes.md`.
