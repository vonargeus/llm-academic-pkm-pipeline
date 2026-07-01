"""
scripts/run_citation_link_agent.py
------------------------------------
Runs the Citation Link Agent (src/agents/link_agent.extract_citation_links)
on all 40 corpus papers and saves per-paper results to:
  data/results/rq3_agent_predictions.json

Does NOT modify existing notes, embeddings, or RQ1/RQ2 artifacts.
"""

from __future__ import annotations

import json
import sys
import time
import unicodedata
import re
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent / ".env", override=False)
except ImportError:
    pass

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.agents.link_agent import extract_citation_links

EXTRACTED_DIR = Path("data/extracted_text")
NOTES_DIR     = Path("data/generated_notes")
OUTPUT_PATH   = Path("data/results/rq3_agent_predictions.json")


def norm_title(title: str | None) -> str | None:
    if not title:
        return None
    t = title.lower()
    t = unicodedata.normalize("NFKD", t)
    t = re.sub(r"[^\w\s]", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def build_corpus_index() -> dict[str, str]:
    """Build normalized_title -> arxiv_id index from generated notes."""
    index = {}
    for note_path in NOTES_DIR.glob("*.md"):
        arxiv_id = note_path.stem
        content = note_path.read_text(encoding="utf-8")
        m = re.search(r'^title:\s*["\']?(.*?)["\']?\s*$', content, re.MULTILINE)
        if m:
            norm = norm_title(m.group(1).strip())
            if norm:
                index[norm] = arxiv_id
    return index


def main() -> None:
    corpus_ids = sorted(p.stem for p in NOTES_DIR.glob("*.md"))
    print(f"Corpus: {len(corpus_ids)} papers")
    assert len(corpus_ids) == 40, f"Expected 40 papers, found {len(corpus_ids)}"

    corpus_index = build_corpus_index()
    print(f"Built corpus title index: {len(corpus_index)} entries\n")

    results: dict[str, dict] = {}

    for i, arxiv_id in enumerate(corpus_ids, 1):
        print(f"[{i:02d}/40] {arxiv_id}")

        ext_path = EXTRACTED_DIR / f"{arxiv_id}.json"
        if not ext_path.exists():
            print(f"  WARNING: No extracted text — skipping.")
            results[arxiv_id] = {"references": [], "error": "no_extracted_text", "section_fallback": False}
            continue

        doc = json.load(open(ext_path, encoding="utf-8"))
        full_text = doc.get("text", "")

        if not full_text.strip():
            print(f"  WARNING: Empty text — skipping.")
            results[arxiv_id] = {"references": [], "error": "empty_text", "section_fallback": False}
            continue

        result = extract_citation_links(full_text, corpus_index=corpus_index)
        refs = result.get("references", [])
        fallback = result.get("section_fallback", False)
        local_resolved = sum(1 for r in refs if r.get("local_arxiv_id"))

        print(f"  {'[FALLBACK] ' if fallback else ''}Extracted {len(refs)} references "
              f"({local_resolved} resolved to local corpus)")

        results[arxiv_id] = result
        time.sleep(1.0)  # rate-limit courtesy delay

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    total = sum(len(v.get("references", [])) for v in results.values())
    print(f"\nDone. Total references extracted: {total}")
    print(f"Saved to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
