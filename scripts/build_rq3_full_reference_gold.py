"""
scripts/build_rq3_full_reference_gold.py
----------------------------------------
Queries Semantic Scholar for the COMPLETE outgoing reference list of each of
the 40 corpus papers. Unlike the previous build_citation_gold.py, this script:
  - Does NOT restrict targets to the 40-paper corpus.
  - Stores every returned reference with paperId, DOI, arXiv, and title.
  - Handles pagination, rate limits (1.1s delay), and retries.
  - Reads S2_API_KEY from .env via python-dotenv.
  - Saves to data/gold_labels/rq3_full_reference_gold.json.

Academic justification:
  Lo et al. (2020) S2ORC; Kinney et al. (2023) Semantic Scholar Open Data Platform.
"""

from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent / ".env", override=False)
except ImportError:
    pass

import requests

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
S2_API_KEY = os.getenv("S2_API_KEY")
if not S2_API_KEY:
    print("ERROR: S2_API_KEY is not set. Add it to your .env file.")
    sys.exit(1)

HEADERS = {"x-api-key": S2_API_KEY}
BASE_URL = "https://api.semanticscholar.org/graph/v1/paper"
FIELDS   = "citedPaper.paperId,citedPaper.externalIds,citedPaper.title"
LIMIT    = 1000   # max allowed by S2 API
DELAY    = 1.1    # seconds between requests
MAX_RETRIES = 3

NOTES_DIR   = Path("data/generated_notes")
OUTPUT_PATH = Path("data/gold_labels/rq3_full_reference_gold.json")

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get_corpus_arxiv_ids() -> list[str]:
    return sorted(p.stem for p in NOTES_DIR.glob("*.md"))


def resolve_s2_paper_id(arxiv_id: str) -> str | None:
    """Resolve arXiv ID → S2 paperId."""
    url = f"{BASE_URL}/arXiv:{arxiv_id}?fields=paperId"
    for attempt in range(MAX_RETRIES):
        try:
            r = requests.get(url, headers=HEADERS, timeout=15)
            if r.status_code == 200:
                return r.json().get("paperId")
            if r.status_code == 429:
                print(f"  Rate limited resolving {arxiv_id}, waiting 60s...")
                time.sleep(60)
            elif r.status_code == 404:
                return None
            else:
                print(f"  Unexpected status {r.status_code} resolving {arxiv_id}")
                return None
        except Exception as e:
            print(f"  Error resolving {arxiv_id} (attempt {attempt+1}): {e}")
            time.sleep(5)
    return None


def fetch_all_references(s2_paper_id: str, arxiv_id: str) -> list[dict]:
    """Fetch the complete reference list for a paper using pagination."""
    all_refs = []
    offset = 0
    page = 0
    while True:
        url = (
            f"{BASE_URL}/{s2_paper_id}/references"
            f"?fields={FIELDS}&limit={LIMIT}&offset={offset}"
        )
        for attempt in range(MAX_RETRIES):
            try:
                r = requests.get(url, headers=HEADERS, timeout=30)
                if r.status_code == 200:
                    data = r.json().get("data", [])
                    break
                if r.status_code == 429:
                    print(f"    Rate limited on page {page}, waiting 60s...")
                    time.sleep(60)
                else:
                    print(f"    Status {r.status_code} on page {page} of {arxiv_id}")
                    data = []
                    break
            except Exception as e:
                print(f"    Fetch error (attempt {attempt+1}): {e}")
                time.sleep(5)
                data = []
        else:
            data = []

        if not data:
            break

        for entry in data:
            cp = entry.get("citedPaper", {})
            ext = cp.get("externalIds") or {}
            all_refs.append({
                "s2_paper_id": cp.get("paperId"),
                "title":       cp.get("title"),
                "doi":         ext.get("DOI"),
                "arxiv_id":    ext.get("ArXiv"),
            })

        page += 1
        offset += LIMIT
        time.sleep(DELAY)

        if len(data) < LIMIT:
            break

    return all_refs


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    corpus_ids = get_corpus_arxiv_ids()
    print(f"Corpus: {len(corpus_ids)} papers\n")

    corpus_set = set(corpus_ids)
    per_paper: dict[str, dict] = {}
    total_refs = 0
    failed: list[str] = []
    total_pages = 0

    for i, arxiv_id in enumerate(corpus_ids, 1):
        print(f"[{i:02d}/{len(corpus_ids)}] {arxiv_id}")

        # Step 1 – resolve S2 paper ID
        time.sleep(DELAY)
        s2_id = resolve_s2_paper_id(arxiv_id)
        if not s2_id:
            print(f"  FAILED to resolve {arxiv_id}")
            failed.append(arxiv_id)
            per_paper[arxiv_id] = {"s2_paper_id": None, "references": [], "failed": True}
            continue

        print(f"  S2 ID: {s2_id}")

        # Step 2 – fetch all references
        refs = fetch_all_references(s2_id, arxiv_id)
        print(f"  References fetched: {len(refs)}")
        total_refs += len(refs)

        # Mark which refs are also in our local corpus
        for ref in refs:
            ref["in_local_corpus"] = bool(
                ref.get("arxiv_id") and ref["arxiv_id"] in corpus_set
            )

        # Estimate pages used (ceiling division)
        pages_used = max(1, -(-len(refs) // LIMIT))  # ceiling division
        total_pages += pages_used

        per_paper[arxiv_id] = {
            "s2_paper_id": s2_id,
            "references":  refs,
            "failed":      False,
        }

    # Build output
    output = {
        "audit_summary": {
            "api_query_timestamp": datetime.now(timezone.utc).isoformat(),
            "corpus_papers": len(corpus_ids),
            "successfully_resolved": len(corpus_ids) - len(failed),
            "failed_resolutions": len(failed),
            "failed_arxiv_ids": failed,
            "total_references_fetched": total_refs,
            "estimated_api_pages": total_pages,
        },
        "per_paper_references": per_paper,
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\nDone. {len(corpus_ids) - len(failed)}/{len(corpus_ids)} resolved.")
    print(f"Total references fetched: {total_refs}")
    if failed:
        print(f"Failed: {failed}")
    print(f"Saved to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
