"""
extract_pdfs.py — Extract plain text from PDFs using PyMuPDF (fitz).

Usage:
    python scripts/extract_pdfs.py --input data/raw_pdfs/ --output data/extracted_text/
"""

import argparse
import json
import re
from pathlib import Path

import fitz  # PyMuPDF


def extract_text(pdf_path: Path) -> str:
    doc = fitz.open(pdf_path)
    pages = []
    for page in doc:
        text = page.get_text("text")
        if text and text.strip():
            pages.append(text.strip())
    return "\n\n".join(pages)


def clean_text(text: str) -> str:
    """Basic cleaning: remove excessive whitespace, fix hyphenation."""
    text = re.sub(r"-\n(\w)", r"\1", text)        # dehyphenate
    text = re.sub(r"\n{3,}", "\n\n", text)         # collapse blank lines
    text = re.sub(r"[ \t]+", " ", text)            # normalise spaces
    return text.strip()


def process_all(input_dir: Path, output_dir: Path):
    output_dir.mkdir(parents=True, exist_ok=True)
    pdf_files = sorted(input_dir.glob("*.pdf"))

    if not pdf_files:
        print(f"No PDFs found in {input_dir}")
        return

    results = {}
    for pdf in pdf_files:
        print(f"Extracting: {pdf.name}")
        try:
            raw = extract_text(pdf)
            cleaned = clean_text(raw)
            out_path = output_dir / f"{pdf.stem}.json"
            payload = {
                "doc_id": pdf.stem,
                "source_pdf": str(pdf),
                "char_count": len(cleaned),
                "text": cleaned,
            }
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2, ensure_ascii=False)
            results[pdf.stem] = {"status": "ok", "chars": len(cleaned), "path": str(out_path)}
            print(f"  [OK] {len(cleaned):,} chars -> {out_path.name}")
        except Exception as e:
            print(f"  [Error] {e}")
            results[pdf.stem] = {"status": "error", "error": str(e)}

    summary_path = output_dir / "_extraction_summary.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    n_ok = sum(1 for v in results.values() if v["status"] == "ok")
    print(f"\nExtracted {n_ok}/{len(pdf_files)} PDFs. Summary -> {summary_path}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="data/raw_pdfs", help="Directory with PDF files")
    parser.add_argument("--output", default="data/extracted_text", help="Output directory for JSON text files")
    args = parser.parse_args()
    process_all(Path(args.input), Path(args.output))


if __name__ == "__main__":
    main()
