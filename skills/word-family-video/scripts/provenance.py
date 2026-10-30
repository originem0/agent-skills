"""审核所依据的实际输入。变更原因可追溯，不用文件时间冒充内容版本。"""
import hashlib
import json
from pathlib import Path

import script_md as smd
from storyboard import local_image


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                     separators=(",", ":")).encode("utf-8")).hexdigest()


def file_hash(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def snapshot(sc, lesson, project, wf, code, voice, rate):
    assets = {}
    for beat in sc.beats:
        if beat.block == "shot":
            for node in beat.scene.get("nodes", []):
                if node.get("type") == "image":
                    path = local_image(project, node.get("file"))
                    assets[node["file"]] = file_hash(path)
        elif beat.block == "photo":
            if beat.arg == "opening":
                ref = lesson.get("opening", {}).get("photo", {}).get("file", "")
                path = local_image(Path(wf) / "lessons", ref)
                assets["lesson:" + ref] = file_hash(path)
            else:
                assets[beat.arg] = file_hash(local_image(project, beat.arg))
    # 文件头的短指纹用于阅读；完整审核另存 SHA-256，状态与署名变化不改变内容版本。
    content_hash = hashlib.sha256(smd.mark(sc.text, "draft", "").encode("utf-8")).hexdigest()
    data = dict(version=1, script=smd.fingerprint(sc.text), script_content=content_hash, lesson=digest(lesson), assets=assets,
                code={name: file_hash(path) for name, path in code.items()}, voice=voice, rate=rate)
    return dict(data, fingerprint=digest(data))


def changed(approved, current):
    labels = {"version": "审核格式", "script": "脚本", "script_content": "脚本", "lesson": "课程", "lesson_file": "课程文件", "assets": "图片素材",
              "code": "画面或编译代码", "voice": "配音音色", "rate": "配音语速"}
    return list(dict.fromkeys(label for key, label in labels.items() if approved.get(key) != current.get(key)))
