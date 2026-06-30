import json
import time
from pathlib import Path
import requests

S2_API_KEY = "s2k-Fp7BtDBGrgkHLWNzRI1fqMfWtamaPsBxDNbGIvFw"
HEADERS = {"x-api-key": S2_API_KEY}

def fetch_paper_references(arxiv_id: str) -> list[str]:
    """
    Fetch all references of a paper from Semantic Scholar and extract their arXiv IDs.
    """
    url = f"https://api.semanticscholar.org/graph/v1/paper/arXiv:{arxiv_id}/references?fields=citedPaper.externalIds"
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        if response.status_code == 200:
            data = response.json().get("data", [])
            cited_arxiv_ids = []
            for item in data:
                cited_paper = item.get("citedPaper")
                if cited_paper:
                    ext_ids = cited_paper.get("externalIds") or {}
                    arxiv = ext_ids.get("ArXiv")
                    if arxiv:
                        # Clean arXiv ID (strip version if present, e.g., '2103.00020v1' -> '2103.00020')
                        clean_arxiv = arxiv.split("v")[0].strip()
                        cited_arxiv_ids.append(clean_arxiv)
            return cited_arxiv_ids
        elif response.status_code == 429:
            print(f"  [Rate Limit 429] Sleeping 5s before retrying {arxiv_id}...")
            time.sleep(5)
            return fetch_paper_references(arxiv_id)
        else:
            print(f"  [Error] S2 Lookup failed for {arxiv_id} (Status: {response.status_code})")
            return []
    except Exception as e:
        print(f"  [Exception] Failed fetching refs for {arxiv_id}: {e}")
        return []

def main():
    notes_dir = Path("data/generated_notes")
    output_path = Path("data/gold_labels/citations_gold.json")
    
    if output_path.exists():
        print(f"Loading existing citations cache from {output_path}...")
        with open(output_path, encoding="utf-8") as f:
            existing = json.load(f)
            print(f"Loaded {len(existing)} records.")
            return

    # Extract all 40 arXiv IDs in our corpus
    corpus_arxiv_ids = {p.stem for p in notes_dir.glob("*.md")}
    print(f"Found {len(corpus_arxiv_ids)} papers in the local generated notes corpus.")
    
    citation_graph = []
    
    for idx, arxiv_id in enumerate(sorted(corpus_arxiv_ids), 1):
        print(f"[{idx}/{len(corpus_arxiv_ids)}] Querying references for arXiv:{arxiv_id}...")
        
        # S2 Rate Limit: max 1 request per second
        time.sleep(1.2)
        
        cited_ids = fetch_paper_references(arxiv_id)
        
        # Filter references to only keep papers that are in our 40-paper corpus
        in_corpus_citations = [cid for cid in cited_ids if cid in corpus_arxiv_ids]
        
        for cid in in_corpus_citations:
            citation_graph.append({
                "source": arxiv_id,
                "target": cid,
                "link_type": "cites"
            })
            print(f"  -> Found in-corpus citation: {arxiv_id} -> {cid}")
            
    # Save the gold citation graph
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(citation_graph, f, indent=2)
        
    print(f"\nSuccessfully built citation gold graph with {len(citation_graph)} links and saved to {output_path}")

if __name__ == "__main__":
    main()
