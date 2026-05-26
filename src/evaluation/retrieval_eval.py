"""
retrieval_eval.py — Compute retrieval metrics for baseline and structured systems.

Metrics: Recall@k, Precision@k, F1@k, MRR
For k in [1, 3, 5, 10]
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Core metric functions
# ---------------------------------------------------------------------------

def recall_at_k(retrieved: list[str], relevant: set[str], k: int) -> float:
    """Recall@k: fraction of relevant docs found in top-k."""
    if not relevant:
        return 0.0
    hits = sum(1 for doc_id in retrieved[:k] if doc_id in relevant)
    return hits / len(relevant)


def precision_at_k(retrieved: list[str], relevant: set[str], k: int) -> float:
    """Precision@k: fraction of top-k results that are relevant."""
    if k == 0:
        return 0.0
    hits = sum(1 for doc_id in retrieved[:k] if doc_id in relevant)
    return hits / k


def f1_at_k(retrieved: list[str], relevant: set[str], k: int) -> float:
    """F1@k: harmonic mean of Precision@k and Recall@k."""
    p = precision_at_k(retrieved, relevant, k)
    r = recall_at_k(retrieved, relevant, k)
    if p + r == 0:
        return 0.0
    return 2 * p * r / (p + r)


def reciprocal_rank(retrieved: list[str], relevant: set[str]) -> float:
    """Reciprocal Rank: 1/rank of first relevant document, or 0."""
    for rank, doc_id in enumerate(retrieved, start=1):
        if doc_id in relevant:
            return 1.0 / rank
    return 0.0


def ndcg_at_k(retrieved: list[str], relevant: set[str], k: int) -> float:
    """nDCG@k with binary relevance (0 or 1)."""
    def dcg(docs):
        return sum(
            (1 if doc_id in relevant else 0) / math.log2(i + 2)
            for i, doc_id in enumerate(docs[:k])
        )
    ideal = sorted([1 if d in relevant else 0 for d in retrieved], reverse=True)
    ideal_docs = [f"ideal_{i}" for i in range(len(ideal))]
    ideal_relevant = {f"ideal_{i}" for i, r in enumerate(ideal) if r == 1}
    idcg = dcg(ideal_docs)
    if idcg == 0:
        return 0.0
    return dcg(retrieved) / idcg


# ---------------------------------------------------------------------------
# Per-query evaluation
# ---------------------------------------------------------------------------

def evaluate_query(
    retrieved: list[str],
    gold_relevant: list[str],
    k_values: list[int] = [1, 3, 5, 10],
) -> dict[str, float]:
    """Compute all metrics for a single query."""
    relevant = set(gold_relevant)
    metrics: dict[str, float] = {}
    for k in k_values:
        metrics[f"recall@{k}"] = recall_at_k(retrieved, relevant, k)
        metrics[f"precision@{k}"] = precision_at_k(retrieved, relevant, k)
        metrics[f"f1@{k}"] = f1_at_k(retrieved, relevant, k)
        metrics[f"ndcg@{k}"] = ndcg_at_k(retrieved, relevant, k)
    metrics["mrr"] = reciprocal_rank(retrieved, relevant)
    return metrics


# ---------------------------------------------------------------------------
# Corpus-level evaluation
# ---------------------------------------------------------------------------

def evaluate_system(
    run: dict[str, list[str]],
    gold: dict[str, list[str]],
    k_values: list[int] = [1, 3, 5, 10],
    query_meta: dict[str, dict] | None = None,
) -> dict[str, Any]:
    """
    Evaluate a retrieval system over all queries.

    Args:
        run: {query_id: [retrieved_doc_id, ...]} (ranked, longest first)
        gold: {query_id: [relevant_doc_id, ...]}
        k_values: list of k cutoffs
        query_meta: optional {query_id: {"type": "simple"|"complex", ...}}

    Returns:
        Full results dict including per-query and aggregate metrics.
    """
    per_query: dict[str, dict] = {}
    all_metrics: dict[str, list[float]] = {}

    for qid, retrieved in run.items():
        gold_rel = gold.get(qid, [])
        if not gold_rel:
            continue  # skip queries with no gold labels

        m = evaluate_query(retrieved, gold_rel, k_values=k_values)
        q_type = (query_meta or {}).get(qid, {}).get("type", "unknown")
        per_query[qid] = {"type": q_type, "metrics": m, "n_relevant": len(gold_rel)}

        for key, val in m.items():
            all_metrics.setdefault(key, []).append(val)

    # Macro-average across all queries
    aggregate = {k: sum(v) / len(v) for k, v in all_metrics.items() if v}

    # Stratified by query type (simple vs complex)
    stratified: dict[str, dict[str, float]] = {}
    for qtype in set(v["type"] for v in per_query.values()):
        subset = [v["metrics"] for v in per_query.values() if v["type"] == qtype]
        if subset:
            stratified[qtype] = {
                k: sum(q[k] for q in subset) / len(subset) for k in subset[0]
            }

    return {
        "n_queries": len(per_query),
        "aggregate": aggregate,
        "stratified_by_type": stratified,
        "per_query": per_query,
    }


# ---------------------------------------------------------------------------
# Load / save helpers
# ---------------------------------------------------------------------------

def load_gold(gold_path: Path) -> dict[str, list[str]]:
    with open(gold_path, encoding="utf-8") as f:
        return json.load(f)


def load_run(run_path: Path) -> dict[str, list[str]]:
    with open(run_path, encoding="utf-8") as f:
        return json.load(f)


def save_results(results: dict, output_path: Path):
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"Results saved -> {output_path}")


# ---------------------------------------------------------------------------
# Pretty printer
# ---------------------------------------------------------------------------

def print_comparison_table(
    results_baseline: dict,
    results_structured: dict,
    results_link_expanded: dict | None = None,
    k_values: list[int] = [1, 3, 5, 10],
):
    """Print a side-by-side metric comparison table."""
    print("\n" + "=" * 90)
    print(f"{'Metric':<18} {'Baseline':>12} {'Structured':>12}" +
          (f" {'Link-Expanded':>14}" if results_link_expanded else ""))
    print("=" * 90)

    for k in k_values:
        for metric_name in [f"recall@{k}", f"precision@{k}", f"f1@{k}"]:
            b = results_baseline["aggregate"].get(metric_name, float("nan"))
            s = results_structured["aggregate"].get(metric_name, float("nan"))
            row = f"{metric_name:<18} {b:>12.4f} {s:>12.4f}"
            if results_link_expanded:
                l = results_link_expanded["aggregate"].get(metric_name, float("nan"))
                row += f" {l:>14.4f}"
            print(row)
        print("-" * 90)

    for metric_name in ["mrr"]:
        b = results_baseline["aggregate"].get(metric_name, float("nan"))
        s = results_structured["aggregate"].get(metric_name, float("nan"))
        row = f"{metric_name:<18} {b:>12.4f} {s:>12.4f}"
        if results_link_expanded:
            l = results_link_expanded["aggregate"].get(metric_name, float("nan"))
            row += f" {l:>14.4f}"
        print(row)
    print("=" * 90)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Evaluate retrieval system runs.")
    parser.add_argument("--baseline-run", required=True, help="JSON file: {qid: [doc_ids]}")
    parser.add_argument("--structured-run", required=True, help="JSON file: {qid: [doc_ids]}")
    parser.add_argument("--link-run", help="JSON file: link-expanded run (optional ablation)")
    parser.add_argument("--gold", required=True, help="Gold labels JSON: {qid: [doc_ids]}")
    parser.add_argument("--queries-meta", help="Query metadata JSON: {qid: {type: ...}}")
    parser.add_argument("--output", default="data/results/retrieval_metrics.json")
    args = parser.parse_args()

    gold = load_gold(Path(args.gold))
    query_meta = json.loads(Path(args.queries_meta).read_text()) if args.queries_meta else None

    baseline_run = load_run(Path(args.baseline_run))
    structured_run = load_run(Path(args.structured_run))

    res_baseline = evaluate_system(baseline_run, gold, query_meta=query_meta)
    res_structured = evaluate_system(structured_run, gold, query_meta=query_meta)
    res_link = None
    if args.link_run:
        link_run = load_run(Path(args.link_run))
        res_link = evaluate_system(link_run, gold, query_meta=query_meta)

    output = {
        "baseline": res_baseline,
        "structured": res_structured,
    }
    if res_link:
        output["link_expanded"] = res_link

    save_results(output, Path(args.output))
    print_comparison_table(res_baseline, res_structured, res_link)
