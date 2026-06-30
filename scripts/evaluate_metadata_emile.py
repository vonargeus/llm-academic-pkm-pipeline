"""
scripts/evaluate_metadata_emile.py

This script evaluates the quality of the metadata extracted by our LLM pipeline
(Metadata Agent) against the expert-crafted gold standard in Emile's vault.

It extracts:
- title, year, venue, authors (bibliographic metadata)
- topics, concepts, method, datasets (semantic metadata/node-level attributes)
and computes Precision, Recall, and F1-score for lists, and exact match accuracy for scalars.
"""

import json
import re
import sys
from pathlib import Path
import yaml

# Add repo root to path to enable importing the src package
repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from src.evaluation.metadata_eval import normalise, exact_match, set_prf

def main():
    notes_dir = Path("data/generated_notes")
    gold_path = Path("data/gold_labels/metadata_gold.json")

    if not gold_path.exists():
        print(f"Error: {gold_path} does not exist. Run scripts/parse_emile_vault.py first.")
        sys.exit(1)

    # 1. Load gold standard
    with open(gold_path, encoding="utf-8") as f:
        gold_all = json.load(f)

    # Map arXiv ID -> Gold Doc ID (title) and Gold Data
    arxiv_to_gold = {}
    for title, data in gold_all.items():
        arxiv_id = data.get("arxiv_id")
        if arxiv_id:
            arxiv_to_gold[arxiv_id] = (title, data)

    print(f"Loaded {len(arxiv_to_gold)} gold papers from Emile's vault with arXiv IDs.")

    # 2. Parse generated notes and evaluate
    eval_results = []
    
    # Check all generated markdown files
    for nf in sorted(notes_dir.glob("*.md")):
        doc_id = nf.stem  # e.g., "1711.11157"
        if doc_id not in arxiv_to_gold:
            continue
            
        gold_title, gold = arxiv_to_gold[doc_id]
        print(f"Evaluating {doc_id} against gold standard: {gold_title!r}")
        
        content = nf.read_text(encoding="utf-8", errors="ignore")
        
        # Parse YAML frontmatter
        fm_match = re.match(r"^---\s*\n(.*?)\n---\s*\n?(.*)", content, re.DOTALL)
        if not fm_match:
            print(f"  [warn] No frontmatter in {nf.name}")
            continue
            
        try:
            fm = yaml.safe_load(fm_match.group(1)) or {}
        except Exception as e:
            print(f"  [warn] YAML parse error in {nf.name}: {e}")
            continue
            
        # Extract predictions
        pred_title = fm.get("title", "")
        pred_year = fm.get("year")
        pred_venue = fm.get("venue", "")
        
        # Lists
        pred_authors = fm.get("authors") or []
        pred_topics = fm.get("topics") or fm.get("hasTopic") or []
        pred_concepts = fm.get("concepts") or fm.get("hasConcept") or []
        pred_method = fm.get("method") or fm.get("usesMethod") or []
        pred_datasets = fm.get("datasets") or fm.get("usesDataset") or []
        
        # Normalize list format
        if isinstance(pred_authors, str): pred_authors = [pred_authors]
        if isinstance(pred_topics, str): pred_topics = [pred_topics]
        if isinstance(pred_concepts, str): pred_concepts = [pred_concepts]
        if isinstance(pred_method, str): pred_method = [pred_method]
        if isinstance(pred_datasets, str): pred_datasets = [pred_datasets]

        # Evaluate
        res = {
            "doc_id": doc_id,
            "title_exact": int(normalise(pred_title) == normalise(gold["title"])),
            "year_exact": exact_match(pred_year, gold["year"]),
            "venue_exact": exact_match(pred_venue, gold["venue"]),
            "authors_prf": set_prf(pred_authors, gold["authors"]),
            "topics_prf": set_prf(pred_topics, gold["topics"]),
            "concepts_prf": set_prf(pred_concepts, gold["concepts"]),
            "method_prf": set_prf(pred_method, gold["method"]),
            "datasets_prf": set_prf(pred_datasets, gold["datasets"])
        }
        eval_results.append(res)

    if not eval_results:
        print("No matches between generated notes and Emile's gold papers.")
        return

    n_notes = len(eval_results)
    
    # Macro averages
    title_acc = sum(r["title_exact"] for r in eval_results) / n_notes
    year_acc = sum(r["year_exact"] for r in eval_results if r["year_exact"] is not None) / n_notes
    venue_acc = sum(r["venue_exact"] for r in eval_results if r["venue_exact"] is not None) / n_notes
    
    def average_prf(prf_list, key):
        valid = [r[key] for r in prf_list if r[key] is not None]
        if not valid:
            return 0.0, 0.0, 0.0
        
        # Filter out cases where gold standard is empty (n_gold == 0)
        # because we can't evaluate precision/recall if there is no ground truth
        valid_eval = [v for v in valid if v.get("n_gold", 0) > 0]
        if not valid_eval:
            return 0.0, 0.0, 0.0
            
        ps = [v["precision"] for v in valid_eval if v["precision"] is not None]
        rs = [v["recall"] for v in valid_eval if v["recall"] is not None]
        f1s = [v["f1"] for v in valid_eval if v["f1"] is not None]
        
        p_avg = sum(ps) / len(ps) if ps else 0.0
        r_avg = sum(rs) / len(rs) if rs else 0.0
        f1_avg = sum(f1s) / len(f1s) if f1s else 0.0
        return p_avg, r_avg, f1_avg

    author_p, author_r, author_f1 = average_prf(eval_results, "authors_prf")
    topic_p, topic_r, topic_f1 = average_prf(eval_results, "topics_prf")
    concept_p, concept_r, concept_f1 = average_prf(eval_results, "concepts_prf")
    method_p, method_r, method_f1 = average_prf(eval_results, "method_prf")
    dataset_p, dataset_r, dataset_f1 = average_prf(eval_results, "datasets_prf")

    print("\n" + "=" * 60)
    print("=== EMILE'S VAULT METADATA EVALUATION RESULTS (6 PAPERS) ===")
    print("=" * 60)
    print(f"Total Papers Evaluated: {n_notes}")
    print(f"Title Exact Match:      {title_acc:.4f}")
    print(f"Year Exact Match:       {year_acc:.4f}")
    print(f"Venue Exact Match:      {venue_acc:.4f}")
    print("-" * 60)
    print(f"Authors:   P={author_p:.4f}, R={author_r:.4f}, F1={author_f1:.4f}")
    print(f"Topics:    P={topic_p:.4f}, R={topic_r:.4f}, F1={topic_f1:.4f}")
    print(f"Concepts:  P={concept_p:.4f}, R={concept_r:.4f}, F1={concept_f1:.4f}")
    print(f"Methods:   P={method_p:.4f}, R={method_r:.4f}, F1={method_f1:.4f}")
    print(f"Datasets:  P={dataset_p:.4f}, R={dataset_r:.4f}, F1={dataset_f1:.4f}")
    print("=" * 60)

    # Save summary
    results_summary = {
        "n_evaluated": n_notes,
        "title_exact_match": title_acc,
        "year_exact_match": year_acc,
        "venue_exact_match": venue_acc,
        "authors_metrics": {"precision": author_p, "recall": author_r, "f1": author_f1},
        "topics_metrics": {"precision": topic_p, "recall": topic_r, "f1": topic_f1},
        "concepts_metrics": {"precision": concept_p, "recall": concept_r, "f1": concept_f1},
        "methods_metrics": {"precision": method_p, "recall": method_r, "f1": method_f1},
        "datasets_metrics": {"precision": dataset_p, "recall": dataset_r, "f1": dataset_f1}
    }
    
    out_path = Path("data/results/metadata_emile_results.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results_summary, f, indent=2, ensure_ascii=False)
    print(f"Saved final results to {out_path}")

if __name__ == "__main__":
    main()
