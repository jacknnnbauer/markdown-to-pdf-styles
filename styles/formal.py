#!/usr/bin/env python3
"""Build American English Speaking Chunks PDF (Rounds 1-3, 120 chunks).

Engine: WeasyPrint 70 in ~/workspace/.venv-md2pdf (Chrome print path in this
VM forwards to the running browser and times out, so WeasyPrint is used,
following the same formal layout goals as build_brief_pdf.py: navy cover,
TOC with real page numbers via target-counter, running header, footer
page numbers, PDF bookmarks, A4).

Design:
- Cover: navy band, tagline, meta table, stats strip, usage notice.
- How to use: field guide, formality legend, pronunciation legend.
- 30 core chunks at a glance: table grouped by round, meaning looked up
  from the parsed entries (not hand-typed, so it cannot drift from body).
- TOC: H2 sections only (front sections + round overviews + themes +
  review plans), with leader dots and real page numbers. PDF bookmarks
  are at section level (H2); chunks are found by their #001-#120 number.
- Body: one chunk = one card (break-inside: avoid), with number, English
  chunk, formality pill, Chinese meaning, examples box, alternatives,
  pronunciation, reminder, practice. Core chunks get a gold left border
  and a star badge, matched from each round's "most worth memorizing"
  list in the source, by normalized substring matching.
"""
import argparse
import html
import re
from pathlib import Path

_ap = argparse.ArgumentParser(description='Build a speaking-chunks PDF in this style.')
_ap.add_argument('input', nargs='?', default=str(Path(__file__).resolve().parent.parent / 'examples' / 'American_English_Speaking_Chunks.md'), help='Input Markdown file')
_ap.add_argument('-o', '--output', default=str(Path(__file__).resolve().parent.parent / 'output' / 'formal.pdf'), help='Output PDF file')
_args = _ap.parse_args()
SRC = Path(_args.input)
OUT = Path(_args.output)
OUT.parent.mkdir(parents=True, exist_ok=True)

NAVY = "#142F4A"
CORAL = "#E85D3D"
GOLD = "#B7791F"

text = SRC.read_text(encoding="utf-8")
lines = text.splitlines()

# ---------- parse ----------
blocks = []  # dicts: h2 / chunk / bullets
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
    elif line.strip() == "---" or line.startswith("# "):
        continue
    # other lines (intro bullets at file head, blank lines) are ignored;
    # cover/how-to/core-table are authored in this script, not from them.
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


# core lists, in document order, matched to chunks
core_lists = []  # list of list-of-chunk-dicts
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

print(f"chunks: {len(chunks)}, core lists: {len(core_lists)}, "
      f"core matched: {sum(len(x) for x in core_lists)}")
assert len(chunks) == 120, f"expected 120 chunks, got {len(chunks)}"
assert len(core_lists) == 3 and all(len(x) == 10 for x in core_lists), \
    f"expected 3x10 core, got {[len(x) for x in core_lists]}"

# ---------- render helpers ----------
def esc(s):
    return html.escape(s or "")


def pill(formality):
    f = formality or ""
    if f.startswith("casual"):
        bg = "#0F766E"
    elif f.startswith("formal"):
        bg = "#7C2D12"
    elif f.startswith("professional"):
        bg = NAVY
    else:
        bg = "#475569"
    return f'<span class="pill" style="background:{bg}">{esc(f)}</span>'


def render_examples(val):
    m = re.match(r"\(1\)\s*(.*?)\s*\(2\)\s*(.*)$", val or "", flags=re.S)
    if m:
        parts = [m.group(1).strip(), m.group(2).strip()]
    else:
        parts = [val.strip()] if val else []
    out = []
    for p in parts:
        # scene tag like [会议] at start of the sentence
        mm = re.match(r"\[([^\]]+)\]\s*(.*)$", p, flags=re.S)
        if mm:
            out.append(f'<p class="ex"><span class="scene">{esc(mm.group(1))}</span> {esc(mm.group(2))}</p>')
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


def field_row(label, body_html):
    return f'<div class="field"><span class="flabel">{label}</span>{body_html}</div>'


def render_chunk(c):
    f = c["fields"]
    core = c.get("core", False)
    cls = "chunk core" if core else "chunk"
    badge = '<span class="corebadge">★ 最值得背</span>' if core else ""
    head = (f'<div class="chead"><span class="cnum">#{c["num"]:03d}</span> '
            f'<span class="ctitle">{esc(c["title"])}</span> '
            f'{pill(f.get("正式度", ""))} {badge}</div>')
    rows = []
    rows.append(field_row("中文意思", f'<span class="meaning">{esc(f.get("中文意思", ""))}</span>'))
    rows.append(f'<div class="field"><span class="flabel">美式例句</span>'
                f'<div class="exbox">{render_examples(f.get("美式例句", ""))}</div></div>')
    rows.append(field_row("可替换说法", render_alts(f.get("可替换说法", ""))))
    rows.append(field_row("发音提示", f'<span class="pron">{esc(f.get("美式发音与流利度提示", ""))}</span>'))
    rows.append(field_row("使用提醒", esc(f.get("使用提醒", ""))))
    rows.append(field_row("迷你练习", esc(f.get("迷你练习", ""))))
    return f'<section class="{cls}">{head}' + "".join(rows) + "</section>"


# ---------- body + TOC ----------
toc_entries = []  # (text, id)
body_parts = []
sec = 0
for b in blocks:
    if b["type"] == "h2":
        sec += 1
        hid = f"sec-{sec}"
        toc_entries.append((b["text"], hid))
        body_parts.append(f'<h2 class="chapter" id="{hid}">{esc(b["text"])}</h2>')
    elif b["type"] == "chunk":
        body_parts.append(render_chunk(b))
    elif b["type"] == "bullets":
        items = "".join(f"<li>{esc(x)}</li>" for x in b["items"])
        body_parts.append(f"<ul>{items}</ul>")
body_html = "\n".join(body_parts)

front_toc = [("如何使用这本书", "howto"), ("30 个最值得背一览", "core30")]
toc_items = "".join(
    f'<li class="l1"><a href="#{hid}">{esc(txt)}</a></li>'
    for txt, hid in front_toc + toc_entries
)

core_rows = ""
for ri, lst in enumerate(core_lists, 1):
    core_rows += f'<tr class="roundrow"><td colspan="4">第 {ri} 轮 · 10 个最值得背</td></tr>'
    for c in lst:
        core_rows += (f"<tr><td class='cn'>#{c['num']:03d}</td>"
                      f"<td class='ce'>{esc(c['title'])}</td>"
                      f"<td>{esc(c['fields'].get('中文意思', ''))}</td>"
                      f"<td class='cth'>{esc(c['h2'].replace('第 ' + str(ri) + ' 轮 · ', ''))}</td></tr>")

CSS = r"""
@page {
  size: A4; margin: 18mm 15mm 18mm 15mm;
  @top-left { content: "美式英语口语表达库"; font-family: "Noto Sans CJK SC", sans-serif; font-size: 8pt; color: #64748b; }
  @top-right { content: string(chapter); font-family: "Noto Sans CJK SC", sans-serif; font-size: 8pt; color: #64748b; }
  @bottom-left { content: "120 chunks · B2-C1 · 美式英语"; font-family: "Noto Sans CJK SC", sans-serif; font-size: 8pt; color: #64748b; }
  @bottom-center { content: counter(page) " / " counter(pages); font-family: "Noto Sans CJK SC", sans-serif; font-size: 8pt; color: #64748b; }
}
@page cover { margin: 0; @top-left { content: none; } @top-right { content: none; } @bottom-left { content: none; } @bottom-center { content: none; } }
@page toc { @top-right { content: "目 录"; } }
html { font-family: "Noto Sans CJK SC", "Noto Sans CJK", "DejaVu Sans", sans-serif; font-size: 9.5pt; line-height: 1.6; color: #1e293b; }
body { margin: 0; }
.cover { page: cover; height: 297mm; box-sizing: border-box; }
.cover .band { background: #142F4A; color: #fff; padding: 20mm 16mm 10mm 16mm; height: 118mm; box-sizing: border-box; }
.cover .kicker { font-size: 8.5pt; letter-spacing: 1.4pt; color: #93C5FD; margin-bottom: 8mm; }
.cover h1 { font-size: 30pt; line-height: 1.25; margin: 0 0 4mm 0; }
.cover .sub { font-size: 13pt; color: #DBEAFE; line-height: 1.5; }
.cover .tagline { margin-top: 6mm; font-size: 10pt; color: #FDE68A; }
.cover .rule { width: 18mm; height: 1.2mm; background: #E85D3D; margin: 10mm 16mm 6mm 16mm; }
.cover table.meta { margin: 0 16mm; width: calc(100% - 32mm); font-size: 9.5pt; line-height: 1.9; }
.cover table.meta th { background: none; color: #475569; width: 28mm; padding: 0; font-weight: bold; text-align: left; vertical-align: top; }
.cover table.meta td { border: none; padding: 0; background: none; }
.cover .stats { margin: 8mm 16mm 0 16mm; background: #142F4A; color: #fff; padding: 5mm; font-size: 10pt; text-align: center; letter-spacing: 0.4pt; }
.cover .stats b { color: #FDE68A; font-size: 13pt; }
.cover .notice { margin: 8mm 16mm 0 16mm; border-left: 3pt solid #E85D3D; background: #FEF2F2; padding: 4mm 5mm; font-size: 9.5pt; line-height: 1.6; }
.cover .foot { margin: 10mm 16mm 0 16mm; border-top: 0.5pt solid #CBD5E1; padding-top: 4mm; font-size: 9pt; color: #64748b; }
.front { break-after: page; }
.front h2 { string-set: none; break-before: auto; font-size: 17pt; color: #142F4A; border-bottom: 1.5pt solid #142F4A; padding-bottom: 2mm; }
.front h3 { font-size: 11.5pt; color: #0F172A; margin-top: 6mm; }
.toc { page: toc; break-after: page; }
.toc h2.tt { string-set: none; break-before: page; font-size: 18pt; color: #142F4A; border-bottom: 1.5pt solid #142F4A; padding-bottom: 3mm; }
.toc ul { list-style: none; padding: 0; margin: 0; }
.toc li { padding: 1.1mm 0; border-bottom: 0.25pt dotted #CBD5E1; }
.toc li a { text-decoration: none; color: #1e293b; font-weight: bold; }
.toc li a::after { content: leader(".") target-counter(attr(href), page); color: #64748b; font-weight: normal; }
h2.chapter { string-set: chapter content(); break-before: page; bookmark-level: 2; font-size: 16pt; color: #142F4A; border-bottom: 1.5pt solid #142F4A; padding-bottom: 2mm; margin-top: 0; }
h2.chapter:first-of-type { break-before: auto; }
.chunk { break-inside: avoid; border: 0.5pt solid #D9E2EC; border-left: 3pt solid #E85D3D; padding: 3.5mm 4mm 3mm 4mm; margin: 0 0 5mm 0; background: #fff; }
.chunk.core { border-left-color: #B7791F; background: #FFFBEB; }
.chead { margin-bottom: 2mm; }
.cnum { color: #E85D3D; font-weight: bold; font-size: 9pt; margin-right: 2mm; }
.chunk.core .cnum { color: #B7791F; }
.ctitle { font-size: 12.5pt; font-weight: bold; color: #0F172A; margin-right: 2mm; }
.pill { display: inline-block; color: #fff; font-size: 7.5pt; padding: 0.6mm 2.2mm; border-radius: 2mm; vertical-align: middle; }
.corebadge { display: inline-block; color: #92400E; background: #FDE68A; font-size: 7.5pt; font-weight: bold; padding: 0.6mm 2.2mm; border-radius: 2mm; vertical-align: middle; }
.field { margin: 1.1mm 0; }
.flabel { display: inline-block; width: 19mm; color: #142F4A; font-weight: bold; font-size: 8.5pt; vertical-align: top; }
.meaning { font-size: 10pt; color: #0F172A; }
.exbox { display: inline-block; width: calc(100% - 20mm); background: #F1F5F9; border-left: 2.5pt solid #142F4A; padding: 2mm 3mm; box-sizing: border-box; vertical-align: top; }
.ex { margin: 0.8mm 0; }
.scene { display: inline-block; background: #142F4A; color: #fff; font-size: 7.5pt; padding: 0.4mm 1.8mm; border-radius: 1.5mm; margin-right: 1.5mm; }
.alts { display: inline-block; width: calc(100% - 20mm); margin: 0; padding-left: 5mm; vertical-align: top; }
.alts li { margin: 0.6mm 0; }
.pron { font-family: "DejaVu Sans", "Noto Sans CJK SC", sans-serif; }
table.core { width: 100%; border-collapse: collapse; font-size: 8.8pt; line-height: 1.45; margin: 4mm 0; }
thead { display: table-header-group; }
table.core th { background: #142F4A; color: #fff; padding: 2mm; text-align: left; }
table.core td { border-bottom: 0.5pt solid #CBD5E1; padding: 2mm; vertical-align: top; }
table.core tr.roundrow td { background: #FEF3C7; font-weight: bold; color: #92400E; }
table.core td.cn { color: #E85D3D; font-weight: bold; white-space: nowrap; }
table.core td.ce { font-weight: bold; color: #0F172A; }
table.core tr { break-inside: avoid; }
ul { margin: 2mm 0 2mm 6mm; padding-left: 5mm; }
li { margin: 1mm 0; }
strong { color: #0F172A; }
p { margin: 2.5mm 0; text-align: justify; }
.legend td { padding: 1.5mm 2mm; }
"""

cover = f"""<div class="cover">
<div class="band"><div class="kicker">AMERICAN ENGLISH SPEAKING CHUNKS · B2-C1</div>
<h1>美式英语口语表达库</h1>
<div class="sub">说得出口的 120 个 chunks · 播客 / 采访 / 演讲 / 会议 / 日常深度交流</div>
<div class="tagline">不只背单词，要背可以直接说出口的整块表达。</div></div>
<div class="rule"></div>
<table class="meta">
<tr><th>收录</th><td>120 个表达 · 第 1–3 轮 · 每轮 5 个主题 × 8 个表达</td></tr>
<tr><th>主题</th><td>商务职场、AI / 科技、情感表达、播客主持、会议谈判、日常交流、采访提问、公开演讲、社交闲聊、远程协作、深度对话、个人成长、职场反馈、播客转场与追问、会议主持与总结</td></tr>
<tr><th>水平与语言</th><td>B2–C1 · 中英双语 · 全部美式英语（美式拼写、美式用词、美式发音）</td></tr>
<tr><th>每条结构</th><td>英文 chunk / 中文意思 / 正式度 / 2 句美式例句 / 可替换说法 / 发音提示 / 使用提醒 / 迷你练习</td></tr>
<tr><th>原稿</th><td>American_English_Speaking_Chunks.md · 编号 #001–#120 与原稿顺序一致</td></tr>
<tr><th>日期</th><td>2026 年 10 月 28 日</td></tr>
</table>
<div class="stats"><b>120</b> chunks &nbsp;·&nbsp; <b>15</b> 个主题 &nbsp;·&nbsp; <b>30</b> 个最值得背 &nbsp;·&nbsp; <b>3</b> 轮</div>
<div class="notice"><b>怎么读这本书：</b>先读第 2 页的用法说明和第 3 页的 30 个最值得背一览，再按主题练。金色边框 + ★ 的是每轮最值得背的 10 个，先把这 30 个练到脱口而出，再扩到全部 120 个。</div>
<div class="foot">个人学习资料 · American English Speaking Chunks · 美式英语口语教练合集</div>
</div>"""

howto = """<div class="front"><h2 id="howto">如何使用这本书</h2>
<h3>1. 一条卡片怎么读</h3>
<p>每条卡片就是一个可以直接说出口的单位，不是单词表。先大声读英文 chunk，再看中文意思确认理解，然后跟读两句例句，最后做迷你练习把它变成自己的话。不要只用眼睛看，用嘴说出来才算学过。</p>
<table class="core legend"><thead><tr><th>卡片位置</th><th>怎么用</th></tr></thead>
<tbody>
<tr><td><b>英文 chunk + 编号</b></td><td>背诵单位。编号 #001–#120 全书唯一，方便和原稿 Markdown 对照、打卡。</td></tr>
<tr><td><b>正式度</b></td><td>决定场合。见下方图例，不要在正式谈判里用 casual，也不要在朋友闲聊里全程用 formal。</td></tr>
<tr><td><b>美式例句</b></td><td>每条 2 句，其中 1 句带场景标签，如 [播客] [会议] [谈判] [采访]，照着场景练。</td></tr>
<tr><td><b>可替换说法</b></td><td>同一意思的更随意 / 更正式 / 更强情绪版本，换着说才不会只会一句话。</td></tr>
<tr><td><b>发音提示</b></td><td>美式 IPA、重音、连读、弱读、语调。/ / 内是美式发音，例如 schedule 读 /ˈskedʒuːl/。</td></tr>
<tr><td><b>使用提醒</b></td><td>适合谁、什么场合、怎么误用。很多表达的问题不在语法，而在场合。</td></tr>
<tr><td><b>迷你练习</b></td><td>填空、跟读或角色扮演。练的时候录音回听一次，比默读三遍有效。</td></tr>
</tbody></table>
<h3>2. 正式度图例</h3>
<p><span class="pill" style="background:#0F766E">casual</span> 朋友、闲聊 &nbsp; <span class="pill" style="background:#475569">neutral</span> 日常 + 职场通用 &nbsp; <span class="pill" style="background:#142F4A">professional</span> 会议、谈判、演讲 &nbsp; <span class="pill" style="background:#7C2D12">formal</span> 正式场合。卡片上出现 “neutral / professional” 表示两者都可用，选更贴近你场景的那一端。</p>
<h3>3. 建议的学习节奏</h3>
<p>每天 1 个主题（8 条），不要一天贪多。每轮附的 7 天复习计划在每轮末尾：跟读日、场景日、混合闪卡日、综合录音日。坚持一个原则：能脱口而出 30 个核心，再扩到 120 个；能用在真实对话里，才算掌握。</p>
<p>本 PDF 由原稿 Markdown 全文生成，未删减任何条目。后续说“继续”追加第 4 轮时，重新生成即可得到新版全本，编号顺延。</p>
</div>"""

core30 = f"""<div class="front"><h2 id="core30">30 个最值得背一览</h2>
<p>每轮最值得背的 10 个，共 30 个。先背这张表，再按主题读卡片。编号与正文卡片一致，查表后可直接翻到对应卡片看例句、发音和练习。</p>
<table class="core"><thead><tr><th>编号</th><th>英文 chunk</th><th>中文意思</th><th>主题</th></tr></thead>
<tbody>{core_rows}</tbody></table>
</div>"""

toc = f'<div class="toc"><h2 class="tt">目　录</h2><ul>{toc_items}</ul></div>'

doc = (f"<!doctype html><html><head><meta charset='utf-8'>"
       f"<title>美式英语口语表达库 · 120 chunks</title><style>{CSS}</style></head>"
       f"<body>{cover}{howto}{core30}{toc}{body_html}</body></html>")

from weasyprint import HTML
HTML(string=doc).write_pdf(str(OUT))
print(f"wrote {OUT}")
