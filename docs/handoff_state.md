# Project Handoff State: Evaluation Status

Updated 2026-07-04. This file is a project-management handoff note, not a thesis source. Use the result JSON files listed below as the authoritative evidence.

---

## 1. Thesis Evaluation Status Overview

| Research Question | Status | Reference Document | Authoritative Output |
|:---|:---:|:---|:---|
| **RQ1: Retrieval Performance** | **Complete & Frozen** | `docs/rq1_evaluation_report.md` | `data/results/retrieval_metrics.json`, `data/results/cv_report.json` |
| **RQ2: Metadata and Topic Evaluation** | **Complete & Frozen** | `docs/rq2_report.md` | `data/results/rq2_results.json`, `data/results/b1c_test_results.json` |
| **RQ3: Citation Reference Evaluation** | **Complete & Frozen** | `docs/reproducibility.md` | `rq3_final_results.json` |
| **RQ4: Expert Evaluation** | **Complete** | `C:\Users\jubam\Downloads\RQ4_Evaluation_Responses.xlsx` | same spreadsheet |

---

## 2. Final Frozen Results

### RQ1 - Retrieval Metrics (k = 5)

Evaluated over the 40-paper corpus using 40 queries. Link-Expanded RAG uses 5-fold cross-validated alpha selection.

- **Flat RAG:** Recall@5 = **0.6958**, Precision@5 = **0.2350**, MRR@5 = **0.7292**
- **Structured RAG:** Recall@5 = **0.6958**, Precision@5 = **0.2250**, MRR@5 = **0.7438**
- **Link-Expanded RAG:** Recall@5 = **0.7188**, Precision@5 = **0.2300**, MRR@5 = **0.7425**

### RQ2 - Bibliographic and Topic Evaluation

- **Bibliographic metadata (n = 40):**
  - Title exact match: **0.9750**
  - Year exact match: **0.7750**
  - Venue fuzzy match: **0.5000**
  - Authors F1: **0.8250**

- **Strict topic evaluation (n = 22):**
  - Precision = **0.0762**
  - Recall = **0.1508**
  - F1 = **0.0957**

- **Canonicalised topic evaluation / calibrated vocabulary-mapping sensitivity analysis:**
  - Development/test split: **7 development papers / 15 held-out test papers**
  - Frozen parameters: tau_m = **0.7361**, best_k = **4**, tau_d = **0.85**
  - Held-out exact scores: Precision = **0.3389**, Recall = **0.4756**, F1 = **0.3831**

Do not use the internal experiment name `B1c` in the thesis body unless it appears in a reproducibility footnote or appendix. In the thesis, call this the **canonicalised topic evaluation** or **calibrated vocabulary-mapping evaluation**.

### RQ3 - Citation Reference Evaluation

Use the revised final pipeline only. The older `rq3_citation_link_evaluation.ipynb` and `data/results/rq3_citation_link_evaluation.json` are superseded and should be treated only as provenance/comparison artefacts.

Final revised run:

- Corpus papers considered: **40**
- Scored papers: **37**
- Excluded because usable gold references were unavailable: **3 papers**
- Provider-block exclusions: **0**
- In-scope extraction failures counted as false negatives: **2 papers**
- Invalid agent outputs filtered before scoring: **57**
- True positives: **1514**
- False positives: **283**
- False negatives: **534**
- Precision = **0.8425**
- Recall = **0.7393**
- F1 = **0.7875**

The RQ3 gold standard is the complete outgoing Semantic Scholar reference list for each scored paper, including external citations. It is not restricted to references pointing to papers in the local corpus.

### RQ4 - Expert Evaluation

The expert evaluation spreadsheet contains five rated generated notes and one expert evaluator.

- Faithfulness mean: **3.8**
- Coverage mean: **3.0**
- Readability mean: **3.4**
- Utility mean: **3.2**
- Overall mean across 20 ratings: **3.35**

Frame RQ4 as exploratory because it uses one expert and five papers.

---

## 3. Gold Standard Files

The expert-vault gold files are:

- `data/gold_labels/emile_vault_gold.json` - expert topics, formerly `metadata_gold.json`
- `data/gold_labels/emile_vault_arxiv_ids.json` - arXiv ID map, formerly `vault_arxiv_ids.json`

---

## 4. Final Output File Map

Use these files to populate thesis tables and result text:

- **RQ1 CV optimization:** `data/results/cv_report.json`
- **RQ1 core retrieval metrics:** `data/results/retrieval_metrics.json`
- **RQ1 runs:** `data/results/baseline_run.json`, `data/results/structured_run.json`, `data/results/link_run.json`
- **RQ2 bibliographic and strict topic results:** `data/results/rq2_results.json`
- **RQ2 canonicalised topic results:** `data/results/b1c_test_results.json`
- **RQ2 canonicalised mapping decisions:** `data/results/b1c_mappings.json`
- **RQ2 frozen threshold details:** `data/results/b1c_vocab_threshold.json`
- **RQ3 final metrics:** `rq3_final_results.json`
- **RQ3 final predictions:** `rq3_final_predictions.json`
- **RQ3 final raw responses:** `rq3_final_raw_responses.json`
- **RQ4 expert responses:** `C:\Users\jubam\Downloads\RQ4_Evaluation_Responses.xlsx`

---

## 5. Thesis Writing Notes

- Remove the old table row `RQ3 primary pipeline comparison - Common subset of 34 papers` from the methodology table. Keep only the final RQ3 row: `RQ3 citation-reference evaluation - 37 scored papers`.
- The old 34-paper RQ3 comparison can be mentioned only as implementation provenance if needed; it should not be presented as the main RQ3 dataset.
- The canonicalised topic evaluation is defensible as a secondary sensitivity analysis: it tests whether poor strict topic overlap is partly caused by vocabulary mismatch between agent labels and expert labels.
- Keep RQ1/RQ2 artefacts frozen when describing RQ3. The revised RQ3 pipeline should not imply that earlier RQ1/RQ2 results were regenerated.
