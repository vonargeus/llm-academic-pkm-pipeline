# Reproducibility Guide

This document provides the parameters and artefacts needed to reproduce the thesis experiments. Values listed here were checked against the local source code and result files on 2026-07-15.

---

## System Requirements

- Python 3.10+
- Windows 10/11 or Linux
- Approximately 4 GB disk space for PDFs and indexes
- Google Gemini API key

---

## Installation

```bash
git clone https://github.com/vonargeus/llm-academic-pkm-pipeline.git
cd llm-academic-pkm-pipeline
python -m venv .venv
.venv\Scripts\activate   # Windows
pip install -r requirements.txt
```

---

## LLM Configuration

All LLM components use the Google Gemini API. Set the key as an environment variable:

```bash
set GEMINI_API_KEY=your_key_here
set LLM_PROVIDER=gemini
```

The ingestion agents use a shared Google Gemini Flash-family wrapper with `temperature=0.0`. The configured pool starts with `gemini-flash-latest` and can rotate to other Gemini Flash-family endpoints after provider-side quota or rate-limit errors. This rotation is an availability mechanism, not an experimental model-comparison variable. The final RQ3 artefacts record the configured pool and explicitly note that the resolved endpoint was not logged for every request.

---

## Verified Fixed Parameters

| Parameter | Value | Source |
|-----------|-------|--------|
| Embedding model | `nomic-ai/nomic-embed-text-v1.5` | `src/retrieval/baseline.py`, `src/retrieval/structured.py` |
| Embedding prefixes | `search_document:` and `search_query:` | `src/retrieval/baseline.py`, `src/retrieval/structured.py` |
| Chunk size for Flat RAG | 512 tokens | `src/retrieval/baseline.py` |
| Chunk overlap for Flat RAG | 50 tokens | `src/retrieval/baseline.py` |
| Retrieval similarity | cosine similarity over normalised embeddings | `src/retrieval/baseline.py`, `src/retrieval/structured.py` |
| Primary retrieval cutoff | k = 5 | `data/results/retrieval_metrics.json`, `data/results/cv_report.json` |
| Link-Expanded RAG CV folds | 5, stratified by query category | `data/results/cv_report.json` |
| RQ1 query categories | 24 simple factual, 8 comparison, 8 neurosymbolic | `data/queries/queries.json` |
| LLM temperature | 0.0 | `src/agents/metadata_agent.py`, `rq3_final_predictions.json` |
| RQ3 requested initial LLM alias | `gemini-flash-latest` | `rq3_final_predictions.json` |
| RQ3 LLM execution mechanism | Gemini Flash-family model pool with availability-driven rotation | `rq3_final_predictions.json`, `src/agents/metadata_agent.py` |
| RQ3 per-request resolved endpoint logging | not logged | `rq3_final_predictions.json` |
| RQ2 strict topic overlap papers | 22 papers | `data/results/rq2_results.json` |
| RQ2 canonicalised topic split | 7 development / 15 test papers; test papers held out from selection of tau_d and k | `data/results/b1c_test_results.json` |
| RQ2 canonicalised tau_m | 0.7361, derived from the 49-label vocabulary across all 22 papers and frozen before agent-label mapping | `data/results/b1c_vocab_threshold.json` |
| RQ2 canonicalised best_k | 4 | `data/results/b1c_test_results.json` |
| RQ2 canonicalised tau_d | 0.85 | `data/results/b1c_test_results.json` |
| RQ3 final scored papers | 37 of 40 corpus papers | `rq3_final_results.json` |
| RQ3 unusable-gold exclusions | 3 papers: `2305.19951`, `2510.14538`, `2602.23878` | `rq3_final_results.json` per-paper statuses |
| RQ3 provider-block exclusions | 0 papers | `rq3_final_results.json` |
| RQ3 in-scope extraction failures | 2 output-truncated papers counted as false negatives: `1711.11157`, `2007.01282` | `rq3_final_results.json` |
| RQ3 invalid agent outputs filtered | 57 records | `rq3_final_results.json` |
| RQ3 final metrics | Precision = 0.8425, Recall = 0.7393, F1 = 0.7875 | `rq3_final_results.json` |
| RQ4 expert evaluation | 5 generated notes, 1 expert evaluator | Local expert-response workbook retained separately |
| RQ4 mean scores | Faithfulness = 3.8, Coverage = 3.0, Readability = 3.4, Utility = 3.2, overall = 3.35 | Local expert-response workbook retained separately |

The RQ3 audit metadata and per-paper statuses both record the same three unusable-gold exclusions.

---

## Execution Order

Each stage is a separate batch process run by the researcher. There is no autonomous orchestration between stages.

```text
Stage 1: PDF text extraction
  -> scripts/extract_pdfs.py
  -> produces extracted PDF text under data/extracted_text/

Stage 2: Metadata extraction
  -> src/agents/metadata_agent.py
  -> produces YAML frontmatter fields such as title, year, venue, authors, DOI, arXiv ID, and topics

Stage 3: Note generation
  -> src/agents/note_agent.py
  -> uses extracted PDF text plus metadata
  -> produces structured Markdown notes

Stage 4: Semantic link generation
  -> src/agents/link_agent.py
  -> uses generated notes
  -> produces wiki-links between related notes

RQ1 and RQ2 artefacts are frozen after Stage 4.

Stage 5: Citation reference extraction for RQ3
  -> rq3_final.ipynb
  -> uses the batched citation-extraction pipeline with deterministic per-entry fallback parsing
  -> extracts explicit bibliography/reference records from PDFs
  -> compares extracted references with Semantic Scholar outgoing reference lists
```

RQ3 evaluates citation-reference extraction against full outgoing Semantic Scholar reference lists, including external citations. The RQ3 gold standard is not restricted to references between papers in the local corpus.

---

## Data Sharing

| Artefact | Shared? | Format | Location |
|----------|---------|--------|----------|
| Paper corpus manifest | Yes | JSON | `data/raw_pdfs/manifest.json` |
| Raw PDFs | No, due to copyright | PDF | Download via `scripts/download_papers.py` |
| Extracted text | Yes | JSON | `data/extracted_text/` |
| Generated notes | Yes | Markdown | `data/generated_notes/` |
| Query set | Yes | JSON | `data/queries/queries.json` |
| Gold labels for retrieval | Yes | JSON | `data/gold_labels/gold_labels.json` |
| Expert topic annotations | Yes | JSON | `data/gold_labels/emile_vault_gold.json` |
| RQ1/RQ2 evaluation results | Yes | JSON | `data/results/` |
| RQ3 final metrics | Yes | JSON | `rq3_final_results.json` |
| RQ3 final predictions | Yes | JSON | `rq3_final_predictions.json` |
| RQ3 raw LLM responses | Optional audit artefact | JSON | `rq3_final_raw_responses.json` |
| RQ4 expert responses | Local evidence file | XLSX | Retained separately as a local evaluation artefact |
| Prompts | Yes | Markdown | `prompts/` |
| Code | Yes | Python / Notebook | `src/`, `scripts/`, selected notebooks |
| Thesis LaTeX | Yes | TeX | `thesis/` |

`data/gold_labels/link_gold.json` exists for local vault-link analysis, but it is not the primary RQ3 gold standard. RQ3 uses Semantic Scholar outgoing reference lists.

---

## Superseded Artefacts

The following artefacts are retained only for provenance or implementation comparison and should not be used as the final RQ3 thesis evidence:

- `rq3_citation_link_evaluation.ipynb`
- `data/results/rq3_citation_link_evaluation.json`

The final RQ3 evidence is `rq3_final_results.json` and its companion prediction/response files.

---

## Known Limitations Affecting Reproducibility

1. **LLM model rotation:** RQ3 records the configured Gemini Flash-family model pool and the first requested alias (`gemini-flash-latest`), but the resolved endpoint was not logged for every request. Exact replication of the hosted Gemini model build is therefore not guaranteed.

2. **LLM non-determinism:** Even at `temperature=0.0`, minor output variations may occur across API versions and dates.

3. **arXiv rate limits:** The download script includes delays between requests. Do not remove these delays when rebuilding the corpus.

4. **PDF extraction quality:** Some PDFs, especially two-column or scanned documents, may extract poorly. See `data/extracted_text/_extraction_summary.json` for per-paper extraction status.

5. **Semantic Scholar availability:** RQ3 gold reference lists depend on Semantic Scholar API availability. Three papers were excluded because usable gold references were unavailable.

6. **RQ3 extraction failures:** Two in-scope RQ3 papers produced output-truncated extraction failures. They remained in the evaluation and contributed false negatives.

7. **RQ4 scope:** RQ4 uses one expert and five generated notes, so it should be reported as an exploratory expert assessment rather than a generalisable user study.
