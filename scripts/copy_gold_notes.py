"""
scripts/copy_gold_notes.py

Description:
    Copies Emile's original 22 paper notes from `data/emile_vault` into 
    `data/generated_notes` using their arXiv IDs as filenames.
    
    This ensures that Pipeline B & C use Emile's handwritten notes as the 
    ground-truth representations, and our note generation agent will automatically 
    skip them and only process the 18 external RAG papers.
"""

import json
import shutil
from pathlib import Path

def main():
    arxiv_ids_path = Path("data/gold_labels/vault_arxiv_ids.json")
    vault_dir = Path("data/emile_vault")
    target_dir = Path("data/generated_notes")
    
    target_dir.mkdir(parents=True, exist_ok=True)
    
    if not arxiv_ids_path.exists():
        print(f"Error: {arxiv_ids_path} does not exist. Run scripts/parse_emile_vault.py first.")
        return
        
    with open(arxiv_ids_path, encoding="utf-8") as f:
        arxiv_map = json.load(f)
        
    print(f"Loaded mapping of {len(arxiv_map)} gold paper notes from Emile's vault.")
    
    copied_count = 0
    for doc_id, arxiv_id in arxiv_map.items():
        if not arxiv_id:
            continue
            
        # Standardize arXiv ID for filename (e.g., replace slash if needed)
        safe_arxiv_id = arxiv_id.replace("/", "_")
        target_filename = f"{safe_arxiv_id}.md"
        target_path = target_dir / target_filename
        
        # Locate the source note in Emile's vault (filename matches doc_id)
        source_filename = f"{doc_id}.md"
        source_path = vault_dir / source_filename
        
        # Case-insensitive check if it doesn't match directly
        if not source_path.exists():
            for f in vault_dir.glob("*.md"):
                if f.stem.lower() == doc_id.lower():
                    source_path = f
                    break
                    
        if source_path.exists():
            shutil.copy2(source_path, target_path)
            copied_count += 1
            print(f"[Copied] '{source_path.name}' -> '{target_filename}'")
        else:
            print(f"[Warning] Could not find note in vault for: '{doc_id}'")
            
    print(f"\nSuccessfully copied {copied_count}/{len(arxiv_map)} gold notes to {target_dir}")

if __name__ == "__main__":
    main()
