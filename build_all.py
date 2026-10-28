#!/usr/bin/env python3
"""Build one or all speaking-chunks PDF styles.

Usage:
    python build_all.py                 # build all 7 styles into output/
    python build_all.py --style night   # build one style
    python build_all.py --input my.md --output-dir out/

Each style is a standalone script in styles/ (WeasyPrint based).
All styles share the same input format: see examples/
American_English_Speaking_Chunks.md. The current scripts expect
3 rounds, 120 chunks, and a "本轮 10 个最值得背" list per round;
other inputs will fail the built-in assertions. Generalising the
parser to arbitrary chunk counts is a TODO, not a silent fallback.
"""
import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
STYLES = ["formal", "muse", "grid", "playbook", "script", "editorial", "night"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--style", choices=STYLES, help="Build one style only")
    ap.add_argument("--input", default=str(ROOT / "examples" / "American_English_Speaking_Chunks.md"))
    ap.add_argument("--output-dir", default=str(ROOT / "output"))
    ap.add_argument("--python", default=sys.executable, help="Python with WeasyPrint installed")
    args = ap.parse_args()
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    names = [args.style] if args.style else STYLES
    for name in names:
        script = ROOT / "styles" / f"{name}.py"
        out = out_dir / f"{name}.pdf"
        print(f"== {name} -> {out}")
        subprocess.run([args.python, str(script), args.input, "-o", str(out)], check=True)
    print("done.")


if __name__ == "__main__":
    main()
