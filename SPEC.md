# SPEC — input, numbering, and expected output

This file is the contract that makes the output reproducible by
anyone, including another AI agent with no prior context. If you
change the input, change the code, or change the fonts, the
expected outputs below no longer apply — say so, don't silently
ship a different book.

## 1. Environment (must match, or pagination will drift)

- Python 3.12, packages exactly as in `requirements.txt`
  (WeasyPrint 70.0 is the renderer; Chrome headless is NOT used).
- Fonts, all installed system-wide before building:
  - Noto Sans CJK SC, Noto Serif CJK SC
  - Liberation Sans, Liberation Serif, Liberation Mono
  - DejaVu Sans (fallback for symbols such as ★)
- On Debian/Ubuntu:
  ```bash
  sudo apt install fonts-noto-cjk fonts-liberation fonts-dejavu
  ```
- Paper: A4, always. No other paper size is supported by the styles.

If a font is missing, WeasyPrint substitutes silently and the
book will look different and paginate differently. That is the
most common cause of "same Markdown, different PDF".

## 2. Input format (exact)

A UTF-8 Markdown file, in this order, with no other structure
assumed:

```markdown
## 第 1 轮总览
- 主题：<theme 1>、<theme 2>、……
- 场景：<scene 1>、<scene 2>、……
- 本轮 10 个最值得背的 chunk：<chunk A>; <chunk B>; ……（10 items, separated by ；or ;）

## 第 1 轮 · 主题 1：<theme name>

### 1. <chunk title>
- 英文 chunk：<title, usually identical to the heading title>
- 中文意思：<Chinese meaning>
- 正式度：<casual | neutral | professional | formal, or a / combination>
- 美式例句：(1) <sentence 1> (2) [<scene>] <sentence 2>
- 可替换说法：<label>：<text> / <label>：<text> / ……
- 美式发音与流利度提示：<text>
- 使用提醒：<text>
- 迷你练习：<text>

## 第 1 轮 · 7 天复习 / 练习计划
- Day 1：……
（7 bullets, content is reproduced as-is)
```

Repeat for rounds 2 and 3, each with 5 themes × 8 chunks.

Rules the code actually implements (do not guess others):

- Chunks are numbered #001, #002, … in **file order**, ignoring
  the numbers in the `###` headings (those are stripped).
- A chunk's theme is the most recent `## …主题…` heading above it.
- A chunk's round is the most recent `## …总览` heading above it.
- Core chunks (★ or the style's equivalent) are found by matching
  each item in a round's “本轮 10 个最值得背” list against chunk
  titles, by normalised substring match (lower-cased, trailing
  punctuation stripped). Unmatched items are printed to stdout
  as `! core not matched:` and must be investigated, not ignored.
- Bullets before the first `##` heading are dropped (they are
  file-head metadata, not book content).
- Contents page numbers are real page numbers, computed by
  WeasyPrint with `target-counter`, not hand-written.

## 3. Current shape (asserted by every style script)

- 3 rounds, 15 themes, 120 chunks, 30 core chunks (10 per round).
- Every style script asserts these counts and exits non-zero
  otherwise. That is intentional: a wrong count means the input
  changed, and the book must not be shipped as if it were the same.

## 4. How to build (the only supported commands)

```bash
python -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python build_all.py                    # all 7 styles -> output/
.venv/bin/python build_all.py --style night     # one style
.venv/bin/python styles/night.py my.md -o out.pdf
```

No other tool, browser, or local file is required. In particular,
nothing in this repo reads `~/workspace`, a personal venv, or any
Muse / agent-specific path. All default paths are relative to the
repository root via `Path(__file__)`.

## 5. Expected output for the example input

Input: `examples/American_English_Speaking_Chunks.md`
(all 7 styles, same input, same numbering):

| Style | Output | Pages | Check |
|---|---|---|---|
| formal | `output/formal.pdf` | 71 | #001–#120 present |
| muse | `output/muse.pdf` | 90 | #001–#120 present |
| grid | `output/grid.pdf` | 62 | #001–#120 present |
| playbook | `output/playbook.pdf` | 66 | #001–#120 present |
| script | `output/script.pdf` | 82 | #001–#120 present |
| editorial | `output/editorial.pdf` | 77 | #001–#120 present |
| night | `output/night.pdf` | 75 | #001–#120 present |

Run the check after building:

```bash
.venv/bin/python verify.py            # needs PyMuPDF; see verify.py header
# or, without PyMuPDF: open each PDF and confirm the page count above
# and that the last chunk is #120.
```

## 6. What "same effect" means — and what it does not

- **Same means:** same visual layout, same page counts as above,
  same chunk order and numbering, same contents page numbers,
  same core-30 marking.
- **Same does NOT mean byte-identical files.** PDF metadata
  (creation date, producer strings) can differ between runs and
  machines. Do not compare files by hash; compare by the checks
  in section 5 and by looking at the cover, one theme page, and
  one appendix page.
- If your page counts differ by even one page, stop: something
  in section 1 (usually a font) or section 2 (input shape) changed.
  Do not "fix" it by editing page numbers by hand.
