#!/usr/bin/env python3
"""Build Muse-style edition of American English Speaking Chunks (v2).

Deliberately NOT the md2pdf formal layout (that project is the user's own;
this edition is Muse's own take, for comparison):
- warm paper, serif English, orange/teal accents, rounded workbook cards
- a checkbox on every card: tick it when you can actually say it
- theme openers with a quick list of the 8 chunks in that theme
- contents as a theme index (not a formal TOC with leader dots)
- a scene index at the end (find a sentence by where you will say it)
- a blank speaking log to fill in by hand after printing

Engine: WeasyPrint 70 in ~/workspace/.venv-md2pdf.
"""
import argparse
import html
import re
from pathlib import Path

_ap = argparse.ArgumentParser(description='Build a speaking-chunks PDF in this style.')
_ap.add_argument('input', nargs='?', default=str(Path(__file__).resolve().parent.parent / 'examples' / 'American_English_Speaking_Chunks.md'), help='Input Markdown file')
_ap.add_argument('-o', '--output', default=str(Path(__file__).resolve().parent.parent / 'output' / 'muse.pdf'), help='Output PDF file')
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

# assign section ids to every h2, in order (contents is printed before body)
sec = 0
for b in blocks:
    if b["type"] == "h2":
        sec += 1
        b["hid"] = f"sec-{sec}"

themes = [b for b in blocks if b["type"] == "h2" and "主题" in b["text"]]
theme_chunks = {}
for c in chunks:
    theme_chunks.setdefault(c["h2"], []).append(c)


def esc(s):
    return html.escape(s or "")


def pill(formality):
    f = formality or ""
    if f.startswith("casual"):
        style = "background:#E6F4F1;color:#0F766E;"
    elif f.startswith("formal"):
        style = "background:#F3E8E8;color:#7C2D12;"
    elif f.startswith("professional"):
        style = "background:#FDEEDD;color:#9A3412;"
    else:
        style = "background:#EEF0F3;color:#475569;"
    return f'<span class="pill" style="{style}">{esc(f)}</span>'


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


def render_card(c):
    f = c["fields"]
    core = c.get("core", False)
    cls = "card core" if core else "card"
    badge = '<span class="corebadge">★ CORE · 最值得背</span>' if core else ""
    return f"""<section class="{cls}">
<div class="cardtop"><span class="box"></span><span class="cnum">#{c["num"]:03d}</span>{pill(f.get("正式度", ""))} {badge}</div>
<div class="ctitle">{esc(c["title"])}</div>
<div class="meaning">{esc(f.get("中文意思", ""))}</div>
<div class="say"><div class="smalllabel">SAY IT LIKE THIS · 例句</div>{render_examples(f.get("美式例句", ""))}</div>
<div class="altblock"><div class="smalllabel">ALTERNATIVES · 换着说</div>{render_alts(f.get("可替换说法", ""))}</div>
<table class="footgrid"><tr>
<td><div class="smalllabel">PRONUNCIATION · 发音</div><div class="pron">{esc(f.get("美式发音与流利度提示", ""))}</div></td>
<td><div class="smalllabel">WATCH OUT · 提醒</div>{esc(f.get("使用提醒", ""))}</td>
</tr></table>
<div class="try"><b>TRY IT ▸</b> {esc(f.get("迷你练习", ""))}</div>
<div class="done"><span class="box"></span> 我能脱口而出这句了</div>
</section>"""


body_parts = []
for b in blocks:
    if b["type"] == "h2":
        cls = "roundhead" if "总览" in b["text"] else "chapter"
        body_parts.append(f'<h2 class="{cls}" id="{b["hid"]}">{esc(b["text"])}</h2>')
        if "主题" in b["text"]:
            tcs = theme_chunks.get(b["text"], [])
            rng = f"#{tcs[0]['num']:03d}–#{tcs[-1]['num']:03d}" if tcs else ""
            pills = "".join(f"<li>{esc(c['title'])}</li>" for c in tcs)
            body_parts.append(
                f'<div class="themeintro"><div class="themeintro-meta">8 chunks · {rng} · 先扫一遍这 8 句，再一张张练</div>'
                f"<ul class='quicklist'>{pills}</ul></div>")
    elif b["type"] == "chunk":
        body_parts.append(render_card(b))
    elif b["type"] == "bullets":
        prefix = "☐ " if "7 天" in b["h2"] else ""
        items = "".join(f"<li>{prefix}{esc(x)}</li>" for x in b["items"])
        body_parts.append(f"<ul class='bodylist'>{items}</ul>")
body_html = "\n".join(body_parts)

# contents: themes only, with real page numbers
content_rows = ""
cur_round = 0
for b in themes:
    if b["round"] != cur_round:
        cur_round = b["round"]
        content_rows += f'<tr class="roundrow"><td colspan="3">第 {cur_round} 轮</td></tr>'
    tcs = theme_chunks.get(b["text"], [])
    rng = f"#{tcs[0]['num']:03d}–#{tcs[-1]['num']:03d}" if tcs else ""
    content_rows += (f'<tr><td class="ctheme"><a href="#{b["hid"]}">{esc(b["text"])}</a></td>'
                     f'<td class="crange">{rng}</td>'
                     f'<td class="cpage"><a href="#{b["hid"]}"></a></td></tr>')

# core 30 as a grid of mini cards (2 columns)
core_cells = []
for lst in core_lists:
    for c in lst:
        core_cells.append(
            f"<td class='minicard'><span class='mcnum'>#{c['num']:03d}</span> "
            f"<b>{esc(c['title'])}</b><br><span class='mcmean'>{esc(c['fields'].get('中文意思', ''))}</span></td>")
core_grid = ""
for i in range(0, len(core_cells), 2):
    pair = core_cells[i:i + 2]
    if len(pair) == 1:
        pair.append("<td></td>")
    core_grid += "<tr>" + "".join(pair) + "</tr>"

# scene index: scene tag -> chunks, in first-seen order
scenes = {}
for c in chunks:
    for tag in re.findall(r"\[([^\]]+)\]", c["fields"].get("美式例句", "")):
        scenes.setdefault(tag, []).append(c)
scene_blocks = ""
for tag, lst in scenes.items():
    items = "； ".join(f"#{c['num']:03d} {c['title']}" for c in lst)
    scene_blocks += f'<div class="sceneblock"><div class="scenetitle">[{esc(tag)}] · {len(lst)} 句</div><p>{esc(items)}</p></div>'

log_rows = "".join(
    "<tr><td></td><td></td><td></td><td></td></tr>" for _ in range(24))

CSS = r"""
@page {
  size: A4; margin: 16mm 14mm 16mm 14mm; background: #FDFBF7;
  @top-left { content: "SAY IT · 美式口语"; font-family: "Noto Sans CJK SC", sans-serif; font-size: 8pt; color: #A8A29E; }
  @top-right { content: string(chapter); font-family: "Noto Sans CJK SC", sans-serif; font-size: 8pt; color: #A8A29E; }
  @bottom-center { content: "· " counter(page) " ·"; font-family: "Noto Sans CJK SC", sans-serif; font-size: 9pt; color: #E4572E; }
}
@page cover { margin: 0; background: #FDFBF7; @top-left { content: none; } @top-right { content: none; } @bottom-center { content: none; } }
@page contents { @top-right { content: "Contents"; } }
html { font-family: "Noto Sans CJK SC", "Noto Sans CJK", "DejaVu Sans", sans-serif; font-size: 9.5pt; line-height: 1.6; color: #1C1A17; }
body { margin: 0; background: #FDFBF7; }
.cover { page: cover; height: 297mm; box-sizing: border-box; padding: 18mm 16mm; }
.cover .topline { font-size: 8.5pt; letter-spacing: 1.6pt; color: #78716C; border-bottom: 0.5pt solid #E8E0D3; padding-bottom: 4mm; margin-bottom: 14mm; }
.cover h1 { font-family: "Noto Serif CJK SC", "Noto Serif", serif; font-size: 46pt; line-height: 1.15; margin: 0; color: #1C1A17; }
.cover .sayit { font-family: "Noto Serif", serif; font-style: italic; font-size: 21pt; color: #E4572E; margin-top: 4mm; }
.cover .stroke { width: 30mm; height: 2mm; background: #E4572E; border-radius: 1mm; margin: 7mm 0; }
.cover p.intro { font-size: 11pt; line-height: 1.7; max-width: 150mm; }
.cover table.stats { width: 100%; border-collapse: collapse; margin-top: 10mm; }
.cover table.stats td { border: 0.75pt solid #1C1A17; padding: 5mm 4mm; text-align: center; }
.cover table.stats b { display: block; font-family: "Noto Serif", serif; font-size: 22pt; color: #E4572E; }
.cover .foot { margin-top: 14mm; font-size: 9pt; color: #78716C; line-height: 1.7; }
.front { break-after: page; }
.front h2 { bookmark-level: 2; string-set: none; break-before: auto; font-family: "Noto Serif CJK SC", "Noto Serif", serif; font-size: 22pt; color: #1C1A17; margin-top: 0; }
.front h3 { font-size: 11.5pt; color: #1C1A17; margin-top: 6mm; }
.principle { margin: 5mm 0; }
.principle .pnum { font-family: "Noto Serif", serif; font-size: 20pt; color: #E4572E; margin-right: 3mm; }
.contents { page: contents; break-after: page; }
.contents h2 { bookmark-level: 2; string-set: none; font-family: "Noto Serif CJK SC", "Noto Serif", serif; font-size: 22pt; }
table.ctable { width: 100%; border-collapse: collapse; font-size: 9.5pt; }
table.ctable td { border-bottom: 0.5pt solid #E8E0D3; padding: 2.4mm 1mm; vertical-align: top; }
table.ctable tr.roundrow td { background: #FFF1C9; font-weight: bold; color: #92400E; border-bottom: none; }
table.ctable td.ctheme a { text-decoration: none; color: #1C1A17; font-weight: bold; }
table.ctable td.crange { color: #E4572E; font-weight: bold; white-space: nowrap; text-align: right; }
table.ctable td.cpage { width: 12mm; text-align: right; }
table.ctable td.cpage a { text-decoration: none; color: #E4572E; font-weight: bold; }
table.ctable td.cpage a::after { content: target-counter(attr(href), page); }
table.coregrid { width: 100%; border-collapse: separate; border-spacing: 3mm; margin-left: -3mm; }
table.coregrid td.minicard { width: 50%; background: #fff; border: 0.5pt solid #E8E0D3; border-radius: 2.5mm; padding: 3mm; vertical-align: top; font-size: 9pt; line-height: 1.5; }
table.coregrid td.minicard .mcnum { color: #E4572E; font-weight: bold; }
table.coregrid td.minicard .mcmean { color: #57534E; }
table.coregrid tr { break-inside: avoid; }
h2.chapter { string-set: chapter content(); break-before: page; bookmark-level: 2; font-family: "Noto Serif CJK SC", "Noto Serif", serif; font-size: 20pt; color: #1C1A17; margin-top: 0; border-bottom: 2pt solid #E4572E; padding-bottom: 2mm; }
h2.roundhead { string-set: chapter content(); break-before: page; bookmark-level: 2; font-family: "Noto Serif CJK SC", "Noto Serif", serif; font-size: 26pt; color: #1C1A17; margin-top: 0; }
.themeintro { background: #FFF1C9; border-radius: 2.5mm; padding: 3.5mm 4mm; margin: 0 0 5mm 0; }
.themeintro-meta { font-size: 8.5pt; color: #92400E; font-weight: bold; margin-bottom: 2mm; }
ul.quicklist { list-style: none; margin: 0; padding: 0; }
ul.quicklist li { display: inline-block; background: #fff; border: 0.5pt solid #E8E0D3; border-radius: 2mm; padding: 1mm 2.5mm; margin: 0 1.5mm 1.5mm 0; font-size: 8.5pt; }
.card { break-inside: avoid; background: #fff; border: 0.75pt solid #E8E0D3; border-radius: 3mm; padding: 4mm 4.5mm 3.5mm 4.5mm; margin: 0 0 5mm 0; }
.card.core { border-color: #EAB308; background: #FFFEF5; }
.cardtop { margin-bottom: 1.5mm; }
.box { display: inline-block; width: 3.5mm; height: 3.5mm; border: 0.75pt solid #1C1A17; border-radius: 0.5mm; vertical-align: middle; margin-right: 2mm; }
.cnum { color: #E4572E; font-weight: bold; font-size: 9pt; margin-right: 2mm; }
.pill { display: inline-block; font-size: 7.5pt; font-weight: bold; padding: 0.6mm 2.2mm; border-radius: 2mm; vertical-align: middle; }
.corebadge { display: inline-block; background: #FFF1C9; color: #92400E; font-size: 7.5pt; font-weight: bold; padding: 0.6mm 2.2mm; border-radius: 2mm; vertical-align: middle; }
.ctitle { font-family: "Noto Serif", "Noto Serif CJK SC", serif; font-size: 15pt; font-weight: bold; color: #1C1A17; line-height: 1.3; }
.meaning { font-size: 10pt; color: #57534E; margin: 0.5mm 0 2mm 0; }
.smalllabel { font-size: 7.5pt; letter-spacing: 1pt; color: #E4572E; font-weight: bold; margin-bottom: 1mm; }
.say { background: #FDFBF7; border-left: 2.5pt solid #E4572E; padding: 2mm 3mm; margin: 2mm 0; }
.ex { margin: 0.8mm 0; }
.scene { color: #147A7A; font-weight: bold; }
.altblock { margin: 2mm 0; }
ul.alts { margin: 0; padding-left: 5mm; }
ul.alts li { margin: 0.6mm 0; }
table.footgrid { width: 100%; border-collapse: collapse; margin: 2mm 0; }
table.footgrid td { width: 50%; vertical-align: top; padding-right: 3mm; }
.pron { font-family: "DejaVu Sans", "Noto Sans CJK SC", sans-serif; }
.try { background: #E6F4F1; border-radius: 2mm; padding: 2.5mm 3mm; margin-top: 2mm; }
.done { margin-top: 2.5mm; font-size: 8.5pt; color: #57534E; }
ul.bodylist { margin: 2mm 0 2mm 6mm; padding-left: 5mm; }
ul.bodylist li { margin: 1mm 0; }
.sceneblock { margin: 4mm 0; break-inside: avoid; }
.scenetitle { font-weight: bold; color: #E4572E; font-size: 10.5pt; margin-bottom: 1mm; }
table.log { width: 100%; border-collapse: collapse; font-size: 9pt; margin: 4mm 0; }
table.log th { background: #1C1A17; color: #fff; padding: 2.5mm; text-align: left; }
table.log td { border: 0.5pt solid #D6D3D1; height: 9mm; }
p { margin: 2.5mm 0; text-align: justify; }
strong { color: #1C1A17; }
"""

cover = """<div class="cover">
<div class="topline">A SPEAKING WORKBOOK &nbsp;·&nbsp; AMERICAN ENGLISH &nbsp;·&nbsp; B2–C1</div>
<h1>说得出口</h1>
<div class="sayit">Say it out loud.</div>
<div class="stroke"></div>
<p class="intro">这不是一本单词书，也不是一份正式报告。这是一本练嘴的本子：120 句可以直接说出口的话，按你会在哪里说出口来组织。先说出来，再慢慢说对，最后在真实对话里用上一次。</p>
<table class="stats"><tr>
<td><b>120</b>chunks</td><td><b>15</b>themes</td><td><b>30</b>start here</td>
</tr></table>
<div class="foot">原稿 Markdown #001–#120 全文 · 第 1–3 轮 · 中英双语 · 美式英语<br>
Print it, tick it, say it. 打印出来，打勾，说出口。<br>
Muse Edition · 2026 年 10 月 28 日 · 与 md2pdf 正式版式不同的另一版</div>
</div>"""

design = """<div class="front"><h2>我为什么这样排</h2>
<p>上一版是正式文档的样子：藏青、表格、目录引导点，适合存档和交付。这一版我想换一个出发点：如果这本书的目的是“说出口”，那版式就应该像一本练嘴的手册，而不是一份报告。</p>
<div class="principle"><span class="pnum">01</span><b>一卡一句话。</b> 每张卡只讲一句能完整说出口的话，英文用大号衬线字先抢眼，中文意思退后半步，先练嘴，再核对意思。</div>
<div class="principle"><span class="pnum">02</span><b>打勾才算会。</b> 每张卡左上角和底部都有一个方框。不是“看过”就打勾，是你能不看卡片、脱口而出一次，才打勾。</div>
<div class="principle"><span class="pnum">03</span><b>按场景找句子。</b> 正文按主题排，但书末有一张场景索引：下次要开会、要采访、要闲聊，先去场景索引里挑一句，而不是从 #001 背到 #120。</div>
<div class="principle"><span class="pnum">04</span><b>留白是给你的。</b> 书末有一张空白打卡表，打印出来手写：哪天、在哪里、把哪句真的说出口了。没用过的句子，不算你的句子。</div>
<h3>正式度怎么看</h3>
<p><span class="pill" style="background:#E6F4F1;color:#0F766E;">casual</span> 朋友闲聊 &nbsp; <span class="pill" style="background:#EEF0F3;color:#475569;">neutral</span> 日常 + 职场通用 &nbsp; <span class="pill" style="background:#FDEEDD;color:#9A3412;">professional</span> 会议、谈判、演讲 &nbsp; <span class="pill" style="background:#F3E8E8;color:#7C2D12;">formal</span> 正式场合。卡片上的 “neutral / professional” 表示两者都可用。</p>
<h3>从哪里开始</h3>
<p>先背下一页的 30 张小卡：每轮最值得背的 10 句。30 句能脱口而出，再按主题往 120 句扩。每天 1 个主题，8 句，不要贪多。</p>
</div>"""

core_page = f"""<div class="front"><h2>Start here · 先背这 30 句</h2>
<p>每轮最值得背的 10 句，共 30 句。编号与正文卡片一致。这页是快速入口，不是替代品：真正练的时候，还是要翻到正文卡片看例句、发音和练习。</p>
<table class="coregrid">{core_grid}</table>
</div>"""

contents = f"""<div class="contents"><h2>Contents · 按主题找</h2>
<p>按主题查，正文里每轮开头还有总览，每轮末尾有 7 天复习计划。页码是实际页码。</p>
<table class="ctable">{content_rows}</table>
</div>"""

scene_page = f"""<div class="front"><h2>Scene index · 按场景找句子</h2>
<p>例句里带场景标签的句子，按场景归到这里。同一句可能出现在多个场景里，这里只按它例句里的场景标签归类，方便你“要去开会了，先挑两句”的时候用。</p>
{scene_blocks}</div>"""

log_page = f"""<div class="front"><h2>Speaking log · 说出口打卡表</h2>
<p>打印出来手写。规则很简单：在真实对话里说出口一次，才填一行。背诵不算，默读不算。</p>
<table class="log"><thead><tr><th style="width:22mm;">日期</th><th style="width:22mm;">Chunk #</th><th>在哪里说出口的</th><th style="width:28mm;">感觉如何</th></tr></thead>
<tbody>{log_rows}</tbody></table>
<p>Colophon · 这版由 Muse 排版，引擎同样是 WeasyPrint，但配色、字体、卡片结构、主题导览、场景索引和打卡表都是另一套思路，与 md2pdf 的正式文档版式无关。原稿与编号未改动，内容与上一版 PDF 一致。</p>
</div>"""

doc = (f"<!doctype html><html><head><meta charset='utf-8'>"
       f"<title>说得出口 · 美式英语口语表达库 Muse Edition</title><style>{CSS}</style></head>"
       f"<body>{cover}{design}{core_page}{contents}{body_html}{scene_page}{log_page}</body></html>")

from weasyprint import HTML
HTML(string=doc).write_pdf(str(OUT))
print(f"wrote {OUT}")
