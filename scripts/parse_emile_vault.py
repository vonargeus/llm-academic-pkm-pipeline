"""
parse_emile_vault.py — Parse Emile's academic-obsidian GitHub repo notes.

This script:
1. Clones or reads the academic-obsidian vault
2. Parses all .md notes and extracts their YAML frontmatter and tags
3. Identifies paper notes (tag: #source/paper) and their arXiv URLs
4. Outputs a structured JSON ready for gold-label comparison

Usage:
    # Clone the repo first:
    git clone https://github.com/HEmile/academic-obsidian.git data/emile_vault/

    # Then parse it:
    python scripts/parse_emile_vault.py --vault data/emile_vault/ --output data/gold_labels/

Why this is valuable:
    Emile's vault is the GOLD STANDARD for this thesis.
    - Paper notes = gold metadata (authors, year, venue, topics, links)
    - Links between notes = gold inter-note link set for link quality evaluation
    - Note structure = target schema for our note generation agent
    We compare our agent's OUTPUT to Emile's HAND-CRAFTED notes.
    That comparison IS our RQ2 (metadata quality) and RQ3 (link quality) evaluation.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import yaml  # pip install pyyaml


# ---------------------------------------------------------------------------
# YAML frontmatter parser
# ---------------------------------------------------------------------------

def parse_frontmatter(md_text: str) -> tuple[dict, str]:
    """
    Extract YAML frontmatter from a markdown file.
    Returns (frontmatter_dict, body_text).
    """
    # Match --- ... --- block at start of file
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n?(.*)", md_text, re.DOTALL)
    if not match:
        return {}, md_text

    yaml_str = match.group(1)
    body = match.group(2).strip()

    try:
        fm = yaml.safe_load(yaml_str) or {}
    except yaml.YAMLError:
        fm = {}

    return fm, body


# ---------------------------------------------------------------------------
# WikiLink extractor
# ---------------------------------------------------------------------------

def extract_wikilinks(text: str) -> list[str]:
    """Extract all [[WikiLink]] and [[WikiLink|Alias]] targets from text."""
    raw = re.findall(r"\[\[([^\]]+)\]\]", text)
    # Handle aliases: [[Target|Alias]] → take Target
    targets = [r.split("|")[0].strip() for r in raw]
    return list(dict.fromkeys(targets))  # deduplicate while preserving order


# ---------------------------------------------------------------------------
# Tag extractor
# ---------------------------------------------------------------------------

def extract_tags(body: str) -> list[str]:
    """Extract Obsidian #tags from note body."""
    return re.findall(r"#([\w/]+)", body)


# ---------------------------------------------------------------------------
# Note type classification
# ---------------------------------------------------------------------------

NOTE_TYPE_MAP = {
    "source/paper": "paper",
    "source/talk": "talk",
    "source/dataset": "dataset",
    "topic": "topic",
    "concept": "concept",
    "concept/problem": "concept",
    "project": "project",
    "project/idea": "project",
    "method": "method",
    "method/tool": "method",
    "method/library": "method",
    "venue/conference": "venue",
    "venue/journal": "venue",
    "institution": "institution",
    "author": "author",
}


def classify_note(tags: list[str], fm: dict) -> str:
    """Determine note type from tags."""
    for tag in tags:
        for tag_key, note_type in NOTE_TYPE_MAP.items():
            if tag == tag_key or tag.startswith(tag_key):
                return note_type
    return "unknown"


# ---------------------------------------------------------------------------
# arXiv URL extractor
# ---------------------------------------------------------------------------

def extract_arxiv_id(fm: dict) -> str | None:
    """Try to extract arXiv ID from frontmatter url or doi_or_arxiv fields."""
    url = fm.get("url", "") or fm.get("doi_or_arxiv", "") or ""
    if not url:
        return None
    # Match arXiv patterns
    match = re.search(r"arxiv\.org/abs/(\d{4}\.\d{4,5})", str(url))
    if match:
        return match.group(1)
    match = re.search(r"(\d{4}\.\d{4,5})", str(url))
    if match:
        return match.group(1)
    return None


# ---------------------------------------------------------------------------
# Parse a single note file
# ---------------------------------------------------------------------------

def parse_note(md_path: Path) -> dict:
    """Parse a single .md note into a structured dict."""
    text = md_path.read_text(encoding="utf-8", errors="ignore")
    fm, body = parse_frontmatter(text)
    tags = extract_tags(body)

    # Also check frontmatter for tags (Obsidian stores them in both places)
    fm_tags = fm.get("tags", [])
    if isinstance(fm_tags, str):
        fm_tags = [fm_tags]
    all_tags = list(dict.fromkeys(tags + fm_tags))

    note_type = classify_note(all_tags, fm)
    arxiv_id = extract_arxiv_id(fm)

    # Collect all wikilinks from frontmatter values + body
    all_text = text
    wikilinks_in_fm = []
    for v in fm.values():
        if isinstance(v, str):
            wikilinks_in_fm += extract_wikilinks(v)
        elif isinstance(v, list):
            for item in v:
                if isinstance(item, str):
                    wikilinks_in_fm += extract_wikilinks(item)

    wikilinks_in_body = extract_wikilinks(body)
    all_wikilinks = list(dict.fromkeys(wikilinks_in_fm + wikilinks_in_body))

    # Extract typed links from frontmatter
    typed_links: list[dict] = []
    typed_link_fields = [
        "hasTopic", "author", "publishedIn", "project", "subset",
        "isA", "with", "uses", "usesMethod", "hasDataset", "relatedTo"
    ]
    for field in typed_link_fields:
        val = fm.get(field)
        if val is None:
            continue
        if isinstance(val, str):
            targets = extract_wikilinks(val)
            for t in targets:
                typed_links.append({"field": field, "target": t})
        elif isinstance(val, list):
            for item in val:
                targets = extract_wikilinks(str(item))
                for t in targets:
                    typed_links.append({"field": field, "target": t})

    return {
        "doc_id": md_path.stem,
        "filename": md_path.name,
        "note_type": note_type,
        "tags": all_tags,
        "arxiv_id": arxiv_id,
        "url": fm.get("url"),
        "year": fm.get("year"),
        "aliases": fm.get("aliases", []),
        "cite_key": fm.get("citeKey") or fm.get("aliases", [None])[0] if fm.get("aliases") else None,
        "frontmatter": {k: v for k, v in fm.items()},
        "typed_links": typed_links,
        "all_wikilinks": all_wikilinks,
        "body_preview": body[:500],
    }


# ---------------------------------------------------------------------------
# Parse full vault
# ---------------------------------------------------------------------------

def parse_vault(vault_dir: Path, output_dir: Path):
    output_dir.mkdir(parents=True, exist_ok=True)

    md_files = [f for f in vault_dir.rglob("*.md") if not f.name.startswith(".")]

    all_notes: list[dict] = []
    paper_notes: list[dict] = []
    link_gold: list[dict] = []

    print(f"\nParsing {len(md_files)} markdown files from {vault_dir}")

    for md_path in sorted(md_files):
        note = parse_note(md_path)
        all_notes.append(note)

        if note["note_type"] == "paper":
            paper_notes.append(note)

        # Build gold link set from typed_links
        for link in note["typed_links"]:
            link_gold.append({
                "source": note["doc_id"],
                "target": link["target"],
                "link_type": link["field"],
                "source_type": note["note_type"],
            })

    # ── Summaries ────────────────────────────────────────────────────────────
    type_counts: dict[str, int] = {}
    for n in all_notes:
        t = n["note_type"]
        type_counts[t] = type_counts.get(t, 0) + 1

    print(f"\nNote types found:")
    for t, c in sorted(type_counts.items()):
        print(f"  {t:20s}  {c}")

    papers_with_arxiv = [p for p in paper_notes if p["arxiv_id"]]
    print(f"\nPaper notes total:       {len(paper_notes)}")
    print(f"Papers with arXiv ID:    {len(papers_with_arxiv)}")
    print(f"Total typed links found: {len(link_gold)}")

    # ── Save outputs ─────────────────────────────────────────────────────────
    # All notes
    all_notes_path = output_dir / "vault_notes.json"
    with open(all_notes_path, "w", encoding="utf-8") as f:
        json.dump(all_notes, f, indent=2, ensure_ascii=False)
    print(f"\nAll notes  -> {all_notes_path}")

    # Paper notes only
    paper_notes_path = output_dir / "vault_paper_notes.json"
    with open(paper_notes_path, "w", encoding="utf-8") as f:
        json.dump(paper_notes, f, indent=2, ensure_ascii=False)
    print(f"Paper notes -> {paper_notes_path}")

    # Gold link set
    link_gold_path = output_dir / "link_gold.json"
    with open(link_gold_path, "w", encoding="utf-8") as f:
        json.dump(link_gold, f, indent=2, ensure_ascii=False)
    print(f"Gold links -> {link_gold_path}")

    # arXiv IDs for download
    arxiv_ids_path = output_dir / "vault_arxiv_ids.json"
    arxiv_map = {p["doc_id"]: p["arxiv_id"] for p in papers_with_arxiv}
    with open(arxiv_ids_path, "w", encoding="utf-8") as f:
        json.dump(arxiv_map, f, indent=2, ensure_ascii=False)
    print(f"arXiv IDs  -> {arxiv_ids_path}")

    # Gold metadata for metadata evaluation
    metadata_gold_path = output_dir / "metadata_gold.json"
    metadata_gold = {}
    for n in paper_notes:
        fm = n["frontmatter"]
        metadata_gold[n["doc_id"]] = {
            "title": n["doc_id"],  # filename is the title in Emile's system
            "aliases": n["aliases"],
            "year": n["year"],
            "venue": _extract_link_target(fm.get("publishedIn", "")),
            "authors": _extract_all_link_targets(fm.get("author", [])),
            "hasTopic": _extract_all_link_targets(fm.get("hasTopic", [])),
            "arxiv_id": n["arxiv_id"],
            "url": n["url"],
        }
    with open(metadata_gold_path, "w", encoding="utf-8") as f:
        json.dump(metadata_gold, f, indent=2, ensure_ascii=False)
    print(f"Metadata gold -> {metadata_gold_path}")

    return {
        "all_notes": len(all_notes),
        "paper_notes": len(paper_notes),
        "papers_with_arxiv": len(papers_with_arxiv),
        "link_gold_entries": len(link_gold),
        "type_counts": type_counts,
    }


def _extract_link_target(val) -> str | None:
    if not val:
        return None
    targets = extract_wikilinks(str(val))
    return targets[0] if targets else str(val)


def _extract_all_link_targets(val) -> list[str]:
    if not val:
        return []
    if isinstance(val, str):
        return extract_wikilinks(val) or [val]
    result = []
    for item in val:
        result += extract_wikilinks(str(item)) or [str(item)]
    return result


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Parse Emile's academic-obsidian vault notes into gold labels."
    )
    parser.add_argument(
        "--vault",
        default="data/emile_vault",
        help="Path to cloned academic-obsidian repo directory",
    )
    parser.add_argument(
        "--output",
        default="data/gold_labels",
        help="Output directory for gold label JSON files",
    )
    args = parser.parse_args()

    stats = parse_vault(Path(args.vault), Path(args.output))
    print(f"\nDone. Summary: {stats}")
