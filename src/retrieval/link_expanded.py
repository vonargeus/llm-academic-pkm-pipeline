"""
link_expanded.py — Graph-informed ablation retrieval module.

Expands top-k retrieved notes by parsing their [[WikiLinks]] and applying
a topological connectivity boost before re-ranking the entire corpus.
"""

from __future__ import annotations

import json
from pathlib import Path
import re
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

def get_linked_notes(note_path: Path) -> list[str]:
    """Extract [[WikiLink]] targets from a note."""
    if not note_path.exists():
        return []
    text = note_path.read_text(encoding="utf-8", errors="ignore")
    raw = re.findall(r"\[\[([^\]]+)\]\]", text)
    return [r.split("|")[0].strip() for r in raw]

def build_title_map(notes_dir: Path) -> dict[str, str]:
    """
    Scan generated notes and map paper titles and aliases (lowercase) to their corresponding arXiv IDs (filenames).
    This enables dynamic identity resolution for Obsidian-style [[WikiLinks]] in the knowledge graph.
    """
    title_map = {}
    for note_path in notes_dir.glob("*.md"):
        doc_id = note_path.stem
        try:
            content = note_path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue

        # Standardise and map the arXiv ID itself
        title_map[doc_id.lower()] = doc_id

        # Extract title from frontmatter: title: "..."
        title_match = re.search(r'^title:\s*"(.*?)"', content, re.MULTILINE)
        if not title_match:
            title_match = re.search(r'^title:\s*(.*?)$', content, re.MULTILINE)
        if title_match:
            title = title_match.group(1).strip().strip('"').strip("'")
            title_map[title.lower()] = doc_id

        # Extract aliases: aliases: [...]
        aliases_match = re.search(r'^aliases:\s*\[(.*?)\]', content, re.MULTILINE)
        if aliases_match:
            aliases_str = aliases_match.group(1)
            aliases = [a.strip().strip('"').strip("'") for a in aliases_str.split(",") if a.strip()]
            for alias in aliases:
                title_map[alias.lower()] = doc_id
                
    return title_map

def retrieve_link_expanded(
    query: str, 
    index_path: Path, 
    notes_dir: Path, 
    top_k: int = 10,
    graph_boost_alpha: float = 0.05
) -> list[str]:
    """
    Retrieve structured notes via vector similarity, extract inter-document
    topological links, apply a connectivity boost, and re-rank the candidate pool.
    
    This acts as a graph-informed retrieval layer where:
        Score_final(d) = CosineSimilarity(q, d) + alpha * I(d is linked by top-k seed nodes)
    
    Args:
        query: User search query string.
        index_path: Path to the structured index JSON file.
        notes_dir: Path to directory containing generated Obsidian Markdown notes.
        top_k: Number of ranked documents to return.
        graph_boost_alpha: Connectivity hyperparameter (alpha) to boost scores of linked nodes.
    """
    # 1. Load the structured index
    with open(index_path, encoding="utf-8") as f:
        index_data = json.load(f)
        
    doc_ids = index_data["doc_ids"]
    doc_embs = np.array(index_data["embeddings"])
    model_name = index_data.get("model", "all-MiniLM-L6-v2")
    
    # 2. Encode query and calculate baseline cosine similarities
    model = SentenceTransformer(model_name, trust_remote_code=True)
    query_text = "search_query: " + query
    query_emb = model.encode([query_text], convert_to_numpy=True, normalize_embeddings=True)
    similarities = cosine_similarity(query_emb, doc_embs)[0]
    
    # Store initial similarities
    doc_scores = {doc_ids[i]: float(similarities[i]) for i in range(len(doc_ids))}
    
    # 3. Retrieve top-k vector similarity seeds
    initial_results = sorted(doc_ids, key=lambda x: doc_scores[x], reverse=True)[:top_k]
    
    # 4. Build identity resolution map (Title/Alias -> arXiv ID)
    title_map = build_title_map(notes_dir)
    
    # 5. Extract links from top-k seed documents
    linked_docs = set()
    for doc_id in initial_results:
        note_path = notes_dir / f"{doc_id}.md"
        linked_targets = get_linked_notes(note_path)
        for target in linked_targets:
            matched_id = title_map.get(target.lower())
            # Ensure the matched ID is valid and not already in the initial seed results
            if matched_id and matched_id in doc_scores and matched_id not in initial_results:
                linked_docs.add(matched_id)
                
    # 6. Apply connectivity boost (alpha) to linked topological neighbors
    boosted_scores = dict(doc_scores)
    for l_doc in linked_docs:
        boosted_scores[l_doc] += graph_boost_alpha
        
    # 7. Re-rank entire corpus based on the boosted scores
    re_ranked = sorted(doc_ids, key=lambda x: boosted_scores[x], reverse=True)[:top_k]
    
    return re_ranked


