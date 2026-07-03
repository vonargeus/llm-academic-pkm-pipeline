# Reproducibility Guide

This document provides all information needed to reproduce the thesis experiments.
All parameters listed here are verified against the actual source code and result JSON files.

---

## System Requirements

- Python 3.10+
- Windows 10/11 or Linux
- ~4 GB disk space for PDFs + indexes
- Google Gemini API key (see below)

---

## Installation

```bash
git clone https://github.com/[TBD]/thesis-obsidian-agent.git
cd thesis-obsidian-agent
python -m venv .venv
.venv\Scripts\activate   # Windows
pip install -r requirements.txt
```

---

## LLM Configuration

All LLM components use the Google Gemini API. Set your key as an environment variable:

```bash
set GEMINI_API_KEY=your_key_here
set LLM_PROVIDER=gemini
```

### Model Pool

The pipeline uses a rotating pool of Google Gemini Flash models to handle per-model
daily rate limits (20 requests/day on free tier). Models are tried in order; if one
exhausts its daily quota, the next is used automatically:

```
gemini-flash-latest   ← tried first
gemini-2.5-flash
gemini-2.0-flash
gemini-3-flash-preview
gemini-2.0-flash-001
gemini-3.5-flash
gemini-3.1-flash-lite
gemini-2.5-flash-lite
gemini-2.0-flash-lite-001
```

This is defined in `src/agents/metadata_agent.py` (MODEL_POOL list).
All models in the pool use `temperature=0.0`.

---

## Verified Fixed Parameters

All values verified from source code and result JSON files.

| Parameter | Value | Source |
|-----------|-------|--------|
| Embedding model | `nomic-ai/nomic-embed-text-v1.5` | `src/retrieval/baseline.py`, `rq1_experimental_suite.ipynb` |
| Chunk size | 512 tokens | `rq1_experimental_suite.ipynb` (tokenizer-based) |
| Chunk overlap | 50 tokens | `rq1_experimental_suite.ipynb` |
| Retrieval similarity | Cosine | `src/retrieval/baseline.py` |
| Primary k value evaluated | 5 | `data/results/retrieval_metrics.json` |
| LLM temperature (all components) | 0.0 | `src/agents/metadata_agent.py` line 107, 146 |
| Note generation input length | first 12,000 characters of extracted text | `src/agents/note_agent.py` line 35 |
| Link candidate input | target note frontmatter + summary (first 2,000 chars) + candidate summaries (first 500 chars each) | `src/agents/link_agent.py` lines 33, 41 |
| RQ2 strict topic overlap papers | 22 (full set) | `data/results/rq2_results.json` |
| RQ2 B1c dev/test split | 7 dev / 15 test | `data/results/b1c_test_results.json` |
| RQ2 B1c embedding threshold (tau_m) | 0.7361 (frozen on dev set) | `data/results/b1c_test_results.json` |
| RQ2 B1c best_k (top mappings kept) | 4 | `data/results/b1c_test_results.json` |
| RQ2 B1c deduplication threshold (tau_d) | 0.85 | `data/results/b1c_test_results.json` |
| RQ3 scored papers | 34 (of 40; 3 excluded: unusable gold; 3 excluded: provider block) | `data/results/rq3_citation_link_evaluation.json` |
| RQ3 excluded (unusable gold) | 2305.19951, 2510.14538, 2602.23878 | `data/results/rq3_citation_link_evaluation.json` |
| RQ3 excluded (provider blocked) | 2309.15217, 2401.15884, 2409.05591 | `data/results/rq3_citation_link_evaluation.json` |
| Link-Expanded RAG CV folds | 5 (stratified by query category) | `data/results/cv_report.json` |

---

## Execution Order (All Stages Manually Triggered)

Each stage is a separate batch process, run sequentially by the researcher.
No autonomous orchestration exists between stages.

```
Stage 1: PDF text extraction
  → python scripts/extract_pdfs.py

Stage 2: Metadata extraction (metadata_agent.py)
  → Produces YAML frontmatter per paper (title, year, venue, authors, DOI, arXiv ID, topics)

Stage 3: Note generation (note_agent.py)
  → Uses extracted text + Stage 2 metadata
  → Produces structured Markdown body (problem, methodology, datasets, findings, limitations)

Stage 4: Semantic link generation (link_agent.py)
  → Uses all generated notes from Stage 3
  → Produces [[wiki-links]] between related papers

[RQ1 + RQ2 artefacts FROZEN here]

Stage 5 (RQ3 only): Citation link extraction (link_agent.extract_citation_links)
  → Uses extracted PDF text (bibliography section)
  → Produces structured reference records resolved against Semantic Scholar
```

---

## Data Sharing

| Artefact | Shared? | Format | Location |
|----------|---------|--------|----------|
| Paper corpus (arXiv IDs) | ✅ Yes | JSON | `data/raw_pdfs/manifest.json` |
| Raw PDFs | ❌ No (copyright) | — | Download via `scripts/download_papers.py` |
| Extracted text | ✅ Yes | JSON | `data/extracted_text/` |
| Generated notes | ✅ Yes | Markdown | `data/generated_notes/` |
| Query set | ✅ Yes | JSON | `data/queries/queries.json` |
| Gold labels (retrieval) | ✅ Yes | JSON | `data/gold_labels/gold_labels.json` |
| Gold labels (expert topics) | ✅ Yes | JSON | `data/gold_labels/emile_vault_gold.json` |
| Evaluation results | ✅ Yes | JSON | `data/results/` |
| Prompts | ✅ Yes | Markdown | `prompts/` |
| Code | ✅ Yes | Python | `src/`, `scripts/` |
| Thesis LaTeX | ✅ Yes | TeX | `Thesis_Draft/` |

> Note: `data/gold_labels/link_gold.json` exists but was not used as the primary
> gold standard for RQ3. RQ3 uses Semantic Scholar outgoing reference lists instead.

---

## Known Limitations Affecting Reproducibility

1. **LLM model rotation:** Results depend on which Gemini Flash model version
   served each paper during ingestion. The exact model per paper is recorded in
   the prediction cache (`_llm_provider` field in each metadata JSON).

2. **LLM non-determinism:** Even at temperature=0.0, minor output variations may
   occur across API versions and dates.

3. **arXiv rate limits:** The download script includes a 3-second delay between
   requests. Do not remove this.

4. **PDF extraction quality:** Some PDFs (scanned, two-column layouts) may extract
   poorly. See `data/extracted_text/_extraction_summary.json` for per-paper quality.

5. **Semantic Scholar availability:** RQ3 gold reference lists depend on Semantic
   Scholar API availability. Three papers had no usable reference records returned.
