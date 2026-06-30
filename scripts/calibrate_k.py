"""
scripts/calibrate_k.py

Description:
    This script performs an empirical calibration experiment to determine the 
    average number of retrieved chunks required in Flat RAG to obtain exactly 
    10 unique document IDs after deduplication.
    
    This replaces arbitrary selection of parameter K with data-driven evidence.
"""

import json
import sys
import numpy as np
from pathlib import Path
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer

# Add project root to path
repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from src.retrieval.baseline import load_index as load_baseline_index

def main():
    queries_path = Path("data/queries/queries.json")
    baseline_index_path = Path("data/results/baseline_index.json")

    if not queries_path.exists() or not baseline_index_path.exists():
        print("Error: Missing query or baseline index files.")
        print("Please run scripts/generate_queries.py and build the baseline index first.")
        return

    # Load queries and index
    with open(queries_path, encoding="utf-8") as f:
        queries = json.load(f)
        
    docs, embeddings, model = load_baseline_index(str(baseline_index_path))
    
    chunk_counts_needed = []
    
    print("\nCalibrating K (checking unique document retrieval depth)...")
    for idx, q in enumerate(queries, 1):
        query_text = q["text"]
        query_emb = model.encode([query_text])
        
        # Calculate similarity with all chunks
        sims = cosine_similarity(query_emb, embeddings)[0]
        sorted_indices = np.argsort(sims)[::-1]
        
        # Walk down the ranked chunks until we see 10 unique docs
        seen_docs = set()
        chunks_checked = 0
        for chunk_idx in sorted_indices:
            chunks_checked += 1
            doc_id = docs[chunk_idx]["doc_id"]
            seen_docs.add(doc_id)
            if len(seen_docs) == 10:
                break
                
        chunk_counts_needed.append(chunks_checked)
        print(f"  Query {idx:2d}: Checked {chunks_checked:2d} chunks to get 10 unique papers.")
            
    avg_chunks = sum(chunk_counts_needed) / len(chunk_counts_needed)
    max_chunks = max(chunk_counts_needed)
    min_chunks = min(chunk_counts_needed)
    
    print("\n" + "=" * 60)
    print("EMPIRE CALIBRATION RESULTS REPORT")
    print("=" * 60)
    print(f"Total test queries evaluated: {len(queries)}")
    print(f"Average chunks needed:         {avg_chunks:.2f}")
    print(f"Minimum chunks needed:         {min_chunks}")
    print(f"Maximum chunks needed:         {max_chunks}")
    print("=" * 60)
    
    # Save the calibration results
    report = {
        "num_queries": len(queries),
        "avg_chunks_needed": avg_chunks,
        "max_chunks_needed": max_chunks,
        "min_chunks_needed": min_chunks,
        "individual_counts": chunk_counts_needed
    }
    output_path = Path("data/results/calibration_report.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f_out:
        json.dump(report, f_out, indent=2)
    print(f"Saved calibration report to {output_path}")

if __name__ == "__main__":
    main()
