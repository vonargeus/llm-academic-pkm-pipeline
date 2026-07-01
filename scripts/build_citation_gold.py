import json
import time
import sys
from datetime import datetime
from pathlib import Path
import requests

S2_API_KEY = "s2k-Fp7BtDBGrgkHLWNzRI1fqMfWtamaPsBxDNbGIvFw"
HEADERS = {"x-api-key": S2_API_KEY}

def api_get(url: str, params: dict = None, max_retries: int = 5) -> dict:
    """
    Make an API GET request with retry logic for 429, timeouts, and server errors.
    """
    delay = 2.0
    for attempt in range(max_retries):
        try:
            response = requests.get(url, headers=HEADERS, params=params, timeout=15)
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                print(f"  [404 Not Found] URL: {url}")
                return None
            elif response.status_code == 429:
                print(f"  [429 Rate Limit] Attempt {attempt+1}/{max_retries}. Sleeping {delay:.1f}s...")
                time.sleep(delay)
                delay *= 2.0
            else:
                print(f"  [Server Error {response.status_code}] Attempt {attempt+1}/{max_retries}. Sleeping {delay:.1f}s...")
                time.sleep(delay)
                delay *= 2.0
        except requests.exceptions.RequestException as e:
            print(f"  [Request Exception] {e}. Attempt {attempt+1}/{max_retries}. Sleeping {delay:.1f}s...")
            time.sleep(delay)
            delay *= 2.0
            
    # If we reached here, the request failed after all retries
    raise RuntimeError(f"API request failed after {max_retries} attempts: {url}")

def main():
    notes_dir = Path("data/generated_notes")
    output_path = Path("data/gold_labels/rq3_semantic_scholar_internal_citation_edges.json")
    
    # 1. Load the exact 40 arXiv IDs from the experiment notes
    corpus_arxiv_ids = sorted({p.stem for p in notes_dir.glob("*.md")})
    if len(corpus_arxiv_ids) != 40:
        print(f"Error: Expected exactly 40 corpus notes, found {len(corpus_arxiv_ids)}")
        sys.exit(1)
        
    print(f"Found {len(corpus_arxiv_ids)} corpus papers to resolve.")
    
    arxiv_to_s2_id = {}
    s2_id_to_arxiv = {}
    failed_resolutions = []
    total_api_pages = 0
    
    # Phase 1: Resolve every paper through Semantic Scholar to get its s2 paperId
    print("\n=== Phase 1: Resolving papers to Semantic Scholar IDs ===")
    for idx, arxiv_id in enumerate(corpus_arxiv_ids, 1):
        print(f"[{idx}/40] Resolving arXiv:{arxiv_id}...")
        url = f"https://api.semanticscholar.org/graph/v1/paper/arXiv:{arxiv_id}?fields=paperId,title"
        time.sleep(1.1)  # cumulative rate limit compliance
        
        try:
            data = api_get(url)
            total_api_pages += 1
            if data and data.get("paperId"):
                s2_id = data["paperId"]
                arxiv_to_s2_id[arxiv_id] = s2_id
                s2_id_to_arxiv[s2_id] = arxiv_id
                print(f"  -> Resolved to S2 PaperID: {s2_id}")
            else:
                print(f"  -> Failed to resolve arXiv:{arxiv_id} (No S2 ID found)")
                failed_resolutions.append(arxiv_id)
        except Exception as e:
            print(f"  -> Error resolving arXiv:{arxiv_id}: {e}")
            failed_resolutions.append(arxiv_id)
            
    # Exit if any resolutions failed
    if failed_resolutions:
        print(f"\nError: Failed to resolve {len(failed_resolutions)} papers. Live API resolution must succeed for all 40 papers.")
        print(f"Failed papers: {failed_resolutions}")
        sys.exit(1)
        
    print(f"\nSuccessfully resolved all {len(arxiv_to_s2_id)} papers.")
    
    # Phase 2: Fetch the complete reference list for every resolved paper
    print("\n=== Phase 2: Fetching reference lists ===")
    internal_edges = set()
    total_references_fetched = 0
    
    for idx, arxiv_id in enumerate(corpus_arxiv_ids, 1):
        s2_id = arxiv_to_s2_id[arxiv_id]
        print(f"[{idx}/40] Fetching references for arXiv:{arxiv_id} (S2 ID: {s2_id})...")
        
        offset = 0
        limit = 1000
        paper_refs = []
        
        while True:
            url = f"https://api.semanticscholar.org/graph/v1/paper/{s2_id}/references"
            params = {
                "fields": "citedPaper.paperId,citedPaper.externalIds,citedPaper.title",
                "offset": offset,
                "limit": limit
            }
            time.sleep(1.1)
            
            try:
                data = api_get(url, params=params)
                total_api_pages += 1
            except Exception as e:
                print(f"  -> Error fetching references page: {e}")
                sys.exit(1)
                
            if not data:
                break
                
            refs = data.get("data", [])
            paper_refs.extend(refs)
            total_references_fetched += len(refs)
            
            # Check pagination
            if len(refs) < limit:
                break
            offset += limit
            
        print(f"  -> Fetched {len(paper_refs)} references.")
        
        # Match references to our corpus
        for ref in paper_refs:
            cited_paper = ref.get("citedPaper")
            if not cited_paper:
                continue
                
            cited_s2_id = cited_paper.get("paperId")
            ext_ids = cited_paper.get("externalIds") or {}
            cited_arxiv = ext_ids.get("ArXiv")
            
            matched_arxiv_id = None
            
            # 1. Match by S2 paperId
            if cited_s2_id and cited_s2_id in s2_id_to_arxiv:
                matched_arxiv_id = s2_id_to_arxiv[cited_s2_id]
            # 2. Fall back to arXiv ID matching
            elif cited_arxiv:
                clean_arxiv = cited_arxiv.split("v")[0].strip()
                if clean_arxiv in corpus_arxiv_ids:
                    matched_arxiv_id = clean_arxiv
                    
            if matched_arxiv_id:
                # Add directed edge: source cites target
                internal_edges.add((arxiv_id, matched_arxiv_id))
                print(f"    * Match found: {arxiv_id} -> {matched_arxiv_id}")
                
    # Format edge list
    citation_edges = []
    for src, tgt in sorted(internal_edges):
        citation_edges.append({
            "source": src,
            "target": tgt,
            "link_type": "cites"
        })
        
    # Generate the Audit Summary
    audit_summary = {
        "corpus_papers": len(corpus_arxiv_ids),
        "successfully_resolved": len(arxiv_to_s2_id),
        "failed_resolutions": len(failed_resolutions),
        "total_references_fetched": total_references_fetched,
        "total_api_pages_fetched": total_api_pages,
        "internal_directed_citation_edges": len(citation_edges),
        "unresolved_or_skipped_records": failed_resolutions,
        "api_query_timestamp": datetime.utcnow().isoformat() + "Z"
    }
    
    output_data = {
        "audit_summary": audit_summary,
        "citation_edges": citation_edges
    }
    
    # Save the output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2)
        
    print("\n" + "="*80)
    print("                AUDIT SUMMARY")
    print("="*80)
    print(f"Corpus Papers:            {audit_summary['corpus_papers']}")
    print(f"Successfully Resolved:    {audit_summary['successfully_resolved']}")
    print(f"Failed Resolutions:       {audit_summary['failed_resolutions']}")
    print(f"Total References Fetched: {audit_summary['total_references_fetched']}")
    print(f"Total API Pages Fetched:  {audit_summary['total_api_pages_fetched']}")
    print(f"Internal Citation Edges:  {audit_summary['internal_directed_citation_edges']}")
    print(f"Timestamp:                {audit_summary['api_query_timestamp']}")
    print("="*80 + "\n")
    print(f"Successfully created gold citation graph at {output_path}")

if __name__ == "__main__":
    main()
