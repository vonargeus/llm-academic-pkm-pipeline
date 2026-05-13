# Related Work — Methodology & Evaluation Extraction

**Purpose:** This table systematically extracts methodology and evaluation design from key papers
for use in the Related Work chapter. For each paper, I record what is directly reusable for
thesis design decisions.

> [!NOTE]
> Focus is on: dataset construction, query design, baselines, evaluation metrics, annotation strategy,
> and failure analysis — not on summarising the paper content.

---

## 1. Lewis et al. (2020) — Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks

**arXiv:** 2005.11401 | **Venue:** NeurIPS 2020

| Dimension | Detail |
|-----------|--------|
| **Problem** | How to ground LLM generation with retrieved documents for knowledge-intensive tasks |
| **Method** | Parametric (seq2seq LM) + non-parametric (dense retrieval over Wikipedia) combined in RAG-token and RAG-sequence variants |
| **Dataset** | NaturalQuestions, TriviaQA, WebQuestions, CuratedTrec (open-domain QA); MSMARCO, Jeopardy (generation) |
| **Dataset size** | Millions of Wikipedia passages; standard benchmark splits |
| **Baselines** | Closed-book GPT-2, T5 fine-tuned, REALM, DPR |
| **Retrieval metrics** | EM (exact match), F1, Hit@k |
| **Generation metrics** | ROUGE-L, BLEU, EM |
| **Human evaluation** | No (automatic only) |
| **Reusable for thesis** | Core baseline paper. Justifies flat-RAG baseline design. Dense retrieval + chunking setup directly mirrors thesis Baseline. Shows that retrieval corpus quality matters. |
| **Limitations / gaps** | No structured metadata. No graph links between documents. Retrieval is flat (no inter-chunk structure). Does not study personal/academic knowledge bases. |

---

## 2. Edge et al. (2024) — From Local to Global: A Graph RAG Approach to Query-Focused Summarization

**arXiv:** 2404.16130 | **Microsoft Research**

| Dimension | Detail |
|-----------|--------|
| **Problem** | How to answer global, sensemaking questions over large corpora where flat RAG fails |
| **Method** | KG extraction → community detection → hierarchical community summaries → map-reduce generation |
| **Dataset** | Podcast transcripts (~1M tokens), news articles (~1.7M tokens) — not academic papers |
| **Dataset size** | ~2 corpora, 500 queries (synthetically generated from each corpus) |
| **Query generation** | LLM generates queries requiring global understanding (not single-document lookup) |
| **Baselines** | Naive RAG (vector search), text summarisation, community summary RAG |
| **Retrieval metrics** | Not standard IR metrics — uses **LLM-as-a-judge** (GPT-4 pairwise comparison) |
| **Generation metrics** | Comprehensiveness, Diversity, Empowerment (LLM-judged, 1–5 or win-rate) |
| **Human evaluation** | No (LLM-as-judge acts as proxy) |
| **Reusable for thesis** | Justifies why cross-document queries need structure. Informs the design of "complex/cross-note" query type. Query synthesis approach (use LLM to generate balanced queries) is directly reusable. **Important warning:** LLM-as-judge is too expensive/opaque for a bachelor thesis — use binary relevance labels instead. |
| **Limitations / gaps** | LLM-as-judge is subjective and expensive. No metadata evaluation. Not designed for personal knowledge bases. Global summaries vs. our typed links are very different. |

---

## 3. Balog & Kenter (2019) — Personal Knowledge Graphs: A Research Agenda

**Venue:** SIGIR 2019 | **No arXiv** (published at SIGIR)

| Dimension | Detail |
|-----------|--------|
| **Problem** | What are Personal Knowledge Graphs (PKGs), what are the research challenges, and how should they be evaluated? |
| **Method** | Survey / research agenda paper (not empirical) |
| **Dataset** | No dataset (conceptual paper) |
| **Baselines** | N/A |
| **Evaluation proposed** | Entity coverage, relation accuracy, completeness, currency, privacy. No single standard metric established. |
| **Human evaluation** | Conceptually recommended; no empirical study in this paper |
| **Reusable for thesis** | Foundational motivation for the thesis. Defines what a PKG is and what challenges remain. Directly supports RQ3 (link quality). Cite this when introducing the Obsidian-as-PKG framing. Key gap: no LLM agent for PKG population at the time — now my thesis partially fills that. |
| **Limitations / gaps** | Very conceptual. No implementation or benchmark. No evaluation framework for LLM-generated links (predates LLMs as capable link generators). |

---

## 4. Weng et al. (2025) — A-MEM: Agentic Memory for LLM Agents

**arXiv:** 2502.12110

| Dimension | Detail |
|-----------|--------|
| **Problem** | How can LLM agents dynamically organize, link, and evolve their memories without static pre-defined structures? |
| **Method** | Zettelkasten-inspired: each memory = atomic note with keywords + tags + context description + links. Uses cosine similarity for initial retrieval + LLM for nuanced link classification. Memory evolution: updates notes as new info arrives. |
| **Dataset** | LoCoMo (long-term conversation), HotpotQA, NQ, WebShop |
| **Dataset size** | LoCoMo: 50 sessions, 300+ turns per session. HotpotQA: ~7K test questions. |
| **Baselines** | MemGPT, MemoryBank, ChatDB, ReadAgent, Zep |
| **Retrieval metrics** | F1, BLEU, ROUGE-L, METEOR for conversational QA |
| **Generation metrics** | F1, BLEU, ROUGE-L |
| **Human evaluation** | No |
| **Ablation studies** | Remove link generation → drops performance. Remove memory evolution → drops. |
| **Reusable for thesis** | Most directly related paper. Core inspiration for the agent that generates notes + links. **Key reusable element:** the two-stage link generation (cosine similarity → LLM typing) is essentially what my Link Agent does. The ablation design (with/without links) maps directly to my Ablation 1. Cite as closest prior work. |
| **Limitations / gaps** | Evaluated on conversational memory, not academic paper retrieval. Notes are short memory snippets, not structured Obsidian-style notes. No metadata evaluation. Not designed for an Obsidian-style knowledge base. No typed relation labels evaluated. |

---

## 5. Sarthi et al. (2024) — RAPTOR: Recursive Abstractive Processing for Tree-Organized Retrieval

**arXiv:** 2401.18059

| Dimension | Detail |
|-----------|--------|
| **Problem** | Flat chunk-based RAG fails for questions requiring multi-document reasoning; hierarchical summarisation can help |
| **Method** | Cluster chunks → summarise clusters → create tree of summaries → retrieve from any level |
| **Dataset** | QASPER, NarrativeQA, QuALITY, GovReport (long-doc QA) |
| **Dataset size** | Standard splits of each benchmark |
| **Baselines** | BM25, DPR, standard chunk RAG, other hierarchical approaches |
| **Retrieval metrics** | Accuracy (multiple choice), F1 (QA) |
| **Generation metrics** | F1, accuracy |
| **Human evaluation** | No |
| **Reusable for thesis** | Justifies hierarchical/structured note representations. Shows that structured aggregation (even if different from typed links) helps multi-document queries. The idea that simple flat chunking is insufficient for complex queries directly parallels my thesis claim. |
| **Limitations / gaps** | Summaries are generic, not structured with typed metadata. No link evaluation. Summaries are auto-generated, not structured as Obsidian notes. |

---

## 6. Es et al. (2023) — RAGAS: Automated Evaluation of Retrieval Augmented Generation

**arXiv:** 2309.15217

| Dimension | Detail |
|-----------|--------|
| **Problem** | How to automatically evaluate RAG systems without expensive human annotation |
| **Method** | Three metrics: Faithfulness (is generated answer faithful to retrieved context?), Answer Relevance (does answer address the question?), Context Recall (does retrieved context contain answer?) — all evaluated using LLM |
| **Dataset** | WikiEval (curated), various QA datasets |
| **Baselines** | Human ratings, traditional QA metrics |
| **Retrieval metrics** | Context Recall (novel automated metric using LLM), Context Precision |
| **Generation metrics** | Faithfulness, Answer Relevance |
| **Human evaluation** | Yes — used to validate automated metrics against human scores |
| **Reusable for thesis** | Informs evaluation design. **Important:** RAGAS uses LLM-as-judge which I avoid for my core evaluation. But Context Recall is conceptually equivalent to my Recall@k. Use this citation to motivate why I use binary gold labels + standard IR metrics (more transparent and reproducible for bachelor scope). The paper shows that automated evaluation is possible but requires care. |
| **Limitations / gaps** | LLM-judge introduces its own biases. Assumes generated answers, not just retrieval. Not designed for structured note evaluation. No metadata or link evaluation. |

---

## 7. Guo et al. (2024) — LightRAG: Simple and Fast Retrieval-Augmented Generation

**arXiv:** 2410.05779

| Dimension | Detail |
|-----------|--------|
| **Problem** | GraphRAG is computationally expensive; can graph-enhanced RAG be made cheaper without sacrificing quality? |
| **Method** | Dual-level retrieval: local (entity-level, similar to vector RAG) + global (graph-level, community summaries). Uses a knowledge graph of entities and relations extracted by LLM. |
| **Dataset** | Agriculture, CS, Legal, Mix (4 domain corpora), each ~500K tokens |
| **Dataset size** | 4 corpora, ~4K queries (LLM-generated) |
| **Baselines** | Naive RAG, GraphRAG (Edge et al.), RQ-RAG |
| **Retrieval metrics** | Comprehensiveness, Diversity, Empowerment (LLM-judged); also win-rates |
| **Generation metrics** | LLM-judged quality |
| **Human evaluation** | No (LLM-as-judge) |
| **Reusable for thesis** | Shows that graph structure improves retrieval especially for relationship queries. Entity-relation extraction is analogous to my Metadata Agent + Link Agent. Dual-level retrieval (local + global) maps to my Option C (link-expanded retrieval). **Caution:** their evaluation is LLM-as-judge, which I replace with binary gold labels. |
| **Limitations / gaps** | LLM-as-judge evaluation. KG is entity-relation triples, not typed Obsidian-style links with metadata fields. Not designed for personal academic knowledge bases. |

---

## 8. Gutierrez et al. (2024) — HippoRAG: Neurobiologically Inspired Long-Term Memory for LLMs

**arXiv:** 2405.14831

| Dimension | Detail |
|-----------|--------|
| **Problem** | LLMs lack episodic long-term memory; can a hippocampal-inspired KG architecture improve multi-hop retrieval? |
| **Method** | Extract named entities → build entity co-occurrence graph → retrieve via PageRank-based graph traversal |
| **Dataset** | MuSiQue (multi-hop QA), 2WikiMultiHopQA, PopQA |
| **Dataset size** | Standard benchmark splits |
| **Baselines** | ColBERT, BM25, RAG, IRCoT, GraphRAG |
| **Retrieval metrics** | Recall@2, F1@2, Answer F1 |
| **Generation metrics** | Answer F1 |
| **Human evaluation** | No |
| **Reusable for thesis** | **Directly comparable setup.** Uses Recall@k as a primary metric (same as my thesis). Multi-hop / cross-document queries are the hard cases where graph structure helps — same claim as my thesis. **Dataset design inspiration:** multi-hop questions where the answer requires traversing 2+ links are the "complex" query type in my thesis. |
| **Limitations / gaps** | Entity-graph only, no typed link relations. No metadata evaluation. Domain is general QA, not personal academic note management. PageRank traversal ≠ typed Obsidian links. |

---

## 9. Qian et al. (2024) — MemoRAG: Moving towards Next-Gen RAG via Memory-Inspired Knowledge Discovery

**arXiv:** 2409.05591

| Dimension | Detail |
|-----------|--------|
| **Problem** | Standard RAG fails for fuzzy, global, or cross-document queries because chunked retrieval lacks memory |
| **Method** | Dual-system: memory model (cheap LLM over full corpus → global memory) + retrieval model (standard dense retrieval). Memory clues guide retrieval. |
| **Dataset** | TriviaQA, NarrativeQA, MSR-QA (QA), also long-document summarisation |
| **Baselines** | Naive RAG, RQ-RAG, HyDE, GraphRAG |
| **Retrieval metrics** | F1, EM, ROUGE-L |
| **Human evaluation** | No |
| **Reusable for thesis** | Shows that memory-augmented retrieval helps for fuzzy queries. Global memory ≈ my structured notes with cross-links. Baseline comparison structure is directly reusable. |
| **Limitations / gaps** | Memory is a hidden LLM state, not an inspectable structured note. No typed links. No metadata evaluation. |

---

## 10. Maharana et al. (2024) — LoCoMo: Localised Long-Context Memory for Conversational Agents

**arXiv:** 2402.17753

| Dimension | Detail |
|-----------|--------|
| **Problem** | How to benchmark long-term conversational memory in LLM agents? |
| **Method** | Benchmark construction: multi-session conversations with manually annotated QA pairs. Tests single-session, multi-session, and temporal reasoning. |
| **Dataset** | LoCoMo dataset: 50 conversations, 9K+ QA pairs, multi-session |
| **Baselines** | No-memory, retrieval-augmented, full-context |
| **Evaluation metrics** | F1, BLEU, ROUGE-L, recall of key facts |
| **Human evaluation** | Yes (for dataset annotation) |
| **Reusable for thesis** | **Most important for evaluation design.** Their stratified evaluation (single vs multi-session queries) maps directly to my simple vs complex query stratification. Their annotation approach (manually create QA pairs with gold answers) is exactly what I should do for my query set. Gold label construction protocol is reusable. |
| **Limitations / gaps** | Conversational memory, not academic document retrieval. No Obsidian-style notes or metadata. |

---

## 11. Shao et al. (2024) — Assisting in Writing Wikipedia-like Articles From Scratch with Large Language Models (STORM)

**arXiv:** 2402.14207

| Dimension | Detail |
|-----------|--------|
| **Problem** | Can LLM agents produce well-structured, grounded long-form articles by simulating expert perspective-driven research? |
| **Method** | Multi-agent pipeline: generate diverse questions → retrieve answers → synthesise outline → write article section by section |
| **Dataset** | Wikipedia evaluation: FreshWiki (100 recently created articles) |
| **Baselines** | Direct generation, simple retrieval-augmented writing |
| **Generation metrics** | Article quality (ROUGE-based + human rating), factual grounding |
| **Human evaluation** | Yes — human raters evaluate article quality |
| **Reusable for thesis** | Inspires multi-step agentic pipeline design (my PDF → Note → Link orchestration). Shows that structured agent pipelines produce more organised outputs. Citation for "agent-generated structured content" in intro. |
| **Limitations / gaps** | No metadata or link evaluation. Focus is on long-form generation quality, not retrieval. No academic Obsidian setup. |

---

## Summary Table: What Each Paper Contributes to My Thesis

| Paper | Core contribution to my evaluation design |
|-------|------------------------------------------|
| Lewis et al. 2020 | Justifies baseline RAG design; metric precedent (EM, F1, Hit@k) |
| Edge et al. 2024 | Complex query design; community structure motivation; LLM-judge to avoid |
| Balog & Kenter 2019 | PKG framing; link quality challenge; motivates RQ3 |
| A-MEM 2025 | Closest prior work; note+link design; ablation design |
| RAPTOR 2024 | Hierarchical structure helps complex queries (supports thesis claim) |
| RAGAS 2023 | Evaluation framework; why I use binary labels not LLM-judge |
| LightRAG 2024 | Dual-level retrieval (parallel to my link expansion); KG approach |
| HippoRAG 2024 | Recall@k for graph RAG; multi-hop query design |
| MemoRAG 2024 | Memory clues for fuzzy queries; simple vs complex comparison |
| LoCoMo 2024 | **Gold label annotation protocol; stratified query evaluation design** |
| STORM 2024 | Multi-agent pipeline justification |

---

## Key Methodological Observations (for thesis writing)

1. **No prior work evaluates typed link quality in structured personal academic notes.** This is the main gap my thesis fills for RQ3.
2. **LLM-as-judge is common but problematic for bachelor scope.** I explicitly avoid it in favour of binary gold labels + standard IR metrics. Cite RAGAS + Edge et al. when explaining this choice.
3. **Query stratification** (simple/factual vs complex/cross-document) is best practice. HippoRAG and LoCoMo both do this. My query set should do the same.
4. **Ablation design** (no links → links → link expansion) mirrors A-MEM ablations and is well-justified.
5. **Dataset size** in related work: 15–100 documents is common at this scope for structured retrieval experiments. My 15–25 paper corpus is defensible.
6. **Annotation**: LoCoMo uses manually constructed QA pairs with gold answers. My approach (manually create 50–100 query/relevance pairs) is methodologically aligned with the field.
