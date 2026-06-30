"""
src/retrieval/baseline.py

Description:
    RAG Baseline implementation for Bachelor Thesis evaluation.
    Implements token-based chunking and Max-Passage (MaxP) document-level retrieval.
"""

import os
import re
import json
import argparse
import sys
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


def split_text_by_tokens(text: str, tokenizer, chunk_size: int = 512, overlap: int = 50) -> list[str]:
    """
    Chunks text by tokens using the model's native tokenizer to prevent silent 
    truncation or word-level splitting.
    """
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return []

    # Encode raw text into token IDs
    tokens = tokenizer.encode(text, add_special_tokens=False)
    
    chunks = []
    start = 0
    while start < len(tokens):
        end = min(len(tokens), start + chunk_size)
        chunk_tokens = tokens[start:end]
        # Decode token IDs back to plain text
        chunk_text = tokenizer.decode(chunk_tokens)
        chunks.append(chunk_text)
        if end == len(tokens):
            break
        start = max(0, end - overlap)
        
    return chunks


def find_wikilinks(text: str):
    return re.findall(r"\[\[([^\]]+)\]\]", text)


def build_index(data_dir: str, index_path: str, model_name: str = "nomic-ai/nomic-embed-text-v1.5"):
    data_path = Path(data_dir)
    pdf_files = list(data_path.glob("*.pdf"))
    txt_files = [f for f in data_path.glob("*.txt") if f.name.lower() != "readme.md"] + \
                [f for f in data_path.glob("*.md") if f.name.lower() != "readme.md"]

    print(f"Loading embedding model: {model_name}...")
    model = SentenceTransformer(model_name, trust_remote_code=True)
    tokenizer = model.tokenizer

    docs = []

    print("Extracting and token-chunking files...")
    for pdf in pdf_files:
        text = extract_pdf_text(pdf)
        chunks = split_text_by_tokens(text, tokenizer, chunk_size=512, overlap=50)
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
        chunks = split_text_by_tokens(text, tokenizer, chunk_size=512, overlap=50)
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

    # Prepend the required Nomic document prefix before embedding
    print(f"Embedding {len(docs)} chunks...")
    prefixed_texts = ["search_document: " + d["text"] for d in docs]
    embeddings = model.encode(prefixed_texts, normalize_embeddings=True)

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
    model = SentenceTransformer(payload["model_name"], trust_remote_code=True)
    return docs, embeddings, model


def retrieve(query: str, docs, embeddings, model, k: int = 5, mode: str = "baseline"):
    """
    Performs Max-Passage (MaxP) document-level retrieval.
    Assigns each parent document the score of its single most relevant chunk.
    """
    # Prepend required Nomic search query prefix
    query_text = "search_query: " + query
    q_emb = model.encode([query_text], normalize_embeddings=True)
    scores = cosine_similarity(q_emb, embeddings)[0]

    # MaxP aggregation: group chunk scores by doc_id and find the maximum score per doc
    doc_max_scores = {}
    for idx, score in enumerate(scores):
        doc_id = docs[idx]["doc_id"]
        if doc_id not in doc_max_scores or score > doc_max_scores[doc_id]:
            doc_max_scores[doc_id] = float(score)

    # Sort documents by their aggregated MaxP score in descending order
    sorted_docs = sorted(doc_max_scores.items(), key=lambda x: x[1], reverse=True)

    # Format output as (score, {"doc_id": doc_id}) for pipeline compatibility
    results = []
    for doc_id, score in sorted_docs[:k]:
        results.append((score, {"doc_id": doc_id}))

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
    ask_parser.add_argument("--mode", choices=["baseline"], default="baseline")
    ask_parser.add_argument("--k", type=int, default=5)

    args = parser.parse_args()

    if args.command == "build":
        build_index(args.data_dir, args.index)
    elif args.command == "ask":
        ask(args.index, args.question, args.mode, args.k)


if __name__ == "__main__":
    main()