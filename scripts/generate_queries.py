"""
scripts/generate_queries.py

Description:
    This script generates the evaluation queries dataset (`queries.json`) and the gold standard relevance 
    labels mapping (`gold_labels.json`) for the updated 40-paper corpus.

Query Set Architecture:
    - 40 queries total to preserve notebook size assertions.
    - 24 Simple Factual queries targeting new RAG/NeSy papers.
    - 8 Comparison queries (cross-document reasoning).
    - 8 Neurosymbolic queries (logical-neural integration).
"""

import json
from pathlib import Path

QUERIES = [
    # ── Simple/Factual Queries (24 Queries) ──────────────────
    {
        "query_id": "q1",
        "text": "Who are the authors of the Retrieval-Augmented Generation (RAG) paper?",
        "category": "simple_factual",
        "relevant_docs": ["2005.11401"]
    },
    {
        "query_id": "q2",
        "text": "What is Fusion-in-Decoder (FiD) and how does it leverage passage retrieval?",
        "category": "simple_factual",
        "relevant_docs": ["2007.01282"]
    },
    {
        "query_id": "q3",
        "text": "What framework evaluates RAG pipelines using faithfulness and answer relevance?",
        "category": "simple_factual",
        "relevant_docs": ["2309.15217"]
    },
    {
        "query_id": "q4",
        "text": "How does GraphRAG perform query-focused summarization over a corpus?",
        "category": "simple_factual",
        "relevant_docs": ["2404.16130"]
    },
    {
        "query_id": "q5",
        "text": "What is LightRAG and how does it optimize graph-based retrieval?",
        "category": "simple_factual",
        "relevant_docs": ["2410.05779"]
    },
    {
        "query_id": "q6",
        "text": "Describe HippoRAG's neurobiologically inspired long-term memory framework.",
        "category": "simple_factual",
        "relevant_docs": ["2405.14831"]
    },
    {
        "query_id": "q7",
        "text": "How does RAPTOR implement recursive tree-structured retrieval?",
        "category": "simple_factual",
        "relevant_docs": ["2401.18059"]
    },
    {
        "query_id": "q8",
        "text": "What is the Zettelkasten-inspired agentic memory system of A-MEM?",
        "category": "simple_factual",
        "relevant_docs": ["2502.12110"]
    },
    {
        "query_id": "q9",
        "text": "How does MemGPT manage virtual context to extend context windows?",
        "category": "simple_factual",
        "relevant_docs": ["2310.08560"]
    },
    {
        "query_id": "q10",
        "text": "Describe the long-term memory mechanism of MemoryBank for LLMs.",
        "category": "simple_factual",
        "relevant_docs": ["2305.10250"]
    },
    {
        "query_id": "q11",
        "text": "What is MemoRAG and how does it use a memory model for retrieval?",
        "category": "simple_factual",
        "relevant_docs": ["2409.05591"]
    },
    {
        "query_id": "q12",
        "text": "How does Self-RAG train LLMs to self-reflect and generate critique tokens?",
        "category": "simple_factual",
        "relevant_docs": ["2310.11511"]
    },
    {
        "query_id": "q13",
        "text": "What is Corrective Retrieval-Augmented Generation (CRAG) and how does it evaluate chunk relevance?",
        "category": "simple_factual",
        "relevant_docs": ["2401.15884"]
    },
    {
        "query_id": "q14",
        "text": "What is a semantic loss function and how is it used for deep learning with symbolic knowledge?",
        "category": "simple_factual",
        "relevant_docs": ["1711.11157"]
    },
    {
        "query_id": "q15",
        "text": "Describe the approximate method A-nesi for probabilistic neurosymbolic inference.",
        "category": "simple_factual",
        "relevant_docs": ["2212.12393"]
    },
    {
        "query_id": "q16",
        "text": "What are reasoning shortcuts in neurosymbolic learning according to Marconato et al.?",
        "category": "simple_factual",
        "relevant_docs": ["2305.19951"]
    },
    {
        "query_id": "q17",
        "text": "How does BEARS mitigate reasoning shortcuts in neurosymbolic models?",
        "category": "simple_factual",
        "relevant_docs": ["2410.02143"]
    },
    {
        "query_id": "q18",
        "text": "Explain DINGO's constrained inference framework for discrete diffusion models.",
        "category": "simple_factual",
        "relevant_docs": ["2505.13138"]
    },
    {
        "query_id": "q19",
        "text": "What is ReDiSC and how does it perform masked diffusion for node classification?",
        "category": "simple_factual",
        "relevant_docs": ["2510.14538"]
    },
    {
        "query_id": "q20",
        "text": "Describe the Unified Latents (UL) framework for vision-language models.",
        "category": "simple_factual",
        "relevant_docs": ["2603.03612"]
    },
    {
        "query_id": "q21",
        "text": "What is flow matching policy gradients and how does it apply to reinforcement learning?",
        "category": "simple_factual",
        "relevant_docs": ["2412.06014"]
    },
    {
        "query_id": "q22",
        "text": "How are probabilistic circuits used for tractable neurosymbolic inference and learning?",
        "category": "simple_factual",
        "relevant_docs": ["2502.01341"]
    },
    {
        "query_id": "q23",
        "text": "How does one properly define and use fuzzy logic operators in neurosymbolic AI?",
        "category": "simple_factual",
        "relevant_docs": ["2507.14484"]
    },
    {
        "query_id": "q24",
        "text": "What is the independence assumption in neurosymbolic learning and how does it affect logic constraints?",
        "category": "simple_factual",
        "relevant_docs": ["2507.21053"]
    },

    # ── Comparison Queries (8 Queries) ───────────────────
    {
        "query_id": "q25",
        "text": "Compare the retrieval and evaluation strategies of Self-RAG and Corrective RAG (CRAG).",
        "category": "comparison",
        "relevant_docs": ["2310.11511", "2401.15884"]
    },
    {
        "query_id": "q26",
        "text": "Compare GraphRAG and LightRAG in terms of knowledge graph utilization.",
        "category": "comparison",
        "relevant_docs": ["2404.16130", "2410.05779"]
    },
    {
        "query_id": "q27",
        "text": "How do HippoRAG and GraphRAG differ in their retrieval strategy?",
        "category": "comparison",
        "relevant_docs": ["2405.14831", "2404.16130"]
    },
    {
        "query_id": "q28",
        "text": "Which systems use memory-inspired architectures or Zettelkasten for LLM agents?",
        "category": "comparison",
        "relevant_docs": ["2502.12110", "2310.08560", "2305.10250", "2409.05591"]
    },
    {
        "query_id": "q29",
        "text": "Compare the hierarchical clustering retrieval of RAPTOR with standard flat RAG.",
        "category": "comparison",
        "relevant_docs": ["2401.18059", "2005.11401"]
    },
    {
        "query_id": "q30",
        "text": "Compare Fusion-in-Decoder and Retrieval-Augmented Generation for QA.",
        "category": "comparison",
        "relevant_docs": ["2007.01282", "2005.11401"]
    },
    {
        "query_id": "q31",
        "text": "Which papers address long-context retrieval evaluation or dialogue memory benchmark pipelines?",
        "category": "comparison",
        "relevant_docs": ["2402.17753", "2309.15217"]
    },
    {
        "query_id": "q32",
        "text": "Which papers focus on graph-based RAG methods?",
        "category": "comparison",
        "relevant_docs": ["2404.16130", "2410.05779", "2405.14831"]
    },

    # ── Neurosymbolic Queries (8 Queries) ───────────────────
    {
        "query_id": "q33",
        "text": "What approaches are proposed to address reasoning shortcuts in neurosymbolic AI?",
        "category": "neurosymbolic",
        "relevant_docs": ["2305.19951", "2410.02143", "2510.14538"]
    },
    {
        "query_id": "q34",
        "text": "Compare A-nesi and Semantic Loss in terms of probabilistic neurosymbolic reasoning.",
        "category": "neurosymbolic",
        "relevant_docs": ["2212.12393", "1711.11157"]
    },
    {
        "query_id": "q35",
        "text": "Which papers address symbol grounding or shortcuts in neurosymbolic learning?",
        "category": "neurosymbolic",
        "relevant_docs": ["2305.19951", "2410.02143", "2510.14538"]
    },
    {
        "query_id": "q36",
        "text": "How does the integration of first-order logic constraints affect neural network training?",
        "category": "neurosymbolic",
        "relevant_docs": ["1711.11157", "2212.12393"]
    },
    {
        "query_id": "q37",
        "text": "What papers use diffusion models for discrete sequence or symbolic logic generation?",
        "category": "neurosymbolic",
        "relevant_docs": ["2505.13138", "2510.14538"]
    },
    {
        "query_id": "q38",
        "text": "What are the main research areas that combine deep learning with symbolic reasoning?",
        "category": "neurosymbolic",
        "relevant_docs": ["1711.11157", "2212.12393", "2305.19951", "2410.02143", "2505.13138", "2510.14538"]
    },
    {
        "query_id": "q39",
        "text": "How are fuzzy logic operators like Lukasiewicz t-norms compared and evaluated in neurosymbolic learning?",
        "category": "neurosymbolic",
        "relevant_docs": ["2507.14484", "2507.21053"]
    },
    {
        "query_id": "q40",
        "text": "Which papers are co-authored by Emile van Krieken?",
        "category": "neurosymbolic",
        "relevant_docs": ["2212.12393", "2505.13138", "2510.14538"]
    }
]

def main():
    queries_dir = Path("data/queries")
    gold_dir = Path("data/gold_labels")
    queries_dir.mkdir(parents=True, exist_ok=True)
    gold_dir.mkdir(parents=True, exist_ok=True)

    queries_output = []
    for q in QUERIES:
        queries_output.append({
            "query_id": q["query_id"],
            "text": q["text"],
            "category": q["category"]
        })
    
    with open(queries_dir / "queries.json", "w", encoding="utf-8") as f:
        json.dump(queries_output, f, indent=2)
    print(f"Generated data/queries/queries.json ({len(queries_output)} queries).")

    gold_output = {}
    for q in QUERIES:
        gold_output[q["query_id"]] = q["relevant_docs"]
        
    with open(gold_dir / "gold_labels.json", "w", encoding="utf-8") as f:
        json.dump(gold_output, f, indent=2)
    print(f"Generated data/gold_labels/gold_labels.json.")

if __name__ == "__main__":
    main()
