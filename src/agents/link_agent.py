"""
link_agent.py — LLM agent that classifies semantic links between a target note and candidate notes.

Extended with Citation Link Agent capability (RQ3):
  extract_citation_links() reads the bibliography section from extracted PDF text,
  extracts explicit references, and resolves local corpus matches.
"""

from __future__ import annotations

import json
import os
import re
import unicodedata
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
    Generate typed semantic links between a target note and a list of candidates.
    Used by the ingestion pipeline for RQ1/RQ2. Not modified.
    
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


# ---------------------------------------------------------------------------
# Citation Link Agent (RQ3)
# Reads the bibliography section from extracted PDF text and extracts explicit
# bibliographic references. Independent of generate_links(); does not modify
# existing notes or the frozen RQ1/RQ2 retrieval graph.
# ---------------------------------------------------------------------------

_REF_SECTION_RE = re.compile(
    r"(?:^|\n)\s*(?:References?|Bibliography|Works\s+Cited|Literature\s+Cited)\s*\n",
    re.IGNORECASE,
)
_MAX_REF_CHARS  = 12_000
_MAX_FULL_CHARS = 20_000

_CITATION_PROMPT = """\
You are an expert academic librarian. The text below is the References or Bibliography \
section of an academic paper.

Extract EVERY reference listed. Do not skip any. Do not limit yourself to a fixed number.

Return ONLY a valid JSON object in this exact format:
{{
  "references": [
    {{
      "title": "Full paper title as written",
      "authors": ["Last, First", "Last2, First2"],
      "year": 2020,
      "doi": "10.xxxx/xxxx or null",
      "arxiv_id": "YYMM.NNNNN or null",
      "s2_paper_id": "40-char hex ID if visible in text or null",
      "venue": "Conference or journal name or null"
    }}
  ]
}}

Rules:
- Include every reference you can detect. Variable count is expected and correct.
- Use null for any field not present in the text.
- Return ONLY the JSON object. No explanation, no markdown outside the JSON.

Reference section text:
{ref_text}
"""


def _detect_ref_section(full_text: str) -> tuple[str, bool]:
    """Return (text_to_send, used_fallback)."""
    match = _REF_SECTION_RE.search(full_text)
    if match:
        section = full_text[match.start():].strip()
        return section[:_MAX_REF_CHARS], False
    return full_text[-_MAX_FULL_CHARS:], True


def _parse_citation_response(raw: str) -> list[dict]:
    """Robustly extract the JSON list from LLM response."""
    raw = re.sub(r"^```(?:json)?\s*", "", raw.strip(), flags=re.IGNORECASE)
    raw = re.sub(r"\s*```$", "", raw.strip())
    try:
        obj = json.loads(raw)
        return obj.get("references", []) if isinstance(obj, dict) else []
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", raw, re.DOTALL)
        if m:
            try:
                obj = json.loads(m.group())
                return obj.get("references", []) if isinstance(obj, dict) else []
            except Exception:
                pass
    return []


def _norm_title(title: str | None) -> str | None:
    if not title:
        return None
    t = title.lower()
    t = unicodedata.normalize("NFKD", t)
    t = re.sub(r"[^\w\s]", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def extract_citation_links(
    full_text: str,
    corpus_index: dict[str, str] | None = None,
) -> dict:
    """
    Citation Link Agent — extracts explicit bibliographic references from the
    References/Bibliography section of a paper's extracted text.

    Args:
        full_text:     The full extracted text of the source PDF.
        corpus_index:  Optional dict mapping normalized_title -> arxiv_id for
                       the 40-paper corpus, used to resolve local wiki-links.

    Returns:
        {
          "references":       list of normalized reference dicts,
          "section_fallback": bool (True if References heading not detected),
          "ref_section_chars": int,
        }
        Each reference dict has: title, authors, year, doi, arxiv_id,
        s2_paper_id, venue, local_arxiv_id (if resolved), local_wikilink (if resolved).
    """
    if not full_text.strip():
        return {
            "status": "missing_text",
            "references": [],
            "section_fallback": False,
            "ref_section_chars": 0,
        }

    ref_text, used_fallback = _detect_ref_section(full_text)
    prompt = _CITATION_PROMPT.format(ref_text=ref_text)

    try:
        raw = call_llm(prompt)
        
        # If Gemini returned empty string because of copyright blocks
        if not raw.strip():
            return {
                "status": "provider_block",
                "references": [],
                "section_fallback": used_fallback,
                "ref_section_chars": len(ref_text),
            }
            
        references = _parse_citation_response(raw)
        
        # Check if JSON parsing failed completely
        # (e.g. LLM returned unparseable text instead of schema)
        if not references and raw.strip():
            # If the response contains markdown or code that failed JSON decoding
            # we classify it as a parse_failure
            status = "parse_failure"
        else:
            status = "success"
            
    except Exception as e:
        err_str = str(e).lower()
        if "finish_reason" in err_str and "4" in err_str:
            status = "provider_block"
        else:
            status = "parse_failure"
        return {
            "status": status,
            "references": [],
            "section_fallback": used_fallback,
            "ref_section_chars": len(ref_text),
            "llm_error": str(e),
        }

    # Resolve to local corpus when corpus_index provided
    if corpus_index:
        for ref in references:
            norm = _norm_title(ref.get("title"))
            local_id = corpus_index.get(norm)
            ref["local_arxiv_id"] = local_id
            ref["local_wikilink"] = f"[[{ref['title']}]]" if local_id else None

    return {
        "status": status,
        "references": references,
        "section_fallback": used_fallback,
        "ref_section_chars": len(ref_text),
    }

