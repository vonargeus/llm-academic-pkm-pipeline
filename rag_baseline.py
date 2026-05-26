"""
RAG Baseline CLI Runner — Root Entrypoint.

This script acts as the command-line interface (CLI) for building and querying the flat RAG baseline index.
To maintain clean codebase design, prevent code duplication, and enforce modularity, all core operations 
(text extraction, chunking, embedding, indexing, and retrieval) are imported from the modular source file:
`src/retrieval/baseline.py`.

### Architectural Context & Scientific Choice:
Instead of duplicate codebases, the core logic is isolated in the library module (`src/retrieval/baseline.py`), 
while this root script provides the operational interface for the researcher.

### Technical & Design Justifications:
1. `sentence-transformers` (`all-MiniLM-L6-v2`): Used to map text segments into a 384-dimensional dense vector space.
2. `scikit-learn` (`cosine_similarity`): Chosen to calculate the semantic match between query vectors and document chunk vectors.
3. Character-to-Token Proxy: Chunks are sized by character length (300 characters, ~60–80 tokens) to guarantee compatibility 
   with the 256-token limit of the sentence-transformer model, preventing truncation issues.
4. Framework Transparency: Raw imports and explicit calculations are used instead of heavy orchestration layers 
   (like LangChain or LlamaIndex) to ensure complete experimental control and prevent hidden variable updates.
"""

import sys
from pathlib import Path

# Add the repository root to the python path to ensure robust imports of the src package
repo_root = Path(__file__).resolve().parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from src.retrieval.baseline import main

if __name__ == "__main__":
    main()