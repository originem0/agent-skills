"""script_md / video 的单元测试。运行：python -I skills/word-family-video/scripts/test_script.py"""
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))   # python -I 不把脚本所在目录放进 sys.path
import script_md as smd  # noqa: E402
import video as v  # noqa: E402  导入时会定位 word-family 并加载它的 build.py

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
    assert not any("真实图片" in x for x in warns_of(GOOD))                 # 用户取消了「每支至少一张照片」的配额


CLEAN = GOOD.replace(">> 这里能不能再加一个生活里的例子？\n", "")


def test_statuses_are_draft_and_approved():
    # 出片只认用户确认：没有「AI 审过就能出片」的中间状态
    assert smd.STATUSES == ("draft", "approved")
    try:
        smd.mark(CLEAN, "reviewed", "AI 审稿")
        raise AssertionError("reviewed 不该再是合法状态")
    except ValueError:
        pass


def test_fingerprint_ignores_status():
    marked = smd.mark(CLEAN, "approved", "用户确认", today="2026-10-28")
    assert smd.fingerprint(marked) == smd.fingerprint(CLEAN)
    assert smd.fingerprint(CLEAN.replace("一家", "一伙")) != smd.fingerprint(CLEAN)


def test_mark_writes_front_matter():
    marked = smd.mark(CLEAN, "approved", "用户确认", today="2026-10-28")
    head = marked.split("---")[1]
    assert "status: approved" in head
    assert f"checked: {smd.fingerprint(CLEAN)} · 用户确认 · 2026-10-28" in head
    assert head.index("status:") > head.index("lesson:")           # 状态紧跟在 lesson 后面
    again = smd.mark(marked, "draft", "")
    assert "status: draft" in again and "checked:" not in again


def test_gate():
    assert any("还没确认" in x for x in smd.gate(smd.parse(CLEAN)))
    ok = smd.mark(CLEAN, "approved", "用户确认")
    assert smd.gate(smd.parse(ok)) == []
    assert any("确认之后脚本又改过" in x for x in smd.gate(smd.parse(ok.replace("一家", "一伙"))))
    hand = CLEAN.replace("lesson: pend", "lesson: pend\nstatus: approved")     # 用户在文件里手改的
    assert any("checked 指纹" in x for x in smd.gate(smd.parse(hand)))
    noted = smd.mark(GOOD, "approved", "用户确认")
    assert any("批注" in x for x in smd.gate(smd.parse(noted)))


def test_review_done_multi_round():
    r1 = "# 审稿记录：pend\n\n## 审稿意见 第 1 轮（AI 审稿）\n\n1. ……\n\n## 处理结果 第 1 轮\n\n1. 采纳：改了开头。\n"
    assert smd.review_done(r1)
    r2 = r1 + "\n## 审稿意见 第 2 轮（AI 审稿）\n\n1. ……\n\n## 处理结果 第 2 轮\n\n"
    assert not smd.review_done(r2)                                  # 只看最新一轮
    assert not smd.review_done("# 审稿记录：pend\n")


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


def test_no_codex_dependency():
    # 用户明确不要绑定 Codex：审稿方由用户选，脚本里不该再有调用外部模型的代码
    assert not hasattr(v, "run_codex")
    assert "codex" not in Path(v.__file__).read_text(encoding="utf-8").lower()


def test_append_review_rounds():
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "review.md"
        assert v.append_review(p, "pend", "AI 审稿", "abcd1234", "1. 开头太慢。") == 1
        assert not smd.review_done(p.read_text(encoding="utf-8"))
        p.write_text(p.read_text(encoding="utf-8") + "1. 采纳：开头改成 NBA 事件。\n", encoding="utf-8")
        assert smd.review_done(p.read_text(encoding="utf-8"))
        assert v.append_review(p, "pend", "AI 审稿", "abcd5678", "1. 结尾没回扣。") == 2
        text = p.read_text(encoding="utf-8")
        assert "采纳：开头改成 NBA 事件" in text and "第 2 轮" in text     # 第一轮的处理结果还在
        assert not smd.review_done(text)


def test_review_prepares_package_and_records():
    import tempfile
    import types
    with tempfile.TemporaryDirectory() as d:
        old = v.PROJECTS
        v.PROJECTS = Path(d)
        try:
            proj = Path(d) / "pend"
            proj.mkdir()
            (proj / "script.md").write_text(CLEAN, encoding="utf-8")
            assert v.cmd_review("pend", L, types.SimpleNamespace(record=False)) == 0
            build = proj / "build"
            assert (build / "review_brief.md").exists()
            assert not (proj / "review.md").exists()                     # 只准备审稿包，不自动审
            assert v.cmd_review("pend", L, types.SimpleNamespace(record=True)) == 1      # 还没有审稿意见
            (build / "review_raw.md").write_text("1. 开头太慢。", encoding="utf-8")
            assert v.cmd_review("pend", L, types.SimpleNamespace(record=True)) == 0
            assert "第 1 轮" in (proj / "review.md").read_text(encoding="utf-8")
            assert not (build / "review_raw.md").exists()                # 记完就清掉，免得重复记
        finally:
            v.PROJECTS = old


def test_mark_approved_waits_for_review_processing():
    import tempfile
    import types
    with tempfile.TemporaryDirectory() as d:
        old = v.PROJECTS
        v.PROJECTS = Path(d)
        try:
            proj = Path(d) / "pend"
            proj.mkdir()
            (proj / "script.md").write_text(CLEAN, encoding="utf-8")
            v.append_review(proj / "review.md", "pend", "AI 审稿", "abcd1234", "1. 开头太慢。")
            ok = types.SimpleNamespace(args=["approved"])
            assert v.cmd_mark("pend", L, ok) == 1                        # 审稿意见还没处理
            with open(proj / "review.md", "a", encoding="utf-8") as f:
                f.write("1. 不采纳：开头已经是具体事件。\n")
            assert v.cmd_mark("pend", L, ok) == 0
            assert smd.parse((proj / "script.md").read_text(encoding="utf-8")).status == "approved"
            assert v.cmd_mark("pend", L, types.SimpleNamespace(args=["reviewed"])) == 1   # 不再有这个状态
        finally:
            v.PROJECTS = old


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


def test_say_as_inside_chinese():
    # 中文口播里英文词两边常不留空格：\b 在汉字旁不算边界，say_as 会悄悄失效
    assert v.tts_text("这个live的意思", {"live": "laiv"}) == "这个laiv的意思"
    assert v.tts_text("olive 和 live", {"live": "laiv"}) == "olive 和 laiv"      # 不改词中间的字母
    t, how = v.cue_time("这个live的意思", "live", [{"t": 0.3, "d": 0.4, "w": "laiv"}], 1.5, {"live": "laiv"})
    assert how == "exact"


def test_review_keeps_pasted_comments():
    # 贴好了意见又顺手重跑 review（没加 --record）：不能把贴进去的意见删掉
    import tempfile
    import types
    with tempfile.TemporaryDirectory() as d:
        old = v.PROJECTS
        v.PROJECTS = Path(d)
        try:
            proj = Path(d) / "pend"
            (proj / "build").mkdir(parents=True)
            (proj / "script.md").write_text(CLEAN, encoding="utf-8")
            (proj / "build" / "review_raw.md").write_text("1. 开头太慢。", encoding="utf-8")
            assert v.cmd_review("pend", L, types.SimpleNamespace(record=False)) == 1
            assert (proj / "build" / "review_raw.md").read_text(encoding="utf-8") == "1. 开头太慢。"
        finally:
            v.PROJECTS = old


def test_review_records_reviewed_fingerprint():
    # 打包后、记录前改了脚本：这一轮要标被审的那一版，而不是记录时的版本
    import tempfile
    import types
    with tempfile.TemporaryDirectory() as d:
        old = v.PROJECTS
        v.PROJECTS = Path(d)
        try:
            proj = Path(d) / "pend"
            proj.mkdir()
            (proj / "script.md").write_text(CLEAN, encoding="utf-8")
            fp0 = smd.fingerprint(CLEAN)
            assert v.cmd_review("pend", L, types.SimpleNamespace(record=False)) == 0
            (proj / "script.md").write_text(CLEAN.replace("从底下", "从下面", 1), encoding="utf-8")
            assert smd.fingerprint((proj / "script.md").read_text(encoding="utf-8")) != fp0
            (proj / "build" / "review_raw.md").write_text("1. 开头太慢。", encoding="utf-8")
            assert v.cmd_review("pend", L, types.SimpleNamespace(record=True)) == 0
            assert f"脚本指纹 {fp0}" in (proj / "review.md").read_text(encoding="utf-8")
        finally:
            v.PROJECTS = old


def test_fact_number_whole_match():
    # 「15」不能因为课程里有「1570」就算查到了：数字要整段对上
    bad = GOOD.replace("{pend}，挂。", "{pend}，挂。有 15 种用法。")
    assert any("「15」" in e for e in errs_of(bad))


def test_review_pasted_headings_demoted():
    # 贴进来的意见里自带「## 处理结果」：不能被当成处理过了，也不能多算一轮
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "review.md"
        v.append_review(p, "pend", "AI 审稿", "abcd1234", "## 审稿意见\n1. 开头慢。\n## 处理结果\n采纳")
        text = p.read_text(encoding="utf-8")
        assert not smd.review_done(text)
        assert v.append_review(p, "pend", "AI 审稿", "abcd1234", "1. 再看看。") == 2


def test_status_without_projects_dir():
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        old = v.PROJECTS
        v.PROJECTS = Path(d) / "projects"
        try:
            assert v.cmd_status() == 0
        finally:
            v.PROJECTS = old


def test_photo_path_inside_project():
    for bad in ("../x.jpg", "C:/x.jpg", "/x.jpg"):
        text = GOOD.replace("## 一场停摆 [event]", f"## 一场停摆 [photo: {bad}]\n> 署名：照片：A，CC0，Commons（https://x）", 1)
        assert any("项目文件夹" in e for e in errs_of(text)), bad


# ================================================================ 第二期：画面


def _tl(*beats):
    out, t = [], 0.0
    for blk, arg, lines, data in beats:
        rows = [{"lineno": 1, "text": p, "plain": p.replace("{", "").replace("}", ""), "s": t + 0.5 + i,
                 "e": t + 1.4 + i, "cues": cues} for i, (p, cues) in enumerate(lines)]
        out.append({"lineno": 1, "title": arg or blk, "block": blk, "arg": arg, "data": data,
                    "t0": t, "t1": t + 1 + len(lines), "lines": rows})
        t += 1 + len(lines)
    return {"total": t, "words": [b[1] for b in beats if b[0] == "word"], "beats": out, "subs": []}


def _browser():
    try:
        import playwright  # noqa: F401
    except ImportError:
        return None
    return True


def _fake_tts(d):
    """不联网：每句 1 秒静音、没有逐词时间戳。返回还原函数。"""
    saved = (v.synth_all, v.decode, v.tts_marks)
    v.synth_all = lambda lines, sa, voice, rate, marks=False: {s: Path(d) / "x.mp3" for s in lines}
    v.decode = lambda mp3, sr=v.SR: v.np.zeros(int(sr * 1.0), v.np.int16)
    v.tts_marks = lambda mp3: []

    def restore():
        v.synth_all, v.decode, v.tts_marks = saved
    return restore


def test_ensure_timeline_refreshes_stale():
    import tempfile
    import types
    with tempfile.TemporaryDirectory() as d:
        old = v.PROJECTS
        v.PROJECTS = Path(d)
        restore = _fake_tts(d)
        try:
            (Path(d) / "pend").mkdir()
            (Path(d) / "pend" / "script.md").write_text(CLEAN, encoding="utf-8")
            a = types.SimpleNamespace(voice=v.VOICE, rate=v.RATE)
            sc, tl, _ = v.ensure_timeline("pend", L, a)
            assert tl["fingerprint"] == smd.fingerprint(CLEAN)
            assert (Path(d) / "pend" / "build" / "timeline.json").exists()
            (Path(d) / "pend" / "script.md").write_text(CLEAN.replace("从底下", "从下面", 1), encoding="utf-8")
            sc2, tl2, _ = v.ensure_timeline("pend", L, a)
            assert tl2["fingerprint"] != tl["fingerprint"]
            (Path(d) / "pend" / "script.md").write_text(CLEAN.replace("{sub}", "{sup}"), encoding="utf-8")
            assert v.ensure_timeline("pend", L, a) is None                       # 脚本有错误：不出时间轴
        finally:
            v.PROJECTS = old
            restore()


def test_render_gate_refuses_unapproved_and_annotated():
    import tempfile
    import types
    with tempfile.TemporaryDirectory() as d:
        old = v.PROJECTS
        v.PROJECTS = Path(d)
        restore = _fake_tts(d)
        try:
            (Path(d) / "pend").mkdir()
            a = types.SimpleNamespace(voice=v.VOICE, rate=v.RATE, force=False)
            (Path(d) / "pend" / "script.md").write_text(CLEAN, encoding="utf-8")            # draft
            assert v.cmd_render("pend", L, a) == 1
            approved = smd.mark(CLEAN, "approved", "用户确认", today="2026-10-28")
            (Path(d) / "pend" / "script.md").write_text(approved.replace("{pend}，挂。", "{pend}，挂。\n>> 再改改"), encoding="utf-8")
            assert v.cmd_render("pend", L, a) == 1                                       # 指纹变了 + 有批注
            assert not list(Path(d).rglob("*.mp4"))
        finally:
            v.PROJECTS = old
            restore()


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
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        old, argv = v.PROJECTS, sys.argv
        v.PROJECTS = Path(d)
        restore = _fake_tts(d)
        try:
            (Path(d) / "pend").mkdir()
            (Path(d) / "pend" / "script.md").write_text(CLEAN, encoding="utf-8")
            sys.argv = ["video.py", "render", "pend"]
            assert v.main() == 1                                                            # draft：走 v2 闸门
            sys.argv = ["video.py", "init", "pend"]                                         # v1 的 init 已删除
            try:
                v.main()
                raise AssertionError("init 应该被拒绝")
            except SystemExit as e:
                assert e.code == 2
            assert not list(Path(d).rglob("*.mp4"))
        finally:
            v.PROJECTS, sys.argv = old, argv
            restore()


def test_no_v1_left():
    src = Path(v.__file__).read_text(encoding="utf-8")
    for name in ("auto_narration", "make_units", "fit_budget", "LAYOUTS", "load_narration", "narration.json",
                 "FRAME_V1", "def cmd_init", "def prepare", "_v2("):
        assert name not in src, name
    assert not (v.HERE / "references" / "narration_guide.md").exists()
    assert not (v.HERE / "assets" / "frame_v1.html").exists()
    assert not list(v.HERE.glob("projects/*/narration.json"))


def test_photo_artist_not_doubled():
    # Commons 的 Artist 对佚名作者常给两份同样的文字（多语言 span），去标签后会变成「Unknown authorUnknown author」
    import photo
    assert photo.artist_name('<span lang="en">Unknown author</span><span>Unknown author</span>') == "Unknown author"
    assert photo.artist_name('<a href="x">MOSSOT</a>') == "MOSSOT"
    assert photo.artist_name("") == "佚名"


# ================================================================ 看片反馈：主图居中、让位、例句、构图、倾斜、取图


def test_validate_example_rules():
    base = GOOD.replace("{pend}，挂。", "{pend}，挂。It depends 就是看情况。")
    ok = base.replace("## suspend [word: suspend]\n", "## suspend [word: suspend]\n> 例句：It {depends}\n")
    assert errs_of(ok) == [], errs_of(ok)
    unread = base.replace("## suspend [word: suspend]\n", "## suspend [word: suspend]\n> 例句：on {hold}\n")
    assert errs_of(unread) == [], errs_of(unread)                            # 例句可读可不读
    two = ok.replace("> 例句：It {depends}\n", "> 例句：It {depends}\n> 例句：It depends\n")
    assert any("例句" in e and "一条" in e for e in errs_of(two))
    long = ok.replace("> 例句：It {depends}\n", "> 例句：a b c d e f g h {i}\n").replace("It depends 就是看情况。", "a b c d e f g h i 就是看情况。")
    assert errs_of(long) == [] and any("例句" in w for w in smd.lint(smd.parse(long)))


def test_build_timeline_example_time():
    text = "---\nlesson: pend\nspine: x\n---\n\n## suspend [word: suspend]\n> 例句：tech {support}\n我们叫 tech support。\n"
    sc = smd.parse(text)
    marks = {"我们叫 tech support。": [{"t": 0.2, "d": 0.2, "w": "我们叫"}, {"t": 0.7, "d": 0.3, "w": "tech"}, {"t": 1.1, "d": 0.4, "w": "support"}]}
    tl, warns = v.build_timeline(sc, {}, lambda p: p, lambda mp3: 2.0, lambda mp3: marks[mp3])
    b = tl["beats"][0]
    assert b["example_at"] == round(b["lines"][0]["s"] + 0.7, 3) and warns == []


def test_photo_get_downloads_image():
    import base64
    import tempfile
    import types
    png = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==")
    with tempfile.TemporaryDirectory() as d:
        old = v.PROJECTS
        v.PROJECTS = Path(d) / "projects"
        try:
            src = Path(d) / "x.png"
            src.write_bytes(png)
            (v.PROJECTS / "pend").mkdir(parents=True)
            assert v.cmd_photo("pend", L, types.SimpleNamespace(args=["get", src.as_uri(), "phone"], clip="")) == 0
            assert list((v.PROJECTS / "pend" / "media").glob("phone.*"))
            bad = Path(d) / "x.html"
            bad.write_text("<html>not an image</html>", encoding="utf-8")
            assert v.cmd_photo("pend", L, types.SimpleNamespace(args=["get", bad.as_uri(), "bad"], clip="")) == 1
            assert not list((v.PROJECTS / "pend" / "media").glob("bad.*"))
        finally:
            v.PROJECTS = old


def test_photo_get_flattens_transparency():
    # 透明背景的 PNG/WebP 直接转 RGB 会露出底下的杂色（mikuexpo 的 hero_chara.webp 变成深蓝夹白块）：先铺白底
    try:
        from PIL import Image
    except ImportError:
        print("SKIP test_photo_get_flattens_transparency（没装 Pillow）")
        return
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        src = Path(d) / "t.png"
        im = Image.new("RGBA", (32, 32), (0, 0, 128, 0))         # 全透明，但底下的颜色是深蓝
        im.paste((200, 30, 30, 255), (0, 0, 16, 32))             # 左半边不透明的红（单个像素经 JPEG 色度抽样会被抹掉）
        im.save(src)
        got = v.get_image(src.as_uri(), Path(d) / "out.jpg")
        px = Image.open(got["file"]).convert("RGB")
        assert min(px.getpixel((28, 16))) > 235, px.getpixel((28, 16))     # 透明处是白的
        assert px.getpixel((4, 16))[0] > 150 and px.getpixel((4, 16))[2] < 90  # 不透明处保留原色
        pal = Path(d) / "p.png"
        Image.new("P", (2, 2), 0).save(pal, transparency=0)                  # 调色板透明
        got = v.get_image(pal.as_uri(), Path(d) / "out2.jpg")
        assert min(Image.open(got["file"]).convert("RGB").getpixel((1, 1))) > 235


# ================================================================ 看片反馈 2：多义项、每个词默认带课程例句


def test_preview_refreshes_when_voice_or_rate_changes():
    import tempfile
    import types
    from unittest.mock import patch
    with tempfile.TemporaryDirectory() as d:
        project = Path(d) / "pend"
        (project / "build").mkdir(parents=True)
        mixes = []
        a = types.SimpleNamespace(voice=v.VOICE, rate=v.RATE)

        def timeline(*args):
            return None, {"fingerprint": "same-script", "voice": a.voice, "rate": a.rate}, {}

        def mix(*args):
            mixes.append((a.voice, a.rate))
            return b"audio"

        def write(path, audio):
            path.write_bytes(audio)

        with patch.object(v, "PROJECTS", Path(d)), patch.object(v, "ensure_timeline", timeline), \
                patch.object(v, "mix_timeline", mix), patch.object(v, "write_audio", write), \
                patch.object(v, "write_frame", return_value=project / "build" / "preview.html"):
            assert v.cmd_preview("pend", L, a) == 0
            assert v.cmd_preview("pend", L, a) == 0
            a.voice = "zh-CN-YunxiNeural"
            assert v.cmd_preview("pend", L, a) == 0
            a.rate = "+0%"
            assert v.cmd_preview("pend", L, a) == 0
            assert mixes == [(v.VOICE, v.RATE), (a.voice, v.RATE), (a.voice, a.rate)]


def test_tts_replaces_partial_cache_and_keeps_failed_attempts_out():
    import tempfile
    import types
    from unittest.mock import patch
    with tempfile.TemporaryDirectory() as d, patch.object(v, "CACHE", Path(d)):
        calls = []

        class Communicate:
            def __init__(self, text, *args, **kwargs):
                self.text = text

            async def save(self, audio, marks):
                calls.append(self.text)
                Path(audio).write_bytes(b"partial")
                Path(marks).write_text("broken", encoding="utf-8")
                if self.text == "failure":
                    raise RuntimeError("interrupted stream")
                Path(audio).write_bytes(b"complete" * 200)
                Path(marks).write_text(json.dumps({"type": "WordBoundary", "offset": 0,
                                                  "duration": 1000000, "text": self.text}), encoding="utf-8")

        async def no_wait(*args):
            pass

        fake = types.SimpleNamespace(Communicate=Communicate)
        with patch.dict(sys.modules, {"edge_tts": fake}), patch.object(v.asyncio, "sleep", no_wait):
            broken = v.tts_path("repair", v.VOICE, v.RATE)
            broken.write_bytes(b"partial")
            broken.with_suffix(".words.jsonl").write_text("broken", encoding="utf-8")
            clips = v.synth_all(["repair"], {}, v.VOICE, v.RATE, marks=True)
            assert clips["repair"].stat().st_size > 1000
            assert v.tts_marks(clips["repair"])[0]["w"] == "repair"
            v.synth_all(["repair"], {}, v.VOICE, v.RATE, marks=True)
            assert calls == ["repair"]
            try:
                v.synth_all(["failure"], {}, v.VOICE, v.RATE, marks=True)
                raise AssertionError("failed stream must be reported")
            except RuntimeError:
                pass
            failed = v.tts_path("failure", v.VOICE, v.RATE)
            assert not failed.exists() and not failed.with_suffix(".words.jsonl").exists()


def test_check_records_unclear_words_without_calling_them_passed():
    import tempfile
    import types
    from unittest.mock import patch

    class Model:
        def __init__(self, *args, **kwargs):
            pass

        def transcribe(self, audio, **kwargs):
            return [types.SimpleNamespace(text=kwargs.get("hotwords", "portable"))], None

    with tempfile.TemporaryDirectory() as d:
        project = Path(d) / "pend"
        project.mkdir()
        (project / "script.md").write_text(CLEAN, encoding="utf-8")
        lines = ["这个 portable 是便携的。", "再说 unknownword。"]
        a = types.SimpleNamespace(voice=v.VOICE, rate=v.RATE, asr="large-v3-turbo")
        with patch.object(v, "PROJECTS", Path(d)), patch.object(v, "check_lines", return_value=(lines, {})), \
                patch.object(v, "synth_all", return_value={s: Path(d) / "x.mp3" for s in lines}), \
                patch.object(v, "decode", return_value=v.np.zeros(16000, v.np.int16)), \
                patch.dict(sys.modules, {"faster_whisper": types.SimpleNamespace(WhisperModel=Model)}):
            assert v.cmd_check("pend", L, a) == 0
        report = json.loads((project / "build" / "check.json").read_text(encoding="utf-8"))
        assert report["status"] == "needs_listening" and report["possible_errors"] == []
        assert report["unclear"][0]["word"] == "unknownword"
        assert report["fingerprint"] == smd.fingerprint(CLEAN)


def test_render_audits_and_preserves_last_good_video_on_failure():
    import tempfile
    import types
    from unittest.mock import patch
    with tempfile.TemporaryDirectory() as d:
        project = Path(d) / "pend"
        (project / "build").mkdir(parents=True)
        approved = smd.parse(smd.mark(CLEAN, "approved", "用户授权 AI 审核"))
        tl = {"total": 3.0, "fingerprint": smd.fingerprint(approved.text), "voice": v.VOICE, "rate": v.RATE}
        out = project / "pend.mp4"
        out.write_bytes(b"last good video")
        attempts = []
        a = types.SimpleNamespace(voice=v.VOICE, rate=v.RATE, force=False)
        result, duration = [1], [3.0]

        def render(hp, total, target, wav):
            attempts.append(target)
            target.write_bytes(b"new video")
            return 1, result[0]

        with patch.object(v, "PROJECTS", Path(d)), patch.object(v, "load_script", return_value=(approved, [], [])), \
                patch.object(v, "ensure_timeline", return_value=(approved, tl, {})), \
                patch.object(v, "write_frame", return_value=project / "build" / "frame.html"), \
                patch.object(v, "mix_timeline", return_value=b"audio"), patch.object(v, "write_audio"), \
                patch.object(v, "render_frames", render), patch.object(v, "media_duration", side_effect=lambda p: duration[0]), \
                patch.object(v, "audit_timeline", return_value=["bad picture"], create=True) as audit:
            (project / "build" / "approval.json").write_text(json.dumps(v.input_snapshot("pend", L, approved, a)), encoding="utf-8")
            (project / "build" / "film.json").write_text(json.dumps({"fingerprint":"compiled-fixture"}), encoding="utf-8")
            assert v.cmd_render("pend", L, a) == 1
            assert not attempts and out.read_bytes() == b"last good video"
            audit.return_value = []
            assert v.cmd_render("pend", L, a) == 1
            assert out.read_bytes() == b"last good video"
            result[0], duration[0] = 0, 4.0
            assert v.cmd_render("pend", L, a) == 1
            assert out.read_bytes() == b"last good video"
            duration[0] = 3.0
            assert v.cmd_render("pend", L, a) == 0
            assert out.read_bytes() == b"new video"
            assert all(path != out for path in attempts)
            assert not list(project.glob("*.rendering.mp4"))
            manifest = json.loads((project / "build" / "render.json").read_text(encoding="utf-8"))
            assert manifest["fingerprint"] == tl["fingerprint"] and manifest["duration"] == 3.0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")      # Git Bash 下默认不是 UTF-8，中文会乱码
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
