"""
scripts/enrich_metadata_gold.py

This script:
1. Loads the existing `data/gold_labels/metadata_gold.json` (parsed from Emile's vault, Group B).
2. Loads `data/raw_pdfs/manifest.json` to get the full list of 22 active corpus papers.
3. Identifies the 16 papers (Group A) that are not yet in `metadata_gold.json`.
4. Queries the Semantic Scholar API to retrieve official bibliographic metadata (title, year, venue, authors) for those 16 papers.
5. Merges this publisher-verified metadata into `metadata_gold.json` so that all 22 papers have ground-truth metadata defined.
6. Sets empty lists for semantic fields (topics, concepts, method, datasets) for the Group A papers, ensuring they are ignored in semantic macro-averages.
"""

import json
import re
import time
from pathlib import Path
import requests

# Semantic Scholar API credentials from evaluate_with_semanticscholar.py
S2_API_KEY = "s2k-Fp7BtDBGrgkHLWNzRI1fqMfWtamaPsBxDNbGIvFw"
HEADERS = {"x-api-key": S2_API_KEY}

def fetch_s2_metadata(arxiv_id: str) -> dict | None:
    """Queries Semantic Scholar API for publisher-verified paper metadata."""
    url = f"https://api.semanticscholar.org/graph/v1/paper/arXiv:{arxiv_id}?fields=title,authors,year,venue"
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 429:
            print(f"  [Rate Limit] Exceeded querying {arxiv_id}. Sleeping 5s...")
            time.sleep(5)
            return fetch_s2_metadata(arxiv_id)
        else:
            print(f"  [Error] S2 Lookup failed for {arxiv_id} (Status code: {response.status_code})")
            return None
    except Exception as e:
        print(f"  [Exception] S2 query failed for {arxiv_id}: {e}")
        return None

def main():
    metadata_gold_path = Path("data/gold_labels/metadata_gold.json")
    manifest_path = Path("data/raw_pdfs/manifest.json")
    
    if not metadata_gold_path.exists():
        print(f"Error: {metadata_gold_path} does not exist. Run scripts/parse_emile_vault.py first.")
        return
        
    if not manifest_path.exists():
        print(f"Error: {manifest_path} does not exist.")
        return

    # Load existing metadata_gold (Group B)
    with open(metadata_gold_path, "r", encoding="utf-8") as f:
        metadata_gold = json.load(f)
        
    # Load manifest of 22 papers
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    # Map existing metadata_gold arxiv_ids to avoid duplicates
    existing_arxiv_ids = set()
    for doc_id, data in metadata_gold.items():
        arxiv_id = data.get("arxiv_id")
        if arxiv_id:
            existing_arxiv_ids.add(arxiv_id)

    print(f"Current metadata_gold.json contains {len(metadata_gold)} entries.")
    print(f"Existing arXiv IDs in metadata_gold: {existing_arxiv_ids}")

    # Determine Group A (the 16 papers from manifest not in Emile's vault)
    group_a_arxiv_ids = []
    for arxiv_id in manifest.keys():
        if arxiv_id not in existing_arxiv_ids:
            group_a_arxiv_ids.append(arxiv_id)
            
    print(f"\nFound {len(group_a_arxiv_ids)} papers to fetch from Semantic Scholar (Group A):")
    print(group_a_arxiv_ids)

    # Fetch and merge Group A metadata
    for idx, arxiv_id in enumerate(group_a_arxiv_ids, 1):
        print(f"[{idx}/{len(group_a_arxiv_ids)}] Fetching S2 metadata for {arxiv_id}...")
        s2_data = fetch_s2_metadata(arxiv_id)
        
        if s2_data:
            title = s2_data.get("title", "").strip()
            # If title is empty, fallback to manifest info
            if not title:
                title = manifest[arxiv_id].get("title", f"Paper {arxiv_id}")
                
            year = s2_data.get("year") or manifest[arxiv_id].get("year")
            venue = s2_data.get("venue")
            authors = [a["name"] for a in s2_data.get("authors", []) if "name" in a]
            if not authors:
                authors = manifest[arxiv_id].get("authors", [])

            # Add to metadata_gold under arXiv ID as key (or use title, but keying by arXiv ID is safer for RAG papers)
            entry_key = arxiv_id
            metadata_gold[entry_key] = {
                "title": title,
                "aliases": [arxiv_id],
                "year": year,
                "venue": venue,
                "authors": authors,
                "topics": [],
                "concepts": [],
                "method": [],
                "datasets": [],
                "arxiv_id": arxiv_id,
                "url": f"https://arxiv.org/abs/{arxiv_id}"
            }
            print(f"  Merged: '{title}'")
        else:
            # Fallback to manifest info if API fails
            print(f"  [Warning] API lookup failed. Falling back to local manifest info for {arxiv_id}.")
            info = manifest[arxiv_id]
            metadata_gold[arxiv_id] = {
                "title": info.get("title", f"Paper {arxiv_id}"),
                "aliases": [arxiv_id],
                "year": info.get("year"),
                "venue": None,
                "authors": info.get("authors", []),
                "topics": [],
                "concepts": [],
                "method": [],
                "datasets": [],
                "arxiv_id": arxiv_id,
                "url": f"https://arxiv.org/abs/{arxiv_id}"
            }

        # Sleep to strictly respect rate limits
        time.sleep(1.2)

    # Save the unified metadata_gold back
    with open(metadata_gold_path, "w", encoding="utf-8") as f:
        json.dump(metadata_gold, f, indent=2, ensure_ascii=False)
        
    print(f"\nSuccessfully enriched metadata_gold.json. Total entries now: {len(metadata_gold)}")

if __name__ == "__main__":
    main()
