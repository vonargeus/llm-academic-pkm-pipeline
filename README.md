# LLM Agents for Interlinked and Personalised Knowledge Bases

Bachelor thesis project by Muhammed Furkan Kaya, Vrije Universiteit Amsterdam.

This repository contains a modular LLM-based pipeline that transforms academic
PDFs into structured, interlinked Obsidian Markdown notes. The thesis evaluates
the pipeline as a collection of distinct tasks rather than assuming that richer
notes or additional links automatically improve retrieval.

## Study Overview

The evaluation uses a focused collection of 40 academic papers and addresses
four research questions:

1. **RQ1 - Retrieval:** comparison of Flat RAG, Structured RAG, and
   Link-Expanded RAG over 40 retrieval queries.
2. **RQ2 - Metadata and topics:** bibliographic extraction over all 40 papers,
   strict topic matching over 22 papers with expert annotations, and a separate
   canonicalised topic sensitivity analysis.
3. **RQ3 - Citation references:** extraction of explicit bibliography records
   compared with Semantic Scholar outgoing reference lists.
4. **RQ4 - Expert evaluation:** exploratory assessment of five generated notes
   by one expert.

The semantic links are not evaluated against an edge-level gold standard. RQ1
measures the aggregate downstream retrieval behaviour of the link-expansion
configuration.

## Pipeline

The implementation has a shared PDF text-extraction stage and two logically
separate downstream paths.

```text
Academic PDF
  -> PyMuPDF text extraction
  -> JSON text record
      |
      +-> Metadata extraction
      |   -> structured note generation
      |   -> typed semantic wiki-link generation
      |   -> Markdown/YAML knowledge base
      |
      +-> Reference-section detection
          -> batched citation-record extraction
          -> deterministic per-entry fallback when required
          -> optional resolution to local Obsidian wiki-links
```

The ingestion stages are separate batch processes initiated by the researcher;
the project is not an autonomous multi-agent system.

## Retrieval Configurations

- **Flat RAG:** PDF-derived text is tokenised with the embedding model's native
  tokenizer and split into 512-token chunks with a 50-token overlap. Chunks are
  embedded independently and paper scores are produced using MaxP aggregation.
- **Structured RAG:** each complete generated Markdown note is represented by
  one paper-level embedding. Paper wiki-links are removed before embedding,
  while topic and concept links are retained as plain text.
- **Link-Expanded RAG:** Structured RAG scores are reused, the five
  highest-ranked notes form the seed set, and eligible one-hop outbound paper
  neighbours receive a fold-selected score boost before reranking.

All three configurations use
`nomic-ai/nomic-embed-text-v1.5`, the `search_document:` and `search_query:`
prefixes, L2-normalised embeddings, and cosine similarity.

## Frozen Results

### RQ1: Retrieval at k = 5

| Configuration | Recall@5 | Precision@5 | MRR@5 |
|---|---:|---:|---:|
| Flat RAG | 0.696 | 0.235 | 0.729 |
| Structured RAG | 0.696 | 0.225 | 0.744 |
| Link-Expanded RAG | 0.719 | 0.230 | 0.742 |

Flat and Structured RAG were evaluated over all 40 queries. The
Link-Expanded row contains aggregated out-of-fold predictions from five-fold
cross-validation stratified by query category.

### RQ2: Metadata and Topic Labels

| Evaluation | Precision | Recall | F1 / accuracy |
|---|---:|---:|---:|
| Title exact match (40 papers) | - | - | 0.975 |
| Year exact match (40 papers) | - | - | 0.775 |
| Venue fuzzy match (40 papers) | - | - | 0.500 |
| Author-set matching (40 papers) | 0.822 | 0.829 | 0.825 |
| Strict topic overlap (22 papers) | 0.076 | 0.151 | 0.096 |
| Canonicalised 15-paper subset | 0.339 | 0.476 | 0.383 |

The strict and canonicalised topic rows use different matching procedures and
evaluation subsets and must not be interpreted as a controlled before/after
comparison. For the canonicalised analysis, the 49-label vocabulary and
mapping threshold were derived across the 22 annotated papers. Only the
near-duplicate threshold and maximum retained topic count were selected on the
seven-paper development subset before application to the separate 15-paper
evaluation subset.

### RQ3: Citation-Reference Extraction

The final evaluation scored 37 papers; three papers without usable gold
reference lists were excluded. Two in-scope model-output failures remained in
the scored set and their missed references contributed to the false-negative
count.

| TP | FP | FN | Precision | Recall | F1 |
|---:|---:|---:|---:|---:|---:|
| 1,514 | 283 | 534 | 0.843 | 0.739 | 0.788 |

### RQ4: Exploratory Expert Evaluation

Five generated notes were rated by one expert on a five-point scale.

| Dimension | Mean |
|---|---:|
| Factual faithfulness | 3.8 |
| Core-contribution coverage | 3.0 |
| Structure and readability | 3.4 |
| Utility for rediscovery | 3.2 |
| Overall | 3.35 |

The RQ4 evidence workbook is retained separately and is not included in this
public repository.

## Repository Structure

```text
configs/                     Legacy configuration files; not authoritative
data/
  extracted_text/            PyMuPDF-derived JSON text records
  generated_notes/           Generated Markdown/YAML notes
  gold_labels/               Retrieval and expert-vault reference labels
  queries/                   RQ1 query set
  results/                   Frozen RQ1 and RQ2 outputs
docs/
  reproducibility.md         Parameters, artefact map, and limitations
prompts/                     Version-controlled ingestion prompts
scripts/                     Corpus preparation and evaluation utilities
src/
  agents/                    Metadata, note, semantic-link, and citation logic
  note_generation/           Predetermined ingestion workflow
  retrieval/                 Final Flat, Structured, and Link-Expanded retrieval
thesis/                      Thesis source and figures
rq1_experimental_suite.ipynb Final RQ1 experimental driver
rq2_metadata_evaluation.ipynb
rq2_calibration.ipynb        RQ2 evaluation and canonicalisation drivers
rq3_final.ipynb              Final batched RQ3 experimental driver
rq3_final_*.json             Final RQ3 audit and result artefacts
```

See [`docs/reproducibility.md`](docs/reproducibility.md) for the complete
parameter and artefact map.

## Installation

Python 3.10 or later is recommended.

```powershell
git clone https://github.com/vonargeus/llm-academic-pkm-pipeline.git
cd llm-academic-pkm-pipeline
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Set `GEMINI_API_KEY` in `.env` before running an LLM-backed stage. Do not
commit `.env`.

The ingestion agents use a shared Gemini Flash-family wrapper with temperature
`0.0`. The wrapper can rotate among configured Flash-family endpoints after
quota or rate-limit errors. This is an availability mechanism, not a model
comparison. Because the resolved endpoint was not logged for every request,
exact reproduction of hosted-model behaviour is limited.

## Core Commands

Raw PDFs are not redistributed. The corpus can be reconstructed from the
manifest and arXiv identifiers where the source remains available.

```powershell
# Download corpus PDFs
python scripts/download_papers.py --output data/raw_pdfs

# Extract PDF text to JSON
python scripts/extract_pdfs.py --input data/raw_pdfs --output data/extracted_text

# Generate structured notes and semantic links (requires Gemini API access)
python scripts/generate_notes.py --input data/extracted_text --output data/generated_notes

# Build the final Flat RAG index
python -m src.retrieval.baseline build `
  --data-dir data/raw_pdfs `
  --index data/results/baseline_index.json

# Build the Structured RAG index
python -m src.retrieval.structured `
  --notes data/generated_notes `
  --output data/results/structured_index.json
```

The notebooks contain the final experimental orchestration and saved outputs.
Re-running LLM-backed experiments may produce different responses or encounter
provider availability changes; use the frozen result artefacts when checking
the reported thesis values.

## Authoritative and Superseded Artefacts

Use these as the final evidence:

- RQ1: `data/results/retrieval_metrics.json` and
  `data/results/cv_report.json`
- RQ2: `data/results/rq2_results.json`,
  `data/results/b1c_vocab_threshold.json`, and
  `data/results/b1c_test_results.json`
- RQ3: `rq3_final_results.json`, `rq3_final_predictions.json`, and
  `rq3_final_raw_responses.json`

The following are retained only for provenance or older implementation
comparison and are not the final thesis evidence:

- `rag_baseline.py`
- `configs/baseline.yaml` and `configs/structured.yaml`
- `rq3_citation_link_evaluation.ipynb`
- `data/results/rq3_citation_link_evaluation.json`

## Data and Reproducibility Notes

- Raw PDFs are excluded because redistribution rights vary.
- Extracted text, generated notes, prompts, queries, labels, and frozen result
  artefacts are included.
- RQ1 relevance judgements, RQ2 expert topic annotations, and RQ4 ratings each
  rely on one annotator or expert source.
- The corpus is a focused personal research collection, so results should not
  be treated as population-level estimates across scientific domains.
- Semantic Scholar availability and record quality affect the RQ3 gold data.

## License

The source code is released under the MIT License. See [`LICENSE`](LICENSE).
The thesis text remains copyright Muhammed Furkan Kaya, 2026.
