# AGENTS.md — for another AI agent reproducing this project

You received a link to this repo and a Markdown file, and you are
asked to produce the same PDFs. Do exactly this, in this order.
Do not redesign, do not "improve" a style, do not substitute
another renderer.

## Reproduce in 5 steps

1. Clone this repo. Do not copy files from anywhere else.
2. Read `SPEC.md` first, especially section 1 (fonts) and
   section 2 (input format). Install the fonts before building.
   A missing CJK font is the usual reason for a different result.
3. Create a fresh venv and install the pinned requirements:
   ```bash
   python -m venv .venv && .venv/bin/pip install -r requirements.txt
   ```
4. Build with the repo's own commands only:
   ```bash
   .venv/bin/python build_all.py
   ```
   Do not use Chrome headless, do not use a different WeasyPrint
   version, do not hand-edit a PDF afterwards.
5. Verify before delivering anything:
   ```bash
   .venv/bin/python verify.py
   ```
   All 7 page counts in `SPEC.md` section 5 must match, and
   #001–#120 must be present in every PDF. If any check fails,
   report the failure and what you changed — do not deliver a
   PDF that fails verification as if it were the same book.

## Rules

- Input is the Markdown file the user gave you, unchanged.
  If its shape differs from `SPEC.md` section 2/3, say so and
  stop; do not silently drop, reorder, or renumber chunks.
- Output goes to `output/` (gitignored). Do not commit generated
  PDFs to the repo; the gallery covers in `gallery/` are the
  showcase, not the deliverable.
- "Same effect" means same layout, same page counts, same
  numbering and contents page numbers (see `SPEC.md` section 6).
  It does not mean byte-identical files.
- If you are asked for a different style, a different paper size,
  or a different input, that is a new task, not a reproduction.
  Say so explicitly.
