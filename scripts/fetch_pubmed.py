#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import shutil
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"


def parse_authors(path: Path) -> list[dict]:
    authors = []
    current = None
    in_queries = False
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.rstrip()
        stripped = line.strip()
        if stripped.startswith("- display:"):
            current = {"display": stripped.split(":", 1)[1].strip(), "queries": []}
            authors.append(current)
            in_queries = False
        elif stripped == "queries:":
            in_queries = True
        elif in_queries and stripped.startswith("- ") and current:
            current["queries"].append(stripped[2:].strip())
    return authors


def request_json(endpoint: str, params: dict) -> dict:
    url = f"{EUTILS}/{endpoint}?" + urllib.parse.urlencode(params)
    with urllib.request.urlopen(url, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def request_xml(endpoint: str, params: dict) -> ET.Element:
    url = f"{EUTILS}/{endpoint}?" + urllib.parse.urlencode(params)
    with urllib.request.urlopen(url, timeout=60) as response:
        return ET.fromstring(response.read())


def find_text(node: ET.Element, path: str) -> str:
    found = node.find(path)
    if found is None:
        return ""
    return "".join(found.itertext()).strip()


def article_ids(pubmed_article: ET.Element) -> dict:
    ids = {}
    pmid = find_text(pubmed_article, ".//MedlineCitation/PMID")
    if pmid:
        ids["pmid"] = pmid
    for item in pubmed_article.findall(".//PubmedData/ArticleIdList/ArticleId"):
        id_type = item.attrib.get("IdType", "").lower()
        if id_type:
            ids[id_type] = "".join(item.itertext()).strip()
    return ids


def parse_record(pubmed_article: ET.Element, query_author: str) -> dict:
    ids = article_ids(pubmed_article)
    article = pubmed_article.find(".//MedlineCitation/Article")
    title = find_text(pubmed_article, ".//ArticleTitle")
    journal = find_text(pubmed_article, ".//Journal/Title") or find_text(pubmed_article, ".//Journal/ISOAbbreviation")
    year = find_text(pubmed_article, ".//JournalIssue/PubDate/Year")
    if not year:
        medline_date = find_text(pubmed_article, ".//JournalIssue/PubDate/MedlineDate")
        match = re.search(r"(19|20)\d{2}", medline_date)
        year = match.group(0) if match else ""
    authors = []
    for author in pubmed_article.findall(".//AuthorList/Author"):
        collective = find_text(author, "CollectiveName")
        if collective:
            authors.append(collective)
            continue
        last = find_text(author, "LastName")
        initials = find_text(author, "Initials")
        if last:
            authors.append(f"{last}, {initials}".strip(", "))
    abstract = " ".join(
        " ".join(item.itertext()).strip()
        for item in pubmed_article.findall(".//Abstract/AbstractText")
        if " ".join(item.itertext()).strip()
    )
    pmid = ids.get("pmid", "")
    doi = ids.get("doi", "")
    return {
        "pmid": pmid,
        "doi": doi,
        "title": title,
        "authors": authors,
        "journal": journal,
        "year": year,
        "abstract": abstract,
        "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else "",
        "doi_url": f"https://doi.org/{doi}" if doi else "",
        "query_author": query_author,
    }


def bib_escape(value: str) -> str:
    return (value or "").replace("\\", "\\\\").replace("{", "\\{").replace("}", "\\}").replace("\n", " ")


def make_key(record: dict, existing: set[str]) -> str:
    lead = "pubmed"
    if record["authors"]:
        lead = re.sub(r"[^A-Za-z0-9]+", "", record["authors"][0].split(",")[0]) or "pubmed"
    key = f"{lead}{record.get('year', '')}{record.get('pmid', '')}"
    key = key or f"pubmed{len(existing)}"
    base = key
    i = 2
    while key in existing:
        key = f"{base}{i}"
        i += 1
    existing.add(key)
    return key


def records_to_bib(records: list[dict]) -> str:
    keys = set()
    entries = []
    for record in records:
        key = make_key(record, keys)
        fields = {
            "title": record.get("title", ""),
            "author": " and ".join(record.get("authors", [])),
            "journal": record.get("journal", ""),
            "year": record.get("year", ""),
            "doi": record.get("doi", ""),
            "pmid": record.get("pmid", ""),
            "url": record.get("url", ""),
            "abstract": record.get("abstract", ""),
            "note": f"PubMed query source: {record.get('query_author', '')}",
        }
        body = "\n".join(
            f"  {name} = {{{bib_escape(value)}}},"
            for name, value in fields.items()
            if value
        ).rstrip(",")
        entries.append(f"@article{{{key},\n{body}\n}}\n")
    return "\n".join(entries)


def load_curation(path: Path) -> dict:
    if not path.exists():
        return {"exclude_pmids": [], "exclude_dois": [], "exclude_titles": []}
    return json.loads(path.read_text(encoding="utf-8"))


def is_excluded(record: dict, curation: dict) -> bool:
    title_norm = re.sub(r"\s+", " ", record.get("title", "")).strip().lower()
    return (
        record.get("pmid") in set(curation.get("exclude_pmids", []))
        or record.get("doi") in set(curation.get("exclude_dois", []))
        or title_norm in {item.lower() for item in curation.get("exclude_titles", [])}
    )


def merge_bib(manual: Path, pubmed: Path, merged: Path) -> None:
    parts = []
    if manual.exists():
        parts.append(manual.read_text(encoding="utf-8"))
    if pubmed.exists():
        parts.append(pubmed.read_text(encoding="utf-8"))
    merged.write_text("\n\n".join(parts), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--authors", type=Path, default=ROOT / "data/pubmed/authors.yml")
    parser.add_argument("--out", type=Path, default=ROOT / "data/publications/pubmed.bib")
    parser.add_argument("--email", default="webmaster@sccn.ucsd.edu")
    parser.add_argument("--tool", default="sccn3-publication-builder")
    parser.add_argument("--retmax", type=int, default=180)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    authors = parse_authors(args.authors)
    if args.dry_run:
        for author in authors:
            print(author["display"], author["queries"])
        return

    raw_dir = ROOT / "data/pubmed/raw"
    if raw_dir.exists():
        shutil.rmtree(raw_dir)
    raw_dir.mkdir(parents=True, exist_ok=True)
    records_by_pmid = {}
    curation = load_curation(ROOT / "data/pubmed/curation.json")

    for author in authors:
        for query in author["queries"]:
            params = {
                "db": "pubmed",
                "term": query,
                "retmode": "json",
                "retmax": args.retmax,
                "sort": "pub date",
                "tool": args.tool,
                "email": args.email,
            }
            data = request_json("esearch.fcgi", params)
            ids = data.get("esearchresult", {}).get("idlist", [])
            safe_query = re.sub(r"[^A-Za-z0-9]+", "_", query).strip("_")
            (raw_dir / f"{safe_query}_esearch.json").write_text(json.dumps(data, indent=2), encoding="utf-8")
            print(f"{query}: {len(ids)} PubMed ids")
            if not ids:
                continue
            root = request_xml(
                "efetch.fcgi",
                {
                    "db": "pubmed",
                    "id": ",".join(ids),
                    "retmode": "xml",
                    "tool": args.tool,
                    "email": args.email,
                },
            )
            (raw_dir / f"{safe_query}_efetch.xml").write_text(ET.tostring(root, encoding="unicode"), encoding="utf-8")
            for article in root.findall(".//PubmedArticle"):
                record = parse_record(article, author["display"])
                if not record.get("pmid"):
                    continue
                if not is_excluded(record, curation):
                    records_by_pmid.setdefault(record["pmid"], record)
            time.sleep(0.35)

    records = sorted(records_by_pmid.values(), key=lambda item: (item.get("year", ""), item.get("title", "")), reverse=True)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(records_to_bib(records), encoding="utf-8")
    (ROOT / "data/publications/pubmed_records.json").write_text(json.dumps(records, indent=2, ensure_ascii=False), encoding="utf-8")
    merge_bib(ROOT / "data/publications/manual.bib", args.out, ROOT / "data/publications/sccn_publications.bib")
    print(f"Wrote {len(records)} unique PubMed records to {args.out}")


if __name__ == "__main__":
    main()
