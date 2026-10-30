"""查词源：etymonline（经 firecrawl）→ Wiktionary API 后备 → 本地缓存。

用法：
    python scripts/etym.py tract attract distract      # 打印每个词的词源正文
    python scripts/etym.py tract --links               # 另外列出「Entries linking to」——找同族词的入口
    python scripts/etym.py tract --refresh             # 忽略缓存重新抓

为什么不直接请求 etymonline：它对脚本请求一律返回 403，只能经 firecrawl 抓。
firecrawl 每次调用消耗额度，所以抓过的词一律缓存在 cache/etym/，同一个词不再重复抓。
并发 10 个会触发 DNS 失败，这里固定最多 3 个并发、失败重试 3 次。
几个子代理同时查词时，多个进程叠加会超过 firecrawl 的并发上限（2 个），抓取失败的词会退回 Wiktionary：
所以要联网抓取时先拿一把跨进程的锁；etymonline 临时没抓到（不是 404）时，Wiktionary 的结果照常打印但不缓存，下次还会再试 etymonline。
"""
import argparse
import contextlib
import json
import re
import shutil
import subprocess
import sys
import threading
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / "cache" / "etym"
LOCK = CACHE / ".fetch.lock"
UA = "word-family-agent/1.0 (personal study tool)"


class FetchLock:
    """跨进程的抓取锁：目录创建是原子操作，Windows 和 POSIX 都能用。"""

    def __enter__(self):
        waited = False
        while True:
            try:
                LOCK.mkdir()
                return self
            except FileExistsError:
                try:
                    # 持锁的进程被杀掉时来不及删锁：超过 6 分钟就当它失效
                    if time.time() - LOCK.stat().st_mtime > 360:
                        LOCK.rmdir()
                        continue
                except FileNotFoundError:
                    continue
                if not waited:
                    print("（别的进程正在抓词源，排队中…）", file=sys.stderr, flush=True)
                    waited = True
                time.sleep(2)

    def __exit__(self, *exc):
        try:
            LOCK.rmdir()
        except FileNotFoundError:
            pass


def cache_path(word: str, src: str) -> Path:
    safe = re.sub(r"[^\w\-]", lambda m: f"_{ord(m.group()):x}_", word)
    return CACHE / f"{safe}.{src}.md"


def fetch_etymonline(word: str):
    """返回 (正文, 状态)。状态：ok / missing（etymonline 没有这个词）/ failed（没抓到，可能是并发或网络）/ no-firecrawl。"""
    exe = shutil.which("firecrawl")
    if not exe:
        return None, "no-firecrawl"
    url = "https://www.etymonline.com/word/" + urllib.parse.quote(word)
    for attempt in range(3):
        try:
            r = subprocess.run([exe, "scrape", url, "--format", "markdown"], capture_output=True,
                               timeout=120, encoding="utf-8", errors="replace")
            if "Origin and history" in r.stdout:
                return r.stdout, "ok"
            if "404" in r.stdout[:2000] or "Page not found" in r.stdout:
                return None, "missing"
            # 个别词页（如 mobile）稳定返回 Next.js 的数据流而不是正文，重试也一样，别再花额度
            if "$Sreact.fragment" in r.stdout[:1000]:
                return None, "failed"
        except subprocess.TimeoutExpired:
            pass
        time.sleep(2 * (attempt + 1))
    return None, "failed"


FAILED = CACHE / "_failed.json"
RETRY_AFTER = 6 * 3600       # 秒：没抓到的词这段时间内不再重抓，免得每查一次都烧额度
_failed_mu = threading.Lock()


def recent_failure(word: str) -> bool:
    try:
        t = json.loads(FAILED.read_text(encoding="utf-8")).get(word)
    except (FileNotFoundError, ValueError):
        return False
    return t is not None and time.time() - t < RETRY_AFTER


def note_failure(word: str):
    with _failed_mu:            # 同一进程的几个线程会同时写；跨进程由 FetchLock 保证只有一个在抓
        try:
            d = json.loads(FAILED.read_text(encoding="utf-8"))
        except (FileNotFoundError, ValueError):
            d = {}
        d[word] = time.time()
        FAILED.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")


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


def cached(word: str):
    for src in ("eo", "wikt"):
        p = cache_path(word, src)
        if p.exists():
            return src, p.read_text(encoding="utf-8")
    return None, None


def lookup(word: str, refresh: bool):
    """返回 (来源, 原文)。来源：eo / wikt / wikt-temp（etymonline 这次没抓到，Wiktionary 结果没缓存）。"""
    if not refresh:
        src, raw = cached(word)
        if raw:
            return src, raw
    if not refresh and recent_failure(word):
        raw, status = None, "failed"
    else:
        raw, status = fetch_etymonline(word)
    if raw:
        cache_path(word, "eo").write_text(raw, encoding="utf-8")
        return "eo", raw
    if status == "failed":
        note_failure(word)
    raw = fetch_wiktionary(word)
    if raw:
        if status == "failed":
            # 缓存了 Wiktionary，以后查这个词就再也不会去试 etymonline 了
            return "wikt-temp", raw
        cache_path(word, "wikt").write_text(raw, encoding="utf-8")
        return "wikt", raw
    return None, None


SRC_LABEL = {"eo": "etymonline", "wikt": "wiktionary",
             "wikt-temp": "wiktionary；etymonline 没抓到，结果没缓存。6 小时后再查会重试，急用就加 --refresh"}


def main():
    for stream in (sys.stdout, sys.stderr):      # 排队提示走 stderr，也要 UTF-8，否则 Windows 下是乱码
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description="查词源（带缓存）")
    ap.add_argument("words", nargs="+")
    ap.add_argument("--links", action="store_true", help="列出 etymonline 的同族链接词条")
    ap.add_argument("--refresh", action="store_true", help="忽略缓存")
    a = ap.parse_args()
    CACHE.mkdir(parents=True, exist_ok=True)
    need_fetch = a.refresh or any(cached(w)[1] is None for w in a.words)
    with FetchLock() if need_fetch else contextlib.nullcontext():
        with ThreadPoolExecutor(max_workers=3) as pool:
            results = list(pool.map(lambda w: (w, *lookup(w, a.refresh)), a.words))
    missing = []
    for word, src, raw in results:
        print(f"\n===== {word}  [{SRC_LABEL.get(src, '未找到')}]")
        if not raw:
            missing.append(word)
            print("（两个来源都没有查到。不要凭记忆补词源：换拼写/词形再查，或在课程里标「词源存疑」。）")
            continue
        main_text, links = extract(raw, "wikt" if src.startswith("wikt") else src)
        print(main_text[:3500])
        if a.links and links:
            print(f"\n-- 同族链接（{len(links)}）：" + ", ".join(links))
    if missing:
        print(f"\n未查到：{', '.join(missing)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
