"""
scripts/run_eval.py

Description:
    This script executes the batch evaluation runner for the Bachelor of AI thesis retrieval pipeline.
    It takes a set of pre-defined test queries and runs them across three distinct retrieval systems:
    1. Baseline RAG (Flat character-based chunks retrieved from raw PDF text).
    2. Structured RAG (Dense vector retrieval on generated structured Obsidian Markdown notes).
    3. Link-Expanded RAG (Graph-informed retrieval: starts with Structured RAG seeds, resolves Obsidian 
       [[WikiLinks]] to arXiv IDs, applies connectivity score boosting, and re-ranks the candidate pool).

Library and Coding Decisions:
    * PyMuPDF (fitz): Selected for layout-aware PDF text extraction.
    * SentenceTransformers (all-MiniLM-L6-v2): Selected for local vector embeddings. This is a lightweight 
      384-dimensional bi-encoder model from Hugging Face that computes semantic similarity locally.
    * Cosine Similarity (Scikit-Learn): Used as the primary vector similarity metric.
    * Independent code implementations: Avoids high-level framework wrappers (e.g. LangChain, LlamaIndex) 
      to ensure complete visibility, reproducibility, and prevent hidden adjustments from confounding results.

Usage:
    python scripts/run_eval.py
"""

import json
import sys
from pathlib import Path

# Add project root to path
repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from src.retrieval.baseline import retrieve as baseline_retrieve, load_index as load_baseline_index
from src.retrieval.structured import retrieve as structured_retrieve
from src.retrieval.link_expanded import retrieve_link_expanded

def main():
    queries_path = Path("data/queries/queries.json")
    baseline_index_path = Path("data/results/baseline_index.json")
    structured_index_path = Path("data/results/structured_index.json")
    notes_dir = Path("data/generated_notes")
    output_dir = Path("data/results")
    output_dir.mkdir(parents=True, exist_ok=True)

    if not queries_path.exists():
        print(f"Error: {queries_path} does not exist. Run scripts/generate_queries.py first.")
        sys.exit(1)

    if not baseline_index_path.exists():
        print(f"Error: {baseline_index_path} does not exist. Build the baseline index first.")
        sys.exit(1)

    with open(queries_path, encoding="utf-8") as f:
        queries = json.load(f)

    # 1. Run Baseline
    print("Running baseline retrieval...")
    docs, embeddings, model = load_baseline_index(str(baseline_index_path))
    baseline_run = {}
    for q in queries:
        qid = q["query_id"]
        text = q["text"]
        # Retrieve top 5 unique documents directly using MaxP aggregation
        retrieved_docs = baseline_retrieve(text, docs, embeddings, model, k=5, mode="baseline")
        baseline_run[qid] = [doc["doc_id"] for score, doc in retrieved_docs]

    with open(output_dir / "baseline_run.json", "w", encoding="utf-8") as f:
        json.dump(baseline_run, f, indent=2)

    # 2. Run Structured
    print("Running structured retrieval...")
    structured_run = {}
    for q in queries:
        qid = q["query_id"]
        text = q["text"]
        # Retrieve top 5 notes
        structured_run[qid] = structured_retrieve(text, structured_index_path, top_k=5)

    with open(output_dir / "structured_run.json", "w", encoding="utf-8") as f:
        json.dump(structured_run, f, indent=2)

    # 3. Run Link-Expanded
    print("Running link-expanded retrieval...")
    link_run = {}
    for q in queries:
        qid = q["query_id"]
        text = q["text"]
        # Retrieve top 5 re-ranked notes with a fixed alpha of 0.05
        link_run[qid] = retrieve_link_expanded(text, structured_index_path, notes_dir, top_k=5, graph_boost_alpha=0.05)

    with open(output_dir / "link_run.json", "w", encoding="utf-8") as f:
        json.dump(link_run, f, indent=2)

    print("All runs saved successfully in data/results/.")

if __name__ == "__main__":
    main()
