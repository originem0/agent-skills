"""可执行分镜的内容契约。只校验声明和引用，不冒充词源或教学效果审稿。"""
import math
import re
from pathlib import Path

ID = re.compile(r"[A-Za-z][A-Za-z0-9_.-]{0,79}\Z")
KINDS = {"etymology", "usage", "analogy", "contrast"}
NODE_TYPES = {"text", "image", "illustration", "shape", "line", "summary"}
ANIMATED = {"x", "y", "w", "h", "opacity", "scale", "rotation"}
SCENE_KEYS = {"nodes", "events", "learn", "requires", "recall", "closing", "label", "family", "focus"}
NODE_KEYS = {"id", "type", "x", "y", "w", "h", "opacity", "scale", "rotation", "text", "runs",
             "font", "size", "color", "weight", "align", "file", "fit", "crop", "credit", "ref", "items",
             "shape", "fill", "stroke", "strokeWidth", "radius", "d", "points", "arrow", "dash",
             "relation", "field", "refs", "layout", "heading", "actionAt", "actLevel"}


def number(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)


def string_list(value):
    return isinstance(value, list) and all(isinstance(x, str) for x in value)


def local_image(project, ref):
    """规范化后检查边界，也覆盖目录链接；图片仍由项目管理，不从远程地址隐式加载。"""
    if not isinstance(ref, str) or not ref or re.match(r"[A-Za-z]:|[/\\]|\w+://", ref):
        raise ValueError("图片须使用项目内的相对路径")
    root = Path(project).resolve()
    path = (root / ref).resolve()
    if not path.is_relative_to(root) or path == root:
        raise ValueError("图片超出项目目录")
    if not path.is_file():
        raise ValueError(f"找不到图片 {ref}")
    if path.suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp", ".svg"}:
        raise ValueError(f"不支持的图片格式 {ref}")
    return path


def validate(sc, lesson, project=None):
    errs, shot_ids, relations, seen, recalled, covered = [], set(), {}, set(), set(), set()
    navigation_words = set()
    words = {w["w"].lower(): w for w in lesson.get("words", []) + ([lesson["finale"]] if lesson.get("finale") else [])}
    scenes = {k for k in ("anchor", "opening", "finale") if lesson.get(k, {}).get("scene")}
    scenes.update(k for k, w in words.items() if w.get("scene"))
    has_closing = False
    for b in sc.beats:
        where = f"第 {b.lineno} 行 [shot: {b.arg}]"
        def err(msg):
            errs.append(f"{where}：{msg}")
        if b.block != "shot":
            err("新分镜不能混入旧画面块；整份旧稿仍可由导入适配层读取")
            continue
        if not ID.fullmatch(b.arg) or b.arg in shot_ids:
            err("镜头编号须唯一，使用字母、数字、点、短横线或下划线")
        shot_ids.add(b.arg)
        for field in ("已知", "推进"):
            if not b.get(field) or not any(b.get(field)):
                err(f"缺少 > {field}，写明本段的理解任务")
        if not b.lines:
            err("分镜缺少口播")
        s = b.scene
        if not s:
            err("缺少 ```scene 分镜块")
            continue
        if set(s) - SCENE_KEYS:
            err("未知分镜字段：" + "、".join(sorted(set(s) - SCENE_KEYS)))
        for key in ("nodes", "events", "learn", "requires", "recall"):
            if not isinstance(s.get(key, []), list):
                err(f"{key} 必须是列表")
        if any(not isinstance(s.get(k, []), list) for k in ("nodes", "events", "learn", "requires", "recall")):
            continue
        if any(not string_list(s.get(k, [])) for k in ("requires", "recall")):
            err("requires、recall 须为关系编号列表")
            continue
        if "closing" in s and not isinstance(s["closing"], bool):
            err("closing 须为 true 或 false")
        if "label" in s and not isinstance(s["label"], str):
            err("label 须为文字")
        if "family" in s and not isinstance(s["family"], str):
            err("family 须为文字；空文字可以在提问时暂不显示词根提示")
        new_relations = set()
        anchors = {}
        for ln in b.lines:
            for a in ln.anchors:
                if not a["text"].strip() or not a["id"] or a["id"] in anchors:
                    err(f"触发点 {a['id']} 为空或重复，用 {{独立编号|实际念的词}} 区分")
                anchors[a["id"]] = a
        for ref in s.get("requires", []) + s.get("recall", []):
            if not isinstance(ref, str) or ref not in seen:
                err(f"关系 {ref} 尚未讲过，不能作为前提或回扣")
        for r in s.get("learn", []):
            if not isinstance(r, dict):
                err("learn 中每项须为关系对象")
                continue
            rid = r.get("id", "")
            if not isinstance(rid, str) or not ID.fullmatch(rid) or rid in relations:
                err(f"关系编号 {rid} 无效或重复")
                continue
            if not isinstance(r.get("kind"), str) or r["kind"] not in KINDS:
                err(f"{rid} 要区分 etymology、usage、analogy 或 contrast")
            if not all(isinstance(r.get(k), str) and r[k].strip() for k in ("label", "detail", "source")):
                err(f"{rid} 缺少 label、detail 或 source")
            src = r.get("source", "")
            if isinstance(src, str) and src.startswith("lesson:"):
                word = src.partition(":")[2].lower()
                if word not in words or not words[word].get("fact"):
                    err(f"{rid} 引用的课程词源 {src} 不存在")
            elif not isinstance(src, str) or not re.match(r"https?://\S+\Z", src):
                err(f"{rid} 的 source 须为课程词源 lesson:词 或已核实的网页 URL")
            if not string_list(r.get("words", [])):
                err(f"{rid} 的 words 须为单词列表")
            else:
                covered.update(w.lower() for w in r.get("words", []) if w.lower() in words)
                if r.get("kind") != "contrast":
                    navigation_words.update(w.lower() for w in r.get("words", []))
                narration = " ".join(ln.plain for ln in b.lines)
                for word in r.get("words", []):
                    if not re.search(rf"(?<![A-Za-z]){re.escape(word)}(?![A-Za-z])", narration, re.I):
                        err(f"{rid} 声明讲解 {word}，但本段口播没有出现这个词")
            relations[rid] = r
            seen.add(rid)
            new_relations.add(rid)
        if "focus" in s:
            if not string_list(s["focus"]) or len(set(w.lower() for w in s["focus"])) != len(s["focus"]):
                err("focus 须为不重复的单词列表；空列表表示本段不突出某个词")
            elif any(w.lower() not in navigation_words for w in s["focus"]):
                err("focus 只能定位此前或本段已引入的词，不能提前显示未知词或形近反例")
        nodes = s.get("nodes", [])
        if not nodes:
            err("分镜没有画面元素")
        by_id, represented = {}, set()
        for node in nodes:
            if not isinstance(node, dict):
                err("画面元素须为对象")
                continue
            nid = node.get("id", "")
            if not isinstance(nid, str) or not ID.fullmatch(nid) or nid in by_id:
                err(f"元素编号 {nid} 无效或重复")
                continue
            by_id[nid] = node
            if set(node) - NODE_KEYS:
                err(f"{nid} 未知字段：" + "、".join(sorted(set(node) - NODE_KEYS)))
            typ = node.get("type")
            if not isinstance(typ, str) or typ not in NODE_TYPES:
                err(f"{nid} 的类型 {typ} 不受支持")
            for k in ("x", "y", "w", "h"):
                if not number(node.get(k)) or (k in ("w", "h") and node[k] <= 0):
                    err(f"{nid}.{k} 须为有效画面坐标或正尺寸")
            for k in ("opacity", "scale", "rotation", "size", "strokeWidth"):
                if k in node and not number(node[k]):
                    err(f"{nid}.{k} 必须为有限数值")
            if number(node.get("opacity")) and not 0 <= node["opacity"] <= 1:
                err(f"{nid}.opacity 应在 0 到 1 之间")
            for key in ("scale", "size", "strokeWidth"):
                if number(node.get(key)) and node[key] <= 0:
                    err(f"{nid}.{key} 须为正数")
            if "text" in node and not isinstance(node["text"], str):
                err(f"{nid}.text 须为文字")
            if "runs" in node and (not isinstance(node["runs"], list) or not node["runs"] or
                                   any(not isinstance(r, dict) or not isinstance(r.get("text"), str) or
                                       set(r) - {"text", "color"} for r in node["runs"])):
                err(f"{nid}.runs 须为含 text 和可选 color 的文字片段列表")
            if typ == "text" and not any(node.get(k) for k in ("text", "runs", "relation")):
                err(f"{nid} 文字元素为空")
            for key, choices in (("font", ("en", "zh")), ("align", ("left", "center", "right")),
                                 ("field", ("label", "detail")), ("actLevel", ("静止", "轻", "正常", "明显")),
                                 ("shape", ("rect", "ellipse", "path")), ("layout", ("branches", "columns"))):
                if key in node and node[key] not in choices:
                    err(f"{nid}.{key} 只能为 {'、'.join(choices)}")
            if "points" in node and (not isinstance(node["points"], list) or len(node["points"]) < 2 or
                                     any(not isinstance(p, list) or len(p) != 2 or not all(number(x) for x in p)
                                         for p in node["points"])):
                err(f"{nid}.points 须为至少两个 [x,y] 坐标")
            if typ == "shape" and node.get("shape") == "path" and not isinstance(node.get("d"), str):
                err(f"{nid} 路径缺少 d")
            if typ == "image":
                if project is not None:
                    try:
                        local_image(project, node.get("file"))
                    except ValueError as e:
                        err(f"{nid}：{e}")
                if not node.get("credit"):
                    err(f"{nid} 图片缺少 credit 署名")
                if node.get("fit", "contain") not in ("contain", "cover"):
                    err(f"{nid}.fit 只能为 contain 或 cover")
                if "crop" in node:
                    crop = node["crop"]
                    if (not isinstance(crop, list) or len(crop) != 4 or not all(number(x) for x in crop)
                            or min(crop) < 0 or crop[2] <= 0 or crop[3] <= 0
                            or crop[0] + crop[2] > 1.000001 or crop[1] + crop[3] > 1.000001):
                        err(f"{nid}.crop 应为图内归一化的 [x,y,宽,高]")
            if typ == "illustration":
                ref = node.get("ref")
                if (not isinstance(ref, str) or ref not in scenes) and not node.get("items"):
                    err(f"{nid} 未指定有效课程线稿 ref 或图形 items")
                if ref and node.get("items"):
                    err(f"{nid} ref 与 items 只能指定一个")
                if "items" in node:
                    raw = node["items"]
                    items = raw.get("items") if isinstance(raw, dict) else raw
                    if not isinstance(items, list) or not items or any(not isinstance(it, dict) for it in items):
                        err(f"{nid}.items 须为图形零件对象列表")
            if typ == "summary":
                refs = node.get("refs", [])
                if not isinstance(refs, list) or not refs or any(not isinstance(x, str) or x not in seen for x in refs):
                    err(f"{nid} 只能总结已讲的关系")
                else:
                    represented.update(refs)
                    if set(refs) - set(s.get("recall", [])):
                        err(f"{nid} 总结的关系须列入本段 recall")
            if "relation" in node:
                rid = node["relation"]
                if not isinstance(rid, str) or rid not in seen:
                    err(f"{nid} 引用了未知关系 {rid}")
                else:
                    represented.add(rid)
            at = node.get("actionAt", 0)
            if not number(at) and (not isinstance(at, str) or at not in anchors):
                err(f"{nid} 的 actionAt 没有对应语音触发点")
        missing = (set(s.get("recall", [])) | new_relations) - represented
        if missing:
            err("讲解或回扣没有对应画面元素：" + "、".join(sorted(missing)))
        for event in s.get("events", []):
            if not isinstance(event, dict):
                err("events 中每项须为事件对象")
                continue
            if set(event) - {"target", "at", "offset", "duration", "to", "ease"}:
                err("事件含未知字段")
            if not isinstance(event.get("target"), str) or event["target"] not in by_id:
                err(f"事件找不到元素 {event.get('target')}")
            at = event.get("at", 0)
            if not number(at) and (not isinstance(at, str) or at not in anchors):
                err(f"事件找不到语音触发点 {at}")
            if not number(event.get("duration", .5)) or event.get("duration", .5) < 0:
                err("事件 duration 须为非负秒数")
            if not number(event.get("offset", 0)):
                err("事件 offset 须为秒数")
            to = event.get("to")
            if not isinstance(to, dict) or not to or set(to) - ANIMATED or any(not number(x) for x in to.values()):
                err("事件 to 只支持位置、尺寸、透明度、缩放与旋转的有限数值")
            elif any(to[k] <= 0 for k in ("w", "h", "scale") if k in to) or "opacity" in to and not 0 <= to["opacity"] <= 1:
                err("事件的尺寸与缩放须为正数，透明度须在 0 到 1 之间")
            if event.get("ease", "smooth") not in ("smooth", "linear", "hold"):
                err("事件 ease 只能是 smooth、linear 或 hold")
        if s.get("closing"):
            has_closing = True
            recalled.update(s.get("recall", []))
        # 数字需要本段依据；不能因为分镜格式不同就跳过原有事实约束。
        from script_md import FACT_RE
        lesson_text = str(lesson)
        sourced = b.get("来源") or any(isinstance(r, dict) and str(r.get("source", "")).startswith("http") for r in s.get("learn", []))
        if not sourced:
            for ln in b.lines:
                for match in FACT_RE.finditer(ln.plain):
                    if not re.search(rf"(?<!\d){re.escape(match[0])}(?!\d)", lesson_text):
                        err(f"第 {ln.lineno} 行的数字 {match[0]} 缺少本段来源")
    if not has_closing:
        errs.append("分镜缺少 closing 收束；可以由多个结尾镜头共同回扣")
    missing = set(relations) - recalled
    if missing:
        errs.append("结尾尚未收拢关系：" + "、".join(sorted(missing)))
    skip = set(re.findall(r"(?:^|[；;])\s*([A-Za-z-]+)", sc.meta.get("skip", "")))
    missing_words = {w["w"].lower() for w in lesson.get("words", [])} - covered - {w.lower() for w in skip}
    if missing_words:
        errs.append("主词没有对应 learn 关系，也未写入 skip：" + "、".join(sorted(missing_words)))
    return errs
