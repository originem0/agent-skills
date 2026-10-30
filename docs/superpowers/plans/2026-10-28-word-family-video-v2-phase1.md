# word-family-video v2 第一期（脚本层）Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 让每支词族视频先有一份节拍脚本 `script.md`：可解析、可自动检查、可由另一家 AI 审稿、有审核状态门槛，并产出时间轴和试听音频；用新流程写出 tract、pend 两份经 AI 审稿的脚本，交用户审（检查点 1）。

**Architecture:** 新模块 `scripts/script_md.py`（只用标准库）负责脚本的解析、校验、检查、指纹与审核状态；`scripts/video.py` 增加 `brief / plan / review / mark / photo / status` 六个命令，`plan` 在有 `script.md` 时走新路径：按句配音（带逐词时间戳）→ 排时间轴 `build/timeline.json` → 混出 `build/preview.mp3`；`photo` 复用 word-family `photo.py` 给任意节拍取真实图片。v1 的 `narration.json` 渲染路径本期保持原样（配音会话仍在用），第二期把渲染接到 timeline 后再删。

**Tech Stack:** Python 3.10+ 标准库 + numpy、edge-tts 7.x（`boundary="WordBoundary"`）、ffmpeg；Codex CLI（可选审稿方）；Claude Code 子代理（批量写稿、Codex 不可用时审稿）。

**Spec:** `docs/superpowers/specs/2026-10-28-word-family-video-v2-design.md`（§3 流程、§4 写稿方法、§5 格式、§6 时间轴、§8 中 word-family 部分、§9 中脚本层部分、§10 第一期）

**本计划只覆盖第一期。**

> **执行约定（用户 2026-10-28 决定，优先于下文）**：本会话直接执行（executing-plans）；**不提交 git、不建 worktree**，直接在主目录 `D:/Development/Automation/agent-skills` 里改，所有"提交"步骤跳过，改动留在工作区由用户决定何时提交。主目录与配音会话共用：开工前的对齐消息里写明这一点；每次改 `video.py`、`SKILL.md` 之前先 `git diff --stat` 看对方有没有新改动，有就先读懂再改。下文的 `$WT` 一律指主目录。
>
> **执行中的两处变更（用户中途决定，详见台账 Ruling）**：① AI 审稿改为用户可选、由用户发起，不调用 Codex，状态只剩 draft / approved（Task 5b 返工）；② 端到端测试改用一课全新的 cap/cip/cept（先用 word-family 做课），不再重写 tract、pend（Task 9）。下文 Task 8、9 已按此改写。 第二期（画面层）和第三期（收尾）在检查点 1 之后另写计划：检查点 1 的反馈可能改变画面块的细节。与 spec 的一处调整：spec §10 把 evals 放在第三期，本计划把 evals 随 `SKILL.md` 一起在 Task 8 改掉——否则第一期结束时 evals 与流程互相矛盾；evals 的基线记录仍留在第三期。

## Global Constraints

- 只用现有依赖：Python 3.10+ 标准库 + numpy、edge-tts、ffmpeg、Playwright；不新增 pip/npm 依赖。Codex CLI 是可选审稿方（本机已装 `codex-cli 0.163.0`），失败时退回独立的 Claude 子代理。
- 所有脚本用 `python -I` 运行；`-I` 不会把脚本所在目录放进 `sys.path`，同目录模块要手动 `sys.path.insert(0, 脚本目录)`。
- 配音默认值归配音会话维护，不改：`VOICE = "zh-CN-YunjianNeural"`、`RATE = "+20%"`、`PRE, LEAD, GAP_LINE, GAP_UNIT, TAIL = 0.35, 0.6, 0.2, 0.45, 1.5`；`cmd_check` 及其辅助函数不改。
- 时长：目标 ≤ 4:50（`TARGET = 290`），硬上限 5:00（`HARD_MAX = 300`）；超时不自动删减，由写稿方删节拍并写进 `skip`。
- 套话：「这不就是……吗」全片最多 1 次；以「吗？」结尾的反问最多 2 句；不用"下面我们来看""接下来是"一类转场套话；一行不超过 40 字。
- 事实：年份、日期、数字、引语、事件必须在所在节拍写 `> 来源：URL（日期）`；词源只来自课程 JSON 或 word-family 的 `etym.py`。
- 写稿子代理 `model: "opus"`（本环境只有 Opus 可用），最多同时 3 个。
- word-family 的课程 JSON（`skills/word-family/lessons/*.json`）不改。
- 用户可见文字（提示、报错、文档）用中文；报错带行号和改法；注释只写"为什么"。
- 在 git worktree（分支 `wfv-v2`）里做；主目录有另一个会话在 `main` 上提交。每个任务结束提交一次，提交信息结尾加 `Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>`。

## Review Focus

- 用户用记事本保存的脚本带 BOM、CRLF 换行：解析结果必须和 LF 文件完全一样（Task 1 `test_parse_bom_crlf`）。
- 全角冒号混用（`lesson：pend`、`> 来源:https://…`、`[word：suspend]`）：一律接受（Task 1 `test_fullwidth_colons`）。
- Codex 没装、超时或输出为空：`review` 返回 2 并给出改派 Claude 子代理的具体做法，不写半截 `review.md`（Task 5 `test_run_codex_missing`、`test_review_fallback_keeps_no_record`）。
- 第二轮审稿不能冲掉第一轮的处理结果，`mark reviewed` 只看最新一轮（Task 3 `test_review_done_multi_round`、Task 5 `test_append_review_rounds`）。
- `say_as` 改了触发词的字母（live 念成 laiv）：触发点仍要按逐词时间戳对上，不能退化成按字数估算（Task 4 `test_cue_time_say_as`）。

---

## 开工前

- [ ] **建 worktree**：用 superpowers:using-git-worktrees 从当前 `main` 建分支 `wfv-v2` 的 worktree（下文记为 `$WT`）。先确认 `docs/superpowers/specs/2026-10-28-word-family-video-v2-design.md` 和本计划已提交到 `main`（用户同意后），否则 worktree 里没有它们。以下命令都在 `$WT` 根目录运行。
- [ ] **和配音会话对齐**：`ListAgents` 找到 `agent-skills-be`（6b52606、4c20fa6、8727f62 三个配音 commit 的作者；找不到或不确定就问用户），用 `SendMessage` 发：

  ```text
  word-family-video v2 改造（ryan-analysis 会话）开工前对齐：我在 worktree 分支 wfv-v2 里改 skills/word-family-video，和你的配音/读音工作有三个交接点。
  1) synth_all 合成时加 edge-tts boundary="WordBoundary"，用 save(音频, 元数据) 把逐词时间戳存成同名 .words.jsonl；新增参数 marks=False，现有调用不受影响，音频和缓存键不变。
  2) 本期 render / stills / check 仍读 narration.json，cmd_check 不动；第二期改成从 script.md 取句子时再找你确认。
  3) narration_guide.md 的「读音」一节第二期并入新的 script_guide.md，内容原样保留。
  设计文档：docs/superpowers/specs/2026-10-28-word-family-video-v2-design.md。你那边如果正在改 video.py 的 synth_all / main，或有没提交的改动，回个消息，我等你提交后再合并。
  ```

  不必等回复再开工；若对方回复有冲突，在 Task 4 动 `synth_all` 之前先合并对方的提交。

---

### Task 1: script.md 解析

**Files:**
- Create: `skills/word-family-video/scripts/script_md.py`
- Test: `skills/word-family-video/scripts/test_script.py`

**Interfaces:**
- Produces（后续任务都用）：
  - `parse(text: str) -> Script`
  - `Script(meta: dict, beats: list[Beat], annotations: list[tuple[int, str]], errors: list[str], text: str)`，属性 `status -> str`（缺省 `"draft"`），方法 `spoken() -> list[Line]`
  - `Beat(title: str, block: str, arg: str, lineno: int, data: list[tuple[str, str, int]], lines: list[Line])`，方法 `get(key) -> list[str]`；标题格式错误的节拍 `block == "?"`
  - `Line(text: str, lineno: int, pause_before: bool)`，属性 `plain -> str`（去掉花括号）、`cues -> list[str]`
  - `say_as(meta) -> dict[str, str]`、`skipped(meta) -> dict[str, str]`（键为小写单词）、`wlen(s) -> float`、常量 `BLOCKS`、`STATUSES`、`CUE_RE`

- [ ] **Step 1: 写失败的测试**

创建 `skills/word-family-video/scripts/test_script.py`：

```python
"""script_md / video 的单元测试。运行：python -I skills/word-family-video/scripts/test_script.py"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))   # python -I 不把脚本所在目录放进 sys.path
import script_md as smd  # noqa: E402

# 缩小版的 pend 课程：只留测试要用的字段
L = {
    "title": "从吊坠开始：pend「挂」一家",
    "root": {"m": "pend", "cn": "挂"},
    "opening": {"type": "pair", "big": "depend 依靠 · spend 花钱", "say": "八竿子打不着", "scene": [{"k": "line"}]},
    "anchor": {"text": "记住这个画面：一根绳，下面挂着一样东西。", "scene": [{"k": "fig"}]},
    "words": [
        {"w": "depend", "split": ["de", "pend"], "parts": [["de-", "从……往下"], ["pend", "挂"]],
         "literal": "从上面往下吊着", "meaning": "v. 依靠", "fact": "拉丁语 dependere；约 1500 年起", "scene": [{"k": "fig"}]},
        {"w": "suspend", "split": ["sus", "pend"], "parts": [{"m": "sus-", "cn": "从下往上", "of": "sub-"}, ["pend", "挂"]],
         "literal": "吊到半空", "meaning": "v. 暂停", "fact": "英语「暂停」义 1570 年代起", "scene": [{"k": "fig"}]},
    ],
    "finale": {"w": "spend", "split": ["s", "pend"], "parts": [{"m": "s-", "cn": "往外", "of": "ex-", "how": "缩略"}, ["pend", "称"]],
               "literal": "把铜块称出去", "meaning": "v. 花（钱）", "fact": "拉丁语 expendere 的缩短", "scene": [{"k": "fig"}]},
    "transfer": [["pending = pend + -ing", "还挂着，没落地"], ["pension = pens + -ion", "养老金"]],
}

GOOD = """---
lesson: pend
spine: 演变——挂 → 称 → 付钱
skip: depend（时长不够）
say_as: live → laiv；or → O R
---

## 开场 [pair: depend | spend]
为什么 {depend} 是依靠，{spend} 却是花钱？

可它们其实是一家。

## 一场停摆 [event]
> 事件：NBA 官方声明 · 2020-03-11
> 原文：The NBA is {suspending} game play.
> 来源：https://official.nba.com/nba-to-suspend-season-following-tonights-games/
2020 年 3 月 11 日晚上，NBA 发出一份声明。
最要紧的是这个词：{suspending}。

## suspend [word: suspend]
{sub}，从底下往上；碰到 p，常写成 {sus}。
{pend}，挂。把事情吊起来，就是 {suspend}。
>> 这里能不能再加一个生活里的例子？

## 第二幕 · 称 [title]
"""


def test_parse_structure():
    sc = smd.parse(GOOD)
    assert sc.errors == [], sc.errors
    assert sc.meta["lesson"] == "pend" and sc.meta["spine"].startswith("演变")
    assert [b.block for b in sc.beats] == ["pair", "event", "word", "title"]
    assert (sc.beats[0].arg, sc.beats[2].arg, sc.beats[3].arg) == ("depend | spend", "suspend", "")
    assert [ln.pause_before for ln in sc.beats[0].lines] == [False, True]
    assert sc.beats[1].get("来源") == ["https://official.nba.com/nba-to-suspend-season-following-tonights-games/"]
    assert sc.beats[2].lines[0].cues == ["sub", "sus"]
    assert sc.beats[2].lines[1].plain == "pend，挂。把事情吊起来，就是 suspend。"
    assert sc.annotations == [(23, "这里能不能再加一个生活里的例子？")]
    assert sc.status == "draft"


def test_meta_items():
    sc = smd.parse(GOOD)
    assert smd.say_as(sc.meta) == {"live": "laiv", "or": "O R"}
    assert smd.skipped(sc.meta) == {"depend": "时长不够"}


def test_parse_bom_crlf():
    # 记事本另存的文件带 BOM、CRLF：解析结果必须一样
    sc = smd.parse("\ufeff" + GOOD.replace("\n", "\r\n"))
    assert sc.errors == [], sc.errors
    assert sc.meta["lesson"] == "pend" and len(sc.beats) == 4


def test_fullwidth_colons():
    sc = smd.parse("---\nlesson：pend\nspine：方向\n---\n\n## x [word：suspend]\n> 来源:https://a.b\n{sus}。\n")
    assert sc.errors == [], sc.errors
    assert sc.meta["lesson"] == "pend"
    assert (sc.beats[0].block, sc.beats[0].arg) == ("word", "suspend")
    assert sc.beats[0].get("来源") == ["https://a.b"]


def test_parse_errors():
    cases = {
        "## 开场 [title]\n": "第 1 行",                                      # 没有文件头
        "---\nlesson: pend\n---\n## 开场\n": "节拍标题",                       # 标题后面没写画面块
        "---\nlesson: pend\n---\n正文\n## a [title]\n": "第一个 ## 节拍之前",
        "---\nlesson: pend\n---\n## a [word: suspend]\n{sub，从底下\n": "花括号",
        "---\nlesson: pend\n---\n## a [event]\n> 没有冒号\n": "> 键：值",
        "---\nlesson: pend\n": "缺少结束的 ---",
    }
    for text, want in cases.items():
        errs = smd.parse(text).errors
        assert any(want in e for e in errs), (text, errs)


if __name__ == "__main__":
    fails = 0
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print("PASS", name)
            except Exception as e:  # noqa: BLE001  测试脚本：任何异常都算这条失败
                fails += 1
                print("FAIL", name, "-", type(e).__name__, e)
    print("\n全部通过" if not fails else f"\n{fails} 个失败")
    sys.exit(1 if fails else 0)
```

以后各任务追加的测试，一律插在 `if __name__ == "__main__":` 这一块的**上面**。

- [ ] **Step 2: 运行，确认失败**

Run: `python -I skills/word-family-video/scripts/test_script.py`
Expected: `ModuleNotFoundError: No module named 'script_md'`

- [ ] **Step 3: 实现解析**

创建 `skills/word-family-video/scripts/script_md.py`：

```python
"""script.md：视频脚本的解析、校验、检查和审核状态。

格式和写法见 references/script_guide.md。只依赖标准库；课程（word-family 的 lesson JSON）以 dict 传入，方便单测。
"""
import re
from dataclasses import dataclass, field

BLOCKS = ("title", "scene", "photo", "word", "event", "pair", "map", "quiz")
STATUSES = ("draft", "reviewed", "approved")
CUE_RE = re.compile(r"\{([^{}]+)\}")
HEAD_RE = re.compile(r"^##\s+(?P<title>.+?)\s*\[(?P<block>[A-Za-z]+)(?:\s*[:：]\s*(?P<arg>[^\]]*))?\]\s*$")
DATA_RE = re.compile(r"^>\s*(?P<key>[^：:]+?)\s*[：:]\s*(?P<val>.*)$")
META_RE = re.compile(r"^\s*(?P<key>[A-Za-z_]+)\s*[：:]\s*(?P<val>.*)$")


def wlen(s: str) -> float:
    """显示宽度：英文字母、数字、空格按半个汉字算。"""
    return sum(0.55 if ord(ch) < 128 else 1 for ch in s)


@dataclass
class Line:
    text: str                     # 原文，含 {触发词}
    lineno: int
    pause_before: bool = False    # 和上一句之间有空行：段落停顿

    @property
    def plain(self) -> str:
        """配音和字幕用的文字：去掉花括号。"""
        return CUE_RE.sub(r"\1", self.text)

    @property
    def cues(self) -> list:
        return [c.strip() for c in CUE_RE.findall(self.text)]


@dataclass
class Beat:
    title: str
    block: str
    arg: str
    lineno: int
    data: list = field(default_factory=list)     # [(键, 值, 行号)]
    lines: list = field(default_factory=list)

    def get(self, key: str) -> list:
        return [v for k, v, _ in self.data if k == key]


@dataclass
class Script:
    meta: dict
    beats: list
    annotations: list     # [(行号, 批注)]
    errors: list          # 解析阶段发现的错误
    text: str             # 去掉 BOM、换行统一成 \n 之后的全文

    @property
    def status(self) -> str:
        return self.meta.get("status") or "draft"

    def spoken(self) -> list:
        return [ln for b in self.beats for ln in b.lines]


def parse(text: str) -> Script:
    # 记事本另存的文件带 BOM、CRLF：先统一，否则第一行的 --- 认不出来
    text = text.lstrip("\ufeff").replace("\r\n", "\n")
    rows = text.split("\n")
    meta, beats, notes, errs = {}, [], [], []
    i = 0
    if rows[0].strip() != "---":
        errs.append("第 1 行：文件要以 --- 开始，先写文件头（lesson、spine 等），再用一行 --- 结束")
    else:
        i = 1
        while i < len(rows) and rows[i].strip() != "---":
            m = META_RE.match(rows[i])
            if m:
                meta[m["key"]] = m["val"].strip()
            elif rows[i].strip():
                errs.append(f"第 {i + 1} 行：文件头每行写成「键: 值」")
            i += 1
        if i >= len(rows):
            errs.append("文件头缺少结束的 ---")
        i += 1
    pause = False
    for n in range(i, len(rows)):
        s, ln = rows[n].strip(), n + 1
        if not s:
            pause = bool(beats and beats[-1].lines)     # 节拍开头的空行不算停顿
            continue
        if s.startswith(">>"):
            notes.append((ln, s[2:].strip()))
            continue
        if s.startswith("#"):
            m = HEAD_RE.match(s)
            if m:
                beats.append(Beat(m["title"], m["block"].lower(), (m["arg"] or "").strip(), ln))
            else:
                errs.append(f"第 {ln} 行：节拍标题写成「## 标题 [画面块]」或「## 标题 [画面块: 参数]」，"
                            f"例如 ## suspend [word: suspend]")
                beats.append(Beat(s.lstrip("#").strip(), "?", "", ln))
            pause = False
            continue
        if not beats:
            errs.append(f"第 {ln} 行：第一个 ## 节拍之前不能有正文")
            continue
        if s.startswith(">"):
            m = DATA_RE.match(s)
            if m:
                beats[-1].data.append((m["key"].strip(), m["val"].strip(), ln))
            else:
                errs.append(f"第 {ln} 行：> 开头的行写成「> 键：值」，例如 > 来源：https://…")
            continue
        if s.count("{") != s.count("}") or "{}" in s:
            errs.append(f"第 {ln} 行：花括号没有配对：{s[:30]}")
        beats[-1].lines.append(Line(s, ln, pause))
        pause = False
    return Script(meta, beats, notes, errs, text)


def _items(s: str) -> list:
    return [p.strip() for p in re.split(r"[；;]", s or "") if p.strip()]


def say_as(meta: dict) -> dict:
    """文件头 say_as：「live → laiv；or → O R」→ {原词: 念法}。只改配音，字幕不变。"""
    out = {}
    for p in _items(meta.get("say_as")):
        m = re.match(r"(.+?)\s*(?:→|->)\s*(.+)$", p)
        if m:
            out[m.group(1).strip()] = m.group(2).strip()
    return out


def skipped(meta: dict) -> dict:
    """文件头 skip：「append（时长不够）；impending」→ {单词: 原因}。"""
    out = {}
    for p in _items(meta.get("skip")):
        m = re.match(r"([A-Za-z][A-Za-z-]*)\s*(?:[（(](.*?)[）)])?\s*$", p)
        if m:
            out[m.group(1).lower()] = (m.group(2) or "").strip()
    return out
```

- [ ] **Step 4: 运行，确认通过**

Run: `python -I skills/word-family-video/scripts/test_script.py`
Expected: 5 行 `PASS`，最后一行 `全部通过`

- [ ] **Step 5: 提交**

```bash
git add skills/word-family-video/scripts/script_md.py skills/word-family-video/scripts/test_script.py
git commit -m "feat(word-family-video): script.md 节拍脚本解析

Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>"
```

---

### Task 2: 对照课程校验 + 念稿感检查

**Files:**
- Modify: `skills/word-family-video/scripts/script_md.py`（替换文件顶部的 import 块；在 `skipped()` 之后追加常量和函数）
- Test: `skills/word-family-video/scripts/test_script.py`

**Interfaces:**
- Consumes: Task 1 的 `parse / Script / Beat / Line / skipped / _items / wlen / BLOCKS / STATUSES / CUE_RE`
- Produces:
  - `validate(sc: Script, L: dict, stem: str, project_dir: Path | None = None) -> list[str]`：错误（含解析错误）；`project_dir` 给出时检查 `[photo: media/…]` 文件存在
  - `lint(sc: Script) -> list[str]`：提醒
  - `norm_part(pt) -> dict`、`lesson_words(L) -> dict[str, dict]`、`word_tokens(w) -> list[str]`（小写）、`scene_names(L) -> list[str]`、`quiz_words(L) -> list[str]`
  - 常量 `STOCK_LIMITS`、`BANNED`、`MAX_LINE`、`FACT_RE`

- [ ] **Step 1: 写失败的测试**（插在 `if __name__ == "__main__":` 之上）

```python
HEAD = "---\nlesson: pend\nspine: x\nskip: depend；suspend\n---\n\n"


def errs_of(text):
    return smd.validate(smd.parse(text), L, "pend")


def warns_of(text):
    return smd.lint(smd.parse(text))


def test_validate_good():
    assert errs_of(GOOD) == []


def test_validate_word_cue():
    errs = errs_of(GOOD.replace("{sub}", "{sup}"))
    assert any("sup 不是 suspend 的词素" in e and "sub" in e for e in errs), errs


def test_validate_event_needs_source():
    errs = errs_of(GOOD.replace("> 来源：https://official.nba.com/nba-to-suspend-season-following-tonights-games/\n", ""))
    assert any("缺 > 来源" in e for e in errs), errs


def test_validate_coverage():
    errs = errs_of(GOOD.replace("skip: depend（时长不够）\n", ""))
    assert any("depend" in e and "skip" in e for e in errs), errs


def test_validate_fact_needs_source():
    bad = GOOD.replace("{pend}，挂。", "{pend}，挂。1998 年就有人这么用。")
    assert any("「1998 年」" in e for e in errs_of(bad))
    ok = GOOD.replace("{pend}，挂。", "{pend}，挂。1570 年代起才有暂停的意思。")   # 课程词源里有 1570
    assert errs_of(ok) == []


def test_validate_blocks_and_args():
    cases = {
        "## a [video]\n一句。\n": "没有这种画面块",
        "## a [scene: tractor]\n一句。\n": "没有「tractor」的线稿",
        "## a [title: 第一幕]\n": "不带参数",
        "## a [scene: suspend]\n\n## b [title]\n": "没有解说",
        "## a [pair: depend]\n{depend}。\n": "[pair: A | B]",
        "## a [quiz]\n答案是 {pendant}。\n": "迁移题的触发词",
        "## a [word: pendant]\n一句。\n": "不是这一课的主词",
        "## a [photo: opening]\n一句。\n": "开场没有照片",
        "## a [photo: media/x.jpg]\n一句。\n": "> 署名",
        "## a [photo: media/x.jpg]\n> 署名：x\n> 版式：半屏\n一句。\n": "版式 只能写",
    }
    for body, want in cases.items():
        errs = errs_of(HEAD + body)
        assert any(want in e for e in errs), (body, errs)
    assert any("spine" in e for e in errs_of("---\nlesson: pend\nskip: depend；suspend\n---\n\n## a [title]\n"))
    assert any("lesson 应为 pend" in e for e in errs_of("---\nlesson: tract\nspine: x\nskip: depend；suspend\n---\n\n## a [title]\n"))


def test_lint_stock_and_banned():
    w = warns_of(GOOD.replace("可它们其实是一家。", "这不就是一家吗？这不就是吗？下面我们来看。"))
    assert any("「这不就是」出现 2 次" in x for x in w), w
    assert any("「下面我们」" in x for x in w), w


def test_lint_long_repeated_flat():
    assert any("太长" in x for x in warns_of(HEAD + "## a [scene: suspend]\n" + "这" * 45 + "\n"))
    assert any("连续三句" in x for x in warns_of(HEAD + "## a [scene: suspend]\n我们一。\n我们二。\n我们三。\n"))
    flat = "\n".join("一二三四五六七八九十" for _ in range(9))
    assert any("太平均" in x for x in warns_of(HEAD + "## a [scene: suspend]\n" + flat + "\n"))


def test_lint_cues_photo_annotations():
    w = warns_of(GOOD.replace("## 第二幕 · 称 [title]", "## 线稿 [scene: suspend]\n吊在 {半空}。"))
    assert any("不会触发画面" in x for x in w), w
    w = warns_of(GOOD.replace("最要紧的是这个词：{suspending}。", "最要紧的是这个词。"))
    assert any("原文高亮「suspending」" in x for x in w), w
    assert any("批注" in x for x in warns_of(GOOD))
    assert any("真实图片" in x for x in warns_of(GOOD))                     # GOOD 没有 [photo]
    with_photo = GOOD + "\n## 饮水机 [photo: media/dispenser.jpg]\n> 署名：x\n一份一份往外出水。\n"
    assert not any("真实图片" in x for x in warns_of(with_photo))
```

- [ ] **Step 2: 运行，确认失败**

Run: `python -I skills/word-family-video/scripts/test_script.py`
Expected: 新增的测试 `FAIL ... AttributeError: module 'script_md' has no attribute 'validate'`（以及 `lint`），Task 1 的 5 个仍 `PASS`

- [ ] **Step 3: 实现**

把 `script_md.py` 顶部的 import 块换成：

```python
import json
import re
import statistics
from dataclasses import dataclass, field
```

在 `skipped()` 之后追加：

```python
STOCK_LIMITS = {"这不就是": 1, "字面意思": 1, "你有没有想过": 1, "其实就是": 2, "换个方向": 2}   # 全片最多出现几次
BANNED = ("下面我们", "接下来我们", "我们再来看", "接下来是", "下面来看")      # 转场套话：用承接内容的句子代替
MAX_LINE = 40
# 年份、月日、百分比、两位以上的数字：要么课程词源里有，要么所在节拍写明来源——专门防编造
FACT_RE = re.compile(r"\d{3,4}\s*年|\d{1,2}\s*月\s*\d{1,2}\s*日|\d+(?:\.\d+)?\s*%|\d{2,}")


def norm_part(pt) -> dict:
    """与 word-family scripts/build.py 的 norm_part 相同（课程格式在那边定义）。"""
    o = {"m": pt[0], "cn": pt[1] if len(pt) > 1 else "", "kind": pt[2] if len(pt) > 2 else None} \
        if isinstance(pt, list) else dict(pt)
    m = o.get("m", "")
    o["kind"] = o.get("kind") or ("p" if m.endswith("-") else "s" if m.startswith("-") else "r")
    return o


def lesson_words(L: dict) -> dict:
    """能做 [word] 拼词的词：主词和 finale，键是小写单词。"""
    ws = list(L.get("words", [])) + ([L["finale"]] if L.get("finale") else [])
    return {w["w"].lower(): w for w in ws}


def word_tokens(w: dict) -> list:
    """[word: X] 里合法的触发词：每个词素（去掉连字符）、词素的原形（of）、整词。"""
    toks = []
    for p in map(norm_part, w.get("parts", [])):
        toks.append(p["m"].strip("-"))
        if p.get("of"):
            toks.append(p["of"].strip("-"))
    toks.append(w["w"])
    return list(dict.fromkeys(t.lower() for t in toks if t))


def scene_names(L: dict) -> list:
    names = [k for k, w in lesson_words(L).items() if w.get("scene")]
    return names + [k for k in ("anchor", "opening", "finale") if (L.get(k) or {}).get("scene")]


def quiz_words(L: dict) -> list:
    return [q.split("=")[0].strip().lower() for q, _ in L.get("transfer", [])]


def validate(sc: Script, L: dict, stem: str, project_dir=None) -> list:
    """对照课程检查脚本；返回错误列表（带行号和改法）。解析阶段的错误也在里面。"""
    errs = list(sc.errors)
    if sc.meta.get("lesson") != stem:
        errs.append(f"文件头 lesson 应为 {stem}（现在是「{sc.meta.get('lesson', '')}」）")
    if not sc.meta.get("spine"):
        errs.append("文件头缺少 spine：先用一句话写下主线（方向型/演变型/场景型/对照型 + 具体路线）")
    if sc.status not in STATUSES:
        errs.append(f"文件头 status 只能是 {' / '.join(STATUSES)}")
    for p in _items(sc.meta.get("say_as")):
        if not re.match(r".+?\s*(?:→|->)\s*.+$", p):
            errs.append(f"文件头 say_as 里的「{p}」要写成「原词 → 念法」")
    if not sc.beats:
        errs.append("脚本里还没有 ## 节拍")
    words, scenes, quiz = lesson_words(L), scene_names(L), quiz_words(L)
    lesson_text = re.sub(r"\s+", "", json.dumps(L, ensure_ascii=False))
    covered = set()
    for b in sc.beats:
        where = f"第 {b.lineno} 行 [{b.block}]"
        if b.block == "?":
            continue                                       # 标题格式错，解析阶段已报
        if b.block not in BLOCKS:
            errs.append(f"{where}：没有这种画面块，可用：{'、'.join(BLOCKS)}")
            continue
        if b.block != "title" and not b.lines:
            errs.append(f"{where}：节拍里没有解说（只有 [title] 可以不说话）")
        if b.block in ("title", "event", "map", "quiz") and b.arg:
            errs.append(f"{where}：这种画面块不带参数，去掉「: {b.arg}」")
        cues = [(ln.lineno, c) for ln in b.lines for c in ln.cues]
        if b.block == "scene" and b.arg.lower() not in scenes:
            errs.append(f"{where}：没有「{b.arg}」的线稿，可用：{'、'.join(scenes)}")
        elif b.block == "photo":
            if b.arg == "opening":
                if not L.get("opening", {}).get("photo"):
                    errs.append(f"{where}：这一课的开场没有照片；改用 [scene: opening]，或用 video.py photo 取图")
            elif not b.arg:
                errs.append(f"{where}：要写图片，例如 [photo: opening] 或 [photo: media/xxx.jpg]")
            else:
                if project_dir is not None and not (project_dir / b.arg).exists():
                    errs.append(f"{where}：找不到图片 {project_dir / b.arg}（用 video.py photo 取图）")
                if not b.get("署名"):
                    errs.append(f"{where}：课程以外的照片要写 > 署名：作者、许可、来源")
            if b.get("版式") and b.get("版式")[0] != "整屏":
                errs.append(f"{where}：> 版式 只能写「整屏」；不写就放在右侧")
        elif b.block == "word":
            w = words.get(b.arg.lower())
            if w is None:
                if not (b.get("释义") and b.get("来源")):
                    errs.append(f"{where}：{b.arg} 不是这一课的主词：换成 {'、'.join(words)} 之一，"
                                f"或补 > 释义：{b.arg} = 意思 和 > 来源：…")
            else:
                covered.add(w["w"].lower())
                toks = word_tokens(w)
                for n, c in cues:
                    if c.lower() not in toks:
                        errs.append(f"第 {n} 行：{c} 不是 {w['w']} 的词素，可用：{'、'.join(toks)}")
        elif b.block == "pair":
            sides = [x.strip() for x in b.arg.split("|")]
            if len(sides) != 2 or not all(sides):
                errs.append(f"{where}：要写成 [pair: A | B]")
            else:
                given = {v.split("=")[0].strip().lower() for v in b.get("释义")}
                for x in sides:
                    if x.lower() not in words and x.lower() not in given:
                        errs.append(f"{where}：{x} 不是这一课的词，补一行 > 释义：{x} = 意思")
                for n, c in cues:
                    if c.lower() not in {x.lower() for x in sides}:
                        errs.append(f"第 {n} 行：pair 里的触发词只能是 {sides[0]} 或 {sides[1]}，不是 {c}")
        elif b.block == "event":
            if not b.get("事件"):
                errs.append(f"{where}：缺 > 事件：名称 · 日期")
            if not b.get("来源"):
                errs.append(f"{where}：缺 > 来源：URL（日期）。来源要核实过；找不到就删掉这个节拍")
        elif b.block == "quiz":
            if not quiz:
                errs.append(f"{where}：这一课没有迁移题")
            for n, c in cues:
                if c.lower() not in quiz:
                    errs.append(f"第 {n} 行：迁移题的触发词只能是 {'、'.join(quiz)}，不是 {c}")
        if not b.get("来源"):
            for ln in b.lines:
                for m in FACT_RE.finditer(ln.plain):
                    if re.sub(r"\s+", "", m.group(0)) not in lesson_text:
                        errs.append(f"第 {ln.lineno} 行：「{m.group(0)}」是年份/日期/数字，但这个节拍没有 > 来源，"
                                    f"课程词源里也查不到：核实后补来源，找不到就删掉这句")
                        break
    skip = skipped(sc.meta)
    missing = [w["w"] for w in L.get("words", []) if w["w"].lower() not in covered | set(skip)]
    if missing:
        errs.append(f"这些主词既没有 [word] 节拍，也不在 skip 里：{'、'.join(missing)}。讲它，或者在文件头 skip 里写明原因")
    return errs


def lint(sc: Script) -> list:
    """不影响生成、但会让成片像念稿的问题。"""
    warns, lines = [], sc.spoken()
    text = "\n".join(ln.plain for ln in lines)
    for k, limit in STOCK_LIMITS.items():
        n = text.count(k)
        if n > limit:
            warns.append(f"「{k}」出现 {n} 次（全片最多 {limit} 次）：换成具体的说法")
    for k in BANNED:
        if k in text:
            warns.append(f"「{k}」是转场套话：用承接内容的句子代替")
    rq = sum(1 for ln in lines if ln.plain.endswith("吗？"))
    if rq > 2:
        warns.append(f"以「吗？」结尾的反问有 {rq} 句（全片最多 2 句）")
    for ln in lines:
        if wlen(ln.plain) > MAX_LINE:
            warns.append(f"第 {ln.lineno} 行太长（约 {wlen(ln.plain):.0f} 字）：拆成两句，念起来有呼吸，字幕也不挤")
    for a, b, c in zip(lines, lines[1:], lines[2:]):
        if len(a.plain) >= 2 and a.plain[:2] == b.plain[:2] == c.plain[:2]:
            warns.append(f"第 {a.lineno}–{c.lineno} 行连续三句都以「{a.plain[:2]}」开头")
    if len(lines) >= 8:
        sd = statistics.pstdev([wlen(ln.plain) for ln in lines])
        if sd < 4:
            warns.append(f"句子长短太平均（标准差 {sd:.1f} 字）：穿插几句四五个字的短句，节奏才像人在说话")
    for b in sc.beats:
        if b.block in ("scene", "photo", "title"):
            for ln in b.lines:
                if ln.cues:
                    warns.append(f"第 {ln.lineno} 行：[{b.block}] 节拍里的 {{…}} 不会触发画面，去掉花括号")
        if b.block == "event":
            said = {c.lower() for ln in b.lines for c in ln.cues}
            for h in CUE_RE.findall(" ".join(b.get("原文"))):
                if h.strip().lower() not in said:
                    warns.append(f"第 {b.lineno} 行 [event]：原文高亮「{h}」在解说里没有对应的 {{{h}}}，会在节拍开头直接高亮")
    if sc.beats and not any(b.block == "photo" for b in sc.beats):
        warns.append("全片没有一张真实图片：实物、场景、事件能找到贴切的图就用（video.py photo 搜图或截图）")
    if sc.annotations:
        warns.append(f"还有 {len(sc.annotations)} 条 >> 批注没处理")
    return warns
```

- [ ] **Step 4: 运行，确认通过**

Run: `python -I skills/word-family-video/scripts/test_script.py`
Expected: 全部 `PASS`，`全部通过`

- [ ] **Step 5: 提交**

```bash
git add skills/word-family-video/scripts/script_md.py skills/word-family-video/scripts/test_script.py
git commit -m "feat(word-family-video): 脚本对照课程校验 + 念稿感检查（套话、句长、无出处数字、无真实图片）

Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>"
```

---

### Task 3: 内容指纹、审核状态与门槛

**Files:**
- Modify: `skills/word-family-video/scripts/script_md.py`（import 块加两行；文件末尾追加）
- Test: `skills/word-family-video/scripts/test_script.py`

**Interfaces:**
- Consumes: Task 1 的 `parse / Script`，Task 1 的 `STATUSES`
- Produces:
  - `fingerprint(text: str) -> str`（8 位十六进制；忽略文件头里 `status`、`checked` 两行）
  - `mark(text: str, status: str, by: str, today: str = "") -> str`（返回新全文；`status != "draft"` 时写 `checked: <指纹> · <by> · <日期>`）
  - `gate(sc: Script) -> list[str]`（不能出片的原因；空列表 = 可以出片）
  - `review_done(md: str) -> bool`（`review.md` 最新一轮「处理结果」是否已填写）

- [ ] **Step 1: 写失败的测试**（插在 `if __name__ == "__main__":` 之上）

```python
CLEAN = GOOD.replace(">> 这里能不能再加一个生活里的例子？\n", "")


def test_fingerprint_ignores_status():
    marked = smd.mark(CLEAN, "reviewed", "AI 审稿", today="2026-10-28")
    assert smd.fingerprint(marked) == smd.fingerprint(CLEAN)
    assert smd.fingerprint(CLEAN.replace("一家", "一伙")) != smd.fingerprint(CLEAN)


def test_mark_writes_front_matter():
    marked = smd.mark(CLEAN, "reviewed", "AI 审稿", today="2026-10-28")
    head = marked.split("---")[1]
    assert "status: reviewed" in head
    assert f"checked: {smd.fingerprint(CLEAN)} · AI 审稿 · 2026-10-28" in head
    assert head.index("status:") > head.index("lesson:")           # 状态紧跟在 lesson 后面
    again = smd.mark(marked, "draft", "")
    assert "status: draft" in again and "checked:" not in again


def test_gate():
    assert any("还没审过" in x for x in smd.gate(smd.parse(CLEAN)))
    ok = smd.mark(CLEAN, "reviewed", "AI 审稿")
    assert smd.gate(smd.parse(ok)) == []
    assert any("审核之后脚本又改过" in x for x in smd.gate(smd.parse(ok.replace("一家", "一伙"))))
    hand = CLEAN.replace("lesson: pend", "lesson: pend\nstatus: approved")     # 用户在文件里手改的
    assert any("checked 指纹" in x for x in smd.gate(smd.parse(hand)))
    noted = smd.mark(GOOD, "reviewed", "AI 审稿")
    assert any("批注" in x for x in smd.gate(smd.parse(noted)))


def test_review_done_multi_round():
    r1 = "# 审稿记录：pend\n\n## 审稿意见 第 1 轮（Codex）\n\n1. ……\n\n## 处理结果 第 1 轮\n\n1. 采纳：改了开头。\n"
    assert smd.review_done(r1)
    r2 = r1 + "\n## 审稿意见 第 2 轮（Codex）\n\n1. ……\n\n## 处理结果 第 2 轮\n\n"
    assert not smd.review_done(r2)                                  # 只看最新一轮
    assert not smd.review_done("# 审稿记录：pend\n")
```

- [ ] **Step 2: 运行，确认失败**

Run: `python -I skills/word-family-video/scripts/test_script.py`
Expected: 4 个新测试 `FAIL ... has no attribute 'mark'`（等），其余 `PASS`

- [ ] **Step 3: 实现**

import 块变成：

```python
import hashlib
import json
import re
import statistics
from dataclasses import dataclass, field
from datetime import date
```

文件末尾追加：

```python
GATE_RE = re.compile(r"^\s*(status|checked)\s*[：:]")


def fingerprint(text: str) -> str:
    """去掉文件头里 status、checked 两行后的内容指纹：改状态不变，改任何内容都会变。"""
    rows = text.lstrip("\ufeff").replace("\r\n", "\n").split("\n")
    keep, in_head = [], False
    for k, r in enumerate(rows):
        if in_head and GATE_RE.match(r):
            continue
        if r.strip() == "---" and (k == 0 or in_head):
            in_head = k == 0
        keep.append(r.rstrip())
    return hashlib.sha1("\n".join(keep).strip().encode("utf-8")).hexdigest()[:8]


def mark(text: str, status: str, by: str, today: str = "") -> str:
    """把文件头 status 改成 status；不是 draft 时写入 checked：指纹 · by · 日期。返回新的全文。"""
    if status not in STATUSES:
        raise ValueError(f"status 只能是 {STATUSES}")
    text = text.lstrip("\ufeff").replace("\r\n", "\n")
    rows = text.split("\n")
    end = next((i for i in range(1, len(rows)) if rows[i].strip() == "---"), None)
    if rows[0].strip() != "---" or end is None:
        raise ValueError("脚本没有完整的文件头（两行 --- 之间）")
    head = [r for r in rows[1:end] if not GATE_RE.match(r)]
    pos = next((i + 1 for i, r in enumerate(head) if re.match(r"^\s*lesson\s*[：:]", r)), 0)
    add = [f"status: {status}"]
    if status != "draft":
        add.append(f"checked: {fingerprint(text)} · {by} · {today or date.today().isoformat()}")
    head[pos:pos] = add
    return "\n".join(["---"] + head + rows[end:])


def gate(sc: Script) -> list:
    """出片前的审核门槛；返回不能出片的原因，空列表表示可以出片。"""
    why = []
    if sc.status not in ("reviewed", "approved"):
        why.append("脚本还没审过（status 是 draft）：先跑 AI 审稿，或者等用户说「通过」")
    else:
        m = re.match(r"\s*([0-9a-f]{8})\b", sc.meta.get("checked", ""))
        now = fingerprint(sc.text)
        if not m:
            why.append("文件头没有 checked 指纹：如果是用户在文件里改成了 approved，运行 video.py mark <课> approved 记录一下")
        elif m.group(1) != now:
            why.append(f"审核之后脚本又改过（指纹 {m.group(1)} → {now}）：重新审一遍；"
                       f"用户自己改的，等用户说「按我改的出片」再 mark approved")
    if sc.annotations:
        why.append(f"还有 {len(sc.annotations)} 条 >> 批注没处理")
    return why


def review_done(md: str) -> bool:
    """review.md 最新一轮「处理结果」下面有没有写内容。"""
    parts = re.split(r"^## 处理结果[^\n]*$", md, flags=re.M)
    if len(parts) < 2:
        return False
    return bool(re.split(r"^## ", parts[-1], maxsplit=1, flags=re.M)[0].strip())
```

- [ ] **Step 4: 运行，确认通过**

Run: `python -I skills/word-family-video/scripts/test_script.py`
Expected: 全部 `PASS`

- [ ] **Step 5: 提交**

```bash
git add skills/word-family-video/scripts/script_md.py skills/word-family-video/scripts/test_script.py
git commit -m "feat(word-family-video): 脚本内容指纹、审核状态与出片门槛

Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>"
```

---

### Task 4: 配音逐词时间戳、时间轴、试听音频，`brief` 与新 `plan`

**Files:**
- Modify: `skills/word-family-video/scripts/video.py`（`import build as wf_build` 之后、常量 `PRE, LEAD…` 那一行之后、`synth_all` 整个函数、`def main():` 之前、`main()` 整个函数）
- Test: `skills/word-family-video/scripts/test_script.py`

**Interfaces:**
- Consumes: `smd.parse / validate / lint / say_as / fingerprint / gate / norm_part / word_tokens / scene_names / wlen`；video.py 现有的 `tts_text(s, say_as)`、`tts_path`、`decode(mp3, sr)`、`chunks(s)`、`wlen(s)`、`load_lesson`、常量 `PRE, LEAD, GAP_LINE, GAP_UNIT, TAIL, TARGET, HARD_MAX, SR, RATE, PROJECTS, CACHE`
- Produces（第二期渲染层直接读）：
  - `synth_all(lines, say_as, voice, rate, marks=False) -> dict[str, Path]`（新增 `marks`；mp3 旁边写同名 `.words.jsonl`）
  - `tts_marks(mp3: Path) -> list[dict]`：`[{"t": 秒, "d": 秒, "w": 词}]`
  - `cue_time(plain, cue, marks, dur, say_as) -> tuple[float, str]`：相对句首秒数，方式 `"exact" | "joined" | "estimate"`
  - `sub_chunks(plain, s, e) -> list[tuple[str, float, float]]`
  - `build_timeline(sc, say_as, clip_of, dur_of, marks_of) -> tuple[dict, list[str]]`
  - `build/timeline.json` 格式：`{"lesson", "fingerprint", "voice", "rate", "total", "words": [按出场顺序的 [word] 词], "beats": [{"lineno", "title", "block", "arg", "data": [[键, 值]], "t0", "t1", "lines": [{"lineno", "text", "plain", "s", "e", "cues": {触发词: 绝对秒}}]}], "subs": [{"s", "e", "t"}]}`，时间都是相对片头的绝对秒数
  - `mix_timeline(tl, clip_of) -> np.ndarray`、`write_audio(path, audio)`、`script_path(stem) -> Path`、`load_script(stem, L) -> (Script, 错误, 提醒)`、`brief_text(stem, L) -> str`、`cmd_brief`、`cmd_plan_script(stem, L, a) -> int`
  - 常量 `TITLE_HOLD = 1.6`、`PARA_GAP = 0.45`

- [ ] **Step 1: 写失败的测试**

在 `test_script.py` 顶部 `import script_md as smd` 下面加一行：

```python
import video as v  # noqa: E402  导入时会定位 word-family 并加载它的 build.py
```

再在 `if __name__ == "__main__":` 之上追加：

```python
def test_cue_time():
    marks = [{"t": 0.4, "d": 0.3, "w": "最要紧"}, {"t": 1.1, "d": 0.5, "w": "suspending"}]
    assert v.cue_time("最要紧的是这个词：suspending。", "suspending", marks, 2.0, {}) == (1.1, "exact")
    marks2 = [{"t": 2.0, "d": 0.2, "w": "until"}, {"t": 2.3, "d": 0.3, "w": "further"}, {"t": 2.7, "d": 0.3, "w": "notice"}]
    assert v.cue_time("而是 until further notice。", "until further notice", marks2, 4.0, {}) == (2.0, "joined")
    t, how = v.cue_time("没有时间戳的句子 pend。", "pend", [], 3.0, {})
    assert how == "estimate" and 0 < t < 3.0


def test_cue_time_say_as():
    # say_as 改了字母（live 念成 laiv）：配音里的词是 laiv，触发词 {live} 仍要精确对上
    assert v.cue_time("live 现场。", "live", [{"t": 0.3, "d": 0.4, "w": "laiv"}], 1.5, {"live": "laiv"}) == (0.3, "exact")


def test_build_timeline():
    text = "---\nlesson: pend\nspine: x\n---\n\n## 第一幕 [title]\n\n## suspend [word: suspend]\n{sub}，从底下往上。\n\n{sus} 是它的变体。\n"
    sc = smd.parse(text)
    marks = {"sub，从底下往上。": [{"t": 0.1, "d": 0.2, "w": "sub"}], "sus 是它的变体。": [{"t": 0.0, "d": 0.2, "w": "sus"}]}
    tl, warns = v.build_timeline(sc, {}, lambda p: p, lambda mp3: 2.0, lambda mp3: marks[mp3])
    assert warns == []
    b0, b1 = tl["beats"]
    assert b0["t0"] == 0 and b0["t1"] == round(v.PRE + v.LEAD + v.TITLE_HOLD + v.GAP_UNIT, 3)
    l1, l2 = b1["lines"]
    assert l1["s"] == round(b0["t1"] + v.PRE, 3) and l1["e"] == round(l1["s"] + 2.0, 3)
    assert l1["cues"] == {"sub": round(l1["s"] + 0.1, 3)}
    assert l2["s"] == round(l1["e"] + v.PARA_GAP, 3)                 # 空行 = 段落停顿
    assert tl["total"] == round(l2["e"] + v.GAP_UNIT + v.TAIL, 3)
    assert tl["words"] == ["suspend"]
    assert tl["subs"][0]["t"] == "sub，从底下往上" and tl["subs"][-1]["e"] == l2["e"]


def test_sub_chunks():
    out = v.sub_chunks("一二三四五六七八九十，一二三四五六七八九十一二三。", 10.0, 14.0)
    assert [c for c, _, _ in out] == ["一二三四五六七八九十", "一二三四五六七八九十一二三"]
    assert out[0][1] == 10.0 and out[-1][2] == 14.0
```

- [ ] **Step 2: 运行，确认失败**

Run: `python -I skills/word-family-video/scripts/test_script.py`
Expected: 4 个新测试 `FAIL ... has no attribute 'cue_time'`（等），其余 `PASS`

- [ ] **Step 3: 实现**

① `video.py` 里 `import build as wf_build  # noqa: E402  复用课程校验与零件库加载` 之后加：

```python
sys.path.insert(0, str(Path(__file__).resolve().parent))   # python -I 不把脚本所在目录放进 sys.path
import script_md as smd  # noqa: E402  v2 节拍脚本：解析、校验、审核状态
```

② 常量 `PRE, LEAD, GAP_LINE, GAP_UNIT, TAIL = …` 那一行之后加：

```python
TITLE_HOLD, PARA_GAP = 1.6, 0.45   # 秒：[title] 节拍不说话时停留多久 / 脚本里空行（段落）的停顿
```

③ 整个 `synth_all` 换成：

```python
def synth_all(lines, say_as, voice, rate, marks=False):
    """按句合成并缓存。顺带记下逐词时间戳（edge-tts WordBoundary，存成同名 .words.jsonl），
    让画面在念到某个词的那一刻动作；marks=True 时，旧缓存缺时间戳的句子会重新合成。"""
    import edge_tts
    CACHE.mkdir(parents=True, exist_ok=True)
    texts = {s: tts_text(s, say_as) for s in lines}

    def missing(t):
        p = tts_path(t, voice, rate)
        return not p.exists() or (marks and not p.with_suffix(".words.jsonl").exists())
    todo = [(t, tts_path(t, voice, rate)) for t in set(texts.values()) if missing(t)]

    async def one(sem, t, p):
        async with sem:
            for attempt in range(4):           # 服务端偶尔返回空音频，重试
                try:
                    await edge_tts.Communicate(t, voice, rate=rate, boundary="WordBoundary").save(
                        str(p), str(p.with_suffix(".words.jsonl")))
                    if p.exists() and p.stat().st_size > 1000:
                        return
                except Exception:
                    pass
                await asyncio.sleep(1.5 * (attempt + 1))
            raise RuntimeError(f"配音失败（检查网络）：{t}")

    async def run():
        sem = asyncio.Semaphore(4)
        await asyncio.gather(*(one(sem, t, p) for t, p in todo))
    if todo:
        print(f"  配音 {len(todo)} 句（其余命中缓存）")
        asyncio.run(run())
    return {s: tts_path(texts[s], voice, rate) for s in lines}
```

④ 在 `def main():` 之前插入：

```python
# ================================================================ v2：节拍脚本（script.md）
def tts_marks(mp3: Path) -> list:
    """逐词时间戳：[{"t": 起点秒, "d": 时长秒, "w": 词}]。旧缓存没有记录时返回空列表。"""
    p = mp3.with_suffix(".words.jsonl")
    if not p.exists():
        return []
    out = []
    for row in p.read_text(encoding="utf-8").splitlines():
        if row.strip():
            m = json.loads(row)
            if m.get("type") == "WordBoundary":
                out.append({"t": m["offset"] / 1e7, "d": m["duration"] / 1e7, "w": m["text"]})
    return out


def cue_time(plain: str, cue: str, marks: list, dur: float, say_as: dict):
    """触发词在这句里被念到的时刻（相对句首，秒）和对上的方式：exact / joined / estimate。
    配音文字经过 say_as 替换，所以拿替换后的写法去对逐词时间戳。"""
    def norm(s):
        return re.sub(r"[^\w]", "", s.lower())
    target = norm(tts_text(cue, say_as))
    for m in marks:
        if norm(m["w"]) == target:
            return m["t"], "exact"
    joined, starts = "", []
    for m in marks:                     # 多词触发（until further notice）：拼起来找第一个词的时刻
        starts.append((len(joined), m["t"]))
        joined += norm(m["w"])
    i = joined.find(target) if target else -1
    if i >= 0:
        return max(t for pos, t in starts if pos <= i), "joined"
    j = plain.lower().find(cue.lower())
    return (dur * wlen(plain[:j]) / max(wlen(plain), 1) if j >= 0 else 0.0), "estimate"


def sub_chunks(plain: str, s: float, e: float) -> list:
    """一句切成字幕段，按字宽分时间。"""
    cs = chunks(plain)
    ws = [max(wlen(c), 1) for c in cs]
    out, t = [], s
    for c, w in zip(cs, ws):
        d = (e - s) * w / sum(ws)
        out.append((c, round(t, 3), round(t + d, 3)))
        t += d
    return out


def build_timeline(sc, say_as, clip_of, dur_of, marks_of):
    """按脚本排时间。clip_of(配音文字)->mp3，dur_of(mp3)->秒，marks_of(mp3)->逐词时间戳。
    返回 (timeline, 提醒)；时间都是相对片头的绝对秒数。"""
    beats, subs, warns, t = [], [], [], 0.0
    last = len(sc.beats) - 1
    for k, b in enumerate(sc.beats):
        t0, lt, rows = t, t + PRE + (LEAD if k == 0 else 0), []
        for j, ln in enumerate(b.lines):
            if j:
                lt += PARA_GAP if ln.pause_before else GAP_LINE
            mp3 = clip_of(ln.plain)
            d = dur_of(mp3)
            cues = {}
            for c in ln.cues:
                off, how = cue_time(ln.plain, c, marks_of(mp3), d, say_as)
                cues[c] = round(lt + off, 3)
                if how == "estimate":
                    warns.append(f"第 {ln.lineno} 行：{c} 没在配音的逐词时间里找到，只能按字数估算，画面可能对不准")
            rows.append({"lineno": ln.lineno, "text": ln.text, "plain": ln.plain,
                         "s": round(lt, 3), "e": round(lt + d, 3), "cues": cues})
            subs += [{"s": s, "e": e, "t": c} for c, s, e in sub_chunks(ln.plain, lt, lt + d)]
            lt += d
        if not b.lines:
            lt += TITLE_HOLD
        t = lt + GAP_UNIT + (TAIL if k == last else 0)
        beats.append({"lineno": b.lineno, "title": b.title, "block": b.block, "arg": b.arg,
                      "data": [[key, val] for key, val, _ in b.data],
                      "t0": round(t0, 3), "t1": round(t, 3), "lines": rows})
    words = list(dict.fromkeys(b.arg.lower() for b in sc.beats if b.block == "word"))
    return {"total": round(t, 3), "words": words, "beats": beats, "subs": subs}, warns


def mix_timeline(tl, clip_of):
    """把每句配音放到时间轴上，返回 48 kHz 单声道 int16。"""
    audio = np.zeros(int((tl["total"] + 1) * SR), np.int16)
    for b in tl["beats"]:
        for r in b["lines"]:
            clip = decode(clip_of(r["plain"]))
            i0 = int(r["s"] * SR)
            audio[i0:i0 + len(clip)] = clip[:len(audio) - i0]
    return audio


def write_audio(path: Path, audio):
    """写 wav；目标是 .mp3 时经 ffmpeg 转码并做响度归一，删掉中间的 wav。"""
    wav = path.with_suffix(".wav")
    with wave.open(str(wav), "wb") as wf:
        wf.setnchannels(1), wf.setsampwidth(2), wf.setframerate(SR)
        wf.writeframes(audio.tobytes())
    if path.suffix == ".mp3":
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(wav), "-af", "loudnorm=I=-16:TP=-1.5:LRA=11",
                        "-ar", str(SR), "-b:a", "128k", str(path)], check=True)
        wav.unlink()


def script_path(stem) -> Path:
    return PROJECTS / stem / "script.md"


def load_script(stem, L):
    """读 projects/<课>/script.md，返回 (脚本, 错误, 提醒)。"""
    sc = smd.parse(script_path(stem).read_text(encoding="utf-8"))
    return sc, smd.validate(sc, L, stem, PROJECTS / stem), smd.lint(sc)


def brief_text(stem, L) -> str:
    """写稿和审稿用的课程素材：只列事实和可用参数，不给现成句子，免得照抄卡片。"""
    def tags(s):
        return re.sub(r"<[^>]+>", "", s or "")
    o, an, root = L["opening"], L["anchor"], L["root"]
    vs = "；".join(f"{x['m']}（{x.get('note', '')}，例 {x.get('ex', '')}）" for x in root.get("variants") or [])
    media_dir = PROJECTS / stem / "media"
    media = sorted(p.relative_to(PROJECTS / stem).as_posix() for p in media_dir.glob("*.*")) if media_dir.exists() else []
    out = [f"课程：{stem}（{L.get('title', '')}）",
           f"词根：{root['m']} = {root['cn']}" + (f"；变体：{vs}" if vs else ""),
           f"开场：类型 {o.get('type', '?')}；{tags(o.get('big'))}；钩子：{tags(o.get('say'))}"
           + (f"；补充：{tags(o['muted'])}" if o.get("muted") else ""),
           f"母画面：{an['text']}",
           "可用线稿：" + "、".join(f"[scene: {n}]" for n in smd.scene_names(L)),
           "可用照片：" + ("[photo: opening]（课程开场照片）" if o.get("photo") else "课程没有开场照片")
           + (f"；本项目已取：{'、'.join(media)}" if media else "") + "。还可以用 video.py photo 搜图或截图"]
    for w in L["words"] + ([L["finale"]] if L.get("finale") else []):
        kind = "finale（结尾回扣）" if w is L.get("finale") else "主词"
        parts = " + ".join(f"{p['m']}（{p['cn']}" + (f"，{p['of']} 的{p.get('how') or '同化/变体'}" if p.get("of") else "") + "）"
                           for p in map(smd.norm_part, w["parts"]))
        out += ["", f"## {w['w']}　{kind}", f"拆分：{parts}", f"字面画面：{w['literal']}　释义：{w['meaning']}",
                f"词源：{w['fact']}"]
        out += [f"延伸：{tags(s)}" for s in w.get("senses", [])]
        if w.get("ex"):
            out.append(f"例句：{w['ex'][0]}（{w['ex'][1]}）")
        if w.get("caveat"):
            out.append(f"注意：{tags(w['caveat'])}")
        out.append(f"[word: {w['w']}] 可用触发词：{'、'.join(smd.word_tokens(w))}")
    if L.get("traps"):
        out += ["", "形近陷阱（不同源）：" + "；".join(tags(t) for t in L["traps"])]
    if L.get("transfer"):
        out.append("迁移题 [quiz]：" + "；".join(f"{q} → {tags(a)}" for q, a in L["transfer"]))
    if L.get("daily"):
        out.append("家族图四角 [map]：" + "、".join(L["daily"]))
    out += ["", f"时长：目标 ≤ {TARGET} 秒，上限 {HARD_MAX} 秒（语速 {RATE}）。参考：开场 + 母画面约 60 秒，"
                f"每词 25–35 秒，回扣 + 家族图 + 结尾约 40 秒。",
            f"词源核对：{L.get('source', '')}"]
    return "\n".join(out)


def cmd_brief(stem, L):
    print(brief_text(stem, L))
    return 0


def cmd_plan_script(stem, L, a):
    """新 plan：解析 + 检查 → 配音（带逐词时间戳）→ 时间轴 → 试听音频。有错误就不往下走。"""
    sc, errs, warns = load_script(stem, L)
    if errs:
        print(f"\n脚本有 {len(errs)} 处错误，改完再运行 plan：")
        for e in errs:
            print("  - [错误]", e)
        return 1
    sa = smd.say_as(sc.meta)
    clips = synth_all([ln.plain for ln in sc.spoken()], sa, a.voice, a.rate, marks=True)
    durs = {}

    def dur_of(mp3):
        if mp3 not in durs:
            durs[mp3] = len(decode(mp3)) / SR
        return durs[mp3]
    tl, cue_warns = build_timeline(sc, sa, clips.__getitem__, dur_of, tts_marks)
    tl.update(lesson=stem, fingerprint=smd.fingerprint(sc.text), voice=a.voice, rate=a.rate)
    build = PROJECTS / stem / "build"
    build.mkdir(parents=True, exist_ok=True)
    (build / "timeline.json").write_text(json.dumps(tl, ensure_ascii=False, indent=1), encoding="utf-8")
    write_audio(build / "preview.mp3", mix_timeline(tl, clips.__getitem__))
    total = tl["total"]
    print(f"\n时长 {total // 60:.0f} 分 {total % 60:.0f} 秒（目标 ≤ {TARGET} 秒），{len(tl['beats'])} 个节拍，"
          f"拼词 {len(tl['words'])} 个")
    for b in tl["beats"]:
        print(f"  [{b['t0']:6.1f}s] {b['block']:<6} {b['title'][:18]:<18} {b['t1'] - b['t0']:5.1f}s  {len(b['lines'])} 句")
    if total > TARGET:
        warns.append(f"超过目标时长 {TARGET} 秒：删掉一些节拍，删掉的主词写进文件头 skip")
    for w in warns + cue_warns:
        print("  - [提醒]", w)
    print(f"\n试听：{build / 'preview.mp3'}")
    gate = smd.gate(sc)
    print(f"状态：{sc.status}" + ("，可以出片" if not gate else "；" + "；".join(gate)))
    if total > HARD_MAX:
        print(f"  - [错误] 超过 5 分钟（{total:.0f} 秒）：不靠加快语速，删节拍")
        return 1
    return 0
```

⑤ 整个 `main()` 换成：

```python
def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description="word-family 课程 → 讲解视频")
    ap.add_argument("cmd", choices=["brief", "plan", "init", "stills", "render", "check"])
    ap.add_argument("lesson", help="词根名（如 tract）或课程 JSON 路径")
    ap.add_argument("--voice", default=VOICE)
    ap.add_argument("--rate", default=RATE, help="语速，默认 +20%%（约 1.2 倍）；原速写 +0%%")
    ap.add_argument("--force", action="store_true", help="超过 5 分钟也渲染")
    ap.add_argument("--asr", default="large-v3-turbo", help="读音检查用的 Whisper 模型（首次使用自动下载约 1.6GB）")
    a = ap.parse_args()
    stem, L = load_lesson(a.lesson)
    if a.cmd == "brief":
        return cmd_brief(stem, L)
    if a.cmd == "plan" and script_path(stem).exists():
        return cmd_plan_script(stem, L, a)
    # 以下是 v1（narration.json）路径：第二期把渲染接到 timeline 后删除
    if a.cmd == "init":
        return cmd_init(stem, L)
    if a.cmd == "plan":
        prepare(stem, L, a.voice, a.rate)
        return 0
    return {"stills": cmd_stills, "render": cmd_render, "check": cmd_check}[a.cmd](stem, L, a)
```

- [ ] **Step 4: 运行单测，确认通过**

Run: `python -I skills/word-family-video/scripts/test_script.py`
Expected: 全部 `PASS`

- [ ] **Step 5: 真实执行：brief 与 plan**

Run: `python -I skills/word-family-video/scripts/video.py brief pend`
Expected: 输出含 `[word: suspend] 可用触发词：sus、sub、pend、suspend` 和 `可用线稿：[scene: depend]、…[scene: anchor]、[scene: opening]、[scene: finale]`

把下面的冒烟脚本写到 `skills/word-family-video/projects/pend/script.md`：

```markdown
---
lesson: pend
spine: 冒烟测试
skip: depend（测试）；append（测试）；impending（测试）；dispense（测试）；compensate（测试）
---

## 一场停摆 [event]
> 事件：NBA 官方声明 · 2020-03-11
> 原文：The NBA is {suspending} game play … {until further notice}.
> 来源：https://official.nba.com/nba-to-suspend-season-following-tonights-games/
2020 年 3 月 11 日晚上，NBA 发出一份声明。
最要紧的是这个词：{suspending}。

## suspend [word: suspend]
{sub}，从底下往上；碰到 p，常写成 {sus}。
{pend}，挂。

把事情吊起来，不让它落地，就是 {suspend}。
```

Run: `python -I skills/word-family-video/scripts/video.py plan pend`
Expected: 退出码 0；`2 个节拍，拼词 1 个`；提醒只有两条：原文高亮「until further notice」没有对应、全片没有真实图片；**没有**"按字数估算"的提醒；`状态：draft；脚本还没审过…`

Run: `python -I -c "import json;t=json.load(open('skills/word-family-video/projects/pend/build/timeline.json',encoding='utf-8'));print(t['total'],[l['cues'] for b in t['beats'] for l in b['lines']])"`
Expected: 每个触发词都有时刻，且落在所在句的 `s`–`e` 之间

Run: `ffprobe -v error -show_entries format=duration -of csv=p=0 skills/word-family-video/projects/pend/build/preview.mp3`
Expected: 与 `total` 相差不超过 1 秒

清理：`rm skills/word-family-video/projects/pend/script.md`（真脚本在 Task 9 写）

- [ ] **Step 6: 提交**

```bash
git add skills/word-family-video/scripts/video.py skills/word-family-video/scripts/test_script.py
git commit -m "feat(word-family-video): 配音逐词时间戳、节拍时间轴、试听音频，新增 brief 与新版 plan

Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>"
```

---

### Task 5: AI 审稿、审核标记、状态总览

**Files:**
- Create: `skills/word-family-video/references/review_brief.md`
- Modify: `skills/word-family-video/scripts/video.py`（import 块、`FRAME = …` 之后、`cmd_plan_script` 之后、`main()` 整个函数）
- Test: `skills/word-family-video/scripts/test_script.py`

**Interfaces:**
- Consumes: Task 4 的 `load_script / brief_text / script_path`；`smd.fingerprint / mark / gate / review_done / parse / STATUSES`
- Produces:
  - `run_codex(build: Path, brief: Path, raw: Path) -> tuple[bool, str]`
  - `append_review(path: Path, stem: str, engine: str, fp: str, raw_text: str) -> int`（返回轮次）
  - `cmd_review(stem, L, a) -> int`（`a.reviewer in {"codex", "claude"}`；Codex 失败返回 2，且不写 `review.md`）
  - `cmd_mark(stem, L, a) -> int`（`a.args[0]` 为目标状态）、`cmd_status() -> int`
  - 命令行：`video.py status`、`video.py review <课> [--reviewer claude]`、`video.py mark <课> reviewed|approved|draft`

- [ ] **Step 1: 写失败的测试**（插在 `if __name__ == "__main__":` 之上）

```python
def test_run_codex_missing():
    here = Path(__file__).resolve().parent
    old = v.shutil.which
    v.shutil.which = lambda name: None
    try:
        ok, why = v.run_codex(here, here / "x.md", here / "y.md")
    finally:
        v.shutil.which = old
    assert not ok and "codex" in why


def test_append_review_rounds():
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "review.md"
        assert v.append_review(p, "pend", "Codex", "abcd1234", "1. 开头太慢。") == 1
        assert not smd.review_done(p.read_text(encoding="utf-8"))
        p.write_text(p.read_text(encoding="utf-8") + "1. 采纳：开头改成 NBA 事件。\n", encoding="utf-8")
        assert smd.review_done(p.read_text(encoding="utf-8"))
        assert v.append_review(p, "pend", "Claude 子代理", "abcd5678", "1. 结尾没回扣。") == 2
        text = p.read_text(encoding="utf-8")
        assert "采纳：开头改成 NBA 事件" in text and "第 2 轮" in text     # 第一轮的处理结果还在
        assert not smd.review_done(text)


def test_review_fallback_keeps_no_record():
    import tempfile
    import types
    with tempfile.TemporaryDirectory() as d:
        old_proj, old_run = v.PROJECTS, v.run_codex
        v.PROJECTS = Path(d)
        v.run_codex = lambda build, brief, raw: (False, "测试：codex 不可用")
        try:
            (Path(d) / "pend").mkdir()
            (Path(d) / "pend" / "script.md").write_text(CLEAN, encoding="utf-8")
            code = v.cmd_review("pend", L, types.SimpleNamespace(reviewer="codex"))
        finally:
            v.PROJECTS, v.run_codex = old_proj, old_run
        assert code == 2
        assert not (Path(d) / "pend" / "review.md").exists()
        assert (Path(d) / "pend" / "build" / "review_brief.md").exists()
```

- [ ] **Step 2: 运行，确认失败**

Run: `python -I skills/word-family-video/scripts/test_script.py`
Expected: 3 个新测试 `FAIL`（`has no attribute 'shutil'` / `'append_review'` / `'cmd_review'`），其余 `PASS`

- [ ] **Step 3: 实现**

① 创建 `skills/word-family-video/references/review_brief.md`：

````markdown
# 审稿要求

你是一位做过很多科普短视频的中文编辑，替一支 5 分钟以内的英语词根词缀讲解视频审脚本。脚本是写给耳朵听的：一行是一句配音；`{…}` 是画面触发点（念到时画面动作）；`>` 开头的行是画面数据和出处，不念；`## 标题 [画面块]` 开始一个节拍。你只提意见，不改任何文件。

下面附了这一课的课程素材（词源都已核实）和待审脚本（带行号）。

## 按这几项审

1. 开头 10 秒：有没有一个观众见过的具体东西或一个矛盾，能不能让人想听下去。
2. 主线：文件头 spine 是否贴合这个词根的特性（方向型 / 演变型 / 场景型 / 对照型），节拍顺序是否沿着主线往前走。
3. 讲法：每个词的讲法是否不同，是否落到了生活或真实事件上；有没有两个词讲成同一个套路。
4. 口播感：像不像一个人在说话；套话、反问是否过多；句子长短有没有变化；有没有书面腔、念卡片的痕迹。
5. 事实：有没有可疑、夸大、没有出处的说法；词源说法与课程素材是否一致；联想有没有标注。出处链接能打开就打开核对。
6. 画面：画面块用得对不对（该用事件卡、对照、线稿、真实图片的地方）；能用真实图片的地方有没有用；屏幕上的字有没有和解说逐句重复。
7. 时长与取舍：哪里拖沓、哪里可以删；跳过的主词是否合理。
8. 结尾：有没有回答开头的问题；总结收不收得住。

## 输出格式

- 编号意见，每条三行：

  ```
  N. 位置：第 X 行 /「节拍标题」
  问题：……
  改法：……（能给改写句就给改写句）
  ```

- 只写真正值得改的，按重要性排序，最多 15 条；没问题的项不用写。
- 最后单列「最想改的三处」，各一句话。
- 不要输出整篇改写稿。
````

② `video.py` 的 import 块里加两行（保持字母序）：

```python
import shutil
from datetime import date
```

③ `FRAME = HERE / "assets" / "frame.html"` 之后加：

```python
REVIEW_BRIEF = HERE / "references" / "review_brief.md"
```

④ 在 `cmd_plan_script` 之后插入：

```python
def run_codex(build: Path, brief: Path, raw: Path):
    """用 Codex（另一家模型）只读审稿，意见写进 raw。返回 (成功, 失败原因)。"""
    exe = shutil.which("codex")
    if not exe:
        return False, "没有找到 codex 命令"
    cmd = [exe, "exec", "--skip-git-repo-check", "--ephemeral", "--sandbox", "read-only", "-C", str(build),
           "-o", str(raw), f"读取当前目录下的 {brief.name}，按其中的要求审稿。只输出审稿意见，不要修改任何文件。"]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=900)
    except subprocess.TimeoutExpired:
        return False, "15 分钟内没有返回"
    if r.returncode or not raw.exists() or not raw.read_text(encoding="utf-8").strip():
        return False, f"退出码 {r.returncode}：{(r.stderr or r.stdout).strip()[-300:]}"
    return True, ""


def append_review(path: Path, stem: str, engine: str, fp: str, raw_text: str) -> int:
    """review.md 按轮次追加：每轮一节「审稿意见」+ 一节空的「处理结果」，由写稿方逐条填写。"""
    old = path.read_text(encoding="utf-8") if path.exists() else f"# 审稿记录：{stem}\n"
    n = len(re.findall(r"^## 审稿意见", old, re.M)) + 1
    path.write_text(old.rstrip() + f"\n\n## 审稿意见 第 {n} 轮（{engine} · {date.today().isoformat()} · 脚本指纹 {fp}）\n\n"
                    f"{raw_text.strip()}\n\n## 处理结果 第 {n} 轮\n\n", encoding="utf-8")
    return n


def cmd_review(stem, L, a):
    sc, errs, _ = load_script(stem, L)
    if errs:
        print("脚本还有错误：先跑 plan 改干净再审稿")
        return 1
    build = PROJECTS / stem / "build"
    build.mkdir(parents=True, exist_ok=True)
    brief, raw = build / "review_brief.md", build / "review_raw.md"
    numbered = "\n".join(f"{i + 1:>3}  {r}" for i, r in enumerate(sc.text.split("\n")))
    brief.write_text(REVIEW_BRIEF.read_text(encoding="utf-8") + "\n\n# 课程素材\n\n" + brief_text(stem, L)
                     + "\n\n# 待审脚本（行号 + 原文）\n\n```\n" + numbered + "\n```\n", encoding="utf-8")
    if a.reviewer == "codex":
        raw.unlink(missing_ok=True)
        ok, why = run_codex(build, brief, raw)
        if not ok:
            print(f"Codex 审稿没成功：{why}\n改派一个独立的 Claude 子代理（model: opus）：只让它读 {brief}，"
                  f"按其中的要求把审稿意见写进 {raw}；然后运行 video.py review {stem} --reviewer claude")
            return 2
        engine = "Codex"
    else:
        if not raw.exists() or not raw.read_text(encoding="utf-8").strip():
            print(f"还没有审稿意见 {raw}：先让独立的 Claude 子代理按 {brief} 审稿并写进这个文件")
            return 1
        engine = "Claude 子代理"
    n = append_review(PROJECTS / stem / "review.md", stem, engine, smd.fingerprint(sc.text),
                      raw.read_text(encoding="utf-8"))
    print(raw.read_text(encoding="utf-8"))
    print(f"\n已写入 {PROJECTS / stem / 'review.md'} 第 {n} 轮。在「处理结果 第 {n} 轮」下逐条写 采纳/部分采纳/不采纳 + 理由，"
          f"改完脚本跑 plan，再运行 video.py mark {stem} reviewed")
    return 0


def cmd_mark(stem, L, a):
    target = a.args[0] if a.args else ""
    if target not in smd.STATUSES:
        print("用法：video.py mark <课> reviewed|approved|draft")
        return 1
    sc, errs, _ = load_script(stem, L)
    if target != "draft":
        if errs:
            print("脚本还有错误：先跑 plan 改干净")
            return 1
        if sc.annotations:
            print(f"还有 {len(sc.annotations)} 条 >> 批注没处理：处理完再标记")
            return 1
    if target == "reviewed":
        rv = PROJECTS / stem / "review.md"
        if not rv.exists():
            print(f"还没有审稿记录：先运行 video.py review {stem}")
            return 1
        if not smd.review_done(rv.read_text(encoding="utf-8")):
            print(f"{rv} 最新一轮「处理结果」还是空的：先逐条写下怎么处理审稿意见")
            return 1
    by = {"reviewed": "AI 审稿", "approved": "用户确认", "draft": ""}[target]
    script_path(stem).write_text(smd.mark(sc.text, target, by), encoding="utf-8")
    print(f"{stem}：status → {target}" + (f"（指纹 {smd.fingerprint(sc.text)}）" if target != "draft" else ""))
    return 0


def cmd_status():
    """所有课的脚本状态一览：批量审核时看进度。"""
    print(f"{'课':<10}{'状态':<10}{'时长':<20}{'批注':<6}能否出片")
    for d in sorted(p for p in PROJECTS.iterdir() if p.is_dir()):
        sp = d / "script.md"
        if not sp.exists():
            print(f"{d.name:<10}{'无脚本':<10}")
            continue
        sc = smd.parse(sp.read_text(encoding="utf-8"))
        dur, tl_p = "未跑 plan", d / "build" / "timeline.json"
        if tl_p.exists():
            tl = json.loads(tl_p.read_text(encoding="utf-8"))
            dur = f"{tl['total']:.0f}s" + ("" if tl.get("fingerprint") == smd.fingerprint(sc.text) else "（脚本已改）")
        gate = smd.gate(sc)
        print(f"{d.name:<10}{sc.status:<10}{dur:<20}{len(sc.annotations):<6}{'可以' if not gate else gate[0]}")
    return 0
```

⑤ 整个 `main()` 换成：

```python
def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description="word-family 课程 → 讲解视频")
    ap.add_argument("cmd", choices=["brief", "plan", "review", "mark", "status", "init", "stills", "render", "check"])
    ap.add_argument("lesson", nargs="?", help="词根名（如 tract）或课程 JSON 路径；status 不用写")
    ap.add_argument("args", nargs="*", help="mark 的目标状态：reviewed / approved / draft")
    ap.add_argument("--voice", default=VOICE)
    ap.add_argument("--rate", default=RATE, help="语速，默认 +20%%（约 1.2 倍）；原速写 +0%%")
    ap.add_argument("--force", action="store_true", help="超过 5 分钟也渲染")
    ap.add_argument("--asr", default="large-v3-turbo", help="读音检查用的 Whisper 模型（首次使用自动下载约 1.6GB）")
    ap.add_argument("--reviewer", choices=["codex", "claude"], default="codex",
                    help="review 的审稿方：codex（默认）；claude = 独立 Claude 子代理已把意见写进 build/review_raw.md")
    a = ap.parse_args()
    if a.cmd == "status":
        return cmd_status()
    if not a.lesson:
        ap.error("要写课程名，例如：video.py plan tract")
    stem, L = load_lesson(a.lesson)
    if a.cmd == "brief":
        return cmd_brief(stem, L)
    if a.cmd in ("plan", "review", "mark") and script_path(stem).exists():
        return {"plan": cmd_plan_script, "review": cmd_review, "mark": cmd_mark}[a.cmd](stem, L, a)
    if a.cmd in ("review", "mark"):
        print(f"没有 {script_path(stem)}：先按 references/script_guide.md 写脚本")
        return 1
    # 以下是 v1（narration.json）路径：第二期把渲染接到 timeline 后删除
    if a.cmd == "init":
        return cmd_init(stem, L)
    if a.cmd == "plan":
        prepare(stem, L, a.voice, a.rate)
        return 0
    return {"stills": cmd_stills, "render": cmd_render, "check": cmd_check}[a.cmd](stem, L, a)
```

- [ ] **Step 4: 运行单测，确认通过**

Run: `python -I skills/word-family-video/scripts/test_script.py`
Expected: 全部 `PASS`

- [ ] **Step 5: 真实执行：Python 调起 codex.CMD + 审核流程（不花审稿 token）**

Run: `python -I -c "import subprocess,shutil;r=subprocess.run([shutil.which('codex'),'exec','--skip-git-repo-check','--ephemeral','--sandbox','read-only','只回复：OK'],capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=300);print(r.returncode,r.stdout.strip()[-40:])"`
Expected: `0 ...OK`（确认 Python 能直接调起 Windows 上的 `codex.CMD`；失败就把 `run_codex` 里的 `cmd` 改成 `["cmd", "/c", exe, …]` 再试，并在提交信息里说明）

用 Task 4 Step 5 的冒烟脚本重新写一份 `projects/pend/script.md`，然后：

```bash
python -I skills/word-family-video/scripts/video.py plan pend
python -I skills/word-family-video/scripts/video.py mark pend reviewed     # 预期拒绝：还没有审稿记录
printf '1. 位置：第 9 行\n问题：测试\n改法：测试\n' > skills/word-family-video/projects/pend/build/review_raw.md
python -I skills/word-family-video/scripts/video.py review pend --reviewer claude   # 预期写入 review.md 第 1 轮
python -I skills/word-family-video/scripts/video.py mark pend reviewed     # 预期拒绝：处理结果还是空的
printf '1. 采纳：测试。\n' >> skills/word-family-video/projects/pend/review.md
python -I skills/word-family-video/scripts/video.py mark pend reviewed     # 预期成功，打印指纹
python -I skills/word-family-video/scripts/video.py status                 # pend 一行：reviewed … 可以
```

再把脚本里任意一个字改掉，`status` 那一行应变成"审核之后脚本又改过…"。
清理：`rm skills/word-family-video/projects/pend/script.md skills/word-family-video/projects/pend/review.md skills/word-family-video/projects/pend/build/review_*`

- [ ] **Step 6: 提交**

```bash
git add skills/word-family-video/scripts/video.py skills/word-family-video/scripts/test_script.py skills/word-family-video/references/review_brief.md
git commit -m "feat(word-family-video): Codex 审稿（失败退回 Claude 子代理）、审核标记与状态总览

Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>"
```

---

### Task 6: 给任意节拍配真实图片（`photo` 命令）

**Files:**
- Modify: `skills/word-family/scripts/photo.py`（docstring；`cmd_pick`、`cmd_shot` 改为调用新的 `save_candidate`、`shoot`）
- Modify: `skills/word-family-video/scripts/video.py`（文件开头的 docstring、`cmd_status` 之后、`main()` 整个函数）
- Test: `skills/word-family-video/scripts/test_script.py`

**Interfaces:**
- Consumes: word-family `photo.py` 现有的 `CACHE`、`slug(q)`、`cmd_search(q, n)`、`set_photo`、`LESSONS`
- Produces:
  - `photo.save_candidate(q: str, n: int, dst: Path) -> {"file": Path, "credit": str, "source": str}`
  - `photo.shoot(url: str, dst: Path, clip: tuple[int, int, int, int]) -> {"file": Path, "credit": str, "source": str}`
  - `cmd_photo(stem, L, a) -> int`（`a.args` = `["search", 查询]` | `["pick", 查询, 编号, 名字]` | `["shot", 网址, 名字]`，`a.clip` = `"x,y,宽,高"`）
  - 命令行：`video.py photo <课> search "查询" | pick "查询" 编号 名字 | shot 网址 名字 [--clip x,y,宽,高]`

- [ ] **Step 1: 写失败的测试**

在 `test_script.py` 顶部 import 区加：

```python
import json
import shutil
```

在 `if __name__ == "__main__":` 之上追加：

```python
def test_photo_usage_and_pick_offline():
    import tempfile
    import types
    import photo as wf_photo                 # word-family 的取图脚本（导入 video 时已加入 sys.path）
    from PIL import Image
    assert v.cmd_photo("pend", L, types.SimpleNamespace(args=["bogus"], clip="0,0,1280,720")) == 1
    q = "unit test dispenser"
    src = wf_photo.CACHE / wf_photo.slug(q)
    with tempfile.TemporaryDirectory() as d:
        old = v.PROJECTS
        v.PROJECTS = Path(d)
        try:
            src.mkdir(parents=True, exist_ok=True)
            Image.new("RGB", (900, 600), "white").save(src / "01.jpg")
            (src / "candidates.json").write_text(json.dumps([{
                "n": 1, "file": "01.jpg", "title": "File:x.jpg", "license": "CC BY 4.0", "artist": "Tester",
                "page": "https://commons.wikimedia.org/wiki/File:x.jpg"}]), encoding="utf-8")
            args = types.SimpleNamespace(args=["pick", q, "1", "dispenser"], clip="0,0,1280,720")
            assert v.cmd_photo("pend", L, args) == 0
            assert (Path(d) / "pend" / "media" / "dispenser.jpg").exists()
        finally:
            v.PROJECTS = old
            shutil.rmtree(src, ignore_errors=True)
```

- [ ] **Step 2: 运行，确认失败**

Run: `python -I skills/word-family-video/scripts/test_script.py`
Expected: `FAIL test_photo_usage_and_pick_offline - AttributeError: module 'video' has no attribute 'cmd_photo'`，其余 `PASS`

- [ ] **Step 3: 实现**

① `photo.py` 的 docstring 第一段之后加一行：

```text
word-family-video 的 photo 命令复用这里的 search / save_candidate / shoot，给视频的任意节拍配图（存进视频项目，不写课程 JSON）。
```

② `photo.py` 里把整个 `cmd_pick` 和 `cmd_shot` 换成下面四个函数（行为不变，只是把"存图"和"截图"拆出来给视频共用）：

```python
def save_candidate(q, n, dst: Path) -> dict:
    """把 search 得到的第 n 张候选图存成 dst（长边不超过 1600），返回 {"file", "credit", "source"}。"""
    src_dir = CACHE / slug(q)
    cj = src_dir / "candidates.json"
    if not cj.exists():
        sys.exit(f"先运行 search \"{q}\"")
    c = next((x for x in json.loads(cj.read_text(encoding="utf-8")) if x["n"] == n), None)
    if not c:
        sys.exit(f"没有第 {n} 张")
    dst.parent.mkdir(parents=True, exist_ok=True)
    try:
        from PIL import Image
        im = Image.open(src_dir / c["file"]).convert("RGB")
        im.thumbnail((1600, 1600))
        im.save(dst, quality=88)
    except ImportError:
        dst = dst.with_suffix(Path(c["file"]).suffix)
        shutil.copy(src_dir / c["file"], dst)
    return {"file": dst, "credit": f"照片：{c['artist']}，{c['license']}，Wikimedia Commons", "source": c["page"]}


def shoot(url, dst: Path, clip) -> dict:
    """网页截图（新闻标题区域等）存成 dst，返回 {"file", "credit", "source"}。"""
    from playwright.sync_api import sync_playwright
    dst.parent.mkdir(parents=True, exist_ok=True)
    x, y, w, h = clip
    with sync_playwright() as p:
        browser = None
        for opts in ({"channel": "chrome"}, {"channel": "msedge"}, {}):
            try:
                browser = p.chromium.launch(**opts)
                break
            except Exception:
                continue
        page = browser.new_page(viewport={"width": max(1280, x + w), "height": max(800, y + h)})
        page.goto(url, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(2500)
        page.screenshot(path=str(dst), clip={"x": x, "y": y, "width": w, "height": h})
        browser.close()
    return {"file": dst, "credit": f"网页截图：{urllib.parse.urlparse(url).netloc}，{datetime.date.today()}", "source": url}


def cmd_pick(stem, q, n):
    got = save_candidate(q, n, LESSONS / "media" / stem / "opening.jpg")
    photo = {"file": f"media/{stem}/{got['file'].name}", "credit": got["credit"], "source": got["source"]}
    set_photo(stem, photo)
    print(f"已写入 lessons/{stem}.json 的 opening.photo：\n  {json.dumps(photo, ensure_ascii=False)}\n再运行 build.py 生成页面")
    return 0


def cmd_shot(stem, url, clip):
    got = shoot(url, LESSONS / "media" / stem / "opening.png", clip)
    photo = {"file": f"media/{stem}/opening.png", "credit": got["credit"], "source": got["source"]}
    set_photo(stem, photo)
    print(f"已截图并写入 opening.photo：{got['file']}\n请打开图片确认截到的是标题区域；不对就用 --clip x,y,宽,高 重截")
    return 0
```

③ `video.py` 在 `cmd_status` 之后插入：

```python
def cmd_photo(stem, L, a):
    """给节拍配真实图片：图存进 projects/<课>/media/，打印可以直接粘进脚本的两行。课程 JSON 不动。"""
    import photo as wf_photo     # word-family 的取图脚本，与 build.py 同目录，已在 sys.path 里
    act, rest = (a.args[0], a.args[1:]) if a.args else ("", [])
    media = PROJECTS / stem / "media"
    if act == "search" and len(rest) == 1:
        return wf_photo.cmd_search(rest[0], 9)
    if act == "pick" and len(rest) == 3 and rest[1].isdigit():
        got = wf_photo.save_candidate(rest[0], int(rest[1]), media / f"{rest[2]}.jpg")
    elif act == "shot" and len(rest) == 2:
        got = wf_photo.shoot(rest[0], media / f"{rest[1]}.png", tuple(int(x) for x in a.clip.split(",")))
    else:
        print('用法：video.py photo <课> search "英文查询" | pick "英文查询" 编号 名字 | shot 网址 名字 [--clip x,y,宽,高]')
        return 1
    rel = got["file"].relative_to(PROJECTS / stem).as_posix()
    print(f"已保存：{got['file']}\n粘进脚本：\n## 标题 [photo: {rel}]\n> 署名：{got['credit']}（{got['source']}）")
    if act == "shot":
        print("先打开图片，确认截到的是标题区域；不对就加 --clip x,y,宽,高 重截")
    return 0
```

④ 整个 `main()` 换成：

```python
def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description="word-family 课程 → 讲解视频")
    ap.add_argument("cmd", choices=["brief", "plan", "review", "mark", "photo", "status",
                                    "init", "stills", "render", "check"])
    ap.add_argument("lesson", nargs="?", help="词根名（如 tract）或课程 JSON 路径；status 不用写")
    ap.add_argument("args", nargs="*", help="mark：reviewed / approved / draft；photo：search 查询 | pick 查询 编号 名字 | shot 网址 名字")
    ap.add_argument("--voice", default=VOICE)
    ap.add_argument("--rate", default=RATE, help="语速，默认 +20%%（约 1.2 倍）；原速写 +0%%")
    ap.add_argument("--force", action="store_true", help="超过 5 分钟也渲染")
    ap.add_argument("--asr", default="large-v3-turbo", help="读音检查用的 Whisper 模型（首次使用自动下载约 1.6GB）")
    ap.add_argument("--reviewer", choices=["codex", "claude"], default="codex",
                    help="review 的审稿方：codex（默认）；claude = 独立 Claude 子代理已把意见写进 build/review_raw.md")
    ap.add_argument("--clip", default="0,0,1280,720", help="photo shot 的截图区域：x,y,宽,高")
    a = ap.parse_args()
    if a.cmd == "status":
        return cmd_status()
    if not a.lesson:
        ap.error("要写课程名，例如：video.py plan tract")
    stem, L = load_lesson(a.lesson)
    if a.cmd == "brief":
        return cmd_brief(stem, L)
    if a.cmd == "photo":
        return cmd_photo(stem, L, a)
    if a.cmd in ("plan", "review", "mark") and script_path(stem).exists():
        return {"plan": cmd_plan_script, "review": cmd_review, "mark": cmd_mark}[a.cmd](stem, L, a)
    if a.cmd in ("review", "mark"):
        print(f"没有 {script_path(stem)}：先按 references/script_guide.md 写脚本")
        return 1
    # 以下是 v1（narration.json）路径：第二期把渲染接到 timeline 后删除
    if a.cmd == "init":
        return cmd_init(stem, L)
    if a.cmd == "plan":
        prepare(stem, L, a.voice, a.rate)
        return 0
    return {"stills": cmd_stills, "render": cmd_render, "check": cmd_check}[a.cmd](stem, L, a)
```

⑤ `video.py` 文件开头的 docstring 整段换成：

```python
"""word-family 课程 → 讲解视频（逐帧动画的线稿板书 + 免费 TTS + 字幕）。

v2 节拍脚本（projects/<课>/script.md，写法见 references/script_guide.md）：
    python scripts/video.py brief  <课>                      # 写稿素材：课程事实、可用画面、触发词、时长预算
    python scripts/video.py plan   <课>                      # 解析 + 检查 + 配音（带逐词时间戳）+ 时间轴 + 试听音频
    python scripts/video.py review <课> [--reviewer claude]  # 另一家模型（Codex）审稿，追加到 review.md
    python scripts/video.py mark   <课> reviewed|approved|draft   # 记录审核状态和内容指纹
    python scripts/video.py photo  <课> search "查询" | pick "查询" 编号 名字 | shot 网址 名字   # 给节拍取真实图片
    python scripts/video.py status                           # 所有课的状态、时长、批注数、能否出片

v1（narration.json，第二期把渲染接到 timeline 后删除）：
    python scripts/video.py init   <课>    # 生成解说词草稿 projects/<课>/narration.json（已存在则不覆盖）
    python scripts/video.py plan   <课>    # 没有 script.md 时：配音、量真实时长、超时自动删减
    python scripts/video.py stills <课>    # 每个单元出一张定格图 projects/<课>/stills/
    python scripts/video.py render <课>    # 逐帧渲染并合成 projects/<课>/<课>.mp4
    python scripts/video.py check  <课>    # 用 Whisper 回听，找读错的英文词（需要 faster-whisper）

课程数据来自 word-family skill 的 lessons/；线稿零件库直接读它的 assets/kit.js，两边画面一致。
依赖：edge-tts（免费，需联网）、ffmpeg、numpy、Python 版 Playwright（用本机 Chrome/Edge）。可选：Pillow、faster-whisper、Codex CLI。
"""
```

- [ ] **Step 4: 运行单测，确认通过**

Run: `python -I skills/word-family-video/scripts/test_script.py`
Expected: 全部 `PASS`

- [ ] **Step 5: 真实执行（联网）**

Run: `python -I skills/word-family-video/scripts/video.py photo pend search "water dispenser"`
Expected: 列出若干候选（只含 CC BY / CC BY-SA / CC0 / 公有领域）和 `_sheet.jpg` 路径；用 Read 打开 `_sheet.jpg` 看图

Run: `python -I skills/word-family-video/scripts/video.py photo pend pick "water dispenser" <看中的编号> dispenser`
Expected: 打印 `## 标题 [photo: media/dispenser.jpg]` 和 `> 署名：照片：…，CC …，Wikimedia Commons（https://commons.wikimedia.org/…）`

Run: `python -I skills/word-family/scripts/photo.py search "tractor field" --n 3`
Expected: 原有的课程取图命令照常可用（不运行 `pick`，免得改课程 JSON）

清理：`rm skills/word-family-video/projects/pend/media/dispenser.jpg`（真脚本在 Task 9 自己取图）

- [ ] **Step 6: 提交**

```bash
git add skills/word-family/scripts/photo.py skills/word-family-video/scripts/video.py skills/word-family-video/scripts/test_script.py
git commit -m "feat(word-family-video): photo 命令，复用 word-family 取图给任意节拍配真实图片

Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>"
```

---

### Task 7: word-family 去掉"桥接必须反问"

**Files:**
- Modify: `skills/word-family/scripts/build.py:11`（docstring）、`:182-183`（删）、`# 变体覆盖` 注释之前（加）
- Modify: `skills/word-family/references/style_guide.md:27`、`:69`
- Modify: `skills/word-family/references/lesson_schema.md:76`
- Modify: `skills/word-family/SKILL.md:76`、`:89`

**Interfaces:**
- Consumes: `build.validate(L, kinds, poses) -> (errs, warns)`、`build.kit_names()`
- Produces: 新提醒文案「N 张卡的 bridge 都用「这不就是……吗」（…）：最多留两张…」；旧提醒「bridge 没有反问」不再出现

- [ ] **Step 1: 先看现状**

Run: `python -I -c "import sys,json,copy; sys.path.insert(0,'skills/word-family/scripts'); import build; K=build.kit_names(); L=json.load(open('skills/word-family/lessons/tract.json',encoding='utf-8')); L2=copy.deepcopy(L); L2['words'][0]['bridge']='直接点破：这就是吸引。'; print([x for x in build.validate(L2,*K)[1] if 'bridge' in x])"`
Expected: 打印出含「bridge 没有反问」的提醒（旧规则还在）

- [ ] **Step 2: 改 build.py**

删除这两行：

```python
        if w.get("bridge") and not re.search(r"[？?]", w["bridge"]):
            warns.append(f"{name}: bridge 没有反问。用「……这不就是 X 吗？」把画面接到词义，让读者自己推出最后一步")
```

在 `    # 变体覆盖：课程本身就是某个有同化形式的前缀，却没列 variants` 这一行之前插入：

```python
    # 桥接句式：反问是推理工具，张张都「这不就是……吗」就成了口癖（视频解说曾因此像念模板）
    same = [w.get("w", "?") for w in words + ([L["finale"]] if L.get("finale") else [])
            if "这不就是" in w.get("bridge", "")]
    if len(same) > 2:
        warns.append(f"{len(same)} 张卡的 bridge 都用「这不就是……吗」（{'、'.join(same)}）：最多留两张，"
                     f"其余换别的接法——直接点破、举一个具体场景、条件分叉")

```

docstring 第 11 行里的 `桥接没有反问` 改成 `桥接句式重复`。

- [ ] **Step 3: 改三份文档**

`style_guide.md:27` 整行换成：

```markdown
| bridge（桥接） | 先摆画面，再把画面接到词义。接法换着用：反问（「……这不就是分心吗？」）、直接点破、举一个具体场景、条件分叉；同一句式全课最多两次 | 直接写「意为分心」；张张都用同一句反问 |
```

`style_guide.md:69` 整行换成：

```markdown
- 中文口语，短句，有停顿感。「其实就是」「你看」「这不就是……吗」都可以用，但同一句式全课最多两次——反问是推理工具，用多了就成了口癖。
```

`lesson_schema.md:76` 整行换成：

```markdown
| `bridge` | ✔ | 画面 → 词义的桥接；接法换着用（反问、点破、举例、条件分叉），同一句式全课最多两次 |
```

`word-family/SKILL.md:76` 整行换成：

```markdown
- 文字按 `style_guide.md` 第二节写：过渡句承接方向变化，字面画面具体，桥接的接法换着用（不要张张都「这不就是……吗」），联想要标注。
```

`word-family/SKILL.md:89` 里的 `桥接没有反问` 改成 `桥接句式重复`。

- [ ] **Step 4: 验证**

Run: 重复 Step 1 的命令
Expected: `[]`（不带问号的 bridge 不再提醒）

Run: `python -I -c "import sys,json; sys.path.insert(0,'skills/word-family/scripts'); import build; K=build.kit_names(); [print(s, [x for x in build.validate(json.load(open(f'skills/word-family/lessons/{s}.json',encoding='utf-8')),*K)[1] if 'bridge' in x]) for s in ('tract','pend')]"`
Expected: tract、pend 各打印一条「N 张卡的 bridge 都用「这不就是……吗」」——两课现有的 bridge 句式确实重复。按 spec，本期不改课程 JSON，下次重建这两课时再改

Run: `grep -rn "桥接没有反问\|结尾用反问\|桥接用反问" skills/word-family/`
Expected: 无输出

- [ ] **Step 5: 提交**

```bash
git add skills/word-family/scripts/build.py skills/word-family/references/style_guide.md skills/word-family/references/lesson_schema.md skills/word-family/SKILL.md
git commit -m "fix(word-family): 去掉「桥接必须反问」，改为提醒同一句式重复

Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>"
```

---

### Task 8: 写稿指南、SKILL.md 新流程、evals

**Files:**
- Create: `skills/word-family-video/references/script_guide.md`
- Modify: `skills/word-family-video/SKILL.md`（整篇重写）
- Create: `skills/word-family-video/evals/batch-scripts.json`、`evals/revise-annotations.json`、`evals/event-needs-source.json`
- Delete: `skills/word-family-video/evals/no-narration.json`、`evals/over-budget.json`（v1 的 init 与自动删减流程，已废弃；其中「第二段含「这不就是……吗？」」的断言按 spec 验收第 1 条删除）
- 不动：`evals/fix-pronunciation.json`（配音会话维护）、`references/narration_guide.md`（第二期并入）

**Interfaces:**
- Consumes: Task 1–6 的命令和格式
- Produces: 写稿子代理在 Task 9 里照着执行的 `SKILL.md` 第 1 节清单和 `script_guide.md`

- [ ] **Step 1: 写 `references/script_guide.md`**

````markdown
# 视频脚本写作指南（projects/<课>/script.md）

脚本是每支视频的成稿：先写给耳朵听，再交给画面。动笔前先运行 `video.py brief <课>` 读素材。

目录：一、定主线 · 二、每个词换讲法 · 三、真实图片 · 四、口播语言 · 五、事实与出处 · 六、格式 · 七、画面块 · 八、时长 · 九、交审前自查 · 十、处理审稿意见 · 十一、读音

## 一、定主线（写进文件头 spine）

主线由词根的性质决定，不由课程卡片的顺序决定。

| 主线 | 怎么认 | 怎么排 | 例 |
|---|---|---|---|
| 方向型 | 词根是一个身体动作，前缀给它换方向 | 同一个母画面换方向，方向尽量成对（往外/往回、往一起/往两边） | tract 拉：attract、distract、extract、contract |
| 演变型 | 词义分几步漂移，后一步从前一步长出来 | 分幕，每幕一个 `[title]`，每幕的词共用这一步的画面 | pend：挂 → 挂上秤称 → 称出去付钱 |
| 场景型 | 词根长在某个领域里 | 带观众在场景里走一圈 | jud：法庭里的 judge、verdict、prejudice |
| 对照型 | 一课围绕反义或容易混的成对词 | 用 `[pair]` 成对讲，讲差别 | import / export、include / exclude |

spine 写一句话：类型 + 具体路线，例如「演变——挂 → 挂上秤称 → 称出去付钱」。节拍标题要看得出主线在往前走。

## 二、每个词换讲法

先给每个词想 2–3 种讲法，再挑最好的一种：

- 真实事件：2020 年 3 月 11 日 NBA 宣布 suspending 赛季（要来源，见第五节）
- 物件特写：饮水机 water dispenser、按一下就缩回的 retractable pen
- 一词多义分叉：contract 既是收缩又是合同——拉到一起的是东西还是人
- 历史演变：spend 是拉丁语 expendere 被磨短的样子
- 反差：长得像却不同源（pen 钢笔来自羽毛），或者两个熟词的矛盾
- 想象小剧场：荒诞好记的小画面；是联想就写 `> 注：联想`
- 冷知识、数字：要来源
- 两词对照：extract 与 retract 一出一回，用 `[pair]`
- 真实标题或原话：要来源

相邻两个词讲法不同；一支视频至少三种；有合适的真实事件就用，没有就不用，不为了"有事件"硬凑。

## 三、真实图片

真实的图比线稿更容易让人记住"这个词我在哪儿见过"。实物、场景、事件能找到贴切的图就用，每支视频至少一张；确实找不到，在汇总里说明。

    python -I "$SKILL/scripts/video.py" photo <课> search "water dispenser"            # 搜维基共享资源，看 _sheet.jpg 挑图
    python -I "$SKILL/scripts/video.py" photo <课> pick "water dispenser" 3 dispenser    # 存成 media/dispenser.jpg
    python -I "$SKILL/scripts/video.py" photo <课> shot https://…/news nba-news           # 新闻页截图，必要时加 --clip x,y,宽,高

- 搜索词用英文，写具体的实物或场景（"retractable pen"、"airport baggage claim sign"），比抽象词好找。
- 图必须一眼看出就是解说说的那个东西；拿不准就不用。
- 命令会打印两行，直接粘进脚本：`## 标题 [photo: media/xxx.jpg]` 和 `> 署名：…`。署名必填。
- 事件现场、新闻截图可以加 `> 版式：整屏`；默认放在右侧，左边同时可以拼词。
- 课程开场有照片的，直接用 `[photo: opening]`。

## 四、口播语言

- 一行就是一句配音，不超过 40 字；长句短句交替，可以有四五个字的短句。
- 反问是工具不是口癖：以「吗？」结尾的反问全片最多 2 句，「这不就是……吗」最多 1 次。
- 不用转场套话（"下面我们来看""接下来是""我们再来看"）。用承接内容的句子过渡：「如果吊在半空的，是你头顶上的一块石头呢？」
- 不念卡片：不说"字面画面是""词性是"；括号、符号、v./adj. 不进解说。
- 英文词直接写，前缀不加连字符（写 sub，不写 sub-）。
- 开场按课程的开场类型（word-family `references/openings.md`）改写成口语，第一句是一个具体的东西或一个矛盾；结尾回答开头的问题，再收一句总结。

改写前后（suspend）：

> 改前：箱子吊到半空……事情悬在那里不往下走，这不就是暂停吗？
>
> 改后：2020 年 3 月 11 日晚上，NBA 发出一份声明，正文就几行。最要紧的是这个词：suspending。不是取消，也不是照常，而是 until further notice，等通知。一整个赛季，就这么被吊在了半空。

## 五、事实与出处

- 年份、日期、数字、引语、事件：用网页搜索找到原始报道并打开核实，在所在节拍写 `> 来源：URL（日期）`。没有来源，`plan` 会报错。
- 词源说法只能来自课程素材（`brief` 里的"词源"）或 word-family 的 `scripts/etym.py`；新查的写 `> 来源：etymonline <词>`。
- 找不到可靠来源的说法，删掉。不许凭记忆补日期、数字、引语。
- 只陈述事实，不评论、不站队。

## 六、格式

    ---
    lesson: pend
    spine: 演变——挂 → 挂上秤称 → 称出去付钱
    skip: append（时长不够，网页版里有）
    say_as: live → laiv
    ---

    ## 一场停摆 [event]
    > 事件：NBA 官方声明 · 2020-03-11
    > 原文：The NBA is {suspending} game play … {until further notice}.
    > 来源：https://official.nba.com/nba-to-suspend-season-following-tonights-games/
    2020 年 3 月 11 日晚上，NBA 发出一份声明，正文就几行。
    最要紧的是这个词：{suspending}。

    ## suspend [word: suspend]
    {sub}，从底下往上；碰到 p，它常常写成 {sus}。
    {pend}，挂。

    把事情吊起来，不让它落地，就是 {suspend}，暂停。

- `## 标题 [画面块]` 或 `## 标题 [画面块: 参数]` 开始一个节拍。标题写给人看；`[title]` 节拍直接把标题显示成章节卡。
- 普通的一行 = 一句配音。`{词}` 是触发点：念到它的那一刻画面动作；花括号不进字幕，也不念。
- 空行 = 段落停顿（比句间停顿长）。
- `> 键：值` 是画面数据和出处，不念：`事件`、`原文`、`来源`、`署名`、`版式`、`释义`、`注`。
- `>> ……` 是审稿人或用户的批注，不念；处理完要删掉，留着就不能出片。
- 文件头：`lesson`、`spine` 必填；`status`、`checked` 由 `video.py mark` 维护，不要手改；`skip` 写没讲的主词和原因；`say_as` 只改配音，字幕不变。
- 每个课程主词要么有一个 `[word]` 节拍，要么写进 `skip`。

## 七、画面块

| 块 | 写法 | 位置 | 触发点 |
|---|---|---|---|
| 章节卡 | `[title]` | 整屏 | — |
| 线稿 | `[scene: 词]`，也可 `anchor` / `opening` / `finale` | 右侧 | — |
| 照片 | `[photo: opening]` 或 `[photo: media/文件]`（课程外的要 `> 署名`） | 右侧；`> 版式：整屏` 时铺满 | — |
| 词素拼合 | `[word: 词]` | 左侧，可与右侧线稿、照片同屏 | `{词素}` 入场；先念原形 `{sub}` 再念 `{sus}` 会出现变形；`{整词}` 合拢并出释义 |
| 引文/事件卡 | `[event]` + `> 事件` `> 来源`（`> 原文` 可选，`{}` 标高亮） | 整屏 | 解说里与高亮相同的 `{片段}` |
| 两词对照 | `[pair: A \| B]` | 整屏 | `{A}`、`{B}` |
| 家族图 | `[map]` | 整屏 | 提到哪个词，哪个节点亮 |
| 迁移题 | `[quiz]` | 整屏 | `{答案词}` 揭晓 |

- 一个词的常见组合：`[scene: 词]` 或 `[photo: …]` 先出画面，紧接 `[word: 词]` 在左边拼词，两者同屏。
- 整屏块出现时，左边的单词会淡出。
- 屏幕上的字只有单词、词素小注、短释义、引文原文、章节标题。解释交给声音。
- `[word]` 里能用哪些触发词，`brief` 里每个词都列出来了。

## 八、时长

目标 ≤ 4:50，上限 5:00（当前语速 +20%）。参考：开场 + 母画面约 60 秒，每词 25–35 秒，回扣 + 家族图 + 结尾约 40 秒。超时就删：先删次要词的展开，再删整个词；删掉的主词写进 `skip`（附原因，例如"时长不够，网页版里有"）。不靠加快语速。

## 九、交审前自查

- [ ] 开头 10 秒里有一个观众见过的具体东西或一个矛盾
- [ ] 主线在节拍标题里看得出来
- [ ] 没有两个词讲成同一个套路
- [ ] 至少一张贴切的真实图片，且有署名
- [ ] 每个年份、数字、引语、事件都有来源
- [ ] 屏幕上的字没有和解说逐句重复
- [ ] 结尾回答了开头的问题

## 十、AI 审稿（可选）与处理意见

AI 审稿不是必经步骤：写完自查、`plan` 干净就交给用户。用户说"审一遍"时：

1. `video.py review <课>` 生成审稿包 `build/review_brief.md`（审稿要求 + 课程素材 + 带行号的脚本）。
2. 派一个独立的 Claude 子代理（`model: opus`），只给它审稿包，让它把意见原样写进 `build/review_raw.md`。用户也可以自己拿审稿包去问任何 AI，把回复贴进这个文件。
3. `video.py review <课> --record` 把意见记进 `review.md`：追加一轮「审稿意见」和一节空的「处理结果」。
4. 在「处理结果」下逐条写：

       1. 采纳：开头改成 NBA 声明，原来的吊箱子画面挪到第 3 句。
       2. 不采纳：审稿建议删掉 compensate，但它是航班延误赔偿这个生活场景的唯一入口；改为压缩到两句。

审稿人的意见不一定对，不采纳要写理由。改完 `plan` 到干净，再交给用户确认。

## 十一、读音

- 配音默认云健（zh-CN-YunjianNeural）、语速 +20%（由配音会话维护）。edge-tts 不支持自定义 SSML，读音只能靠改写文字。
- 两三个字母的前缀（at、ad、dis、sub）谁都读不准：直接写成要念的样子，或在文件头 `say_as` 里替换，例如 `say_as: retractable → re-tractable；or → O R`。只影响配音，字幕不变。
- 出片后用 `video.py check <课>` 回听检查，判读规则见 `references/narration_guide.md` 第四节。
````

- [ ] **Step 2: 重写 `SKILL.md`**

````markdown
---
name: word-family-video
description: >
  把 word-family 做好的词族课（lessons/<词根>.json）做成 5 分钟以内的讲解视频：先写节拍脚本
  script.md（按词根特性定主线、每个词换讲法、真实事件和图片附出处），交用户审改确认（可选让 AI 再审一遍），
  再渲染成线稿动画 + 免费配音 + 字幕的成片。支持几课批量写稿。
  Use when 用户想把某一课或几课词根词缀做成视频、写或改视频脚本、审稿、出片。
  触发词：词根视频, 词族视频, 讲解视频, 视频脚本, 生成视频, word family video。
compatibility: Python 3.10+ with numpy; edge-tts (free, needs network); ffmpeg; Python Playwright using local Chrome/Edge. Optional Pillow, faster-whisper (large-v3-turbo, ~1.6 GB download on first check). Requires the word-family skill.
metadata:
  platforms: claude-code
---

# 词族讲解视频

每支视频都先有一份脚本 `projects/<课>/script.md`。它是成稿，也是以后回头修改的入口：

写稿（含自查）→ `plan` 自动检查 → 停下交给用户 →（用户要求时）AI 审稿 → 用户确认 → 出片 → 读音检查

本文件所在目录记为 `$SKILL`，命令都写成 `python -I "$SKILL/scripts/video.py" <命令> <课>`。写稿前必读 `$SKILL/references/script_guide.md`。

## 状态规则（每一步都适用）

- 只有两档：`draft`（写过或改过）、`approved`（用户确认过）。只有 `approved` 的脚本能出片。
- 只有用户明确说"通过""按我改的出片"，才能运行 `mark <课> approved`；用户说"审一遍后直接出片"也算预先确认。
- 确认过的脚本被改过，要等用户再确认；工具按内容指纹拒绝出片，不要绕过，也不要手改文件头的 `status`、`checked`。
- AI 审稿只在用户要求时做，用户满意就不做。

## 1. 写脚本（可以几课一起）

用户点了几课，就给每课派一个子代理（`model: opus`，最多同时 3 个；etymonline 和网页搜索都有并发限制）。每个子代理按下面的清单完成一课，回报：主线、时长、每个词的讲法、用到的事件与图片及出处、还剩的提醒。

- [ ] 课程存在，word-family 的 `build.py` 零错误（没有就先用 word-family 做课）
- [ ] `brief <课>`：读素材（词源、可用画面与照片、每个词的触发词、时长预算）
- [ ] 读 `script_guide.md`，定主线，写进文件头 `spine`
- [ ] 每个词想 2–3 种讲法；要用的事件、数字、引语先用网页搜索核实，记下出处
- [ ] 给需要的节拍取图：`photo <课> search …` → 看 `_sheet.jpg` → `photo <课> pick …`（每支视频至少一张，找不到在回报里说明）
- [ ] 写 `projects/<课>/script.md`
- [ ] `plan <课>`：[错误] 改到没有，[提醒] 逐条改掉；超时就删节拍，删掉的主词写进 `skip`
- [ ] 按 `script_guide.md` 第九节自查，改完再 `plan` 到干净

全部完成后运行 `status`，把汇总交给用户：每课的主线、时长、事件与图片及出处，以及 `script.md` 和试听音频 `projects/<课>/build/preview.mp3` 的路径。然后停下，等用户审。

## 2. 用户审改

- 用户直接改 `script.md`，或写 `>> 批注` 后说"按批注改"：逐条处理并删掉批注行 → `plan` 到干净 → 告诉用户每条怎么处理的。
- 用户说"审一遍"：按 `script_guide.md` 第十节，`review <课>` 生成审稿包 → 派一个独立的 Claude 子代理（`model: opus`，只给它审稿包）把意见写进 `build/review_raw.md` → `review <课> --record` → 在 `review.md` 逐条写处理结果并改稿 → `plan` 到干净 → 告诉用户改了什么。用户也可以自己拿审稿包去问任何 AI，把回复贴进 `build/review_raw.md`。
- 用户说"通过"：`mark <课> approved`。

## 3. 出片

改造中：v2 第二期（画面层）完成前，新脚本还不能渲染。`render`、`stills`、`check` 仍按旧版 `narration.json` 工作，只用于配音和读音调试；`check` 的判读规则见 `references/narration_guide.md` 第四节。

## 不要做的事

- 不要编造：没有来源的年份、数字、引语、事件一律不写；词源只用课程素材或 `etym.py`。
- 不要替用户 `mark approved`，也不要在用户没要求时自行审稿。
- 不要为了塞进 5 分钟把语速调到默认（+20%）以上；删节拍。
- 不要改 `assets/frame.html` 和 word-family 的零件库来"修"某一课的画面。
````

- [ ] **Step 3: 换 evals**

删除 `evals/no-narration.json`、`evals/over-budget.json`。创建 `evals/batch-scripts.json`：

```json
{
  "query": "/word-family-video 给 tract 和 pend 各写一份视频脚本",
  "files": [],
  "expected_behavior": [
    "给每课各派一个子代理（model: opus），不在主会话里串行写",
    "每份脚本先跑 brief，写完跑 plan 到无错误无提醒，并按 script_guide 自查",
    "两课的 spine 不同（tract 方向型、pend 演变型）；每个真实事件都有 > 来源 链接；每课至少一张带署名的真实图片，或说明为什么没有",
    "写完就停下，汇报主线、时长、事件与图片及出处和试听音频路径；不自行审稿、不自行 mark approved、不渲染"
  ]
}
```

创建 `evals/revise-annotations.json`：

```json
{
  "query": "/word-family-video 我在 pend 的脚本里写了几条批注，按批注改",
  "files": ["projects/pend/script.md"],
  "setup": "在 projects/pend/script.md 里加两行批注：一条要求开场换成生活场景，一条要求删掉某个节拍",
  "expected_behavior": [
    "逐条处理每一行 >> 批注，处理完删除批注行",
    "改完运行 plan 到无错误无提醒",
    "告诉用户每条批注是怎么处理的",
    "不自行 mark approved：等用户说通过，或按用户要求再走一遍 AI 审稿"
  ]
}
```

创建 `evals/event-needs-source.json`：

```json
{
  "query": "/word-family-video 给 tract 的 contract 加一个真实的历史事件当例子",
  "files": ["projects/tract/script.md"],
  "expected_behavior": [
    "先用网页搜索找到并打开可靠来源核实事件，不凭记忆写日期",
    "用 [event] 节拍，带 > 事件 和 > 来源：URL（日期）",
    "找不到可靠来源时如实告诉用户，不添加该事件",
    "改完跑 plan 无错误，并说明这次修改需要用户重新确认才能出片"
  ]
}
```

创建 `evals/review-on-request.json`：

```json
{
  "query": "/word-family-video 让 AI 把 pend 的脚本审一遍",
  "files": ["projects/pend/script.md"],
  "expected_behavior": [
    "先运行 review 生成审稿包，再派一个独立的 Claude 子代理（model: opus），只给它审稿包",
    "把审稿意见写进 build/review_raw.md 后运行 review --record，在 review.md 的处理结果里逐条写采纳/不采纳及理由",
    "按采纳的意见改稿，plan 跑到无错误无提醒，并告诉用户改了什么",
    "不调用 Codex 等外部命令行；不自行 mark approved"
  ]
}
```

- [ ] **Step 4: 验证**

Run: `wc -l skills/word-family-video/SKILL.md skills/word-family-video/references/script_guide.md`
Expected: `SKILL.md` < 500 行；`script_guide.md` 超过 100 行，且第三行是"目录：…"

Run: `ls skills/word-family-video/evals/`
Expected: `baseline.md  batch-scripts.json  event-needs-source.json  fix-pronunciation.json  review-on-request.json  revise-annotations.json`

Run: `python -I -c "import json,glob; [json.load(open(f,encoding='utf-8')) for f in glob.glob('skills/word-family-video/evals/*.json')]; print('ok')"`
Expected: `ok`

Run: `grep -rn "这不就是" skills/word-family-video/SKILL.md skills/word-family-video/evals/`
Expected: 无输出（只在 script_guide 里作为"最多 1 次"的限制和改前示例出现）

- [ ] **Step 5: 提交**

```bash
git add -A skills/word-family-video/SKILL.md skills/word-family-video/references/script_guide.md skills/word-family-video/evals/
git commit -m "docs(word-family-video): 写稿指南、两段式流程与批量写稿、evals 换成新流程

Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>"
```

---

### Task 9: 用新流程做一课 cap/cip/cept 并写脚本（检查点 1）

> 用户在执行中改了测试对象（台账 Task 9 Ruling）：不再重写 tract、pend，改为一课全新的 cap/cip/cept。课程还不存在，先用 word-family 做课。本节不含提交步骤（用户决定不提交）。

**Files:**
- Create: `skills/word-family/lessons/<课>.json`、`lessons/<课>.html`（word-family 流程产物；文件名按 word-family 的命名规则，多半是 `cap`，以它的判断为准）
- Create: `skills/word-family-video/projects/<课>/script.md`（以及 `media/*`，如取了图）

**Interfaces:**
- Consumes: word-family `SKILL.md` 全流程；Task 8 的 `SKILL.md` 第 1 节清单、`script_guide.md`；Task 4–6 的命令
- Produces: 一份 `status: draft`、`plan` 干净的脚本和试听音频，交用户审

- [ ] **Step 1: 做课（word-family）**

派一个子代理（`subagent_type: "general-purpose"`，`model: "opus"`），提示词：

    你在执行 word-family skill。按 D:/Development/Automation/agent-skills/skills/word-family/SKILL.md 的完整流程，为用户给的词根 cap/cip/cept（拉丁语 capere「拿、抓」）做一课。
    要求：词源必须用 scripts/etym.py 核实；cap / cip / cept / ceive 的变体关系要讲清楚（写进 root.variants，主词至少覆盖两个变体）；captain、capital 这类来自 caput「头」的形近词放进形近陷阱；开场从 openings.md 里选真正贴合、用得最少的类型；build.py 零错误、提醒逐条处理。
    不确定的地方（例如文件名用哪个词根、某个词是否同源）按 SKILL.md 自己判断，并在回报里说明。
    完成后只回报：课程文件路径、母画面、主词与变体、开场类型、未处理的提醒及理由。

收到回报后核对：`python -I skills/word-family/scripts/build.py skills/word-family/lessons/<课>.json --no-check` 零错误；课程 JSON 的 `root.variants` 非空。

- [ ] **Step 2: 写视频脚本**

派写稿子代理（`model: "opus"`），提示词：

    你在执行 word-family-video skill 的写稿流程。按 D:/Development/Automation/agent-skills/skills/word-family-video/SKILL.md「1. 写脚本」的清单，为课程 <课> 写视频脚本。
    所有命令在 D:/Development/Automation/agent-skills 下运行，形如：python -I skills/word-family-video/scripts/video.py <命令> <课>。
    写之前读完 skills/word-family-video/references/script_guide.md。
    硬性要求：真实事件、数字、引语必须用网页搜索找到原始来源并打开核实，写进 > 来源；词源只用 brief 里的课程素材，或 skills/word-family/scripts/etym.py；至少一张贴切的真实图片（用 photo 命令），找不到要说明原因。
    不要审稿，不要 mark approved，不要渲染。
    完成后只回报：主线（spine）、总时长、节拍数、每个词用的讲法、用到的事件与图片及出处、plan 是否零错误零提醒。

- [ ] **Step 3: 独立复核**

```bash
python -I skills/word-family-video/scripts/video.py plan <课>
python -I skills/word-family-video/scripts/video.py status
grep -n "^spine:" skills/word-family-video/projects/<课>/script.md
grep -c "这不就是" skills/word-family-video/projects/<课>/script.md
grep -n "^## .*\[photo" skills/word-family-video/projects/<课>/script.md
```

Expected: `plan` 退出码 0、没有 `[错误]` `[提醒]`、时长 ≤ 290 秒；`status` 为 draft、批注 0；「这不就是」≤ 1；至少一个 `[photo` 节拍（没有则回报里有原因）。不满足就用 `SendMessage` 把具体问题发回写稿子代理，修正后再复核。

- [ ] **Step 4: 抽查事实**

挑两条 `> 来源` 用 WebFetch 打开，核对日期、原文与脚本一致；再抽两个词的词源说法，与课程 JSON 的 `fact` 对照。不一致就按 Step 3 的方式退回修改。

- [ ] **Step 5: 检查点 1——交用户审**

汇报并停下：主线、时长、节拍数、每个词的讲法、事件与图片及出处；附 `script.md`、`build/preview.mp3`、课程页 `lessons/<课>.html` 的路径。说明：可以直接改或写 `>>` 批注；想让 AI 再审就说"审一遍"；满意说"通过"；画面要等第二期。第二期计划在收到反馈后再写。
