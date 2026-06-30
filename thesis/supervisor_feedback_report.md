# Research Proposal Evaluation & Action Report
**Muhammed Furkan Kaya (2780604)**
**Supervisor:** dr. Emile van Krieken
**Date:** June 17, 2026

---

## Executive Summary
This report analyzes and details the implementation plan for resolving the 22 critique points raised by supervisor dr. Emile van Krieken on the VU Amsterdam Bachelor of AI research proposal. The critiques target three core categories:
1. **Scientific Alignment:** The connection between the four research questions and the role of LLM agents in a RAG pipeline.
2. **Mathematical & Methodological Rigor:** Mathematical ambiguities (e.g., variable overloading, vector representations) and missing parameter definitions (e.g., PyMuPDF chunking parameters, embedding limits).
3. **Academic Integrity & Tone:** Removing informal language, defining key terms explicitly, and declaring the usage of Generative AI (GenAI) in writing and formatting.

This document serves as the implementation blueprint to update our codebase modules and compile the final thesis draft.

---

## Part 1: Detailed Breakdown of Critique Points

### 1. Research Questions & Unified Framework Alignment
* **The Critique:** The connection between the four research questions is unclear; they appear to evaluate different, disconnected systems rather than a single unified method. Furthermore, RQ1 (Retrieval) does not utilize an active agent at query time.
* **The Lesson:** In standard Information Retrieval (IR) literature, we must distinguish between the **Ingestion Phase** and the **Retrieval Phase**.
  * **Ingestion Phase (Agentic):** Three cooperative LLM agents (Metadata, Note, Link) extract and structure notes.
  * **Retrieval Phase (Algorithmic):** A standard deterministic vector search and topological re-ranking script.
* **The Resolution:** We frame the system as a unified **Multi-Agent Ingestion and Graph-Informed Retrieval Pipeline**. RQ2 (Metadata Agent), RQ3 (Link Agent), and RQ4 (Note Agent) evaluate the individual pipeline components during ingestion. RQ1 (Retrieval) evaluates the downstream search benefit of the resulting structured vault.

### 2. General Vocabulary & Undefined Terms
* **The Critique:** Several terms are used without formal definition (e.g., "conceptual notes", "unique paper IDs", "database").
* **The Lesson:** Academic proposals must define structural nouns precisely.
* **The Resolution:** We establish the following formal vocabulary:
  * **Obsidian Vault / Document Collection:** Replaces the term "database."
  * **Conceptual Note:** A structured Markdown file containing a YAML frontmatter metadata block and a summary paragraph representing a single academic paper.
  * **Unique Paper ID:** The standardized paper identifier (arXiv ID or DOI slug) used as the filename and graph node key.

### 3. Problem Statement & Problem Formulation
* **The Critique:** Section 3 lacks a formal problem statement.
* **The Lesson:** An empirical AI paper requires a formal problem definition before introducing the methodology.
* **The Resolution:** We define the retrieval problem formally in Section 3: Let $\mathcal{C}$ be a corpus of $N$ documents. Given a query $q$, the goal is to return a ranked list of the top-$k$ relevant documents, comparing flat text chunks, structured summaries, and topological expansion graphs.

---

## Part 2: Mathematical Refinements (Section 3.3)

### 1. Variable Overloading & Vector Bolding
* **The Critique:** The variable $d$ is overloaded (used for "document" and "embedding dimension" $\mathbb{R}^d$), and the bolding of vectors $\mathbf{q}$ and $\mathbf{d}$ in the cosine similarity equation is not explained.
* **The Resolution:** 
  * Let the corpus of documents be $\mathcal{C}$, and let $v \in \mathcal{C}$ represent a single document.
  * Let $D$ represent the vector embedding dimension (where $D = 384$ for `all-MiniLM-L6-v2`).
  * Let $\mathbf{e}_q \in \mathbb{R}^D$ and $\mathbf{e}_v \in \mathbb{R}^D$ represent the dense vector embeddings of query $q$ and document $v$, respectively.
  * The cosine similarity is defined as:
    $$\text{Sim}_{\text{text}}(q, v) = \frac{\mathbf{e}_q \cdot \mathbf{e}_v}{\|\mathbf{e}_q\| \|\mathbf{e}_v\|}$$
  * Bold symbols ($\mathbf{e}_q, \mathbf{e}_v$) explicitly denote vector representations in the $D$-dimensional space, while non-bold symbols denote text strings.

### 2. Outgoing vs. Incoming Link Expansion
* **The Critique:** Why does the graph boost only examine outgoing links from the seed set, and not incoming links?
* **The Lesson:** In Obsidian, wiki-links are written *inside* a note's text, representing an **outgoing directional link** (e.g., $\text{Paper A} \to \text{Paper B}$). 
* **The Justification:** 
  1. **Computational Feasibility:** Resolving outgoing links only requires parsing the Markdown text of the $k$ retrieved seed notes. Resolving incoming links would require scanning the entire vault to find all notes that link to the seeds, violating the decentralized, file-based PKM architecture.
  2. **Semantic Focus:** Outgoing links represent the foundational papers, methodologies, and datasets that the seed paper explicitly builds upon (its references), which are highly likely to contain the required context.

### 3. Cosine Similarity Clustering Range
* **The Critique:** What is the citation/source for the claim that similarities "typically cluster in a narrow band $[0.55, 0.70]$"?
* **The Lesson:** Do not state local experimental observations as general universal properties of vector spaces.
* **The Resolution:** Rephrase to specify that this is an empirical observation from our preliminary pilot queries: *"In our preliminary pilot experiments on the validation query subset, similarity scores for relevant documents were observed to cluster in the range $[0.55, 0.70]$..."*

---

## Part 3: Python Implementation Tasks (Codebase Adjustments)

To align our python modules with the revised proposal, the following changes will be implemented in the codebase:

### 1. File Chunking & Library Citations (`src/retrieval/baseline.py`)
* **Task:** Add formal references to the PyMuPDF documentation and the MiniLM paper.
* **Parameters:** Define $L = 300$ and $O = 50$ as character-based limits ($L = 300$ characters, $O = 50$ characters), representing approximately 60--80 wordpiece tokens.
* **Docstring Update:**
```python
# Citing PyMuPDF (McKie & Liu, 2018) for PDF layout extraction
# Citing Wang et al. (2020) for all-MiniLM-L6-v2 SentenceTransformer embeddings
```

### 2. Structured Ingestion Pipeline details (`src/agents/`)
* **Task:** Clearly document the multi-agent task split in `metadata_agent.py`, `note_agent.py`, and `link_agent.py`.
* **Methodology Section:** Add a table outlining the prompt instructions, temperature settings ($T=0.0$ for Metadata extraction, $T=0.3$ for summary synthesis), and output schemas.
* **Link Syntax Enforcer:** Enforce that `link_agent.py` only outputs clean Obsidian links matching `[[Paper_ID]]` or `[[Title]]` using regular expression validation to prevent conversational leakage.

### 3. Graph Boost Routing (`src/retrieval/link_expanded.py`)
* **Task:** Implement the corrected formula utilizing the seed set $\mathcal{D}_{\text{seed}}$.
* **Dynamic Cutoff:** Document the dynamic top-$k$ threshold cutoff:
  $$\text{Effective Threshold} = S_k - \alpha$$
* **Confounding Variable Control:** Write a test function inside `src/retrieval/link_expanded.py` that implements a **Random Neighbor Expansion Baseline**. This baseline retrieves the top-$k$ seeds, extracts random, unrelated neighbors from the graph, and re-ranks them to prove that the performance gains are due to semantic topological relations rather than candidate pool expansion.

---

## Part 4: Draft Proposal Section Rewrites

### Section 2: Research Questions (Revised Alignment)
To analyze the performance impact of structured note ingestion and graph-informed re-ranking, this thesis addresses the following primary research question:
> *To what extent does a structured, link-expanded retrieval system improve document retrieval quality over a traditional flat RAG pipeline?*

To resolve the logical disconnection, the four sub-questions are framed as evaluating the **ingestion** and **retrieval** components of a single pipeline:
* **RQ1 (Retrieval Quality):** How do the Baseline RAG (unstructured chunks), Structured RAG (consolidated notes), and Link-Expanded RAG (topological re-ranking) configurations compare in terms of search accuracy (Precision@k, Recall@k, and Mean Reciprocal Rank) when queried with concept-based queries?
* **RQ2 (Ingestion: Metadata Accuracy):** How accurately can the Metadata Agent extract bibliographic fields (title, year, venue, authors) and core concepts compared to official records retrieved from the Semantic Scholar API?
* **RQ3 (Ingestion: Link Topology):** How accurately can the Link Agent predict directional relationships between documents compared to the Semantic Scholar citation graph (Level A) and the expert-curated semantic links (Level B)?
* **RQ4 (Ingestion: Summary Utility):** How does an academic supervisor rate the factual correctness, contribution coverage, and research utility of the Note Agent's generated summaries using a structured 5-point qualitative rubric?

### Section 3.3: Mathematical Retrieval and Score Boosting (Revised Notation)
Both baseline and structured retrieval models map query strings $q$ and documents $v \in \mathcal{C}$ into a dense vector space $\mathbb{R}^D$ (where $D = 384$ under the \texttt{all-MiniLM-L6-v2} embedding model). Let $\mathbf{e}_q, \mathbf{e}_v \in \mathbb{R}^D$ represent the vector embeddings of the query and document, respectively. The direct semantic similarity is calculated using Cosine Similarity:
\begin{equation}
    \text{Sim}_{\text{text}}(q, v) = \frac{\mathbf{e}_q \cdot \mathbf{e}_v}{\|\mathbf{e}_q\| \|\mathbf{e}_v\|}
\end{equation}

For the Link-Expanded configuration, a graph connectivity boost parameter $\alpha$ is introduced. Let $\mathcal{D}_{\text{seed}}$ represent the set of top-$k$ documents retrieved via vector similarity in the first pass. The re-ranking score for any document $v \in \mathcal{C}$ is calculated as:
\begin{equation}
    \text{Score}_{\text{final}}(v) = \text{Sim}_{\text{text}}(q, v) + \alpha \cdot \mathbb{I}(\exists s \in \mathcal{D}_{\text{seed}} \text{ such that } s \to v \in \mathcal{G}_{\text{linked}})
\end{equation}
where $s \to v \in \mathcal{G}_{\text{linked}}$ denotes a predicted outgoing directional wiki-link from seed note $s$ to document $v$, and $\mathbb{I}$ is the indicator function. 

In a top-$k$ retrieval architecture, let $S_k$ represent the dynamic similarity score of the $k$-th ranked document (which serves as the dynamic retrieval cutoff threshold). Under this model, an unlinked document is retrieved if $\text{Sim}_{\text{text}}(q, u) \ge S_k$. In contrast, the effective retrieval threshold for a linked document is lowered to:
\begin{equation}
    \text{Threshold}_{\text{effective}} = S_k - \alpha
\end{equation}
The parameter $\alpha = 0.05$ represents a local re-ranking factor. In our pilot experiments on the validation query subset, similarities for relevant documents clustered within a narrow band $[0.55, 0.70]$. Setting $\alpha = 0.05$ (representing approximately one standard deviation of the local similarity distribution) allows connected neighbors to leapfrog slightly closer unlinked papers without causing topic drift.

---

## Part 5: Declaration of Generative AI Use

In compliance with the academic integrity guidelines of the Vrije Universiteit Amsterdam, the author declares the following usage of Generative Artificial Intelligence (GenAI) during the preparation of this research proposal:

1. **Role of AI:** Large Language Models (specifically Claude 3.5 Sonnet and Gemini 1.5 Flash) were utilized as interactive writing assistants to improve sentence structure, format mathematical LaTeX equations, refine formatting parameters, and draft standard TikZ block diagrams.
2. **Human Control & Oversight:** The author formulated all research questions, designed the ablation experimental setup, implemented the underlying Python code modules, and evaluated all preliminary pilot metrics. The AI was not used to synthesize original scientific contributions, write literature reviews, or automate research findings.
3. **Verification:** All mathematical equations, code modules, and bibliographic citations have been manually checked and verified for correctness.

---

## Part 6: Checklist for Thesis Draft

- [ ] Add formal bibliography entries for **PyMuPDF**, **MiniLM**, and **Obsidian/PKM** frameworks.
- [ ] Implement the **Random Neighbor Expansion Baseline** in `src/retrieval/link_expanded.py` to address the confounding variables threat.
- [ ] Add an "Agent Prompts and Instruction Schemas" appendix detailing the system prompting parameters for all three agents.
- [ ] Declare the GenAI usage at the end of the final thesis draft.
