"""把分镜和已测量的语音时间编译成自足画面；浏览器不接收课程或教学规则。"""
import base64
import copy
import hashlib
import mimetypes
from pathlib import Path

from storyboard import local_image, number

VERSION = 2
COLORS = {"ink": "#24343c", "muted": "#677981", "faint": "#aebabe", "rule": "#cbd5d5",
          "root": "#356857", "prefix": "#38667f", "suffix": "#76868d", "paper": "#f6f8f7",
          "green": "#e6eee9", "blue": "#e6eef3", "accent": "#9a653b", "white": "#ffffff"}

# 只改共享零件的色值，不把网页的排版与词表带入视频。
PALETTE = {"#1e242b": COLORS["ink"], "#b84a14": COLORS["prefix"], "#176b4d": COLORS["root"],
           "#2b5c8f": COLORS["prefix"], "#9aa0a8": COLORS["faint"], "#5e6670": COLORS["muted"],
           "#6b717a": COLORS["muted"], "#e7f3ee": COLORS["green"], "#fdf0e6": COLORS["blue"],
           "#d6d0c4": COLORS["rule"], "#efe9de": COLORS["paper"], "#8a6a4a": COLORS["muted"],
           "#f1ddd6": COLORS["blue"]}


def map_colors(value):
    if isinstance(value, str):
        for old, new in PALETTE.items():
            value = value.replace(old, new)
        return value
    if isinstance(value, list):
        return [map_colors(x) for x in value]
    if isinstance(value, dict):
        return {k: map_colors(v) for k, v in value.items()}
    return value


def color(value):
    return COLORS.get(value, value)


def text_node(id, text, x, y, w, h, size=52, **kwargs):
    return dict(id=id, type="text", text=text, x=x, y=y, w=w, h=h, size=size, **kwargs)


def summary_nodes(node, relations):
    """排布由作者选择；这里展开已点名的关系，不从整课词表补词或推断词源。"""
    refs, width, height = node["refs"], node["w"], node["h"]
    cols = 3 if node.get("layout") == "branches" else 2
    cols = min(cols, len(refs))
    rows = (len(refs) + cols - 1) // cols
    heading = 100 if node.get("heading") else 0
    gap, cell_w, cell_h = 72, (width - (cols - 1) * 72) / cols, (height - heading) / rows
    children = []
    if heading:
        children.append(text_node("heading", node["heading"], 0, 0, width, 90, 64, color="root"))
    for i, ref in enumerate(refs):
        r, x, y = relations[ref], (i % cols) * (cell_w + gap), heading + (i // cols) * cell_h
        children += [dict(id=f"rule-{i}", type="shape", shape="rect", x=x, y=y + 9, w=4, h=cell_h - 28,
                          fill="accent" if r["kind"] == "contrast" else "root", radius=1),
                     text_node(f"word-{i}", r["label"], x + 24, y, cell_w - 24, min(70, cell_h * .45),
                               min(52, (cell_w - 24) / max(len(r["label"]) * .57, 1)),
                               font="en", color="accent" if r["kind"] == "contrast" else "root"),
                     text_node(f"detail-{i}", r["detail"], x + 24, y + min(74, cell_h * .46), cell_w - 24,
                               max(42, cell_h * .48 - 12), 30, color="ink")]
    return dict(node, type="group", children=children)


def compile_film(stem, lesson, timeline, project_dir, wf_dir):
    assets, asset_paths, shots, relations = {}, {}, [], {}
    navigation_words = {}
    words = {w["w"].lower(): w for w in lesson.get("words", []) + ([lesson["finale"]] if lesson.get("finale") else [])}

    def asset(path):
        path = Path(path).resolve()
        raw = path.read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        key = "a" + digest[:20]
        if key not in assets:
            mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
            assets[key] = "data:" + mime + ";base64," + base64.b64encode(raw).decode("ascii")
        asset_paths[str(path)] = digest
        return key

    def resolve_time(ref, beat, cues):
        if number(ref):
            return beat["t0"] + ref
        if ref not in cues:
            raise ValueError(f"镜头 {beat['arg']} 找不到语音触发点 {ref}")
        return cues[ref]

    def resolve_node(raw, beat, cues, trusted=False):
        node = copy.deepcopy(raw)
        if node.get("relation") and not node.get("text"):
            node["text"] = relations[node["relation"]][node.get("field", "label")]
        typ = node["type"]
        if typ == "summary":
            node = summary_nodes(node, relations)
        elif typ == "image":
            path = Path(node.pop("path")) if trusted and "path" in node else local_image(project_dir, node.pop("file"))
            node["asset"] = asset(path)
        elif typ == "illustration":
            if node.get("ref"):
                ref = node.pop("ref")
                source = lesson.get(ref) if ref in ("anchor", "opening", "finale") else words.get(ref.lower())
                if not source or not source.get("scene"):
                    raise ValueError(f"镜头 {beat['arg']} 没有课程线稿 {ref}")
                node["items"] = copy.deepcopy(source["scene"])
            node["items"] = map_colors(node["items"])
            node["actionAt"] = round(resolve_time(node.get("actionAt", 0), beat, cues), 3)
            node.setdefault("actLevel", "静止")
        for k in ("color", "fill", "stroke"):
            if k in node:
                node[k] = color(node[k])
        for run in node.get("runs", []):
            if run.get("color"):
                run["color"] = color(run["color"])
        if node.get("children"):
            node["children"] = [resolve_node(child, beat, cues, trusted) for child in node["children"]]
        for k in ("relation", "field", "refs", "layout", "heading"):
            node.pop(k, None)
        return node

    native = all(b["block"] == "shot" for b in timeline["beats"])
    if not native:
        from legacy_import import import_beats
        source_beats = import_beats(stem, lesson, timeline, project_dir, wf_dir)
    else:
        source_beats = timeline["beats"]
    for index, b in enumerate(source_beats):
        s = b["scene"]
        relations.update({r["id"]: r for r in s.get("learn", [])})
        # 导航依据本片的实际讲解记录，不把课程的整张词表提前暴露给观众。
        introduced = [w for r in s.get("learn", []) if r.get("kind") != "contrast" for w in r.get("words", [])]
        for word in introduced:
            navigation_words.setdefault(word.lower(), word)
        recalled = [w for ref in s.get("recall", []) for w in relations[ref].get("words", [])]
        focus = s.get("focus", introduced or recalled)
        navigation = dict(words=list(navigation_words.values()),
                          active=list(dict.fromkeys(navigation_words[w.lower()] for w in focus if w.lower() in navigation_words)))
        cues = {c: t for ln in b["lines"] for c, t in ln["cues"].items()}
        nodes = [resolve_node(n, b, cues, not native) for n in s["nodes"]]
        by_id = {n["id"]: n for n in nodes}
        tracks, lanes = [], {}
        for event in sorted(s.get("events", []), key=lambda e: resolve_time(e.get("at", 0), b, cues) + e.get("offset", 0)):
            at = resolve_time(event.get("at", 0), b, cues) + event.get("offset", 0)
            end = at + event.get("duration", .5)
            if at < b["t0"] - .001 or end > b["t1"] + .001:
                raise ValueError(f"镜头 {b['arg']} 的 {event['target']} 事件超出镜头时段")
            for prop, value in event["to"].items():
                key = (event["target"], prop)
                previous = lanes.get(key)
                if previous and previous["end"] > at + .001:
                    raise ValueError(f"镜头 {b['arg']} 的 {key[0]}.{prop} 有重叠动作")
                defaults = {"opacity": 1, "scale": 1, "rotation": 0}
                start_value = previous["to"] if previous else by_id[key[0]].get(prop, defaults.get(prop, 0))
                track = dict(target=key[0], prop=prop, at=round(at, 3), end=round(end, 3),
                             start=start_value, to=value, ease=event.get("ease", "smooth"))
                tracks.append(track)
                lanes[key] = track
        shots.append(dict(id=b["arg"] if native else f"import-{index:03d}", title=s.get("label", b["title"]),
                          family=s.get("family", f"{lesson['root']['m']} · {lesson['root']['cn']}"),
                          t0=b["t0"], t1=b["t1"], lineno=b["lineno"], nodes=nodes, tracks=tracks,
                          navigation=navigation,
                          cues=cues, learn=[r["id"] for r in s.get("learn", [])], recall=s.get("recall", [])))
    film = dict(version=VERSION, stem=stem, root=f"{lesson['root']['m']} · {lesson['root']['cn']}",
                total=timeline["total"], subs=timeline["subs"], shots=shots, assets=assets,
                provenance=dict(native=native, relations=relations, assets=asset_paths))
    from provenance import digest
    film["fingerprint"] = digest(film)
    return film


def sample_times(film):
    """检查变化前、中、后；时间来自最终轨道，与定格图共用，不猜动作发生的时刻。"""
    samples = set()
    for shot in film["shots"]:
        samples.update((shot["t0"] + .1, max(shot["t0"], shot["t1"] - .5)))
        for tr in shot["tracks"]:
            samples.update((max(shot["t0"], tr["at"] - .01), tr["at"],
                            (tr["at"] + tr["end"]) / 2, min(shot["t1"] - .001, tr["end"])))
        for node in shot["nodes"]:
            if node["type"] == "illustration" and node.get("actLevel") != "静止":
                start = node["actionAt"]
                samples.update(start + offset for offset in (.1, 1.4, 3.0) if shot["t0"] <= start + offset < shot["t1"])
    return sorted(t for t in samples if 0 <= t < film["total"])
