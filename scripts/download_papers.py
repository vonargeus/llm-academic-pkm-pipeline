"""
download_papers.py — Download arXiv PDFs for the thesis corpus.

Usage:
    python scripts/download_papers.py --output data/raw_pdfs/
    python scripts/download_papers.py --output data/raw_pdfs/ --ids 2005.11401 2404.16130

The default list is the curated thesis corpus. You can override with --ids.
"""

import argparse
import json
import os
import time
from pathlib import Path

import arxiv

# ---------------------------------------------------------------------------
# Curated corpus: arXiv paper IDs for the thesis dataset
# Organised by category. Edit this list to add/remove papers.
# ---------------------------------------------------------------------------
CORPUS = [
    # ── RAG ──────────────────────────────────────────────────────────────
    {"id": "2005.11401", "label": "Lewis et al. 2020 — Retrieval-Augmented Generation",           "category": "RAG"},
    {"id": "2007.01282", "label": "Izacard & Grave 2020 — Fusion-in-Decoder",                    "category": "RAG"},
    {"id": "2310.11511", "label": "Asai et al. 2023 — Self-RAG: Self-Reflective Retrieval",       "category": "RAG"},
    {"id": "2401.15884", "label": "Yan et al. 2024 — Corrective RAG (CRAG)",                     "category": "RAG"},
    {"id": "2309.15217", "label": "Es et al. 2023 — RAGAS: RAG Evaluation Framework",            "category": "RAG_Eval"},
    # ── Graph-Enhanced RAG ───────────────────────────────────────────────
    {"id": "2404.16130", "label": "Edge et al. 2024 — GraphRAG: From Local to Global",           "category": "GraphRAG"},
    {"id": "2410.05779", "label": "Guo et al. 2024 — LightRAG: Graph + Vector RAG",              "category": "GraphRAG"},
    {"id": "2405.14831", "label": "Gutierrez et al. 2024 — HippoRAG: Memory-Inspired RAG",       "category": "GraphRAG"},
    # ── Hierarchical / Structured RAG ────────────────────────────────────
    {"id": "2401.18059", "label": "Sarthi et al. 2024 — RAPTOR: Hierarchical Tree Retrieval",    "category": "HierarchicalRAG"},
    # ── Agentic / LLM Memory ─────────────────────────────────────────────
    {"id": "2502.12110", "label": "A-MEM: Agentic Memory for LLM Agents (Zettelkasten)",         "category": "AgenticMemory"},
    {"id": "2310.08560", "label": "Packer et al. 2023 — MemGPT: LLMs as Operating Systems",     "category": "AgenticMemory"},
    {"id": "2305.10250", "label": "Zhong et al. 2023 — MemoryBank: Long-Term Memory for LLMs",  "category": "AgenticMemory"},
    {"id": "2409.05591", "label": "Qian et al. 2024 — MemoRAG: Memory-Augmented Generation",    "category": "AgenticMemory"},
    # ── Personal Knowledge Graphs / PKM ──────────────────────────────────
    {"id": "2306.07516", "label": "Balog & Kenter 2023 — Personal Knowledge Graphs Survey",      "category": "PKG"},
    # ── Structured Writing / Synthesis ───────────────────────────────────
    {"id": "2402.14207", "label": "Shao et al. 2024 — STORM: Long-Form Article Writing Agent",  "category": "StructuredSynthesis"},
    # ── Evaluation / Benchmarks ───────────────────────────────────────────
    {"id": "2402.17753", "label": "Maharana et al. 2024 — LoCoMo: Long-Context Memory Eval",    "category": "MemoryEval"},
    # ── Document Understanding ────────────────────────────────────────────
    {"id": "2406.14177", "label": "Ma et al. 2024 — MDocAgent: Multi-modal Document Agent",     "category": "DocumentUnderstanding"},
    # ── Scientific Information Extraction ────────────────────────────────
    {"id": "2210.06726", "label": "Lo et al. 2022 — ORKG: Scholarly Knowledge Graphs",          "category": "ScientificIE"},
]
# ---------------------------------------------------------------------------


def download_corpus(output_dir: Path, ids: list[str] | None = None, delay: float = 3.0):
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = output_dir / "manifest.json"

    if ids:
        targets = [{"id": i, "label": i, "category": "custom"} for i in ids]
    else:
        targets = CORPUS

    manifest = {}
    client = arxiv.Client()

    for entry in targets:
        arxiv_id = entry["id"]
        safe_id = arxiv_id.replace("/", "_")
        pdf_path = output_dir / f"{safe_id}.pdf"

        if pdf_path.exists():
            print(f"[skip]  {arxiv_id}  (already downloaded)")
            manifest[arxiv_id] = {
                "path": str(pdf_path),
                "label": entry["label"],
                "category": entry["category"],
                "status": "cached",
            }
            continue

        print(f"[fetch] {arxiv_id}  {entry['label'][:60]}")
        try:
            search = arxiv.Search(id_list=[arxiv_id])
            results = list(client.results(search))
            if not results:
                print(f"  [Warning] Not found: {arxiv_id}")
                manifest[arxiv_id] = {"status": "not_found", **entry}
                continue

            paper = results[0]
            paper.download_pdf(dirpath=str(output_dir), filename=f"{safe_id}.pdf")

            manifest[arxiv_id] = {
                "path": str(pdf_path),
                "label": entry["label"],
                "category": entry["category"],
                "title": paper.title,
                "authors": [str(a) for a in paper.authors],
                "year": paper.published.year if paper.published else None,
                "abstract": paper.summary[:500],
                "status": "ok",
            }
            print(f"  [OK] saved -> {pdf_path.name}")
            time.sleep(delay)  # be polite to arXiv

        except Exception as e:
            print(f"  [Error] {e}")
            manifest[arxiv_id] = {"status": "error", "error": str(e), **entry}

    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    n_ok = sum(1 for v in manifest.values() if v.get("status") in ("ok", "cached"))
    print(f"\nDone: {n_ok}/{len(targets)} papers downloaded. Manifest -> {manifest_path}")


def main():
    parser = argparse.ArgumentParser(description="Download arXiv papers for thesis corpus.")
    parser.add_argument("--output", default="data/raw_pdfs", help="Output directory for PDFs")
    parser.add_argument("--ids", nargs="*", help="Override: specific arXiv IDs to download")
    parser.add_argument("--delay", type=float, default=3.0, help="Seconds between requests (default 3)")
    args = parser.parse_args()

    download_corpus(Path(args.output), ids=args.ids, delay=args.delay)


if __name__ == "__main__":
    main()
