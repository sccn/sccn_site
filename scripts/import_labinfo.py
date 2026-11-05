#!/usr/bin/env python3
"""Mirror the Lab Information section of sccn.ucsd.edu into this site.

Usage: python3 scripts/import_labinfo.py [--mirror DIR]

Crawls https://sccn.ucsd.edu/labinfo/ (pages and the assets their <main> content
references, staying under /labinfo/), then writes:

- src/data/labinfo.json  -> section nav + one entry per page (route, title, source,
  content_html), rendered by render_labinfo() in build_site.py
- public/labinfo/...     -> images, spreadsheets, code samples, and the Excel HTML
  exports, copied verbatim

Content handling: templated pages keep only their <main> content without the old
Bootstrap sub navbar and wrapper; plain pages keep their <body>. The first <h1> is
dropped (the site shell renders the title). Links to /labinfo/ pages become site
routes (directories keep a trailing slash, .php -> .php.html); links or images that
404 on the live server are unlinked or removed; other sccn.ucsd.edu links stay
absolute, except contact pages which map to /contact/. Assets above MAX_COPY_BYTES
are linked to the live server instead of being committed.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urljoin, urlsplit, urlunsplit

ROOT = Path(__file__).resolve().parents[1]
BASE = "https://sccn.ucsd.edu"
PREFIX = "/labinfo/"
MAX_COPY_BYTES = 20 * 1024 * 1024
PAGE_EXT = {"", ".html", ".htm", ".php"}
LEAD = "Practical information for SCCN members and visitors: computing, experiments, and equipment."

# Sub navigation as shown on the live section (LabStreamer is an external manual).
NAV = [
    {"label": "Overview", "url": "/labinfo/"},
    {
        "label": "Computing",
        "items": [
            {"label": "Computer Account", "url": "/labinfo/computing/account/"},
            {"label": "Data Storage", "url": "/labinfo/computing/data/"},
            {"label": "Email", "url": "/labinfo/computing/email/"},
            {"label": "MATLAB", "url": "/labinfo/computing/matlab/"},
            {"label": "Remote Access", "url": "/labinfo/computing/remote-desktop/"},
            {"label": "Personal Computer", "url": "/labinfo/computing/pc/"},
            {"label": "Printing", "url": "/labinfo/computing/printing/"},
            {"label": "Workstations", "url": "/labinfo/computing/workstations/"},
        ],
    },
    {"label": "Experiments", "url": "/labinfo/experiments/"},
    {
        "label": "Equipment",
        "items": [
            {"label": "LabStreamer", "url": "https://www.neurobs.com/manager/content/docs/labstreamer/index.html"},
            {"label": "MoBIGaze eye-tracking system", "url": "/labinfo/equipment/eyetracker/"},
            {"label": "Equipment Latencies", "url": "/labinfo/equipment/latencies/"},
            {"label": "EyeLink", "url": "/labinfo/equipment/eyelink/"},
        ],
    },
]
SEEDS = [NAV[0]["url"], NAV[2]["url"]] + [item["url"] for group in (NAV[1], NAV[3]) for item in group["items"] if item["url"].startswith("/")]

# Pages without a <title> or <h1> on the live site.
TITLE_OVERRIDES = {
    "/labinfo/equipment/latencies/biosemi--accum.html": "BioSemi Latency Charts",
}


def fetch(url: str) -> tuple[int, bytes]:
    req = urllib.request.Request(url, headers={"User-Agent": "sccn-site-import/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return resp.status, resp.read()
    except urllib.error.HTTPError as err:
        return err.code, b""


def normalize_page(path: str) -> str:
    """Directory-style pages get a trailing slash so /x and /x/ are one page."""
    if not Path(path).suffix and not path.endswith("/"):
        return path + "/"
    return path


def is_verbatim(path: str) -> bool:
    """Excel HTML exports are served as-is instead of being rewrapped."""
    return "_files/" in path or path.endswith(".htm")


def route_for(path: str) -> str:
    if path.endswith(".php"):
        return path + ".html"
    return normalize_page(path)


def local_path(root: Path, path: str) -> Path:
    rel = path[len(PREFIX):]
    if rel.endswith("/") or rel == "":
        rel += "index.html"
    return root / rel


def humanize(path: str) -> str:
    return re.sub(r"[-_]+", " ", Path(path.rstrip("/")).stem).strip().title()


def crawl(mirror: Path) -> tuple[dict, dict]:
    queue = [normalize_page(seed) for seed in SEEDS]
    pages: dict[str, dict] = {}
    assets: dict[str, dict] = {}
    while queue:
        path = queue.pop(0)
        if path in pages:
            continue
        url = BASE + path
        status, body = fetch(url)
        entry = {"status": status}
        pages[path] = entry
        if status != 200:
            print(f"  [{status}] {path}")
            continue
        target = local_path(mirror, path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(body)
        entry["file"] = target
        text = body.decode("utf-8", errors="replace")
        title = re.search(r"(?is)<title>(.*?)</title>", text)
        entry["title"] = title.group(1).strip() if title else ""
        main = re.search(r"(?is)<main[^>]*>(.*?)</main>", text)
        content = re.sub(r'(?is)<nav class="navbar sub.*?</nav>', "", main.group(1) if main else text)
        for attr, link in re.findall(r"""(href|src)=["']([^"']+)["']""", content):
            if link.startswith(("#", "mailto:", "javascript:", "tel:")):
                continue
            parts = urlsplit(urljoin(url, link))
            if parts.netloc != "sccn.ucsd.edu" or not parts.path.startswith(PREFIX):
                continue
            if attr == "href" and Path(parts.path).suffix.lower() in PAGE_EXT:
                queue.append(normalize_page(parts.path))
            else:
                assets.setdefault(parts.path, {})
        print(f"  [{status}] {path}  {entry['title']}")
        time.sleep(0.2)
    for path, info in assets.items():
        status, body = fetch(BASE + path)
        info.update(status=status, bytes=len(body))
        if status == 200 and len(body) <= MAX_COPY_BYTES:
            target = local_path(mirror, path)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(body)
            info["file"] = target
        time.sleep(0.1)
    return pages, assets


WRAPPER = re.compile(
    r'(?is)^\s*<div class="container">\s*<div class="row">\s*<section class="col-lg-12">(.*)</section>\s*</div>\s*</div>\s*$'
)


def import_section(pages: dict, assets: dict) -> None:
    public_root = ROOT / "public"
    live_pages = {p for p, e in pages.items() if e["status"] == 200 and not is_verbatim(p)}
    dead = {p for p, e in pages.items() if e["status"] != 200} | {p for p, a in assets.items() if a["status"] != 200}
    remote_only = {p for p, a in assets.items() if a["status"] == 200 and a["bytes"] > MAX_COPY_BYTES}
    report = {"unlinked": [], "removed": [], "live": set()}

    target_dir = public_root / PREFIX.strip("/")
    if target_dir.exists():
        shutil.rmtree(target_dir)
    copied = 0
    for path, info in list(assets.items()) + [(p, e) for p, e in pages.items() if is_verbatim(p)]:
        if info.get("status") != 200 or "file" not in info:
            continue
        dst = public_root / path.lstrip("/")
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(info["file"], dst)
        copied += 1

    def resolve(page_path: str, link: str) -> tuple[str, str]:
        if link.startswith(("#", "mailto:", "javascript:", "tel:")):
            return "keep", link
        absolute = urljoin(BASE + page_path, link)
        parts = urlsplit(absolute)
        if parts.netloc != "sccn.ucsd.edu":
            return "keep", link
        path = parts.path
        suffix = ("#" + parts.fragment) if parts.fragment else ""
        if path.startswith(PREFIX):
            norm = normalize_page(path)
            if norm in live_pages:
                return "rewritten", route_for(norm) + suffix
            if path in dead or norm in dead:
                return "dead", absolute
            if path in remote_only:
                return "rewritten", absolute
            return "rewritten", path + suffix
        if path.startswith("/contact"):
            return "rewritten", "/contact/"
        report["live"].add(absolute)
        return "rewritten", absolute

    def rewrite(page_path: str, html: str) -> str:
        def fix_anchor(match: re.Match) -> str:
            href = re.search(r"""href=["']([^"']*)["']""", match.group(1))
            if href and resolve(page_path, href.group(1))[0] == "dead":
                report["unlinked"].append((page_path, href.group(1)))
                return match.group(2)
            return match.group(0)

        def fix_img(match: re.Match) -> str:
            src = re.search(r"""src=["']([^"']*)["']""", match.group(0))
            if src and resolve(page_path, src.group(1))[0] == "dead":
                report["removed"].append((page_path, src.group(1)))
                return ""
            return match.group(0)

        def fix_attr(match: re.Match) -> str:
            attr, quote, link = match.groups()
            return f"{attr}={quote}{resolve(page_path, link)[1]}{quote}"

        html = re.sub(r"(?is)(<a\b[^>]*>)(.*?)</a>", fix_anchor, html)
        html = re.sub(r"(?is)<img\b[^>]*>", fix_img, html)
        return re.sub(r"""(href|src)=(["'])([^"']+)\2""", fix_attr, html)

    out_pages = []
    for path in sorted(live_pages):
        entry = pages[path]
        text = Path(entry["file"]).read_text(encoding="utf-8", errors="replace")
        title = entry.get("title", "").strip()
        main = re.search(r"(?is)<main[^>]*>(.*?)</main>", text)
        if main:
            content = re.sub(r'(?is)<nav class="navbar sub.*?</nav>', "", main.group(1))
            wrapped = WRAPPER.match(content)
            if wrapped:
                content = wrapped.group(1)
        else:
            body = re.search(r"(?is)<body[^>]*>(.*?)</body>", text)
            content = body.group(1) if body else text
            content = re.sub(r"(?is)<!DOCTYPE[^>]*>|<html[^>]*>|</html>|<head>.*?</head>|<head>|<meta[^>]*>|<body[^>]*>|</body>", "", content)
        h1 = re.search(r"(?is)<h1[^>]*>(.*?)</h1>", content)
        if h1:
            title = title or re.sub(r"<[^>]+>", "", h1.group(1)).strip()
            content = content[: h1.start()] + content[h1.end():]
        title = TITLE_OVERRIDES.get(path) or title or humanize(path)
        content = re.sub(r"\n\s*\n+", "\n", rewrite(path, content)).strip()
        out_pages.append({"route": route_for(path), "title": title, "source": BASE + path, "content_html": content})

    data = {"lead": LEAD, "nav": NAV, "pages": out_pages}
    (ROOT / "src/data/labinfo.json").write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"\nWrote {len(out_pages)} pages to src/data/labinfo.json and {copied} files to public{PREFIX}")
    if remote_only:
        print("Too large to commit, linked to the live server:", ", ".join(sorted(remote_only)))
    for page, link in report["unlinked"]:
        print(f"Unlinked (404 on live site): {page} -> {link}")
    for page, link in report["removed"]:
        print(f"Removed image (404 on live site): {page} -> {link}")
    for link in sorted(report["live"]):
        print(f"Kept pointing at live server: {link}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--mirror", type=Path, help="directory for the raw download (default: a temporary directory)")
    args = parser.parse_args()
    mirror = args.mirror or Path(tempfile.mkdtemp(prefix="sccn-labinfo-"))
    mirror.mkdir(parents=True, exist_ok=True)
    print(f"Crawling {BASE}{PREFIX} into {mirror}")
    pages, assets = crawl(mirror)
    import_section(pages, assets)


if __name__ == "__main__":
    main()
