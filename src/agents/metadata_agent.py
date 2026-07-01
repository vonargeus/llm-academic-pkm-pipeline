"""
metadata_agent.py — LLM agent that extracts structured metadata from academic paper text.

Supported LLMs (set via environment variable LLM_PROVIDER):
  - "gemini"  → Google Gemini 1.5 Flash (default)
  - "openai"  → GPT-4o-mini
  - "anthropic" → Claude 3 Haiku
"""

from __future__ import annotations

import json
import os
import re
import textwrap
from pathlib import Path

# Auto-load .env file so GEMINI_API_KEY etc. are always available
# Works even if python-dotenv is not installed (graceful fallback)
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent.parent / ".env", override=False)
except ImportError:
    pass



# ---------------------------------------------------------------------------
# Prompt (loaded from prompts/metadata_agent.md or inline fallback)
# ---------------------------------------------------------------------------
PROMPT_PATH = Path(__file__).parent.parent.parent / "prompts" / "metadata_agent.md"

INLINE_PROMPT = """\
You are an expert academic librarian. Extract structured metadata from the
following academic paper text. Return ONLY a valid JSON object with these fields:

{
  "title": "...",
  "authors": ["...", "..."],
  "year": 2024,
  "venue": "...",
  "doi_or_arxiv": "...",
  "research_problem": "One sentence.",
  "method": ["..."],
  "datasets": ["..."],
  "evaluation_metrics": ["..."],
  "main_contributions": ["..."],
  "topics": ["..."],
  "concepts": ["..."],
  "keywords": ["..."],
  "limitations": "..."
}

Rules:
- For list fields, include ALL relevant items you can find.
- If a field is unknown, use null (not "unknown").
- Do NOT add any explanation outside the JSON.
- year must be an integer or null.

Paper text (first 8000 characters):
{text}
"""


def load_prompt(text: str) -> str:
    if PROMPT_PATH.exists():
        template = PROMPT_PATH.read_text(encoding="utf-8")
    else:
        template = INLINE_PROMPT
    return template.replace("{text}", text[:8000])


# ---------------------------------------------------------------------------
# LLM backends
# ---------------------------------------------------------------------------

import time
from google.api_core.exceptions import ResourceExhausted

# Model pool for rotating due to daily limit (20 reqs/day/model)
MODEL_POOL = [
    "gemini-flash-latest",
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-3-flash-preview",
    "gemini-2.0-flash-001",
    "gemini-3.5-flash",
    "gemini-3.1-flash-lite",
    "gemini-2.5-flash-lite",
    "gemini-2.0-flash-lite-001",
]
CURRENT_MODEL_INDEX = 0

def _call_gemini(prompt: str, model: str = "gemini-2.5-flash") -> str:
    import google.generativeai as genai
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable is not set.")
    genai.configure(api_key=api_key)
    m = genai.GenerativeModel(model)
    
    max_retries = 5
    for attempt in range(max_retries):
        try:
            response = m.generate_content(
                prompt,
                generation_config={"temperature": 0.0},
            )
            return response.text
        except ResourceExhausted as e:
            err_str = str(e).lower()
            if "perday" in err_str or "daily" in err_str or "limit: 20" in err_str or "limit: 0" in err_str or "requests per day" in err_str:
                # Raise immediately to trigger model rotation in call_llm
                raise e
            if attempt == max_retries - 1:
                raise e
            print(f"\n[Rate Limit] Exceeded. Sleeping 60s before retry (attempt {attempt + 1}/{max_retries})...")
            time.sleep(60)
        except Exception as e:
            err_str = str(e).lower()
            if "perday" in err_str or "daily" in err_str or "limit: 20" in err_str or "limit: 0" in err_str or "requests per day" in err_str:
                raise e
            if "quota" in err_str or "limit" in err_str or "429" in err_str:
                if attempt == max_retries - 1:
                    raise e
                print(f"\n[Quota/Rate Limit Exception] {e}. Sleeping 60s...")
                time.sleep(60)
            else:
                err_str_full = str(e)
                # finish_reason 4 = copyright block — permanent, never retry
                if "finish_reason" in err_str_full and "] is 4" in err_str_full:
                    print(f"\n[Copyright Block] Gemini refused content (finish_reason=4). Skipping this paper.")
                    return ""
                if attempt == max_retries - 1:
                    raise e
                print(f"\n[Transient Error] {e}. Sleeping 10s...")
                time.sleep(10)


def _call_openai(prompt: str, model: str = "gpt-4o-mini") -> str:
    from openai import OpenAI
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    resp = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0,
        max_tokens=2048,
    )
    return resp.choices[0].message.content


def _call_anthropic(prompt: str, model: str = "claude-3-haiku-20240307") -> str:
    import anthropic
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    message = client.messages.create(
        model=model,
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text


def call_llm(prompt: str) -> str:
    global CURRENT_MODEL_INDEX
    provider = os.environ.get("LLM_PROVIDER", "gemini").lower()
    if provider == "gemini":
        while CURRENT_MODEL_INDEX < len(MODEL_POOL):
            model = MODEL_POOL[CURRENT_MODEL_INDEX]
            try:
                return _call_gemini(prompt, model=model)
            except Exception as e:
                err_str = str(e).lower()
                if "perday" in err_str or "daily" in err_str or "limit: 20" in err_str or "limit: 0" in err_str or "requests per day" in err_str:
                    print(f"\n[Quota Rotation] Model '{model}' daily quota exhausted. Rotating to next model...")
                    CURRENT_MODEL_INDEX += 1
                    continue
                raise e
        raise RuntimeError("All models in the Gemini model pool have exhausted their daily quota.")
    elif provider == "openai":
        return _call_openai(prompt)
    elif provider == "anthropic":
        return _call_anthropic(prompt)
    else:
        raise ValueError(f"Unknown LLM_PROVIDER: {provider!r}. Use 'gemini', 'openai', or 'anthropic'.")


# ---------------------------------------------------------------------------
# Metadata extraction
# ---------------------------------------------------------------------------

def extract_json(raw: str) -> dict:
    """Extract JSON from LLM output even if wrapped in markdown code fences."""
    # Strip markdown code fences if present
    cleaned = re.sub(r"```(?:json)?\s*", "", raw).strip().rstrip("`")
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise ValueError(f"LLM did not return valid JSON.\nRaw output:\n{raw}\nError: {e}")


def extract_metadata(text: str) -> dict:
    """
    Extract structured metadata from academic paper text.

    Args:
        text: Plain text of the academic paper.

    Returns:
        Dictionary of structured metadata fields.
    """
    prompt = load_prompt(text)
    raw_output = call_llm(prompt)
    metadata = extract_json(raw_output)
    # Add provenance
    metadata["_extracted_by"] = "metadata_agent"
    metadata["_llm_provider"] = os.environ.get("LLM_PROVIDER", "gemini")
    return metadata


def extract_metadata_from_file(text_json_path: Path, output_path: Path | None = None) -> dict:
    """Load a text JSON file, extract metadata, optionally save."""
    with open(text_json_path, encoding="utf-8") as f:
        payload = json.load(f)

    text = payload["text"]
    metadata = extract_metadata(text)
    metadata["doc_id"] = payload.get("doc_id", text_json_path.stem)

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

    return metadata


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Extract metadata from a paper text JSON file.")
    parser.add_argument("input", help="Path to extracted text JSON file")
    parser.add_argument("--output", help="Path to save metadata JSON (optional)")
    args = parser.parse_args()

    meta = extract_metadata_from_file(
        Path(args.input),
        output_path=Path(args.output) if args.output else None,
    )
    print(json.dumps(meta, indent=2, ensure_ascii=False))
