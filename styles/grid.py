#!/usr/bin/env python3
"""Build Grid Edition (v3) of American English Speaking Chunks.

Designed from scratch, deliberately unlike the two earlier editions:
- v1 (formal): navy band cover, meta table, leader-dot TOC, rectangular cards.
- v2 (Muse workbook): warm cream paper, serif English, orange, rounded
  cards with tick boxes, yellow theme intros, scene index, speaking log.
- v3 (this file): Swiss grid. White paper only, sans only, black rules,
  one accent colour (electric blue), no cards, no cream, no yellow, no
  tick-box workbook. Each chunk is a grid row: a number column on the
  left, the utterance on the right. English and examples come first;
  the Chinese meaning is an annotation after them, not the headline.
  Appendices are a plain alphabetical index and a master checklist,
  not a scene index or a handwritten log.

Engine: WeasyPrint 70 in ~/workspace/.venv-md2pdf.
"""
import argparse
import html
import re
from pathlib import Path

_ap = argparse.ArgumentParser(description='Build a speaking-chunks PDF in this style.')
_ap.add_argument('input', nargs='?', default=str(Path(__file__).resolve().parent.parent / 'examples' / 'American_English_Speaking_Chunks.md'), help='Input Markdown file')
_ap.add_argument('-o', '--output', default=str(Path(__file__).resolve().parent.parent / 'output' / 'grid.pdf'), help='Output PDF file')
_args = _ap.parse_args()
SRC = Path(_args.input)
OUT = Path(_args.output)
OUT.parent.mkdir(parents=True, exist_ok=True)

text = SRC.read_text(encoding="utf-8")
lines = text.splitlines()

blocks = []
cur_h2 = ""
cur_chunk = None
cur_bullets = None
round_no = 0


def flush_chunk():
    global cur_chunk
    if cur_chunk is not None:
        blocks.append(cur_chunk)
        cur_chunk = None


def flush_bullets():
    global cur_bullets
    if cur_bullets is not None:
        blocks.append({"type": "bullets", "items": cur_bullets, "h2": cur_h2})
        cur_bullets = None


for line in lines:
    if line.startswith("## "):
        flush_chunk()
        flush_bullets()
        cur_h2 = line[3:].strip()
        if "总览" in cur_h2:
            round_no += 1
        blocks.append({"type": "h2", "text": cur_h2, "round": round_no})
    elif line.startswith("### "):
        flush_chunk()
        flush_bullets()
        cur_chunk = {
            "type": "chunk",
            "title": re.sub(r"^\d+\.\s*", "", line[4:].strip()),
            "fields": {},
            "h2": cur_h2,
            "round": round_no,
        }
    elif line.startswith("- ") and cur_chunk is not None:
        body = line[2:].strip()
        if "：" in body:
            label, val = body.split("：", 1)
        elif ":" in body:
            label, val = body.split(":", 1)
        else:
            label, val = body, ""
        cur_chunk["fields"][label.strip()] = val.strip()
    elif line.startswith("- ") and cur_chunk is None:
        if cur_bullets is None:
            cur_bullets = []
        cur_bullets.append(line[2:].strip())
flush_chunk()
flush_bullets()

chunks = [b for b in blocks if b["type"] == "chunk"]
for i, c in enumerate(chunks, 1):
    c["num"] = i


def norm(s):
    s = s.lower().strip()
    s = re.sub(r"[.…。]+$", "", s)
    s = re.sub(r"\s+", " ", s)
    return s


core_lists = []
for b in blocks:
    if b["type"] == "bullets":
        for item in b["items"]:
            if item.startswith("本轮 10 个最值得背"):
                _, val = item.split("：", 1) if "：" in item else item.split(":", 1)
                names = [x.strip() for x in re.split(r"[；;]", val) if x.strip()]
                matched = []
                for name in names:
                    nn = norm(name)
                    hit = None
                    for c in chunks:
                        ct = norm(c["title"])
                        if nn == ct or nn in ct or ct in nn:
                            hit = c
                            break
                    if hit is not None:
                        hit["core"] = True
                        matched.append(hit)
                    else:
                        print(f"! core not matched: {name}")
                core_lists.append(matched)

print(f"chunks: {len(chunks)}, core: {sum(len(x) for x in core_lists)}")
assert len(chunks) == 120
assert len(core_lists) == 3 and all(len(x) == 10 for x in core_lists)

sec = 0
for b in blocks:
    if b["type"] == "h2":
        sec += 1
        b["hid"] = f"sec-{sec}"

themes = [b for b in blocks if b["type"] == "h2" and "主题" in b["text"]]
for ti, b in enumerate(themes, 1):
    b["tcode"] = f"T{ti:02d}"
theme_chunks = {}
for c in chunks:
    theme_chunks.setdefault(c["h2"], []).append(c)
theme_by_text = {b["text"]: b for b in themes}


def esc(s):
    return html.escape(s or "")


def render_examples(val):
    m = re.match(r"\(1\)\s*(.*?)\s*\(2\)\s*(.*)$", val or "", flags=re.S)
    parts = [m.group(1).strip(), m.group(2).strip()] if m else ([val.strip()] if val else [])
    out = []
    for p in parts:
        mm = re.match(r"\[([^\]]+)\]\s*(.*)$", p, flags=re.S)
        if mm:
            out.append(f'<p class="ex"><span class="scene">[{esc(mm.group(1))}]</span> {esc(mm.group(2))}</p>')
        else:
            out.append(f'<p class="ex">{esc(p)}</p>')
    return "".join(out)


def render_alts_inline(val):
    segs = [s.strip() for s in (val or "").split(" / ") if s.strip()]
    return " / ".join(esc(s) for s in segs)


def render_row(c):
    f = c["fields"]
    core = c.get("core", False)
    core_mark = '<div class="coremark">■ CORE</div>' if core else ""
    form_html = esc(f.get("正式度", "")).replace(" / ", "<br>")
    return f"""<section class="row">
<div class="numcol"><div class="num">{c["num"]:03d}</div><div class="form">{form_html}</div>{core_mark}</div>
<div class="maincol">
<div class="ctitle">{esc(c["title"])}</div>
{render_examples(f.get("美式例句", ""))}
<div class="meaning">中文：{esc(f.get("中文意思", ""))}</div>
<div class="also"><b>ALSO</b> — {render_alts_inline(f.get("可替换说法", ""))}</div>
<div class="meta">PRON — {esc(f.get("美式发音与流利度提示", ""))}<br>NOTE — {esc(f.get("使用提醒", ""))}</div>
<div class="try">→ TRY — {esc(f.get("迷你练习", ""))}</div>
</div>
<div class="clear"></div>
</section>"""


body_parts = []
for b in blocks:
    if b["type"] == "h2":
        cls = "roundhead" if "总览" in b["text"] else "chapter"
        body_parts.append(f'<h2 class="{cls}" id="{b["hid"]}">{esc(b["text"])}</h2>')
        if "主题" in b["text"]:
            tcs = theme_chunks.get(b["text"], [])
            rng = f"#{tcs[0]['num']:03d}–#{tcs[-1]['num']:03d}" if tcs else ""
            tcode = theme_by_text[b["text"]]["tcode"]
            running = " · ".join(c["title"] for c in tcs)
            body_parts.append(
                f'<div class="themehead"><span class="tcode">{tcode}</span> '
                f'<span class="trange">{rng}</span><div class="running">{esc(running)}</div></div>')
    elif b["type"] == "chunk":
        body_parts.append(render_row(b))
    elif b["type"] == "bullets":
        items = "".join(f"<li>{esc(x)}</li>" for x in b["items"])
        body_parts.append(f"<ul class='bodylist'>{items}</ul>")
body_html = "\n".join(body_parts)

# contents: themes only
content_rows = ""
cur_round = 0
for b in themes:
    if b["round"] != cur_round:
        cur_round = b["round"]
        content_rows += f'<tr class="roundrow"><td colspan="3">ROUND {cur_round}</td></tr>'
    tcs = theme_chunks.get(b["text"], [])
    rng = f"#{tcs[0]['num']:03d}–#{tcs[-1]['num']:03d}" if tcs else ""
    content_rows += (f'<tr><td class="ctheme"><a href="#{b["hid"]}">{esc(b["text"])}</a></td>'
                     f'<td class="crange">{rng}</td>'
                     f'<td class="cpage"><a href="#{b["hid"]}"></a></td></tr>')

# core 30 as a plain two-column list (no cards, bottom rules only)
core_cells = []
for lst in core_lists:
    for c in lst:
        core_cells.append(
            f"<td><span class='mcnum'>#{c['num']:03d}</span> <b>{esc(c['title'])}</b> — {esc(c['fields'].get('中文意思', ''))}</td>")
core_grid = ""
for i in range(0, len(core_cells), 2):
    pair = core_cells[i:i + 2]
    if len(pair) == 1:
        pair.append("<td></td>")
    core_grid += "<tr>" + "".join(pair) + "</tr>"

# alphabetical index: group by first letter of the English title
def sort_key(c):
    return c["title"].lower()


alpha = {}
for c in sorted(chunks, key=sort_key):
    letter = sort_key(c)[0].upper()
    alpha.setdefault(letter, []).append(c)
alpha_blocks = ""
for letter in sorted(alpha):
    items = " · ".join(f"{c['title']} #{c['num']:03d}" for c in alpha[letter])
    alpha_blocks += f'<div class="alphablock"><span class="aletter">{letter}</span><p>{esc(items)}</p></div>'

check_rows = "".join(
    f"<tr><td class='cn'>#{c['num']:03d}</td><td>{esc(c['title'])}</td><td><span class='box'></span></td></tr>"
    for c in chunks)

CSS = r"""
@page {
  size: A4; margin: 15mm 14mm 15mm 14mm; background: #fff;
  @top-left { content: "SPEAKING CHUNKS"; font-family: "Liberation Sans", "Noto Sans CJK SC", sans-serif; font-size: 7.5pt; letter-spacing: 1pt; color: #111; }
  @top-right { content: string(chapter); font-family: "Liberation Sans", "Noto Sans CJK SC", sans-serif; font-size: 7.5pt; color: #6B7280; }
  @bottom-left { content: "GRID EDITION · B2–C1 · AMERICAN ENGLISH"; font-family: "Liberation Sans", "Noto Sans CJK SC", sans-serif; font-size: 7.5pt; color: #6B7280; }
  @bottom-right { content: counter(page); font-family: "Liberation Sans", sans-serif; font-size: 9pt; font-weight: bold; color: #2337FF; }
}
@page cover { margin: 0; background: #fff; @top-left { content: none; } @top-right { content: none; } @bottom-left { content: none; } @bottom-right { content: none; } }
@page contents { @top-right { content: "INDEX"; } }
html { font-family: "Liberation Sans", "Noto Sans CJK SC", sans-serif; font-size: 9.5pt; line-height: 1.55; color: #111; }
body { margin: 0; background: #fff; }
.cover { page: cover; height: 297mm; box-sizing: border-box; padding: 16mm 14mm; }
.cover .topline { border-top: 3pt solid #111; padding-top: 3mm; font-size: 8pt; letter-spacing: 1.5pt; display: flex; justify-content: space-between; }
.cover h1 { font-size: 52pt; line-height: 0.95; letter-spacing: -1pt; margin: 14mm 0 0 0; text-transform: uppercase; }
.cover h1 .dot { color: #2337FF; }
.cover .square { width: 12mm; height: 12mm; background: #2337FF; margin: 8mm 0; }
.cover .cn { font-size: 16pt; font-weight: bold; }
.cover .sub { font-size: 10.5pt; color: #374151; line-height: 1.6; max-width: 150mm; }
.cover table.meta { width: 100%; border-collapse: collapse; margin-top: 12mm; }
.cover table.meta td { border-top: 1pt solid #111; padding: 3mm 2mm 3mm 0; vertical-align: top; font-size: 9pt; }
.cover table.meta td.lab { color: #6B7280; width: 28mm; text-transform: uppercase; letter-spacing: 0.5pt; font-size: 8pt; }
.cover .bignums { margin-top: 12mm; font-size: 20pt; font-weight: bold; letter-spacing: -0.5pt; }
.cover .bignums span { color: #2337FF; }
.cover .foot { margin-top: 10mm; font-size: 8.5pt; color: #6B7280; line-height: 1.6; border-top: 0.5pt solid #D1D5DB; padding-top: 3mm; }
.front { break-before: page; break-after: page; }
.front h2 { bookmark-level: 2; string-set: none; break-before: auto; font-size: 22pt; letter-spacing: -0.5pt; margin-top: 0; text-transform: uppercase; }
.front h2.appendix { string-set: chapter content(); }
.spec { width: 100%; border-collapse: collapse; font-size: 9.5pt; margin: 4mm 0; }
.spec td { border-top: 0.5pt solid #D1D5DB; padding: 2.5mm 2mm 2.5mm 0; vertical-align: top; }
.spec td.lab { color: #6B7280; width: 32mm; text-transform: uppercase; letter-spacing: 0.5pt; font-size: 8pt; }
.contents { page: contents; break-after: page; }
.contents h2 { bookmark-level: 2; string-set: none; font-size: 22pt; text-transform: uppercase; letter-spacing: -0.5pt; }
table.ctable { width: 100%; border-collapse: collapse; font-size: 9.5pt; }
table.ctable td { border-bottom: 0.5pt solid #E5E7EB; padding: 2.4mm 1mm; vertical-align: top; }
table.ctable tr.roundrow td { background: #111; color: #fff; font-weight: bold; letter-spacing: 1pt; font-size: 8.5pt; border-bottom: none; }
table.ctable td.ctheme a { text-decoration: none; color: #111; font-weight: bold; }
table.ctable td.crange { color: #111; white-space: nowrap; text-align: right; }
table.ctable td.cpage { width: 12mm; text-align: right; }
table.ctable td.cpage a { text-decoration: none; color: #2337FF; font-weight: bold; }
table.ctable td.cpage a::after { content: target-counter(attr(href), page); }
table.coregrid { width: 100%; border-collapse: collapse; font-size: 8.8pt; line-height: 1.5; }
table.coregrid td { width: 50%; border-bottom: 0.5pt solid #E5E7EB; padding: 2.2mm 3mm 2.2mm 0; vertical-align: top; }
table.coregrid td .mcnum { color: #2337FF; font-weight: bold; }
table.coregrid tr { break-inside: avoid; }
h2.chapter { string-set: chapter content(); break-before: page; bookmark-level: 2; font-size: 18pt; letter-spacing: -0.5pt; margin-top: 0; border-bottom: 2pt solid #111; padding-bottom: 2mm; }
h2.roundhead { string-set: chapter content(); break-before: page; bookmark-level: 2; font-size: 24pt; letter-spacing: -0.5pt; margin-top: 0; }
.themehead { border-top: 3pt solid #111; border-bottom: 0.5pt solid #111; padding: 3mm 0; margin: 0 0 4mm 0; }
.tcode { font-size: 20pt; font-weight: bold; color: #2337FF; margin-right: 4mm; }
.trange { font-weight: bold; }
.running { color: #374151; font-size: 8.8pt; margin-top: 1.5mm; line-height: 1.5; }
.row { break-inside: avoid; border-top: 1.5pt solid #111; padding: 3mm 0 3.5mm 0; margin: 0; }
.numcol { float: left; width: 26mm; }
.num { font-size: 20pt; font-weight: bold; letter-spacing: -0.5pt; line-height: 1; }
.form { font-size: 7pt; text-transform: uppercase; letter-spacing: 0.5pt; color: #6B7280; margin-top: 1.5mm; line-height: 1.4; }
.coremark { font-size: 7.5pt; font-weight: bold; color: #2337FF; margin-top: 1.5mm; }
.maincol { margin-left: 28mm; }
.clear { clear: both; }
.ctitle { font-size: 13.5pt; font-weight: bold; letter-spacing: -0.2pt; line-height: 1.3; }
.ex { margin: 0.8mm 0; }
.scene { color: #2337FF; font-weight: bold; }
.meaning { color: #374151; margin: 1mm 0; }
.also { margin: 1mm 0; }
.meta { font-size: 8pt; color: #6B7280; line-height: 1.5; margin: 1mm 0; }
.try { font-weight: bold; margin-top: 1mm; }
ul.bodylist { margin: 2mm 0 2mm 6mm; padding-left: 5mm; }
ul.bodylist li { margin: 1mm 0; }
.alphablock { margin: 3mm 0; break-inside: avoid; }
.aletter { font-size: 18pt; font-weight: bold; color: #2337FF; margin-right: 3mm; }
.alphablock p { display: inline; }
table.check { width: 100%; border-collapse: collapse; font-size: 8.5pt; margin: 4mm 0; }
table.check th { background: #111; color: #fff; padding: 2mm; text-align: left; }
table.check td { border-bottom: 0.5pt solid #E5E7EB; padding: 1.6mm 2mm; vertical-align: top; }
table.check td.cn { color: #2337FF; font-weight: bold; white-space: nowrap; }
table.check tr { break-inside: avoid; }
.box { display: inline-block; width: 3.5mm; height: 3.5mm; border: 0.75pt solid #111; vertical-align: middle; }
p { margin: 2.5mm 0; }
strong { color: #111; }
"""

cover = """<div class="cover">
<div class="topline"><span>GRID EDITION</span><span>2026</span></div>
<h1>Speaking<br>Chunks<span class="dot">.</span></h1>
<div class="square"></div>
<div class="cn">美式英语口语表达库</div>
<p class="sub">说得出口的 120 句。没有卡片，没有装饰，只剩网格、黑线和一句话本身。先读英文，再看例句，中文意思只是注脚。</p>
<table class="meta">
<tr><td class="lab">Contents</td><td>120 chunks · 15 themes · 3 rounds · #001–#120</td></tr>
<tr><td class="lab">Level</td><td>B2–C1 · 中英双语 · 美式英语</td></tr>
<tr><td class="lab">Per entry</td><td>英文 chunk / 2 句例句 / 中文意思 / 可替换说法 / 发音 / 提醒 / 练习</td></tr>
<tr><td class="lab">Source</td><td>American_English_Speaking_Chunks.md · 编号与原稿顺序一致</td></tr>
</table>
<div class="bignums"><span>120</span> / <span>15</span> / <span>30</span></div>
<div class="foot">120 chunks · 15 themes · 30 to start with.<br>Grid Edition · 与正式版、Muse  workbook 版不同的第三种排法。</div>
</div>"""

spec = """<div class="front"><h2>Specification</h2>
<table class="spec">
<tr><td class="lab">Grid</td><td>左列是编号与正式度，右列是句子本身。每一行以 1.5pt 黑线开头，行与行之间只靠黑线分隔，没有卡片、没有底色。</td></tr>
<tr><td class="lab">Type</td><td>全部无衬线。英文 chunk 加粗 13.5pt，例句、注脚依次降级，信息层级只靠字号和黑线，不靠颜色块。</td></tr>
<tr><td class="lab">Colour</td><td>只有一种点缀色：电光蓝。只用在编号、核心标记、场景标签和页码上，其他全部是黑、白、灰。</td></tr>
<tr><td class="lab">Order</td><td>每行先给英文和例句，再给中文意思。顺序本身就是主张：先说，再核对。</td></tr>
<tr><td class="lab">Use</td><td>先读下一页的 30 句，再按主题索引查。书末有按字母排序的索引和一张 120 行的主清单，适合查、适合打勾、适合打印后夹在笔记本里。</td></tr>
</table>
</div>"""

core_page = f"""<div class="front"><h2>30 to start with</h2>
<p>每轮最值得背的 10 句，共 30 句，按原稿每轮清单的顺序排列。编号与正文行号一致。</p>
<table class="coregrid">{core_grid}</table>
</div>"""

contents = f"""<div class="contents"><h2>Index · 主题索引</h2>
<p>按主题查。正文里每轮开头还有总览，每轮末尾有 7 天复习计划。页码是实际页码。</p>
<table class="ctable">{content_rows}</table>
</div>"""

alpha_page = f"""<div class="front"><h2 class="appendix">Alphabetical index</h2>
<p>按英文 chunk 首字母排序。数字是正文行号。</p>
{alpha_blocks}</div>"""

check_page = f"""<div class="front"><h2 class="appendix">Master checklist · 120 行总清单</h2>
<p>全部 120 句，一行一句。能脱口而出一次，就在右边方框里打勾。这一页是查漏用的总表，不是练习页。</p>
<table class="check"><thead><tr><th>#</th><th>Chunk</th><th style="width:12mm;">✓</th></tr></thead>
<tbody>{check_rows}</tbody></table>
<p>Colophon · Grid Edition. Set in a grid, sans only, black rules, one blue. Content and numbering are unchanged from the source Markdown; only the layout is new, and it shares no layout elements with the formal edition or the Muse workbook edition.</p>
</div>"""

doc = (f"<!doctype html><html><head><meta charset='utf-8'>"
       f"<title>Speaking Chunks · Grid Edition</title><style>{CSS}</style></head>"
       f"<body>{cover}{spec}{core_page}{contents}{body_html}{alpha_page}{check_page}</body></html>")

from weasyprint import HTML
HTML(string=doc).write_pdf(str(OUT))
print(f"wrote {OUT}")
