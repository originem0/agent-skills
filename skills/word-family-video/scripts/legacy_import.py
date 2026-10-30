"""旧画面块的单向导入。输出普通分镜节点，播放器不再维护第二套布局规则。

旧稿缺少明确构图，导入采用保守的静态排布，并保留作者指定的画面、义项和触发。
新的讲解应直接写 shot；不从中文释义推断动作，不替作者编造词源关系。
"""
import copy
import re

import script_md as smd
from scene_compile import text_node


def clean(text):
    return re.sub(r"<[^>]+>", "", text or "").strip()


def example_runs(text, word=""):
    if "{" in text:
        return [{"text": s.strip("{}"), "color": "root" if s.startswith("{") else "ink"}
                for s in re.split(r"(\{[^{}]+\})", text) if s]
    # 沿用已有词形高亮，不能把截断后的词干显示成另一个词。
    base = word[:-1] if len(word) > 4 and word[-1] in "eyt" else word
    match = re.search(rf"(?<![A-Za-z]){re.escape(base)}[A-Za-z]*", text, re.I) if base else None
    if not match:
        return [{"text": text, "color": "ink"}]
    return [{"text": s, "color": c} for s, c in
            ((text[:match.start()], "ink"), (match[0], "root"), (text[match.end():], "ink")) if s]


def import_beats(stem, lesson, timeline, project_dir, wf_dir):
    words, out, taught, relations = smd.lesson_words(lesson), [], {}, {}
    previous_visual = None
    for index, beat in enumerate(timeline["beats"]):
        b = copy.deepcopy(beat)
        data = {}
        for key, value in b.get("data", []):
            data.setdefault(key, value)
        block, arg = b["block"], b.get("arg", "").strip()
        cues = {c.lower(): t for row in b["lines"] for c, t in row["cues"].items()}
        start = b["lines"][0]["s"] if b["lines"] else b["t0"]
        nodes, events, learned = [], [], []

        def reveal(node, at):
            node["opacity"] = 0
            nodes.append(node)
            events.append(dict(target=node["id"], at=max(0, min(at, b["t1"] - .35) - b["t0"]),
                               duration=.25, to={"opacity": 1}))

        def remember(word, meaning, detail=None):
            key = word.lower()
            if key not in relations:
                rid = "imported-" + re.sub(r"[^a-z0-9-]", "-", key)
                rel = dict(id=rid, kind="usage", label=word, detail=detail or meaning,
                           source="legacy-script", words=[word])
                learned.append(rel)
                relations[key] = rel
            taught[key] = relations[key]["id"]

        def illustration(ref, x, y, w, h):
            nonlocal previous_visual
            if ref == "沿用" and previous_visual:
                node = copy.deepcopy(previous_visual[0])
                node.update(x=x, y=y, w=w, h=h)
                node["actionAt"] = previous_visual[1] - b["t0"]
            else:
                source = lesson.get(ref) if ref in ("opening", "anchor", "finale") else words.get(ref.lower())
                if not source or not source.get("scene"):
                    return
                node = dict(id="drawing", type="illustration", ref=ref, x=x, y=y, w=w, h=h,
                            actionAt=cues.get(data.get("动作点", "").strip("{} ").lower(), start) - b["t0"],
                            actLevel=data.get("动作", "正常"))
            nodes.append(node)
            previous_visual = (copy.deepcopy(node), b["t0"] + node["actionAt"])

        if block == "word":
            word = words.get(arg.lower(), {})
            meaning = clean(data.get("释义") or word.get("meaning", ""))
            camera = data.get("镜头", "右图")
            left = 1010 if camera == "左图" else 120
            width = 790 if camera != "大字" else 1680
            whole = cues.get(arg.lower(), start)
            split = word.get("split", [])
            runs = [{"text": part, "color": c} for part, c in zip(split, ("prefix", "root", "suffix")) if part]
            title = text_node("word", arg, left, 205, width, 150, min(104, width / max(len(arg) * .58, 1)), font="en", color="root")
            if runs and "".join(split).lower() == arg.lower():
                title["runs"] = runs
            nodes.append(title)
            reveal(text_node("meaning", meaning, left, 385, width, 115, 38), whole)
            parts = list(map(smd.norm_part, word.get("parts", [])))
            if parts:
                for i, part in enumerate(parts):
                    pwidth = width / len(parts)
                    text = f"{part['m']}  {part.get('cn', '')}"
                    if part.get("of"):
                        text += f"\n{part['of']} 的{part.get('how') or '变体'}"
                    at = cues.get(part["m"].strip("-").lower(), cues.get((part.get("of") or "").strip("-").lower(), start))
                    reveal(text_node(f"part-{i}", text, left + i * pwidth, 530, pwidth - 20, 100, 27,
                                     color={"p":"prefix", "r":"root", "s":"muted"}[part["kind"]]), at)
            if camera != "大字":
                illustration(data.get("画面", arg), 100 if camera == "左图" else 980, 275, 840, 450)
            remember(arg, meaning, clean(data.get("释义") or word.get("literal", "")))
            example = data.get("例句")
            zh = ""
            if example is None and word.get("ex"):
                example = word["ex"][0]
                zh = word["ex"][1] if len(word["ex"]) > 1 else ""
            if example and example not in ("-", "无"):
                at = b.get("example_at", whole + .6)
                reveal(text_node("example", "", left, 720, width, 74, 36, font="en",
                                 runs=example_runs(example, arg)), at)
                if zh:
                    reveal(text_node("translation", zh, left, 805, width, 65, 27, color="muted"), at)
        elif block == "scene":
            illustration(arg, 140, 185, 1640, 640)
        elif block == "photo":
            photo = lesson.get("opening", {}).get("photo", {})
            node = dict(id="photo", type="image", x=130, y=150, w=1660, h=700, fit="contain",
                        credit=data.get("署名") or photo.get("credit", ""))
            if arg == "opening":
                node["path"] = str(wf_dir / "lessons" / photo["file"])
            else:
                node["file"] = arg
            nodes.append(node)
        elif block == "pair":
            given = {value.partition("=")[0].strip().lower(): value.partition("=")[2].strip()
                     for key, value in b.get("data", []) if key == "释义"}
            for i, word in enumerate(arg.split("|")):
                word = word.strip()
                meaning = clean(given.get(word.lower()) or words.get(word.lower(), {}).get("meaning", ""))
                x, at = 120 + i * 900, cues.get(word.lower(), start)
                nodes.append(text_node(f"word-{i}", word, x, 295, 780, 160, min(110, 1250 / max(len(word), 1)), font="en", color="root"))
                reveal(text_node(f"meaning-{i}", meaning, x, 490, 780, 180, 39), at)
                if word.lower() in words and word.lower() in smd.explained_pair_words(arg, b["lines"]):
                    remember(word, meaning, clean(given.get(word.lower()) or words[word.lower()].get("literal", "")))
            nodes.append(dict(id="divider", type="line", x=960, y=255, w=1, h=485,
                              points=[[0,0],[0,485]], stroke="rule"))
        elif block in ("recap", "map"):
            refs = [taught[w.strip().lower()] for w in arg.split("|") if w.strip().lower() in taught] if block == "recap" else list(taught.values())
            if refs:
                nodes.append(dict(id="summary", type="summary", x=120, y=180, w=1680, h=690,
                                  refs=refs, layout="branches" if len(refs) > 4 else "columns",
                                  heading=f"{lesson['root']['m']} · {lesson['root']['cn']}"))
        elif block == "event":
            nodes += [text_node("event", data.get("事件", b["title"]), 140, 180, 1640, 120, 54, color="muted"),
                      text_node("quote", "", 140, 365, 1640, 380, 64, font="en", runs=example_runs(data.get("原文", "")))]
        elif block == "quiz":
            qs = lesson.get("transfer", [])
            chosen = next((q for q in qs if q[0].split("=")[0].strip().lower() in cues), qs[0] if qs else None)
            if chosen:
                word, _, formula = chosen[0].partition("=")
                at = cues.get(word.strip().lower(), b["lines"][-1]["s"] if b["lines"] else start)
                nodes.append(text_node("formula", formula.strip(), 160, 230, 1600, 180, 100, font="en", color="root"))
                reveal(text_node("answer", word.strip(), 160, 445, 1600, 160, 112, font="en", color="root"), at)
                reveal(text_node("meaning", clean(chosen[1]), 160, 675, 1600, 145, 46), at)
        if block in ("scene", "photo") and data.get("例句") not in (None, "-", "无"):
            for node in nodes:
                node["h"] = min(node["h"], 600)
            nodes.append(text_node("example", "", 140, 815, 1640, 80, 40, font="en", align="center", runs=example_runs(data["例句"])))
        if not nodes:
            nodes.append(text_node("title", b["title"], 140, 365, 1640, 240, 92, color="root"))
        if block == "word":
            focus = [arg.lower()]
        elif block in ("pair", "recap"):
            focus = [w.strip().lower() for w in arg.split("|") if w.strip().lower() in taught]
        elif block == "map":
            focus = list(taught)
        elif block == "scene":
            focus = [arg.lower()] if arg.lower() in taught else []
        elif block == "photo":
            # 例句是作者明确指定的关联；不从照片内容或中文解说猜当前词。
            example = data.get("例句", "")
            focus = [word for word in taught if re.search(rf"(?<![A-Za-z]){re.escape(word)}(?![A-Za-z])", example, re.I)]
        else:
            focus = []
        b["scene"] = dict(nodes=nodes, events=events, learn=learned, focus=focus)
        out.append(b)
    return out
