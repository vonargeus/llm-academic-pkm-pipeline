"""
link_eval.py — Evaluate LLM-generated links against gold labels.

Metrics:
  - Link Precision, Recall, F1 (strict match: source + target + type)
  - Partial Match Precision, Recall, F1 (loose match: source + target only)
  - Relation Type Accuracy (given correct source+target, is type correct?)
"""

from __future__ import annotations

import json
from pathlib import Path

def normalize_target(t: str) -> str:
    """Lowercase and strip for fuzzy matching if needed."""
    return t.lower().strip()

def evaluate_links(predicted_links: list[dict], gold_links: list[dict]) -> dict:
    """Evaluate predicted links against gold links."""
    # Build sets for evaluation
    pred_strict = {(l["source"], normalize_target(l.get("linked_to", l.get("target", ""))), l["link_type"]) for l in predicted_links}
    pred_loose = {(l["source"], normalize_target(l.get("linked_to", l.get("target", "")))) for l in predicted_links}
    
    gold_strict = {(l["source"], normalize_target(l.get("linked_to", l.get("target", ""))), l["link_type"]) for l in gold_links}
    gold_loose = {(l["source"], normalize_target(l.get("linked_to", l.get("target", "")))) for l in gold_links}
    
    # Loose (pair only) P/R/F1
    tp_loose = len(pred_loose & gold_loose)
    p_loose = tp_loose / len(pred_loose) if pred_loose else 0.0
    r_loose = tp_loose / len(gold_loose) if gold_loose else 0.0
    f1_loose = 2 * p_loose * r_loose / (p_loose + r_loose) if p_loose + r_loose > 0 else 0.0
    
    # Strict (pair + type) P/R/F1
    tp_strict = len(pred_strict & gold_strict)
    p_strict = tp_strict / len(pred_strict) if pred_strict else 0.0
    r_strict = tp_strict / len(gold_strict) if gold_strict else 0.0
    f1_strict = 2 * p_strict * r_strict / (p_strict + r_strict) if p_strict + r_strict > 0 else 0.0
    
    # Type accuracy (only for pairs that exist in both)
    type_correct = tp_strict
    type_total = tp_loose
    type_accuracy = type_correct / type_total if type_total > 0 else 0.0
    
    return {
        "n_gold_links": len(gold_links),
        "n_pred_links": len(predicted_links),
        "loose_match_pair_only": {
            "precision": round(p_loose, 4),
            "recall": round(r_loose, 4),
            "f1": round(f1_loose, 4)
        },
        "strict_match_pair_and_type": {
            "precision": round(p_strict, 4),
            "recall": round(r_strict, 4),
            "f1": round(f1_strict, 4)
        },
        "relation_type_accuracy": round(type_accuracy, 4),
        "hallucinated_links": len(pred_loose - gold_loose),
        "missing_links": len(gold_loose - pred_loose)
    }

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--predictions", required=True, help="JSON file with predicted links")
    parser.add_argument("--gold", required=True, help="JSON file with gold links")
    parser.add_argument("--output", default="data/results/link_eval.json")
    args = parser.parse_args()

    with open(args.predictions, encoding="utf-8") as f:
        preds = json.load(f)
    with open(args.gold, encoding="utf-8") as f:
        gold = json.load(f)

    results = evaluate_links(preds, gold)
    
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
        
    print(json.dumps(results, indent=2))
