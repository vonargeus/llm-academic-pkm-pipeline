"""
scripts/generate_notes.py

Description:
    This script is the main entry point to execute the LLM agent pipeline over your paper corpus.
    It orchestrates the transformation of raw extracted academic text into interlinked Obsidian Markdown notes.

Pipeline Mechanism & Agent Design:
    1. Orchestrator (process_corpus): Manages the flow of processing each document in data/extracted_text/.
    2. Metadata Agent (metadata_agent.py): Calls Gemini to extract structured metadata (title, year, authors, 
       venue, datasets, methods, concepts) into a standardized YAML frontmatter format.
    3. Note Agent (note_agent.py): Generates structured markdown summaries of each paper (Main Contribution, 
       Method, Key Results, Limitations).
    4. Link Agent (link_agent.py): Evaluates candidate papers and establishes typed relational links 
       (e.g., "extends", "comparesTo", "usesMethod") represented as Obsidian [[WikiLinks]].

Library and Coding Decisions:
    * Google Generative AI (google.generativeai): Used to interact with Gemini models.
    * Model Rotation Pool: Implements a list of models (Gemini 2.5 Flash, 3.1 Flash Lite, etc.) and rotates 
      automatically on 429 Rate Limit/Quota Exhaustion exceptions. During execution, it automatically 
      switches to `gemini-3.1-flash-lite` to utilize its 500 requests/day free tier.
    * Idempotence & Caching: Skips already processed notes, allowing resumes without waste.

Usage:
    python scripts/generate_notes.py --input data/extracted_text/ --output data/generated_notes/
"""

import argparse
import sys
from pathlib import Path

# Add the repository root to the python path to ensure robust imports of the src package
repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

# Auto-load dotenv
try:
    from dotenv import load_dotenv
    load_dotenv(repo_root / ".env")
except ImportError:
    pass

from src.note_generation.orchestrator import process_corpus

def main():
    parser = argparse.ArgumentParser(description="Run LLM pipeline to generate notes from extracted text.")
    parser.add_argument("--input", default="data/extracted_text", help="Directory with extracted text JSON files")
    parser.add_argument("--output", default="data/generated_notes", help="Output directory for Markdown notes")
    parser.add_argument("--max-papers", type=int, help="Limit number of papers processed (for testing)")
    args = parser.parse_args()

    process_corpus(Path(args.input), Path(args.output), args.max_papers)

if __name__ == "__main__":
    main()
