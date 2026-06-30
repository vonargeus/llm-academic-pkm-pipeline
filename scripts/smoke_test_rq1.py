"""
scripts/smoke_test_rq1.py

Description:
    Runs a single-query smoke test to verify all index building, 
    preflight checks, and retrieval pipelines before running the full evaluation.
"""

import json
import sys
from pathlib import Path
from sentence_transformers import SentenceTransformer

# Add repository root to python path for importing src
repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from src.retrieval.baseline import build_index as build_baseline, retrieve as retrieve_baseline
from src.retrieval.structured import build_structured_index as build_structured, retrieve as retrieve_structured
from src.retrieval.link_expanded import retrieve_link_expanded

def main():
    extracted_dir = Path("data/extracted_text")
    notes_dir = Path("data/generated_notes")
    baseline_idx = Path("data/results/baseline_index_smoke.json")
    structured_idx = Path("data/results/structured_index_smoke.json")
    queries_path = Path("data/queries/queries.json")
    gold_path = Path("data/gold_labels/gold_labels.json")
    
    print("--- SMOKE TEST START ---")
    
    # 1. Directory creation
    baseline_idx.parent.mkdir(parents=True, exist_ok=True)
    
    # 2. Preflight Check
    print("\n[Step 1] Running preflight check...")
    with open(queries_path, encoding="utf-8") as f:
        queries = json.load(f)
    with open(gold_path, encoding="utf-8") as f:
        gold = json.load(f)
        
    extracted_ids = {f.stem for f in extracted_dir.glob("*.json") if not f.name.startswith("_")}
    notes_ids = {f.stem for f in notes_dir.glob("*.md")}
    
    assert len(extracted_ids) == 40, f"Error: expected 40 extracted texts, found {len(extracted_ids)}"
    assert extracted_ids == notes_ids, "Error: JSON text files and MD notes mismatch!"
    assert len(queries) == 40, "Error: expected 40 queries"
    print("PASS: Preflight check matches.")
    
    # 3. Load model
    print("\n[Step 2] Loading SentenceTransformer...")
    model = SentenceTransformer("nomic-ai/nomic-embed-text-v1.5", trust_remote_code=True)
    
    # 4. Build Baseline Index
    print("\n[Step 3] Building Baseline Index...")
    raw_pdfs_dir = Path("data/raw_pdfs")
    build_baseline(str(raw_pdfs_dir), str(baseline_idx))
    
    # 5. Build Structured Index
    print("\n[Step 4] Building Structured Index...")
    build_structured(notes_dir, structured_idx)
    
    # 6. Load Indices
    print("\n[Step 5] Loading indices back...")
    with open(baseline_idx, encoding="utf-8") as f:
        b_data = json.load(f)
    docs = b_data["docs"]
    embeddings = np_embs = b_data["embeddings"] # check loading
    
    with open(structured_idx, encoding="utf-8") as f:
        s_data = json.load(f)
        
    # 7. Run One Query
    test_query = queries[0]
    qid = test_query["query_id"]
    q_text = test_query["text"]
    print(f"\n[Step 6] Running search for Query {qid}: '{q_text}'")
    
    # Mode A: Baseline
    res_b = retrieve_baseline(q_text, docs, embeddings, model, k=5)
    print(f"  Baseline RAG Top-5: {[d['doc_id'] for score, d in res_b]}")
    
    # Mode B: Structured
    res_s = retrieve_structured(q_text, structured_idx, top_k=5)
    print(f"  Structured RAG Top-5: {res_s}")
    
    # Mode C: Link-Expanded
    res_l = retrieve_link_expanded(q_text, structured_idx, notes_dir, top_k=5)
    print(f"  Link-Expanded RAG Top-5: {res_l}")
    
    print("\n--- SMOKE TEST SUCCESS ---")

if __name__ == "__main__":
    main()
