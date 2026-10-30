"""把课程 JSON 渲染成单文件 HTML，并刷新课程目录。

用法：
    python scripts/build.py lessons/tract.json          # 生成 lessons/tract.html，并自动做版面检查
    python scripts/build.py lessons/tract.json --snap   # 另存整页截图 lessons/_snap/tract*.png，供人工复查
    python scripts/build.py --all                       # 重建全部课程

检查分三级：
    错误   —— 数据不合格，不生成页面（缺字段、零件名写错、split 拼不回单词……）
    提醒   —— 页面照常生成，但内容或版面有问题，交付前必须处理或向用户说明
              （漏标的同化形式、字面画面过长、桥接句式重复、画面文字重叠/出界……）
    版面检查需要 Python 版 Playwright（pip install playwright），用本机 Chrome/Edge 运行，不需要另装浏览器；
    没装就跳过并提示，此时请用 --snap 截图人工看。

只依赖标准库；--snap 需要 Chrome 或 Edge，装了 Pillow 时会把长截图切段。
"""
import argparse
import json
import math
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = ROOT / "assets" / "lesson_template.html"
KIT = ROOT / "assets" / "kit.js"
LESSONS = ROOT / "lessons"
PLACEHOLDER = "/*__LESSON_JSON__*/null"
KIT_PLACEHOLDER = "/*__KIT_JS__*/"

WORD_FIELDS = ["w", "split", "parts", "literal", "bridge", "meaning", "fact", "scene"]

# 常见前缀的同化形式（拉丁语前缀碰到某些辅音时向它靠拢，为了顺口）。
# 只用来提醒「可能漏标」，不是判决：an-/e- 等也可能是别的前缀（希腊语 an- 表否定、e-mail），由写课的人判断。
ASSIM = {
    "ad-": ["ac", "af", "ag", "al", "an", "ap", "ar", "as", "at"],
    "com-/con-": ["col", "cor", "co"],
    "in-": ["il", "im", "ir"],
    "ex-": ["e", "ef"],
    "sub-": ["suc", "suf", "sug", "sum", "sup", "sur", "sus"],
    "ob-": ["oc", "of", "op"],
    "dis-": ["dif"],
    "syn-": ["sym", "syl", "sys"],
    "ab-": ["abs"],
}
FORM2BASE = {f: base for base, forms in ASSIM.items() for f in forms}
BASES = {b.strip("-") for base in ASSIM for b in base.split("/")}


def load_template(path: Path) -> str:
    """读模板并内联线稿零件库（网页版和视频版共用 kit.js）。"""
    return path.read_text(encoding="utf-8").replace(KIT_PLACEHOLDER, KIT.read_text(encoding="utf-8"))


def kit_names(tpl: str = None):
    """从零件库源码里读出零件名和姿势名，避免两处清单不同步。"""
    tpl = tpl or KIT.read_text(encoding="utf-8")
    k_block = tpl.split("const K = {", 1)[1].split("\n};", 1)[0]
    kinds = set(re.findall(r"^  (\w+)(?:\(o\)|: o =>)", k_block, re.M))
    p_block = tpl.split("const POSES = {", 1)[1].split("\n};", 1)[0]
    poses = set(re.findall(r"^  (\w+):", p_block, re.M))
    return kinds, poses


def norm_part(pt):
    """词素可写成 [形式, 中文义, 类型?] 或 {m, cn, kind?, of?}，统一成 dict。和 kit.js 的 normPart 保持一致。"""
    o = {"m": pt[0], "cn": pt[1] if len(pt) > 1 else "", "kind": pt[2] if len(pt) > 2 else None} \
        if isinstance(pt, list) else dict(pt)
    m = o.get("m", "")
    o["kind"] = o.get("kind") or ("p" if m.endswith("-") else "s" if m.startswith("-") else "r")
    return o


# 开场方式，详见 references/openings.md
OPENING_TYPES = {"name": "熟词拆名", "scene": "生活场景/标识", "pair": "双词矛盾", "polysemy": "一词多义之谜",
                 "news": "时事新闻", "pop": "品牌/游戏/流行文化", "story": "想象小剧场", "visual": "视觉谜题"}


def check_opening(o, kinds, poses, errs, warns):
    t = o.get("type")
    if not t:
        warns.append(f"opening 缺少 type（开场方式，见 references/openings.md）：{'、'.join(f'{k}={v}' for k, v in OPENING_TYPES.items())}")
    elif t not in OPENING_TYPES:
        errs.append(f"opening.type={t!r} 不存在，可选：{', '.join(OPENING_TYPES)}")
    if t == "news":
        src = o.get("source") or {}
        if not all(src.get(k) for k in ("title", "url", "date")):
            errs.append("时事开场必须写 opening.source = {title, url, date}，来自真实检索；查不到就换别的开场，不许编新闻")
    ph = o.get("photo")
    if ph:
        if not (LESSONS / ph.get("file", "")).exists():
            errs.append(f"opening.photo.file 指向的图片不存在：lessons/{ph.get('file')}（用 scripts/photo.py pick/shot 生成）")
        if not ph.get("credit"):
            errs.append("opening.photo 缺少 credit（署名和许可，photo.py 会自动写）")
    if "scene" in o:
        check_scene(o["scene"], "opening", kinds, poses, errs)
    elif not ph:
        errs.append("opening 缺少 scene（没有 photo 时必须有线稿画面）")


def opening_usage(current: Path):
    """统计其他课程用过的开场类型，按修改时间从新到旧。"""
    used = []
    for jp in sorted(LESSONS.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
        if jp.resolve() == current.resolve():
            continue
        try:
            used.append(json.loads(jp.read_text(encoding="utf-8")).get("opening", {}).get("type"))
        except (json.JSONDecodeError, AttributeError):
            pass
    return [u for u in used if u]


def check_scene(sc, where, kinds, poses, errs):
    items = sc if isinstance(sc, list) else (sc or {}).get("items")
    if not isinstance(items, list) or not items:
        errs.append(f"{where}: scene 为空")
        return
    roles = [it["id"] for it in items if it.get("k") == "fig" and "id" in it]
    if any(not isinstance(role, str) or not role.strip() for role in roles) or len(set(map(str, roles))) != len(roles):
        errs.append(f"{where}: 人物 id 应为本场景中唯一的文字")
    for i, it in enumerate(items):
        k = it.get("k")
        if k not in kinds:
            errs.append(f"{where}: 第 {i + 1} 个零件 k={k!r} 不存在（可用：{', '.join(sorted(kinds))}）")
        if k == "fig" and it.get("pose", "stand") not in poses:
            errs.append(f"{where}: 姿势 {it.get('pose')!r} 不存在（可用：{', '.join(sorted(poses))}）")
        motion = it.get("motion")
        if motion is not None:
            frm = motion.get("from") if isinstance(motion, dict) else None
            numeric = lambda x: isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)
            if k != "fig" or not isinstance(frm, list) or len(frm) != 2 or not all(numeric(x) for x in frm):
                errs.append(f"{where}: 第 {i + 1} 个图元 motion 需要人物的 from: [x,y] 起点")
            if k == "fig" and (not numeric(it.get("x")) or not numeric(it.get("y", 108))):
                errs.append(f"{where}: 第 {i + 1} 个图元 motion 需要有效的终位 x/y")
            if isinstance(motion, dict) and "duration" in motion and (not numeric(motion["duration"]) or motion["duration"] <= 0):
                errs.append(f"{where}: motion.duration 应为正的秒数")
        if "follow" in it and (k == "fig" or not isinstance(it["follow"], str) or it["follow"] not in roles):
            errs.append(f"{where}: 第 {i + 1} 个图元 follow={it['follow']!r} 需要道具指向本场景的人物 id")


def validate(L, kinds, poses):
    """返回（错误, 提醒）。错误阻止生成，提醒不阻止。"""
    errs, warns = [], []
    for key in ["title", "root", "opening", "anchor", "words"]:
        if key not in L:
            errs.append(f"缺少顶层字段 {key}")
    if errs:
        return errs, warns
    teaching = L.get("teaching", {})
    if not isinstance(teaching, dict):
        errs.append("teaching 应为对象（known、discovery、contrasts），旧课可省略")
    else:
        if "known" in teaching and (not isinstance(teaching["known"], list)
                                    or any(not isinstance(x, str) or not x.strip() for x in teaching["known"])):
            errs.append("teaching.known 应为非空文字组成的数组，写学习者已有的经验")
        if "discovery" in teaching and not isinstance(teaching["discovery"], str):
            errs.append("teaching.discovery 应为文字，说明解释带来的新联系")
        contrasts = teaching.get("contrasts", [])
        if not isinstance(contrasts, list):
            errs.append("teaching.contrasts 应为数组")
        else:
            for i, contrast in enumerate(contrasts):
                if not isinstance(contrast, dict) or any(not isinstance(contrast.get(k), str)
                                                        or not contrast[k].strip()
                                                        for k in ("a", "b", "distinction", "fact", "source")):
                    errs.append(f"teaching.contrasts 第 {i + 1} 项需要 a、b、distinction、fact、source，双方先查证")
    root = L["root"]
    if not {"m", "cn"} <= set(root):
        errs.append("root 需要 m 和 cn")
    for i, v in enumerate(root.get("variants") or []):
        if not isinstance(v, dict) or not v.get("m"):
            errs.append(f"root.variants 第 {i + 1} 项应为 {{\"m\": 形式, \"note\": 出现条件, \"ex\": 例词}}")
    check_opening(L["opening"], kinds, poses, errs, warns)
    if "scene" not in L["anchor"]:
        errs.append("anchor 缺少 scene")
    else:
        check_scene(L["anchor"]["scene"], "anchor", kinds, poses, errs)

    words = L["words"]
    if not 3 <= len(words) <= 8:
        errs.append(f"words 有 {len(words)} 个；家族图按 3–8 个设计")
    elif not 5 <= len(words) <= 7:
        warns.append(f"words 有 {len(words)} 个，建议 5–7 个")
    used_forms = set()
    for w in words + ([L["finale"]] if L.get("finale") else []):
        name = w.get("w", "?")
        for f in WORD_FIELDS:
            if f not in w:
                errs.append(f"{name}: 缺少字段 {f}")
        if "split" in w and "".join(w["split"]).lower() != name.lower():
            errs.append(f"{name}: split {w['split']} 拼起来不等于单词本身")
        if "scene" in w:
            check_scene(w["scene"], name, kinds, poses, errs)
        for pt in w.get("parts", []):
            if not isinstance(pt, (list, dict)) or (isinstance(pt, dict) and "m" not in pt):
                errs.append(f"{name}: parts 每项应为 [形式, 中文义] 或 {{\"m\":…, \"cn\":…}}")
                continue
            p = norm_part(pt)
            form = p["m"].strip("-").lower()
            used_forms.add(form)
            if p["kind"] == "p" and form in FORM2BASE and not p.get("of"):
                base = FORM2BASE[form]
                warns.append(f"{name}: 前缀 {p['m']} 可能是 {base} 的同化形式。若是，把这个词素写成 "
                             f"{{\"m\": \"{p['m']}\", \"cn\": \"{p['cn']}\", \"of\": \"{base.split('/')[0]}\"}}，"
                             f"并在 caveat 里用一句话解释为什么变（向后一个辅音靠拢，为了顺口）")
        # 内容质量提醒
        lit = w.get("literal", "")
        if len(lit) > 12:
            warns.append(f"{name}: literal「{lit}」{len(lit)} 字，超过 12 字，家族图上会挤")
        cav = w.get("caveat", "")
        if cav and (len(re.findall(r"[。！？]", cav)) > 2 or len(cav) > 90):
            warns.append(f"{name}: caveat 过长（{len(cav)} 字），最多两句话，细节放进 fact 或删掉")
        # 标点不能判断有几个真实义项；按来源审核，避免单义词为消除提醒而凑同义改写。
        if not w.get("ex"):
            warns.append(f"{name}: 缺少 ex（例句）：网页卡片和视频词卡都在释义下面放这句")
        if w is not words[0] and not w.get("link"):
            warns.append(f"{name}: 缺少 link（过渡句），卡片之间会断开")

    # 桥接句式：反问是推理工具，张张都「这不就是……吗」就成了口癖（视频解说曾因此像念模板）
    same = [w.get("w", "?") for w in words + ([L["finale"]] if L.get("finale") else [])
            if "这不就是" in w.get("bridge", "")]
    if len(same) > 2:
        warns.append(f"{len(same)} 张卡的 bridge 都用「这不就是……吗」（{'、'.join(same)}）：最多留两张，"
                     f"其余换别的接法——直接点破、举一个具体场景、条件分叉")

    # 变体覆盖：课程本身就是某个有同化形式的前缀，却没列 variants
    rm = root.get("m", "").strip("-").lower()
    if rm in BASES and not root.get("variants"):
        forms = next(fs for b, fs in ASSIM.items() if rm in [x.strip("-") for x in b.split("/")])
        warns.append(f"root {root['m']} 有常见同化形式（{'、'.join(f + '-' for f in forms)}），"
                     f"请在 root.variants 里列出常用的，并让主词至少覆盖其中两个")
    vforms = [v["m"].strip("-").lower() for v in root.get("variants") or [] if isinstance(v, dict) and v.get("m")]
    if vforms and not used_forms & set(vforms):
        warns.append("root.variants 里的变体一个都没出现在主词的 parts 里：主词应至少覆盖一个常用变体")

    tr = L.get("transfer", [])
    for i, t in enumerate(tr):
        if not (isinstance(t, list) and len(t) == 2):
            errs.append(f"transfer 第 {i + 1} 项应为 [题目, 答案]")
    if tr and len(tr) != 3:
        warns.append(f"transfer 有 {len(tr)} 道，建议 3 道")
    return errs, warns


# 在浏览器里量出每个零件的实际位置：文字压文字、文字被人物大面积遮住、零件出界、家族图文字重叠。
# 文字类零件只量它里面的 <text>（不含气泡尾巴），避免把「尾巴指向说话人」误报成重叠。
LAYOUT_JS = r"""
() => {
  const TEXTY = new Set(['text','tag','bubble','paper','thought','spot']);
  const issues = [];
  const owner = el => {
    const card = el.closest('article[id]'); if (card) return card.id.replace(/^w-/, '');
    const p = el.closest('.panel'); if (!p) return '?';
    return p.classList.contains('opening') ? 'opening' : p.classList.contains('anchor') ? 'anchor' : 'panel';
  };
  const inter = (a, b) => Math.max(0, Math.min(a.r, b.r) - Math.max(a.l, b.l)) * Math.max(0, Math.min(a.b, b.b) - Math.max(a.t, b.t));
  document.querySelectorAll('figure.stage svg').forEach(svg => {
    const R = svg.getBoundingClientRect(), sx = 280 / R.width, sy = 122 / R.height;
    const box = els => {
      const rs = [...els].map(e => e.getBoundingClientRect()).filter(r => r.width || r.height);
      if (!rs.length) return null;
      return { l: (Math.min(...rs.map(r => r.left)) - R.left) * sx, r: (Math.max(...rs.map(r => r.right)) - R.left) * sx,
               t: (Math.min(...rs.map(r => r.top)) - R.top) * sy, b: (Math.max(...rs.map(r => r.bottom)) - R.top) * sy };
    };
    const items = [...svg.querySelectorAll(':scope > g[data-k]')].map(g => {
      const k = g.dataset.k, texty = TEXTY.has(k);
      return { k, i: +g.dataset.i, texty, full: box([g]), txt: texty ? box(g.querySelectorAll('text')) : null };
    }).filter(x => x.full);
    const where = owner(svg);
    for (const a of items) {
      const f = a.full;
      if (f.l < -3 || f.t < -3 || f.r > 283 || f.b > 125)
        issues.push(`${where}: 第 ${a.i + 1} 个零件 ${a.k} 超出画面（x ${f.l.toFixed(0)}–${f.r.toFixed(0)}，y ${f.t.toFixed(0)}–${f.b.toFixed(0)}；画面范围 x 0–280，y 0–122）`);
    }
    for (let p = 0; p < items.length; p++) for (let q = p + 1; q < items.length; q++) {
      const a = items[p], b = items[q];
      if (a.texty && b.texty && a.txt && b.txt) {
        const o = inter(a.txt, b.txt);
        if (o > 12) issues.push(`${where}: 第 ${a.i + 1} 个零件 ${a.k} 和第 ${b.i + 1} 个零件 ${b.k} 的文字重叠`);
      } else if (a.texty !== b.texty) {
        const t = a.texty ? a : b, o2 = a.texty ? b : a;
        if (o2.k !== 'fig' || !t.txt) continue;
        const area = (t.txt.r - t.txt.l) * (t.txt.b - t.txt.t), o = inter(t.txt, o2.full);
        if (area && o / area > 0.35) issues.push(`${where}: 第 ${t.i + 1} 个零件 ${t.k} 的文字被第 ${o2.i + 1} 个零件（人物）遮住了 ${(o / area * 100).toFixed(0)}%`);
      }
    }
  });
  document.querySelectorAll('.map svg').forEach(svg => {
    const ts = [...svg.querySelectorAll('text')].map(t => ({ s: t.textContent, r: t.getBoundingClientRect() }));
    for (let p = 0; p < ts.length; p++) for (let q = p + 1; q < ts.length; q++) {
      const a = ts[p].r, b = ts[q].r;
      const o = Math.max(0, Math.min(a.right, b.right) - Math.max(a.left, b.left)) * Math.max(0, Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top));
      if (o > 20) issues.push(`家族图: 「${ts[p].s}」和「${ts[q].s}」重叠（缩短 literal 或 daily 文字）`);
    }
  });
  return issues;
}
"""


def check_layout(html_path: Path):
    """返回版面问题列表；没装 Playwright 时返回 None。"""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return None
    with sync_playwright() as p:
        browser = None
        for opts in ({"channel": "chrome"}, {"channel": "msedge"}, {}):   # 优先用本机浏览器，免得另装
            try:
                browser = p.chromium.launch(**opts)
                break
            except Exception:
                continue
        if not browser:
            return None
        page = browser.new_page(viewport={"width": 1060, "height": 900})
        page.goto(html_path.resolve().as_uri())
        page.wait_for_timeout(300)
        issues = page.evaluate(LAYOUT_JS)
        browser.close()
    return issues


def render(L, tpl):
    # 防止数据里的 </script> 提前闭合脚本
    data = json.dumps(L, ensure_ascii=False, indent=1).replace("</", "<\\/")
    return tpl.replace(PLACEHOLDER, data)


def write_index():
    rows = []
    for jp in sorted(LESSONS.glob("*.json")):
        try:
            L = json.loads(jp.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        words = "、".join(w["w"] for w in L.get("words", []))
        rows.append(f'<li><a href="{jp.stem}.html">{L["title"]}</a><span>{words}</span></li>')
    html = f"""<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8"><title>词族课 · 目录</title>
<style>body{{background:#f7f5f0;color:#1e242b;font-family:-apple-system,"Segoe UI","Microsoft YaHei",sans-serif;padding:40px 18px}}
main{{max-width:760px;margin:0 auto}}h1{{font-size:1.4rem;margin-bottom:18px}}li{{list-style:none;background:#fff;border:1px solid #e4dfd5;
border-radius:12px;padding:14px 18px;margin-bottom:10px}}a{{color:#176b4d;font-weight:700;text-decoration:none;font-size:1.05rem}}
span{{display:block;color:#6b717a;font-size:.85rem;margin-top:4px;font-family:Georgia,serif}}</style></head>
<body><main><h1>词族课 · 目录（{len(rows)} 课）</h1><ul>{''.join(rows)}</ul></main></body></html>"""
    (LESSONS / "index.html").write_text(html, encoding="utf-8")


def find_browser():
    for p in [r"C:\Program Files\Google\Chrome\Application\chrome.exe",
              r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
              r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
              r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"]:
        if Path(p).exists():
            return p
    return shutil.which("chrome") or shutil.which("google-chrome") or shutil.which("msedge")


def snap(html_path: Path, n_cards: int):
    browser = find_browser()
    if not browser:
        print("  [snap] 没找到 Chrome/Edge，跳过截图")
        return []
    out_dir = LESSONS / "_snap"
    out_dir.mkdir(exist_ok=True)
    full = out_dir / f"{html_path.stem}.png"
    height = 1700 + 620 * n_cards + 1400
    subprocess.run([browser, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                    f"--window-size=1060,{height}", "--virtual-time-budget=3000",
                    f"--screenshot={full}", html_path.resolve().as_uri()],
                   capture_output=True, timeout=120)
    if not full.exists():
        print("  [snap] 截图失败")
        return []
    try:
        from PIL import Image  # 可选：把长图切成 1600px 一段，便于逐段查看
    except ImportError:
        return [full]
    im = Image.open(full)
    parts = []
    for i, top in enumerate(range(0, im.height, 1600)):
        seg = im.crop((0, top, im.width, min(top + 1600, im.height)))
        if seg.convert("L").getextrema()[0] > 235:  # 整段空白就不要了
            continue
        p = out_dir / f"{html_path.stem}_{i}.png"
        seg.save(p)
        parts.append(p)
    full.unlink()
    return parts


def build(json_path: Path, tpl: str, kinds, poses, do_snap: bool, do_check: bool) -> bool:
    try:
        L = json.loads(json_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"[失败] {json_path.name}: JSON 格式错误 —— {e}")
        return False
    errs, warns = validate(L, kinds, poses)
    if errs:
        print(f"[失败] {json_path.name}:")
        for e in errs:
            print("  - [错误]", e)
        return False
    out = json_path.with_suffix(".html")
    out.write_text(render(L, tpl), encoding="utf-8")
    print(f"[完成] {out}")
    used = opening_usage(json_path)
    t = L["opening"].get("type")
    if used:
        stat = "、".join(f"{OPENING_TYPES.get(k, k)} {used.count(k)}" for k in sorted(set(used), key=used.count, reverse=True))
        unused = [v for k, v in OPENING_TYPES.items() if k not in used]
        print(f"  [开场] 本课：{OPENING_TYPES.get(t, '未标注')}；其他课程用过：{stat}" + (f"；还没用过：{'、'.join(unused)}" if unused else ""))
        if t and t == used[0]:
            print(f"  [选材] 类型与最近一课相同（{OPENING_TYPES[t]}）；比较实际的场景与新联系，不按类型硬轮换")
    if do_check:
        issues = check_layout(out)
        if issues is None:
            print("  [版面] 未安装 Playwright，跳过自动检查；请用 --snap 截图逐张查看")
        else:
            warns += [f"版面 {x}" for x in issues]
    for w in warns:
        print("  - [提醒]", w)
    if do_check and not warns:
        print("  无提醒")
    if do_snap:
        for p in snap(out, len(L["words"]) + (1 if L.get("finale") else 0)):
            print(f"  [snap] {p}")
    return True


def main():
    # Windows 控制台默认 GBK，统一输出 UTF-8，避免中文乱码
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description="课程 JSON → HTML")
    ap.add_argument("json", nargs="*", help="课程 JSON 路径")
    ap.add_argument("--all", action="store_true", help="重建 lessons/ 下全部课程")
    ap.add_argument("--snap", action="store_true", help="生成整页截图供人工复查")
    ap.add_argument("--no-check", action="store_true", help="跳过自动版面检查")
    a = ap.parse_args()
    tpl = load_template(TEMPLATE)
    kinds, poses = kit_names()
    paths = sorted(LESSONS.glob("*.json")) if a.all else [Path(p) for p in a.json]
    if not paths:
        ap.print_help()
        return 1
    ok = all([build(p, tpl, kinds, poses, a.snap, not a.no_check) for p in paths])
    write_index()
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
