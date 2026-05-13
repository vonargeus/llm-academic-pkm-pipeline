# Annotation Guidelines

**Purpose:** Standardise how gold labels are constructed for metadata quality, link quality,
and retrieval relevance evaluation.

> [!IMPORTANT]
> All annotations are done by the thesis author. A random sample (~20 pairs) is spot-checked
> by the supervisor for quality assurance. Annotation decisions should be documented here
> for reproducibility.

---

## 1. Retrieval Relevance Labels

### Definition

A document `d` is **relevant** to query `q` if:
- A reader familiar with the topic would expect `d` to help answer `q`, AND
- The document contains substantive information directly addressing `q` (not just tangentially mentioning a term).

### Binary Labels

- **1 (relevant)**: The document directly addresses the query. If the user asked `q`, this document would be a useful result.
- **0 (not relevant)**: The document does not directly address `q`, or mentions it only incidentally.

### Annotation Process

1. For each query `q`, read the query carefully.
2. For each paper in the corpus, decide: would a user searching for `q` want to find this paper?
3. Assign 1 or 0.
4. Aim for **at least 1 and at most 5 relevant documents per query**.
5. If a query has 0 relevant documents in the corpus, discard the query.
6. Document any ambiguous decisions in `docs/annotation_notes.md`.

### Inter-Annotator Agreement (QA check)

- Spot-check: supervisor reviews 20 random (query, document) pairs.
- Report Cohen's κ if spot-check is completed.
- If disagreement > 20%, re-annotate the full query.

---

## 2. Metadata Gold Labels

### Source

For each paper, construct gold labels from:
- **Title, authors, year, venue:** directly from the paper's title page or header.
- **DOI or arXiv ID:** from the paper URL or header.
- **Research problem:** one sentence paraphrase of the abstract's problem statement.
- **Method:** names of the main proposed methods/systems. Use names exactly as used in the paper.
- **Datasets:** names of all datasets used in experiments. Use official dataset names.
- **Evaluation metrics:** all metric names mentioned in the experiments section.
- **Topics:** 3–8 high-level research area labels. Use terms from the paper's keywords, abstract, or related work. Normalise to common phrases (e.g., "retrieval-augmented generation", not "RAG").
- **Concepts:** 5–15 specific technical concepts, algorithms, or sub-topics mentioned.
- **Keywords:** 5–10 short index terms.
- **Limitations:** brief paraphrase of limitations section. Can be null.

### Normalisation Rules

When comparing predicted vs. gold:
- Lowercase everything.
- Remove punctuation.
- Compare after normalisation (e.g., "Recall@k" = "recall at k" = "recall@k").
- For list fields: a predicted item is correct if its normalised form matches any gold item's normalised form.
- Abbreviations: treat "RAG" and "Retrieval-Augmented Generation" as the same if context makes it clear.

### Coverage

- Gold labels for at minimum **all papers** in the corpus.
- Aim to annotate within 15–20 minutes per paper.

---

## 3. Link Gold Labels

### Definition

A link between paper A and paper B exists if:
- Paper A explicitly cites paper B AND there is a meaningful semantic relationship, OR
- Paper A does not cite B but both papers address the same topic/method/dataset in a way that a knowledgeable reader would connect them.

**Do not** add links just because two papers are in the same broad field.

### Link Types

| Type | Definition |
|------|-----------|
| `hasTopic` | Paper A is about a high-level topic that is the subject of note B |
| `usesMethod` | Paper A uses the method described in paper/note B |
| `evaluatesOn` | Paper A evaluates on the dataset in B |
| `extends` | Paper A directly builds on the approach in paper B |
| `comparesTo` | Paper A explicitly uses paper B as a baseline |
| `contradicts` | Paper A's findings contradict or challenge paper B |
| `hasDataset` | B is a dataset note, A uses that dataset |
| `publishedIn` | B is a venue note, A was published there |
| `isA` | A concept in A is a specific instance of a concept in B |
| `subset` | A topic in A is a sub-area of a topic in B |

### Annotation Process

1. For each pair of papers (A, B) in the corpus:
   - Read both titles, abstracts, and related work sections.
   - Decide: is there a meaningful link?
   - If yes, assign the most specific link type.
2. Links are **directional** but may be bidirectional (e.g., A extends B AND B is extended by A).
3. Do not over-link: prefer precision over recall in gold labels.
4. Record all annotation decisions in a structured spreadsheet or JSON file.

### Gold Link Format

```json
[
  {
    "source": "doc_id_A",
    "target": "doc_id_B",
    "link_type": "extends",
    "direction": "forward",
    "confidence": 1.0,
    "justification": "Paper A explicitly builds on the RAG framework from paper B."
  }
]
```

---

## 4. Summary Evaluation Rubric

Used by supervisor for 20 sampled summaries. Each dimension scored 1–5.

| Score | Meaning |
|-------|---------|
| 1 | Poor — significant errors, major omissions, or misleading |
| 2 | Below acceptable — some correct points but notable problems |
| 3 | Acceptable — mostly correct, minor issues |
| 4 | Good — accurate and useful |
| 5 | Excellent — highly accurate, complete, and clear |

### Dimensions

1. **Factual correctness**: Are all claims in the summary factually accurate w.r.t. the paper?
2. **Contribution coverage**: Does the summary cover the main contribution?
3. **Hallucination absence**: Does the summary avoid claims not supported by the paper?
4. **Usefulness for rediscovery**: Would this summary help a researcher decide whether to read the paper?
5. **Clarity**: Is the summary written in clear, readable language?

### Instructions for Supervisor

- Read each generated summary without having the paper open.
- Score each dimension independently.
- Note any specific factual errors in the comments field.
- Time estimate: ~5–7 minutes per summary.
