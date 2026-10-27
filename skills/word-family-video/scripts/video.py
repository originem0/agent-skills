"""word-family 课程 → 讲解视频（逐帧动画的线稿板书 + 免费 TTS + 字幕），时长自动控制在 5 分钟内。

用法（<课> 可以写词根名，如 tract，也可以写课程 JSON 路径）：
    python scripts/video.py init   <课>    # 生成解说词草稿 projects/<课>/narration.json（已存在则不覆盖）
    python scripts/video.py plan   <课>    # 配音（缓存）、量真实时长、超时自动删减，打印每个单元和提醒
    python scripts/video.py stills <课>    # 每个单元出一张定格图 projects/<课>/stills/，先看画面
    python scripts/video.py render <课>    # 逐帧渲染并合成 projects/<课>/<课>.mp4
    python scripts/video.py check  <课>    # 用 Whisper 回听，找读错的英文词（需要 faster-whisper）

课程数据来自 word-family skill 的 lessons/；线稿零件库直接读它的 assets/kit.js，两边画面一致。
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
import wave
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent.parent
CACHE = HERE / "cache" / "tts"
PROJECTS = HERE / "projects"
FRAME = HERE / "assets" / "frame.html"

VOICE = "zh-CN-YunxiNeural"   # 实测中英混读最准：tractor / distract / subtract 都能被语音识别还原；晓晓会把英文读走样
SR, FPS = 48000, 30
PRE, LEAD, GAP_LINE, GAP_UNIT, TAIL = 0.35, 0.6, 0.25, 0.55, 1.5   # 秒：单元开头留给画面先出场 / 片头 / 句间 / 单元间 / 片尾
TARGET, HARD_MAX = 290, 300   # 目标 ≤ 4:50，硬上限 5:00
MIN_WORDS = 4                 # 删词最多删到只剩 4 个主词
LAYOUTS = ["lay-a", "lay-b", "lay-c"]   # 图右文左 / 图左文右 / 大字主角，按词轮换


def find_word_family() -> Path:
    for c in [os.environ.get("WORD_FAMILY_DIR"), HERE.parent / "word-family",
              Path.home() / ".claude" / "skills" / "word-family"]:
        if c and (Path(c) / "assets" / "kit.js").exists():
            return Path(c).resolve()
    sys.exit("找不到 word-family skill：请设置环境变量 WORD_FAMILY_DIR 指向它的目录")


WF = find_word_family()
sys.path.insert(0, str(WF / "scripts"))
import build as wf_build  # noqa: E402  复用课程校验与零件库加载


# ================================================================ 课程与解说词
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


def clean(s: str) -> str:
    s = re.sub(r"<[^>]+>", "", s)
    return re.sub(r"（[^）]*）|\([^)]*\)", "", s).strip()


def part_dicts(w):
    return [wf_build.norm_part(p) for p in w["parts"]]


def auto_word(w):
    """由卡片字段拼一版解说：第一段讲过渡和词素，第二段讲字面画面和桥接。能用，但口语感弱，建议改写。"""
    ps = part_dicts(w)
    pre = [p for p in ps if p["kind"] == "p"]
    root = [p for p in ps if p["kind"] == "r"]
    s1 = [w["link"]] if w.get("link") else [f"再看 {w['w']}。"]
    if pre and root:
        of = f"，它是 {pre[0]['of'].rstrip('-')} 的变体" if pre[0].get("of") else ""
        s1.append(f"{pre[0]['m'].rstrip('-')} 表示{clean(pre[0]['cn'])}{of}，加上 {root[0]['m']}，{clean(root[0]['cn'])}。")
    s2 = [f"字面意思就是，{w['literal']}。", clean(w["bridge"])]
    return [s1, s2]


def auto_narration(L):
    o, an = L["opening"], L["anchor"]
    N = {"order": [w["w"] for w in L["words"]],
         "opening": [x for x in [clean(o["big"]).replace("＝", "，就是") + "。", clean(o["say"]), clean(o.get("muted", ""))] if x],
         "anchor": [x for x in [an["text"], clean(an.get("more", ""))] if x],
         "words": {w["w"]: auto_word(w) for w in L["words"]},
         "map": ["我们把它们串起来。"] + [f"{w['literal']}，是 {w['w']}。" for w in L["words"]],
         "outro": [f"下次再碰到带 {L['root']['m'].strip('-')} 的词，先想想这个画面，再看它往哪个方向。"],
         "say_as": {}}
    if L.get("finale"):
        N["finale"] = auto_word(L["finale"])
    if L.get("traps"):
        N["traps"] = [clean(t) for t in L["traps"]]
    if L.get("transfer"):
        N["transfer"] = [["最后留几个词，你用同一个画面推推看：",
                          "，".join(q.split("=")[0].strip() for q, _ in L["transfer"]) + "。",
                          "暂停一下，想好了再往下看。"],
                         [clean(a.split("。")[0]) + "。" for _, a in L["transfer"]]]
    return N


def load_narration(stem, L):
    """读 projects/<课>/narration.json；缺的部分用自动解说补上，并给出提醒。"""
    warns = []
    auto = auto_narration(L)
    p = PROJECTS / stem / "narration.json"
    if not p.exists():
        warns.append("没有 narration.json，整片用自动解说（口语感弱）。先运行 init 生成草稿再改写")
        return auto, warns
    N = json.loads(p.read_text(encoding="utf-8"))
    for k in ["opening", "anchor", "map", "outro"]:
        if not N.get(k):
            N[k] = auto[k]
            warns.append(f"narration 缺少 {k}，已用自动解说")
    N.setdefault("say_as", {})
    N.setdefault("order", auto["order"])
    words = N.setdefault("words", {})
    for w in L["words"]:
        v = words.get(w["w"])
        if not (isinstance(v, list) and len(v) == 2 and v[0] and v[1]):
            words[w["w"]] = auto["words"][w["w"]]
            warns.append(f"narration.words.{w['w']} 缺失或格式不对（应为 [[第一段…], [第二段…]]），已用自动解说")
    if L.get("finale") and not (isinstance(N.get("finale"), list) and len(N["finale"]) == 2):
        N["finale"] = auto["finale"]
        warns.append("narration 缺少 finale，已用自动解说")
    for k in ["traps", "transfer"]:
        if L.get(k) and k not in N:
            N[k] = auto[k]
    unknown = [x for x in N["order"] if x not in {w["w"] for w in L["words"]}]
    if unknown:
        warns.append(f"order 里有课程中不存在的词：{unknown}")
    for s in all_lines(N):
        if wlen(s) > 42:
            warns.append(f"句子太长（{len(s)} 字），拆成两句更好念、字幕也不挤：{s[:30]}…")
    return N, warns


def all_lines(N):
    out = list(N["opening"]) + list(N["anchor"]) + list(N["map"]) + list(N["outro"]) + list(N.get("traps", []))
    for v in list(N["words"].values()) + ([N["finale"]] if N.get("finale") else []) + ([N["transfer"]] if N.get("transfer") else []):
        out += v[0] + v[1]
    return [s for s in out if s and s.strip()]


# ================================================================ 配音
def tts_text(s: str, say_as: dict) -> str:
    for k, v in say_as.items():          # 只改朗读用的文字，字幕不变（修正读错的英文词）
        s = re.sub(rf"\b{re.escape(k)}\b", v, s)
    # 「」读出来会有怪停顿；前缀的连字符不读
    return re.sub(r"\b([A-Za-z]+)-(?=\s|，|。|$)", r"\1", s.replace("「", "“").replace("」", "”"))


def tts_path(text, voice, rate):
    return CACHE / (hashlib.sha1(f"{voice}|{rate}|{text}".encode()).hexdigest()[:16] + ".mp3")


def synth_all(lines, say_as, voice, rate):
    import edge_tts
    CACHE.mkdir(parents=True, exist_ok=True)
    texts = {s: tts_text(s, say_as) for s in lines}
    todo = [(t, tts_path(t, voice, rate)) for t in set(texts.values()) if not tts_path(t, voice, rate).exists()]

    async def one(sem, t, p):
        async with sem:
            for attempt in range(4):           # 服务端偶尔返回空音频，重试
                try:
                    await edge_tts.Communicate(t, voice, rate=rate).save(str(p))
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


def decode(mp3: Path, sr: int = SR) -> np.ndarray:
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(mp3), "-f", "s16le", "-ac", "1", "-ar", str(sr), "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.int16)


# ================================================================ 单元、时长与删减
def make_units(L, N, spoken, traps, transfer):
    units = [{"kind": "opening", "lines": N["opening"]}, {"kind": "anchor", "lines": N["anchor"]}]
    for pos, i in enumerate(spoken):
        s1, s2 = N["words"][L["words"][i]["w"]]
        units.append({"kind": "word", "idx": i, "layout": LAYOUTS[pos % 3], "lines": s1 + s2, "s2": len(s1)})
    if L.get("finale"):
        s1, s2 = N["finale"]
        units.append({"kind": "finale", "layout": LAYOUTS[len(spoken) % 3], "lines": s1 + s2, "s2": len(s1)})
    dropped = [w["w"].lower() for i, w in enumerate(L["words"]) if i not in spoken]
    keep = [s for s in N["map"] if not (any(d in s.lower() for d in dropped)
                                         and not any(L["words"][i]["w"].lower() in s.lower() for i in spoken))]
    units.append({"kind": "map", "lines": keep})
    if traps and N.get("traps"):
        units.append({"kind": "traps", "lines": N["traps"]})
    if transfer and N.get("transfer"):
        t1, t2 = N["transfer"]
        units.append({"kind": "transfer", "lines": t1 + t2, "qn": len(t1)})
    units.append({"kind": "outro", "lines": N["outro"]})
    for u in units:
        u["lines"] = [s for s in u["lines"] if s and s.strip()]
    return units


def timeline(units, dur):
    """给每个单元和每句排时间；返回总时长。dur(text) -> 秒。"""
    t = 0.0
    for k, u in enumerate(units):
        lt = PRE + (LEAD if k == 0 else 0)
        u["t0"], lines = t, []
        for s in u["lines"]:
            d = dur(s)
            lines.append({"s": round(lt, 3), "e": round(lt + d, 3), "text": s})
            lt += d + GAP_LINE
        u["lines_t"] = lines
        u["dur"] = round(lt - GAP_LINE + GAP_UNIT + (TAIL if k == len(units) - 1 else 0), 3)
        t += u["dur"]
    return t


def fit_budget(L, N, dur):
    """超过目标时长就删：先删形近陷阱，再删迁移题，最后按 order 从不重要的词删起。"""
    pri = [x for x in N["order"] if x in {w["w"] for w in L["words"]}]
    pri += [w["w"] for w in L["words"] if w["w"] not in pri]
    spoken = list(range(len(L["words"])))
    traps = transfer = True
    notes = []

    def total():
        return timeline(make_units(L, N, spoken, traps, transfer), dur)
    if total() > TARGET and traps and N.get("traps"):
        traps = False
        notes.append("删掉了「形近陷阱」单元（网页版里仍有）")
    if total() > TARGET and transfer and N.get("transfer"):
        transfer = False
        notes.append("删掉了「迁移题」单元（网页版里仍有）")
    for w in reversed(pri):
        if total() <= TARGET or len(spoken) <= MIN_WORDS:
            break
        i = next(i for i, x in enumerate(L["words"]) if x["w"] == w)
        spoken.remove(i)
        notes.append(f"删掉了 {w} 的讲解（家族图上仍显示）。请检查它后一张卡的过渡句是否还接得上")
    units = make_units(L, N, spoken, traps, transfer)
    return units, spoken, timeline(units, dur), notes


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


def subtitles(units):
    subs = []
    for u in units:
        for ln in u["lines_t"]:
            cs = chunks(ln["text"])
            wts = [max(wlen(c), 1) for c in cs]
            t = u["t0"] + ln["s"]
            for c, w in zip(cs, wts):
                d = (ln["e"] - ln["s"]) * w / sum(wts)
                subs.append({"s": round(t, 3), "e": round(t + d, 3), "t": c})
                t += d
    return subs


# ================================================================ 画面
def page_html(L, units, spoken, subs, total):
    data_units = []
    for u in units:
        d = {k: u[k] for k in ("kind", "idx", "layout", "s2", "qn") if k in u}
        d.update(t0=round(u["t0"], 3), dur=u["dur"], lines=u["lines_t"])
        if u["kind"] == "map":            # 家族图节点：解说提到哪个词，哪个节点就在那一刻点亮
            d["nodeAt"] = {}
            for i, w in enumerate(L["words"]):
                hit = next((ln["s"] for ln in u["lines_t"] if w["w"].lower() in ln["text"].lower()), None)
                if hit is not None:
                    d["nodeAt"][str(i)] = hit
        data_units.append(d)
    L = json.loads(json.dumps(L))           # 拷贝一份再改：开场照片换成绝对路径，帧页面在 projects/ 下也能加载
    ph = L["opening"].get("photo")
    if ph:
        ph["uri"] = (WF / "lessons" / ph["file"]).resolve().as_uri()
    data = {"lesson": L, "units": data_units, "subs": subs, "total": total, "spoken": spoken}
    html = FRAME.read_text(encoding="utf-8")
    html = html.replace("/*__KIT_JS__*/", (WF / "assets" / "kit.js").read_text(encoding="utf-8"))
    return html.replace("/*__DATA_JSON__*/null", json.dumps(data, ensure_ascii=False).replace("</", "<\\/"))


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
        sys.exit("Playwright 启动不了浏览器：请安装 Chrome/Edge，或运行 playwright install chromium")
    page = browser.new_page(viewport={"width": 1920, "height": 1080})
    page.goto(html_path.resolve().as_uri())
    page.wait_for_function("window.setT !== undefined")
    page.evaluate("setT(0)")                                   # 先进入开场，等图片加载完，避免第一帧空白
    page.wait_for_function("[...document.images].every(i => i.complete)")
    return pw, browser, page


# ================================================================ 主流程
def prepare(stem, L, voice, rate, quiet=False):
    N, warns = load_narration(stem, L)
    clips = synth_all(all_lines(N), N["say_as"], voice, rate)
    durs = {}

    def dur(s):
        if s not in durs:
            durs[s] = len(decode(clips[s])) / SR
        return durs[s]
    units, spoken, total, notes = fit_budget(L, N, dur)
    if total > HARD_MAX:
        warns.append(f"删减后仍有 {total:.0f} 秒，超过 5 分钟：请缩短解说词（每个词的第二段最多 3 句）")
    if not quiet:
        print(f"\n时长 {total // 60:.0f} 分 {total % 60:.0f} 秒（目标 ≤ {TARGET} 秒），讲解 {len(spoken)}/{len(L['words'])} 个主词")
        for u in units:
            name = u["kind"] + (f" {L['words'][u['idx']]['w']}" if u["kind"] == "word" else "")
            print(f"  [{u['t0']:6.1f}s] {name:<18} {u['dur']:5.1f}s  {len(u['lines'])} 句")
        for n in notes:
            print("  - [删减]", n)
        for w in warns:
            print("  - [提醒]", w)
    return N, clips, units, spoken, total, dur


def cmd_init(stem, L):
    p = PROJECTS / stem / "narration.json"
    if p.exists():
        print(f"已存在，不覆盖：{p}")
        return 0
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(auto_narration(L), ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"已生成解说词草稿：{p}\n下一步：按 references/narration_guide.md 改写成口语，再运行 plan 看时长")
    return 0


def write_frame(stem, L, units, spoken, total):
    subs = subtitles(units)
    build = PROJECTS / stem / "build"
    build.mkdir(parents=True, exist_ok=True)
    hp = build / "frame.html"
    hp.write_text(page_html(L, units, spoken, subs, total), encoding="utf-8")
    return hp


def cmd_stills(stem, L, a):
    N, clips, units, spoken, total, _ = prepare(stem, L, a.voice, a.rate)
    hp = write_frame(stem, L, units, spoken, total)
    out = PROJECTS / stem / "stills"
    out.mkdir(parents=True, exist_ok=True)
    for f in out.glob("*.png"):
        f.unlink()
    pw, browser, page = open_page(hp)
    shots = []
    for k, u in enumerate(units):
        page.evaluate("t => setT(t)", u["t0"] + u["dur"] - 0.05)      # 单元末尾：所有元素都已出场
        p = out / f"{k:02d}_{u['kind']}.png"
        page.screenshot(path=str(p))
        shots.append(p)
    browser.close()
    pw.stop()
    try:
        from PIL import Image
        W, H, cols = 640, 360, 3
        sheet = Image.new("RGB", (W * cols, H * ((len(shots) + cols - 1) // cols)), "white")
        for i, s in enumerate(shots):
            sheet.paste(Image.open(s).resize((W, H)), ((i % cols) * W, (i // cols) * H))
        sheet.save(out / "_sheet.jpg", quality=85)
        print(f"\n定格图：{out}（总览 _sheet.jpg）")
    except ImportError:
        print(f"\n定格图：{out}")
    return 0


def cmd_render(stem, L, a):
    N, clips, units, spoken, total, dur = prepare(stem, L, a.voice, a.rate)
    if total > HARD_MAX and not a.force:
        print("超过 5 分钟，不渲染（加 --force 强制）")
        return 1
    build = PROJECTS / stem / "build"
    hp = write_frame(stem, L, units, spoken, total)
    # 音频：按时间轴把每句放到对应位置
    audio = np.zeros(int((total + 1) * SR), np.int16)
    for u in units:
        for ln in u["lines_t"]:
            clip = decode(clips[ln["text"]])
            i0 = int((u["t0"] + ln["s"]) * SR)
            audio[i0:i0 + len(clip)] = clip[:len(audio) - i0]
    with wave.open(str(build / "audio.wav"), "wb") as wf:
        wf.setnchannels(1), wf.setsampwidth(2), wf.setframerate(SR)
        wf.writeframes(audio.tobytes())
    out = PROJECTS / stem / f"{stem}.mp4"
    ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "image2pipe", "-c:v", "mjpeg", "-framerate", str(FPS), "-i", "-",
                           "-i", str(build / "audio.wav"), "-af", "loudnorm=I=-16:TP=-1.5:LRA=11",
                           "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
                           "-c:a", "aac", "-b:a", "160k", "-shortest", str(out)], stdin=subprocess.PIPE)
    pw, browser, page = open_page(hp)
    n = int(total * FPS)
    last, shots = None, 0
    print(f"\n逐帧渲染 {n} 帧…")
    for f in range(n):
        need = page.evaluate("t => setT(t)", f / FPS)
        if need or last is None:          # 画面没变化（没有动画、字幕没换）就复用上一帧，省掉截图
            last = page.screenshot(type="jpeg", quality=92)
            shots += 1
        ff.stdin.write(last)
        if f % (FPS * 30) == 0:
            print(f"  {f / FPS:5.0f}s / {total:.0f}s")
    browser.close()
    pw.stop()
    ff.stdin.close()
    ff.wait()
    if ff.returncode:
        print("ffmpeg 合成失败")
        return 1
    print(f"完成：{out}（{total:.0f} 秒；实际截图 {shots} 帧，其余复用）")
    return 0


def cmd_check(stem, L, a):
    """把每句含英文的配音转写回文字，对比解说词里的英文词，找出可能读错的。"""
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        print("没装 faster-whisper（pip install faster-whisper），跳过读音检查")
        return 0
    N, warns = load_narration(stem, L)
    clips = synth_all(all_lines(N), N["say_as"], a.voice, a.rate)
    model = WhisperModel("small", device="cpu", compute_type="int8")
    stop = {"the", "and", "you", "for", "with", "this", "that", "from", "are", "was"}
    bad = 0

    def heard_ok(tok, letters):
        # 在转写里找和这个词最像的一段（长度 ±2），整体相似度 ≥ 0.7 就算读对。
        # 只看连续相同字母会把读对的 append 听成 "up and" 也判错，误报太多会把人带去修本来没错的地方。
        best = 0.0
        for n in range(max(1, len(tok) - 2), len(tok) + 3):
            for i in range(0, max(1, len(letters) - n + 1)):
                best = max(best, difflib.SequenceMatcher(None, tok, letters[i:i + n]).ratio())
        return best >= 0.7

    for s in all_lines(N):
        # 3 个字母以内的（dis、sub、ad 这类前缀）Whisper 在中文语境里本来就听不准，不查
        toks = [t for t in re.findall(r"[A-Za-z]{4,}", s) if t.lower() not in stop]
        if not toks:
            continue
        # Whisper 要求 16 kHz 单声道；用 48 kHz 喂进去会听成慢放录音，满篇幻觉
        segs, _ = model.transcribe(decode(clips[s], 16000).astype(np.float32) / 32768, language="zh",
                                   initial_prompt="以下是中英混合的英语词汇讲解。")
        heard = "".join(x.text for x in segs)
        letters = re.sub(r"[^a-z]", "", heard.lower())
        for t in toks:
            if not heard_ok(t.lower(), letters):
                bad += 1
                print(f"  - 可能读错 {t}：听到「{heard.strip()}」")
    print("没有发现读错的英文词" if not bad else f"\n共 {bad} 处。确认读错的，在 narration.json 的 say_as 里加替换，例如 \"retractable\": \"re-tractable\"")
    return 0


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description="word-family 课程 → 讲解视频")
    ap.add_argument("cmd", choices=["init", "plan", "stills", "render", "check"])
    ap.add_argument("lesson", help="词根名（如 tract）或课程 JSON 路径")
    ap.add_argument("--voice", default=VOICE)
    ap.add_argument("--rate", default="+0%", help="语速，如 +5%%")
    ap.add_argument("--force", action="store_true", help="超过 5 分钟也渲染")
    a = ap.parse_args()
    stem, L = load_lesson(a.lesson)
    if a.cmd == "init":
        return cmd_init(stem, L)
    if a.cmd == "plan":
        prepare(stem, L, a.voice, a.rate)
        return 0
    return {"stills": cmd_stills, "render": cmd_render, "check": cmd_check}[a.cmd](stem, L, a)


if __name__ == "__main__":
    sys.exit(main())
