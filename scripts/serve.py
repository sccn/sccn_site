#!/usr/bin/env python3
"""Serve dist/ locally, honoring the baked GitHub Pages URL prefix.

build_site.py bakes the prefix from ../.baseurl into dist (recorded in
dist/.baseurl). This server strips it from incoming requests, so the baked
site previews correctly at both / and /<prefix>/ — matching how GitHub
Pages will serve it.

Usage:  python3 scripts/serve.py [port]      (default port 8173)
"""

import os
import sys
import urllib.parse
from functools import partial
from http.server import HTTPServer, SimpleHTTPRequestHandler

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST = os.path.join(ROOT, "dist")


def _load_baseurl():
    try:
        with open(os.path.join(DIST, ".baseurl"), encoding="utf-8") as fh:
            prefix = fh.read().strip().strip("/")
    except OSError:
        return ""
    return f"/{prefix}" if prefix else ""


BASEURL = _load_baseurl()


class PrefixHandler(SimpleHTTPRequestHandler):
    def send_head(self):
        if BASEURL:
            parts = urllib.parse.urlsplit(self.path)
            if parts.path == BASEURL or parts.path.startswith(BASEURL + "/"):
                stripped = parts.path[len(BASEURL):] or "/"
                self.path = urllib.parse.urlunsplit(
                    ("", "", stripped, parts.query, ""))
        return super().send_head()

    def send_header(self, keyword, value):
        # Keep redirects (e.g. directory 301s) inside the prefixed URL space.
        if (BASEURL and keyword == "Location"
                and value.startswith("/") and not value.startswith("//")):
            value = BASEURL + value
        super().send_header(keyword, value)

    def list_directory(self, path):
        # GitHub Pages serves no directory listings; mirror that in preview.
        self.send_error(404, "File not found")
        return None


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8173
    server = HTTPServer(("127.0.0.1", port), partial(PrefixHandler, directory=DIST))
    print(f"Serving {DIST}")
    print(f"  http://127.0.0.1:{port}{BASEURL}/   (Ctrl-C to stop)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
