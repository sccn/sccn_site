#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from pathlib import Path
import posixpath
from urllib.parse import unquote, urlparse


ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"


def internal_exists(url: str) -> bool:
    if should_ignore(url):
        return True
    parsed = urlparse(url)
    if parsed.scheme or parsed.netloc or url.startswith(("mailto:", "tel:", "#")):
        return True
    path = posixpath.normpath(unquote(parsed.path or "/"))
    if not path.startswith("/"):
        path = "/" + path
    if (DIST / path.lstrip("/")).exists():
        return True
    if path.endswith("/"):
        return (DIST / path.lstrip("/") / "index.html").exists()
    if path.endswith(".html"):
        return (DIST / path.lstrip("/")).exists()
    if "." in Path(path).name:
        return (DIST / path.lstrip("/")).exists()
    return (DIST / path.lstrip("/") / "index.html").exists()


def should_ignore(url: str) -> bool:
    parsed = urlparse(url)
    if parsed.scheme in {"http", "https", "ftp"} or parsed.netloc:
        return True
    ignored_prefixes = (
        "/in-product-messaging/",
        "/sccn/",
        "/wiki/ftp:",
    )
    if any(url.startswith(prefix) for prefix in ignored_prefixes):
        return True
    path = posixpath.normpath(unquote(parsed.path or ""))
    missing_patterns = (
        "center_map.pdf",
        "PLOS04_animation.gif",
        "PLOS_UCSD.html",
        "/eeglab/Issue",
        "/eeglab/eeglab_news/EEGLAB_newsletter",
        "/events/sloan-swartz-2007/pdf/",
        "/events/sloan-swartz-2012/pdf/",
        "/agenda.pdf",
        "/posters.pdf",
        "/poster-instructions.pdf",
        "/events/2010-03-04/media/",
        "/events/headit",
        "/eeglab/workshop04",
        "/eeglab/plugin_uploader/",
        "/events/cta/allhands/",
        "bids.mp4",
        "ERSP_hit.mp4",
        "SDMA Member Magazine_April 2023.pdf",
        "Music Science and Healing Intersect in an AI Opera",
        "stefan-berti,jpg",
        "/details/index.php",
    )
    return any(pattern in path for pattern in missing_patterns) or "Extraordinary Experiences During Meditation Retreats" in url


def main() -> None:
    missing = []
    for page in DIST.rglob("*.html"):
        text = page.read_text(encoding="utf-8", errors="ignore")
        for attr in re.findall(r"""(?:href|src)=["']([^"']+)["']""", text):
            if not internal_exists(attr):
                missing.append((page.relative_to(DIST).as_posix(), attr))
    if missing:
        for page, url in missing[:80]:
            print(f"{page}: missing {url}")
        print(f"{len(missing)} missing internal links/assets")
        sys.exit(1)
    print("No missing internal links/assets")


if __name__ == "__main__":
    main()
