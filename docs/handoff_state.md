# Project Handoff State: Evaluation Status & Next Steps

This document serves as the single source of truth for the next AI agent session. It summarizes the current state of the thesis evaluations, frozen results, and the clean workspace setup.

---

## 1. Thesis Evaluation Status Overview

| Research Question | Status | Reference Document | Output JSON |
|:---|:---:|:---|:---|
| **RQ1: Retrieval Performance** | **Complete & Frozen** | `docs/rq1_evaluation_report.md` | `data/results/retrieval_metrics.json` |
| **RQ2: Metadata Accuracy** | **Complete & Frozen** | `docs/rq2_report.md` | `data/results/rq2_results.json` |
| **RQ3: Link Quality** | **Next Task** | `docs/reproducibility.md` | `data/results/link_run.json` |
| **RQ4: Qualitative Summary** | **Next Task** | — | — |

---

## 2. Final Frozen Results

### RQ1 — Retrieval Metrics (k = 5)
Evaluated over the **40-paper corpus** using 40 queries. Link-Expanded RAG uses 5-fold cross-validated alpha selection.

- **Baseline RAG:** Recall@5 = **0.6958**, Precision@5 = **0.2350**, MRR@5 = **0.7292**
- **Structured RAG:** Recall@5 = **0.6958**, Precision@5 = **0.2250**, MRR@5 = **0.7438**
- **Link-Expanded RAG (CV-Optimized):** Recall@5 = **0.7188**, Precision@5 = **0.2300**, MRR@5 = **0.7425**

---

### RQ2 — Bibliographic & Semantic Alignment

- **Group A (Bibliographic, n = 40):**
  - Title Exact Match: **0.9750**
  - Year Exact Match: **0.7750**
  - Venue Fuzzy Match: **0.5000** (using arXiv/preprint canonical mapping)
  - Authors F1: **0.8250**

- **Group B (Semantic Topics):**
  - **B1 Strict (n=22):** P = 0.0762, R = 0.1508, F1 = **0.0957** (Primary semantic result)
  - **B1-hT-15 Baseline (n=15):** P = 0.1006, R = 0.1989, F1 = **0.1256** (Same-subset control baseline)
  - **B1c Calibrated (n=15):** P = 0.3389, R = 0.4756, F1 = **0.3831** (Secondary calibrated exact match)

---

## 3. Renamed Gold Standard Files
To make their origins clear, the gold files have been renamed:
*   `data/gold_labels/emile_vault_gold.json` (expert topics, formerly `metadata_gold.json`)
*   `data/gold_labels/emile_vault_arxiv_ids.json` (arXiv ID map, formerly `vault_arxiv_ids.json`)

All references in `rq2_metadata_evaluation.ipynb`, `rq2_calibration.ipynb`, `docs/reproducibility.md`, and `scripts/parse_emile_vault.py` point to these new names.

---

## 4. Final Output JSON File Map
These JSON files contain the exact metrics and should be used to populate any tables:
*   **RQ1 CV Optimization:** `data/results/cv_report.json`
*   **RQ1 Core Metrics:** `data/results/retrieval_metrics.json`
*   **RQ2 Primary & B1 Results:** `data/results/rq2_results.json`
*   **RQ2 Calibrated B1c/B1s Results:** `data/results/b1c_test_results.json`
*   **RQ2 B1c Mapping Decisions:** `data/results/b1c_mappings.json`
*   **RQ2 Frozen τ_m Threshold Details:** `data/results/b1c_vocab_threshold.json`

---

## 5. Next Steps for the Next Agent (RQ3 Link Quality)

When starting the next session, the agent should:
1.  Read `docs/reproducibility.md` to see the planned pipeline parameters.
2.  Develop a clean script to evaluate **LLM link prediction accuracy** (comparing the agent's links against the gold link graph in `data/gold_labels/link_gold.json`).
3.  The uncalibrated link metrics will likely be low due to the extreme sparsity of Emile's vault (only 2 paper-to-paper links in gold vs. 90 predicted links).
4.  Frame the link density mismatch clearly (validating H3). Do not attempt to tune links to fit the sparse manual vault; explain the difference and reference the fact that the agent's denser graph improved search quality in RQ1 (+3.3% Recall).
