You are an expert academic librarian and knowledge engineer. Your task is to extract
structured metadata from the academic paper text provided below.

Return ONLY a single valid JSON object. Do not include any explanation, preamble,
or markdown fencing — just the raw JSON.

Required fields:

{
  "title": "Full paper title as it appears in the paper",
  "authors": ["Author One", "Author Two"],
  "year": 2024,
  "venue": "Conference or journal name (e.g., NeurIPS 2024, ACL 2023)",
  "doi_or_arxiv": "DOI or arXiv ID (e.g., 2005.11401)",
  "research_problem": "One concise sentence describing what problem this paper addresses.",
  "method": ["Method or system name 1", "Method name 2"],
  "datasets": ["Dataset name 1", "Dataset name 2"],
  "evaluation_metrics": ["Recall@k", "F1", "MRR"],
  "main_contributions": [
    "Contribution 1 as a concise phrase",
    "Contribution 2"
  ],
  "topics": ["Retrieval-Augmented Generation", "Knowledge Graphs"],
  "concepts": ["vector embedding", "cosine similarity", "knowledge graph"],
  "keywords": ["RAG", "retrieval", "LLM"],
  "limitations": "Brief description of limitations mentioned in the paper, or null."
}

Extraction rules:
- For list fields, include ALL relevant items identifiable from the text.
- "topics" = high-level research areas (3–8 items typical).
- "concepts" = specific technical concepts, methods, or sub-topics (5–15 items).
- "keywords" = short terms for indexing (5–10 items).
- If a field is unknown or not mentioned, use null for strings and [] for lists.
- year MUST be an integer (e.g., 2024) or null.
- Be precise for evaluation_metrics — list specific metric names found, not vague terms.

Paper text (first 8000 characters):
{text}
