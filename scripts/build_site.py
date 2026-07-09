#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import shutil
from datetime import date
from html import escape
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
PUBLIC = ROOT / "public"
DATA = ROOT / "src/data"
STATE_FILE = ".baseurl"


def normalize_baseurl(prefix: str) -> str:
    """Return '' for domain-root hosting, otherwise '/repo-name'."""
    prefix = prefix.strip().strip("/")
    return f"/{prefix}" if prefix else ""


def rebase_urls(data: bytes, old: bytes, new: bytes) -> bytes:
    """Move root-absolute HTML URL attributes from one prefix to another."""
    pattern = re.compile(
        rb'(?<![-\w])((?:href|src|action)="|content="\d+;\s*url=)'
        + re.escape(old)
        + rb'(/(?!/))'
    )
    return pattern.sub(lambda match: match.group(1) + new + match.group(2), data)


def bake_baseurl(site_dir: Path, prefix: str) -> int:
    """Bake the configured Pages prefix into generated HTML files."""
    state_path = site_dir / STATE_FILE
    old = normalize_baseurl(state_path.read_text().strip() if state_path.exists() else "")
    new = normalize_baseurl(prefix)
    changed = 0
    if old != new:
        for path in sorted(site_dir.rglob("*.html")):
            data = path.read_bytes()
            out = rebase_urls(data, old.encode(), new.encode())
            if out != data:
                path.write_bytes(out)
                changed += 1
    state_path.write_text(f"{new}\n", encoding="utf-8")
    return changed


def load_json(name: str, default=None):
    path = DATA / name
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def html_escape(value: str) -> str:
    return escape(value or "", quote=True)


def strip_tags(fragment: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", fragment or "")).strip()


def slug_text(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (value or "").lower()).strip()


def ensure_dist() -> None:
    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir(parents=True)
    if PUBLIC.exists():
        for item in PUBLIC.iterdir():
            target = DIST / item.name
            if item.is_dir():
                shutil.copytree(item, target)
            else:
                shutil.copy2(item, target)
    source_css = ROOT / "src/styles/site.css"
    source_js = ROOT / "src/scripts/site.js"
    if source_css.exists():
        shutil.copy2(source_css, DIST / "assets-site.css")
    if source_js.exists():
        shutil.copy2(source_js, DIST / "assets-site.js")
    pub_data = ROOT / "data/publications"
    if pub_data.exists():
        target = DIST / "data/publications"
        target.mkdir(parents=True, exist_ok=True)
        for item in pub_data.glob("*.bib"):
            shutil.copy2(item, target / item.name)


def write_page(route: str, html: str) -> None:
    route = route.split("#", 1)[0]
    if route.endswith("/"):
        path = DIST / route.lstrip("/") / "index.html"
    elif route.endswith(".html"):
        path = DIST / route.lstrip("/")
    else:
        path = DIST / route.lstrip("/") / "index.html"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(html, encoding="utf-8")


def render_header(active: str = "") -> str:
    nav = load_json("navigation.json", [])
    links = []
    for item in nav:
        current = ' aria-current="page"' if active == item["url"] else ""
        links.append(f'<a href="{item["url"]}"{current}>{html_escape(item["label"])}</a>')
    return f"""
    <a class="skip-link" href="#main">Skip to main content</a>
    <header class="site-header">
      <div class="nav-shell">
        <a class="brand" href="/" aria-label="SCCN home"><img src="/images/sccn.svg" alt="SCCN"></a>
        <button class="nav-toggle" type="button" data-nav-toggle aria-controls="primary-nav" aria-expanded="false"><span></span><span class="sr-only">Menu</span></button>
        <nav class="primary-nav" id="primary-nav" data-primary-nav aria-label="Primary navigation">
          {''.join(links)}
        </nav>
        <form class="header-search" action="/search/" method="get" data-header-search>
          <button class="icon-button" type="button" data-search-toggle aria-label="Open search" aria-expanded="false">
            <svg width="19" height="19" viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="7"></circle><path d="m20 20-3.5-3.5"></path></svg>
          </button>
          <input class="search-input" data-search-input name="q" type="search" autocomplete="off" aria-label="Search SCCN">
        </form>
      </div>
    </header>
    """


def render_footer() -> str:
    return """
    <footer class="site-footer">
      <div class="footer-grid">
        <div>
          <strong>Swartz Center for Computational Neuroscience</strong><br>
          Institute for Neural Computation, UC San Diego<br>
          9500 Gilman Drive # 0559, La Jolla, CA 92093-0559
        </div>
        <div>
          Office: 858-822-7534 &middot; Fax: 858-822-7556<br>
          <a href="/methods/">Methods</a> &middot;
          <a href="/news-events/">News</a> &middot;
          <a href="/visit/">Visit</a> &middot;
          <a href="/login/">Internal</a>
        </div>
      </div>
    </footer>
    """


def render_page(title: str, content: str, active: str = "", description: str = "") -> str:
    desc = description or "Swartz Center for Computational Neuroscience at UC San Diego."
    return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta name="description" content="{html_escape(desc)}">
    <meta name="ORGANIZATION" content="University of California, San Diego">
    <meta name="SITE" content="Swartz Center for Computational Neuroscience">
    <title>{html_escape(title)} - SCCN</title>
    <link rel="icon" href="/images/favicon.ico">
    <link rel="stylesheet" href="/assets-site.css">
  </head>
  <body>
    {render_header(active)}
    <main id="main" class="main">
      {content}
    </main>
    {render_footer()}
    <script src="/assets-site.js" defer></script>
  </body>
</html>
"""


def render_home() -> tuple[str, str]:
    people = load_json("people.json", [])
    methods = load_json("methods.json", [])
    research = load_json("research.json", [])[:3]
    news = load_json("news.json", [])[:3]
    pub_count = len(load_json("publications.json", []) or [])
    people_count = sum(len(group["people"]) for group in people)
    content = f"""
      <section class="hero">
        <div class="hero-grid container">
          <div>
            <p class="eyebrow">Open EEG methods and infrastructure</p>
            <h1>Swartz Center for Computational Neuroscience</h1>
            <p class="lead">SCCN develops open electrophysiological methods, interoperable data infrastructure, and computational neuroscience research linking neural dynamics to cognition, behavior, clinical state, and human experience.</p>
            <div class="button-row">
              <a class="button" href="/methods/">Explore methods</a>
              <a class="button secondary" href="/projects/">Research themes</a>
            </div>
          </div>
          <figure class="hero-media">
            <img src="/people/images/sccn-2024.jpg" alt="SCCN group">
          </figure>
        </div>
      </section>
      <section class="section">
        <div class="container image-band text-only">
          <div>
            <p class="eyebrow">Computational neuroscience laboratory</p>
            <h2>A full stack for EEG science</h2>
            <p>SCCN connects EEGLAB, NEMAR, HED, shared datasets, scalable computation, independent component analysis, source modeling, quality control, and reproducible workflows into infrastructure for mature data-intensive EEG research.</p>
            <div class="button-row">
              <a class="button" href="/publications/">Browse publications</a>
              <a class="button secondary" href="/people/">Meet the team</a>
            </div>
          </div>
        </div>
      </section>
      <section class="section band">
        <div class="container">
          <div class="section-header">
            <div>
              <p class="eyebrow">Methods</p>
              <h2>Open tools and data systems</h2>
            </div>
            <p>Core SCCN methods support analysis, annotation, data access, and reproducible EEG workflows.</p>
          </div>
          <div class="method-grid">
            {''.join(render_method_card(item, show_image=False, show_icon=True) for item in methods[:3])}
          </div>
        </div>
      </section>
      <section class="section">
        <div class="container">
          <div class="section-header">
            <div>
              <p class="eyebrow">Research</p>
              <h2>Research directions</h2>
            </div>
            <a class="button secondary" href="/projects/">Explore all research</a>
          </div>
          <div class="research-grid">
            {''.join(render_research_card(item) for item in research)}
          </div>
        </div>
      </section>
      <section class="section band">
        <div class="container feature-grid">
          <article class="feature">
            <h2>{people_count}</h2>
            <p class="metadata">Current members in the SCCN directory</p>
            <p><a href="/people/">View People</a></p>
          </article>
          <article class="feature">
            <h2>{pub_count}</h2>
            <p class="metadata">Publication records from preserved content and PubMed</p>
            <p><a href="/publications/">Search Publications</a></p>
          </article>
          <article class="feature">
            <h2>EEGLAB + NEMAR</h2>
            <p class="metadata">Open methods, data, annotation, and computing</p>
            <p><a href="/methods/">View Methods</a></p>
          </article>
        </div>
      </section>
      <section class="section">
        <div class="container">
          <div class="section-header">
            <div>
              <p class="eyebrow">News</p>
              <h2>News and events</h2>
            </div>
            <a class="button secondary" href="/news-events/">All News</a>
          </div>
          <div class="news-grid">
            {''.join(render_news_card(item, show_image=False) for item in news)}
          </div>
        </div>
      </section>
    """
    return "/", render_page("Swartz Center for Computational Neuroscience", content, "/", "Open EEG methods and computational neuroscience research at UC San Diego.")


def render_method_icon(item: dict) -> str:
    title = item.get("title", "Method")
    key = re.sub(r"[^a-z0-9]+", "", title.lower())
    image = item.get("image", "/images/sccn.svg")
    return f'<span class="method-icon method-icon-{html_escape(key or "method")}" aria-hidden="true"><img src="{html_escape(image)}" alt=""></span>'


def render_method_card(item: dict, show_image: bool = True, show_icon: bool = False) -> str:
    url = item.get("url") or "/methods/"
    image = ""
    if show_image:
        image = f'<img src="{html_escape(item.get("image", "/images/sccn.svg"))}" alt="{html_escape(item.get("title", "Method"))}">'
    icon = render_method_icon(item) if show_icon else ""
    return f"""
      <article class="method-card">
        {image}
        {icon}
        <h3>{html_escape(item.get('title', 'Method'))}</h3>
        <p>{html_escape(item.get('summary', '')[:220])}</p>
        {f'<p><a href="{html_escape(url)}">Learn more</a></p>' if url else ''}
      </article>
    """


def render_research_card(item: dict) -> str:
    return f"""
      <article class="research-card">
        <div class="body">
          <h3>{html_escape(item.get('title', 'Research'))}</h3>
          <p>{html_escape(item.get('summary', '')[:260])}</p>
        </div>
      </article>
    """


def render_news_card(item: dict, show_image: bool = True) -> str:
    title = html_escape(item.get("title", "News"))
    url = item.get("url") or "/news-events/"
    link = f'<a href="{html_escape(url)}">{title}</a>' if url else title
    image = ""
    if show_image:
        image = f'<img src="{html_escape(item.get("image", "/people/images/sccn-2024.jpg"))}" alt="">'
    return f"""
      <article class="news-card">
        {image}
        <div class="body">
          <p class="metadata">{html_escape(item.get('date', ''))}</p>
          <h3>{link}</h3>
          <p class="summary">{html_escape(item.get('summary', ''))}</p>
        </div>
      </article>
    """


def render_people() -> tuple[str, str]:
    groups = load_json("people.json", [])
    count = sum(len(group["people"]) for group in groups)
    cards = []
    for group in groups:
        cards.append(f'<h2 class="group-heading">{html_escape(group["group"])}</h2>')
        cards.append('<div class="person-grid">')
        for person in group["people"]:
            cards.append(render_person_card(person))
        cards.append("</div>")
    content = f"""
      <section class="hero">
        <div class="container image-band">
          <img src="/people/images/sccn-2024.jpg" alt="SCCN group">
          <div>
            <p class="eyebrow">People</p>
            <h1>Current Members</h1>
            <p class="lead">SCCN brings together researchers, engineers, students, administrators, visitors, and collaborators working on open EEG methods, data systems, and neural dynamics.</p>
          </div>
        </div>
      </section>
      <section class="section">
        <div class="container">
          <div class="person-toolbar">
            <input class="filter-input" type="search" data-people-search placeholder="Search current members by name or title" aria-label="Search current members">
            <span class="metadata" data-people-count>{count} shown</span>
          </div>
          {''.join(cards)}
          <div class="bottom-links">
            <article class="legacy-card">
              <h2>Alumni</h2>
              <p>Former SCCN members are preserved in a separate archive page.</p>
              <p><a class="button secondary" href="/people/alumni/">View Alumni</a></p>
            </article>
            <article class="legacy-card">
              <h2>How to Join</h2>
              <p>Students interested in SCCN research and methods work can review current joining information.</p>
              <p><a class="button secondary" href="/people/join/">How to Join</a></p>
            </article>
          </div>
        </div>
      </section>
    """
    return "/people/", render_page("People", content, "/people/", "Current members of the Swartz Center for Computational Neuroscience.")


def render_person_card(person: dict) -> str:
    role = html_escape(person.get("role", ""))
    name = html_escape(person.get("name", ""))
    title = f'<a href="{html_escape(person["profile"])}">{name}</a>' if person.get("profile") else name
    search = slug_text(" ".join([person.get("name", ""), role]))
    return f"""
      <article class="person-card" data-person-card data-search="{html_escape(search)}">
        <img src="{html_escape(person.get('image', '/people/images/generic.jpg'))}" alt="{html_escape(person.get('alt') or person.get('name', ''))}">
        <div>
          <h3>{title}</h3>
          {f'<p class="role">{role}</p>' if role else ''}
        </div>
      </article>
    """


def render_alumni() -> tuple[str, str]:
    groups = load_json("alumni.json", [])
    parts = []
    total = 0
    for group in groups:
        total += len(group["people"])
        parts.append(f'<h2 class="group-heading">{html_escape(group["group"])}</h2>')
        parts.append('<div class="person-grid">')
        for person in group["people"]:
            search = slug_text(person.get("text", ""))
            parts.append(
                f"""
                <article class="person-card" data-person-card data-search="{html_escape(search)}">
                  <img src="{html_escape(person.get('image', '/people/images/generic.jpg'))}" alt="{html_escape(person.get('name', ''))}">
                  <div><h3>{html_escape(person.get('name', ''))}</h3><p>{html_escape(person.get('text', '')[:260])}</p></div>
                </article>
                """
            )
        parts.append("</div>")
    content = f"""
      <section class="hero"><div class="narrow"><p class="eyebrow">People</p><h1>Alumni</h1><p class="lead">Former SCCN members preserved from the source people directory.</p></div></section>
      <section class="section"><div class="container">
        <div class="person-toolbar"><input class="filter-input" type="search" data-people-search placeholder="Search alumni" aria-label="Search alumni"><span class="metadata" data-people-count>{total} shown</span></div>
        {''.join(parts)}
        <p><a class="button secondary" href="/people/">Back to current members</a></p>
      </div></section>
    """
    return "/people/alumni/", render_page("Alumni", content, "/people/")


def render_join() -> tuple[str, str]:
    join = load_json("join.json", {"content_html": ""})
    content = f"""
      <section class="hero"><div class="narrow"><p class="eyebrow">People</p><h1>How to Join SCCN</h1><p class="lead">Information for UC San Diego students interested in open EEG methods, data infrastructure, and computational neuroscience.</p></div></section>
      <section class="section"><div class="narrow legacy-content">{join.get('content_html', '')}<p><a class="button secondary" href="/people/">Back to People</a></p></div></section>
    """
    return "/people/join/", render_page("How to Join", content, "/people/")


def render_research() -> tuple[str, str]:
    entries = load_json("research.json", [])
    cards = "".join(render_research_card(entry) for entry in entries)
    content = f"""
      <section class="hero">
        <div class="container image-band">
          <img src="/projects/images/EEG_Source_Imag_on_Cortex.png" alt="EEG source imaging on cortex">
          <div><p class="eyebrow">Research</p><h1>Research</h1><p class="lead">SCCN research focuses on EEG and related electrophysiological signals as windows into neural dynamics, cognition, behavior, clinical state, and human experience.</p></div>
        </div>
      </section>
      <section class="section"><div class="container research-grid">{cards}</div></section>
    """
    return "/projects/", render_page("Research", content, "/projects/")


def render_methods() -> tuple[str, str]:
    methods = load_json("methods.json", [])
    content = f"""
      <section class="hero">
        <div class="container image-band plain-media">
          <img src="/images/eeglab_small.png" alt="EEGLAB interface">
          <div><p class="eyebrow">Methods</p><h1>Methods</h1><p class="lead">SCCN develops open, reproducible methods for electrophysiological data: metadata, interoperable formats, preprocessing, source modeling, quality control, data sharing, and large-scale computation.</p></div>
        </div>
      </section>
      <section class="section"><div class="container method-grid">{''.join(render_method_card(item) for item in methods)}</div></section>
    """
    return "/methods/", render_page("Methods", content, "/methods/")


def render_publications() -> tuple[str, str]:
    pubs = load_json("publications.json", []) or []
    generated = date.today().isoformat()
    rows = []
    for pub in pubs:
        rows.append(render_publication_row(pub))
    content = f"""
      <section class="hero"><div class="narrow"><p class="eyebrow">Publications</p><h1>Publications</h1><p class="lead">Search SCCN references generated from preserved publication content and reusable PubMed/BibTeX processing.</p></div></section>
      <section class="section"><div class="container">
        <div class="publication-toolbar">
          <input class="filter-input" type="search" data-publication-search placeholder="Search by title, author, journal, year, DOI, or PMID" aria-label="Search publications">
          <a class="button secondary" href="/data/publications/sccn_publications.bib">Download BibTeX</a>
        </div>
        <p class="metadata"><span data-publication-count>{len(pubs)} references</span> &middot; Generated {generated}</p>
        <div class="publication-list">{''.join(rows)}</div>
      </div></section>
    """
    return "/publications/", render_page("Publications", content, "/publications/")


def render_publication_row(pub: dict) -> str:
    search = slug_text(" ".join(str(pub.get(key, "")) for key in ["title", "authors", "journal", "year", "doi", "pmid", "abstract", "note"]))
    links = []
    if pub.get("pmid"):
        links.append(f'<a href="https://pubmed.ncbi.nlm.nih.gov/{html_escape(pub["pmid"])}/">PubMed</a>')
    if pub.get("doi"):
        links.append(f'<a href="https://doi.org/{html_escape(pub["doi"])}">DOI</a>')
    if pub.get("url") and not pub.get("pmid") and is_reasonable_publication_url(pub.get("url", "")):
        links.append(f'<a href="{html_escape(pub["url"])}">Source</a>')
    source = " ".join(part for part in [pub.get("journal", ""), pub.get("year", "")] if part)
    return f"""
      <article class="publication-row" data-publication-row data-search="{html_escape(search)}">
        <span class="year-chip">{html_escape(pub.get('year') or 'Archive')}</span>
        <p class="publication-title">{html_escape(pub.get('title', 'Untitled reference'))}</p>
        <p class="publication-authors">{html_escape(pub.get('authors', ''))}</p>
        <p class="publication-source">{html_escape(source)}</p>
        {f'<div class="publication-links">{"".join(links)}</div>' if links else ''}
      </article>
    """


def is_reasonable_publication_url(url: str) -> bool:
    parsed = urlparse(url)
    if parsed.scheme in {"http", "https"}:
        return True
    if " " in url:
        return False
    return url.startswith("/")


def render_news() -> tuple[str, str]:
    entries = load_json("news.json", [])
    content = f"""
      <section class="hero"><div class="narrow"><p class="eyebrow">News</p><h1>News &amp; Events</h1><p class="lead">Recent and archived SCCN news and events. Each item includes a summary and image; longer items link to full pages or external articles.</p></div></section>
      <section class="section"><div class="container news-grid">{''.join(render_news_card(item) for item in entries)}</div></section>
    """
    return "/news-events/", render_page("News & Events", content, "/news-events/")


def render_visit() -> tuple[str, str]:
    visit = load_json("visit.json", {"content_html": ""})
    visit_html = re.sub(
        r'\s*<h1>Visit SCCN</h1>\s*<p class="lead">.*?</p>',
        "",
        visit.get("content_html", ""),
        count=1,
        flags=re.S,
    )
    content = f"""
      <section class="hero"><div class="narrow"><p class="eyebrow">Visit</p><h1>Visit</h1><p class="lead">Location and contact information for SCCN at UC San Diego.</p></div></section>
      <section class="section"><div class="narrow legacy-content">{visit_html}</div></section>
    """
    return "/visit/", render_page("Visit", content, "/visit/")


def render_search() -> tuple[str, str]:
    content = """
      <section class="hero"><div class="narrow"><p class="eyebrow">Search</p><h1>Search SCCN</h1><p class="lead">Search people, research, methods, publications, news, and archive pages.</p></div></section>
      <section class="section"><div class="narrow">
        <form data-site-search-form class="publication-toolbar">
          <input class="filter-input" data-site-search-input type="search" name="q" placeholder="Search SCCN" aria-label="Search SCCN">
          <button class="button" type="submit">Search</button>
        </form>
        <div class="search-results" data-search-results></div>
      </div></section>
    """
    return "/search/", render_page("Search", content)


def render_legacy(page: dict) -> tuple[str, str]:
    content = f"""
      <section class="hero"><div class="narrow"><p class="eyebrow">Archive</p><h1>{html_escape(page.get('title', 'Archive'))}</h1><p class="lead">Preserved SCCN source content rendered in the SCCN3 site shell.</p></div></section>
      <section class="section"><div class="container legacy-content">{page.get('content_html', '')}</div></section>
    """
    return page["route"], render_page(page.get("title", "Archive"), content)


def render_redirect(target: str) -> str:
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta http-equiv="refresh" content="0; url={html_escape(target)}"><link rel="canonical" href="{html_escape(target)}"><title>Redirecting</title></head><body><p><a href="{html_escape(target)}">Continue</a></p></body></html>"""


def page_text_for_index(title: str, route: str, content: str) -> dict:
    text = strip_tags(content)
    return {
        "title": title,
        "url": route,
        "text": text,
        "excerpt": html_escape(text[:220] + ("..." if len(text) > 220 else "")),
    }


def main() -> None:
    ensure_dist()
    pages = [
        render_home(),
        render_people(),
        render_alumni(),
        render_join(),
        render_research(),
        render_methods(),
        render_publications(),
        render_news(),
        render_visit(),
        render_search(),
    ]
    for legacy in load_json("legacy_pages.json", []):
        route = legacy.get("route", "")
        if route in {route for route, _ in pages}:
            continue
        pages.append(render_legacy(legacy))

    search_index = []
    for route, html_text in pages:
        write_page(route, html_text)
        title = re.search(r"<title>(.*?) - SCCN</title>", html_text)
        search_index.append(page_text_for_index(title.group(1) if title else route, route, html_text))
        if route.endswith(".html"):
            compat = route[:-5]
            if compat and compat != route:
                write_page(compat, render_redirect(route))

    redirects = load_json("redirects.json", {})
    redirects.update(
        {
            "/events/sloan-swartz-2007/program.php": "/events/sloan-swartz-2007/program.html",
            "/events/sloan-swartz-2007/details.html": "/events/sloan-swartz-2007/details.php.html",
            "/events/sloan-swartz-2007/map.html": "/events/sloan-swartz-2007/map.php.html",
            "/sloan-swartz-2007/map.html": "/events/sloan-swartz-2007/map.php.html",
        }
    )
    for source, target in redirects.items():
        write_page(source, render_redirect(target))
    write_page("/news/", render_redirect("/news-events/"))
    write_page("/public/", render_redirect("/"))
    (DIST / "search-index.json").write_text(json.dumps(search_index, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Built {len(pages)} pages and {len(redirects) + 2} redirects into {DIST}")
    apply_baseurl()


def apply_baseurl() -> None:
    """Bake the GitHub Pages URL prefix from <site>/.baseurl into dist.

    The prefix (e.g. "/sccn_site2" for https://arnodelorme.github.io/sccn_site2/)
    lives in .baseurl next to package.json; edit that file and rebuild to
    change it, or empty it to serve at a domain root. Rewriting is done by
    this script, which records the baked state in dist/.baseurl.
    """
    conf = ROOT / ".baseurl"
    prefix = conf.read_text(encoding="utf-8").strip() if conf.exists() else ""
    if not prefix.strip("/"):
        return
    changed = bake_baseurl(DIST, prefix)
    print(f"Baked URL prefix {prefix} into {changed} files")


if __name__ == "__main__":
    main()
