"""查词源：etymonline（经 firecrawl）→ Wiktionary API 后备 → 本地缓存。

用法：
    python scripts/etym.py tract attract distract      # 打印每个词的词源正文
    python scripts/etym.py tract --links               # 另外列出「Entries linking to」——找同族词的入口
    python scripts/etym.py tract --refresh             # 忽略缓存重新抓

为什么不直接请求 etymonline：它对脚本请求一律返回 403，只能经 firecrawl 抓。
firecrawl 每次调用消耗额度，所以抓过的词一律缓存在 cache/etym/，同一个词不再重复抓。
并发 10 个会触发 DNS 失败，这里固定最多 3 个并发、失败重试 3 次。
"""
import argparse
import json
import re
import shutil
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / "cache" / "etym"
UA = "word-family-agent/1.0 (personal study tool)"


def cache_path(word: str, src: str) -> Path:
    safe = re.sub(r"[^\w\-]", lambda m: f"_{ord(m.group()):x}_", word)
    return CACHE / f"{safe}.{src}.md"


def fetch_etymonline(word: str) -> str | None:
    exe = shutil.which("firecrawl")
    if not exe:
        return None
    url = "https://www.etymonline.com/word/" + urllib.parse.quote(word)
    for attempt in range(3):
        try:
            r = subprocess.run([exe, "scrape", url, "--format", "markdown"], capture_output=True,
                               timeout=120, encoding="utf-8", errors="replace")
            if "Origin and history" in r.stdout:
                return r.stdout
            if "404" in r.stdout[:2000] or "Page not found" in r.stdout:
                return None
        except subprocess.TimeoutExpired:
            pass
        time.sleep(2 * (attempt + 1))
    return None


def fetch_wiktionary(word: str) -> str | None:
    q = urllib.parse.urlencode({"action": "parse", "page": word, "prop": "wikitext", "format": "json"})
    req = urllib.request.Request(f"https://en.wiktionary.org/w/api.php?{q}", headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.load(resp)
    except Exception:
        return None
    text = data.get("parse", {}).get("wikitext", {}).get("*", "")
    # 只取 English 段落里的 Etymology 小节
    # 注意 "\n===Etymology" 也以 "\n==" 开头，必须只按二级标题（恰好两个 =）切分
    eng = re.split(r"\n==[^=]", text.split("==English==", 1)[-1], maxsplit=1)[0] if "==English==" in text else text
    secs = re.findall(r"===\s*Etymology[^=]*===\n(.*?)(?=\n===)", eng, re.S)
    return "\n\n".join(s.strip() for s in secs) or None


def extract(raw: str, src: str):
    """返回（词源正文, 同族链接列表）。"""
    if src == "wikt":
        return raw.strip(), []
    body = raw.split("# Origin and history", 1)[-1].split("\n", 1)[-1]  # 去掉标题行残余 "of _word_"
    # 页面在正文/同族列表之后还有广告、"More to explore"、"Trending" 热门榜，必须截断，否则会混进无关词
    body = re.split(r"\n(?:Advertisement|## More to explore|## Share )", body, maxsplit=1)[0]
    main, _, linking = body.partition("## Entries linking")
    main = re.sub(r"\]\(https?://[^)]*\)", "]", main)          # 去掉链接 URL，保留文字
    main = re.sub(r"!\[[^\]]*\]\[?[^\n]*", "", main)
    main = "\n".join(l for l in main.splitlines()
                     if l.strip() and l.strip() != "* * *" and not l.startswith("[also from"))
    # 每个链接词条带 title "Origin and meaning of X"；清单里也有只是顺带提到该词的词条，只能当候选
    links = re.findall(r'"Origin and meaning of ([^"]+)"', linking)
    return main.strip(), sorted(set(x.strip() for x in links))


def lookup(word: str, refresh: bool):
    for src in ("eo", "wikt"):
        p = cache_path(word, src)
        if p.exists() and not refresh:
            return src, p.read_text(encoding="utf-8")
    raw = fetch_etymonline(word)
    if raw:
        cache_path(word, "eo").write_text(raw, encoding="utf-8")
        return "eo", raw
    raw = fetch_wiktionary(word)
    if raw:
        cache_path(word, "wikt").write_text(raw, encoding="utf-8")
        return "wikt", raw
    return None, None


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description="查词源（带缓存）")
    ap.add_argument("words", nargs="+")
    ap.add_argument("--links", action="store_true", help="列出 etymonline 的同族链接词条")
    ap.add_argument("--refresh", action="store_true", help="忽略缓存")
    a = ap.parse_args()
    CACHE.mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(max_workers=3) as pool:
        results = list(pool.map(lambda w: (w, *lookup(w, a.refresh)), a.words))
    missing = []
    for word, src, raw in results:
        print(f"\n===== {word}  [{ {'eo': 'etymonline', 'wikt': 'wiktionary'}.get(src, '未找到') }]")
        if not raw:
            missing.append(word)
            print("（两个来源都没有查到。不要凭记忆补词源：换拼写/词形再查，或在课程里标「词源存疑」。）")
            continue
        main_text, links = extract(raw, src)
        print(main_text[:3500])
        if a.links and links:
            print(f"\n-- 同族链接（{len(links)}）：" + ", ".join(links))
    if missing:
        print(f"\n未查到：{', '.join(missing)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
