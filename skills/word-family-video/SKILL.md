---
name: word-family-video
description: >
  把 word-family 生成的词族课（lessons/<词根>.json）做成 5 分钟以内的讲解视频：静态线稿逐笔画出、
  元素按解说依次出场、版式轮换、免费 TTS 配音、字幕内嵌，超时自动按重要性删减。
  Use when 用户想把某一课词根词缀做成视频、讲解视频、短视频。
  触发词：词根视频, 词族视频, 讲解视频, 生成视频, word family video。
compatibility: Python 3.10+ with numpy; edge-tts (free, needs network); ffmpeg; Python Playwright using local Chrome/Edge. Optional Pillow, faster-whisper (large-v3-turbo, ~1.6 GB download on first check). Requires the word-family skill.
metadata:
  platforms: claude-code
---

# 词族讲解视频

你的任务：把一课已经做好的词族课，做成一支 5 分钟以内的讲解视频，输出 `projects/<词根>/<词根>.mp4`。

**你只需要写解说词。** 画面、版式、动画、字幕、时长控制都由 `scripts/video.py` 自动完成，不要去改坐标或模板。

本文件所在目录记为 `$SKILL`。开工前先读 `$SKILL/references/narration_guide.md`（**必读**）。
完整样例：`$SKILL/projects/tract/narration.json`。

## 工作流程

### 0. 确认课程存在

课程来自 word-family skill 的 `lessons/<词根>.json`。没有的话，先用 word-family 做课；它的 `build.py` 必须零错误。
（`video.py` 自动在同级目录或 `~/.claude/skills/word-family` 找 word-family；都不在时设置环境变量 `WORD_FAMILY_DIR`。）

### 1. 生成解说词草稿

```bash
python -I "$SKILL/scripts/video.py" init <词根>
```

生成 `projects/<词根>/narration.json`。已存在时不会覆盖。

### 2. 改写解说词

按 `narration_guide.md` 第二节逐条改写：一句一件事、先画面后词义、每个词至少一个「这不就是……吗？」、过渡句承接方向。
**一定要排 `order`**：最常用、最重要的词在前，超时会从后往前删。

### 3. 看时长和提醒

```bash
python -I "$SKILL/scripts/video.py" plan <词根>
```

它会配音（免费，有缓存）、量真实时长、超时自动删减，然后列出每个单元的时长：

- `[删减]`：删了什么。删了主词的，检查它后一张卡的过渡句是否还接得上，接不上就改。
- `[提醒]`：句子太长、缺少某段解说等。逐条改掉，再运行 `plan`，直到没有提醒。

### 4. 看画面

```bash
python -I "$SKILL/scripts/video.py" stills <词根>
```

每个单元出一张定格图（`projects/<词根>/stills/`，总览 `_sheet.jpg`）。画面问题（人物和文字重叠等）属于课程本身，回 word-family 改课程 JSON、重新 `build.py`，再回来。

### 5. 渲染

```bash
python -I "$SKILL/scripts/video.py" render <词根>
```

约 1–2 分钟。超过 5 分钟时拒绝渲染（回到第 2 步缩短）。

### 6. 读音检查（可选，推荐）

```bash
python -I "$SKILL/scripts/video.py" check <词根>
```

列出可能读错的英文词：两遍识别（第二遍把没对上的词作为热词）都没对上的报「可能读错」，只有第二遍才对上的报「读得可能不够清楚」。短于 4 个字母的词不查。报出来的仍可能是 Whisper 听错。你听不到声音，所以：转写和原词明显不是同一个词的（如 pending 被听成「偏顶」），在 narration.json 的 `say_as` 里加替换后重新 `render` 再 `check`；拿不准的，交付时把这些词和所在句子列给用户，请用户试听确认。

### 7. 交付

告诉用户：视频路径、时长、讲了几个主词；删减了什么（如果有）；没处理的提醒和理由（如果有）。

## 不要做的事

- 不要改 `assets/frame.html` 和 word-family 的零件库来「修」某一课的画面——改课程 JSON。
- 不要为了塞进 5 分钟而加快语速；删内容。
- 不要在解说词里念括号、符号、词性缩写（v.、adj.）。
