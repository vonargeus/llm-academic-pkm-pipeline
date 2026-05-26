"""
scripts/generate_queries.py

Description:
    This script generates the evaluation queries dataset (`queries.json`) and the gold standard relevance 
    labels mapping (`gold_labels.json`) for the 22-paper corpus.

Query Set Architecture & Design:
    * Corpus size: 22 papers (6 Neurosymbolic AI papers from supervisor Emile's hand-crafted vault, and 16 RAG/GraphRAG/Memory papers).
    * Total Queries: 40 queries designed to evaluate the retrieval system across varying levels of difficulty:
      1. Simple Factual (22 queries): Direct single-paper factual questions (1 per paper in the active corpus).
      2. Comparison (9 queries): Cross-paper comparative questions requiring the retrieval of multiple RAG or GraphRAG papers.
      3. Neurosymbolic (9 queries): Domain-specific neurosymbolic queries targeting the 6 gold papers.
    * Gold standard relevance mapping: Compiles the list of relevant document IDs (arXiv IDs) for each query. 

Usage:
    python scripts/generate_queries.py
"""

import json
from pathlib import Path

# Define the 40 queries stratified by category and difficulty
QUERIES = [
    # ── Simple/Factual Queries (1 per paper in our active corpus) ──────────────────
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
        "text": "What coding theory properties are evaluated in the three-weight linear codes paper?",
        "category": "simple_factual",
        "relevant_docs": ["2306.07516"]
    },
    {
        "query_id": "q13",
        "text": "How does STORM synthesize topic outlines from scratch using multi-perspective question asking?",
        "category": "simple_factual",
        "relevant_docs": ["2402.14207"]
    },
    {
        "query_id": "q14",
        "text": "What pipeline does LoCoMo use to evaluate open-domain dialogues over long contexts?",
        "category": "simple_factual",
        "relevant_docs": ["2402.17753"]
    },
    {
        "query_id": "q15",
        "text": "Describe FBK's simultaneous speech translation submission for IWSLT 2024.",
        "category": "simple_factual",
        "relevant_docs": ["2406.14177"]
    },
    {
        "query_id": "q16",
        "text": "How does the training of small reasoners benefit from LLM explanations?",
        "category": "simple_factual",
        "relevant_docs": ["2210.06726"]
    },
    {
        "query_id": "q17",
        "text": "What is a semantic loss function and how is it used for deep learning with symbolic knowledge?",
        "category": "simple_factual",
        "relevant_docs": ["1711.11157"]
    },
    {
        "query_id": "q18",
        "text": "Describe the approximate method A-nesi for probabilistic neurosymbolic inference.",
        "category": "simple_factual",
        "relevant_docs": ["2212.12393"]
    },
    {
        "query_id": "q19",
        "text": "What are reasoning shortcuts in neurosymbolic learning according to Marconato et al.?",
        "category": "simple_factual",
        "relevant_docs": ["2305.19951"]
    },
    {
        "query_id": "q20",
        "text": "How does BEARS mitigate reasoning shortcuts in neurosymbolic models?",
        "category": "simple_factual",
        "relevant_docs": ["2402.12240"]
    },
    {
        "query_id": "q21",
        "text": "Explain Neurosymbolic Diffusion Models (NeSyDM) and their applications.",
        "category": "simple_factual",
        "relevant_docs": ["2505.13138"]
    },
    {
        "query_id": "q22",
        "text": "What introduction to symbol grounding and reasoning shortcuts is provided by Marconato et al. in 2025?",
        "category": "simple_factual",
        "relevant_docs": ["2510.14538"]
    },

    # ── Complex/Comparative Queries (Multi-paper relationships) ───────────────────
    {
        "query_id": "q23",
        "text": "Compare the memory mechanisms of MemGPT and MemoryBank.",
        "category": "comparison",
        "relevant_docs": ["2310.08560", "2305.10250"]
    },
    {
        "query_id": "q24",
        "text": "Which papers focus on evaluating RAG pipelines or dialog systems?",
        "category": "comparison",
        "relevant_docs": ["2309.15217", "2402.17753"]
    },
    {
        "query_id": "q25",
        "text": "Compare GraphRAG and LightRAG in terms of knowledge graph utilization.",
        "category": "comparison",
        "relevant_docs": ["2404.16130", "2410.05779"]
    },
    {
        "query_id": "q26",
        "text": "How do HippoRAG and GraphRAG differ in their retrieval strategy?",
        "category": "comparison",
        "relevant_docs": ["2405.14831", "2404.16130"]
    },
    {
        "query_id": "q27",
        "text": "Which systems use memory-inspired architectures or Zettelkasten for LLM agents?",
        "category": "comparison",
        "relevant_docs": ["2502.12110", "2310.08560", "2305.10250", "2409.05591"]
    },
    {
        "query_id": "q28",
        "text": "Compare the hierarchical clustering retrieval of RAPTOR with standard flat RAG.",
        "category": "comparison",
        "relevant_docs": ["2401.18059", "2005.11401"]
    },
    {
        "query_id": "q29",
        "text": "What approaches are proposed to address reasoning shortcuts in neurosymbolic AI?",
        "category": "neurosymbolic",
        "relevant_docs": ["2305.19951", "2402.12240", "2510.14538"]
    },
    {
        "query_id": "q30",
        "text": "Compare A-nesi and Semantic Loss in terms of probabilistic neurosymbolic reasoning.",
        "category": "neurosymbolic",
        "relevant_docs": ["2212.12393", "1711.11157"]
    },
    {
        "query_id": "q31",
        "text": "How do STORM and MemoRAG handle long contexts or document generation?",
        "category": "comparison",
        "relevant_docs": ["2402.14207", "2409.05591"]
    },
    {
        "query_id": "q32",
        "text": "Which papers are co-authored by Emile van Krieken?",
        "category": "metadata_lookup",
        "relevant_docs": ["2212.12393", "2402.12240", "2505.13138", "2510.14538"]
    },
    {
        "query_id": "q33",
        "text": "Which papers address symbol grounding or shortcuts in neurosymbolic learning?",
        "category": "neurosymbolic",
        "relevant_docs": ["2305.19951", "2402.12240", "2510.14538"]
    },
    {
        "query_id": "q34",
        "text": "What are the common evaluation metrics used across different RAG systems?",
        "category": "comparison",
        "relevant_docs": ["2005.11401", "2309.15217"]
    },
    {
        "query_id": "q35",
        "text": "How does the integration of first-order logic constraints affect neural network training?",
        "category": "neurosymbolic",
        "relevant_docs": ["1711.11157", "2212.12393"]
    },
    {
        "query_id": "q36",
        "text": "Which papers focus on graph-based RAG methods?",
        "category": "comparison",
        "relevant_docs": ["2404.16130", "2410.05779", "2405.14831"]
    },
    {
        "query_id": "q37",
        "text": "Compare the retrieval mechanisms of A-MEM and HippoRAG.",
        "category": "comparison",
        "relevant_docs": ["2502.12110", "2405.14831"]
    },
    {
        "query_id": "q38",
        "text": "What are the main research areas that combine deep learning with symbolic reasoning?",
        "category": "neurosymbolic",
        "relevant_docs": ["1711.11157", "2212.12393", "2305.19951", "2402.12240", "2505.13138", "2510.14538"]
    },
    {
        "query_id": "q39",
        "text": "Compare Fusion-in-Decoder and Retrieval-Augmented Generation for QA.",
        "category": "comparison",
        "relevant_docs": ["2007.01282", "2005.11401"]
    },
    {
        "query_id": "q40",
        "text": "Which papers deal with machine translation or explanations from large language models?",
        "category": "comparison",
        "relevant_docs": ["2406.14177", "2210.06726"]
    }
]

def main():
    # Paths for output
    queries_dir = Path("data/queries")
    gold_dir = Path("data/gold_labels")
    queries_dir.mkdir(parents=True, exist_ok=True)
    gold_dir.mkdir(parents=True, exist_ok=True)

    # 1. Output queries.json
    # Format: list of queries with query_id, text, and category
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

    # 2. Output gold_labels.json
    # Format: dictionary mapping query_id to list of relevant document IDs (arXiv IDs)
    gold_output = {}
    for q in QUERIES:
        gold_output[q["query_id"]] = q["relevant_docs"]
        
    with open(gold_dir / "gold_labels.json", "w", encoding="utf-8") as f:
        json.dump(gold_output, f, indent=2)
    print(f"Generated data/gold_labels/gold_labels.json.")

if __name__ == "__main__":
    main()
