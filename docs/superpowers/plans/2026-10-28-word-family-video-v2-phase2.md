# word-family-video v2 第二、三期（画面层 + 收尾）Implementation Plan

> **当前状态与执行约定（2026-10-29，优先于历史步骤）**：v2 实现、后续反馈与本次收尾已完成；81 项测试通过，port、spir、dis 三支成片已通过实际 MP4 验收。直接在当前目录完成，未提交、未建 worktree、未引入依赖；用户明确授权 agent 自行审核脚本，只看最终成片。历史步骤中的固定模型、强制分工和重复中间确认不再适用于本次任务。20 课批量仍暂停。实测结果见 `.superpowers/sdd/2026-10-28-word-family-video-v2-phase2/progress.md` 与 `skills/word-family-video/evals/baseline.md`；下文保留原实施方案与测试草案，未勾选不等于尚未开发。

> **执行约定（用户 2026-10-28 决定，优先于下文）**：本会话直接执行（executing-plans），写完不等审、任务之间不停、直到整个项目完成；**不提交 git、不建 worktree**，直接在主目录 `D:/Development/Automation/agent-skills` 改；子代理一律 `model: "opus"`；改 `video.py`、`SKILL.md`、`kit.js` 前先 `git diff --stat` 看有没有别人的新改动。同目录的 word-family-video-ff 会话在 `projects/<20 个新词根>/` 下写 v2 脚本，等本计划能渲染后统一出片：不改它们的内容；脚本格式若有改动、渲染可用时都要 SendMessage 通知它。用户已授权"中间不用等我同意"：第二支样片（tract）的脚本由本会话在 plan 干净后 `mark approved`，记为 Ruling。

**Goal:** 让 `script.md` 直接渲染成符合设计 §7 的成片（新 frame.html、8 种画面块、进度条、预览、定格图自检、render、读音检查），产出 cap 与 tract 两支成片；然后删掉 v1、补齐文档与 evals。

**Architecture:** Python 端把 `timeline.json` + 课程 JSON 编成一份"画面数据"（每个节拍放哪一层、舞台放什么、左侧放什么、转场类型、前缀动效、家族图节点亮起时刻），所有判断都在这里、可单元测试；`frame.html` 只负责按 `setT(t)` 画出来——所有节拍层一次建好，每帧只算各层的透明度和位移（纯函数，不用 CSS 动画）。页面内置 `audit()` 自检重叠、出界、箭头缺失，`stills` 与 `render` 都调用它。

**Tech Stack:** Python 3.10+ 标准库 + numpy、edge-tts、ffmpeg/ffprobe、Python Playwright（本机 Chrome/Edge）；页面纯 HTML/SVG/JS；不新增依赖。

**Spec:** `docs/superpowers/specs/2026-10-28-word-family-video-v2-design.md`（§6 时间轴、§7 画面层、§8 迁移、§9 验证、§10 分期、验收标准）。第一期计划与台账：`docs/superpowers/plans/2026-10-28-word-family-video-v2-phase1.md`、`.superpowers/sdd/2026-10-28-word-family-video-v2-phase1/progress.md`。

## Global Constraints

- 只用现有依赖；所有脚本 `python -I` 运行，同目录模块手动 `sys.path.insert`。
- 配音默认值不改：`VOICE = "zh-CN-YunjianNeural"`、`RATE = "+20%"`、停顿 `PRE, LEAD, GAP_LINE, GAP_UNIT, TAIL = 0.35, 0.6, 0.2, 0.45, 1.5`、`TITLE_HOLD, PARA_GAP = 1.6, 0.45`。
- 配色（§7 原值）：底 `#eef1f2`（径向渐变到 `#e2e7e9`）、墨 `#27303a`、次要 `#7b8690`、淡 `#b8c1c8`、分隔线 `#d3d9dd`、前缀 `#4f6d8a`、词根 `#557a6a`、后缀 `#8a939b`、高亮 `#d9e4ee`。
- 字体：英文 `"Sitka Display", Cambria, Georgia, serif`；中文释义 `"Noto Serif SC", "SimSun", serif`；字幕与界面 `"Noto Sans SC", "Microsoft YaHei", sans-serif`；单词 96 px。
- 线稿：色值映射、线宽 ×0.62、箭头 marker id 加画面名前缀；word-family 网页版不受影响（只在 video 侧处理 kit.js 的输出）。
- 弹簧：平滑 `damping 200`、轻弹 `damping 20 / stiffness 170`（mass 1，与 Remotion 同一套物理）。转场：线稿→线稿、进入章节卡用上推 0.8 s，其余交叉淡化 0.5 s；转场与上一节拍末尾的静音重叠，不额外占时长。
- 出片条件：`approved`、指纹一致、无 `>>` 批注、`plan` 无错误；不满足拒绝并说明原因。成片时长与 timeline 一致（±0.2 s）。
- 屏幕上的文字只有：单词、词素小注、短释义、引文原文、章节标题、进度条、署名、字幕。不出现与解说逐句重复的句子。
- 用户可见文字中文；报错带行号和改法；注释只写"为什么"。
- 单元测试：`python -I skills/word-family-video/scripts/test_script.py`（浏览器相关测试在没有 Playwright 时跳过并打印 SKIP）。

## Review Focus

- 同一页上有多张线稿（舞台里的线稿 + 家族图 + 章节卡）：箭头 marker id 必须按画面加前缀，否则后建的 `<defs>` 让前面的箭头头消失（Task 1 `test_restyle_svg_prefixes_markers`，Task 3 audit 的箭头检查）。
- 课程 JSON 里写死的暖色（`#b84a14`、`#176b4d`、`#fdf0e6` 等，出现在 scene 零件参数里）也要映射成冷色（Task 1 `test_frame_data_maps_lesson_colors`）。
- 照片路径带中文/空格/括号（`Receipt_from_the_store_(PNG).jpg`）：页面里要按 file URI 正确加载，stills 不能出现裂图（Task 1 `test_frame_data_photo_uri`，Task 3 audit 的 `img.naturalWidth == 0` 检查）。
- 脚本在 plan 之后被改过（timeline 指纹过期）：stills / preview / render 不能拿旧时间轴出图，要自动重跑时间轴（配音命中缓存）（Task 4 `test_render_gate_*`）。
- 触发点只能估算或不存在（`[pair]` 没写 `{A}`、`[quiz]` 没写答案触发词）：元素要有合理的默认出场时刻，不能永远不出现（Task 1 `test_frame_data_default_cue_times`）。

---

## 文件结构

- Modify: `skills/word-family-video/scripts/video.py` —— 新增「画面数据」一节（`restyle_svg` 不在这里，见下）、`frame_data`、`write_frame_v2`、`cmd_preview`、`cmd_stills_v2`、`cmd_render_v2`、`check` 改为从脚本取句子；Task 7 删 v1。
- Create: `skills/word-family-video/scripts/frame_data.py` —— 纯函数：`prefix_motion(cn)`、`map_colors(obj)`、`stage_plan(beats)`、`frame_data(stem, L, tl, project_dir, wf_dir)`。不 import playwright/edge-tts，便于测试。
- Rewrite: `skills/word-family-video/assets/frame.html` —— v2 画面（旧版 Task 7 前先另存为 `assets/frame_v1.html` 供 v1 路径用，Task 7 删除）。
- Modify: `skills/word-family-video/scripts/test_script.py` —— 新增测试。
- Create: `skills/word-family-video/projects/tract/script.md`、`projects/pend/script.md`（写稿子代理）。
- Delete（Task 7）：`assets/frame_v1.html`、`references/narration_guide.md`、`projects/tract/narration.json`、`projects/pend/narration.json`、video.py 的 v1 函数。
- Modify（Task 8）：`SKILL.md`、`使用说明.md`、`references/script_guide.md`（七、画面块补版式说明）、`evals/fix-pronunciation.json`、新建 `evals/render-unapproved.json`、`evals/baseline.md`。

---

### Task 1: 画面数据（frame_data.py）

**Files:**
- Create: `skills/word-family-video/scripts/frame_data.py`
- Test: `skills/word-family-video/scripts/test_script.py`

**Interfaces:**
- Consumes: `timeline.json` 的结构（第一期 `build_timeline`）：`{"total", "words", "beats": [{"lineno","title","block","arg","data":[[k,v]],"t0","t1","lines":[{"plain","s","e","cues":{词:秒}}]}], "subs":[{"s","e","t"}]}`；`script_md.norm_part`。
- Produces:
  - `COLOR_MAP: dict[str, str]`（暖色 → 冷色，键小写）
  - `map_colors(obj) -> obj`：递归替换字符串里的色值（大小写不敏感）。
  - `prefix_motion(cn: str, kind: str) -> str`：返回 `"down"|"up"|"out"|"back"|"together"|"apart"|"toward"|"forward"|"across"|"shrink"|"rise"`（`kind != "p"` 一律 `"rise"`）。
  - `stage_plan(beats: list) -> list[dict]`：每个节拍 `{"layer": "full"|"split", "stage": {"kind":"scene"|"photo"|None,"ref":str,"full":bool}, "left": {"kind":"word"|"root"|"carry"|None,"ref":str}, "trans": "push"|"fade", "keep_root": bool}`。
  - `frame_data(stem, L, tl, project_dir: Path, wf_dir: Path) -> dict`：注入页面的全部数据 `{"lesson": L', "beats": [...], "subs", "total", "words", "root", "title"}`，每个 beat 在 timeline 字段之上加 `plan`（上面的 dict）和 `view`（块专属数据，见 Step 3）。

- [ ] **Step 1: 写失败的测试**（追加到 `test_script.py` 的 `if __name__` 之前）

```python
import frame_data as fd  # noqa: E402


def _tl(*beats):
    out, t = [], 0.0
    for blk, arg, lines, data in beats:
        rows = [{"lineno": 1, "text": p, "plain": p.replace("{", "").replace("}", ""), "s": t + 0.5 + i,
                 "e": t + 1.4 + i, "cues": cues} for i, (p, cues) in enumerate(lines)]
        out.append({"lineno": 1, "title": arg or blk, "block": blk, "arg": arg, "data": data,
                    "t0": t, "t1": t + 1 + len(lines), "lines": rows})
        t += 1 + len(lines)
    return {"total": t, "words": [b[1] for b in beats if b[0] == "word"], "beats": out, "subs": []}


def test_prefix_motion():
    assert fd.prefix_motion("在…上", "p") == "down"
    assert fd.prefix_motion("从下、下面", "p") == "up"
    assert fd.prefix_motion("往外", "p") == "out"
    assert fd.prefix_motion("回（这里的确切含义存疑）", "p") == "back"
    assert fd.prefix_motion("一起", "p") == "together"
    assert fd.prefix_motion("分开", "p") == "apart"
    assert fd.prefix_motion("朝向", "p") == "toward"
    assert fd.prefix_motion("提前、在前", "p") == "forward"
    assert fd.prefix_motion("在中间", "p") == "across"
    assert fd.prefix_motion("不", "p") == "shrink"
    assert fd.prefix_motion("拿", "r") == "rise"
    assert fd.prefix_motion("什么都不是", "p") == "rise"


def test_frame_data_maps_lesson_colors():
    out = fd.map_colors({"scene": [{"k": "tag", "c": "#B84A14"}, {"fill": "#fdf0e6"}], "x": "#176b4d 和 #2b5c8f"})
    assert out["scene"][0]["c"] == "#4f6d8a" and out["scene"][1]["fill"] == "#d9e4ee"
    assert out["x"] == "#557a6a 和 #4f6d8a"


def test_stage_plan_layers_and_transitions():
    tl = _tl(("photo", "media/a.jpg", [("x", {})], []), ("scene", "anchor", [("y", {})], []),
             ("scene", "w1", [("z", {})], []), ("word", "w1", [("{w1}", {"w1": 3.0})], []),
             ("title", "", [], []), ("event", "", [("e", {})], []), ("word", "w2", [("{w2}", {})], []))
    P = fd.stage_plan(tl["beats"])
    assert [p["layer"] for p in P] == ["split", "split", "split", "split", "full", "full", "split"]
    assert P[0]["stage"] == {"kind": "photo", "ref": "media/a.jpg", "full": False}
    assert P[1]["left"]["kind"] == "root" and P[2]["trans"] == "push"          # 线稿 → 线稿：上推
    assert P[3]["stage"] == {"kind": "scene", "ref": "w1", "full": False}       # [word] 沿用前一拍的舞台
    assert P[4]["trans"] == "push" and P[5]["trans"] == "fade"                  # 进入章节卡：上推
    assert P[6]["stage"] == {"kind": "scene", "ref": "w2", "full": False}       # 前一拍是整屏块：用这个词自己的线稿


def test_stage_plan_keep_root():
    tl = _tl(("word", "attract", [("a", {})], []), ("word", "distract", [("b", {})], []),
             ("word", "spend", [("c", {})], []))
    roots = {"attract": "tract", "distract": "tract", "spend": "pend"}
    P = fd.stage_plan(tl["beats"], roots)
    assert [p["keep_root"] for p in P] == [False, True, False]


def test_frame_data_default_cue_times():
    tl = _tl(("pair", "accept | except", [("同一只手。", {}), ("一个进一个出。", {})], []),
             ("quiz", "", [("猜猜看。", {}), ("答案。", {})], []))
    D = fd.frame_data("pend", L, tl, Path("."), Path("."))
    a, b = D["beats"][0]["view"]["items"]
    assert a["at"] < b["at"] <= tl["beats"][0]["t1"]                            # 没写触发词：按句子依次出场
    q = D["beats"][1]["view"]
    assert q["reveal"] == tl["beats"][1]["lines"][-1]["s"]                      # 没写答案触发词：最后一句揭晓


def test_frame_data_photo_uri():
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        proj = Path(d) / "x"
        (proj / "media").mkdir(parents=True)
        (proj / "media" / "Receipt (PNG) 小票.jpg").write_bytes(b"\xff\xd8")
        tl = _tl(("photo", "media/Receipt (PNG) 小票.jpg", [("x", {})], [["署名", "照片：A，CC0"]]))
        D = fd.frame_data("pend", L, tl, proj, Path("."))
        v0 = D["beats"][0]["view"]
        assert v0["src"].startswith("file:///") and "%28PNG%29" in v0["src"] and v0["credit"] == "照片：A，CC0"


def test_frame_data_map_nodes():
    tl = _tl(("map", "", [("pending 和 suspend 都是挂。", {}), ("spend 是付钱。", {})], []))
    D = fd.frame_data("pend", L, tl, Path("."), Path("."))
    at = D["beats"][0]["view"]["nodeAt"]
    assert at["suspend"] == tl["beats"][0]["lines"][0]["s"] and at["spend"] == tl["beats"][0]["lines"][1]["s"]
```

（`L` 是 test_script.py 已有的 pend 课程夹具：主词 depend、suspend，finale spend，迁移题 pending、pension。）

- [ ] **Step 2: 运行，确认失败**

Run: `python -I skills/word-family-video/scripts/test_script.py`
Expected: 新测试 FAIL（`ModuleNotFoundError: frame_data` 导致整个文件导入失败也算——先建空文件 `frame_data.py` 再跑，看到每条新测试各自 FAIL）。

- [ ] **Step 3: 实现 `frame_data.py`**

```python
"""script.md 的时间轴 → 画面数据。frame.html 只负责画：放哪一层、舞台放什么、何时出场，都在这里决定（可测试）。"""
import json
import re
from pathlib import Path

import script_md as smd

# 课程线稿是 word-family 网页版的暖色；视频用冷色（设计 §7）。课程 JSON 里写死的色值同样替换
COLOR_MAP = {"#1e242b": "#27303a", "#b84a14": "#4f6d8a", "#176b4d": "#557a6a", "#2b5c8f": "#4f6d8a",
             "#9aa0a8": "#b8c1c8", "#5e6670": "#7b8690", "#6b717a": "#7b8690", "#fdf0e6": "#d9e4ee",
             "#e7f3ee": "#e3ebe7", "#eef0f2": "#e9ecee", "#d6d0c4": "#d3d9dd", "#e4dfd5": "#d3d9dd",
             "#fbf9f4": "#f4f6f7", "#d9d2c5": "#cfd6db", "#f3d9c6": "#dfe5ea"}
_HEX = re.compile(r"#[0-9a-fA-F]{6}\b")

# 前缀按意思入场（§7）：按 cn 里的关键词判断，先匹配的优先
MOTIONS = [("shrink", ("不", "非", "无", "否", "反")), ("apart", ("分开", "离")), ("together", ("一起", "共同", "合")),
           ("back", ("回", "再")), ("out", ("外", "出")), ("up", ("从下", "下")), ("down", ("上",)),
           ("toward", ("朝", "向", "加到", "到")), ("forward", ("前",)), ("across", ("横跨", "穿过", "中间", "之间"))]


def map_colors(obj):
    if isinstance(obj, str):
        return _HEX.sub(lambda m: COLOR_MAP.get(m.group(0).lower(), m.group(0)), obj)
    if isinstance(obj, list):
        return [map_colors(x) for x in obj]
    if isinstance(obj, dict):
        return {k: map_colors(v) for k, v in obj.items()}
    return obj


def prefix_motion(cn: str, kind) -> str:
    if kind != "p":
        return "rise"
    for name, keys in MOTIONS:
        if any(k in (cn or "") for k in keys):
            return name
    return "rise"
```

注意 `MOTIONS` 的顺序要让测试通过："回（这里的确切含义存疑）"含"在"不含"不"——`shrink` 的关键词只放单字否定前缀含义（"不" 会误伤"不发音"这类长释义，所以只在 `cn` 去掉括号注释后、长度 ≤ 4 时才判 shrink）。实现时：`core = re.sub(r"（[^）]*）|\([^)]*\)", "", cn)`，只用 `core` 匹配；`shrink` 额外要求 `len(core) <= 4`。"在中间" 要命中 across 而不是 down/forward：`across` 的检查放在 `down`、`forward` 之前。按测试调整列表顺序为：shrink、apart、together、back、out、across、up、down、toward、forward。

```python
FULL = {"title", "event", "pair", "map", "quiz"}


def stage_plan(beats, roots=None) -> list:
    """每个节拍放哪一层、舞台放什么、怎么转场。roots: 词 → 词根词素（判断相邻两词是否同根）。"""
    roots, out, stage, prev_word = roots or {}, [], None, None
    for b in beats:
        blk, arg = b["block"], (b.get("arg") or "").strip()
        p = {"layer": "full" if blk in FULL else "split", "stage": None, "left": {"kind": None, "ref": ""},
             "trans": "fade", "keep_root": False}
        full_photo = blk == "photo" and any(k == "版式" and v.startswith("整屏") for k, v in b.get("data", []))
        if blk == "scene":
            stage = {"kind": "scene", "ref": arg, "full": False}
        elif blk == "photo":
            stage = {"kind": "photo", "ref": arg, "full": full_photo}
        elif blk == "word":
            if stage is None:                       # 前一拍是整屏块或片头：用这个词自己的线稿
                stage = {"kind": "scene", "ref": arg, "full": False}
            p["left"] = {"kind": "word", "ref": arg}
            p["keep_root"] = bool(prev_word and roots.get(prev_word) and roots.get(prev_word) == roots.get(arg))
            prev_word = arg
        if p["layer"] == "full":
            stage, prev_word = None, None
        else:
            p["stage"] = dict(stage)
            if blk == "scene" and arg == "anchor":
                p["left"] = {"kind": "root", "ref": ""}
            elif blk in ("scene", "photo") and not full_photo and out and out[-1]["left"]["kind"] == "word":
                p["left"] = {"kind": "carry", "ref": out[-1]["left"]["ref"]}
        prev = out[-1] if out else None
        if blk == "title" or (prev and prev["stage"] and p["stage"] and prev["stage"]["kind"] == "scene"
                              and blk == "scene" and prev["stage"]["ref"] != p["stage"]["ref"]):
            p["trans"] = "push"
        out.append(p)
    return out
```

```python
def _lesson_words(L):
    return {w["w"].lower(): w for w in L.get("words", []) + ([L["finale"]] if L.get("finale") else [])}


def _cue_or(line_cues, word, fallback):
    for c, t in line_cues:
        if c.lower() == word.lower():
            return t
    return fallback


def frame_data(stem, L, tl, project_dir: Path, wf_dir: Path) -> dict:
    words = _lesson_words(L)
    roots = {k: next((p["m"] for p in map(smd.norm_part, w["parts"]) if p.get("kind") == "r"), "") for k, w in words.items()}
    plans = stage_plan(tl["beats"], roots)
    beats = []
    for b, plan in zip(tl["beats"], plans):
        lines = b["lines"]
        cues = [(c, t) for r in lines for c, t in r["cues"].items()]
        data = {k: v for k, v in b.get("data", [])}
        starts = [r["s"] for r in lines] or [b["t0"] + 0.4]
        view = {}
        blk, arg = b["block"], (b.get("arg") or "").strip()
        if blk == "word":
            w = words.get(arg.lower())
            if w:
                parts = [dict(p, motion=prefix_motion(p.get("cn", ""), p.get("kind"))) for p in map(smd.norm_part, w["parts"])]
                view = {"w": w["w"], "split": w.get("split", []), "parts": parts, "meaning": _short(w.get("meaning", "")),
                        "cues": {c: t for c, t in cues}, "whole": _cue_or(cues, w["w"], starts[-1])}
            else:                                   # 课程外的同族词：只显示整词和 > 释义
                view = {"w": arg, "split": [], "parts": [], "meaning": data.get("释义", ""),
                        "cues": {c: t for c, t in cues}, "whole": _cue_or(cues, arg, starts[0])}
        elif blk == "photo":
            src = (wf_dir / "lessons" / L["opening"]["photo"]["file"]) if arg == "opening" else (project_dir / arg)
            credit = data.get("署名") or (L["opening"].get("photo", {}).get("credit", "") if arg == "opening" else "")
            view = {"src": src.resolve().as_uri(), "credit": credit}
        elif blk == "event":
            view = {"head": data.get("事件", ""), "quote": data.get("原文", ""), "source": data.get("来源", ""),
                    "cues": {c: t for c, t in cues}}
        elif blk == "pair":
            a, _, c = arg.partition("|")
            items = []
            for i, x in enumerate((a.strip(), c.strip())):
                w = words.get(x.lower())
                items.append({"w": x, "split": (w or {}).get("split", []), "meaning": _short((w or {}).get("meaning", "")),
                              "at": _cue_or(cues, x, starts[min(i, len(starts) - 1)] + (0.6 if len(starts) == 1 and i else 0))})
            view = {"items": items}
        elif blk == "map":
            node_at = {}
            for k in words:
                hit = next((r["s"] for r in lines if re.search(rf"(?<![A-Za-z]){re.escape(k)}(?![A-Za-z])", r["plain"], re.I)), None)
                if hit is not None:
                    node_at[k] = hit
            view = {"nodeAt": node_at, "start": starts[0]}
        elif blk == "quiz":
            qs = L.get("transfer", [])
            ans = smd.quiz_words(L)
            hit = next(((i, t) for c, t in cues for i, a in enumerate(ans) if c.lower() == a), None)
            idx = [hit[0]] if hit else list(range(len(qs)))
            view = {"items": [{"q": qs[i][0], "a": _short(qs[i][1])} for i in idx],
                    "reveal": hit[1] if hit else starts[-1]}
        elif blk == "title":
            view = {"text": b["title"]}
        beats.append(dict(b, plan=plan, view=view))
    Lv = map_colors(json.loads(json.dumps(L)))
    return {"lesson": Lv, "beats": beats, "subs": tl["subs"], "total": tl["total"], "words": tl["words"],
            "root": {"m": L["root"]["m"], "cn": L["root"]["cn"],
                     "variants": [v["m"] for v in L["root"].get("variants") or []]}, "stem": stem}


def _short(s: str) -> str:
    """释义只留第一项，屏幕上不出现整句。"""
    s = re.sub(r"<[^>]+>", "", s or "")
    return re.split(r"[；;。]", s)[0].strip()
```

`frame_data` 的 pair 默认时刻：两句及以上时 A 在第 1 句、B 在第 2 句开始；只有一句时 B 比 A 晚 0.6 s——测试 `test_frame_data_default_cue_times` 覆盖前者。

- [ ] **Step 4: 运行，确认通过**

Run: `python -I skills/word-family-video/scripts/test_script.py`
Expected: 全部通过（含 7 条新测试）。

- [ ] **Step 5: 用真数据冒烟**

Run: `python -I -c "import sys,json;sys.path.insert(0,'skills/word-family-video/scripts');sys.stdout.reconfigure(encoding='utf-8');import frame_data as fd;from pathlib import Path;L=json.load(open('skills/word-family/lessons/cap.json',encoding='utf-8'));tl=json.load(open('skills/word-family-video/projects/cap/build/timeline.json',encoding='utf-8'));D=fd.frame_data('cap',L,tl,Path('skills/word-family-video/projects/cap'),Path('skills/word-family'));print([ (b['block'],b['plan']['layer'],b['plan']['trans'],(b['plan']['stage'] or {}).get('ref')) for b in D['beats']])"`
Expected: 19 项；`[word]` 节拍的 stage ref 是前一拍的线稿/照片；`[event]/[pair]/[map]/[quiz]/[title]` 为 full。

---

### Task 2: 新 frame.html（8 种画面块、进度条、弹簧与转场）

**Files:**
- Copy: `skills/word-family-video/assets/frame.html` → `assets/frame_v1.html`（v1 路径改读 `FRAME_V1`，Task 7 删）
- Rewrite: `skills/word-family-video/assets/frame.html`
- Modify: `skills/word-family-video/scripts/video.py`（`FRAME_V1` 常量；`page_html` 改读 `FRAME_V1`；新增 `write_frame_v2`）
- Test: `test_script.py`（浏览器冒烟）

**Interfaces:**
- Consumes: Task 1 `frame_data(...)` 的输出；word-family `kit.js` 的 `scene(sc, caption)`、`familyMap(L)`、`esc`、`textW`。
- Produces:
  - 页面全局函数 `setT(t) -> bool`（是否需要重新截图）、`audit() -> list[str]`（Task 3 用）、`restyleSvg(html, prefix) -> string`。
  - `video.write_frame_v2(stem, L, tl) -> Path`（写 `build/frame.html`）。
  - 注入占位：`/*__DATA_JSON__*/null`、`/*__KIT_JS__*/`、`/*__EXTRA__*/`（preview 用）。

- [ ] **Step 1: 写失败的浏览器冒烟测试**

```python
def _browser():
    try:
        import playwright  # noqa: F401
    except ImportError:
        return None
    return True


def test_frame_v2_smoke():
    if not _browser():
        print("SKIP test_frame_v2_smoke（没装 Playwright）")
        return
    tlp = v.PROJECTS / "cap" / "build" / "timeline.json"
    if not tlp.exists():
        print("SKIP test_frame_v2_smoke（先 plan cap）")
        return
    stem, Lc = v.load_lesson("cap")
    tl = json.loads(tlp.read_text(encoding="utf-8"))
    hp = v.write_frame_v2(stem, Lc, tl)
    pw, browser, page = v.open_page(hp)
    try:
        for b in tl["beats"]:
            page.evaluate("t => setT(t)", b["t1"] - 0.5)
            assert page.evaluate("() => document.querySelectorAll('.beat.on').length") >= 1, b["title"]
        page.evaluate("t => setT(t)", 0.0)
        assert page.evaluate("() => !document.querySelector('.hd')")                   # 没有常驻顶栏
        assert page.evaluate("() => !!document.querySelector('#prog')")                  # 顶部进度条
        assert page.evaluate("() => getComputedStyle(document.body).backgroundColor") == "rgb(238, 241, 242)"
    finally:
        browser.close()
        pw.stop()
```

- [ ] **Step 2: 运行，确认失败**

Run: `python -I skills/word-family-video/scripts/test_script.py`
Expected: `FAIL test_frame_v2_smoke - AttributeError ... write_frame_v2`

- [ ] **Step 3: 另存 v1 模板，加 `write_frame_v2`**

`cp assets/frame.html assets/frame_v1.html`；video.py：

```python
FRAME_V1 = HERE / "assets" / "frame_v1.html"   # v1（narration.json）专用，第三期随 v1 一起删
```

`page_html` 里 `FRAME.read_text` 改成 `FRAME_V1.read_text`。新增：

```python
sys.path.insert(0, str(Path(__file__).resolve().parent))
import frame_data as fdata  # noqa: E402


def frame_html(stem, L, tl, extra: str = "") -> str:
    D = fdata.frame_data(stem, L, tl, PROJECTS / stem, WF)
    html = FRAME.read_text(encoding="utf-8")
    html = html.replace("/*__KIT_JS__*/", (WF / "assets" / "kit.js").read_text(encoding="utf-8"))
    html = html.replace("/*__EXTRA__*/", extra)
    return html.replace("/*__DATA_JSON__*/null", json.dumps(D, ensure_ascii=False).replace("</", "<\\/"))


def write_frame_v2(stem, L, tl, name="frame.html", extra="") -> Path:
    build = PROJECTS / stem / "build"
    build.mkdir(parents=True, exist_ok=True)
    hp = build / name
    hp.write_text(frame_html(stem, L, tl, extra), encoding="utf-8")
    return hp
```

- [ ] **Step 4: 写新 frame.html**

结构要点（完整实现写进文件；下面是必须一致的骨架与算法）：

```html
<style>
  :root { --bg:#eef1f2; --bg2:#e2e7e9; --ink:#27303a; --muted:#7b8690; --faint:#b8c1c8; --rule:#d3d9dd;
          --pre:#4f6d8a; --root:#557a6a; --suf:#8a939b; --hi:#d9e4ee;
          --en:"Sitka Display", Cambria, Georgia, serif; --zh:"Noto Serif SC", "SimSun", serif;
          --ui:"Noto Sans SC", "Microsoft YaHei", sans-serif; }
  html, body { width:1920px; height:1080px; overflow:hidden; margin:0; }
  body { background: radial-gradient(ellipse at 50% 45%, var(--bg) 55%, var(--bg2) 100%); background-color: var(--bg);
         color: var(--ink); font-family: var(--ui); }
  /* 分区：进度条 0–96；主区 120–900（左 120–900px 宽，舞台 960–1800）；字幕 930–1030 */
  #prog { position:absolute; left:96px; right:96px; top:34px; height:44px; display:flex; align-items:center; gap:28px;
          border-bottom:1px solid var(--rule); font-size:24px; }
  #prog .w { font-family:var(--en); color:var(--faint); padding-bottom:8px; border-bottom:3px solid transparent; }
  #prog .w.done { color:var(--muted); } #prog .w.now { color:var(--ink); border-color:var(--pre); }
  #prog .n { margin-left:auto; color:var(--muted); font-variant-numeric: tabular-nums; }
  .beat { position:absolute; inset:0; opacity:0; }
  .left { position:absolute; left:120px; top:250px; width:780px; }
  .stage { position:absolute; left:960px; top:170px; width:840px; height:640px; display:flex; align-items:center; justify-content:center; }
  .stage svg { width:100%; height:auto; overflow:visible; }
  .stage .photo { width:100%; height:100%; overflow:hidden; border-radius:6px; }
  .stage .photo img { width:100%; height:100%; object-fit:cover; }
  .stage.full { left:0; top:0; width:1920px; height:1080px; }
  .credit { position:absolute; right:40px; bottom:18px; font-size:16px; color:var(--muted); }
  .wordrow { font-family:var(--en); font-size:96px; font-weight:600; display:flex; align-items:flex-end; white-space:nowrap; }
  .morph { display:inline-flex; flex-direction:column; align-items:center; }
  .morph small { font-family:var(--zh); font-size:26px; color:var(--muted); margin-top:6px; }
  .p { color:var(--pre); } .r { color:var(--root); } .s { color:var(--suf); }
  .meaning { font-family:var(--zh); font-size:40px; margin-top:28px; }
  .sub { position:absolute; left:0; right:0; top:950px; text-align:center; font-size:42px; font-weight:600; color:var(--ink);
         text-shadow: 0 0 18px var(--bg), 0 0 8px var(--bg), 0 0 3px var(--bg); }
</style>
<body><div id="prog"></div><div id="beats"></div><div class="sub" id="sub"></div>
<script>
const DATA = /*__DATA_JSON__*/null;
/*__KIT_JS__*/
// 弹簧：与 Remotion 同一套物理（mass 1）；按帧积分，结果只取决于 t，逐帧截图可复现
function spring(t, { damping = 200, stiffness = 100, mass = 1 } = {}) {
  if (t <= 0) return 0;
  let x = 0, v = 0; const dt = 1 / 240, n = Math.min(Math.ceil(t / dt), 2400);
  for (let i = 0; i < n; i++) { const a = (-stiffness * (x - 1) - damping * v) / mass; v += a * dt; x += v * dt; }
  return x;
}
const SMOOTH = { damping: 200 }, BOUNCY = { damping: 20, stiffness: 170 };
```

- `restyleSvg(html, prefix)`：`stroke-width="x"` → `x*0.62`；`id="foo"` → `id="prefix-foo"`，`url(#foo)` → `url(#prefix-foo)`；`href="#foo"` 同理。线稿颜色已由 Python `map_colors` 处理了课程 JSON；kit.js 常量里的暖色在注入前由 Python 对 kit.js 文本做同一次 `map_colors` 替换（`frame_html` 里对 kit.js 文本调用 `fdata.map_colors`）。
- 页面加载时为每个节拍建一个 `<section class="beat" data-i>`：
  - `split` 层：`.left`（word：每个词素一个 `.morph` 元素 + `.meaning`；root：词根大字 + 释义 + 变体行；carry：上一拍的整词静态显示，不带释义）+ `.stage`（scene：`restyleSvg(scene(L 中对应 scene, caption), "b"+i)`；photo：`<div class="photo"><img src></div>`，`full` 时 `.stage.full` 并显示 `.credit`；非整屏照片也在照片下沿显示一行小号署名）。
  - `full` 层：title（居中 120px 章节标题 + 下方 `root.m 一家` 小字）、event（上方 `> 事件` 小字、中间引文原文 54px 衬线体，每个 `{cue}` 片段包 `<mark data-at>`，下方来源域名小字）、pair（左右两个大词 + 短释义，中间竖分隔线）、map（`restyleSvg(familyMap(L), "map")`，节点 `[data-node]` 按 `nodeAt` 点亮，未提到的保持 0.15）、quiz（题面 `q`，揭晓时显示 `a`）。
- 进度条：`DATA.words`（脚本顺序的 `[word]` 词）；当前节拍之前最后一个 `[word]` 为 now，之前的 done，其余淡；右侧 `"02 / 07"`；标题 `root.m 一家`。
- 每帧 `setT(t)`：
  - 找当前节拍 i（`t < beats[i].t1`）。转场窗口 `W = trans=="push" ? 0.8 : 0.5`，从 `t0 - min(W, 0.45)` 开始：`q = spring(t - start, SMOOTH)`；fade：旧层 `opacity 1-q`，新层 `q`；push：旧层 `translateY(-120q px)` 且淡出，新层从 `+120(1-q)` 上来。只有 i-1、i 两层可见，其余 `opacity:0`。
  - `split` 层：舞台与上一拍相同（`stage` 深度相等）时舞台不参与转场（不闪），只换左侧。
  - 词素入场：每个 `.morph` 的出场时刻 = `cues[词素去连字符]`，否则按词素顺序从第一句开始每 0.5 s 一个；`keep_root` 为真时词根从 t0 起就在。动效按 `motion`：down `y:-80→0`、up `y:80→0`、out `x:-60→0`（从词根方向滑出）、back `x:120→0`、together `x:±90→0`（向词根合拢）、apart 先 `x:0` 再弹开留 12px 缝、toward `x:-140→0`、forward `x:-40→0 + scale .9→1`、across `x:260→0`、shrink `scale 1.15→1`、rise `y:24→0`；位移用 `BOUNCY`，透明度用 `SMOOTH`。变体（parts 里带 `of` 的词素）：先显示 `of`（原形），到它自己的触发时刻（或原形出场 +0.8 s）换成 `m`。念到整词（`whole`）时词素间距 `gap 24px→0` 合拢、`.meaning` 浮现。
  - 线稿逐笔画出（沿用 v1 `prepDraw/applyDraw` 的算法，在节拍 t0+0.3 开始、1.8 s 画完），画完后镜头 `scale 1.00→1.05`（到 t1 线性）。照片 `scale 1.00→1.06` 缓推。
  - event 的 `<mark>`：到时刻背景从透明过渡到 `var(--hi)`。
  - 字幕：`DATA.subs` 找当前段。
  - 返回值：有任何元素处在过渡中（0<q<1）、画线中、镜头缓推中、字幕变化或节拍变化时为 true。
- `window.setT = setT; window.audit = audit;`

- [ ] **Step 5: 运行冒烟测试**

Run: `python -I skills/word-family-video/scripts/test_script.py`
Expected: 全部通过（`test_frame_v2_smoke` PASS，不是 SKIP）。

- [ ] **Step 6: 目视检查 6 张关键帧**

写一个临时脚本（放在台账目录 `.superpowers/sdd/2026-10-28-word-family-video-v2-phase2/`）对 cap 截 photo、anchor、word（capture 词素出场中途和末尾）、event、pair、map 六帧，用 Read 看图；不对就改 frame.html 再看。没有截图前不进入 Task 3。

---

### Task 3: 自检 audit() + stills

**Files:**
- Modify: `assets/frame.html`（`audit()`）、`scripts/video.py`（`cmd_stills_v2`、`ensure_timeline`）
- Test: `test_script.py`

**Interfaces:**
- Produces:
  - 页面 `audit() -> string[]`：当前可见节拍的问题，每条形如 `"出界：.meaning 超出画面 (x=1890..2010)"`。
  - `video.ensure_timeline(stem, L, a, quiet=True) -> (sc, tl, clips) | None`：脚本有错误时打印并返回 None；timeline 缺失或指纹过期时重算（配音命中缓存）并写回 `build/timeline.json`。`cmd_plan_script` 改为调用它。
  - `video.cmd_stills_v2(stem, L, a) -> int`：每个节拍 `t1 - 0.5` 一张 `stills/NN_<block>.png` + `_sheet.jpg`；每张调用 `audit()`，有问题列出并返回 1。

- [ ] **Step 1: 写失败的测试**

```python
def test_audit_catches_overflow_and_missing_marker():
    if not _browser():
        print("SKIP test_audit_catches_overflow_and_missing_marker（没装 Playwright）")
        return
    tlp = v.PROJECTS / "cap" / "build" / "timeline.json"
    if not tlp.exists():
        print("SKIP（先 plan cap）")
        return
    stem, Lc = v.load_lesson("cap")
    tl = json.loads(tlp.read_text(encoding="utf-8"))
    pw, browser, page = v.open_page(v.write_frame_v2(stem, Lc, tl))
    try:
        b = next(x for x in tl["beats"] if x["block"] == "word")
        page.evaluate("t => setT(t)", b["t1"] - 0.5)
        assert page.evaluate("() => audit()") == []
        page.evaluate("""() => { const m = document.querySelector('.beat.on .meaning'); m.style.marginLeft = '1500px'; }""")
        assert any("出界" in x for x in page.evaluate("() => audit()"))
        m = next(x for x in tl["beats"] if x["block"] == "map")
        page.evaluate("t => setT(t)", m["t1"] - 0.5)
        page.evaluate("""() => document.querySelectorAll('.beat.on marker').forEach(e => e.remove())""")
        assert any("箭头" in x for x in page.evaluate("() => audit()")) or \
            page.evaluate("() => !document.querySelector('.beat.on [marker-end]')")
    finally:
        browser.close()
        pw.stop()


def test_ensure_timeline_refreshes_stale(monkeypatch=None):
    import tempfile
    import types
    with tempfile.TemporaryDirectory() as d:
        old = v.PROJECTS
        v.PROJECTS = Path(d)
        calls = []
        real = v.synth_all
        v.synth_all = lambda lines, sa, voice, rate, marks=False: calls.append(len(lines)) or {s: Path(d) / "x.mp3" for s in lines}
        real_decode, real_marks = v.decode, v.tts_marks
        v.decode = lambda mp3, sr=v.SR: v.np.zeros(int(sr * 1.0), v.np.int16)
        v.tts_marks = lambda mp3: []
        try:
            (Path(d) / "pend").mkdir()
            (Path(d) / "pend" / "script.md").write_text(CLEAN, encoding="utf-8")
            a = types.SimpleNamespace(voice=v.VOICE, rate=v.RATE)
            sc, tl, _ = v.ensure_timeline("pend", L, a)
            assert tl["fingerprint"] == smd.fingerprint(CLEAN) and calls
            (Path(d) / "pend" / "script.md").write_text(CLEAN.replace("从底下", "从下面", 1), encoding="utf-8")
            sc2, tl2, _ = v.ensure_timeline("pend", L, a)
            assert tl2["fingerprint"] != tl["fingerprint"]
        finally:
            v.PROJECTS, v.synth_all, v.decode, v.tts_marks = old, real, real_decode, real_marks
```

- [ ] **Step 2: 运行，确认失败**

Expected: 两条新测试 FAIL（`audit is not defined` / `no attribute ensure_timeline`）。

- [ ] **Step 3: 实现**

`audit()`：对 `.beat.on`（透明度 > 0.5 的那一层）里所有 `.chk` 元素（词素、整词、释义、引文、标题、题面、照片、舞台 svg、署名）+ `#sub`（有字时）+ `#prog`：
- 出界：`getBoundingClientRect()` 任一边超出 `0..1920 × 0..1080`（留 8px 余量）。
- 重叠：左侧区（`.left` 内元素的并集）与舞台区（`.stage` 的 rect）相交；任何 `.chk` 文本与字幕 rect 相交；进度条与主区相交。
- 箭头：可见 svg 里每个 `[marker-end]`，`url(#id)` 在文档里找不到 → `"箭头缺失：<prefix>"`。
- 裂图：可见 `img` 的 `naturalWidth == 0`。
- 文字溢出线稿框：svg 内 `text` 的 bbox 超出它所在 `<g>` 里第一个 `rect/ellipse` 的 bbox（只查同组内有形状的；修第一期发现的 RECEIPT 那一类）。

`ensure_timeline`：把 `cmd_plan_script` 里"解析→配音→build_timeline→写 timeline.json"抽出来；`cmd_plan_script` 调用它，再写 preview.mp3 和打印节拍表（输出与现在一致）。

`cmd_stills_v2`：`ensure_timeline` → `write_frame_v2` → 逐节拍截图 + audit → 总览图（沿用 v1 的 PIL 拼图）→ 打印问题，有问题返回 1。

- [ ] **Step 4: 运行测试，全部通过**

- [ ] **Step 5: `stills cap`，看总览图和每一张有问题的定格图，修到 audit 无问题**

Run: `python -I skills/word-family-video/scripts/video.py stills cap`
Expected: 退出码 0，打印 `定格图：…（总览 _sheet.jpg），自检无问题`。Read `_sheet.jpg` 目视确认。

---

### Task 4: preview、render、check 接入脚本

**Files:**
- Modify: `scripts/video.py`（`cmd_preview`、`cmd_render_v2`、`check_lines`、`main` 分派）
- Test: `test_script.py`

**Interfaces:**
- Consumes: `ensure_timeline`、`write_frame_v2(extra=...)`、`mix_timeline`、`write_audio`、`smd.gate`、`open_page`。
- Produces: 命令 `preview <课>`（不要求 approved）、`stills <课>`（不要求 approved）、`render <课>`（要求出片条件）、`check <课>`（从 script.md 取句子）。

- [ ] **Step 1: 写失败的测试**

```python
def test_render_gate_refuses_unapproved_and_annotated():
    import tempfile
    import types
    with tempfile.TemporaryDirectory() as d:
        old = v.PROJECTS
        v.PROJECTS = Path(d)
        try:
            (Path(d) / "pend").mkdir()
            a = types.SimpleNamespace(voice=v.VOICE, rate=v.RATE, force=False)
            (Path(d) / "pend" / "script.md").write_text(CLEAN, encoding="utf-8")            # draft
            assert v.cmd_render_v2("pend", L, a) == 1
            approved = smd.mark(CLEAN, "approved", "用户确认", today="2026-10-28")
            (Path(d) / "pend" / "script.md").write_text(approved.replace("{pend}，挂。", "{pend}，挂。\n>> 再改改"), encoding="utf-8")
            assert v.cmd_render_v2("pend", L, a) == 1                                       # 指纹变了 + 有批注
            assert not list(Path(d).rglob("*.mp4"))
        finally:
            v.PROJECTS = old


def test_check_reads_script_lines():
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        old = v.PROJECTS
        v.PROJECTS = Path(d)
        try:
            (Path(d) / "pend").mkdir()
            (Path(d) / "pend" / "script.md").write_text(CLEAN, encoding="utf-8")
            lines, sa = v.check_lines("pend", L)
            assert lines and all("{" not in s for s in lines)
        finally:
            v.PROJECTS = old


def test_v2_commands_dispatch():
    src = Path(v.__file__).read_text(encoding="utf-8")
    assert '"preview"' in src and "cmd_render_v2" in src and "cmd_stills_v2" in src
```


- [ ] **Step 2: 运行，确认失败**

- [ ] **Step 3: 实现**

- `main`：有 `script.md` 时，`preview/stills/render/check` 分派到 v2；去掉第一期加的"有 script.md 就拒绝 render/stills/check"的那段，改成只拒绝 `init`（提示用 script.md 流程）。第一期测试 `test_v1_render_refuses_when_script_exists` 改为：`init` 返回 1；`render` 对 draft 脚本返回 1（走 v2 闸门），且不生成 mp4。
- `cmd_render_v2`：`sc, errs, _ = load_script`；有错误 → 打印并返回 1；`smd.gate(sc)` 非空 → 打印"不能出片：…"并返回 1；`ensure_timeline` → 总时长 > HARD_MAX 且没有 `--force` → 1；写 `build/audio.wav`（`mix_timeline`）→ `write_frame_v2` → 逐帧截图（沿用 v1 的复用逻辑）→ ffmpeg 合成 `projects/<课>/<课>.mp4`（参数同 v1，含 loudnorm）→ `ffprobe -show_entries format=duration` 与 `tl["total"]` 比较，差 > 0.2 s 打印 `[错误]` 并返回 1。
- `cmd_preview`：`ensure_timeline` → 确保 `build/preview.mp3` 存在且与时间轴同指纹（不同就重新混音）→ `write_frame_v2(name="preview.html", extra=PREVIEW_JS)`。`PREVIEW_JS`：把 `body` 用 `transform: scale(innerWidth/1920)` 缩放进窗口，底部叠一条控件（`<audio src="preview.mp3">`、播放/暂停、拖动条、当前时间），`requestAnimationFrame` 里 `setT(audio.currentTime)`。打印 `用浏览器打开：file:///…/preview.html`。
- `check_lines(stem, L) -> (lines, say_as)`：有 `script.md` 时返回 `[ln.plain for ln in sc.spoken()]` 和 `smd.say_as(sc.meta)`；否则沿用 v1 的 `all_lines(N)` 与 `N["say_as"]`。`cmd_check` 只把取句子的两行换成它（判读算法不改）；结尾的改法提示换成"在 script.md 文件头的 say_as 里加替换，例如 say_as: retractable → re-tractable"。

- [ ] **Step 4: 运行测试，全部通过**

- [ ] **Step 5: 通知 word-family-video-ff**：SendMessage 说明 `stills / preview / render / check` 已可用于 script.md、出片条件、自检含义、命令写法；脚本格式没有变化（如有变化逐条列出）。

---

### Task 5: cap 成片 + 自检

- [ ] **Step 1**: `python -I skills/word-family-video/scripts/video.py stills cap` → 退出码 0，Read `_sheet.jpg` 和至少 photo / word / event / pair / map / quiz 各一张，确认：无常驻顶栏、进度条在顶部、冷色、屏幕上没有与解说逐句重复的句子。有问题改 frame.html（不改 cap 的脚本内容——它已 approved），回到 Step 1。
- [ ] **Step 2**: `python -I skills/word-family-video/scripts/video.py render cap` → 退出码 0，打印时长与 timeline 一致。
- [ ] **Step 3**: `ffprobe` 读成片时长、`ffmpeg -i cap.mp4 -af ebur128 -f null -` 读响度（约 -16 LUFS），在 30 s、120 s、240 s 各抽一帧（`ffmpeg -ss … -frames:v 1`）用 Read 看。
- [ ] **Step 4**: `python -I skills/word-family-video/scripts/video.py check cap`（没装 faster-whisper 时记录为跳过）。可能读错的词：在 cap 的 script.md 文件头加 `say_as` 会改指纹——**不改**，记进台账交用户（cap 已 approved）。

---

### Task 6: tract、pend 改写为 script.md（第二支成片：tract）

- [ ] **Step 1**: 并行派两个写稿子代理（`model: "opus"`），提示词同第一期 Task 9 Step 2，课程分别为 tract、pend；补充："tract 用方向型主线，pend 用演变型主线（挂 → 称 → 付钱）；tract 课程有开场照片可用 [photo: opening]；不要动 projects/tract、projects/pend 下的 narration.json"。
- [ ] **Step 2**: 独立复核（同第一期 Task 9 Step 3）：两课 `plan` 零错误零提醒、≤ 290 秒、「这不就是」≤ 1、至少一个 `[photo` 节拍、`spine` 一个方向型一个演变型；抽查各一条来源（curl/WebFetch）与一个词源。
- [ ] **Step 3**: `mark tract approved`、`mark pend approved`（Ruling：用户授权"中间不用等我同意"）→ `stills tract` → `render tract` → 同 Task 5 Step 3 的验证。pend 只出定格图（设计要求两支成片：cap + tract）。

---

### Task 7: 删除 v1

**Files:**
- Delete: `assets/frame_v1.html`、`references/narration_guide.md`、`projects/tract/narration.json`、`projects/pend/narration.json`
- Modify: `scripts/video.py`、`scripts/test_script.py`

- [ ] **Step 1: 写失败的测试**

```python
def test_no_v1_left():
    src = Path(v.__file__).read_text(encoding="utf-8")
    for name in ("auto_narration", "make_units", "fit_budget", "LAYOUTS", "load_narration", "narration.json", "FRAME_V1", "def cmd_init"):
        assert name not in src, name
    assert not (v.HERE / "references" / "narration_guide.md").exists()
    assert not (v.HERE / "assets" / "frame_v1.html").exists()
```

- [ ] **Step 2: 运行，确认失败**
- [ ] **Step 3: 删除**：video.py 中 `clean/part_dicts/auto_word/auto_narration/load_narration/all_lines/make_units/timeline/fit_budget/subtitles/page_html/prepare/cmd_init/write_frame/cmd_stills/cmd_render`（v1 版）、`MIN_WORDS/LAYOUTS/FRAME_V1`；`cmd_stills_v2/cmd_render_v2` 改名为 `cmd_stills/cmd_render`；`check_lines` 只保留 script 分支（没有 script.md 时提示先写脚本）；`main` 的 `choices` 去掉 `init`；没有 script.md 时 `plan/stills/render/preview/check` 一律提示"先按 references/script_guide.md 写脚本"并返回 1；模块 docstring 只保留 v2 命令。删除 `test_v1_render_refuses_when_script_exists`（v1 已不存在），新增 `test_no_v1_left`。`script_guide.md` 里若还引用 `narration_guide.md`，改成指向本文件第十一节。
- [ ] **Step 4: 运行全部测试通过；`plan cap`、`stills cap` 仍退出码 0**

---

### Task 8: 文档、evals、基线、记忆

**Files:**
- Modify: `SKILL.md`（§3 出片：`stills`→看总览→`render`→`check`；出片条件；`preview` 用法；"不要做的事"里删掉 frame.html 那条的 v1 措辞）、`使用说明.md`（v2 流程、命令表、预览、读音检查）、`references/script_guide.md`（七、画面块：补每种块在画面上的样子与 `> 版式：整屏`）、`evals/fix-pronunciation.json`（指向 `projects/pend/script.md`，`say_as` 写在文件头）、新建 `evals/render-unapproved.json`、`evals/baseline.md`（追加 v2 真实执行记录：cap、tract 时长、截图帧数、渲染耗时、响度、自检结果）。
- 记忆：更新 `C:\Users\samsara\.claude\projects\D--Development-Automation-agent-skills\memory\` 里与本项目相关的条目（如有过时的 v1 说法）。

- [ ] **Step 1**: `evals/render-unapproved.json`：

```json
{
  "query": "/word-family-video 把 pend 渲染出来",
  "files": ["projects/pend/script.md"],
  "expected_behavior": [
    "先看 status：脚本是 draft（或确认后又被改过、留有 >> 批注）时，不运行 render，告诉用户原因和下一步（审脚本后说「通过」）",
    "不自行 mark approved，不手改文件头的 status / checked",
    "用户确认后才 render，render 前先跑 stills 看自检"
  ]
}
```

- [ ] **Step 2**: 写文档；`SKILL.md` < 500 行；超过 100 行的 references 带目录。
- [ ] **Step 3**: `python -I skills/word-family-video/scripts/test_script.py` 全过；`grep -rn "narration" skills/word-family-video --include=*.md` 只剩历史记录（baseline.md）。
- [ ] **Step 4**: 通知 word-family-video-ff：v1 已删除、最终命令写法、`SKILL.md` §3 的出片流程。

---

## 最终审查

手工打包（不提交）：`git diff -U10 HEAD -- skills/` + 新文件全文（`frame_data.py`、新 `frame.html`、第一期新建文件不再重复），派独立审查子代理（`model: "opus"`，按 code-reviewer.md），附本计划 Review Focus 原文与两份台账的 Ruling 行。Critical/Important 按 TDD 一次修完，Minor 记台账。
