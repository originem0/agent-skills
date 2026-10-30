"""script.md：视频脚本的解析、校验、检查和审核状态。

格式和写法见 references/script_guide.md。只依赖标准库；课程（word-family 的 lesson JSON）以 dict 传入，方便单测。
"""
import hashlib
import json
import re
import statistics
from dataclasses import dataclass, field
from datetime import date

BLOCKS = ("title", "scene", "photo", "word", "event", "pair", "recap", "map", "quiz", "shot")
CAMERAS = ("自动", "右图", "左图", "大字", "居中")
ACTING = ("正常", "轻", "明显", "静止")
STATUSES = ("draft", "approved")      # 用户确认或明确授权 AI 审核后通过；审稿本身不改变状态
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
        return CUE_RE.sub(lambda m: m[1].partition("|")[2] if "|" in m[1] else m[1], self.text)

    @property
    def cues(self) -> list:
        return [c.strip() for c in CUE_RE.findall(self.text)]

    @property
    def anchors(self) -> list:
        """保留触发点在原句中的位置，同一句两个同名词可以分别驱动画面。"""
        out, removed = [], 0
        for m in CUE_RE.finditer(self.text):
            key, sep, value = m[1].partition("|")
            value = value if sep else key
            out.append({"id": key.strip(), "text": value, "start": m.start() - removed})
            removed += len(m[0]) - len(value)
        return out


@dataclass
class Beat:
    title: str
    block: str
    arg: str
    lineno: int
    data: list = field(default_factory=list)     # [(键, 值, 行号)]
    lines: list = field(default_factory=list)
    scene: dict = field(default_factory=dict)

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
    pause, fence, fence_line = False, None, 0
    for n in range(i, len(rows)):
        s, ln = rows[n].strip(), n + 1
        if fence is not None:
            if s == "```":
                try:
                    def unique(pairs):
                        result = {}
                        for key, value in pairs:
                            if key in result:
                                raise ValueError(f"重复字段 {key}")
                            result[key] = value
                        return result
                    obj = json.loads("\n".join(fence), object_pairs_hook=unique,
                                     parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)))
                    if not isinstance(obj, dict):
                        raise ValueError("scene 必须是 JSON 对象")
                    beats[-1].scene = obj
                except (ValueError, TypeError) as e:
                    errs.append(f"第 {fence_line} 行：分镜 JSON 无效：{e}")
                fence = None
            else:
                fence.append(rows[n])
            continue
        if s.startswith("```"):
            if s != "```scene" or not beats or beats[-1].block != "shot" or beats[-1].scene:
                errs.append(f"第 {ln} 行：每个 [shot] 只允许一个 ```scene 分镜块")
            else:
                fence, fence_line = [], ln
            continue
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
    if fence is not None:
        errs.append(f"第 {fence_line} 行：分镜块缺少结束的 ```")
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


STOCK_LIMITS = {"这不就是": 1, "字面意思": 1, "你有没有想过": 1, "其实就是": 2, "换个方向": 2}   # 只提醒具体套话，不限制反问总量
BANNED = ("下面我们", "接下来我们", "我们再来看", "接下来是", "下面来看")      # 转场套话：用承接内容的句子代替
MAX_LINE = 40
EXAMPLE_MAX = 8               # > 例句 最多几个英文词：屏幕上只放短语，不放整句


def norm_phrase(s: str) -> str:
    """比较短语用：大小写、多余空白不算差别。"""
    return re.sub(r"\s+", " ", s or "").strip().lower()


def example_phrase(b) -> str:
    """节拍里 > 例句 的短语（去掉花括号）；没有就返回空串。"""
    v = b.get("例句")
    return CUE_RE.sub(r"\1", v[0]).strip() if v else ""
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


def explained_pair_words(arg, lines) -> list:
    """有实际陈述的对照可承担讲解；仅在开场问题里点名不算已经讲清。"""
    statements = [ln.plain if isinstance(ln, Line) else ln.get("plain", "") for ln in lines]
    statements = [s for s in statements if not s.rstrip().endswith(("?", "？"))]
    return [w.strip().lower() for w in arg.split("|") if w.strip() and
            any(re.search(rf"(?<![A-Za-z]){re.escape(w.strip())}(?![A-Za-z])", s, re.I) for s in statements)]


def visual_options(sc: Script) -> dict:
    """脚本确定后选择也确定；随机不依赖 Python 进程 hash 或逐帧调用顺序。"""
    seed = int(sc.meta["seed"]) if sc.meta.get("seed") else int(fingerprint(sc.text), 16)
    return {"seed": seed}


def validate(sc: Script, L: dict, stem: str, project_dir=None) -> list:
    """对照课程检查脚本；返回错误列表（带行号和改法）。解析阶段的错误也在里面。"""
    errs = list(sc.errors)
    if sc.meta.get("lesson") != stem:
        errs.append(f"文件头 lesson 应为 {stem}（现在是「{sc.meta.get('lesson', '')}」）")
    if not sc.meta.get("spine"):
        errs.append("文件头缺少 spine：先用一句话写下焦点问题与实际路线，无需套固定分类")
    if sc.meta.get("seed") and not re.fullmatch(r"\d{1,10}", sc.meta["seed"]):
        errs.append("文件头 seed 应为 0–4294967295 的整数，选定后预览和成片保持一致")
    elif sc.meta.get("seed") and int(sc.meta["seed"]) > 4294967295:
        errs.append("文件头 seed 应为 0–4294967295 的整数")
    if sc.status not in STATUSES:
        errs.append(f"文件头 status 只能是 {' / '.join(STATUSES)}")
    for p in _items(sc.meta.get("say_as")):
        if not re.match(r".+?\s*(?:→|->)\s*.+$", p):
            errs.append(f"文件头 say_as 里的「{p}」要写成「原词 → 念法」")
    if not sc.beats:
        errs.append("脚本里还没有 ## 节拍")
    if any(b.block == "shot" for b in sc.beats):
        import storyboard
        return errs + storyboard.validate(sc, L, project_dir)
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
        for key, choices in (("镜头", CAMERAS), ("动作", ACTING)):
            values = b.get(key)
            if values and (len(values) != 1 or values[0] not in choices):
                errs.append(f"{where}：> {key} 只能写一项：{'、'.join(choices)}")
            if values and b.block not in ("scene", "photo", "word"):
                errs.append(f"{where}：> {key} 只用于场景、照片或词的节拍")
        if b.get("镜头") == ["大字"] and b.block != "word":
            errs.append(f"{where}：大字镜头用于 [word]；独立标题用 [title]")
        if b.get("镜头") == ["居中"] and b.block == "word":
            errs.append(f"{where}：词卡用左图、右图或大字；场景单独出现时可居中")
        if b.get("画面"):
            if b.block != "word" or len(b.get("画面")) != 1 or b.get("画面")[0].lower() not in scenes + ["沿用"]:
                errs.append(f"{where}：> 画面 只用于 [word]，选本课线稿名或沿用")
            if b.get("镜头") == ["大字"]:
                errs.append(f"{where}：大字镜头不显示舞台，不需要 > 画面")
        if b.get("动作点"):
            point = b.get("动作点")[0].strip("{} ")
            if len(b.get("动作点")) != 1 or b.block not in ("scene", "word") or not point:
                errs.append(f"{where}：动作点只用于 [scene]/[word]，写一处解说中的触发词")
            elif not any(point.lower() == cue.lower() for ln in b.lines for cue in ln.cues):
                errs.append(f"{where}：动作点 {point} 要在解说里写成 {{{point}}}，才能按声音动作")
        exs = [(v, n) for k, v, n in b.data if k == "例句"]
        if exs:
            if len(exs) > 1:
                errs.append(f"{where}：每个节拍最多一条 > 例句（现在 {len(exs)} 条），留最要紧的那条")
            if b.block not in ("word", "scene", "photo"):
                errs.append(f"第 {exs[0][1]} 行：> 例句 只能用在 [word]、[scene]、[photo] 节拍里")
        cues = [(ln.lineno, c) for ln in b.lines for c in ln.cues]
        if b.block == "scene" and b.arg.lower() not in scenes:
            errs.append(f"{where}：没有「{b.arg}」的线稿，可用：{'、'.join(scenes)}")
        elif b.block == "photo":
            if b.arg == "opening":
                if not L.get("opening", {}).get("photo"):
                    errs.append(f"{where}：这一课的开场没有照片；改用 [scene: opening]，或用 video.py photo 取图")
            elif not b.arg:
                errs.append(f"{where}：要写图片，例如 [photo: opening] 或 [photo: media/xxx.jpg]")
            elif re.match(r"[A-Za-z]:|[/\\]", b.arg) or ".." in re.split(r"[/\\]", b.arg):
                errs.append(f"{where}：图片要放在项目文件夹里，写相对路径，例如 [photo: media/xxx.jpg]（不是 {b.arg}）")
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
                covered.update(w for w in explained_pair_words(b.arg, b.lines) if w in words)
        elif b.block == "recap":
            names = [x.strip().lower() for x in b.arg.split("|")]
            if not 1 <= len(names) <= 4 or not all(names) or len(set(names)) != len(names):
                errs.append(f"{where}：局部小结写 1–4 个不同的已讲词，例如 [recap: import | export]")
            else:
                for name in names:
                    if name not in words or name not in covered:
                        errs.append(f"{where}：{name} 尚未讲清或不属于本课主线；小结只回扣已讲词，不同源对比用 [pair]")
                for n, c in cues:
                    if c.lower() not in names:
                        errs.append(f"第 {n} 行：局部小结的触发词只能是 {'、'.join(names)}")
            if b.get("版式") and b.get("版式") not in (["对照"], ["分支"]):
                errs.append(f"{where}：局部小结版式可写对照或分支")
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
                    tok = re.sub(r"\s+", "", m.group(0))
                    # 整段对上：「15」不能因为课程里有「1570」就算查到
                    if not re.search(rf"(?<!\d){re.escape(tok)}(?!\d)", lesson_text):
                        errs.append(f"第 {ln.lineno} 行：「{m.group(0)}」是年份/日期/数字，但这个节拍没有 > 来源，"
                                    f"课程词源里也查不到：核实后补来源，找不到就删掉这句")
                        break
    skip = skipped(sc.meta)
    missing = [w["w"] for w in L.get("words", []) if w["w"].lower() not in covered | set(skip)]
    if missing:
        errs.append(f"这些主词既没有 [word] 或实际的 [pair] 讲解，也不在 skip 里：{'、'.join(missing)}。讲它，或者在文件头 skip 里写明原因")
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
            acted = {s.strip("{} ").lower() for s in b.get("动作点")}
            for ln in b.lines:
                if any(c.lower() not in acted for c in ln.cues):
                    warns.append(f"第 {ln.lineno} 行：[{b.block}] 节拍里的 {{…}} 不会触发画面，去掉花括号")
        if b.block == "event":
            said = {c.lower() for ln in b.lines for c in ln.cues}
            for h in CUE_RE.findall(" ".join(b.get("原文"))):
                if h.strip().lower() not in said:
                    warns.append(f"第 {b.lineno} 行 [event]：原文高亮「{h}」在解说里没有对应的 {{{h}}}，会在节拍开头直接高亮")
        for k, v, n in b.data:
            if k == "例句" and len(re.findall(r"[A-Za-z]+(?:['’-][A-Za-z]+)*", v)) > EXAMPLE_MAX:
                warns.append(f"第 {n} 行：> 例句 超过 {EXAMPLE_MAX} 个英文词，屏幕上太长：只摘最要紧的短语")
    if sc.annotations:
        warns.append(f"还有 {len(sc.annotations)} 条 >> 批注没处理")
    return warns


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
    if sc.status != "approved":
        why.append("脚本还没确认（status 是 draft）：用户确认或明确授权 AI 审核通过后再 mark approved")
    else:
        m = re.match(r"\s*([0-9a-f]{8})\b", sc.meta.get("checked", ""))
        now = fingerprint(sc.text)
        if not m:
            why.append("文件头没有 checked 指纹：如果是用户在文件里改成了 approved，运行 video.py mark <课> approved 记录一下")
        elif m.group(1) != now:
            why.append(f"确认之后脚本又改过（指纹 {m.group(1)} → {now}）：按用户的审核授权重新确认，再 mark approved")
    if sc.annotations:
        why.append(f"还有 {len(sc.annotations)} 条 >> 批注没处理")
    return why


def review_done(md: str) -> bool:
    """review.md 最新一轮「处理结果」下面有没有写内容。"""
    parts = re.split(r"^## 处理结果[^\n]*$", md, flags=re.M)
    if len(parts) < 2:
        return False
    return bool(re.split(r"^## ", parts[-1], maxsplit=1, flags=re.M)[0].strip())
