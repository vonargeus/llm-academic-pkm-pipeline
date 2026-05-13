"""
orchestrator.py — Pipeline to orchestrate metadata, note, and link generation for a batch of papers.
"""

from __future__ import annotations

import json
from pathlib import Path

from src.agents.metadata_agent import extract_metadata
from src.agents.note_agent import generate_note
from src.agents.link_agent import generate_links

def process_corpus(extracted_text_dir: Path, output_dir: Path, max_papers: int | None = None):
    output_dir.mkdir(parents=True, exist_ok=True)
    
    text_files = sorted(extracted_text_dir.glob("*.json"))
    if max_papers:
        text_files = text_files[:max_papers]
        
    print(f"Processing {len(text_files)} papers...")
    
    notes_data = []
    
    # Step 1: Metadata & Note Generation
    for idx, tf in enumerate(text_files, 1):
        print(f"[{idx}/{len(text_files)}] Processing {tf.stem}...")
        
        with open(tf, encoding="utf-8") as f:
            payload = json.load(f)
            
        text = payload["text"]
        doc_id = payload.get("doc_id", tf.stem)
        
        # 1a. Metadata
        print("  -> Extracting metadata...")
        metadata = extract_metadata(text)
        metadata["doc_id"] = doc_id
        
        # 1b. Note Generation
        print("  -> Generating note...")
        note_md = generate_note(text, metadata)
        
        notes_data.append({
            "doc_id": doc_id,
            "title": metadata.get("title", doc_id),
            "frontmatter": metadata,
            "summary": "Extracted summary. " + metadata.get("research_problem", ""),
            "md_content": note_md
        })
        
        # Save intermediate note without links
        out_path = output_dir / f"{doc_id}.md"
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(note_md)
            
    # Step 2: Link Generation (requires all notes to be available as candidates)
    print("\nStarting Link Generation...")
    for idx, target in enumerate(notes_data, 1):
        print(f"[{idx}/{len(notes_data)}] Linking {target['doc_id']}...")
        candidates = [n for n in notes_data if n["doc_id"] != target["doc_id"]]
        
        try:
            links = generate_links(target, candidates)
            print(f"  -> Found {len(links)} links")
        except Exception as e:
            print(f"  -> Link generation failed: {e}")
            links = []
            
        # Append links to the markdown file
        if links:
            links_md = "\n\n## Generated Links\n"
            for link in links:
                links_md += f"- **[[{link.get('linked_to')}]]** ({link.get('link_type')}): {link.get('justification')}\n"
                
            out_path = output_dir / f"{target['doc_id']}.md"
            with open(out_path, "a", encoding="utf-8") as f:
                f.write(links_md)
                
    print("\nPipeline complete!")
