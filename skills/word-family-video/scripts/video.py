"""word-family 课程 → 讲解视频（节拍脚本 + 线稿动画 + 免费 TTS + 字幕）。

每支视频先有一份脚本 projects/<课>/script.md（写法见 references/script_guide.md；<课> 可以写词根名或课程 JSON 路径）：
    python scripts/video.py brief   <课>                  # 写稿素材：课程事实、可用画面、触发词、时长预算
    python scripts/video.py plan    <课>                  # 解析 + 检查 + 配音（带逐词时间戳）+ 时间轴 + 试听音频
    python scripts/video.py review  <课> [--record]       # 可选：生成审稿包交给 AI 审；--record 把意见记进 review.md
    python scripts/video.py mark    <课> approved|draft   # 记录用户确认（带内容指纹）
    python scripts/video.py photo   <课> search "查询" | pick "查询" 编号 名字 | shot 网址 名字 | get 图片网址 名字
    python scripts/video.py status                        # 所有课的状态、时长、批注数、能否出片
    python scripts/video.py preview <课>                  # 浏览器实时预览：画面 + 试听音频 + 拖动条，不用渲染
    python scripts/video.py stills  <课>                  # 每个节拍一张定格图 + 总览，并自检出界、重叠、箭头缺失
    python scripts/video.py render  <课>                  # 只渲染用户确认过的脚本 → projects/<课>/<课>.mp4
    python scripts/video.py check   <课>                  # 用 Whisper 回听，找读错的英文词（需要 faster-whisper）

课程数据来自 word-family skill 的 lessons/；图形零件来自 assets/kit.js。分镜编译见 scene_compile.py。
依赖：edge-tts（免费，需联网）、ffmpeg、numpy、Python 版 Playwright（用本机 Chrome/Edge）。可选：Pillow、faster-whisper。
"""
import argparse
import asyncio
import difflib
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import wave
from datetime import date
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent.parent
CACHE = HERE / "cache" / "tts"
PROJECTS = HERE / "projects"
FRAME = HERE / "assets" / "story_frame.html"
PLAYER = HERE / "assets" / "scene_player.js"
ACTORS = HERE / "assets" / "actors.js"
REVIEW_BRIEF = HERE / "references" / "review_brief.md"

VOICE = "zh-CN-YunjianNeural"   # 用户试听六个音色后选定；晓晓会把英文读走样，云扬读英文更差。换音色用 --voice
SR, FPS = 48000, 30
RATE = "+20%"                 # 用户反馈原速偏慢、1.2 倍才合适：配音直接按 1.2 倍语速合成（比整片变速自然）
PRE, LEAD, GAP_LINE, GAP_UNIT, TAIL = 0.35, 0.6, 0.2, 0.45, 1.5   # 秒：单元开头留给画面先出场 / 片头 / 句间 / 单元间 / 片尾（停顿随语速同比缩短）
TITLE_HOLD, PARA_GAP = 1.6, 0.45   # 秒：[title] 节拍不说话时停留多久 / 脚本里空行（段落）的停顿
TARGET, HARD_MAX = 290, 300   # 目标 ≤ 4:50，硬上限 5:00
TIMELINE_VERSION = 2


def find_word_family() -> Path:
    for c in [os.environ.get("WORD_FAMILY_DIR"), HERE.parent / "word-family",
              Path.home() / ".claude" / "skills" / "word-family"]:
        if c and (Path(c) / "assets" / "kit.js").exists():
            return Path(c).resolve()
    sys.exit("找不到 word-family skill：请设置环境变量 WORD_FAMILY_DIR 指向它的目录")


WF = find_word_family()
sys.path.insert(0, str(WF / "scripts"))
import build as wf_build  # noqa: E402  复用课程校验与零件库加载
sys.path.insert(0, str(Path(__file__).resolve().parent))   # python -I 不把脚本所在目录放进 sys.path
import script_md as smd  # noqa: E402  v2 节拍脚本：解析、校验、审核状态
import scene_compile as compiler  # noqa: E402
import provenance  # noqa: E402


# ================================================================ 课程
def load_lesson(arg: str):
    p = Path(arg)
    if not p.suffix:
        p = WF / "lessons" / f"{arg}.json"
    if not p.exists():
        sys.exit(f"找不到课程：{p}（先用 word-family 生成课程）")
    L = json.loads(p.read_text(encoding="utf-8"))
    errs, _ = wf_build.validate(L, *wf_build.kit_names())
    if errs:
        sys.exit("课程数据有误，请先在 word-family 里修好：\n  - " + "\n  - ".join(errs))
    return p.stem, L


# ================================================================ 配音
def tts_text(s: str, say_as: dict) -> str:
    for k, v in say_as.items():          # 只改朗读用的文字，字幕不变（修正读错的英文词）
        # 只看拉丁字母边界：\b 把汉字也算单词字符，「这个live的」里找不到边界
        s = re.sub(rf"(?<![A-Za-z]){re.escape(k)}(?![A-Za-z])", v, s)
    # 「」读出来会有怪停顿；前缀的连字符不读
    return re.sub(r"\b([A-Za-z]+)-(?=\s|，|。|$)", r"\1", s.replace("「", "“").replace("」", "”"))


def tts_path(text, voice, rate):
    return CACHE / (hashlib.sha1(f"{voice}|{rate}|{text}".encode()).hexdigest()[:16] + ".mp3")


def synth_all(lines, say_as, voice, rate, marks=False):
    """按句合成并缓存。顺带记下逐词时间戳（edge-tts WordBoundary，存成同名 .words.jsonl），
    让画面在念到某个词的那一刻动作；marks=True 时，旧缓存缺时间戳的句子会重新合成。"""
    import edge_tts
    CACHE.mkdir(parents=True, exist_ok=True)
    texts = {s: tts_text(s, say_as) for s in lines}

    def missing(t):
        p = tts_path(t, voice, rate)
        if not p.exists() or p.stat().st_size <= 1000:
            return True
        if marks:
            try:
                return not tts_marks(p)
            except (OSError, ValueError, KeyError):
                return True
        return False
    todo = [(t, tts_path(t, voice, rate)) for t in set(texts.values()) if missing(t)]

    async def one(sem, t, p):
        async with sem:
            for attempt in range(4):           # 服务端偶尔返回空音频，重试
                try:
                    # 在线合成可能中途断流；只有完整音频和时间戳才进入缓存。
                    with tempfile.TemporaryDirectory(prefix=p.stem + "-", dir=CACHE) as tmp:
                        clip = Path(tmp) / p.name
                        await edge_tts.Communicate(t, voice, rate=rate, boundary="WordBoundary").save(
                            str(clip), str(clip.with_suffix(".words.jsonl")))
                        if clip.exists() and clip.stat().st_size > 1000 and tts_marks(clip):
                            clip.with_suffix(".words.jsonl").replace(p.with_suffix(".words.jsonl"))
                            clip.replace(p)
                            return
                except Exception:
                    pass
                if attempt < 3:
                    await asyncio.sleep(1.5 * (attempt + 1))
            raise RuntimeError(f"配音失败（检查网络）：{t}")

    async def run():
        sem = asyncio.Semaphore(4)
        await asyncio.gather(*(one(sem, t, p) for t, p in todo))
    if todo:
        print(f"  配音 {len(todo)} 句（其余命中缓存）")
        asyncio.run(run())
    return {s: tts_path(texts[s], voice, rate) for s in lines}


def decode(mp3: Path, sr: int = SR) -> np.ndarray:
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(mp3), "-f", "s16le", "-ac", "1", "-ar", str(sr), "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.int16)


# ================================================================ 字幕
def wlen(s):  # 英文字母按半个字宽计
    return sum(0.55 if ord(ch) < 128 else 1 for ch in s)


def chunks(s: str, limit=20):
    """按标点切成字幕短句；过长的再切。末尾标点不显示。"""
    parts = [p.strip() for p in re.split(r"(?<=[，。？！；：])", s) if p.strip()]
    out, buf = [], ""
    for p in parts:
        if buf and wlen(buf + p) > limit:
            out.append(buf)
            buf = p
        else:
            buf += p
    if buf:
        out.append(buf)
    res = []
    for c in out:
        while wlen(c) > limit + 6:
            cut = len(c) // 2
            sp = c.rfind(" ", 0, cut + 6)
            cut = sp if sp > cut - 8 else cut
            res.append(c[:cut].strip())
            c = c[cut:].strip()
        res.append(c)
    return [re.sub(r"[，。；：、]+$", "", c) for c in res if c]


# ================================================================ 画面
def open_page(html_path):
    from playwright.sync_api import sync_playwright
    pw = sync_playwright().start()
    for opts in ({"channel": "chrome"}, {"channel": "msedge"}, {}):   # 优先用本机浏览器，免得另装
        try:
            browser = pw.chromium.launch(**opts)
            break
        except Exception:
            browser = None
    if not browser:
        pw.stop()
        sys.exit("Playwright 启动不了浏览器：请安装 Chrome/Edge，或运行 playwright install chromium")
    page = browser.new_page(viewport={"width": 1920, "height": 1080})
    page.goto(html_path.resolve().as_uri())
    page.wait_for_function("window.setT !== undefined")
    page.evaluate("setT(0)")                                   # 先进入开场，等图片加载完，避免第一帧空白
    page.wait_for_function("[...document.images].every(i => i.complete)")
    page.evaluate("() => document.fonts.ready")
    return pw, browser, page


# ================================================================ 读音检查
def phon(s: str) -> str:
    """粗略的发音骨架：同音字母归并、去掉元音和重复字母。append 和 Whisper 听成的 "up and" 骨架都是 pnd。"""
    s = s.lower()
    for a, b in (("ph", "f"), ("ck", "k"), ("qu", "kw"), ("x", "ks"), ("c", "k"), ("q", "k"), ("z", "s"), ("v", "f")):
        s = s.replace(a, b)
    s = re.sub(r"[aeiouyhw]", "", s)
    return re.sub(r"(.)\1+", r"\1", s)


def best_ratio(tok, text):
    """在 text 里找和 tok 最像的一段（长度 ±2），返回最高相似度。"""
    best = 0.0
    for n in range(max(1, len(tok) - 2), len(tok) + 3):
        for i in range(0, max(1, len(text) - n + 1)):
            best = max(best, difflib.SequenceMatcher(None, tok, text[i:i + n]).ratio())
    return best


def heard_ok(tok, heard):
    """拼写相似度 ≥ 0.7，或发音骨架相似度 ≥ 0.8，就算听到了。
    只比拼写会把读对的 append（听成 up and）判错；误报太多会把人带去修本来没错的地方。"""
    letters = re.sub(r"[^a-z]", "", heard.lower())
    if best_ratio(tok.lower(), letters) >= 0.7:
        return True
    pt = phon(tok)
    return len(pt) >= 2 and best_ratio(pt, phon(letters)) >= 0.8


def cmd_check(stem, L, a):
    """把每句含英文的配音转写回文字，找可能读错的英文词。
    第一遍不给提示；没对上的词第二遍作为热词再听一次。两遍都没对上 → 可能读错；
    只有第二遍才对上 → 读得可能不够清楚（提示会让识别偏向预期词，所以单独列出，不算通过）。"""
    build = PROJECTS / stem / "build"
    build.mkdir(parents=True, exist_ok=True)
    sc = smd.parse(script_path(stem).read_text(encoding="utf-8"))
    report = {"fingerprint": smd.fingerprint(sc.text), "voice": a.voice, "rate": a.rate,
              "model": a.asr, "status": "skipped", "possible_errors": [], "unclear": []}

    def save_report():
        (build / "check.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    try:
        from faster_whisper import WhisperModel
    except ImportError:
        print("没装 faster-whisper（pip install faster-whisper），跳过读音检查")
        save_report()
        return 0
    lines, say_as = check_lines(stem, L)
    clips = synth_all(lines, say_as, a.voice, a.rate)
    try:
        model = WhisperModel(a.asr, device="cpu", compute_type="int8")
    except Exception as e:
        print(f"加载 {a.asr} 失败（{e}），改用 small，误报会多一些")
        report["model"] = "small"
        model = WhisperModel("small", device="cpu", compute_type="int8")
    stop = {"the", "and", "you", "for", "with", "this", "that", "from", "are", "was"}
    bad, weak = [], []
    for s in lines:
        # 3 个字母以内的（dis、sub、ad 这类前缀）Whisper 在中文语境里本来就听不准，不查
        toks = [t for t in re.findall(r"[A-Za-z]{4,}", s) if t.lower() not in stop]
        if not toks:
            continue
        # Whisper 要求 16 kHz 单声道；用 48 kHz 喂进去会听成慢放录音，满篇幻觉
        audio = decode(clips[s], 16000).astype(np.float32) / 32768
        heard = "".join(x.text for x in model.transcribe(audio, language="zh")[0])
        miss = [t for t in toks if not heard_ok(t, heard)]
        if not miss:
            continue
        heard2 = "".join(x.text for x in model.transcribe(audio, language="zh", hotwords=" ".join(miss))[0])
        for t in miss:
            (weak if heard_ok(t, heard2) else bad).append((t, s, heard.strip()))
    for t, s, h in bad:
        print(f"  - 可能读错 {t}：听到「{h}」")
    if weak:
        print("  读得可能不够清楚（第一遍没听出，提示后才认出）：" + "、".join(sorted({t for t, _, _ in weak})))
    if not bad and not weak:
        print("没有发现读错的英文词")
    elif bad:
        print(f"\n共 {len(bad)} 处可能读错。确认读错的，在 script.md 文件头的 say_as 里加替换，例如 say_as: retractable → re-tractable（只改配音，字幕不变）")
    report.update(status="needs_listening" if bad or weak else "passed",
                  possible_errors=[{"word": t, "sentence": s, "heard": h} for t, s, h in bad],
                  unclear=[{"word": t, "sentence": s, "heard": h} for t, s, h in weak])
    save_report()
    return 0


# ================================================================ 节拍脚本（script.md）
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


def cue_time(plain: str, cue: str, marks: list, dur: float, say_as: dict, start=None):
    """触发词在这句里被念到的时刻（相对句首，秒）和对上的方式：exact / joined / estimate。
    配音文字经过 say_as 替换，所以拿替换后的写法去对逐词时间戳。"""
    def norm(s):
        return re.sub(r"[^\w]", "", s.lower())
    target = norm(tts_text(cue, say_as))
    if start is None:
        for m in marks:
            if norm(m["w"]) == target:
                return m["t"], "exact"
    joined, starts = "", []
    for m in marks:                     # 多词触发（until further notice）：拼起来找第一个词的时刻
        starts.append((len(joined), m["t"]))
        joined += norm(m["w"])
    # 以原句的字符位置区分重复词。不能把第二次 import 也绑到第一次发音。
    occurrence = norm(tts_text(plain[:start], say_as)).count(target) if start is not None and target else 0
    i, search_from = -1, 0
    for _ in range(occurrence + 1):
        i = joined.find(target, search_from) if target else -1
        if i < 0:
            break
        search_from = i + len(target)
    if i >= 0:
        return max(t for pos, t in starts if pos <= i), "joined"
    j = start if start is not None else plain.lower().find(cue.lower())
    return (dur * wlen(plain[:j]) / max(wlen(plain), 1) if j >= 0 else 0.0), "estimate"


def sub_chunks(plain: str, s: float, e: float, marks=None, say_as=None) -> list:
    """一句切成字幕段，按字宽分时间。"""
    cs = chunks(plain)
    if marks and cs:
        times, cursor = [], 0
        for c in cs:
            pos = plain.find(c, cursor)
            if pos < 0:
                break
            at, how = cue_time(plain, c, marks, e - s, say_as or {}, pos)
            if how == "estimate":
                break
            times.append(max(s, min(e, s + at)))
            cursor = pos + len(c)
        if len(times) == len(cs) and all(a < b for a, b in zip(times, times[1:])):
            times[0] = s
            return [(c, round(at, 3), round(end, 3)) for c, at, end in zip(cs, times, times[1:] + [e])]
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
        ex = smd.example_phrase(b)          # > 例句：念到这个短语的那一刻上屏
        ex_at = None
        for j, ln in enumerate(b.lines):
            if j:
                lt += PARA_GAP if ln.pause_before else GAP_LINE
            mp3 = clip_of(ln.plain)
            d = dur_of(mp3)
            cues = {}
            for anchor in ln.anchors:
                c = anchor["id"]
                off, how = cue_time(ln.plain, anchor["text"], marks_of(mp3), d, say_as,
                                     anchor["start"] if b.block == "shot" else None)
                cues[c] = round(lt + off, 3)
                if how == "estimate":
                    warns.append(f"第 {ln.lineno} 行：{c} 没在配音的逐词时间里找到，只能按字数估算，画面可能对不准")
            if ex and ex_at is None and smd.norm_phrase(ex) in smd.norm_phrase(ln.plain):
                off, how = cue_time(ln.plain, ex, marks_of(mp3), d, say_as)
                ex_at = round(lt + off, 3)
            rows.append({"lineno": ln.lineno, "text": ln.text, "plain": ln.plain,
                         "s": round(lt, 3), "e": round(lt + d, 3), "cues": cues})
            subs += [{"s": s, "e": e, "t": c} for c, s, e in sub_chunks(
                ln.plain, lt, lt + d, marks_of(mp3) if b.block == "shot" else None, say_as)]
            lt += d
        if not b.lines:
            lt += TITLE_HOLD
        t = lt + GAP_UNIT + (TAIL if k == last else 0)
        beats.append({"lineno": b.lineno, "title": b.title, "block": b.block, "arg": b.arg,
                      "data": [[key, val] for key, val, _ in b.data],
                      "t0": round(t0, 3), "t1": round(t, 3), "lines": rows})
        if b.block == "shot":
            beats[-1]["scene"] = b.scene
        if ex_at is not None:
            beats[-1]["example_at"] = ex_at
    taught = []
    for b in sc.beats:
        taught += [b.arg.lower()] if b.block == "word" else smd.explained_pair_words(b.arg, b.lines) if b.block == "pair" else []
        if b.block == "shot":
            taught += [w.lower() for r in b.scene.get("learn", []) for w in r.get("words", [])]
    words = list(dict.fromkeys(taught))
    return {"total": round(t, 3), "words": words, "beats": beats, "subs": subs,
            "visual": smd.visual_options(sc)}, warns


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


def load_script(stem, L, lesson_stem=None):
    """读 projects/<课>/script.md，返回 (脚本, 错误, 提醒)。"""
    sc = smd.parse(script_path(stem).read_text(encoding="utf-8"))
    errors = smd.validate(sc, L, lesson_stem or stem, PROJECTS / stem)
    if not errors:
        for beat in sc.beats:
            for node in beat.scene.get("nodes", []):
                if node.get("type") == "illustration" and node.get("items"):
                    wf_build.check_scene(node["items"], f"第 {beat.lineno} 行 {node['id']}", *wf_build.kit_names(), errors)
    return sc, errors, smd.lint(sc)


def input_snapshot(stem, L, sc, a):
    files = {"scripts/" + name: HERE / "scripts" / name for name in
             ("video.py", "script_md.py", "storyboard.py", "scene_compile.py", "legacy_import.py", "provenance.py")}
    files.update({"assets/" + path.name: path for path in (FRAME, PLAYER, ACTORS)})
    files["word-family/kit.js"] = WF / "assets" / "kit.js"
    snapshot = provenance.snapshot(sc, L, PROJECTS / stem, WF, files,
                                   getattr(a, "voice", VOICE), getattr(a, "rate", RATE))
    if getattr(a, "lesson", None):
        source = Path(a.lesson)
        if not source.suffix:
            source = WF / "lessons" / f"{a.lesson}.json"
        snapshot["lesson_file"] = provenance.file_hash(source)
        snapshot["fingerprint"] = provenance.digest({k: v for k, v in snapshot.items() if k != "fingerprint"})
    return snapshot


def approval_gate(stem, L, sc, a):
    why = smd.gate(sc)
    path = PROJECTS / stem / "build" / "approval.json"
    if sc.status == "approved":
        try:
            approved = json.loads(path.read_text(encoding="utf-8"))
            current = input_snapshot(stem, L, sc, a)
            differences = provenance.changed(approved, current)
            if approved.get("fingerprint") != current["fingerprint"]:
                why.append("审核后输入已变化：" + "、".join(differences or ["审核记录"]) + "；按既有授权重新审核并 mark approved")
        except FileNotFoundError:
            why.append("缺少完整输入审核记录，或素材已丢失；复核后 mark approved")
        except (OSError, ValueError, TypeError):
            why.append("审核记录或素材无效；复核后 mark approved")
    return why


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
    teaching = L.get("teaching", {})
    out.append(f"共同讲解原则：{WF / 'references' / 'teaching_principles.md'}；视频从素材重新定路线，不照搬卡片顺序")
    if teaching.get("known"):
        out.append("已有经验：" + "；".join(teaching["known"]))
    if teaching.get("discovery"):
        out.append("值得揭开的联系：" + teaching["discovery"])
    for c in teaching.get("contrasts", []):
        out += [f"可选对比：{c['a']} / {c['b']} —— {c['distinction']}", f"对比依据：{c['fact']}；{c['source']}"]
    previous = sorted((p for p in PROJECTS.glob("*/script.md") if p.parent.name != stem),
                      key=lambda p: p.stat().st_mtime, reverse=True)[:3]
    if previous:
        out.append("近期作品（供比较实际入口与路线，不是轮换配额）：")
        for p in previous:
            old = smd.parse(p.read_text(encoding="utf-8"))
            first = old.beats[0] if old.beats else None
            out.append(f"  {p.parent.name}：{old.meta.get('spine', '')}；入口 {first.block if first else '?'}，{first.title if first else ''}")
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
        out += ["", "差异与家族补充（逐项辨析）：" + "；".join(tags(t) for t in L["traps"])]
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


def ensure_timeline(stem, L, a, quiet=False):
    """脚本 → 配音（命中缓存就不联网）→ 时间轴。timeline.json 缺失、脚本改过或换了音色语速时重算。
    脚本有错误时打印并返回 None；否则返回 (脚本, 时间轴, 配音文字→mp3)。"""
    sc, errs, _ = load_script(stem, L, getattr(a, "lesson_stem", None))
    if errs:
        print(f"\n脚本有 {len(errs)} 处错误，改完再运行 plan：")
        for e in errs:
            print("  - [错误]", e)
        return None
    sa = smd.say_as(sc.meta)
    clips = synth_all([ln.plain for ln in sc.spoken()], sa, a.voice, a.rate, marks=True)
    build = PROJECTS / stem / "build"
    tp = build / "timeline.json"
    fp = smd.fingerprint(sc.text)
    if tp.exists():
        try:
            tl = json.loads(tp.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            tl = {}
        if isinstance(tl, dict) and (tl.get("version"), tl.get("fingerprint"), tl.get("voice"), tl.get("rate")) == (TIMELINE_VERSION, fp, a.voice, a.rate):
            tl.setdefault("cue_warns", [])
            tl.setdefault("visual", smd.visual_options(sc))
            return sc, tl, clips
    durs = {}

    def dur_of(mp3):
        if mp3 not in durs:
            durs[mp3] = len(decode(mp3)) / SR
        return durs[mp3]
    tl, cue_warns = build_timeline(sc, sa, clips.__getitem__, dur_of, tts_marks)
    tl.update(version=TIMELINE_VERSION, lesson=stem, fingerprint=fp, voice=a.voice, rate=a.rate, cue_warns=cue_warns)
    build.mkdir(parents=True, exist_ok=True)
    tp.write_text(json.dumps(tl, ensure_ascii=False, indent=1), encoding="utf-8")
    if not quiet:
        print(f"  时间轴已更新：{tp}")
    return sc, tl, clips


def cmd_plan_script(stem, L, a):
    """新 plan：解析 + 检查 → 配音（带逐词时间戳）→ 时间轴 → 试听音频。有错误就不往下走。"""
    got = ensure_timeline(stem, L, a, quiet=True)
    if not got:
        return 1
    sc, tl, clips = got
    warns = smd.lint(sc)
    build = PROJECTS / stem / "build"
    try:
        write_frame(stem, L, tl)
    except (ValueError, KeyError, OSError) as e:
        print(f"  - [错误] 分镜不能编译：{e}")
        return 1
    write_audio(build / "preview.mp3", mix_timeline(tl, clips.__getitem__))
    (build / "preview.fp").write_text(audio_fingerprint(tl), encoding="utf-8")
    total = tl["total"]
    print(f"\n时长 {total // 60:.0f} 分 {total % 60:.0f} 秒（目标 ≤ {TARGET} 秒），{len(tl['beats'])} 个节拍，"
          f"涉及 {len(tl['words'])} 个词")
    for b in tl["beats"]:
        print(f"  [{b['t0']:6.1f}s] {b['block']:<6} {b['title'][:18]:<18} {b['t1'] - b['t0']:5.1f}s  {len(b['lines'])} 句")
    if total > TARGET:
        warns.append(f"超过目标时长 {TARGET} 秒：删掉一些节拍，删掉的主词写进文件头 skip")
    for w in warns + tl["cue_warns"]:
        print("  - [提醒]", w)
    print(f"\n试听：{build / 'preview.mp3'}")
    gate = approval_gate(stem, L, sc, a)
    print(f"状态：{sc.status}" + ("，可以出片" if not gate else "；" + "；".join(gate)))
    if total > HARD_MAX:
        print(f"  - [错误] 超过 5 分钟（{total:.0f} 秒）：不靠加快语速，删节拍")
        return 1
    return 0


def frame_html(stem, L, tl, extra: str = "", film=None) -> str:
    """预览、定格和编码共用自足的编译结果；不把课程交给浏览器。"""
    D = film if film is not None else compiler.compile_film(stem, L, tl, PROJECTS / stem, WF)
    kit = compiler.map_colors((WF / "assets" / "kit.js").read_text(encoding="utf-8"))
    html = (FRAME.read_text(encoding="utf-8").replace("/*__KIT_JS__*/", kit)
            .replace("/*__ACTORS_JS__*/", ACTORS.read_text(encoding="utf-8"))
            .replace("/*__PLAYER_JS__*/", PLAYER.read_text(encoding="utf-8")).replace("/*__EXTRA__*/", extra))
    return html.replace("/*__DATA_JSON__*/null", json.dumps(D, ensure_ascii=False).replace("</", "<\\/"))


def write_frame(stem, L, tl, name="frame.html", extra="") -> Path:
    build = PROJECTS / stem / "build"
    build.mkdir(parents=True, exist_ok=True)
    hp = build / name
    film = compiler.compile_film(stem, L, tl, PROJECTS / stem, WF)
    hp.write_text(frame_html(stem, L, tl, extra, film), encoding="utf-8")
    (build / "film.json").write_text(json.dumps(film, ensure_ascii=False, indent=1), encoding="utf-8")
    return hp


def contact_sheet(shots, path):
    """定格图拼成一张总览；没装 Pillow 就跳过。"""
    try:
        from PIL import Image
    except ImportError:
        return False
    W, H, cols = 640, 360, 3
    sheet = Image.new("RGB", (W * cols, H * ((len(shots) + cols - 1) // cols)), "white")
    for i, s in enumerate(shots):
        sheet.paste(Image.open(s).resize((W, H)), ((i % cols) * W, (i // cols) * H))
    sheet.save(path, quality=85)
    return True


def cmd_stills(stem, L, a):
    """每个节拍末尾一张定格图 + 总览，并逐张自检（出界、重叠、箭头缺失、裂图、文字溢出线稿框）。"""
    got = ensure_timeline(stem, L, a)
    if not got:
        return 1
    sc, tl, _ = got
    hp = write_frame(stem, L, tl)
    out = PROJECTS / stem / "stills"
    out.mkdir(parents=True, exist_ok=True)
    for f in out.glob("*.png"):
        f.unlink()
    pw, browser, page = open_page(hp)
    shots, problems = [], []
    try:
        for k, b in enumerate(tl["beats"]):
            page.evaluate("t => setT(t)", b["t1"] - 0.5)       # 节拍末尾、下一拍转场之前：所有元素都已出场
            p = out / f"{k:02d}_{b['block']}.png"
            page.screenshot(path=str(p))
            shots.append(p)
            problems += [f"{p.name}（第 {b['lineno']} 行「{b['title']}」）：{x}" for x in page.evaluate("() => audit()")]
    finally:
        browser.close()
        pw.stop()
    sheet = contact_sheet(shots, out / "_sheet.jpg")
    print(f"\n定格图：{out}" + ("（总览 _sheet.jpg）" if sheet else ""))
    if problems:
        print(f"自检发现 {len(problems)} 处问题（改脚本里对应的节拍，或把问题告诉维护 frame.html 的人）：")
        for x in problems:
            print("  - [问题]", x)
        return 1
    print("自检无问题：没有出界、重叠、箭头缺失、裂图")
    return 0


def check_lines(stem, L):
    """读音检查要听的句子和 say_as（来自 script.md）。"""
    sc = smd.parse(script_path(stem).read_text(encoding="utf-8"))
    return [ln.plain for ln in sc.spoken()], smd.say_as(sc.meta)


def audit_timeline(hp, tl):
    """按实际编译轨道检查变化前、中、后，与预览及成片使用同一画面。"""
    pw, browser, page = open_page(hp)
    problems = []
    try:
        film = page.evaluate("filmData")
        for at in compiler.sample_times(film):
            b = next(s for s in film["shots"] if s["t1"] > at)
            page.evaluate("t => setT(t)", at)
            problems.extend(f"第 {b['lineno']} 行「{b['title']}」（{at:.1f}s）：{x}"
                            for x in page.evaluate("() => audit()"))
    finally:
        browser.close()
        pw.stop()
    return list(dict.fromkeys(problems))


def render_frames(hp, total, out_mp4, wav):
    """逐帧截图 → ffmpeg 合成；画面没变化（没有动画、字幕没换）就复用上一帧。返回 (实际截图帧数, ffmpeg 返回码)。"""
    pw, browser, page = open_page(hp)
    n, last, shots = int(round(total * FPS)), None, 0
    print(f"\n逐帧渲染 {n} 帧…")
    try:
        ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "image2pipe", "-c:v", "mjpeg", "-framerate", str(FPS), "-i", "-",
                               "-i", str(wav), "-af", "loudnorm=I=-16:TP=-1.5:LRA=11",
                               "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
                               "-c:a", "aac", "-b:a", "160k", "-shortest", str(out_mp4)], stdin=subprocess.PIPE)
        try:
            for f in range(n):
                need = page.evaluate("t => setT(t)", f / FPS)
                if need or last is None:
                    last = page.screenshot(type="jpeg", quality=92)
                    shots += 1
                ff.stdin.write(last)
                if f % (FPS * 30) == 0:
                    print(f"  {f / FPS:5.0f}s / {total:.0f}s")
        finally:
            try:
                ff.stdin.close()
            finally:
                ff.wait()
    finally:
        browser.close()
        pw.stop()
    return shots, ff.returncode


def media_duration(path) -> float:
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", str(path)],
                       capture_output=True, text=True)
    try:
        return float(r.stdout.strip())
    except ValueError:
        return -1.0


def cmd_render(stem, L, a):
    """出片：只认用户确认过、之后没改过、没有批注、plan 无错误的脚本。"""
    sc, errs, _ = load_script(stem, L, getattr(a, "lesson_stem", None))
    if errs:
        print(f"脚本有 {len(errs)} 处错误，先运行 plan 改干净：")
        for e in errs:
            print("  - [错误]", e)
        return 1
    why = approval_gate(stem, L, sc, a)
    rv = PROJECTS / stem / "review.md"
    if rv.exists() and not smd.review_done(rv.read_text(encoding="utf-8")):
        why.append("最新一轮审稿意见还没处理，先补齐 review.md 的处理结果")
    if why:
        print("不能出片：" + "；".join(why))
        return 1
    got = ensure_timeline(stem, L, a)
    if not got:
        return 1
    sc, tl, clips = got
    total = tl["total"]
    if total > HARD_MAX and not getattr(a, "force", False):
        print(f"超过 5 分钟（{total:.0f} 秒），不渲染：删节拍（加 --force 强制）")
        return 1
    build = PROJECTS / stem / "build"
    write_audio(build / "audio.wav", mix_timeline(tl, clips.__getitem__))
    hp = write_frame(stem, L, tl)
    problems = audit_timeline(hp, tl)
    if problems:
        print("画面自检未通过，不渲染：")
        for problem in problems:
            print("  - [问题]", problem)
        return 1
    out = PROJECTS / stem / f"{stem}.mp4"
    pending = out.with_name(f"{stem}.rendering.mp4")
    try:
        approved_inputs = input_snapshot(stem, L, sc, a)
        if approval_gate(stem, L, sc, a):
            print("准备画面期间审核输入发生变化，复核后重新渲染")
            return 1
        shots, rc = render_frames(hp, total, pending, build / "audio.wav")
        if rc:
            print("ffmpeg 合成失败")
            return 1
        got_d = media_duration(pending)
        if abs(got_d - total) > 0.2:
            print(f"  - [错误] 成片时长和时间轴差 {got_d - total:+.2f} 秒")
            return 1
        latest, script_errors, _ = load_script(stem, L, getattr(a, "lesson_stem", None))
        if (script_errors or approval_gate(stem, L, latest, a) or
                input_snapshot(stem, L, latest, a)["fingerprint"] != approved_inputs["fingerprint"]):
            print("编码期间输入发生变化，保留旧成片；复核后重新渲染")
            return 1
        # 编码失败或时长不符时，保留上一版可播放的成片。
        pending.replace(out)
        manifest = {"fingerprint": tl["fingerprint"], "voice": tl["voice"], "rate": tl["rate"],
                    "duration": got_d, "timeline_duration": total, "captured_frames": shots,
                    "date": date.today().isoformat(), "file": out.name, "audit": "passed",
                    "inputs": approved_inputs["fingerprint"], "sha256": provenance.file_hash(out),
                    "film": json.loads((build / "film.json").read_text(encoding="utf-8"))["fingerprint"]}
        (build / "render.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as e:
        print(f"渲染失败：{e}")
        return 1
    finally:
        pending.unlink(missing_ok=True)
    print(f"完成：{out}（{got_d:.1f} 秒，时间轴 {total:.1f} 秒；实际截图 {shots} 帧，其余复用）")
    return 0


PREVIEW_JS = r"""
// 预览：页面缩放进窗口，底部叠一条播放控件，按音频时间逐帧调用 setT
(function () {
  const fit = () => { const k = Math.min(innerWidth / 1920, (innerHeight - 56) / 1080);
    document.body.style.transformOrigin = "0 0"; document.body.style.transform = `scale(${k})`; };
  addEventListener("resize", fit); fit();
  document.documentElement.style.overflow = "hidden"; document.documentElement.style.background = "#1b1f24";
  const bar = document.createElement("div");
  bar.style.cssText = "position:fixed;left:0;right:0;bottom:0;height:56px;display:flex;align-items:center;gap:14px;padding:0 18px;background:#22282f;color:#dfe5ea;font:14px sans-serif;z-index:9";
  bar.innerHTML = `<button id="pp" style="width:72px;height:32px">播放</button><input id="sk" type="range" min="0" max="${DATA.total}" step="0.01" value="0" style="flex:1"><span id="tm">0:00</span><audio id="au" src="preview.mp3" preload="auto"></audio>`;
  document.documentElement.appendChild(bar);
  const au = bar.querySelector("#au"), sk = bar.querySelector("#sk"), tm = bar.querySelector("#tm"), pp = bar.querySelector("#pp");
  const mmss = t => `${Math.floor(t / 60)}:${String(Math.floor(t % 60)).padStart(2, "0")}`;
  pp.onclick = () => au.paused ? au.play() : au.pause();
  au.onplay = () => pp.textContent = "暂停"; au.onpause = () => pp.textContent = "播放";
  sk.oninput = () => { au.currentTime = +sk.value; setT(+sk.value); };
  const loop = () => { const t = au.currentTime; setT(t); if (!au.paused) sk.value = t; tm.textContent = `${mmss(t)} / ${mmss(DATA.total)}`; requestAnimationFrame(loop); };
  setT(0); loop();
})();
"""


def audio_fingerprint(tl):
    # 同一份脚本换音色或语速后，也必须重混试听音频。
    return hashlib.sha1(json.dumps([tl["fingerprint"], tl["voice"], tl["rate"]]).encode()).hexdigest()[:16]


def cmd_preview(stem, L, a):
    """浏览器实时预览（画面 + 试听音频 + 拖动条），不用渲染，也不用起本地服务。"""
    got = ensure_timeline(stem, L, a)
    if not got:
        return 1
    sc, tl, clips = got
    build = PROJECTS / stem / "build"
    fp_file = build / "preview.fp"
    fp = audio_fingerprint(tl)
    if not (build / "preview.mp3").exists() or not fp_file.exists() or fp_file.read_text(encoding="utf-8") != fp:
        write_audio(build / "preview.mp3", mix_timeline(tl, clips.__getitem__))
        fp_file.write_text(fp, encoding="utf-8")
    hp = write_frame(stem, L, tl, name="preview.html", extra=PREVIEW_JS)
    print(f"用浏览器打开：{hp.resolve().as_uri()}")
    return 0


def append_review(path: Path, stem: str, engine: str, fp: str, raw_text: str) -> int:
    """review.md 按轮次追加：每轮一节「审稿意见」+ 一节空的「处理结果」，由写稿方逐条填写。"""
    old = path.read_text(encoding="utf-8") if path.exists() else f"# 审稿记录：{stem}\n"
    n = len(re.findall(r"^## 审稿意见", old, re.M)) + 1
    # 贴进来的意见自带一、二级标题会冒充轮次或「处理结果」：降成三级
    raw_text = re.sub(r"^#{1,2}(?=\s)", "###", raw_text, flags=re.M)
    path.write_text(old.rstrip() + f"\n\n## 审稿意见 第 {n} 轮（{engine} · {date.today().isoformat()} · 脚本指纹 {fp}）\n\n"
                    f"{raw_text.strip()}\n\n## 处理结果 第 {n} 轮\n\n", encoding="utf-8")
    return n


def review_record_args(stem, a):
    """后续命令仍从原课程读取素材，不能把独立版本名当成课程 JSON 名。"""
    lesson = getattr(a, "lesson_stem", stem)
    args = ["review", getattr(a, "lesson", None) or lesson]
    if stem != lesson:
        args += ["--project", stem]
    return args + ["--record"]


def cmd_review(stem, L, a):
    """按任务授权生成审稿包，由审稿方或当前 agent 审核；意见原样保存后用 --record 记录。"""
    sc, errs, _ = load_script(stem, L, getattr(a, "lesson_stem", None))
    if errs:
        print("脚本还有错误：先跑 plan 改干净再审稿")
        return 1
    build = PROJECTS / stem / "build"
    build.mkdir(parents=True, exist_ok=True)
    brief, raw = build / "review_brief.md", build / "review_raw.md"
    record_cmd = subprocess.list2cmdline(["video.py", *review_record_args(stem, a)])
    if a.record:
        if not raw.exists() or not raw.read_text(encoding="utf-8").strip():
            print(f"还没有审稿意见：把审稿方的意见原样写进 {raw}，再运行 {record_cmd}")
            return 1
        # 这一轮标被审的那一版：打包时的指纹写在审稿包第一行
        m = re.search(r"脚本指纹 (\w+)", brief.read_text(encoding="utf-8").split("\n", 1)[0]) if brief.exists() else None
        fp, now = (m.group(1) if m else smd.fingerprint(sc.text)), smd.fingerprint(sc.text)
        if fp != now:
            print(f"注意：脚本在打包审稿后改过（审的是 {fp}，现在是 {now}），处理意见时对照着看")
        n = append_review(PROJECTS / stem / "review.md", stem, "AI 审稿", fp, raw.read_text(encoding="utf-8"))
        raw.unlink()                    # 记完就清掉，下一轮不会把旧意见再记一遍
        print(f"已记进 {PROJECTS / stem / 'review.md'} 第 {n} 轮。在「处理结果 第 {n} 轮」下逐条写 "
              f"采纳/部分采纳/不采纳 + 理由，改完脚本跑 plan")
        return 0
    if raw.exists() and raw.read_text(encoding="utf-8").strip():
        print(f"{raw} 里已经有审稿意见：先运行 {record_cmd} 记下来；不要这些意见就手动删掉这个文件再打包")
        return 1
    numbered = "\n".join(f"{i + 1:>3}  {r}" for i, r in enumerate(sc.text.split("\n")))
    brief.write_text(f"<!-- 脚本指纹 {smd.fingerprint(sc.text)} -->\n" + REVIEW_BRIEF.read_text(encoding="utf-8")
                     + "\n\n# 课程素材\n\n" + brief_text(stem, L)
                     + "\n\n# 待审脚本（行号 + 原文）\n\n```\n" + numbered + "\n```\n", encoding="utf-8")
    print(f"审稿包：{brief}\n把这个文件交给审稿方，将意见写进 {raw}，然后运行 {record_cmd}。"
          "用户明确授权自行审核时，由当前 agent 审核并记录处理结果。")
    return 0


def cmd_mark(stem, L, a):
    target = a.args[0] if a.args else ""
    if target not in smd.STATUSES:
        print("用法：video.py mark <课> approved|draft（approved 需要用户确认，或用户明确授权 AI 审核后直接出片）")
        return 1
    sc, errs, _ = load_script(stem, L, getattr(a, "lesson_stem", None))
    if target == "approved":
        if errs:
            print("脚本还有错误：先跑 plan 改干净")
            return 1
        if sc.annotations:
            print(f"还有 {len(sc.annotations)} 条 >> 批注没处理：处理完再标记")
            return 1
        rv = PROJECTS / stem / "review.md"
        if rv.exists() and not smd.review_done(rv.read_text(encoding="utf-8")):
            print(f"{rv} 最新一轮审稿意见还没处理：先在「处理结果」下逐条写明怎么处理")
            return 1
    record = input_snapshot(stem, L, sc, a) if target == "approved" else None
    script_path(stem).write_text(smd.mark(sc.text, target, getattr(a, "by", "用户确认")), encoding="utf-8")
    approval = PROJECTS / stem / "build" / "approval.json"
    if record is not None:
        approval.parent.mkdir(parents=True, exist_ok=True)
        record.update(by=getattr(a, "by", "用户确认"), date=date.today().isoformat())
        approval.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    else:
        approval.unlink(missing_ok=True)
    print(f"{stem}：status → {target}" + (f"（指纹 {smd.fingerprint(sc.text)}）" if target != "draft" else ""))
    return 0


def cmd_status():
    """所有课的脚本状态一览：批量审核时看进度。"""
    if not PROJECTS.is_dir():
        print(f"还没有任何脚本（{PROJECTS} 不存在）：先按 references/script_guide.md 写一课")
        return 0
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
        try:
            lesson_name = sc.meta.get("lesson", d.name)
            _, lesson = load_lesson(lesson_name)
            options = argparse.Namespace(lesson=lesson_name, voice=tl.get("voice", VOICE) if tl_p.exists() else VOICE,
                                         rate=tl.get("rate", RATE) if tl_p.exists() else RATE)
            gate = approval_gate(d.name, lesson, sc, options)
        except (OSError, ValueError, SystemExit):
            gate = ["课程或审核输入不可用"]
        print(f"{d.name:<10}{sc.status:<10}{dur:<20}{len(sc.annotations):<6}{'可以' if not gate else gate[0]}")
    return 0


def get_image(url: str, dst: Path) -> dict:
    """下载一张网络图片存成 dst（.jpg，长边不超过 1600）。不是图片就报错，不留文件。
    用户确认视频不公开、图片可以从任意网站取；署名写来源网站和日期。"""
    import urllib.parse
    import urllib.request
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (word-family-video)"})
    with urllib.request.urlopen(req, timeout=30) as r:
        data = r.read(30 * 1024 * 1024 + 1)
    if len(data) > 30 * 1024 * 1024:
        raise ValueError("图片超过 30 MB")
    import io
    try:
        from PIL import Image
        im = Image.open(io.BytesIO(data))
        im.load()
    except ImportError:
        raise ValueError("没装 Pillow（pip install pillow），没法检查和缩放图片")
    except Exception:
        raise ValueError("下载到的不是图片（可能是网页或防盗链提示）：换成图片本身的地址")
    # 透明背景（RGBA / LA / 调色板透明）先铺到白底上，和照片卡片的白边一致；直接转 RGB 会露出透明处底下的杂色
    if "A" in im.getbands() or (im.mode == "P" and "transparency" in im.info):
        im = im.convert("RGBA")
        bg = Image.new("RGB", im.size, (255, 255, 255))
        bg.paste(im, mask=im.getchannel("A"))
        im = bg
    else:
        im = im.convert("RGB")
    im.thumbnail((1600, 1600))
    dst.parent.mkdir(parents=True, exist_ok=True)
    im.save(dst, "JPEG", quality=88)
    host = urllib.parse.urlparse(url).netloc or "本地文件"
    return {"file": dst, "credit": f"来源：{host}，{date.today().isoformat()}", "source": url}


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
    elif act == "get" and len(rest) == 2:
        try:
            got = get_image(rest[0], media / f"{rest[1]}.jpg")
        except Exception as e:  # noqa: BLE001  网络、格式问题都按一条中文提示报给用户
            print(f"取图失败：{e}")
            return 1
    else:
        print('用法：video.py photo <课> search "英文查询" | pick "英文查询" 编号 名字 | shot 网址 名字 [--clip x,y,宽,高]'
              ' | get 图片网址 名字')
        return 1
    rel = got["file"].relative_to(PROJECTS / stem).as_posix()
    print(f"已保存：{got['file']}\n粘进脚本：\n## 标题 [photo: {rel}]\n> 署名：{got['credit']}（{got['source']}）")
    if act == "shot":
        print("先打开图片，确认截到的是标题区域；不对就加 --clip x,y,宽,高 重截")
    return 0


def main():
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description="word-family 课程 → 讲解视频")
    ap.add_argument("cmd", choices=["brief", "plan", "review", "mark", "photo", "status",
                                    "preview", "stills", "render", "check"])
    ap.add_argument("lesson", nargs="?", help="词根名（如 tract）或课程 JSON 路径；status 不用写")
    ap.add_argument("args", nargs="*", help="mark：approved / draft；photo：search 查询 | pick 查询 编号 名字 | shot 网址 名字 | get 图片网址 名字")
    ap.add_argument("--voice", default=VOICE)
    ap.add_argument("--rate", default=RATE, help="语速，默认 +20%%（约 1.2 倍）；原速写 +0%%")
    ap.add_argument("--force", action="store_true", help="超过 5 分钟也渲染")
    ap.add_argument("--asr", default="large-v3-turbo", help="读音检查用的 Whisper 模型（首次使用自动下载约 1.6GB）")
    ap.add_argument("--record", action="store_true", help="review：把 build/review_raw.md 里的审稿意见记进 review.md")
    ap.add_argument("--by", default="用户确认", help="mark：记录确认依据；用户授权自行审核时写「用户授权 AI 审核」")
    ap.add_argument("--project", help="独立视频版本名，仍读取同一课程；例如 port-cables")
    ap.add_argument("--clip", default="0,0,1280,720", help="photo shot 的截图区域：x,y,宽,高")
    a = ap.parse_args()
    if a.cmd == "status":
        return cmd_status()
    if not a.lesson:
        ap.error("要写课程名，例如：video.py plan tract")
    stem, L = load_lesson(a.lesson)
    a.lesson_stem = stem
    if a.project:
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}", a.project):
            ap.error("--project 写 1–64 个字母、数字、下划线或连字符，不能是路径")
        stem = a.project
    if a.cmd == "brief":
        return cmd_brief(stem, L)
    if a.cmd == "photo":
        return cmd_photo(stem, L, a)
    if not script_path(stem).exists():
        print(f"没有 {script_path(stem)}：先按 references/script_guide.md 写脚本")
        return 1
    return {"plan": cmd_plan_script, "review": cmd_review, "mark": cmd_mark, "preview": cmd_preview,
            "stills": cmd_stills, "render": cmd_render, "check": cmd_check}[a.cmd](stem, L, a)


if __name__ == "__main__":
    sys.exit(main())
