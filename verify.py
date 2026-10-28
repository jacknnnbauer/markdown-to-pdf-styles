#!/usr/bin/env python3
"""Verify generated PDFs against SPEC.md section 5.

Requires PyMuPDF (fitz), which is NOT in requirements.txt because
it is only needed for verification, not for building:
    pip install pymupdf

Usage: python verify.py [--output-dir output]

Checks, per style: file exists, page count matches SPEC.md,
and #001-#120 all appear in extracted text. Exits non-zero
on any failure, and prints exactly which check failed.
"""
import argparse
import sys
from pathlib import Path

EXPECTED = {
    "formal": 71,
    "muse": 90,
    "grid": 62,
    "playbook": 66,
    "script": 82,
    "editorial": 77,
    "night": 75,
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--output-dir", default=str(Path(__file__).resolve().parent / "output"))
    args = ap.parse_args()
    try:
        import fitz
    except ImportError:
        print("PyMuPDF (fitz) is required for verification: pip install pymupdf")
        return 2
    out_dir = Path(args.output_dir)
    failures = []
    for name, pages in EXPECTED.items():
        path = out_dir / f"{name}.pdf"
        if not path.exists():
            failures.append(f"{name}: missing {path}")
            continue
        doc = fitz.open(path)
        if len(doc) != pages:
            failures.append(f"{name}: pages {len(doc)} != expected {pages}")
        text = "".join(p.get_text() for p in doc)
        missing = [f"#{i:03d}" for i in range(1, 121) if f"#{i:03d}" not in text]
        if missing:
            failures.append(f"{name}: missing chunks {missing}")
        else:
            print(f"{name}: OK ({len(doc)} pages, #001-#120 present)")
    if failures:
        print("\nFAILURES:")
        for f in failures:
            print(" -", f)
        return 1
    print("\nAll checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
