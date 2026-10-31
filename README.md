# markdown-to-pdf-styles

🌐 [English version](README_EN.md)

把 Markdown 转成 PDF 的样式库：先选样式，再生成。同一份 Markdown
进来，出来的是完全不同的书。

第一版的 7 个样式是围绕一个示例做的——美式英语口语表达库
（3 轮、120 条、B2–C1、中英双语，编号 #001–#120），这样你能在
同一份内容上直观看到每个样式的效果。示例在 `examples/` 里；
样式本身才是这个项目，不是示例。当前样式要求什么样的输入格式，
见 `SPEC.md`，里面也老实写了局限：它们目前只认这个示例的
结构，把它们通用化到任意 Markdown 是后续工作，不是这一版声称
已经做到的事。

## 7 个样式

| 样式 | 文件 | 适用场景 | 样子 |
|---|---|---|---|
| formal | `styles/formal.py` | 正式交付、存档 | 藏青封面、信息表、带引导点的目录、每条一张卡片、金色核心边框 |
| muse | `styles/muse.py` | 口语练习、打勾过关 | 暖米纸面、衬线英文、橙色点缀、带打勾框的圆角练习卡 |
| grid | `styles/grid.py` | 查阅、打印进笔记本 | 白纸面、只用无衬线、黑线、只用亮蓝、英文在前中文作注释、字母索引、120 行打卡表 |
| playbook | `styles/playbook.py` | 玩着练，不是死记 | 包豪斯几何（红圆、黄半圆、蓝方块、黑条）、SAY / MEAN / EXAMPLE / SWAP / SOUND / WATCH / PLAY 短标签、自选 10 句、30 天挑战格 |
| script | `styles/script.py` | 大声排练台词 | 打字机等宽字体、只用黑 + 丝带红、剧本标题页（FADE IN）、LINE / MEANS / DIALOGUE / ALT TAKE / DIRECTOR'S NOTE / WATCH OUT / REHEARSE、场景列表、排练记录 |
| editorial | `styles/editorial.py` | 像杂志一样读 | 衬线刊头 SPEAK、只用深绿、标题 / 导语 / 金句 / 边栏 / 提示 / 注意 / TRY THIS、编辑来信、封面故事、笔记页 |
| night | `styles/night.py` | 晚上在屏幕上读 | 深色页面、浅色字、只用琥珀色、SAY IT AFTER DARK 封面、夜间规则、夜间精选、10 点前睡觉、夜间练习记录。**只适合屏幕，不适合打印**——深色页面很费墨 |

封面预览在 `gallery/` 里（`cover-<样式>.png`）。

## 生成效果截图

这些是 `build_all.py` 从 `examples/American_English_Speaking_Chunks.md`
生成的 PDF 里截的真实页面（130 dpi，不是示意图）。每行同时展示
该样式的封面和一张内页正文卡片，动手建之前就能先判断排版合不合意。

| 样式 | 封面 | 内页 |
|---|---|---|
| formal | ![formal cover](gallery/cover-formal.png) | ![formal interior, p. 20](gallery/page-formal.png) |
| muse | ![muse cover](gallery/cover-muse.png) | ![muse interior, p. 20](gallery/page-muse.png) |
| grid | ![grid cover](gallery/cover-grid.png) | ![grid interior, p. 15](gallery/page-grid.png) |
| playbook | ![playbook cover](gallery/cover-playbook.png) | ![playbook interior, p. 8](gallery/page-playbook.png) |
| script | ![script cover](gallery/cover-script.png) | ![script interior, p. 8](gallery/page-script.png) |
| editorial | ![editorial cover](gallery/cover-editorial.png) | ![editorial interior, p. 8](gallery/page-editorial.png) |
| night | ![night cover](gallery/cover-night.png) | ![night interior, p. 8](gallery/page-night.png) |

所有截图都在 `gallery/` 里（封面是 `cover-<样式>.png`，内页是
`page-<样式>.png`）。生成的 PDF 本身不入仓——见 `AGENTS.md`——
用 `python build_all.py` 就能重建。

## 快速开始

```bash
pip install -r requirements.txt
# 生成一个样式：
python styles/night.py examples/American_English_Speaking_Chunks.md -o output/night.pdf
# 或者全部 7 个：
python build_all.py
# 或者通过驱动脚本生成一个样式：
python build_all.py --style playbook
```

每个样式脚本也可以单独运行：

```bash
python styles/<style>.py [input.md] [-o output.pdf]
```

不带参数时默认读取
`examples/American_English_Speaking_Chunks.md`，写到
`output/<style>.pdf`。

## 环境要求

- Python 3.12（已用 WeasyPrint 70 测过；见 `requirements.txt`）
- 字体：Noto Sans CJK / Noto Serif CJK 和 Liberation 系列。
  Debian/Ubuntu 上：`fonts-noto-cjk`、`fonts-liberation`。
  没有中文字体的话，中文会渲染不出来。
- 渲染器特意用 WeasyPrint：Chrome 无头打印在每个环境下不一定
  可靠，而 WeasyPrint 能通过 `target-counter` 在目录里给出真实页码。

## 输入格式

输入是一份结构如下的 Markdown 文件（见 `examples/`）：

```markdown
## 第 1 轮总览
- 主题：商务职场、AI / 科技……
- 场景：播客、采访……
- 本轮 10 个最值得背的 chunk：Let's unpack that; Walk us through it; ……

## 第 1 轮 · 主题 1：商务职场 Business & Workplace

### 1. circle back on this
- 英文 chunk：circle back on this
- 中文意思：晚点再回头讨论这件事
- 正式度：professional
- 美式例句：(1) Let's circle back on this after we get the data. (2) [会议] I know we're short on time, so let's circle back on this on Thursday.
- 可替换说法：更随意：let's revisit this later / 更正式：……
- 美式发音与流利度提示：……
- 使用提醒：……
- 迷你练习：……

## 第 1 轮 · 7 天复习 / 练习计划
- Day 1：……
```

每条 chunk 都会按原文顺序完整渲染，编号从文件顺序得来，
#001……。每轮总览里的“最值得背”清单会回查到对应的 chunk，
在正文和前面的 30 句核心区用 ★（或该样式的等价标记）标出来。

### 当前局限（老实写，不藏着）

当前脚本要求示例的结构：3 轮、120 条、每轮一个 10 条核心清单。
它们会校验这些数量，形状不对会直接失败，而不是悄悄产出一本
错的书。把解析器通用化到任意条数是下一个 TODO；第一版公开版
还没有做。

## 可复现性——同一份 Markdown，在哪都出同一本书

这是硬性要求，不是锦上添花：任何人——包括一个没有任何先前
上下文的 AI 智能体——克隆这个仓库、拿同一份 Markdown 文件，
都必须能产出同样的 PDF。

- **先读 `SPEC.md`。** 它钉死了准确的环境（Python 3.12、
  WeasyPrint 70.0、中日韩 + Liberation 字体）、exact 输入格式，
  以及每个样式的预期页数。
- **如果你是来复现的智能体，读 `AGENTS.md`**：那是一份 5 步
  清单，里面写明校验不过时要停下来汇报，而不是交一本不一样
  的书。
- **建完要校验：** `python verify.py`（需要 PyMuPDF，
  `pip install pymupdf`）。它检查每份 PDF 的页数和 #001–#120
  是否齐全。
- **还可能不一样的地方：** PDF 元数据（生成日期等），所以两次
  运行的文件不会逐字节相同。但版式、页数、chunk 顺序、编号和
  目录页码必须一致。如果页数差了哪怕一页，说明字体或输入形状
  变了——见 `SPEC.md` 第 6 节。
- **这个仓库不依赖什么：** 不依赖 Chrome、不依赖个人工作区
  路径、不依赖某个智能体的专属工具。所有默认路径都相对于
  仓库根目录。唯一的外部要求就是上面列的钉死版本的 Python 包
  和系统字体。

## 仓库结构

```
.
├── README.md
├── README_EN.md            # 英文版介绍
├── LICENSE
├── requirements.txt
├── build_all.py          # 驱动脚本：生成一个或全部样式
├── styles/
│   ├── formal.py
│   ├── muse.py
│   ├── grid.py
│   ├── playbook.py
│   ├── script.py
│   ├── editorial.py
│   └── night.py
├── examples/
│   └── American_English_Speaking_Chunks.md   # 示例输入（120 条）
├── gallery/
│   ├── cover-<style>.png  # 封面预览
│   └── page-<style>.png   # 内页截图
└── output/               # 生成的 PDF 放这里（gitignored）
```

生成的 PDF 特意**不提交**：中文字体让每份有 4–5 MB，而且
任何人用上面的一条命令就能重建。gallery 里的封面和内页截图
就是展示用的。

## 许可证

MIT。见 `LICENSE`。
