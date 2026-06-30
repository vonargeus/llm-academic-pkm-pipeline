"""
scripts/query_paper_info.py

Usage:
    python scripts/query_paper_info.py --arxiv 2005.11401
    python scripts/query_paper_info.py --arxiv 2402.12240
"""

import argparse
import json
import os
import sys
import requests

def get_with_retry(url: str, headers: dict, max_retries: int = 5, initial_delay: float = 2.0, backoff: float = 2.0):
    import time
    delay = initial_delay
    for attempt in range(max_retries):
        try:
            response = requests.get(url, headers=headers, timeout=15)
            if response.status_code == 200:
                return response
            elif response.status_code == 429:
                print(f"  [Rate Limit 429] Exceeded. Retrying in {delay:.1f} seconds (Attempt {attempt + 1}/{max_retries})...")
                time.sleep(delay)
                delay *= backoff
            else:
                return response
        except Exception as e:
            if attempt == max_retries - 1:
                raise e
            time.sleep(delay)
    return response

def query_paper(arxiv_id: str):
    # Enforce UTF-8 encoding on Windows to prevent printing errors
    if sys.platform == "win32":
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    api_key = "s2k-Fp7BtDBGrgkHLWNzRI1fqMfWtamaPsBxDNbGIvFw"
    headers = {"x-api-key": api_key}
    
    # 1. Fetch paper details
    paper_url = f"https://api.semanticscholar.org/graph/v1/paper/arXiv:{arxiv_id}?fields=title,authors,year,venue,externalIds,s2FieldsOfStudy,abstract"
    
    # 2. Fetch references with intents and topics
    ref_url = f"https://api.semanticscholar.org/graph/v1/paper/arXiv:{arxiv_id}/references?fields=intents,isInfluential,citedPaper.title,citedPaper.authors,citedPaper.year,citedPaper.venue,citedPaper.s2FieldsOfStudy"
    
    import time
    print(f"[*] Querying Semantic Scholar API for arXiv:{arxiv_id}...\n")
    try:
        r_paper = get_with_retry(paper_url, headers)
        if r_paper.status_code != 200:
            print(f"[Error] Failed to fetch paper details (Status: {r_paper.status_code})")
            print(r_paper.text)
            return
            
        time.sleep(1.2)  # Respect the 1 request per second cumulative rate limit
        r_refs = get_with_retry(ref_url, headers)
        if r_refs.status_code != 200:
            print(f"[Error] Failed to fetch references (Status: {r_refs.status_code})")
            print(r_refs.text)
            return
            
        paper_data = r_paper.json()
        ref_data = r_refs.json().get("data", [])
        
        # Consolidate results
        consolidated = {
            "query_arxiv_id": arxiv_id,
            "paper_metadata": paper_data,
            "total_references_count": len(ref_data),
            "references": ref_data
        }
        
        # Save complete JSON payload to data/results/
        os.makedirs("data/results", exist_ok=True)
        output_file = f"data/results/s2_paper_{arxiv_id}.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(consolidated, f, indent=2, ensure_ascii=False)
            
        print("=" * 80)
        print("PAPER METADATA")
        print("=" * 80)
        print(f"Title:      {paper_data.get('title')}")
        print(f"Year:       {paper_data.get('year')}")
        print(f"Venue:      {paper_data.get('venue')}")
        print(f"Authors:    {', '.join([a['name'] for a in paper_data.get('authors', [])])}")
        print(f"Topics:     {', '.join([f['category'] for f in paper_data.get('s2FieldsOfStudy', [])])}")
        print(f"Abstract:   {paper_data.get('abstract', '')[:250]}...")
        
        print("\n" + "=" * 80)
        print(f"REFERENCES WITH CITATION INTENTS (Total: {len(ref_data)})")
        print("=" * 80)
        
        # Print first 5 references
        for idx, ref in enumerate(ref_data[:5], 1):
            cited = ref.get("citedPaper", {})
            intents = ref.get("intents", [])
            is_inf = ref.get("isInfluential", False)
            topics = [t["category"] for t in cited.get("s2FieldsOfStudy", [])] if cited.get("s2FieldsOfStudy") else []
            
            print(f"[{idx}] {cited.get('title')} ({cited.get('year')})")
            print(f"    * Authors:     {', '.join([a['name'] for a in cited.get('authors', [])][:3])}")
            print(f"    * Topics:      {topics if topics else 'N/A'}")
            print(f"    * Intents:     {intents if intents else 'None (General Background Reference)'}")
            print(f"    * Influential: {is_inf}")
            print("-" * 80)
            
        print(f"\n[OK] Full API payload cached successfully at:")
        print(f"     {output_file}")
        print("\nYou can open this JSON file to inspect all references, fields, and raw intents.")
        
    except Exception as e:
        print(f"[Exception] Request failed: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Query paper details and citation intents from Semantic Scholar.")
    parser.add_argument("--arxiv", required=True, help="arXiv ID of the target paper (e.g. 2005.11401)")
    args = parser.parse_args()
    query_paper(args.arxiv)
