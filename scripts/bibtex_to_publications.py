#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


FIELD_RE = re.compile(r"(\w+)\s*=\s*\{", re.MULTILINE)


def split_entries(text: str) -> list[str]:
    entries = []
    start = None
    depth = 0
    for i, char in enumerate(text):
        if char == "@" and depth == 0:
            start = i
        if start is None:
            continue
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                entries.append(text[start : i + 1])
                start = None
    return entries


def parse_fields(body: str) -> dict:
    fields = {}
    pos = 0
    while True:
        match = FIELD_RE.search(body, pos)
        if not match:
            break
        name = match.group(1).lower()
        value_start = match.end()
        depth = 1
        i = value_start
        while i < len(body):
            if body[i] == "{" and body[i - 1 : i] != "\\":
                depth += 1
            elif body[i] == "}" and body[i - 1 : i] != "\\":
                depth -= 1
                if depth == 0:
                    break
            i += 1
        fields[name] = body[value_start:i].replace("\\{", "{").replace("\\}", "}").strip()
        pos = i + 1
    return fields


def parse_entry(entry: str) -> dict | None:
    header = re.match(r"@(?P<type>\w+)\s*\{\s*(?P<key>[^,]+),", entry)
    if not header:
        return None
    fields = parse_fields(entry[header.end() : -1])
    title = fields.get("title") or fields.get("note") or header.group("key")
    authors = fields.get("author", "")
    year = fields.get("year", "")
    return {
        "type": header.group("type").lower(),
        "key": header.group("key").strip(),
        "title": clean(title),
        "authors": clean(authors),
        "journal": clean(fields.get("journal", "")),
        "year": clean(year),
        "doi": clean(fields.get("doi", "")),
        "pmid": clean(fields.get("pmid", "")),
        "url": clean(fields.get("url", "")),
        "abstract": clean(fields.get("abstract", "")),
        "note": clean(fields.get("note", "")),
    }


def clean(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def dedupe(records: list[dict]) -> list[dict]:
    seen = set()
    output = []
    for record in records:
        ident = record.get("pmid") or record.get("doi") or re.sub(r"\W+", "", record.get("title", "").lower())
        if not ident or ident in seen:
            continue
        seen.add(ident)
        output.append(record)
    return output


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bib", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    records = []
    for entry in split_entries(args.bib.read_text(encoding="utf-8")):
        record = parse_entry(entry)
        if record:
            records.append(record)
    records = dedupe(records)
    records.sort(key=lambda item: (item.get("year", ""), item.get("title", "")), reverse=True)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(records, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {len(records)} publication records to {args.out}")


if __name__ == "__main__":
    main()
