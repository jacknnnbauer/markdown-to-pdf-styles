#!/usr/bin/env python3
"""Build Playbook Edition (v4) of American English Speaking Chunks.

Designed from scratch at the user's request to forget the previous
three editions. What is deliberately NOT reused:
- v1 formal: navy band, meta table, leader-dot TOC, rectangular cards.
- v2 workbook: warm cream paper, serif English, orange, rounded cards
  with tick boxes, yellow theme intros, scene index, speaking log.
- v3 grid: white paper, sans-only black rules, electric blue, left
  number column, alphabetical index, 120-row checklist.

v4 instead starts from a different idea: speaking is play, so the book
is a playbook. Bauhaus-inspired geometry (red circle, yellow semicircle,
blue square, black bar), poster type, and short playful field labels
(SAY / MEAN / EXAMPLE / SWAP / SOUND / WATCH / PLAY). Theme colours
cycle red-yellow-blue-black purely to tell themes apart; formality is
shown as plain black outline text, never as a colour, so colour never
carries meaning here. Appendices are new too: pick-your-10 and a
30-day challenge grid, not a scene index, alphabetical index, checklist
or handwritten log.

Engine: WeasyPrint 70 in ~/workspace/.venv-md2pdf.
"""
import argparse
import html
import re
from pathlib import Path

_ap = argparse.ArgumentParser(description='Build a speaking-chunks PDF in this style.')
_ap.add_argument('input', nargs='?', default=str(Path(__file__).resolve().parent.parent / 'examples' / 'American_English_Speaking_Chunks.md'), help='Input Markdown file')
_ap.add_argument('-o', '--output', default=str(Path(__file__).resolve().parent.parent / 'output' / 'playbook.pdf'), help='Output PDF file')
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
        # Drop the file-head meta bullets that appear before the first
        # ## heading: they used to leak into the PDF as a stray page
        # between the contents map and Round 1.
        if cur_h2:
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
theme_chunks = {}
for c in chunks:
    theme_chunks.setdefault(c["h2"], []).append(c)

# theme colours cycle: red, yellow, blue, black (text colour pairs with each)
THEME_COLORS = [("#D90429", "#FFFFFF"), ("#FFC300", "#111111"),
                ("#1849A9", "#FFFFFF"), ("#111111", "#FFFFFF")]
for ti, b in enumerate(themes):
    b["color"], b["ctext"] = THEME_COLORS[ti % len(THEME_COLORS)]
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


def render_alts(val):
    segs = [s.strip() for s in (val or "").split(" / ") if s.strip()]
    items = []
    for s in segs:
        if "：" in s:
            lab, v = s.split("：", 1)
            items.append(f"<li><b>{esc(lab)}：</b>{esc(v)}</li>")
        else:
            items.append(f"<li>{esc(s)}</li>")
    return "<ul class='alts'>" + "".join(items) + "</ul>"


def render_play(c):
    f = c["fields"]
    tb = theme_by_text.get(c["h2"])
    color = tb["color"] if tb else "#D90429"
    ctext = tb["ctext"] if tb else "#FFFFFF"
    star = ' <span class="star">★</span>' if c.get("core") else ""
    return f"""<section class="play">
<div class="numcircle" style="background:{color};color:{ctext}">#{c["num"]:03d}</div>
<div class="playmain">
<div class="say">{esc(c["title"])}{star} <span class="formpill">{esc(f.get("正式度", ""))}</span></div>
<div class="mean">MEAN — {esc(f.get("中文意思", ""))}</div>
<div class="exbox"><div class="smalllabel">EXAMPLE — 例句</div>{render_examples(f.get("美式例句", ""))}</div>
<div class="swap"><div class="smalllabel">SWAP — 换着说</div>{render_alts(f.get("可替换说法", ""))}</div>
<div class="small">SOUND — {esc(f.get("美式发音与流利度提示", ""))}</div>
<div class="small">WATCH — {esc(f.get("使用提醒", ""))}</div>
<div class="playbox">PLAY ▸ {esc(f.get("迷你练习", ""))}</div>
</div>
<div class="clear"></div>
</section>"""


body_parts = []
for b in blocks:
    if b["type"] == "h2":
        cls = "roundhead" if "总览" in b["text"] else "chapter"
        body_parts.append(f'<h2 class="{cls}" id="{b["hid"]}">{esc(b["text"])}</h2>')
        if "总览" in b["text"]:
            rc = [c for c in chunks if c["round"] == b["round"]]
            items = "".join(
                f"<li><span class='rnum'>#{c['num']:03d}</span> {esc(c['title'])}</li>" for c in rc)
            body_parts.append(
                f'<div class="roundindex"><div class="rlabel">本轮 40 句速览 · ROUND INDEX</div>'
                f"<ul>{items}</ul></div>")
        if "主题" in b["text"]:
            tb = theme_by_text[b["text"]]
            tcs = theme_chunks.get(b["text"], [])
            rng = f"#{tcs[0]['num']:03d}–#{tcs[-1]['num']:03d}" if tcs else ""
            items = "".join(
                f"<li><span class='olistnum'>{i:02d}</span> {esc(c['title'])}</li>"
                for i, c in enumerate(tcs, 1))
            body_parts.append(
                f'<div class="themebar" style="background:{tb["color"]};color:{tb["ctext"]}">'
                f'{esc(b["text"])} &nbsp;·&nbsp; {rng}</div>'
                f"<ol class='themeol'>{items}</ol>")
    elif b["type"] == "chunk":
        body_parts.append(render_play(b))
    elif b["type"] == "bullets":
        items = "".join(f"<li>{esc(x)}</li>" for x in b["items"])
        body_parts.append(f"<ul class='bodylist'>{items}</ul>")
body_html = "\n".join(body_parts)

# contents: round bars + theme rows with colour dots
content_parts = ""
cur_round = 0
for b in themes:
    if b["round"] != cur_round:
        cur_round = b["round"]
        content_parts += f'<div class="roundbar">ROUND {cur_round}</div>'
    tcs = theme_chunks.get(b["text"], [])
    rng = f"#{tcs[0]['num']:03d}–#{tcs[-1]['num']:03d}" if tcs else ""
    tb = theme_by_text[b["text"]]
    content_parts += (f'<div class="crow"><span class="dot" style="background:{tb["color"]}"></span> '
                      f'<a href="#{b["hid"]}">{esc(b["text"])}</a> '
                      f'<span class="crange">{rng}</span> '
                      f'<span class="cpage"><a href="#{b["hid"]}"></a></span></div>')

# core 30 as colour-topped tiles, 3 per row
core_cells = []
for ci, lst in enumerate(core_lists):
    for c in lst:
        color = THEME_COLORS[ci % len(THEME_COLORS)][0]
        core_cells.append(
            f"<td class='tile'><div class='tiletop' style='background:{color}'></div>"
            f"<span class='mcnum'>#{c['num']:03d}</span> <b>{esc(c['title'])}</b>"
            f"<br><span class='mcmean'>{esc(c['fields'].get('中文意思', ''))}</span></td>")
core_grid = ""
for i in range(0, len(core_cells), 3):
    pair = core_cells[i:i + 3]
    while len(pair) < 3:
        pair.append("<td></td>")
    core_grid += "<tr>" + "".join(pair) + "</tr>"

pick_rows = "".join(
    f"<tr><td>{i}</td><td></td><td></td><td></td></tr>" for i in range(1, 11))
day_cells = ""
for d in range(1, 31):
    day_cells += f"<td class='day'><b>{d}</b><br><span class='dayline'>chunk # ______</span></td>"
    if d % 5 == 0 and d < 30:
        day_cells += "</tr><tr>"
day_grid = f"<tr>{day_cells}</tr>"

CSS = r"""
@page {
  size: A4; margin: 15mm 14mm 15mm 14mm; background: #fff;
  @top-left { content: "PLAYBOOK"; font-family: "Liberation Sans", "Noto Sans CJK SC", sans-serif; font-size: 8pt; font-weight: bold; letter-spacing: 1.5pt; color: #D90429; }
  @top-right { content: string(chapter); font-family: "Noto Sans CJK SC", sans-serif; font-size: 8pt; color: #6B7280; }
  @bottom-left { content: "B2–C1 · AMERICAN ENGLISH"; font-family: "Noto Sans CJK SC", sans-serif; font-size: 8pt; color: #6B7280; }
  @bottom-right { content: counter(page); font-family: "Liberation Sans", sans-serif; font-size: 10pt; font-weight: bold; color: #D90429; }
}
@page cover { margin: 0; background: #fff; @top-left { content: none; } @top-right { content: none; } @bottom-left { content: none; } @bottom-right { content: none; } }
@page contents { @top-right { content: "MAP"; } }
html { font-family: "Noto Sans CJK SC", "Liberation Sans", sans-serif; font-size: 9.5pt; line-height: 1.55; color: #111; }
body { margin: 0; background: #fff; }
.cover { page: cover; height: 297mm; box-sizing: border-box; padding: 16mm 14mm; }
.cover .topline { font-size: 8.5pt; letter-spacing: 1.5pt; font-weight: bold; border-bottom: 3pt solid #111; padding-bottom: 3mm; }
.cover h1 { font-family: "Liberation Sans", sans-serif; font-size: 54pt; line-height: 0.95; letter-spacing: -1pt; margin: 12mm 0 0 0; text-transform: uppercase; }
.cover h1 .dot { color: #D90429; }
.cover .shapes { margin: 8mm 0 4mm 0; }
.cover .circle { display: inline-block; width: 26mm; height: 26mm; background: #D90429; border-radius: 50%; vertical-align: bottom; }
.cover .semi { display: inline-block; width: 30mm; height: 15mm; background: #FFC300; border-radius: 15mm 15mm 0 0; margin-left: 6mm; vertical-align: bottom; }
.cover .square { display: inline-block; width: 15mm; height: 15mm; background: #1849A9; margin-left: 6mm; vertical-align: bottom; }
.cover .bar { display: inline-block; width: 42mm; height: 6mm; background: #111; margin-left: 6mm; vertical-align: bottom; }
.cover .cn { font-size: 18pt; font-weight: bold; margin-top: 6mm; }
.cover .sub { font-size: 10.5pt; color: #374151; line-height: 1.7; max-width: 155mm; }
.cover table.nums { width: 100%; border-collapse: collapse; margin-top: 10mm; }
.cover table.nums td { padding: 4mm 3mm; vertical-align: top; color: #fff; }
.cover table.nums td.y { color: #111; }
.cover table.nums b { display: block; font-size: 24pt; line-height: 1; }
.cover .foot { margin-top: 10mm; font-size: 8.5pt; color: #6B7280; line-height: 1.7; border-top: 0.5pt solid #D1D5DB; padding-top: 3mm; }
.front { break-before: page; break-after: page; }
.front.playflow { break-before: auto; break-after: auto; }
.front h2 { bookmark-level: 2; string-set: none; break-before: auto; font-family: "Liberation Sans", sans-serif; font-size: 24pt; letter-spacing: -0.5pt; margin-top: 0; text-transform: uppercase; }
.front h2.appendix { string-set: chapter content(); }
.front h2.appendix.challenge { break-before: page; }
.coverfoot { margin-top: 52mm; }
.tryline { background: #111; color: #fff; padding: 4mm; font-weight: bold; font-size: 10.5pt; }
.footshapes { margin-top: 4mm; }
.roundindex { margin: 4mm 0; border-top: 0.5pt solid #D1D5DB; padding-top: 3mm; }
.roundindex .rlabel { font-size: 7.5pt; letter-spacing: 1pt; font-weight: bold; color: #D90429; margin-bottom: 2mm; }
.roundindex ul { list-style: none; margin: 0; padding: 0; column-count: 2; column-gap: 6mm; }
.roundindex li { break-inside: avoid; font-size: 8.5pt; padding: 0.8mm 0; border-bottom: 0.5pt dotted #E5E7EB; }
.roundindex li .rnum { color: #D90429; font-weight: bold; }
.rulebox { padding: 4mm; margin: 3mm 0; color: #fff; }
.rulebox.y { color: #111; }
.rulebox h3 { margin: 0 0 1.5mm 0; font-size: 12pt; }
.rulebox p { margin: 0; }
.contents { page: contents; break-before: page; break-after: page; }
.contents h2 { bookmark-level: 2; string-set: none; font-family: "Liberation Sans", sans-serif; font-size: 24pt; text-transform: uppercase; letter-spacing: -0.5pt; }
.roundbar { background: #111; color: #fff; font-weight: bold; letter-spacing: 1pt; font-size: 8.5pt; padding: 2mm 3mm; margin-top: 4mm; }
.crow { border-bottom: 0.5pt solid #E5E7EB; padding: 2.4mm 1mm; }
.crow a { text-decoration: none; color: #111; font-weight: bold; }
.dot { display: inline-block; width: 3.2mm; height: 3.2mm; border-radius: 50%; margin-right: 2mm; vertical-align: middle; }
.crange { color: #6B7280; margin-left: 2mm; }
.cpage { float: right; }
.cpage a { text-decoration: none; color: #D90429; font-weight: bold; }
.cpage a::after { content: target-counter(attr(href), page); }
table.tiles { width: 100%; border-collapse: separate; border-spacing: 3mm; margin-left: -3mm; }
table.tiles td.tile { width: 33.3%; border: 0.5pt solid #D1D5DB; padding: 0 0 3mm 0; vertical-align: top; font-size: 9pt; line-height: 1.5; }
table.tiles td.tile .tiletop { height: 2.5mm; margin-bottom: 2.5mm; }
table.tiles td.tile .mcnum { color: #D90429; font-weight: bold; margin-left: 3mm; }
table.tiles td.tile b { display: block; margin: 0 3mm; }
table.tiles td.tile .mcmean { color: #57534E; margin: 0 3mm; }
table.tiles tr { break-inside: avoid; }
h2.chapter { string-set: chapter content(); break-before: page; bookmark-level: 2; font-family: "Liberation Sans", sans-serif; font-size: 19pt; letter-spacing: -0.5pt; margin-top: 0; border-bottom: 3pt solid #111; padding-bottom: 2mm; }
h2.roundhead { string-set: chapter content(); break-before: page; bookmark-level: 2; font-family: "Liberation Sans", sans-serif; font-size: 26pt; letter-spacing: -0.5pt; margin-top: 0; }
.themebar { padding: 3.5mm 4mm; font-weight: bold; font-size: 11pt; margin: 0 0 3mm 0; }
ol.themeol { list-style: none; margin: 0 0 4mm 0; padding: 0; column-count: 2; column-gap: 6mm; }
ol.themeol li { padding: 1mm 0; border-bottom: 0.5pt dotted #D1D5DB; font-weight: bold; break-inside: avoid; }
.olistnum { color: #D90429; margin-right: 2mm; }
.play { break-inside: avoid; padding: 2.2mm 0 3mm 0; border-bottom: 0.5pt solid #E5E7EB; margin-bottom: 0.5mm; }
.numcircle { float: left; width: 14mm; height: 14mm; border-radius: 50%; text-align: center; line-height: 14mm; font-weight: bold; font-size: 8.5pt; white-space: nowrap; }
.playmain { margin-left: 17mm; }
.playmain { margin-left: 16mm; }
.clear { clear: both; }
.say { font-family: "Liberation Sans", sans-serif; font-size: 13pt; font-weight: bold; letter-spacing: -0.2pt; line-height: 1.3; }
.star { color: #D90429; }
.formpill { display: inline-block; border: 0.75pt solid #111; font-size: 7.5pt; font-weight: normal; padding: 0.4mm 2mm; border-radius: 2mm; vertical-align: middle; margin-left: 2mm; }
.mean { color: #374151; margin: 0.5mm 0 2mm 0; }
.smalllabel { font-size: 7.5pt; letter-spacing: 1pt; font-weight: bold; color: #D90429; margin-bottom: 1mm; }
.exbox { background: #EFEFEF; border-radius: 2mm; padding: 2mm 2.5mm; margin: 1.5mm 0; }
.ex { margin: 0.8mm 0; }
.scene { color: #1849A9; font-weight: bold; }
.swap { margin: 2mm 0; }
ul.alts { margin: 0; padding-left: 5mm; }
ul.alts li { margin: 0.6mm 0; }
.small { font-size: 9pt; color: #374151; line-height: 1.5; margin: 1mm 0; }
.playbox { background: #FEF3C7; border-left: 4pt solid #FFC300; padding: 2mm 2.5mm; margin-top: 1.5mm; }
ul.bodylist { margin: 2mm 0 2mm 6mm; padding-left: 5mm; }
ul.bodylist li { margin: 1mm 0; }
table.pick { width: 100%; border-collapse: collapse; font-size: 9.5pt; margin: 4mm 0; }
table.pick th { background: #111; color: #fff; padding: 2.5mm; text-align: left; }
table.pick td { border-bottom: 0.5pt solid #D1D5DB; height: 8mm; padding: 1.5mm 2mm; }
table.days { width: 100%; border-collapse: collapse; margin: 4mm 0; }
table.days td.day { width: 20%; height: 16mm; border: 0.5pt solid #111; padding: 2mm; vertical-align: top; font-size: 8.5pt; }
table.days td.day b { color: #D90429; }
.dayline { color: #6B7280; }
p { margin: 2.5mm 0; }
strong { color: #111; }
"""

cover = """<div class="cover">
<div class="topline">PLAYBOOK EDITION &nbsp;·&nbsp; 2026</div>
<h1>Words<br>at play<span class="dot">.</span></h1>
<div class="shapes"><span class="circle"></span><span class="semi"></span><span class="square"></span><span class="bar"></span></div>
<div class="cn">玩着说英语 · 美式口语表达库</div>
<p class="sub">120 句可以直接说出口的话，做成一本可以玩的本子。先大声说出来，再看意思，再换着说，最后在真实对话里玩一次。</p>
<table class="nums"><tr>
<td style="background:#D90429;"><b>120</b>chunks</td>
<td style="background:#FFC300;" class="y"><b>15</b>themes</td>
<td style="background:#1849A9;"><b>30</b>start here</td>
</tr></table>
<div class="foot">原稿 Markdown #001–#120 全文 · 第 1–3 轮 · B2–C1 · 中英双语 · 美式英语<br>
Playbook Edition · 从零新排的一版，与前三版的版式无关。</div>
<div class="coverfoot"><div class="tryline">TRY ONE NOW — Let's unpack that · 我们来拆解一下这个</div>
<div class="footshapes"><span style="display:inline-block;width:10mm;height:10mm;background:#D90429;border-radius:50%;margin-right:4mm;"></span><span style="display:inline-block;width:14mm;height:7mm;background:#FFC300;border-radius:7mm 7mm 0 0;margin-right:4mm;"></span><span style="display:inline-block;width:7mm;height:7mm;background:#1849A9;margin-right:4mm;"></span><span style="display:inline-block;width:20mm;height:3mm;background:#111;"></span></div></div>
</div>"""

play = """<div class="front playflow"><h2>How to play</h2>
<div class="rulebox" style="background:#D90429;"><h3>01 · SAY IT FIRST</h3><p>先读英文，大声读出来。读不顺就跟读例句两遍，再看中文意思核对，不要先背中文再翻译成英文。</p></div>
<div class="rulebox y" style="background:#FFC300;"><h3>02 · SWAP IT</h3><p>同一句换着说：更随意、更正式、更强情绪各说一遍。只会一种说法，到了真实场合还是会卡住。</p></div>
<div class="rulebox" style="background:#1849A9;"><h3>03 · PLAY IT FOR REAL</h3><p>在真实对话里用上一次，才算你的。书末有一张“选出你的 10 句”和一张 30 天挑战格，先挑 10 句，再一天一句玩 30 天。</p></div>
<p>正式度只用黑框文字标出，不用颜色表示：casual 是朋友闲聊，neutral 是日常 + 职场通用，professional 是会议、谈判、演讲，formal 是正式场合。本书里的红、黄、蓝、黑只是用来区分主题的几何色，不代表正式度。</p>
</div>"""

core_page = f"""<div class="front playflow"><h2>Start here · 30</h2>
<p>每轮最值得背的 10 句，共 30 句，按原稿每轮清单的顺序排列。编号与正文一致，顶部色条按轮次循环红、黄、蓝。</p>
<table class="tiles">{core_grid}</table>
</div>"""

contents = f"""<div class="contents"><h2>Map · 主题地图</h2>
<p>按主题查。圆点颜色只用来区分主题，与正式度无关。正文里每轮开头还有总览，每轮末尾有 7 天复习计划。页码是实际页码。</p>
{content_parts}</div>"""

appendix = f"""<div class="front"><h2 class="appendix">Pick your 10 · 选出你的 10 句</h2>
<p>从 120 句里选出你最想先练会的 10 句，写下来。选的过程本身就是一次复习。</p>
<table class="pick"><thead><tr><th style="width:12mm;">#</th><th style="width:26mm;">Chunk #</th><th>Chunk</th><th>为什么选它</th></tr></thead>
<tbody>{pick_rows}</tbody></table>
<h2 class="appendix challenge">30-day challenge · 30 天挑战</h2>
<p>一天一句，30 天玩完 30 句。在格子里写下当天练的 chunk 编号，练完打勾。</p>
<table class="days">{day_grid}</table>
<p>Colophon · Playbook Edition. Designed from scratch for this round: geometry, poster type and short SAY / MEAN / EXAMPLE / SWAP / SOUND / WATCH / PLAY labels. Content and numbering are unchanged from the source Markdown.</p>
</div>"""

doc = (f"<!doctype html><html><head><meta charset='utf-8'>"
       f"<title>Words at Play · Playbook Edition</title><style>{CSS}</style></head>"
       f"<body>{cover}{play}{core_page}{contents}{body_html}{appendix}</body></html>")

from weasyprint import HTML
HTML(string=doc).write_pdf(str(OUT))
print(f"wrote {OUT}")
