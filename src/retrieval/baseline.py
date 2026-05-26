"""
RAG Baseline implementation for Bachelor Thesis evaluation.

This script implements a standard, flat Retrieval-Augmented Generation (RAG) retrieval pipeline. 
To ensure academic rigor, reproducibility, and mathematical transparency, this pipeline is built 
using raw scientific libraries rather than higher-level orchestration frameworks (like LangChain or LlamaIndex).
This prevents "framework magic" (hidden prompting, automatic chunk slicing, undocumented vector operations) 
from confounding the experimental results.

### Library Selection & Technical Justifications:
1. `fitz` (PyMuPDF): Chosen for fast, standard, and highly accurate plain-text extraction from academic PDFs. 
   Unlike heavier OCR-based tools, PyMuPDF reads PDF text layout blocks sequentially, which is crucial for multi-column research papers.
2. `sentence_transformers`: The industry standard library for generating dense vector embeddings from text.
   We use the `all-MiniLM-L6-v2` model which embeds inputs into a 384-dimensional space.
3. `scikit-learn` (`cosine_similarity`): Cosine similarity is the mathematically standard metric used to measure 
   alignment between query vectors and document chunk vectors. We implement this directly using scikit-learn to maintain 
   mathematical precision and avoid database-specific rounding differences.
4. `numpy`: Used for high-performance vector manipulation and sorting.
5. `re` (Regular Expressions): Used to clean extracted PDF spacing and extract Obsidian-style WikiLinks ([[link_target]]) from text blocks.

### Chunking Logic & Token-to-Character Proxy:
The embedding model (`all-MiniLM-L6-v2`) has a maximum sequence limit of 256 tokens. 
To avoid silent truncation during embedding generation, this script chunks text into blocks of 300 characters with an overlap of 50 characters.
* Character count vs. Token count proxy: In English text, 300 characters is a safe proxy for roughly 60–80 tokens.
* By using a conservative 300-character boundary, we guarantee that every chunk fits comfortably within the model's 256-token limit,
  completely preventing data loss or truncation at indexing time.
"""

import os
import re
import json
import argparse
from pathlib import Path

import fitz  # PyMuPDF
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity


def extract_pdf_text(pdf_path: Path) -> str:
    doc = fitz.open(pdf_path)
    parts = []
    for page in doc:
        text = page.get_text("text")
        if text:
            parts.append(text)
    return "\n".join(parts)


def split_text(text: str, chunk_size: int = 300, overlap: int = 50):
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return []

    chunks = []
    start = 0
    while start < len(text):
        end = min(len(text), start + chunk_size)
        chunk = text[start:end]
        chunks.append(chunk)
        if end == len(text):
            break
        start = max(0, end - overlap)
    return chunks


def find_wikilinks(text: str):
    return re.findall(r"\[\[([^\]]+)\]\]", text)


def build_index(data_dir: str, index_path: str, model_name: str = "all-MiniLM-L6-v2"):
    data_path = Path(data_dir)
    pdf_files = list(data_path.glob("*.pdf"))
    txt_files = list(data_path.glob("*.txt")) + list(data_path.glob("*.md"))

    docs = []

    for pdf in pdf_files:
        text = extract_pdf_text(pdf)
        chunks = split_text(text)
        for i, chunk in enumerate(chunks):
            docs.append({
                "doc_id": pdf.stem,
                "source": str(pdf),
                "chunk_id": i,
                "text": chunk,
                "links": find_wikilinks(chunk),
            })

    for txt in txt_files:
        text = txt.read_text(encoding="utf-8", errors="ignore")
        chunks = split_text(text)
        for i, chunk in enumerate(chunks):
            docs.append({
                "doc_id": txt.stem,
                "source": str(txt),
                "chunk_id": i,
                "text": chunk,
                "links": find_wikilinks(chunk),
            })

    if not docs:
        raise ValueError(f"No .pdf, .txt, or .md files found in {data_dir}")

    model = SentenceTransformer(model_name)
    texts = [d["text"] for d in docs]
    embeddings = model.encode(texts, normalize_embeddings=True)

    payload = {
        "model_name": model_name,
        "docs": docs,
        "embeddings": embeddings.tolist(),
    }

    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(payload, f)

    print(f"Built index with {len(docs)} chunks from {len(pdf_files) + len(txt_files)} files.")
    print(f"Saved to {index_path}")


def load_index(index_path: str):
    with open(index_path, "r", encoding="utf-8") as f:
        payload = json.load(f)
    docs = payload["docs"]
    embeddings = np.array(payload["embeddings"], dtype=np.float32)
    model = SentenceTransformer(payload["model_name"])
    return docs, embeddings, model


def retrieve(query: str, docs, embeddings, model, k: int = 5, mode: str = "baseline"):
    q_emb = model.encode([query], normalize_embeddings=True)
    scores = cosine_similarity(q_emb, embeddings)[0]
    top_idx = np.argsort(scores)[::-1][:k]

    results = []
    seen = set()

    for idx in top_idx:
        seen.add(int(idx))
        results.append((float(scores[idx]), docs[idx]))

    if mode == "linked":
        top_doc_ids = {docs[idx]["doc_id"] for idx in top_idx}
        linked_idxs = []
        for i, d in enumerate(docs):
            if i in seen:
                continue
            linked_targets = set(d.get("links", []))
            if linked_targets & top_doc_ids:
                linked_idxs.append(i)

        if linked_idxs:
            linked_scores = [(float(scores[i]) + 0.05, docs[i]) for i in linked_idxs]
            linked_scores = sorted(linked_scores, key=lambda x: x[0], reverse=True)
            for item in linked_scores[:k]:
                results.append(item)

        results = sorted(results, key=lambda x: x[0], reverse=True)[:k]

    return results


def ask(index_path: str, question: str, mode: str = "baseline", k: int = 5):
    docs, embeddings, model = load_index(index_path)
    results = retrieve(question, docs, embeddings, model, k=k, mode=mode)

    print(f"\nQUESTION: {question}")
    print(f"MODE: {mode}\n")

    for rank, (score, doc) in enumerate(results, start=1):
        print("=" * 80)
        print(f"Rank: {rank}")
        print(f"Score: {score:.4f}")
        print(f"Doc ID: {doc['doc_id']}")
        print(f"Source: {doc['source']}")
        print(f"Chunk ID: {doc['chunk_id']}")
        print(f"Links: {doc.get('links', [])}")
        print("-" * 80)
        print(doc["text"][:1000])
        print()

    print("=" * 80)


def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    build_parser = subparsers.add_parser("build")
    build_parser.add_argument("--data-dir", required=True)
    build_parser.add_argument("--index", required=True)

    ask_parser = subparsers.add_parser("ask")
    ask_parser.add_argument("--index", required=True)
    ask_parser.add_argument("--question", required=True)
    ask_parser.add_argument("--mode", choices=["baseline", "linked"], default="baseline")
    ask_parser.add_argument("--k", type=int, default=5)

    args = parser.parse_args()

    if args.command == "build":
        build_index(args.data_dir, args.index)
    elif args.command == "ask":
        ask(args.index, args.question, args.mode, args.k)


if __name__ == "__main__":
    main()