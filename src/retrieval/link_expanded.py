"""
link_expanded.py — Ablation retrieval module.

Expands top-k retrieved notes with notes they link to (1-hop expansion).
"""

from __future__ import annotations

import json
from pathlib import Path
import re

from src.retrieval.structured import retrieve as structured_retrieve

def get_linked_notes(note_path: Path) -> list[str]:
    """Extract [[WikiLink]] targets from a note."""
    if not note_path.exists():
        return []
    text = note_path.read_text(encoding="utf-8", errors="ignore")
    raw = re.findall(r"\[\[([^\]]+)\]\]", text)
    return [r.split("|")[0].strip() for r in raw]

def retrieve_link_expanded(
    query: str, 
    index_path: Path, 
    notes_dir: Path, 
    top_k: int = 10,
    expansion_depth: int = 1
) -> list[str]:
    """
    Retrieve documents, then expand the set by following links, and re-rank.
    
    In a real scenario, you'd re-rank the expanded set by similarity. 
    Here, we append linked notes to the initial top-k set.
    """
    initial_results = structured_retrieve(query, index_path, top_k=top_k)
    
    expanded_set = list(initial_results)
    
    if expansion_depth > 0:
        for doc_id in initial_results:
            note_path = notes_dir / f"{doc_id}.md"
            linked = get_linked_notes(note_path)
            for link in linked:
                if link not in expanded_set:
                    expanded_set.append(link)
                    
    # Cap to avoid massive sets, e.g., double the initial top-k
    return expanded_set[:top_k * 2]

