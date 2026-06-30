"""
src/retrieval/structured.py

Description:
    Structured note retrieval module.
    Embeds cleaned agent-generated notes and retrieves them via cosine similarity.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity


def clean_markdown_links(text: str) -> str:
    """
    Removes Markdown wiki-links to prevent graph relation leakage in Pipeline B:
    - Strips citation paper links completely (e.g. [[2005.11401]]).
    - Replaces topic links (e.g. [[semantic loss]]) with their display text.
    """
    # 1. Strip absolute citation links / arXiv IDs completely (e.g. [[2005.11401]])
    text = re.sub(r'\[\[\d{4}\.\d{4,5}(\|[^\]]+)?\]\]', '', text)
    
    # 2. Replace aliased links [[Topic Name|display text]] with just display text
    text = re.sub(r'\[\[[^\]|]+\|([^\]]+)\]\]', r'\1', text)
    
    # 3. Replace simple concept links [[Topic Name]] with Topic Name
    text = re.sub(r'\[\[([^\]]+)\]\]', r'\1', text)
    
    return text


def build_structured_index(notes_dir: Path, output_path: Path, model_name: str = "nomic-ai/nomic-embed-text-v1.5"):
    """
    Build a dense retrieval index over structured Obsidian notes, cleaning links 
    to isolate textual content from graph topology.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"Loading embedding model: {model_name}...")
    model = SentenceTransformer(model_name, trust_remote_code=True)
    max_seq_length = model.max_seq_length
    print(f"Embedding model max context limit: {max_seq_length} tokens.")
    
    note_files = sorted(notes_dir.glob("*.md"))
    if not note_files:
        print(f"No Markdown notes found in {notes_dir}")
        return
        
    doc_ids = []
    texts = []
    
    print(f"Cleaning links and tokenizing {len(note_files)} notes...")
    for md_path in note_files:
        raw_text = md_path.read_text(encoding="utf-8")
        
        # Strip Obsidian wiki-links to isolate the textual representation
        cleaned_text = clean_markdown_links(raw_text)
        
        # Check token length using model's native tokenizer
        tokens = model.tokenizer.encode(cleaned_text, add_special_tokens=False)
        token_len = len(tokens)
        
        # Explicitly fail if a note exceeds the model's supported limit to prevent silent truncation
        if token_len > max_seq_length:
            raise ValueError(
                f"Error: Note {md_path.name} has {token_len} tokens, "
                f"exceeding the model's context limit of {max_seq_length} tokens! Truncation is active."
            )
            
        print(f"  Note: {md_path.stem} | Tokens: {token_len:4d} (Below limit)")
        
        doc_ids.append(md_path.stem)
        texts.append(cleaned_text)
        
    # Prepend required Nomic document prefix before embedding
    prefixed_texts = ["search_document: " + t for t in texts]
    print(f"Embedding notes...")
    embeddings = model.encode(prefixed_texts, convert_to_numpy=True, normalize_embeddings=True)
    
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
        
    model_name = index_data.get("model", "nomic-ai/nomic-embed-text-v1.5")
    model = SentenceTransformer(model_name, trust_remote_code=True)
    
    # Prepend required Nomic search query prefix
    query_text = "search_query: " + query
    query_emb = model.encode([query_text], convert_to_numpy=True, normalize_embeddings=True)
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
    parser.add_argument("--model", default="nomic-ai/nomic-embed-text-v1.5", help="Embedding model")
    args = parser.parse_args()
    
    build_structured_index(Path(args.notes), Path(args.output), args.model)
