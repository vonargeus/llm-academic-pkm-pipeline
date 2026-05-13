"""
note_agent.py — LLM agent that generates an Obsidian Markdown note from a paper's text and metadata.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from src.agents.metadata_agent import call_llm


PROMPT_PATH = Path(__file__).parent.parent.parent / "prompts" / "paper_note_agent.md"

INLINE_PROMPT = """\
Convert the extracted text and metadata of this academic paper into an Obsidian-style Markdown note.

Paper metadata (JSON):
{metadata_json}

Paper text (first 12000 characters):
{text}
"""

def load_prompt(text: str, metadata: dict) -> str:
    if PROMPT_PATH.exists():
        template = PROMPT_PATH.read_text(encoding="utf-8")
    else:
        template = INLINE_PROMPT
        
    # Format the prompt using simple string replacement instead of .format() 
    # to avoid KeyError on \{ and \} that might be inside the prompt instructions.
    prompt = template.replace("{metadata_json}", json.dumps(metadata, indent=2))
    prompt = prompt.replace("{text}", text[:12000])
    
    # Optional placeholders in the prompt if we want to pre-fill the YAML
    # from the metadata we already extracted.
    prompt = prompt.replace("{title}", metadata.get("title") or "")
    prompt = prompt.replace("{title_short}", metadata.get("aliases", [""])[0] if metadata.get("aliases") else "")
    prompt = prompt.replace("{method_names}", ", ".join(metadata.get("method") or []))
    prompt = prompt.replace("{authors}", ", ".join(f'"{a}"' for a in metadata.get("authors") or []))
    prompt = prompt.replace("{year}", str(metadata.get("year") or ""))
    prompt = prompt.replace("{venue}", metadata.get("venue") or "")
    prompt = prompt.replace("{doi_or_arxiv}", metadata.get("doi_or_arxiv") or "")
    prompt = prompt.replace("{topics}", ", ".join(f'"{t}"' for t in metadata.get("topics") or []))
    prompt = prompt.replace("{concepts}", ", ".join(f'"{c}"' for c in metadata.get("concepts") or []))
    prompt = prompt.replace("{methods}", ", ".join(f'"{m}"' for m in metadata.get("method") or []))
    prompt = prompt.replace("{datasets}", ", ".join(f'"{d}"' for d in metadata.get("datasets") or []))
    prompt = prompt.replace("{metrics}", ", ".join(f'"{m}"' for m in metadata.get("evaluation_metrics") or []))

    return prompt

def generate_note(text: str, metadata: dict) -> str:
    """
    Generate an Obsidian Markdown note for a paper.
    
    Args:
        text: Plain text of the academic paper.
        metadata: Extracted metadata dict.
        
    Returns:
        String containing the Markdown note with YAML frontmatter.
    """
    prompt = load_prompt(text, metadata)
    raw_output = call_llm(prompt)
    
    # Strip potential markdown fences if the LLM wrapped the whole response
    cleaned = raw_output.strip()
    if cleaned.startswith("```markdown"):
        cleaned = cleaned[11:]
    if cleaned.startswith("```"):
        cleaned = cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
        
    return cleaned.strip()

def generate_note_from_files(text_json_path: Path, metadata_json_path: Path, output_path: Path | None = None) -> str:
    with open(text_json_path, encoding="utf-8") as f:
        text_payload = json.load(f)
        
    with open(metadata_json_path, encoding="utf-8") as f:
        metadata = json.load(f)

    text = text_payload["text"]
    note_md = generate_note(text, metadata)

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(note_md)

    return note_md

if __name__ == "__main__":
    import argparse
    # auto-load dotenv
    try:
        from dotenv import load_dotenv
        load_dotenv(Path(__file__).parent.parent.parent / ".env")
    except ImportError:
        pass

    parser = argparse.ArgumentParser(description="Generate a note from extracted text and metadata.")
    parser.add_argument("--text", required=True, help="Path to extracted text JSON file")
    parser.add_argument("--metadata", required=True, help="Path to metadata JSON file")
    parser.add_argument("--output", help="Path to save output Markdown file")
    args = parser.parse_args()

    md = generate_note_from_files(Path(args.text), Path(args.metadata), Path(args.output) if args.output else None)
    print(md[:500] + "\n... [truncated]")
