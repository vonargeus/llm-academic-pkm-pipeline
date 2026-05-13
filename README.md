# LLM Agents for Interlinked and Personalised Knowledge Bases

**Bachelor Thesis — Vrije Universiteit Amsterdam**  
**Student:** Muhammed Furkan Kaya  
**Supervisor:** Emile van Krieken (CS dept., AI: Learning and Reasoning)  
**Program:** B Artificial Intelligence  

---

## Project Overview

This project builds and evaluates an LLM-agent pipeline that processes academic PDFs and converts them into structured, interlinked Obsidian-style notes. The core research question is:

> *To what extent can an LLM agent improve retrieval in an Obsidian-style personal knowledge base by generating structured metadata and inter-note links from academic papers, compared to a simple RAG baseline?*

### Systems Compared

| System | Description |
|--------|-------------|
| **Baseline RAG** | Fixed-size chunking → embeddings → cosine similarity retrieval |
| **Structured Notes** | LLM-generated Obsidian notes with metadata and typed links → retrieval |
| **Link-Expanded** | Structured notes + link-expansion at retrieval time (ablation) |

### Evaluation Dimensions

1. **Retrieval quality** — Recall@k, Precision@k, F1@k, MRR (k = 1, 3, 5, 10)
2. **Metadata quality** — Field-level exact match + Precision/Recall/F1 for multi-label fields
3. **Link quality** — Link Precision, Recall, F1; hallucinated link count
4. **Summary quality** — Expert review of 20 samples by supervisor (supplementary)

---

## Repository Structure

```
thesis-obsidian-agent/
├── README.md
├── requirements.txt
├── pyproject.toml
├── configs/
│   ├── baseline.yaml         # Baseline RAG config
│   ├── structured.yaml       # Structured note system config
│   └── evaluation.yaml       # Evaluation config
├── data/
│   ├── raw_pdfs/             # Downloaded arXiv PDFs
│   ├── extracted_text/       # Plain-text extractions (JSON)
│   ├── generated_notes/      # LLM-generated Obsidian notes (Markdown)
│   ├── queries/              # Evaluation query set (JSON)
│   ├── gold_labels/          # Relevance labels per (query, note) pair
│   └── results/              # Evaluation metric outputs
├── src/
│   ├── ingestion/            # PDF download + text extraction
│   ├── chunking/             # Fixed-size chunker for baseline
│   ├── agents/               # Metadata, Note, Link agents
│   ├── note_generation/      # Orchestration: PDF → note → links
│   ├── metadata_extraction/  # Utilities for metadata parsing
│   ├── link_generation/      # Link candidate retrieval + LLM typing
│   ├── retrieval/            # Baseline, structured, link-expanded retrievers
│   └── evaluation/           # Retrieval, metadata, link evaluators
├── prompts/
│   ├── metadata_agent.md     # Metadata extraction prompt
│   ├── paper_note_agent.md   # Note generation prompt
│   ├── link_agent.md         # Link generation + typing prompt
│   └── summary_agent.md      # Summary generation prompt
├── notebooks/                # Exploratory analysis
├── thesis/                   # LaTeX thesis source
├── scripts/
│   ├── download_papers.py    # Download arXiv PDFs
│   ├── extract_pdfs.py       # Extract text from PDFs
│   ├── build_baseline_index.py
│   ├── generate_notes.py     # Run agent pipeline
│   ├── generate_links.py
│   ├── run_retrieval_eval.py
│   └── run_full_eval.py      # End-to-end evaluation
└── docs/
    ├── dataset.md            # Dataset construction decisions
    ├── related_work_table.md # Related work methodology extraction
    ├── annotation_guidelines.md
    └── reproducibility.md
```

---

## Setup

```bash
# Create and activate virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

### Required API Key

Set your LLM API key (default: Google Gemini):
```bash
set GEMINI_API_KEY=your_key_here
```

---

## Quickstart

```bash
# 1. Download papers
python scripts/download_papers.py --output data/raw_pdfs/

# 2. Extract text
python scripts/extract_pdfs.py --input data/raw_pdfs/ --output data/extracted_text/

# 3. Build baseline RAG index
python scripts/build_baseline_index.py --input data/raw_pdfs/ --output data/results/baseline_index.json

# 4. Generate structured notes + links
python scripts/generate_notes.py --input data/extracted_text/ --output data/generated_notes/

# 5. Run full evaluation
python scripts/run_full_eval.py --queries data/queries/queries.json \
    --gold data/gold_labels/gold_labels.json \
    --output data/results/
```

---

## Reproducibility

All experiments use:
- **Embedding model:** `all-MiniLM-L6-v2` (sentence-transformers)
- **LLM:** Google Gemini 1.5 Flash (version pinned in `configs/`)
- **Temperature:** 0.0 for metadata/link generation; 0.3 for note/summary generation
- **Chunking:** 800 tokens, 120-token overlap
- **k values:** 1, 3, 5, 10

See `docs/reproducibility.md` for full details.

---

## License

Code: MIT. See `LICENSE`.  
PDFs: Not redistributed. Only arXiv IDs and DOIs are shared. See `data/raw_pdfs/README.md`.  
Thesis text: © Muhammed Furkan Kaya, 2026.
