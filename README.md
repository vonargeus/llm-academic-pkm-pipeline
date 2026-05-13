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
| **Baseline RAG** | Fixed-size chunking (300 tokens) → embeddings → cosine similarity retrieval |
| **Structured Notes** | LLM-generated Obsidian notes with metadata and typed links → retrieval |
| **Link-Expanded** | Structured notes + link-expansion at retrieval time (ablation) |

---

## Repository Structure

```
Bsc_Project/
├── rag_baseline.py           # Standard RAG baseline (build/ask)
├── requirements.txt
├── configs/
│   ├── structured.yaml       # Structured note system config
│   └── evaluation.yaml       # Evaluation config
├── data/
│   ├── raw_pdfs/             # Downloaded arXiv PDFs
│   ├── extracted_text/       # Plain-text extractions (JSON)
│   ├── generated_notes/      # LLM-generated Obsidian notes (Markdown)
│   ├── queries/              # Evaluation query set (JSON)
│   ├── gold_labels/          # Gold standard labels
│   └── results/              # Evaluation metric outputs
├── src/
│   ├── agents/               # Metadata, Note, Link agents
│   ├── note_generation/      # Orchestration
│   ├── retrieval/            # Baseline and structured retrievers
│   └── evaluation/           # Metric calculators
├── prompts/
│   ├── metadata_agent.md     # Metadata extraction prompt
│   ├── paper_note_agent.md   # Note generation prompt
│   └── link_agent.md         # Link generation prompt
├── thesis/                   # LaTeX thesis source
└── scripts/
    ├── download_papers.py    # Download arXiv PDFs
    ├── extract_pdfs.py       # Extract text from PDFs
    ├── generate_notes.py     # Run agent pipeline
    └── parse_emile_vault.py  # Create gold labels from expert vault
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

The system uses **Gemini 2.0 Flash**. Add your key to a `.env` file:
```env
GEMINI_API_KEY=your_key_here
```

---

## Quickstart

```bash
# 1. Download papers (from arXiv manifest)
python scripts/download_papers.py

# 2. Extract text from PDFs
python scripts/extract_pdfs.py

# 3. Build baseline RAG index (uses 300-token chunks)
python rag_baseline.py build --data-dir data/raw_pdfs/ --index data/results/baseline_index.json

# 4. Generate structured notes + links (requires API key)
python scripts/generate_notes.py

# 5. Ask a question to the baseline
python rag_baseline.py ask --index data/results/baseline_index.json --question "What is RAG?"
```

---

## Reproducibility

All experiments use:
- **Embedding model:** `all-MiniLM-L6-v2` (sentence-transformers)
- **LLM:** Google Gemini 2.0 Flash
- **Temperature:** 0.0 for metadata/link generation; 0.3 for note/summary generation
- **Chunking:** 300 tokens, 50-token overlap
- **k values:** 1, 3, 5, 10

---

## License

Code: MIT.  
Thesis text: © Muhammed Furkan Kaya, 2026.
