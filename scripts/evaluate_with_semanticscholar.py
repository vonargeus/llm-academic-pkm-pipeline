"""
evaluate_with_semanticscholar.py

This script evaluates the quality of the metadata extracted by our LLM pipeline
(Metadata Agent) against the official records provided by the Semantic Scholar API.

================================================================================
LIBRARIES USED & THEIR ROLES:
================================================================================
1. `requests`: Used to make HTTP GET requests to the Semantic Scholar REST API
   (https://api.semanticscholar.org/graph/v1/paper/arXiv:...) to fetch official
   publisher-verified bibliographic metadata.
2. `yaml` (PyYAML): Used to parse the YAML frontmatter block at the top of 
   the generated Markdown notes (e.g., extracting "title", "year", "venue", "authors").
3. `re` (Regular Expressions): Used to extract the YAML block delimiters (---) 
   and to clean and normalize strings (lowercasing, stripping punctuation) before 
   comparing them.
4. `json`: Used to cache the fetched gold standard metadata locally and to export
   the final evaluation scores to data/results/metadata_scholar_results.json.
5. `pathlib.Path`: Used for file path manipulations in a platform-independent way.
6. `time`: Used to implement rate limit sleep delays (1.2 seconds) between API requests.

================================================================================
DOCUMENTS UNDER EVALUATION:
================================================================================
* The generated Obsidian Markdown notes stored in the `data/generated_notes/` folder.
* These notes are named after their arXiv IDs (e.g., "2309.15217.md") and contain
  a YAML block at the top containing extracted metadata and a summary below it.

================================================================================
THE THREE RAG SYSTEMS DEFINED:
================================================================================
While this script evaluates the Metadata Agent (RQ2), the underlying research 
compares the following three RAG architectures:
1. Baseline RAG (Flat Chunks): Chunks raw PDF text sequentially (300 characters,
   50 overlap) and runs vector search. It has no metadata or link awareness.
2. Structured RAG (Notes): Indexes and retrieves full agent-generated notes.
3. Link-Expanded RAG (Graph): Seeded by Structured RAG, parses Obsidian wiki-links
   ([[WikiLinks]]), applies a connectivity boost (+0.05), and re-ranks the candidates.
================================================================================
"""

import json
import os
import re
import sys
import time
from pathlib import Path
import requests
import yaml

# Add repo root to path to enable importing the src package
repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from src.evaluation.metadata_eval import normalise, exact_match, set_prf

# Semantic Scholar API authentication credentials
S2_API_KEY = "s2k-Fp7BtDBGrgkHLWNzRI1fqMfWtamaPsBxDNbGIvFw"
HEADERS = {"x-api-key": S2_API_KEY}

def fetch_s2_metadata(arxiv_id: str) -> dict | None:
    """
    Connects to the Semantic Scholar API paper lookup endpoint.
    Retrieves the publisher-verified fields: title, authors, year, and publication venue.
    """
    url = f"https://api.semanticscholar.org/graph/v1/paper/arXiv:{arxiv_id}?fields=title,authors,year,venue"
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 429:
            # Handles rate-limiting gracefully if the limit is breached
            print("  [Rate Limit] Exceeded! Sleeping 5s before returning None...")
            time.sleep(5)
            return None
        else:
            print(f"  [Error] S2 Lookup failed for {arxiv_id} with status {response.status_code}")
            return None
    except Exception as e:
        print(f"  [Exception] S2 query failed: {e}")
        return None

def build_api_gold_standard(notes_dir: Path, output_path: Path):
    """
    Scans the local generated notes directory, identifies arXiv ID names,
    queries the Semantic Scholar API for each, and saves a consolidated 
    gold standard JSON file (metadata_api_gold.json).
    """
    if output_path.exists():
        print(f"Loading cached API gold standard from {output_path}...")
        with open(output_path, encoding="utf-8") as f:
            return json.load(f)

    print("Building Gold Standard Metadata via Semantic Scholar API...")
    gold_data = {}
    
    # Matches notes that are named after valid arXiv IDs (e.g. 2309.15217)
    note_files = [f for f in sorted(notes_dir.glob("*.md")) if re.match(r"^\d{4}\.\d{4,5}$", f.stem)]
    
    for idx, nf in enumerate(note_files, 1):
        arxiv_id = nf.stem
        print(f"[{idx}/{len(note_files)}] Fetching S2 metadata for {arxiv_id}...")
        
        data = fetch_s2_metadata(arxiv_id)
        if data:
            title = data.get("title", "")
            year = data.get("year")
            venue = data.get("venue", "")
            authors = [a["name"] for a in data.get("authors", []) if "name" in a]
            
            gold_data[arxiv_id] = {
                "title": title,
                "year": year,
                "venue": venue,
                "authors": authors
            }
        else:
            print(f"  [warn] Could not fetch metadata for {arxiv_id}. Using fallbacks.")
            
        # Respect the 1 request per second limit strictly to avoid rate limiting blocks
        time.sleep(1.2)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(gold_data, f, indent=2, ensure_ascii=False)
    print(f"API Gold Standard compiled and saved to {output_path}")
    return gold_data

def main():
    notes_dir = Path("data/generated_notes")
    gold_api_path = Path("data/gold_labels/metadata_api_gold.json")
    gold_api_path.parent.mkdir(parents=True, exist_ok=True)

    # 1. Compile or load gold standard from Semantic Scholar
    gold_standard = build_api_gold_standard(notes_dir, gold_api_path)

    # 2. Parse our generated markdown notes to extract predicted metadata
    print("\nParsing generated markdown notes...")
    eval_results = []
    
    for nf in sorted(notes_dir.glob("*.md")):
        doc_id = nf.stem
        if doc_id not in gold_standard:
            continue
            
        gold = gold_standard[doc_id]
        content = nf.read_text(encoding="utf-8", errors="ignore")
        
        # Parse YAML frontmatter between --- blocks
        fm_match = re.match(r"^---\s*\n(.*?)\n---\s*\n?(.*)", content, re.DOTALL)
        if not fm_match:
            continue
            
        try:
            fm = yaml.safe_load(fm_match.group(1)) or {}
        except Exception:
            continue
            
        # Extract metadata fields generated by our agent pipeline
        pred_title = fm.get("title", "")
        pred_year = fm.get("year")
        pred_venue = fm.get("venue", "")
        pred_authors = fm.get("authors", [])
        if isinstance(pred_authors, str):
            pred_authors = [pred_authors]

        # Evaluate predicted fields against API gold standard
        res = {
            "doc_id": doc_id,
            "title_exact": int(normalise(pred_title) == normalise(gold["title"])),
            "year_exact": exact_match(pred_year, gold["year"]),
            "venue_exact": exact_match(pred_venue, gold["venue"]),
            "authors_prf": set_prf(pred_authors, gold["authors"])
        }
        eval_results.append(res)

    # 3. Aggregate results using macro-averages
    if not eval_results:
        print("No matches to evaluate.")
        return

    n_notes = len(eval_results)
    title_acc = sum(r["title_exact"] for r in eval_results) / n_notes
    year_acc = sum(r["year_exact"] for r in eval_results) / n_notes
    venue_acc = sum(r["venue_exact"] for r in eval_results) / n_notes
    
    author_p = sum(r["authors_prf"]["precision"] for r in eval_results if r["authors_prf"]["precision"] is not None) / n_notes
    author_r = sum(r["authors_prf"]["recall"] for r in eval_results if r["authors_prf"]["recall"] is not None) / n_notes
    author_f1 = sum(r["authors_prf"]["f1"] for r in eval_results if r["authors_prf"]["f1"] is not None) / n_notes

    print("\n" + "=" * 60)
    print("=== SEMANTIC SCHOLAR METADATA EVALUATION RESULTS (ALL PAPERS) ===")
    print("=" * 60)
    print(f"Total Papers Evaluated: {n_notes}")
    print(f"Title Exact Match:      {title_acc:.4f}")
    print(f"Year Exact Match:       {year_acc:.4f}")
    print(f"Venue Exact Match:      {venue_acc:.4f}")
    print("-" * 60)
    print(f"Authors Precision:      {author_p:.4f}")
    print(f"Authors Recall:         {author_r:.4f}")
    print(f"Authors F1-Score:       {author_f1:.4f}")
    print("=" * 60)

    # Save evaluation summary
    results_summary = {
        "n_evaluated": n_notes,
        "title_exact_match": title_acc,
        "year_exact_match": year_acc,
        "venue_exact_match": venue_acc,
        "authors_metrics": {
            "precision": author_p,
            "recall": author_r,
            "f1": author_f1
        }
    }
    with open("data/results/metadata_scholar_results.json", "w", encoding="utf-8") as f:
        json.dump(results_summary, f, indent=2, ensure_ascii=False)
    print("Saved final results to data/results/metadata_scholar_results.json")

if __name__ == "__main__":
    main()
