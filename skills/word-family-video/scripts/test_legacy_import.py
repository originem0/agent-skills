"""旧稿沿用同一编译器：保留义项、例句、触发和家族边界，不保留旧模板的倾斜规则。"""
import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parent))
import video as v
from legacy_import import example_runs


def timeline(text):
    sc=v.smd.parse(text)
    marks=[{"w":"suspend","t":2},{"w":"suspended","t":2},{"w":"from","t":3},{"w":"school","t":4},{"w":"pending","t":4}]
    return v.build_timeline(sc,{},lambda _:Path("clip.mp3"),lambda _:6,lambda _:marks)[0]


class LegacyImportTests(unittest.TestCase):
    def test_senses_examples_and_explicit_suppression_survive_import(self):
        lesson=copy.deepcopy(v.load_lesson("pend")[1])
        word=next(w for w in lesson["words"] if w["w"]=="suspend")
        word["meaning"]="v. 悬挂；暂停；停学"
        word["ex"]=["suspended from school","被停学"]
        text="---\nlesson: pend\nspine: 挂与暂停\n---\n## 停学 [word: suspend]\n{suspend}，暂停。\n"
        def nodes(raw):
            film=v.compiler.compile_film("pend",lesson,timeline(raw),Path("."),v.WF)
            return {n["id"]:n for n in film["shots"][0]["nodes"]}
        full=nodes(text)
        self.assertIn("停学",full["meaning"]["text"])
        self.assertEqual(full["translation"]["text"],"被停学")
        self.assertEqual("".join(r["text"] for r in full["example"]["runs"]),"suspended from school")
        selected=nodes(text.replace("{suspend}","> 释义：v. 暂停\n> 例句：-\n{suspend}",1))
        self.assertEqual(selected["meaning"]["text"],"v. 暂停")
        self.assertNotIn("example",selected)

    def test_example_highlight_includes_inflected_word_without_changing_it(self):
        for word,sentence,expected in (("receive","received a gift","received"),("distract","distracting noise","distracting")):
            runs=example_runs(sentence,word)
            self.assertEqual("".join(r["text"] for r in runs),sentence)
            self.assertEqual(next(r["text"] for r in runs if r["color"]=="root"),expected)

    def test_quiz_reveals_answer_at_its_cue_and_does_not_leak_it_in_formula(self):
        lesson=v.load_lesson("pend")[1]
        text="---\nlesson: pend\nspine: 挂着\n---\n## 留个悬念 [quiz]\n{pending}，还悬着。\n"
        tl=timeline(text)
        film=v.compiler.compile_film("pend",lesson,tl,Path("."),v.WF)
        nodes={n["id"]:n for n in film["shots"][0]["nodes"]}
        self.assertNotIn("pending",nodes["formula"]["text"])
        self.assertEqual(nodes["answer"]["opacity"],0)
        at=next(t["at"] for t in film["shots"][0]["tracks"] if t["target"]=="answer")
        self.assertEqual(at,tl["beats"][0]["lines"][0]["cues"]["pending"])

    def test_legacy_finale_uses_taught_words_instead_of_entire_course(self):
        lesson=v.load_lesson("capit")[1]
        text="---\nlesson: capit\nspine: 财产的一支\n---\n## 牛 [word: cattle]\ncattle 是牛。\n## 一家 [map]\n财产变成牲畜，再收窄。\n"
        film=v.compiler.compile_film("capit",lesson,timeline(text),Path("."),v.WF)
        summary=film["shots"][-1]["nodes"][0]
        labels=[n["text"] for n in summary["children"] if n["id"].startswith("word-")]
        self.assertEqual(labels,["cattle"])
        detail=next(n["text"] for n in summary["children"] if n["id"]=="detail-0")
        self.assertEqual(detail,v.smd.lesson_words(lesson)["cattle"]["literal"])
        self.assertNotIn("handkerchief",json.dumps(film,ensure_ascii=False))
        self.assertEqual(film["shots"][0]["navigation"],{"words":["cattle"],"active":["cattle"]})
        self.assertEqual(film["shots"][-1]["navigation"],{"words":["cattle"],"active":["cattle"]})

    def test_legacy_word_revisit_does_not_leave_navigation_at_the_last_new_word(self):
        lesson=v.load_lesson("pend")[1]
        text="---\nlesson: pend\nspine: 回到挂\n---\n## 依靠 [word: depend]\ndepend。\n## 暂停 [word: suspend]\nsuspend。\n## 回到依靠 [word: depend]\ndepend。\n"
        film=v.compiler.compile_film("pend",lesson,timeline(text),Path("."),v.WF)
        self.assertEqual(film["shots"][0]["navigation"]["words"],["depend"])
        self.assertEqual(film["shots"][-1]["navigation"],{"words":["depend","suspend"],"active":["depend"]})

    def test_real_legacy_projects_compile_without_modifying_their_scripts(self):
        for project,lesson_name in (("capit","capit"),("port-cables","port"),("tract","tract")):
            with self.subTest(project=project):
                folder=v.PROJECTS/project
                path=folder/"script.md"
                before=path.read_bytes()
                lesson=v.load_lesson(lesson_name)[1]
                film=v.compiler.compile_film(project,lesson,timeline(before.decode("utf-8")),folder,v.WF)
                self.assertFalse(film["provenance"]["native"])
                self.assertNotIn("lesson",film)
                self.assertTrue(all(s["nodes"] for s in film["shots"]))
                self.assertEqual(before,path.read_bytes())


if __name__=="__main__":
    unittest.main()
