"""
link_agent.py — LLM agent that classifies semantic links between a target note and candidate notes.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from src.agents.metadata_agent import call_llm


PROMPT_PATH = Path(__file__).parent.parent.parent / "prompts" / "link_agent.md"

def load_prompt(target_note: dict, candidate_notes: list[dict]) -> str:
    if PROMPT_PATH.exists():
        template = PROMPT_PATH.read_text(encoding="utf-8")
    else:
        template = "Fallback prompt text..."
        
    prompt = template.replace("{target_title}", target_note.get("title", ""))
    
    # We want to pass the frontmatter and a brief summary of the target note
    fm_str = json.dumps(target_note.get("frontmatter", {}), indent=2)
    prompt = prompt.replace("{target_frontmatter}", fm_str)
    prompt = prompt.replace("{target_summary}", target_note.get("summary", "")[:2000])
    
    # Format candidates
    cands_formatted = []
    for c in candidate_notes:
        cands_formatted.append({
            "title": c.get("title"),
            "frontmatter": c.get("frontmatter"),
            "summary": c.get("summary", "")[:500]
        })
        
    prompt = prompt.replace("{n_candidates}", str(len(candidate_notes)))
    prompt = prompt.replace("{candidates_json}", json.dumps(cands_formatted, indent=2))

    return prompt

def extract_json_array(raw: str) -> list[dict]:
    import re
    cleaned = re.sub(r"```(?:json)?\s*", "", raw).strip().rstrip("`")
    try:
        data = json.loads(cleaned)
        if isinstance(data, dict):
            return [data]
        return data
    except json.JSONDecodeError as e:
        raise ValueError(f"LLM did not return valid JSON array.\nRaw output:\n{raw}\nError: {e}")

def generate_links(target_note: dict, candidate_notes: list[dict]) -> list[dict]:
    """
    Generate typed links between a target note and a list of candidates.
    
    Args:
        target_note: Dict containing title, frontmatter, and summary.
        candidate_notes: List of dicts, each with title, frontmatter, and summary.
        
    Returns:
        List of link dictionaries.
    """
    if not candidate_notes:
        return []
        
    prompt = load_prompt(target_note, candidate_notes)
    raw_output = call_llm(prompt)
    links = extract_json_array(raw_output)
    
    # Filter by confidence
    return [l for l in links if l.get("confidence", 0.0) >= 0.6]

