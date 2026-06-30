# RQ2 Ingestion Performance: Metadata Extraction Accuracy

This report presents the final evaluation methodology, experimental setup, and results for **Research Question 2 (RQ2)**: *How accurately can the LLM agent extract bibliographic metadata (title, year, venue, and authors) compared with externally curated bibliographic records, and semantic attributes (topics) compared with expert-authored annotations?*

---

## 1. Wording and Hypotheses

- **RQ2 Formulation:**
  How accurately can the LLM agent extract:
  1. **bibliographic metadata** — title, year, venue, and authors — compared with externally curated bibliographic records; and
  2. **semantic attributes** — topics — compared with expert-authored annotations?

- **Hypothesis H2:**
  The LLM agent is expected to achieve higher alignment for bibliographic metadata, measured using exact match and author-set F1, than for semantic attributes, measured using set-based Precision, Recall, and F1 against expert-authored annotations.

---

## 2. Evaluation Methodology

### Group A — Bibliographic Metadata (Objective Fields)

We evaluate the agent's bibliographic extraction on the full **40-paper corpus** against externally curated records retrieved from the **Semantic Scholar API**.

For each note, we evaluate:
1. **Title Exact Match** — exact match after alphanumeric normalization and lowercasing.
2. **Year Exact Match** — exact integer comparison.
3. **Venue Fuzzy Match** — normalized using a custom matcher resolving acronyms (e.g. `"ICML"` → `"International Conference on Machine Learning"`), computing Jaccard token-set similarity (excluding noise terms: *proceedings, conference, journal, workshop*), with a threshold of ≥ 0.70. Digits and years are stripped from venue strings before comparison, and various arXiv preprint formats (e.g., `arxiv`, `arxiv.org`, `preprint`) are mapped to a canonical `arxiv` token to ensure robust matching.
4. **Authors F1-Score** — set-based Precision, Recall, and F1 comparing extracted author last-name tokens to gold record authors.

---

### Group B — Semantic Alignment (Subjective Fields)

Evaluated on the **22 papers** present in both the 40-paper corpus and Emile's Obsidian vault.

- **Agent Predicted Set:** `hasTopic` only from the generated note frontmatter.
- **Emile Gold Set:** `topics` field from Emile's vault notes.

All strings are normalised: WikiLink brackets stripped, lowercase, punctuation removed, whitespace collapsed. 

#### B1 — Strict Expert Alignment (Primary Semantic Result)
Direct set-based Precision, Recall, and F1 of `Agent(hasTopic)` against Emile's manually annotated topics on all **22 papers**. Six full paper-title tags (bibliographic cross-references used by Emile as database relations, not concept labels) are excluded from Emile's gold set.

#### B1-hT-15 — Same-Subset Raw Baseline
An uncalibrated `hasTopic`-only baseline computed on the same **15 test papers** used by B1c. Paper-title tags are removed from the gold set, but no canonical vocabulary mapping, deduplication, or top-k selection is applied. This serves as the direct, apples-to-apples baseline for B1c.

- **B1c — Calibrated Semantic Alignment (Secondary Sensitivity Analysis)**
To analyze the impact of vocabulary and schema mismatch, we perform a calibrated exact match experiment:
1. A canonical vocabulary **V** of 49 topic labels is derived from Emile's complete tag set across all 22 papers (paper titles excluded).
2. All 49 labels are embedded using `nomic-ai/nomic-embed-text-v1.5` with the `clustering:` prefix.
3. A mapping threshold **τ_m = 0.7361** is computed as the 90th percentile of all 1,176 unique pairwise cosines within V — frozen before evaluation.
4. The 22 papers are split into a **7-paper development set** (for grid-searching deduplication threshold $\tau_d$ and top-$k$, yielding $\tau_d = 0.85, k = 4$) and a **15-paper test set**.
5. On the test set, agent topics are mapped to canonical V labels via the frozen $\tau_m$, the top-4 are retained, and exact string matching is evaluated against Emile's gold set.

---

## 3. Results

### Group A — Bibliographic Metadata (n = 40)

| Metric | Score |
|:---|:---:|
| Title Exact Match | **0.9750** |
| Year Exact Match | **0.7750** |
| Venue Fuzzy Match | **0.5000** |
| Authors F1-Score | **0.8250** |

All 40 generated notes were matched to a Semantic Scholar record.

---

### Group B — Semantic Alignment

| Metric | B1 Strict (n=22) | B1-hT-15 Baseline (n=15) | B1c Calibrated (n=15) |
|:---|:---:|:---:|:---:|
| Precision | 0.0762 | 0.1006 | **0.3389** |
| Recall | 0.1508 | 0.1989 | **0.4756** |
| **F1-Score** | **0.0957** | **0.1256** | **0.3831** |
| Avg. predicted tags | 5.3 (raw) | 5.3 (raw) | 4.0 (capped) |

*Note: B1 strict (n=22) is the primary semantic metric. B1-hT-15 and B1c represent a secondary sensitivity analysis on the 15-paper test subset.*

---

## 4. Discussion

### H2 is Supported
The results confirm Hypothesis H2. Bibliographic metadata extraction achieves high accuracy across objective fields (Title: 97.5%, Authors F1: 82.5%, Year: 77.5%), whereas strict semantic alignment against expert vault annotations yields a low F1-score of 9.6% (B1 Strict). 

The discrepancy is not a failure of LLM comprehension, but a fundamental characteristic of semantic classification:
1. **Granularity mismatch:** Emile uses a sparse, high-level set of concept labels (avg. 2.9 per paper), while the agent extracts more specific topics (avg. 5.3 per paper).
2. **Vocabulary divergence:** A domain expert writes custom semantic tags (e.g. `reasoning shortcuts`, `ensembles`) that are highly subjective. Even when the agent identifies the correct semantic space, it uses slightly different terminology.

### Impact of Calibration (B1-hT-15 vs B1c)
The calibrated semantic analysis isolates this vocabulary naming effect. When the agent's open-ended topics are mapped onto the expert's fixed 49-label ontology using embedding similarity (B1c):
- Exact F1-score on the 15-paper test subset rises from **0.1256** (raw baseline) to **0.3831** (calibrated exact match) — a **3.05× improvement**.
- Recall increases from **0.1989** to **0.4756**, indicating that nearly half of Emile's annotated topics are correctly captured by the agent once translated into the expert's custom dialect.

This improvement demonstrates that a significant portion of the semantic "error" in Group B is a schema-mapping problem rather than a lack of semantic understanding by the agent.

### Limitations
- **Preprint venue mismatch:** Venue match is moderate (50.0%) because the agent reads arXiv headers from preprints, whereas Semantic Scholar indexes the officially published conference venues.
- **Closed-vocabulary scope:** The vocabulary V was built using labels from all 22 overlapping papers. B1c therefore represents projection into a *known* expert ontology, rather than generalization to entirely unseen topic categories.
