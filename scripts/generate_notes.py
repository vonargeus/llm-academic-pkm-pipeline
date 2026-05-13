"""
generate_notes.py — CLI wrapper to run the full LLM agent pipeline.

Usage:
    python scripts/generate_notes.py --input data/extracted_text/ --output data/generated_notes/
"""

import argparse
from pathlib import Path

# Auto-load dotenv
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent / ".env")
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
