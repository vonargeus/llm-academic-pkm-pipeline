"""
metadata_eval.py — Evaluate LLM-generated metadata against gold labels.

Metrics:
  - Exact match for scalar fields (year, venue, doi_or_arxiv)
  - Precision / Recall / F1 for multi-label list fields (topics, methods, datasets, metrics, concepts)
  - Title similarity (normalised string match)
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def normalise(s: str) -> str:
    """Lowercase, strip punctuation for fuzzy comparison."""
    return re.sub(r"[^a-z0-9 ]", "", s.lower()).strip()


def exact_match(pred: Any, gold: Any) -> int:
    """Return 1 if pred == gold (after normalisation if strings)."""
    if isinstance(pred, str) and isinstance(gold, str):
        return int(normalise(pred) == normalise(gold))
    return int(pred == gold)


def set_prf(pred_list: list[str], gold_list: list[str]) -> dict[str, float]:
    """Compute Precision, Recall, F1 for multi-label fields (token-level normalisation)."""
    pred_set = {normalise(x) for x in (pred_list or []) if x}
    gold_set = {normalise(x) for x in (gold_list or []) if x}

    if not gold_set:
        # No gold labels: can't evaluate
        return {"precision": None, "recall": None, "f1": None, "n_gold": 0, "n_pred": len(pred_set)}

    tp = len(pred_set & gold_set)
    precision = tp / len(pred_set) if pred_set else 0.0
    recall = tp / len(gold_set)
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

    return {
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "n_gold": len(gold_set),
        "n_pred": len(pred_set),
        "tp": tp,
        "fp": len(pred_set - gold_set),
        "fn": len(gold_set - pred_set),
    }


# ---------------------------------------------------------------------------
# Per-note evaluation
# ---------------------------------------------------------------------------

# Fields evaluated with exact match
EXACT_MATCH_FIELDS = ["year", "venue", "doi_or_arxiv"]

# Fields evaluated with P/R/F1
SET_FIELDS = ["topics", "concepts", "keywords", "evaluation_metrics", "datasets", "method", "main_contributions"]


def evaluate_note_metadata(
    predicted: dict,
    gold: dict,
) -> dict[str, Any]:
    """
    Evaluate predicted metadata for a single note against gold labels.

    Args:
        predicted: LLM-generated metadata dict.
        gold: Manually annotated ground truth dict.

    Returns:
        Per-field evaluation results dict.
    """
    results: dict[str, Any] = {"doc_id": predicted.get("doc_id", "unknown")}

    # Title similarity (normalised)
    pred_title = normalise(predicted.get("title", ""))
    gold_title = normalise(gold.get("title", ""))
    results["title_exact"] = int(pred_title == gold_title)
    results["title_pred"] = predicted.get("title", "")
    results["title_gold"] = gold.get("title", "")

    # Exact match fields
    for field in EXACT_MATCH_FIELDS:
        results[f"{field}_exact"] = exact_match(
            predicted.get(field), gold.get(field)
        )
        results[f"{field}_pred"] = predicted.get(field)
        results[f"{field}_gold"] = gold.get(field)

    # Set P/R/F1 fields
    for field in SET_FIELDS:
        pred_vals = predicted.get(field) or []
        gold_vals = gold.get(field) or []
        if isinstance(pred_vals, str):
            pred_vals = [pred_vals]
        if isinstance(gold_vals, str):
            gold_vals = [gold_vals]
        results[f"{field}_prf"] = set_prf(pred_vals, gold_vals)

    return results


# ---------------------------------------------------------------------------
# Corpus-level aggregation
# ---------------------------------------------------------------------------

def aggregate_metadata_results(per_note: list[dict]) -> dict[str, Any]:
    """Macro-average exact match and P/R/F1 across all notes."""
    agg: dict[str, Any] = {}

    # Exact match fields
    for field in ["title"] + EXACT_MATCH_FIELDS:
        key = f"{field}_exact"
        vals = [r[key] for r in per_note if key in r]
        agg[key] = round(sum(vals) / len(vals), 4) if vals else None

    # Set P/R/F1 fields
    for field in SET_FIELDS:
        key = f"{field}_prf"
        submetrics = ["precision", "recall", "f1"]
        for sm in submetrics:
            vals = [r[key][sm] for r in per_note if r.get(key, {}).get(sm) is not None]
            agg[f"{field}_{sm}"] = round(sum(vals) / len(vals), 4) if vals else None

    return agg


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def evaluate_metadata_corpus(
    predictions_dir: Path,
    gold_path: Path,
    output_path: Path | None = None,
) -> dict[str, Any]:
    """
    Evaluate metadata quality over the full corpus.

    Args:
        predictions_dir: Directory of per-note metadata JSONs (from metadata_agent).
        gold_path: Path to gold labels JSON: {doc_id: {field: value, ...}}
        output_path: Where to save results.

    Returns:
        Dict with per-note results and aggregate metrics.
    """
    with open(gold_path, encoding="utf-8") as f:
        gold_all = json.load(f)

    per_note = []
    for pred_file in sorted(predictions_dir.glob("*.json")):
        with open(pred_file, encoding="utf-8") as f:
            predicted = json.load(f)
        doc_id = predicted.get("doc_id", pred_file.stem)
        if doc_id not in gold_all:
            print(f"  [warn] No gold labels for doc_id={doc_id!r}. Skipping.")
            continue
        gold = gold_all[doc_id]
        gold["doc_id"] = doc_id
        result = evaluate_note_metadata(predicted, gold)
        per_note.append(result)

    aggregate = aggregate_metadata_results(per_note)
    output = {"n_notes": len(per_note), "aggregate": aggregate, "per_note": per_note}

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        print(f"Metadata evaluation results saved → {output_path}")

    return output


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--predictions", required=True, help="Dir with per-note metadata JSON files")
    parser.add_argument("--gold", required=True, help="Gold labels JSON: {doc_id: {field: value}}")
    parser.add_argument("--output", default="data/results/metadata_eval.json")
    args = parser.parse_args()

    results = evaluate_metadata_corpus(
        Path(args.predictions), Path(args.gold), Path(args.output)
    )

    print("\n=== METADATA EVALUATION AGGREGATE ===")
    for k, v in results["aggregate"].items():
        print(f"  {k:<35} {v}")
