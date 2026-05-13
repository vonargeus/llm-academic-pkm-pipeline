"""
structured.py — Retrieval module for the structured note system.

Embeds full Obsidian Markdown notes and retrieves them via cosine similarity.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

def build_structured_index(notes_dir: Path, output_path: Path, model_name: str = "all-MiniLM-L6-v2"):
    """
    Build a dense retrieval index over structured Obsidian notes.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"Loading embedding model: {model_name}...")
    model = SentenceTransformer(model_name)
    
    note_files = sorted(notes_dir.glob("*.md"))
    if not note_files:
        print(f"No Markdown notes found in {notes_dir}")
        return
        
    doc_ids = []
    texts = []
    
    print(f"Embedding {len(note_files)} notes...")
    for md_path in note_files:
        text = md_path.read_text(encoding="utf-8")
        doc_ids.append(md_path.stem)
        texts.append(text)
        
    embeddings = model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)
    
    # Save the index
    index_data = {
        "doc_ids": doc_ids,
        "embeddings": embeddings.tolist(),
        "model": model_name
    }
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(index_data, f)
        
    print(f"Index built and saved to {output_path}")
    return index_data

def retrieve(query: str, index_path: Path, top_k: int = 10) -> list[str]:
    """Retrieve top-k documents for a query."""
    with open(index_path, encoding="utf-8") as f:
        index_data = json.load(f)
        
    model_name = index_data.get("model", "all-MiniLM-L6-v2")
    model = SentenceTransformer(model_name)
    
    query_emb = model.encode([query], convert_to_numpy=True, normalize_embeddings=True)
    doc_embs = np.array(index_data["embeddings"])
    
    similarities = cosine_similarity(query_emb, doc_embs)[0]
    
    # Sort by similarity descending
    top_indices = np.argsort(similarities)[::-1][:top_k]
    
    return [index_data["doc_ids"][i] for i in top_indices]

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--notes", default="data/generated_notes", help="Directory with Markdown notes")
    parser.add_argument("--output", default="data/results/structured_index.json", help="Path to save index")
    parser.add_argument("--model", default="all-MiniLM-L6-v2", help="Embedding model")
    args = parser.parse_args()
    
    build_structured_index(Path(args.notes), Path(args.output), args.model)
