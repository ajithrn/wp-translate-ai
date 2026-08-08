"""
Official WordPress.org GlotPress Glossary Fetcher
"""

from __future__ import annotations

import html
import json
import re
import urllib.request
from pathlib import Path

from lib.config import get_locale, load_config

BASE = "https://translate.wordpress.org"
_config = load_config()
UA = _config.get("user_agent", "wp-translate-ai/2.0")


def _get(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", errors="replace")


def fetch_official_glossary(context_dir: Path, target_locale: str | None = None) -> dict[str, str]:
    """Fetch the official WordPress.org glossary for a given locale."""
    loc = target_locale or get_locale()
    url = f"{BASE}/locale/{loc}/default/glossary/"

    print(f"  Fetching official WordPress glossary for [{loc}]...")
    try:
        page_html = _get(url)
    except Exception as e:
        print(f"  ✗ Failed to fetch glossary for '{loc}': {e}")
        return {}

    # Extract tr rows containing term and translation
    matches = re.findall(r"<tr[^>]*>(.*?)</tr>", page_html, re.DOTALL)
    glossary = {}

    for match in matches:
        cells = re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", match, re.DOTALL)
        clean_cells = [html.unescape(re.sub(r"<[^>]+>", "", c)).strip() for c in cells]
        # Valid data rows have: [English term, part_of_speech, Target Translation, ...]
        if len(clean_cells) >= 3 and clean_cells[0] and clean_cells[2] and clean_cells[0] != "Item":
            term = clean_cells[0]
            translation = clean_cells[2]
            # Exclude metadata rows
            if not term.startswith("Original term:") and not term.startswith("Part of speech"):
                glossary[term] = translation

    if not glossary:
        print(f"  ⚠️ No glossary entries found for locale '{loc}'.")
        return {}

    # Save to context/locales/<locale>/glossary.json
    loc_dir = context_dir / "locales" / loc
    loc_dir.mkdir(parents=True, exist_ok=True)
    out_file = loc_dir / "glossary.json"

    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(glossary, f, ensure_ascii=False, indent=2)

    print(f"  ✓ Saved {len(glossary)} official terms to '{out_file.relative_to(context_dir.parent)}'")
    return glossary


def init_locale(context_dir: Path, target_locale: str) -> bool:
    """Initialize a new locale by fetching official glossary and creating prompt-template.md if missing."""
    loc = target_locale.lower()
    fetch_official_glossary(context_dir, target_locale=loc)

    loc_dir = context_dir / "locales" / loc
    loc_dir.mkdir(parents=True, exist_ok=True)
    template_file = loc_dir / "prompt-template.md"

    if not template_file.exists():
        content = f"""## {loc.upper()} ({loc}) Locale Guidelines

> **Note**: This document extends the global technical rules in `context/prompt-template.md`.

You are an expert translator for the **{loc.upper()} (`{loc}`)** locale. Translate WordPress interface strings into natural, fluent text for native speakers.

---

### Strict Rules & Register

1. **Script & Terminology**:
   - Write standard terms in native script where appropriate.
   - *Exception*: Keep technical acronyms, protocols (`URL`, `HTML`, `CSS`, `PHP`, `FTP`, `HTTP`, `HTTPS`, `API`, `REST`, `RSS`, `JSON`, `SQL`, `XML`, `AJAX`, `DNS`, `IP`, `SSL`, `TLS`, `SEO`, `CMS`), and font names in English script.

2. **Formal Register**:
   - Always use standard formal UI register for {loc}. Never use informal phrasing.

3. **No Word-for-Word Translation**:
   - Do not follow English sentence structure rigidly. Use natural grammatical flow for {loc}.

4. **NEVER Alter Placeholders**:
   - Preserve all placeholders (`%s`, `%1$s`, `%2$s`, `###SITENAME###`) and HTML tags (`<a href="...">`, `<span>`, `<strong>`) EXACTLY as given.

---

### Contextual Style Guide

**1. UI Labels & Headers** — Concise & direct:
- Add concise native-script terms for UI headers and labels.

**2. Theme / Plugin Descriptions** — Professional, engaging tone:
- Provide engaging native-script phrasing for theme & plugin showcase descriptions.

**3. Error Messages / 404 Pages** — Friendly & simple:
- Friendly native-script phrasing for error states.

**4. Narrative & Block Pattern Content** — Expressive & natural flow:
- Natural native-script phrasing for story/pattern strings.

**5. Meta Text (Posted on, Categories)** — Concise:
- Native phrasing for post metadata.

**6. Latin Lorem Ipsum** — Leave untouched, do not translate.

**7. Quotes** — Expressive, living language:
- Natural native-script quotes.

---

### Common Mistakes to Avoid

| Avoid This | Use This | Reason |
| :--- | :--- | :--- |
| Literal word-for-word translation | Natural native phrasing | Sounds mechanical in UI context |
| Informal register | Formal UI register | Standard WordPress UI requirement |
| Adding trailing period when source lacks one | Match source punctuation exactly | Fails GlotPress validation |

---

### Format Preservation Examples

**Correct:**

```
Original: "Bookmark the <a href="%3$s" title="Permalink to %4$s" rel="bookmark">permalink</a>."
Translation: "<a href="%3$s" title="%4$s permalink" rel="bookmark">permalink</a>"
```

*(HTML tag structure, attributes, quotes remain identical; only text is translated into target script).*

---

### Key Considerations

- Maintain consistency across string variants.
- Check the `references` field to understand context (`comments.php` = comments, `404.php` = error page, `block-patterns.php` = demo content).
- Always honor official glossary terms loaded from `context/locales/{loc}/glossary.json`.
"""
        template_file.write_text(content, encoding="utf-8")
        print(f"  ✓ Created locale template: '{template_file.relative_to(context_dir.parent)}'")

    print(f"  ✓ Locale '{loc}' ready in context/locales/{loc}/")
    return True

