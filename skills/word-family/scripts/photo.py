"""给课程开场配一张真实图片：从维基共享资源搜图（免费许可、自动署名），或者给网页截图（如新闻标题）。

用法：
    python scripts/photo.py search "baggage claim sign"          # 候选图下载到 cache/photos/<查询>/，总览图 _sheet.jpg（带编号）
    python scripts/photo.py pick tract "tractor trailer" 3        # 选第 3 张：存为 lessons/media/tract/opening.jpg，并写进 lessons/tract.json
    python scripts/photo.py shot tract https://example.com/news   # 网页截图（默认截首屏 1280×720），写进 lessons/tract.json
    python scripts/photo.py clear tract                           # 去掉开场图片

图片是可选的：搜不到贴合的就不用，开场照常用线稿。
搜索词用英文、写具体的实物或场景（"tractor field"、"airport baggage claim sign"），比抽象词好找得多。
只保留 CC BY / CC BY-SA / CC0 / 公有领域的图，署名写进 opening.photo.credit，页面和视频上都会显示。
"""
import argparse
import datetime
import json
import re
import shutil
import sys
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LESSONS = ROOT / "lessons"
CACHE = ROOT / "cache" / "photos"
UA = "word-family-agent/1.0 (personal study tool)"
OK_LICENSE = re.compile(r"^(CC BY(-SA)? [\d.]+|CC0|Public domain|PD)", re.I)


def slug(q: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", q.lower()).strip("-")[:60]


def get_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def download(url, path):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r, open(path, "wb") as f:
        shutil.copyfileobj(r, f)


def strip_html(s):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", s or "")).strip()


def cmd_search(q, n):
    params = {"action": "query", "format": "json", "generator": "search", "gsrnamespace": 6,
              "gsrsearch": f"{q} filetype:bitmap", "gsrlimit": 30, "prop": "imageinfo",
              "iiprop": "url|extmetadata|size|mime", "iiurlwidth": 1200}
    d = get_json("https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode(params))
    pages = sorted(d.get("query", {}).get("pages", {}).values(), key=lambda p: p.get("index", 0))
    out = CACHE / slug(q)
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    cands = []
    for p in pages:
        ii = p["imageinfo"][0]
        m = ii.get("extmetadata", {})
        lic = strip_html(m.get("LicenseShortName", {}).get("value", ""))
        if ii.get("width", 0) < 800 or not OK_LICENSE.match(lic) or ii.get("mime") not in ("image/jpeg", "image/png"):
            continue
        k = len(cands) + 1
        ext = ".png" if ii["mime"] == "image/png" else ".jpg"
        f = out / f"{k:02d}{ext}"
        try:
            download(ii.get("thumburl") or ii["url"], f)
        except Exception:
            continue
        cands.append({"n": k, "file": f.name, "title": p["title"], "license": lic,
                      "artist": strip_html(m.get("Artist", {}).get("value", "")) or "佚名",
                      "page": ii.get("descriptionurl", "")})
        if len(cands) >= n:
            break
    (out / "candidates.json").write_text(json.dumps(cands, ensure_ascii=False, indent=1), encoding="utf-8")
    if not cands:
        print("没有找到合适的图（换个更具体的英文搜索词，或者不用图）")
        return 0
    for c in cands:
        print(f"  {c['n']:>2}. {c['title'][5:70]}  [{c['license']}]")
    try:   # 总览图，编号写在左上角，方便挑
        from PIL import Image, ImageDraw
        W, H, cols = 420, 280, 3
        sheet = Image.new("RGB", (W * cols, H * ((len(cands) + cols - 1) // cols)), "white")
        dr = ImageDraw.Draw(sheet)
        for i, c in enumerate(cands):
            im = Image.open(out / c["file"]).convert("RGB")
            im.thumbnail((W - 8, H - 8))
            x, y = (i % cols) * W, (i // cols) * H
            sheet.paste(im, (x + 4, y + 4))
            dr.rectangle([x + 4, y + 4, x + 44, y + 40], fill="black")
            dr.text((x + 14, y + 10), str(c["n"]), fill="white")
        sheet.save(out / "_sheet.jpg", quality=85)
        print(f"\n总览图：{out / '_sheet.jpg'}（看图挑选，再用 pick）")
    except ImportError:
        print(f"\n候选图在：{out}")
    return 0


def set_photo(stem, photo):
    jp = LESSONS / f"{stem}.json"
    if not jp.exists():
        sys.exit(f"找不到课程 {jp}")
    L = json.loads(jp.read_text(encoding="utf-8"))
    if photo:
        L["opening"]["photo"] = photo
    else:
        L["opening"].pop("photo", None)
    jp.write_text(json.dumps(L, ensure_ascii=False, indent=1), encoding="utf-8")


def cmd_pick(stem, q, n):
    src_dir = CACHE / slug(q)
    cj = src_dir / "candidates.json"
    if not cj.exists():
        sys.exit(f"先运行 search \"{q}\"")
    c = next((x for x in json.loads(cj.read_text(encoding="utf-8")) if x["n"] == n), None)
    if not c:
        sys.exit(f"没有第 {n} 张")
    dst_dir = LESSONS / "media" / stem
    dst_dir.mkdir(parents=True, exist_ok=True)
    dst = dst_dir / "opening.jpg"
    try:
        from PIL import Image
        im = Image.open(src_dir / c["file"]).convert("RGB")
        im.thumbnail((1600, 1600))
        im.save(dst, quality=88)
    except ImportError:
        dst = dst_dir / ("opening" + Path(c["file"]).suffix)
        shutil.copy(src_dir / c["file"], dst)
    photo = {"file": f"media/{stem}/{dst.name}", "credit": f"照片：{c['artist']}，{c['license']}，Wikimedia Commons",
             "source": c["page"]}
    set_photo(stem, photo)
    print(f"已写入 lessons/{stem}.json 的 opening.photo：\n  {json.dumps(photo, ensure_ascii=False)}\n再运行 build.py 生成页面")
    return 0


def cmd_shot(stem, url, clip):
    from playwright.sync_api import sync_playwright
    dst_dir = LESSONS / "media" / stem
    dst_dir.mkdir(parents=True, exist_ok=True)
    dst = dst_dir / "opening.png"
    x, y, w, h = clip
    with sync_playwright() as p:
        browser = None
        for opts in ({"channel": "chrome"}, {"channel": "msedge"}, {}):
            try:
                browser = p.chromium.launch(**opts)
                break
            except Exception:
                continue
        page = browser.new_page(viewport={"width": max(1280, x + w), "height": max(800, y + h)})
        page.goto(url, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(2500)
        page.screenshot(path=str(dst), clip={"x": x, "y": y, "width": w, "height": h})
        browser.close()
    site = urllib.parse.urlparse(url).netloc
    photo = {"file": f"media/{stem}/opening.png", "credit": f"网页截图：{site}，{datetime.date.today()}", "source": url}
    set_photo(stem, photo)
    print(f"已截图并写入 opening.photo：{dst}\n请打开图片确认截到的是标题区域；不对就用 --clip x,y,宽,高 重截")
    return 0


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description="给课程开场配真实图片")
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("search")
    s.add_argument("query")
    s.add_argument("--n", type=int, default=9)
    s = sub.add_parser("pick")
    s.add_argument("lesson")
    s.add_argument("query")
    s.add_argument("n", type=int)
    s = sub.add_parser("shot")
    s.add_argument("lesson")
    s.add_argument("url")
    s.add_argument("--clip", default="0,0,1280,720", help="x,y,宽,高")
    s = sub.add_parser("clear")
    s.add_argument("lesson")
    a = ap.parse_args()
    if a.cmd == "search":
        return cmd_search(a.query, a.n)
    if a.cmd == "pick":
        return cmd_pick(a.lesson, a.query, a.n)
    if a.cmd == "shot":
        return cmd_shot(a.lesson, a.url, [int(v) for v in a.clip.split(",")])
    set_photo(a.lesson, None)
    print("已去掉开场图片")
    return 0


if __name__ == "__main__":
    sys.exit(main())
