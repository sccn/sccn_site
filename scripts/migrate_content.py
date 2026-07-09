#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import shutil
from html import escape
from pathlib import Path, PurePosixPath

from lxml import html


ROOT = Path(__file__).resolve().parents[2]
SITE = ROOT / "sccn3"
SOURCE = ROOT / "sccn.ucsd.edu_modified"

NAVIGATION = [
    {"label": "People", "url": "/people/"},
    {"label": "Research", "url": "/projects/"},
    {"label": "Methods", "url": "/methods/"},
    {"label": "Publications", "url": "/publications/"},
    {"label": "News", "url": "/news-events/"},
    {"label": "Visit", "url": "/visit/"},
]

MAJOR_SOURCE_FILES = {
    "index.html",
    "people/index.html",
    "people/former.html",
    "people/join.html",
    "projects.html",
    "methods/index.html",
    "publications.html",
    "news/index.html",
    "news-events/index.html",
    "visit/index.html",
}


def ensure_dirs() -> None:
    for rel in [
        "src/data",
        "public",
        "data/publications",
        "data/pubmed/raw",
    ]:
        (SITE / rel).mkdir(parents=True, exist_ok=True)


def text_content(node) -> str:
    return " ".join(" ".join(node.itertext()).split())


def parse_html(path: Path):
    return html.fromstring(path.read_text(encoding="utf-8", errors="ignore"))


def clean_link(url: str | None, base_dir: str = "") -> str:
    if not url:
        return ""
    url = url.strip()
    if (
        url.startswith(("http://", "https://", "mailto:", "tel:", "#", "javascript:"))
        or url.startswith("data:")
    ):
        return url
    if url.startswith("/"):
        return normalize_internal(url)
    normalized = PurePosixPath("/", base_dir, url).as_posix()
    return normalize_internal(normalized)


def normalize_internal(url: str) -> str:
    if not url or url.startswith(("http://", "https://", "mailto:", "tel:", "#")):
        return url
    if "#" in url:
        path, frag = url.split("#", 1)
        suffix = "#" + frag
    else:
        path, suffix = url, ""
    if "?" in path:
        path, query = path.split("?", 1)
        suffix = "?" + query + suffix
    path = PurePosixPath(path).as_posix()
    replacements = {
        "/projects.html": "/projects/",
        "/publications.html": "/publications/",
        "/people/former.html": "/people/alumni/",
        "/people/join.html": "/people/join/",
        "/news/index.php": "/news/",
        "/news/index.php.html": "/news/",
        "/contact/index.php": "/contact/",
        "/contact/index.php.html": "/contact/",
    }
    return replacements.get(path, path) + suffix


def rewrite_fragment(node, source_rel: str):
    base_dir = str(PurePosixPath(source_rel).parent)
    if base_dir == ".":
        base_dir = ""
    for element in node.xpath(".//*[@src]"):
        element.set("src", clean_link(element.get("src"), base_dir))
    for element in node.xpath(".//*[@href]"):
        element.set("href", clean_link(element.get("href"), base_dir))
    for bad in node.xpath(".//script|.//style|.//form[contains(@action, '/search')]"):
        parent = bad.getparent()
        if parent is not None:
            parent.remove(bad)
    return node


def fragment_html(node, source_rel: str) -> str:
    clone = html.fromstring(html.tostring(node, encoding="unicode"))
    rewrite_fragment(clone, source_rel)
    return html.tostring(clone, encoding="unicode", method="html")


def inner_html(node, source_rel: str) -> str:
    clone = html.fromstring(html.tostring(node, encoding="unicode"))
    rewrite_fragment(clone, source_rel)
    return "".join(html.tostring(child, encoding="unicode", method="html") for child in clone)


def page_title(doc, fallback: str) -> str:
    h1 = doc.xpath("//main//h1")
    if h1:
        title = text_content(h1[0])
        if title:
            return title
    title = doc.xpath("//title/text()")
    return title[0].strip() if title else fallback


def copy_assets() -> dict:
    public_dir = SITE / "public"
    if public_dir.exists():
        shutil.rmtree(public_dir)
    public_dir.mkdir(parents=True, exist_ok=True)
    manifest = {}
    for path in SOURCE.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() in {".html", ".php", ".py", ".pyc", ".log"}:
            continue
        if "__pycache__" in path.parts:
            continue
        rel = path.relative_to(SOURCE)
        target = SITE / "public" / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)
        manifest[str(rel)] = "/" + rel.as_posix()
    shutil.copy2(SITE / "src/styles/site.css", SITE / "public/assets-site.css")
    shutil.copy2(SITE / "src/scripts/site.js", SITE / "public/assets-site.js")
    aliases = {
        SOURCE / "eeglab/images/400px-Eeglab_small.jpg": SITE / "public/images/400px-Eeglab_small.jpg",
        SOURCE / "facilities/images/SDSC_building.jpg": SITE / "public/images/SDSC_building.jpg",
        Path("/Users/arno/Doc2/Screen_captures/2013/eeglab_small.png"): SITE / "public/images/eeglab_small.png",
        Path("/Users/arno/Downloads/eegdash_long (1).svg"): SITE / "public/images/eegdash_long.svg",
        SITE.parent / "sccn1/assets/img/eegprep.jpg": SITE / "public/images/eegprep.jpg",
    }
    for source, target in aliases.items():
        if source.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
            manifest[str(target.relative_to(SITE / "public"))] = "/" + target.relative_to(SITE / "public").as_posix()
    workshop_images = SOURCE / "events/BrainConnectivityWorkshop2015/images"
    if workshop_images.exists():
        for source in workshop_images.iterdir():
            if source.is_file():
                target = SITE / "public/events/images" / source.name
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, target)
                manifest[str(target.relative_to(SITE / "public"))] = "/" + target.relative_to(SITE / "public").as_posix()
    manifest["assets-site.css"] = "/assets-site.css"
    manifest["assets-site.js"] = "/assets-site.js"
    return manifest


def extract_people() -> list[dict]:
    doc = parse_html(SOURCE / "people/index.html")
    dirs = doc.xpath("//div[contains(concat(' ', normalize-space(@class), ' '), ' tab-pane ') and @id='current']//div[contains(concat(' ', normalize-space(@class), ' '), ' directory ')]")
    if not dirs:
        return []
    directory = dirs[0]
    groups = []
    current_group = None
    for child in directory:
        if not isinstance(child.tag, str):
            continue
        if child.tag.lower() == "h2":
            current_group = {"group": text_content(child), "people": []}
            groups.append(current_group)
            continue
        if current_group is None:
            continue
        for article in child.xpath(".//div[contains(concat(' ', normalize-space(@class), ' '), ' article ')]"):
            h3 = article.xpath(".//h3[1]")
            if not h3:
                continue
            name = text_content(h3[0])
            link_nodes = h3[0].xpath(".//a[@href]") or article.xpath(".//a[h3][@href]")
            profile = clean_link(link_nodes[0].get("href"), "people") if link_nodes else ""
            img = article.xpath(".//img[1]")
            image = clean_link(img[0].get("src"), "people") if img else "/people/images/generic.jpg"
            alt = img[0].get("alt") if img else name
            paragraphs = [text_content(p) for p in article.xpath("./p") if text_content(p)]
            role = ""
            for paragraph in paragraphs:
                if "@" not in paragraph and not re.fullmatch(r"\d{4}.*", paragraph):
                    role = paragraph
                    break
            interests = [text_content(li) for li in article.xpath(".//li") if text_content(li)]
            email_nodes = article.xpath(".//a[starts-with(@href, 'mailto:')]")
            email = email_nodes[0].get("href").replace("mailto:", "") if email_nodes else ""
            current_group["people"].append(
                {
                    "name": name,
                    "role": role,
                    "profile": profile,
                    "email": email,
                    "image": image,
                    "alt": alt or name,
                    "interests": interests[:5],
                    "notes": paragraphs,
                }
            )
    return groups


def extract_alumni() -> list[dict]:
    doc = parse_html(SOURCE / "people/former.html")
    dirs = doc.xpath("//div[contains(concat(' ', normalize-space(@class), ' '), ' directory ')]")
    directory = dirs[0] if dirs else doc.xpath("//main")[0]
    groups = []
    current_group = None
    for child in directory:
        if not isinstance(child.tag, str):
            continue
        if child.tag.lower() == "h2":
            current_group = {"group": text_content(child), "people": []}
            groups.append(current_group)
            continue
        if current_group is None:
            continue
        for article in child.xpath(".//div[contains(concat(' ', normalize-space(@class), ' '), ' article ')]"):
            h3 = article.xpath(".//h3[1]")
            if not h3:
                continue
            img = article.xpath(".//img[1]")
            current_group["people"].append(
                {
                    "name": text_content(h3[0]),
                    "image": clean_link(img[0].get("src"), "people") if img else "/people/images/generic.jpg",
                    "text": text_content(article),
                    "html": inner_html(article, "people/former.html"),
                }
            )
    return groups


def extract_methods() -> list[dict]:
    doc = parse_html(SOURCE / "methods/index.html")
    image_map = {
        "EEGLAB": "/images/eeglab_small.png",
        "NEMAR": "/images/nemar.svg",
        "HED": "/images/hed-logo-transparent.png",
        "EEGDash": "/images/eegdash_long.svg",
        "EEGPrep": "/images/eegprep.jpg",
    }
    methods = []
    for card in doc.xpath("//main//*[contains(concat(' ', normalize-space(@class), ' '), ' card ')]"):
        h2 = card.xpath(".//h2[1]")
        if not h2:
            continue
        title = text_content(h2[0])
        body = card.xpath(".//*[contains(concat(' ', normalize-space(@class), ' '), ' card-body ')]")
        body_node = body[0] if body else card
        link = body_node.xpath(".//a[@href][1]")
        methods.append(
            {
                "title": title,
                "image": image_map.get(title, "/images/sccn.svg"),
                "body_html": inner_html(body_node, "methods/index.html"),
                "summary": text_content(body_node)[:360],
                "url": clean_link(link[0].get("href"), "methods") if link else "",
            }
        )
    return methods


def extract_research() -> list[dict]:
    doc = parse_html(SOURCE / "projects.html")
    entries = []
    for p in doc.xpath("//main//p[contains(concat(' ', normalize-space(@class), ' '), ' card-text ')]"):
        full = text_content(p)
        if not full or len(full) < 40:
            continue
        strong = p.xpath(".//strong[1]")
        title = text_content(strong[0]).rstrip(".") if strong else full[:80].rstrip(".")
        entries.append(
            {
                "title": title,
                "summary": full,
                "body_html": fragment_html(p, "projects.html"),
                "image": "/projects/images/EEG_Source_Imag_on_Cortex.png",
            }
        )
    return entries


def extract_news() -> list[dict]:
    doc = parse_html(SOURCE / "news/index.html")
    main = doc.xpath("//main")[0]
    entries = []
    fallback_images = [
        "/news/2021-09-20/media/bids.png",
        "/projects/images/EEG_Source_Imag_on_Cortex.png",
        "/events/media/EEGOcean_hiperspace2.JPG",
        "/people/images/sccn-2024.jpg",
        "/images/sccn.jpg",
    ]
    fallback_index = 0
    h2s = main.xpath(".//h2")
    for h2 in h2s:
        title_text = text_content(h2)
        if "—" not in title_text and "&mdash;" not in html.tostring(h2, encoding="unicode"):
            continue
        match = re.match(r"(?P<date>[A-Za-z]+\s+\d{1,2},\s+\d{4}|\d{4}-\d{2}-\d{2})\s+[—-]\s+(?P<title>.+)", title_text)
        if match:
            date = match.group("date")
            title = match.group("title")
        else:
            parts = re.split(r"\s+[—-]\s+", title_text, maxsplit=1)
            if len(parts) != 2:
                continue
            date, title = parts
        nodes = []
        current = h2.getnext()
        while current is not None and (not isinstance(current.tag, str) or current.tag.lower() != "h2"):
            nodes.append(current)
            current = current.getnext()
        wrapper = html.Element("div")
        for node in nodes:
            wrapper.append(html.fromstring(html.tostring(node, encoding="unicode")))
        rewrite_fragment(wrapper, "news/index.html")
        summary = text_content(wrapper)
        if len(summary) > 340:
            summary = summary[:337].rsplit(" ", 1)[0] + "..."
        image_node = wrapper.xpath(".//img[1]")
        image = image_node[0].get("src") if image_node else fallback_images[fallback_index % len(fallback_images)]
        if not image_node:
            fallback_index += 1
        link_node = wrapper.xpath(".//a[contains(translate(normalize-space(.), 'MORE', 'more'), 'more')][@href] | .//a[@href][1]")
        url = clean_link(link_node[0].get("href"), "news") if link_node else ""
        entries.append(
            {
                "date": date,
                "title": title,
                "summary": summary or title,
                "image": image,
                "url": url,
                "body_html": inner_html(wrapper, "news/index.html"),
            }
        )
    for entry in entries:
        if entry["date"] == "September 20, 2021":
            entry["url"] = "/news/2021-09-20/"
            if entry["summary"] == entry["title"]:
                full = SOURCE / "news/2021-09-20/index.html"
                if full.exists():
                    full_doc = parse_html(full)
                    paragraphs = [text_content(p) for p in full_doc.xpath("//main//p") if text_content(p)]
                    if paragraphs:
                        entry["summary"] = paragraphs[0][:337].rsplit(" ", 1)[0] + "..."
    extra_events = [
        {
            "date": "November 19, 2025",
            "title": "SFN 2025 Open House",
            "summary": "SCCN event listing preserved from the News & Events page.",
            "image": "/people/images/sccn-2024.jpg",
            "url": "/events/2025-11-19/",
            "body_html": "",
        },
        {
            "date": "November 11-15, 2023",
            "title": "Neuroscience 2023",
            "summary": "SCCN event listing preserved from the News & Events page.",
            "image": "/events/media/EEGOcean_hiperspace2.JPG",
            "url": "/events/2023-11-11/",
            "body_html": "",
        },
    ]
    return extra_events + entries


def extract_legacy_pages() -> list[dict]:
    pages = []
    for path in sorted(SOURCE.rglob("*.html")):
        rel = path.relative_to(SOURCE).as_posix()
        if rel in MAJOR_SOURCE_FILES:
            continue
        doc = parse_html(path)
        main = doc.xpath("//main")
        if main:
            content = inner_html(main[0], rel)
        else:
            body = doc.xpath("//body")
            content = inner_html(body[0], rel) if body else ""
        if not text_content(html.fromstring(f"<div>{content}</div>")):
            continue
        pages.append(
            {
                "source": rel,
                "title": page_title(doc, rel),
                "route": legacy_route(rel),
                "content_html": content,
            }
        )
    return pages


def legacy_route(rel: str) -> str:
    route = "/" + rel
    if route.endswith("/index.html"):
        route = route[: -len("index.html")]
    route = normalize_internal(route)
    return route


def extract_simple_content(rel: str) -> dict:
    doc = parse_html(SOURCE / rel)
    main = doc.xpath("//main")
    content = inner_html(main[0], rel) if main else ""
    return {"title": page_title(doc, rel), "content_html": content}


def make_manual_bib() -> None:
    doc = parse_html(SOURCE / "publications.html")
    entries = []
    seen = set()
    for li in doc.xpath("//main//li"):
        text = text_content(li)
        if len(text) < 30:
            continue
        year_match = re.search(r"\b(19|20)\d{2}\b", text)
        year = year_match.group(0) if year_match else ""
        link = li.xpath(".//a[@href][1]")
        url = clean_link(link[0].get("href"), "") if link else ""
        title = text_content(link[0]) if link else text[:90]
        author = text[: year_match.start()].strip(" .,") if year_match else ""
        key_base = re.sub(r"[^A-Za-z0-9]+", "", (author.split(",")[0] if author else "sccn") + year + title[:24])
        key = key_base or f"sccn{len(entries)}"
        original_key = key
        i = 2
        while key in seen:
            key = f"{original_key}{i}"
            i += 1
        seen.add(key)
        entries.append(
            "@misc{"
            + key
            + ",\n"
            + f"  title = {{{bib_escape(title)}}},\n"
            + (f"  author = {{{bib_escape(author)}}},\n" if author else "")
            + (f"  year = {{{year}}},\n" if year else "")
            + (f"  url = {{{bib_escape(url)}}},\n" if url else "")
            + f"  note = {{{bib_escape(text)}}}\n"
            + "}\n"
        )
    (SITE / "data/publications/manual.bib").write_text("\n".join(entries), encoding="utf-8")


def bib_escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace("{", "\\{").replace("}", "\\}").replace("\n", " ")


def write_json(rel: str, data) -> None:
    path = SITE / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def write_inventory(assets: dict, legacy_pages: list[dict]) -> None:
    source_pages = sorted(path.relative_to(SOURCE).as_posix() for path in SOURCE.rglob("*.html"))
    lines = [
        "# SCCN3 Content Inventory",
        "",
        f"Source: `{SOURCE.name}`",
        f"Total source HTML pages: {len(source_pages)}",
        f"Copied static assets: {len(assets)}",
        "",
        "## Top Menu",
        "",
    ]
    lines.extend(f"- {item['label']}: `{item['url']}`" for item in NAVIGATION)
    lines.extend(["", "## High-Priority Reworked Pages", ""])
    lines.extend(
        [
            "- `/` from `index.html`",
            "- `/people/` from current members in `people/index.html`",
            "- `/people/alumni/` from `people/former.html`",
            "- `/people/join/` from `people/join.html`",
            "- `/projects/` from `projects.html`",
            "- `/methods/` from `methods/index.html`",
            "- `/publications/` from generated BibTeX and preserved manual entries",
            "- `/news-events/` from `news/index.html` and `news-events/index.html`",
            "- `/visit/` from `visit/index.html`",
        ]
    )
    lines.extend(["", "## Legacy Pages Rewrapped", ""])
    lines.extend(f"- `{page['source']}` -> `{page['route']}`" for page in legacy_pages)
    lines.append("")
    (SITE / "content-inventory.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    ensure_dirs()
    assets = copy_assets()
    people = extract_people()
    alumni = extract_alumni()
    methods = extract_methods()
    research = extract_research()
    news = extract_news()
    legacy_pages = extract_legacy_pages()
    redirects = {
        "/projects.html": "/projects/",
        "/publications.html": "/publications/",
        "/people/former.html": "/people/alumni/",
        "/people/join.html": "/people/join/",
        "/news/index.php.html": "/news/",
        "/news/index.php": "/news/",
        "/contact/index.php.html": "/contact/",
    }
    write_json("src/data/navigation.json", NAVIGATION)
    write_json("src/data/assets.json", assets)
    write_json("src/data/people.json", people)
    write_json("src/data/alumni.json", alumni)
    write_json("src/data/methods.json", methods)
    write_json("src/data/research.json", research)
    write_json("src/data/news.json", news)
    write_json("src/data/legacy_pages.json", legacy_pages)
    write_json("src/data/redirects.json", redirects)
    write_json("src/data/join.json", extract_simple_content("people/join.html"))
    write_json("src/data/visit.json", extract_simple_content("visit/index.html"))
    make_manual_bib()
    write_inventory(assets, legacy_pages)
    print(f"Migrated {sum(len(group['people']) for group in people)} current people")
    print(f"Migrated {sum(len(group['people']) for group in alumni)} alumni")
    print(f"Migrated {len(research)} research entries, {len(methods)} methods, {len(news)} news/events")
    print(f"Rewrapped {len(legacy_pages)} legacy pages")


if __name__ == "__main__":
    main()
