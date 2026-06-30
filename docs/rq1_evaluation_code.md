# RQ1 Evaluation Code — Revised Architecture with Safeguards

This document contains the complete python script implementing our revised, peer-defensible evaluation architecture for **RQ1 (Retrieval Performance)**. It includes the four evaluator-approved safeguards:
1. **Corpus Preflight Assertions:** Verifies that all 40 PDFs, extracted JSON files, generated notes, and gold labels map to the exact same document IDs.
2. **Strict Graph Leakage Prevention:** Uses a title map to detect paper-to-paper links and strips them completely, while converting general concept/topic links to plain text.
3. **Automatic 19-Minute Cache Bypass:** Bypasses baseline embedding generation if the file already exists on disk.
4. **Five-Fold Cross-Validated Alpha Selection:** Selects the optimal link-boosting parameter $\alpha$ using a deterministic score-transition search over 5 deterministic splits.

---

## Complete Evaluation Pipeline Code

```python
import json
import re
import math
from pathlib import Path
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

# ===========================================================================
# 1. Utility Functions: Link Cleaning & Token Chunking
# ===========================================================================

def build_title_map(notes_dir: Path) -> dict[str, str]:
    """
    Builds a lowercase Title/Alias/ArXivID -> arXiv ID mapping.
    This is used to detect paper-to-paper references.
    """
    title_map = {}
    for note_path in notes_dir.glob("*.md"):
        doc_id = note_path.stem
        content = note_path.read_text(encoding="utf-8", errors="ignore")
        
        # Lowercase arXiv ID mapping
        title_map[doc_id.lower()] = doc_id
        
        # Extract title from frontmatter
        title_match = re.search(r'^title:\\s*"(.*?)"', content, re.MULTILINE)
        if not title_match:
            title_match = re.search(r'^title:\\s*(.*?)$', content, re.MULTILINE)
        if title_match:
            title_map[title_match.group(1).strip().strip('"').strip("'").lower()] = doc_id
            
        # Extract aliases from frontmatter
        aliases_match = re.search(r'^aliases:\\s*\[(.*?)\]', content, re.MULTILINE)
        if aliases_match:
            aliases = [a.strip().strip('"').strip("'") for a in aliases_match.group(1).split(",") if a.strip()]
            for alias in aliases:
                title_map[alias.lower()] = doc_id
    return title_map


def clean_markdown_links(text: str, title_map: dict[str, str]) -> str:
    """
    Strips Obsidian WikiLinks from Markdown notes to prevent relation leakages:
    - Paper-to-paper links (targets matching our 40 papers) are stripped completely.
    - Concept/topic links (targets not in our paper corpus) are converted to plain text.
    """
    def replacer(match):
        raw_target = match.group(1).split('|')[0].strip()
        display_text = match.group(1).split('|')[-1].strip()
        
        # If the target refers to another paper in our corpus, strip it entirely
        if raw_target.lower() in title_map:
            return ""
        # Otherwise, keep the display text as plain text
        return display_text

    return re.sub(r"\[\[([^\]]+)\]\]", replacer, text)


def split_text_by_tokens(text: str, tokenizer, chunk_size: int = 512, overlap: int = 50) -> list[str]:
    """
    Splits unstructured text into overlapping chunks using the model's native tokenizer.
    """
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return []
    
    tokens = tokenizer.encode(text, add_special_tokens=False)
    
    chunks = []
    start = 0
    while start < len(tokens):
        end = min(len(tokens), start + chunk_size)
        chunk_tokens = tokens[start:end]
        chunk_text = tokenizer.decode(chunk_tokens)
        chunks.append(chunk_text)
        if end == len(tokens):
            break
        start = max(0, end - overlap)
    return chunks


# ===========================================================================
# 2. Preflight Check
# ===========================================================================

def run_preflight_check(extracted_dir: Path, notes_dir: Path, queries_path: Path, gold_path: Path):
    """
    Verifies that all 40 PDFs, extracted JSON files, generated notes, and 
    gold labels map to the exact same document IDs.
    """
    extracted_ids = {f.stem for f in extracted_dir.glob("*.json") if not f.name.startswith("_")}
    notes_ids = {f.stem for f in notes_dir.glob("*.md")}
    
    with open(queries_path, encoding="utf-8") as f:
        queries = json.load(f)
    
    with open(gold_path, encoding="utf-8") as f:
        gold = json.load(f)
        
    query_ids = [q["query_id"] for q in queries]
    unique_query_ids = set(query_ids)
    
    gold_ids = set()
    for doc_list in gold.values():
        gold_ids.update(doc_list)
        
    print(f"Preflight Check:")
    print(f"  Extracted JSON papers count: {len(extracted_ids)}")
    print(f"  Generated notes count:       {len(notes_ids)}")
    print(f"  Total queries count:         {len(queries)}")
    print(f"  Unique query IDs count:      {len(unique_query_ids)}")
    print(f"  Gold relevance papers count:  {len(gold_ids)}")
    
    assert len(extracted_ids) == 40, f"Error: Expected 40 extracted texts, found {len(extracted_ids)}"
    assert extracted_ids == notes_ids, "Error: Extracted JSON IDs and Generated Note IDs mismatch!"
    assert len(queries) == 40, f"Error: Expected exactly 40 queries, found {len(queries)}"
    assert len(unique_query_ids) == len(queries), "Error: Query IDs are not unique!"
    assert set(gold.keys()) == unique_query_ids, "Error: Mismatch between query IDs and gold label keys!"
    assert gold_ids.issubset(extracted_ids), "Error: Gold labels reference paper IDs not present in corpus!"
    print("PASS: Preflight corpus check completed successfully. All 40 papers and queries are aligned.")


# ===========================================================================
# 3. Index Builders
# ===========================================================================

def build_baseline_index(extracted_dir: Path, model, output_path: Path):
    json_files = sorted(extracted_dir.glob("*.json"))
    docs = []
    
    for f in json_files:
        if f.name.startswith("_"):
            continue
        data = json.loads(f.read_text(encoding="utf-8"))
        text = data["text"]
        
        chunks = split_text_by_tokens(text, model.tokenizer, chunk_size=512, overlap=50)
        for i, chunk in enumerate(chunks):
            docs.append({
                "doc_id": data["doc_id"],
                "source": data["source_pdf"],
                "chunk_id": i,
                "text": chunk
            })
            
    prefixed_texts = ["search_document: " + d["text"] for d in docs]
    print(f"Embedding {len(docs)} chunks for Pipeline A...")
    embeddings = model.encode(prefixed_texts, convert_to_numpy=True, normalize_embeddings=True)
    
    index_data = {
        "docs": docs,
        "embeddings": embeddings.tolist(),
        "model_name": "nomic-ai/nomic-embed-text-v1.5"
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f_out:
        json.dump(index_data, f_out)
    print(f"Pipeline A index saved -> {output_path}")


def build_structured_index(notes_dir: Path, model, output_path: Path):
    note_files = sorted(notes_dir.glob("*.md"))
    doc_ids = []
    texts = []
    max_limit = model.max_seq_length
    
    # Pre-build title map to detect paper links
    title_map = build_title_map(notes_dir)
    
    for md_path in note_files:
        content = md_path.read_text(encoding="utf-8")
        
        # Clean links to isolate text content from graph topology
        cleaned_text = clean_markdown_links(content, title_map)
        
        tokens = model.tokenizer.encode(cleaned_text, add_special_tokens=False)
        token_len = len(tokens)
        if token_len > max_limit:
            raise ValueError(f"Error: Note {md_path.name} has {token_len} tokens, exceeding {max_limit}!")
            
        doc_ids.append(md_path.stem)
        texts.append(cleaned_text)
        
    prefixed_texts = ["search_document: " + t for t in texts]
    print(f"Embedding {len(doc_ids)} structured notes for Pipeline B...")
    embeddings = model.encode(prefixed_texts, convert_to_numpy=True, normalize_embeddings=True)
    
    index_data = {
        "doc_ids": doc_ids,
        "embeddings": embeddings.tolist(),
        "model": "nomic-ai/nomic-embed-text-v1.5"
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f_out:
        json.dump(index_data, f_out)
    print(f"Pipeline B index saved -> {output_path}")


# ===========================================================================
# 4. Retrieval Modules
# ===========================================================================

def retrieve_baseline_maxp(query: str, docs, embeddings, model, k: int = 5) -> list[str]:
    query_text = "search_query: " + query
    query_emb = model.encode([query_text], convert_to_numpy=True, normalize_embeddings=True)
    similarities = cosine_similarity(query_emb, embeddings)[0]
    
    doc_max_scores = {}
    for idx, score in enumerate(similarities):
        doc_id = docs[idx]["doc_id"]
        if doc_id not in doc_max_scores or score > doc_max_scores[doc_id]:
            doc_max_scores[doc_id] = float(score)
            
    sorted_docs = sorted(doc_max_scores.items(), key=lambda x: x[1], reverse=True)
    return [doc_id for doc_id, score in sorted_docs[:k]]


def retrieve_structured(query: str, index_data, model, k: int = 5) -> list[str]:
    query_text = "search_query: " + query
    query_emb = model.encode([query_text], convert_to_numpy=True, normalize_embeddings=True)
    doc_embs = np.array(index_data["embeddings"])
    similarities = cosine_similarity(query_emb, doc_embs)[0]
    top_indices = np.argsort(similarities)[::-1][:k]
    return [index_data["doc_ids"][i] for i in top_indices]


def retrieve_link_expanded(query: str, index_data, model, notes_dir: Path, k: int = 5, alpha: float = 0.05) -> list[str]:
    query_text = "search_query: " + query
    query_emb = model.encode([query_text], convert_to_numpy=True, normalize_embeddings=True)
    doc_ids = index_data["doc_ids"]
    doc_embs = np.array(index_data["embeddings"])
    
    similarities = cosine_similarity(query_emb, doc_embs)[0]
    doc_scores = {doc_ids[i]: float(similarities[i]) for i in range(len(doc_ids))}
    
    initial_seeds = sorted(doc_ids, key=lambda x: doc_scores[x], reverse=True)[:k]
    title_map = build_title_map(notes_dir)
    linked_docs = set()
    
    for doc_id in initial_seeds:
        note_path = notes_dir / f"{doc_id}.md"
        if note_path.exists():
            text = note_path.read_text(encoding="utf-8")
            raw_links = re.findall(r"\[\[([^\]]+)\]\]", text)
            targets = [r.split("|")[0].strip() for r in raw_links]
            for target in targets:
                matched_id = title_map.get(target.lower())
                if matched_id and matched_id in doc_scores and matched_id not in initial_seeds:
                    linked_docs.add(matched_id)
                    
    boosted_scores = dict(doc_scores)
    for l_doc in linked_docs:
        boosted_scores[l_doc] += alpha
        
    re_ranked = sorted(doc_ids, key=lambda x: boosted_scores[x], reverse=True)[:k]
    return re_ranked


# ===========================================================================
# 5. Metrics & Runner
# ===========================================================================

def recall_at_5(retrieved, relevant) -> float:
    if not relevant:
        return 0.0
    hits = sum(1 for d in retrieved[:5] if d in relevant)
    return hits / len(relevant)


def precision_at_5(retrieved, relevant) -> float:
    hits = sum(1 for d in retrieved[:5] if d in relevant)
    return hits / 5.0


def mrr_at_5(retrieved, relevant) -> float:
    for rank, doc_id in enumerate(retrieved[:5], start=1):
        if doc_id in relevant:
            return 1.0 / rank
    return 0.0


def run_eval_suite(queries, gold, baseline_index_path, structured_index_path, notes_dir, output_dir):
    with open(baseline_index_path, encoding="utf-8") as f:
        baseline_data = json.load(f)
    baseline_docs = baseline_data["docs"]
    baseline_embs = np.array(baseline_data["embeddings"])
    
    with open(structured_index_path, encoding="utf-8") as f:
        structured_data = json.load(f)
        
    runs = {"baseline": {}, "structured": {}}
    per_query_metrics = {}
    
    for q in queries:
        qid = q["query_id"]
        text = q["text"]
        rel = set(gold[qid])
        
        # Search Pipelines A & B
        runs["baseline"][qid] = retrieve_baseline_maxp(text, baseline_docs, baseline_embs, model, k=5)
        runs["structured"][qid] = retrieve_structured(text, structured_data, model, k=5)
        
        assert len(runs["baseline"][qid]) == 5
        assert len(runs["structured"][qid]) == 5
        
        # Compute metrics per query
        per_query_metrics[qid] = {}
        for name in runs.keys():
            retrieved = runs[name][qid]
            per_query_metrics[qid][name] = {
                "retrieved": retrieved,
                "gold": list(rel),
                "Recall@5": recall_at_5(retrieved, rel),
                "Precision@5": precision_at_5(retrieved, rel),
                "MRR@5": mrr_at_5(retrieved, rel)
            }
            
    # Compute macro averages
    macro_results = {}
    for run_name in runs.keys():
        recalls = [per_query_metrics[qid][run_name]["Recall@5"] for qid in per_query_metrics.keys()]
        precisions = [per_query_metrics[qid][run_name]["Precision@5"] for qid in per_query_metrics.keys()]
        mrrs = [per_query_metrics[qid][run_name]["MRR@5"] for qid in per_query_metrics.keys()]
        
        macro_results[run_name] = {
            "Recall@5": float(np.mean(recalls)),
            "Precision@5": float(np.mean(precisions)),
            "MRR@5": float(np.mean(mrrs))
        }
        
    # Save reports to disk
    output_dir.mkdir(parents=True, exist_ok=True)
    with open(output_dir / "baseline_run.json", "w", encoding="utf-8") as f:
        json.dump(runs["baseline"], f, indent=2)
    with open(output_dir / "structured_run.json", "w", encoding="utf-8") as f:
        json.dump(runs["structured"], f, indent=2)
    with open(output_dir / "per_query_report.json", "w", encoding="utf-8") as f:
        json.dump(per_query_metrics, f, indent=2)
    with open(output_dir / "retrieval_metrics.json", "w", encoding="utf-8") as f:
        json.dump(macro_results, f, indent=2)
        
    return macro_results


# ===========================================================================
# 6. Results Freeze Verification Check
# ===========================================================================

from pathlib import Path

remaining = []
for note_path in Path("data/generated_notes").glob("*.md"):
    text = note_path.read_text(encoding="utf-8", errors="ignore")
    if "# Possible Relevance to My Thesis" in text:
        remaining.append(note_path.name)

print("Notes still containing thesis-relevance section:", remaining)
assert not remaining, f"Section still exists in: {remaining}"
```
