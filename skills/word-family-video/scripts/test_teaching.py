"""教学素材、过程小结、独立版本和实际人物动画的行为验证。"""
import copy
import hashlib
import json
import math
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import video as v

smd = v.smd
_, LESSON = v.load_lesson("tract")


def script(body, keep=("extract",), seed=27):
    skip = "；".join(w["w"] for w in LESSON["words"] if w["w"] not in keep)
    return smd.parse(f"---\nlesson: tract\nspine: 从熟悉动作连接新关系\nseed: {seed}\nskip: {skip}\n---\n\n{body}")


def timeline(sc):
    marks = [{"w": w, "t": t} for w, t in (("拉", 1), ("ex", 1), ("tract", 2),
                                          ("extract", 3), ("attract", 1), ("distract", 2))]
    return v.build_timeline(sc, {}, lambda _: Path("clip.mp3"), lambda _: 6, lambda _: marks)[0]


def film(sc, lesson=LESSON):
    return v.compiler.compile_film("tract", lesson, timeline(sc), Path("."), v.WF)


def node(shot, id):
    return next(n for n in shot["nodes"] if n["id"] == id)


class TeachingTests(unittest.TestCase):
    def test_motion_metadata_rejects_invalid_paths_and_prop_targets(self):
        kinds, poses = v.wf_build.kit_names()
        good = [{"k": "fig", "id": "carrier", "x": 80, "pose": "carry",
                 "motion": {"from": [204, 108], "duration": 3.2}},
                {"k": "rect", "x": 62, "y": 12, "w": 36, "h": 18, "follow": "carrier"}]
        errors = []
        v.wf_build.check_scene(good, "搬运", kinds, poses, errors)
        self.assertEqual(errors, [])
        invalid = []
        for start in (None, [204], [True, 108], [math.inf, 108]):
            case = copy.deepcopy(good)
            case[0]["motion"]["from"] = start
            invalid.append(case)
        for duration in (0, -1, True, math.nan):
            case = copy.deepcopy(good)
            case[0]["motion"]["duration"] = duration
            invalid.append(case)
        missing = copy.deepcopy(good)
        missing[1]["follow"] = "absent"
        invalid.append(missing)
        invalid.append(good + [copy.deepcopy(good[0])])
        for field, value in (("id", ""), ("id", 0), ("x", None), ("y", math.inf), ("follow", "carrier")):
            case = copy.deepcopy(good)
            case[0][field] = value
            invalid.append(case)
        for case in invalid:
            with self.subTest(case=case):
                errors = []
                v.wf_build.check_scene(case, "搬运", kinds, poses, errors)
                self.assertTrue(errors)

    def test_optional_materials_and_required_contrast_evidence(self):
        old = copy.deepcopy(LESSON)
        old.pop("teaching", None)
        self.assertEqual(v.wf_build.validate(old, *v.wf_build.kit_names())[0], [])
        good = copy.deepcopy(LESSON)
        good["teaching"] = {"known": ["手里的绳子"], "discovery": "言论也能拉回",
                            "contrasts": [{"a": "tract", "b": "track", "distinction": "形近",
                                           "fact": "已核对各自词条", "source": "etymonline"}]}
        self.assertEqual(v.wf_build.validate(good, *v.wf_build.kit_names())[0], [])
        del good["teaching"]["contrasts"][0]["fact"]
        self.assertTrue(any("contrasts" in e for e in v.wf_build.validate(good, *v.wf_build.kit_names())[0]))

    def test_pair_can_teach_and_recap_cannot_teach_new_words(self):
        sc = script("## 一股力与两股力 [pair: attract | distract]\n"
                    "{attract} 把目光拉到一处。\n{distract} 把注意力拉向几处。\n"
                    "## 同一条关系 [recap: attract | distract]\n"
                    "一个方向与几个方向，拉的动作没变。\n", keep=("attract", "distract"))
        self.assertEqual(smd.validate(sc, LESSON, "tract"), [])
        tl = timeline(sc)
        self.assertEqual(tl["words"], ["attract", "distract"])
        data = film(sc)
        summary = node(data["shots"][1], "summary")["children"]
        self.assertEqual([x["text"] for x in summary if x["id"].startswith("word-")], ["attract", "distract"])
        self.assertNotIn("extract", json.dumps(summary))
        bad = script("## 提前总结 [recap: extract]\n还没讲这个词。\n", keep=("extract",))
        self.assertTrue(any("尚未讲清" in e for e in smd.validate(bad, LESSON, "tract")))
        self.assertTrue(any("skip" in e for e in smd.validate(bad, LESSON, "tract")))

    def test_question_and_repeated_or_foreign_recap_do_not_count(self):
        sc = script("## 问题 [pair: attract | distract]\n为什么 attract 与 distract 不同？\n"
                    "## 小结 [recap: attract | attract]\n拉的方向不同。\n", keep=("attract", "distract"))
        errors = smd.validate(sc, LESSON, "tract")
        self.assertTrue(any("不同的已讲词" in e for e in errors))
        self.assertTrue(any("skip" in e for e in errors))
        bad = script("## 已知 [word: extract]\n{extract}，拉出来。\n"
                     "## 混进另一家 [recap: extract | captain]\n两家。\n")
        self.assertTrue(any("captain" in e and "主线" in e for e in smd.validate(bad, LESSON, "tract")))

    def test_visual_choices_are_repeatable_and_explicit_camera_wins(self):
        body = ("## 拉 [scene: extract]\n从土里往外拉。\n"
                "## 词 [word: extract]\n> 镜头：左图\n{extract}，拉出来。\n"
                "## 收拢 [recap: extract]\n拉出来，接回同一动作。\n")
        sc = script(body)
        self.assertEqual(smd.validate(sc, LESSON, "tract"), [])
        tl = timeline(sc)
        first = film(sc)
        self.assertEqual(first, film(sc))
        self.assertLess(node(first["shots"][1], "drawing")["x"], node(first["shots"][1], "word")["x"])
        self.assertTrue(all(n.get("rotation", 0) == 0 for shot in first["shots"] for n in shot["nodes"]))
        approved = smd.parse(smd.mark(sc.text, "approved", "测试授权"))
        self.assertEqual(smd.visual_options(sc), smd.visual_options(approved))
        big = film(script("## 词 [word: extract]\n> 镜头：大字\n{extract}。\n"))
        self.assertFalse(any(n["type"] == "illustration" for n in big["shots"][0]["nodes"]))

    def test_invalid_controls_and_action_cue(self):
        bad = script("## 拉 [scene: extract]\n> 镜头：随机乱选\n> 动作：跳舞\n> 动作点：拉\n从土里拿出来。\n"
                     "## 词 [word: extract]\n{extract}。\n")
        errors = smd.validate(bad, LESSON, "tract")
        self.assertTrue(any("镜头" in e for e in errors))
        self.assertTrue(any("动作" in e for e in errors))
        self.assertTrue(any("动作点" in e for e in errors))
        good = script("## 拉 [scene: extract]\n> 动作点：拉\n从土里{拉}出来。\n"
                      "## 词 [word: extract]\n{extract}。\n")
        self.assertEqual(smd.validate(good, LESSON, "tract"), [])
        self.assertFalse(any("不会触发" in w for w in smd.lint(good)))
        self.assertEqual(node(film(good)["shots"][0], "drawing")["actionAt"], 1.95)

    def test_direct_word_changes_scene_and_explicit_carry_is_preserved(self):
        body = "## 一个词 [word: extract]\n{extract}，拉出。\n## 另一个词 [word: retract]\nretract，拉回。\n"
        plans = film(script(body, keep=("extract", "retract")))["shots"]
        self.assertNotEqual(node(plans[0], "drawing")["items"], node(plans[1], "drawing")["items"])
        shared = body.replace("retract，拉回。", "> 画面：沿用\nretract，拉回。")
        plans = film(script(shared, keep=("extract", "retract")))["shots"]
        self.assertEqual(node(plans[0], "drawing")["items"], node(plans[1], "drawing")["items"])
        self.assertEqual(node(plans[0], "drawing")["actionAt"], node(plans[1], "drawing")["actionAt"])
        big = body.replace("{extract}，拉出。", "> 镜头：大字\n{extract}，拉出。")
        plans = film(script(big, keep=("extract", "retract")))["shots"]
        self.assertFalse(any(n["type"] == "illustration" for n in plans[0]["nodes"]))
        self.assertTrue(any(n["type"] == "illustration" for n in plans[1]["nodes"]))

    def test_explicit_senses_follow_current_branch_and_default_stays_complete(self):
        body = "## 词 [word: extract]\n{extract}，拉出来。\n"
        full = node(film(script(body))["shots"][0], "meaning")["text"]
        selected = node(film(script(body.replace("{extract}", "> 释义：v. 拔出\n{extract}", 1)))["shots"][0], "meaning")["text"]
        self.assertIn("摘录", full)
        self.assertEqual(selected, "v. 拔出")
        pair = script("## 一对 [pair: attract | distract]\n> 释义：attract = v. 吸引\n"
                      "attract 把目光拉过来，distract 把注意力拉开。\n", keep=("attract", "distract"))
        self.assertEqual(node(film(pair)["shots"][0], "meaning-0")["text"], "v. 吸引")

    def test_contrast_words_are_not_claimed_as_family_members(self):
        sc = script("## 对照 [pair: extract | captain]\n> 释义：captain = 队长\n"
                    "extract 是拉出来；captain 是队长。\n", keep=("extract",))
        self.assertEqual(smd.validate(sc, LESSON, "tract"), [])
        data = film(sc)
        self.assertEqual([r["label"] for r in data["provenance"]["relations"].values()], ["extract"])
        self.assertEqual([node(data["shots"][0], f"word-{i}")["text"] for i in (0, 1)], ["extract", "captain"])

    def test_named_project_keeps_source_lesson_and_blocks_paths(self):
        with tempfile.TemporaryDirectory(prefix="wf-teaching-") as temp:
            projects = Path(temp)
            target = projects / "rope-version"
            target.mkdir()
            (target / "script.md").write_text(script("## 词 [word: extract]\n{extract}。\n").text, encoding="utf-8")
            with patch.object(v, "PROJECTS", projects):
                self.assertEqual(v.load_script("rope-version", LESSON, "tract")[1], [])
                calls = []
                with patch.object(sys, "argv", ["video.py", "plan", "tract", "--project", "rope-version"]), \
                     patch.object(v, "cmd_plan_script", side_effect=lambda name, lesson, args: calls.append((name, args.lesson_stem)) or 0):
                    self.assertEqual(v.main(), 0)
                self.assertEqual(calls, [("rope-version", "tract")])
                with patch.object(sys, "argv", ["video.py", "plan", "tract", "--project", "../escape"]):
                    with self.assertRaises(SystemExit) as exc:
                        v.main()
                    self.assertEqual(exc.exception.code, 2)

    def test_named_project_review_followup_records_in_the_same_project(self):
        with tempfile.TemporaryDirectory(prefix="wf-review-") as temp:
            project = Path(temp) / "rope-version"
            project.mkdir()
            (project / "script.md").write_text(script("## 词 [word: extract]\n{extract}。\n").text, encoding="utf-8")
            args = SimpleNamespace(lesson="tract", lesson_stem="tract", record=False)
            with patch.object(v, "PROJECTS", Path(temp)):
                self.assertEqual(v.cmd_review("rope-version", LESSON, args), 0)
                raw = project / "build" / "review_raw.md"
                raw.write_text("1. 保持当前词源解释。", encoding="utf-8")
                with patch.object(sys, "argv", ["video.py", *v.review_record_args("rope-version", args)]):
                    self.assertEqual(v.main(), 0)
                self.assertTrue((project / "review.md").exists())
                self.assertFalse(raw.exists())
                self.assertFalse((Path(temp) / "tract").exists())

    def test_browser_joint_motion_contact_and_seek(self):
        sc = script("## 拉出来 [scene: extract]\n> 动作：明显\n> 动作点：拉\n从土里{拉}出来。\n"
                    "## 一句话 [word: extract]\n> 镜头：左图\n{ex} 往外，{tract} 拉，合起来 {extract}。\n"
                    "## 收拢 [recap: extract]\n> 版式：分支\n这个方向接回拉的动作。\n")
        tl = timeline(sc)
        with tempfile.TemporaryDirectory(prefix="wf-teaching-") as temp:
            path = Path(temp) / "frame.html"
            path.write_text(v.frame_html("tract", LESSON, tl), encoding="utf-8")
            pw, browser, page = v.open_page(path)
            try:
                start = page.evaluate("DATA.shots[0].nodes.find(n => n.type === 'illustration').actionAt")
                def joints(at):
                    page.evaluate("t => setT(t)", at)
                    return page.evaluate("""() => [...document.querySelector('.shot.on').querySelectorAll('[data-part=arm1], [data-part=leg0]')].map(e => e.getAttribute('d'))""")
                before, mid = joints(start), joints(start + 1.2)
                self.assertNotEqual(before, mid)
                self.assertTrue(page.evaluate("""() => [...document.querySelector('.shot.on').querySelectorAll('[data-rope]')].every(r => {
                    const p = r.parentElement.dataset.hand.split(',').map(Number);
                    return Math.abs(+r.getAttribute('x1')-p[0]) < .001 && Math.abs(+r.getAttribute('y1')-p[1]) < .001;
                })"""))
                later = start + 1.8
                page.evaluate("t => setT(t)", later)
                image = hashlib.sha256(page.screenshot()).hexdigest()
                page.evaluate("setT(0)")
                page.evaluate("t => setT(t)", later)
                self.assertEqual(image, hashlib.sha256(page.screenshot()).hexdigest())
                for pose in ("pull", "push", "carry", "walk", "give", "think"):
                    data = page.evaluate("""pose => [0,.5,1].map(q => VIDEO_ACTORS.frame({x:140, pose, rope:[220,80], flip:1, s:.8}, q, 1.3))""", pose)
                    self.assertNotEqual(data[0]["a"], data[1]["a"])
                    self.assertTrue(all(abs(f["l"][i][2][1]) < .001 for f in (data[0], data[2]) for i in range(2)))
                for beat in page.evaluate("DATA.shots.map(b => ({t0:b.t0,t1:b.t1}))"):
                    page.evaluate("t => setT(t)", beat["t1"] - .5)
                    self.assertEqual(page.evaluate("audit()"), [])
            finally:
                browser.close()
                pw.stop()

    def test_browser_moving_actor_steps_with_prop_and_stops(self):
        lesson = copy.deepcopy(v.load_lesson("port")[1])
        actor = next(x for x in lesson["words"] if x["w"] == "import")["scene"]
        carrier = next(x for x in actor if x.get("id") == "carrier")
        # 高低不同的起终位也必须使用实际手的位置，不能只在水平搬运时碰巧对齐。
        carrier["motion"]["from"][1] = 92
        carrier["rope"] = [250, 82]
        sc = smd.parse("---\nlesson: port\nspine: 随箱子走进仓库\n---\n\n"
                       "## 搬进去 [scene: import]\n箱子从外面搬进仓库。\n"
                       "## 名字 [word: import]\n{import}。\n")
        with tempfile.TemporaryDirectory(prefix="wf-motion-") as temp:
            path = Path(temp) / "frame.html"
            path.write_text(v.frame_html("port", lesson, timeline(sc)), encoding="utf-8")
            pw, browser, page = v.open_page(path)
            try:
                data = page.evaluate("""() => {
                    const b = DATA.shots[0], drawing=b.nodes.find(n => n.type === 'illustration'), o=drawing.items.find(x => x.motion);
                    const rows = [];
                    for (let i = 0; i <= 32; i++) {
                        const q = i / 32, at = drawing.actionAt + q * o.motion.duration;
                        setT(at);
                        const sec = document.querySelector('.shot.on'), group = [...sec.querySelectorAll('[data-actor]')].find(g => JSON.parse(g.dataset.actor).id === o.id);
                        const p = VIDEO_ACTORS.frame(o, q), mat = group.querySelector('[data-body]').transform.baseVal.consolidate().matrix;
                        const actual = new DOMPoint(...p.a[1][2]).matrixTransform(mat);
                        const box = sec.querySelector('[data-follow]'), bm = box.transform.baseVal.consolidate().matrix;
                        const prop = new DOMPoint(80, 30).matrixTransform(bm);
                        const rope = group.querySelector('[data-rope]');
                        rows.push({q, origin:p.origin, hand:[actual.x,actual.y], recorded:group.dataset.hand.split(',').map(Number),
                                   rope:[+rope.getAttribute('x1'),+rope.getAttribute('y1')], prop:[prop.x,prop.y],
                                   feet:p.l.map(l => [p.origin[0]+p.dir*l[2][0]*p.s,p.origin[1]+l[2][1]*p.s])});
                    }
                    const at = drawing.actionAt + o.motion.duration / 2;
                    setT(at);
                    const cam = document.querySelector('.shot.on .cam');
                    const moving = VIDEO_ACTORS.update(cam, at + .01);
                    setT(drawing.actionAt + o.motion.duration + .1);
                    const settled = VIDEO_ACTORS.update(cam, drawing.actionAt + o.motion.duration + .2);
                    const held = VIDEO_ACTORS.frame(o, 1);
                    return {rows, held, after:VIDEO_ACTORS.frame(o, 5), moving, settled};
                }""")
                rows = data["rows"]
                self.assertEqual(rows[0]["origin"], [204, 92])
                self.assertEqual(rows[-1]["origin"], [80, 108])
                self.assertTrue(all(a["origin"][0] > b["origin"][0] for a, b in zip(rows, rows[1:])))
                for row in rows:
                    self.assertLess(math.dist(row["hand"], row["recorded"]), .005)
                    self.assertLess(math.dist(row["hand"], row["rope"]), .005)
                    self.assertLess(abs(row["hand"][1] - row["prop"][1]), .005)
                    self.assertLess(abs(row["hand"][0] - row["prop"][0]), 18)
                self.assertTrue(any(row["origin"][1] - min(foot[1] for foot in row["feet"]) > 2 for row in rows))
                planted = any(abs(a["feet"][i][0] - b["feet"][i][0]) < .005
                              and abs(a["feet"][i][1] - a["origin"][1]) < .005
                              and abs(b["feet"][i][1] - b["origin"][1]) < .005
                              for a, b in zip(rows, rows[1:]) for i in range(2))
                self.assertTrue(planted)
                self.assertTrue(data["moving"])
                self.assertFalse(data["settled"])
                self.assertEqual(data["held"], data["after"])
                at = page.evaluate("DATA.shots[0].nodes.find(n => n.type === 'illustration').actionAt + 1.6")
                page.evaluate("t => setT(t)", at)
                # GPU 抗锯齿会让少数边缘像素相差 1 级；严格比较实际坐标、样式和可见内容。
                first = page.evaluate("document.documentElement.outerHTML")
                page.evaluate("setT(0)")
                page.evaluate("t => setT(t)", at)
                self.assertEqual(first, page.evaluate("document.documentElement.outerHTML"))
            finally:
                browser.close()
                pw.stop()


if __name__ == "__main__":
    unittest.main()
