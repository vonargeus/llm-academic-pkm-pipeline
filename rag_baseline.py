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