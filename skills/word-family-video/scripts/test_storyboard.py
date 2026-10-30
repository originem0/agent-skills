"""分镜的用户行为：内容契约、独立触发、输入审核、同一画面随机定位。无需联网。"""
import copy
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import video as v
import storyboard

L = {"root": {"m": "port", "cn": "搬"}, "words": [
    {"w": "import", "fact": "portare，搬进", "meaning": "导入", "scene": [{"k":"fig", "x":140}]},
    {"w": "export", "fact": "portare，搬出", "meaning": "导出"}]}


def relation(rid, word, detail):
    return dict(id=rid, kind="etymology", label=word, detail=detail, source="lesson:" + word, words=[word])


def body():
    return [
        ("inside", "先{first|import}，再{second|import}。", dict(
            learn=[relation("in", "import", "往里面搬")],
            nodes=[dict(id="word", type="text", relation="in", x=120, y=240, w=650, h=140, font="en", size=96)],
            events=[dict(target="word", at="first", duration=.5, to={"x":740}),
                    dict(target="word", at="second", duration=.5, to={"x":1120})])),
        ("outside", "{out|export}，往外搬。", dict(
            requires=["in"], learn=[relation("out", "export", "往外面搬")],
            nodes=[dict(id="word", type="text", relation="out", x=120, y=240, w=700, h=140)])),
        ("close", "进出需要参照，搬的动作没有变。", dict(
            recall=["in", "out"], closing=True,
            nodes=[dict(id="connections", type="summary", refs=["in", "out"], x=120, y=200, w=1680, h=580)]))]


def script(beats=None):
    text = "---\nlesson: port\nspine: 同一张照片随着参照改变方向\n---\n"
    for name, narration, scene in beats or body():
        text += f"\n## {name} [shot: {name}]\n> 已知：手机里的一张照片\n> 推进：分清相对于谁的进出\n{narration}\n```scene\n{json.dumps(scene,ensure_ascii=False)}\n```\n"
    return v.smd.parse(text)


def timeline(sc):
    marks = [{"w":"先", "t":0}, {"w":"import", "t":1}, {"w":"再", "t":2}, {"w":"import", "t":3},
             {"w":"export", "t":1}, {"w":"往外搬", "t":2}]
    tl = v.build_timeline(sc, {}, lambda _: Path("voice.mp3"), lambda _: 6, lambda _: marks)[0]
    tl.update(version=v.TIMELINE_VERSION, fingerprint=v.smd.fingerprint(sc.text), voice=v.VOICE, rate=v.RATE)
    return tl


class StoryboardTests(unittest.TestCase):
    def test_navigation_tracks_introductions_and_can_return_to_an_earlier_word(self):
        beats=body()
        beats[-1][2]["focus"]=["import"]
        sc=script(beats)
        self.assertEqual(v.smd.validate(sc,L,"port"),[])
        film=v.compiler.compile_film("port",L,timeline(sc),Path("."),v.WF)
        nav=[s["navigation"] for s in film["shots"]]
        self.assertEqual(nav[0],{"words":["import"],"active":["import"]})
        self.assertEqual(nav[1],{"words":["import","export"],"active":["export"]})
        self.assertEqual(nav[2],{"words":["import","export"],"active":["import"]})

    def test_navigation_rejects_unknown_words_and_keeps_contrasts_out_of_family(self):
        for value in (["export"],["import","IMPORT"],"import",[[]]):
            beats=body();beats[0][2]["focus"]=value
            self.assertTrue(any("focus" in e for e in v.smd.validate(script(beats),L,"port")))
        beats=body();beats[1][2]["learn"][0]["kind"]="contrast"
        film=v.compiler.compile_film("port",L,timeline(script(beats)),Path("."),v.WF)
        self.assertEqual(film["shots"][-1]["navigation"]["words"],["import"])
        beats[1][2]["focus"]=["export"]
        self.assertTrue(any("focus" in e for e in v.smd.validate(script(beats),L,"port")))

    def test_browser_navigation_fits_long_lists_and_is_reversible(self):
        sc=script();tl=timeline(sc)
        film=v.compiler.compile_film("port",L,tl,Path("."),v.WF)
        words=["extraordinary"+str(i) for i in range(24)]
        film["shots"][1]["navigation"]={"words":words,"active":[words[19]]}
        film["shots"][2]["navigation"]={"words":words,"active":[words[2]]}
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/"frame.html"
            path.write_text(v.frame_html("test",L,tl,film=film),encoding="utf-8")
            pw,browser,page=v.open_page(path)
            try:
                self.assertEqual(page.locator("#words .word").all_text_contents(),["import"])
                for index,expected in ((1,words[19]),(2,words[2])):
                    page.evaluate("t=>setT(t)",film["shots"][index]["t0"]+.2)
                    self.assertEqual(page.locator("#words .now").all_text_contents(),[expected])
                    self.assertLess(page.locator("#words .word").count(),len(words))
                    self.assertGreater(page.locator("#words .more").count(),0)
                    self.assertTrue(page.evaluate("""() => {const r=document.getElementById('words').getBoundingClientRect();
                        return [...document.querySelectorAll('#words span')].every(n=>{const b=n.getBoundingClientRect();return b.left>=r.left-1 && b.right<=r.right+1;});}"""))
                    self.assertEqual(page.evaluate("audit()"),[])
                expected=page.locator("#words").inner_html()
                page.evaluate("setT(0)")
                self.assertEqual(page.locator("#words .word").all_text_contents(),["import"])
                page.evaluate("t=>setT(t)",film["shots"][2]["t0"]+.2)
                self.assertEqual(page.locator("#words").inner_html(),expected)
            finally:
                browser.close();pw.stop()

    def test_named_repeated_words_keep_their_own_positions(self):
        sc = script()
        self.assertEqual(v.smd.validate(sc, L, "port"), [])
        line = sc.beats[0].lines[0]
        self.assertEqual(line.plain, "先import，再import。")
        self.assertEqual([a["start"] for a in line.anchors], [1, 9])
        cues = timeline(sc)["beats"][0]["lines"][0]["cues"]
        self.assertAlmostEqual(cues["second"] - cues["first"], 2)
        film = v.compiler.compile_film("port", L, timeline(sc), Path("."), v.WF)
        self.assertEqual([tr["at"] for tr in film["shots"][0]["tracks"]], [cues["first"], cues["second"]])

    def test_relations_cannot_be_recalled_before_teaching_or_lost_at_the_end(self):
        beats = body()
        beats[0][2]["recall"] = ["out"]
        self.assertTrue(any("尚未讲过" in e for e in v.smd.validate(script(beats), L, "port")))
        beats = body()
        beats[-1][2]["recall"] = ["in"]
        beats[-1][2]["nodes"][0]["refs"] = ["in"]
        self.assertTrue(any("结尾尚未收拢关系：out" in e for e in v.smd.validate(script(beats), L, "port")))
        beats = body()
        beats[0][2]["nodes"][0].pop("relation")
        beats[0][2]["nodes"][0]["text"] = "无关文字"
        self.assertTrue(any("对应画面元素" in e for e in v.smd.validate(script(beats), L, "port")))

    def test_invalid_json_duplicates_and_mixed_formats_report_errors(self):
        raw = script().text
        for invalid in (raw.replace('"nodes":', '"nodes": [], "nodes":', 1),
                        raw.replace('"x": 120', '"x": NaN', 1), raw.replace('```\n', '', 1),
                        raw + "\n## 旧拍 [title]\n旧内容。\n"):
            self.assertTrue(v.smd.validate(v.smd.parse(invalid), L, "port"))

    def test_malformed_fields_are_actionable_errors_instead_of_tracebacks(self):
        mutations = [lambda s: s.update(recall=[[]]), lambda s: s.update(closing="yes"),
                     lambda s: s["learn"][0].update(kind=[]), lambda s: s["nodes"][0].update(type=[]),
                     lambda s: s["nodes"][0].update(runs=["bad"]), lambda s: s["nodes"][0].update(actionAt=[]),
                     lambda s: s["events"][0].update(target=[]), lambda s: s["events"][0].update(at=[]),
                     lambda s: s["events"][0].update(ease=[]), lambda s: s["events"][0].update(to={"opacity":2}),
                     lambda s: s["nodes"][0].update(items=[None], type="illustration")]
        for mutate in mutations:
            beats = body()
            mutate(beats[0][2])
            with self.subTest(scene=beats[0][2]):
                self.assertTrue(v.smd.validate(script(beats), L, "port"))

    def test_source_word_coverage_and_numeric_claims_remain_required(self):
        beats = body()
        beats[0][2]["learn"][0]["source"] = "lesson:missing"
        self.assertTrue(any("不存在" in e for e in v.smd.validate(script(beats), L, "port")))
        raw = script().text.replace("先{first|import}，再{second|import}。", "2029 年销量增长。")
        errors = v.smd.validate(v.smd.parse(raw), L, "port")
        self.assertTrue(any("数字 2029" in e for e in errors))
        self.assertTrue(any("口播没有出现" in e for e in errors))

    def test_overlapping_tracks_and_events_after_the_shot_are_rejected(self):
        for event in (dict(target="word", at="first", duration=3, to={"x":200}),
                      dict(target="word", at=100, duration=1, to={"x":200})):
            beats = body()
            beats[0][2]["events"].append(event)
            with self.subTest(event=event), self.assertRaises(ValueError):
                v.compiler.compile_film("port", L, timeline(script(beats)), Path("."), v.WF)

    def test_compilation_is_stable_and_does_not_send_the_lesson_to_the_player(self):
        sc = script()
        first = v.compiler.compile_film("port", L, timeline(sc), Path("."), v.WF)
        second = v.compiler.compile_film("port", L, timeline(sc), Path("."), v.WF)
        self.assertEqual(first, second)
        self.assertNotIn("lesson", first)
        self.assertNotIn("portare", json.dumps(first["shots"]))
        changed = body()
        changed[0] = (changed[0][0], "这里先{first|import}，然后再{second|import}。", changed[0][2])
        later = v.compiler.compile_film("port", L, timeline(script(changed)), Path("."), v.WF)
        self.assertEqual(first["shots"][1]["id"], later["shots"][1]["id"])
        self.assertEqual(first["shots"][1]["nodes"], later["shots"][1]["nodes"])

    def test_images_are_embedded_and_cannot_escape_the_project(self):
        from PIL import Image
        with tempfile.TemporaryDirectory() as temp:
            p = Path(temp)
            Image.new("RGB", (32,32), "red").save(p / "photo.png")
            beats = body()
            beats[0][2]["nodes"].append(dict(id="photo", type="image", file="photo.png", credit="测试自制", x=100,y=420,w=400,h=400))
            self.assertEqual(v.smd.validate(script(beats), L, "port", p), [])
            film = v.compiler.compile_film("port", L, timeline(script(beats)), p, v.WF)
            self.assertTrue(next(iter(film["assets"].values())).startswith("data:image/png;base64,"))
            for ref in ("../photo.png", "D:/outside.png", "https://example.org/a.png"):
                with self.assertRaises(ValueError):
                    storyboard.local_image(p, ref)

    def test_approval_tracks_lesson_image_code_voice_and_script_changes(self):
        from PIL import Image
        with tempfile.TemporaryDirectory() as temp:
            projects = Path(temp)
            project = projects / "port"
            project.mkdir()
            Image.new("RGB", (8,8), "red").save(project / "photo.png")
            beats = body()
            beats[0][2]["nodes"].append(dict(id="photo", type="image", file="photo.png", credit="自制", x=100,y=420,w=400,h=400))
            sc = script(beats)
            (project / "script.md").write_text(sc.text, encoding="utf-8")
            args = SimpleNamespace(args=["approved"], by="用户授权 AI 审核", voice=v.VOICE, rate=v.RATE)
            with patch.object(v, "PROJECTS", projects):
                self.assertEqual(v.cmd_mark("port", L, args), 0)
                approved = v.smd.parse((project / "script.md").read_text(encoding="utf-8"))
                self.assertEqual(v.approval_gate("port", L, approved, args), [])
                changed = copy.deepcopy(L)
                changed["words"][0]["meaning"] = "进口；导入"
                self.assertTrue(any("课程" in e for e in v.approval_gate("port", changed, approved, args)))
                args.voice = "another-voice"
                self.assertTrue(any("音色" in e for e in v.approval_gate("port", L, approved, args)))
                args.voice, args.rate = v.VOICE, "+0%"
                self.assertTrue(any("语速" in e for e in v.approval_gate("port", L, approved, args)))
                args.rate = v.RATE
                Image.new("RGB", (8,8), "blue").save(project / "photo.png")
                self.assertTrue(any("图片" in e for e in v.approval_gate("port", L, approved, args)))
                code = project / "player.js"
                code.write_text("changed", encoding="utf-8")
                with patch.object(v, "PLAYER", code):
                    self.assertTrue(any("代码" in e for e in v.approval_gate("port", L, approved, args)))
                modified = v.smd.parse(approved.text.replace("同一张照片随着参照改变方向", "新主线"))
                self.assertTrue(any("脚本" in e for e in v.approval_gate("port", L, modified, args)))

    def test_browser_random_seeks_match_sequential_playback_and_audit_overlaps(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "frame.html"
            sc, tl = script(), timeline(script())
            path.write_text(v.frame_html("port", L, tl), encoding="utf-8")
            pw, browser, page = v.open_page(path)
            try:
                self.assertEqual(page.evaluate("audit()"), [])
                at = tl["beats"][0]["lines"][0]["cues"]["second"] + .25
                page.evaluate("t=>setT(t)", at)
                expected = page.evaluate("document.querySelector('.shot.on').outerHTML")
                page.evaluate("t=>setT(t)", tl["total"]-.1)
                page.evaluate("setT(0)")
                page.evaluate("t=>setT(t)", at)
                self.assertEqual(expected, page.evaluate("document.querySelector('.shot.on').outerHTML"))
                self.assertTrue(page.evaluate("!('lesson' in filmData)"))
                page.evaluate("""() => {const n=document.querySelector('.shot.on .text');const c=n.cloneNode(true);c.dataset.nodeId='overlap';n.parentElement.appendChild(c)}""")
                self.assertTrue(any("文字重叠" in issue for issue in page.evaluate("audit()")))
            finally:
                browser.close()
                pw.stop()

    def test_crop_preserves_photo_proportions_and_marker_audit_is_real(self):
        from PIL import Image
        with tempfile.TemporaryDirectory() as temp:
            folder=Path(temp)
            Image.new("RGB", (400, 200), "green").save(folder / "photo.png")
            beats=body()
            beats[0][2]["nodes"] += [dict(id="photo", type="image", file="photo.png", credit="自制", x=120,y=460,w=600,h=150,crop=[0,0,.5,1]),
                                     dict(id="arrow",type="line",x=120,y=780,w=700,h=4,arrow=True)]
            sc=script(beats)
            film=v.compiler.compile_film("port",L,timeline(sc),folder,v.WF)
            path=folder/"frame.html"
            path.write_text(v.frame_html("port",L,timeline(sc),film=film),encoding="utf-8")
            pw,browser,page=v.open_page(path)
            try:
                ratios=page.evaluate("""() => {const n=document.querySelector('.shot.on .crop-window'), i=n.querySelector('img');
                    return [n.clientWidth/n.clientHeight,i.clientWidth/i.clientHeight];}""")
                self.assertEqual(ratios,[1,2])
                self.assertEqual(page.evaluate("audit()"),[])
                page.evaluate("document.querySelectorAll('.shot.on marker').forEach(n=>n.remove())")
                self.assertTrue(any("箭头" in e for e in page.evaluate("audit()")))
            finally:
                browser.close()
                pw.stop()


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    unittest.main()
