"""
GlotPress Fetcher — scrapes pending ml_IN strings from any project.

Input formats:
  - Full URL: https://translate.wordpress.org/projects/wp-themes/twentyten/ml/default/
  - Path: wp-themes/twentyten
  - Slug (assumes wp-themes): twentyten
"""

from __future__ import annotations

import html
import json
import re
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

BASE = "https://translate.wordpress.org"
LOCALE = "ml"
SET_SLUG = "default"
ROWS_PER_PAGE = 15
SLEEP = 0.7
UA = "wp-ml-translate/2.0"
PENDING_STATUSES = ["untranslated", "waiting", "fuzzy"]

PLACEHOLDER_RE = re.compile("|".join([
    r"%%", r"%\d+\$[sdf]", r"%[sdf]",
    r"###[A-Z_]+###", r"\{\{[^}]+\}\}",
    r"</?[a-zA-Z][^>]*>", r"&#\d+;|&[a-z]+;",
]))
SPAN_RE = re.compile(r"<span\b[^>]*>|</span>", re.I)


def _get(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read().decode("utf-8", errors="replace")


def parse_input(s: str) -> tuple[str, str, str]:
    """Parse input → (project_type, slug, locale_url)."""
    s = s.strip().rstrip("/")
    # Strip query string for URL parsing
    base_url = s.split("?")[0].rstrip("/") if s.startswith("http") else s

    if s.startswith("http"):
        # Standard project URL: /projects/wp-themes/twentyten/ml/default/
        m = re.search(r"/projects/([^/]+)/([^/]+)", base_url)
        if m:
            return (m.group(1), m.group(2),
                    f"{BASE}/projects/{m.group(1)}/{m.group(2)}/{LOCALE}/{SET_SLUG}/")
        # Locale URL with specific project: /locale/ml/default/wp-themes/twentyten
        m = re.search(r"/locale/[^/]+/[^/]+/([^/]+)/([^/]+)", base_url)
        if m:
            return (m.group(1), m.group(2),
                    f"{BASE}/projects/{m.group(1)}/{m.group(2)}/{LOCALE}/{SET_SLUG}/")
        # Locale listing page (no specific project)
        raise ValueError(
            f"This URL is a listing page, not a specific project URL.\n"
            f"  Fetch each project individually, e.g.:\n"
            f"  python3 wp-ml-translate.py fetch twentyten twentyeleven twentytwelve"
        )
    if "/" in s:
        t, slug = s.split("/", 1)
        return t, slug, f"{BASE}/projects/{t}/{slug}/{LOCALE}/{SET_SLUG}/"
    return "wp-themes", s, f"{BASE}/projects/wp-themes/{s}/{LOCALE}/{SET_SLUG}/"


def _api_stats(proj_type: str, slug: str) -> dict:
    """Get project name + locale stats from API."""
    data = json.loads(_get(f"{BASE}/api/projects/{proj_type}/{slug}"))
    name = data.get("name", slug)
    for ts in data.get("translation_sets", []):
        if ts.get("locale") == LOCALE and ts.get("slug") == SET_SLUG:
            return {
                "name": name,
                "total": int(ts.get("all_count", 0)),
                "translated": int(ts.get("current_count", 0)),
                "untranslated": int(ts.get("untranslated_count", 0)),
                "waiting": int(ts.get("waiting_count", 0)),
                "fuzzy": int(ts.get("fuzzy_count", 0)),
                "percent": int(ts.get("percent_translated", 0)),
            }
    if data.get("sub_projects"):
        sub_slugs = [sp["slug"] for sp in data["sub_projects"]]
        for target in ["stable", "dev"]:
            if target in sub_slugs:
                res = _api_stats(proj_type, f"{slug}/{target}")
                res["sub_slug"] = f"{slug}/{target}"
                return res
    return {"name": name, "total": 0, "translated": 0, "untranslated": 0,
            "waiting": 0, "fuzzy": 0, "percent": 0}


def _spans(fragment: str, cls: str) -> list[str]:
    out = []
    for opener in re.finditer(rf'<span class="{cls}"[^>]*>', fragment):
        depth, pos = 1, opener.end()
        while depth:
            tok = SPAN_RE.search(fragment, pos)
            if not tok:
                break
            depth += -1 if tok.group(0).startswith("</") else 1
            pos = tok.end() if depth else tok.start()
        out.append(fragment[opener.end():pos])
    return out


def _strip(frag: str) -> str:
    t = re.sub(r"<br\s*/?>", "\n", frag)
    t = re.sub(r"<[^>]+>", "", t)
    return html.unescape(t).strip()


def _glossary(row_html: str) -> dict:
    hits = {}
    for m in re.finditer(
        r'<span class="glossary-word" data-translations="([^"]*)">(.*?)</span>',
        row_html, re.S
    ):
        word = _strip(m.group(2))
        try:
            entries = json.loads(html.unescape(m.group(1)))
        except Exception:
            continue
        for e in entries:
            tr = e.get("translation", "")
            if tr and word not in hits:
                hits[word] = tr
    return hits


def _parse_page(page_html: str, proj_type: str, slug: str) -> list[dict]:
    out = []
    for m in re.finditer(
        r'<tr class="(?P<cls>preview[^"]*)" id="preview-(?P<id>\d+)"[^>]*>(?P<body>.*?)</tr>',
        page_html, re.S
    ):
        oid, cls, body = m.group("id"), m.group("cls"), m.group("body")
        status = next((s for s in PENDING_STATUSES + ["current", "rejected", "old"]
                       if re.search(rf"\b{s}\b", cls)), "")
        priority = ""
        pm = re.search(r"priority-([a-z]+)", cls)
        if pm:
            priority = pm.group(1)

        originals = _spans(body, "original-text")
        singular = _strip(originals[0]) if originals else ""
        plural = _strip(originals[1]) if len(originals) > 1 else ""
        ctx = _strip(_spans(body, "context")[0]) if _spans(body, "context") else ""

        glossary = _glossary(body)

        # Editor row
        editor = ""
        em = re.search(rf'<tr class="editor[^"]*" id="editor-{oid}".*?</tr>', page_html, re.S)
        if em:
            editor = em.group(0)
        refs = ""
        if editor:
            rb = re.search(r"References</[^>]+>(.*?)</(?:ul|dd|div)>", editor, re.S)
            if rb:
                refs = " | ".join(dict.fromkeys(
                    r.strip() for r in re.findall(
                        r">([^<>]+?\.(?:php|css|js|html)(?::\d+)?)<", rb.group(1))
                ))
        comment = ""
        if editor:
            cm = re.search(r"Comment</[^>]+>(.*?)</(?:div|dd|p)>", editor, re.S)
            if cm:
                comment = _strip(cm.group(1))

        out.append({
            "id": oid,
            "status": status,
            "priority": priority,
            "context": ctx,
            "original": singular,
            "plural": plural,
            "references": refs,
            "comment": comment,
            "glossary_hits": glossary,
            "placeholders": _extract_ph(singular + " " + plural),
            "translation": "",
            "translation_status": "pending",
            "submitted": False,
            "permalink": f"{BASE}/projects/{proj_type}/{slug}/{LOCALE}/{SET_SLUG}/?filters%5Boriginal_id%5D={oid}",
        })
    return out


def _extract_ph(text: str) -> list[str]:
    seen = []
    for m in PLACEHOLDER_RE.finditer(text):
        if m.group(0) not in seen:
            seen.append(m.group(0))
    return seen


def _fetch_status(proj_type: str, slug: str, url: str, status: str) -> list[dict]:
    rows, page, seen = [], 1, set()
    while True:
        qs = urllib.parse.urlencode({
            "filters[status]": status, "filters[term]": "",
            "filters[term_scope]": "scope_any", "filter": "Apply Filters",
            "sort[by]": "priority", "sort[how]": "desc", "page": page,
        })
        html_page = _get(f"{url}?{qs}")
        batch = [r for r in _parse_page(html_page, proj_type, slug) if r["id"] not in seen]
        if not batch:
            break
        seen.update(r["id"] for r in batch)
        rows.extend(batch)
        if len(batch) < ROWS_PER_PAGE:
            break
        page += 1
        time.sleep(SLEEP)
    return rows


def fetch_project(input_str: str, data_dir: Path) -> Path | None:
    """Main entry: fetch pending strings → save JSON in data/<slug>/strings.json."""
    proj_type, slug, url = parse_input(input_str)
    stats = _api_stats(proj_type, slug)

    if "sub_slug" in stats:
        slug = stats["sub_slug"]
        url = f"{BASE}/projects/{proj_type}/{slug}/{LOCALE}/{SET_SLUG}/"

    pending = stats["untranslated"] + stats["waiting"] + stats["fuzzy"]
    print(f"  {stats['name']} — {stats['percent']}% ({pending} pending)")

    if pending == 0:
        print("  ✓ Nothing pending!")
        return None

    print(f"  Scraping...")
    strings = []
    for st in PENDING_STATUSES:
        if stats.get(st, 0) == 0:
            continue
        got = _fetch_status(proj_type, slug, url, st)
        strings.extend(got)
        time.sleep(SLEEP)

    print(f"  {len(strings)} strings fetched")

    project_data = {
        "project": {
            "slug": slug,
            "name": stats["name"],
            "type": proj_type,
            "url": url,
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "stats": {
                "total": stats["total"],
                "translated": stats["translated"],
                "pending": pending,
                "percent": stats["percent"],
            },
        },
        "strings": strings,
    }

    proj_dir = data_dir / slug
    proj_dir.mkdir(parents=True, exist_ok=True)
    out = proj_dir / "strings.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(project_data, f, ensure_ascii=False, indent=2)

    print(f"  ✓ {out}")
    return out
