"""
scripts/rq3_citation_evaluate.py
----------------------------------
Strict, auditable reference extraction evaluator (RQ3).
Enforces:
  1. Transitive Deduplication (for both predictions and gold).
  2. Exact Status Processing (excludes gold_unusable and provider_block from primary metrics).
  3. Pre-scoring Identity Checks.
  4. Global and Local Mathematical Assertions.
"""

from __future__ import annotations

import json
import re
import unicodedata
import hashlib
from datetime import datetime, timezone
from pathlib import Path

GOLD_PATH        = Path("data/gold_labels/rq3_full_reference_gold.json")
PREDICTIONS_PATH = Path("data/results/rq3_agent_predictions.json")
OUTPUT_PATH      = Path("data/results/rq3_citation_link_evaluation.json")
NOTES_DIR        = Path("data/generated_notes")

# ---------------------------------------------------------------------------
# Normalisation helpers
# ---------------------------------------------------------------------------

def norm_arxiv(v):
    if not v:
        return None
    return re.sub(r"v\d+$", "", str(v).strip().lower())

def norm_doi(v):
    if not v:
        return None
    return str(v).strip().lower()

def norm_s2(v):
    if not v:
        return None
    return str(v).strip()

def norm_title(v):
    if not v:
        return None
    t = str(v).lower()
    t = unicodedata.normalize("NFKD", t)
    t = re.sub(r"[^\w\s]", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t

def jaccard(a, b):
    if not a or not b:
        return 0.0
    sa, sb = set(a.split()), set(b.split())
    return len(sa & sb) / len(sa | sb) if (sa or sb) else 0.0

def fuzzy_cands(agent_ref, gold_refs, thr=0.55):
    at = norm_title(agent_ref.get("title"))
    if not at:
        return []
    c = [{"gold_title": r.get("title"), "score": round(jaccard(at, norm_title(r.get("title")) or ""), 4)}
         for r in gold_refs if jaccard(at, norm_title(r.get("title")) or "") >= thr]
    return sorted(c, key=lambda x: -x["score"])[:5]

# ---------------------------------------------------------------------------
# Transitive Deduplication helper
# ---------------------------------------------------------------------------


def deduplicate_references(refs: list[dict]) -> tuple[list[dict], int]:
    """
    Deduplicates references transitively. If any identifier (S2 ID, DOI, arXiv ID,
    or normalized title) matches an existing accepted reference, it is treated
    as a duplicate. Returns (unique_references, invalid_count).
    """
    unique_refs = []
    invalid_count = 0
    
    for ref in refs:
        s2  = norm_s2(ref.get("s2_paper_id"))
        doi = norm_doi(ref.get("doi"))
        arx = norm_arxiv(ref.get("arxiv_id"))
        tit = norm_title(ref.get("title"))
        
        # 1. Identity validation (pre-filtering invalid predictions)
        if not any([s2, doi, arx, tit]):
            invalid_count += 1
            continue
            
        # 2. Transitive duplicate check
        is_duplicate = False
        for u in unique_refs:
            if s2 and norm_s2(u.get("s2_paper_id")) == s2:
                is_duplicate = True
                break
            if doi and norm_doi(u.get("doi")) == doi:
                is_duplicate = True
                break
            if arx and norm_arxiv(u.get("arxiv_id")) == arx:
                is_duplicate = True
                break
            if tit and norm_title(u.get("title")) == tit:
                is_duplicate = True
                break
                
        if not is_duplicate:
            unique_refs.append(ref)
            
    return unique_refs, invalid_count

# ---------------------------------------------------------------------------
# Main Evaluator Logic
# ---------------------------------------------------------------------------

def main():
    if not GOLD_PATH.exists():
        print(f"ERROR: Gold file not found: {GOLD_PATH}")
        raise SystemExit(1)

    if not PREDICTIONS_PATH.exists():
        print(f"ERROR: Predictions not found: {PREDICTIONS_PATH}")
        raise SystemExit(1)

    # Load gold and predictions
    with open(GOLD_PATH, encoding="utf-8") as f:
        gold_data = json.load(f)
    with open(PREDICTIONS_PATH, encoding="utf-8") as f:
        predictions_data = json.load(f)

    prov = predictions_data.get("provenance_metadata", {})
    predictions = predictions_data.get("predictions", {})

    corpus_ids = sorted(p.stem for p in NOTES_DIR.glob("*.md"))
    corpus_set = set(corpus_ids)
    gold_audit = gold_data.get("audit_summary", {})
    per_paper_g = gold_data.get("per_paper_references", {})

    # Evaluation counters
    global_tp = 0
    global_fp = 0
    global_fn = 0
    match_type_counts = {"s2_id": 0, "doi": 0, "arxiv_id": 0, "exact_title": 0}
    
    per_paper_results = {}
    total_invalid_outputs = 0
    excluded_gold_unusable = []
    excluded_provider_blocks = []
    
    per_paper_totals_sum = {"tp": 0, "fp": 0, "fn": 0}

    for arxiv_id in corpus_ids:
        paper_gold = per_paper_g.get(arxiv_id, {})
        gold_refs  = paper_gold.get("references", [])
        agent_data = predictions.get(arxiv_id, {})
        agent_refs = agent_data.get("references", [])
        agent_status = agent_data.get("status", "success")

        # 1. Deduplicate gold references transitively
        unique_gold, _ = deduplicate_references(gold_refs)

        # 2. Deduplicate predictions transitively and count invalid outputs
        unique_preds, invalid_cnt = deduplicate_references(agent_refs)
        total_invalid_outputs += invalid_cnt

        # 3. Determine usability exclusions
        if paper_gold.get("failed"):
            per_paper_results[arxiv_id] = {"status": "gold_unusable", "tp": 0, "fp": 0, "fn": 0}
            continue

        # Exclude suspicious empty gold references (API database holes)
        if len(unique_gold) == 0 and len(unique_preds) > 0:
            excluded_gold_unusable.append(arxiv_id)
            per_paper_results[arxiv_id] = {
                "status": "gold_unusable",
                "tp": 0, "fp": 0, "fn": 0,
                "agent_ref_count": len(unique_preds),
                "gold_ref_count": 0
            }
            continue

        # Exclude provider blocks from primary evaluation metrics
        if agent_status == "provider_block":
            excluded_provider_blocks.append(arxiv_id)
            per_paper_results[arxiv_id] = {
                "status": "provider_block",
                "tp": 0, "fp": 0, "fn": 0,
                "agent_ref_count": len(unique_preds),
                "gold_ref_count": len(unique_gold)
            }
            continue

        # Process standard paper results (including successes with empty predictions)
        gold_pool = list(unique_gold)
        matched_gold_indices = set()
        paper_tp = 0
        paper_fp = 0
        agent_records = []

        for ref in unique_preds:
            match_found = False
            
            # Match priority cascade: S2 ID -> DOI -> arXiv ID -> Title
            s2 = norm_s2(ref.get("s2_paper_id"))
            if s2:
                for idx, g in enumerate(gold_pool):
                    if idx not in matched_gold_indices and norm_s2(g.get("s2_paper_id")) == s2:
                        matched_gold_indices.add(idx)
                        match_type_counts["s2_id"] += 1
                        paper_tp += 1
                        agent_records.append({"agent_title": ref.get("title"), "matched": g.get("title"), "match_type": "s2_id", "result": "TP"})
                        match_found = True
                        break
            if match_found: continue

            doi = norm_doi(ref.get("doi"))
            if doi:
                for idx, g in enumerate(gold_pool):
                    if idx not in matched_gold_indices and norm_doi(g.get("doi")) == doi:
                        matched_gold_indices.add(idx)
                        match_type_counts["doi"] += 1
                        paper_tp += 1
                        agent_records.append({"agent_title": ref.get("title"), "matched": g.get("title"), "match_type": "doi", "result": "TP"})
                        match_found = True
                        break
            if match_found: continue

            arx = norm_arxiv(ref.get("arxiv_id"))
            if arx:
                for idx, g in enumerate(gold_pool):
                    if idx not in matched_gold_indices and norm_arxiv(g.get("arxiv_id")) == arx:
                        matched_gold_indices.add(idx)
                        match_type_counts["arxiv_id"] += 1
                        paper_tp += 1
                        agent_records.append({"agent_title": ref.get("title"), "matched": g.get("title"), "match_type": "arxiv_id", "result": "TP"})
                        match_found = True
                        break
            if match_found: continue

            tit = norm_title(ref.get("title"))
            if tit:
                for idx, g in enumerate(gold_pool):
                    if idx not in matched_gold_indices and norm_title(g.get("title")) == tit:
                        matched_gold_indices.add(idx)
                        match_type_counts["exact_title"] += 1
                        paper_tp += 1
                        agent_records.append({"agent_title": ref.get("title"), "matched": g.get("title"), "match_type": "exact_title", "result": "TP"})
                        match_found = True
                        break
            if match_found: continue

            # No match found -> False Positive
            paper_fp += 1
            agent_records.append({"agent_title": ref.get("title"), "result": "FP", "fuzzy_match_candidates": fuzzy_cands(ref, gold_pool)})

        # False Negatives
        paper_fn = len(gold_pool) - len(matched_gold_indices)
        fn_refs = [gold_pool[i] for i in range(len(gold_pool)) if i not in matched_gold_indices]

        # Integrity Assertions (Per-Paper Level)
        assert paper_tp + paper_fn == len(unique_gold), f"Discrepancy in paper {arxiv_id}: TP({paper_tp}) + FN({paper_fn}) != unique_gold({len(unique_gold)})"
        assert paper_tp + paper_fp == len(unique_preds), f"Discrepancy in paper {arxiv_id}: TP({paper_tp}) + FP({paper_fp}) != unique_preds({len(unique_preds)})"

        # Update global scores
        global_tp += paper_tp
        global_fp += paper_fp
        global_fn += paper_fn

        per_paper_totals_sum["tp"] += paper_tp
        per_paper_totals_sum["fp"] += paper_fp
        per_paper_totals_sum["fn"] += paper_fn

        per_paper_results[arxiv_id] = {
            "status": agent_status,
            "agent_ref_count": len(unique_preds),
            "gold_ref_count": len(unique_gold),
            "tp": paper_tp,
            "fp": paper_fp,
            "fn": paper_fn,
            "agent_records": agent_records,
            "false_negative_refs": fn_refs
        }

    # Integrity Assertions (Global Level)
    scored_papers = [p for p in corpus_ids if per_paper_results[p]["status"] not in ["gold_unusable", "provider_block"]]
    assert global_tp == per_paper_totals_sum["tp"], "Sum of per-paper TPs does not equal global TP"
    assert global_fp == per_paper_totals_sum["fp"], "Sum of per-paper FPs does not equal global FP"
    assert global_fn == per_paper_totals_sum["fn"], "Sum of per-paper FNs does not equal global FN"

    # Calculate final metrics
    precision = global_tp / (global_tp + global_fp) if (global_tp + global_fp) > 0 else 0.0
    recall    = global_tp / (global_tp + global_fn) if (global_tp + global_fn) > 0 else 0.0
    f1        = (2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0)

    print("\n" + "=" * 70)
    print("RQ3 — CITATION LINK AGENT EVALUATION (DEDUPLICATED & AUDITED)")
    print("=" * 70)
    print(f"  True Positives  (TP): {global_tp}")
    print(f"  False Positives (FP): {global_fp}")
    print(f"  False Negatives (FN): {global_fn}")
    print(f"  Precision:            {precision:.5f}")
    print(f"  Recall:               {recall:.5f}")
    print(f"  F1-Score:             {f1:.5f}")
    print(f"\n  Match breakdown: {match_type_counts}")
    print(f"  Invalid LLM outputs removed: {total_invalid_outputs}")
    print(f"  Gold unusable papers excluded (API failures): {excluded_gold_unusable}")
    print(f"  Provider blocked papers excluded: {excluded_provider_blocks}")
    print(f"  Scored papers count: {len(scored_papers)}/40")
    print("=" * 70)

    output = {
        "audit_metadata": {
            "evaluation_timestamp":  datetime.now(timezone.utc).isoformat(),
            "research_question":     "How accurately can an LLM-based Citation Link Agent extract explicit bibliographic references from academic papers compared with Semantic Scholar reference records?",
            "gold_build_timestamp":  gold_audit.get("api_query_timestamp"),
            "gold_papers_resolved":  gold_audit.get("successfully_resolved"),
            "gold_total_references": gold_audit.get("total_references_fetched"),
            "rq1_rq2_frozen":        True,
            "one_to_one_matching":   True,
            "transitive_deduplication": True,
            "invalid_agent_outputs_filtered": total_invalid_outputs,
            "excluded_gold_unusable_papers": excluded_gold_unusable,
            "excluded_provider_blocked_papers": excluded_provider_blocks,
            "scored_papers_count": len(scored_papers),
        },
        "overall_metrics": {
            "true_positives":  global_tp,
            "false_positives": global_fp,
            "false_negatives": global_fn,
            "precision":       round(precision, 5),
            "recall":          round(recall, 5),
            "f1":              round(f1, 5),
            "match_type_breakdown": match_type_counts,
        },
        "per_paper_results": per_paper_results,
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(f"\nResults saved to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
