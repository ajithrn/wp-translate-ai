#!/usr/bin/env python3
from __future__ import annotations

"""
wp-translate-ai -- Universal AI-Powered WordPress Translation Toolkit

Usage:
    python3 wp-translate-ai.py init                     # Interactive project setup
    python3 wp-translate-ai.py add-locale <code>        # Add & setup new target locale (--locale hi)
    python3 wp-translate-ai.py fetch <url-or-slug>      # Fetch pending strings (--locale hi)
    python3 wp-translate-ai.py translate [slug]         # Generate AI prompt batch
    python3 wp-translate-ai.py apply [slug]             # Apply AI JSON translations
    python3 wp-translate-ai.py submit [slug]            # Submit via browser helper
    python3 wp-translate-ai.py status [slug]            # Show progress
"""

__version__ = "2.0.0"

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
CONTEXT_DIR = ROOT / "context"
sys.path.insert(0, str(ROOT))

from lib.config import get_locale, load_config


def _get_projects() -> list[tuple[str, str]]:
    """Get list of (slug, locale) tuples that have strings.json in data/."""
    if not DATA_DIR.exists():
        return []
    res = []
    for p in DATA_DIR.rglob("strings.json"):
        rel = p.parent.relative_to(DATA_DIR)
        parts = rel.parts
        if len(parts) >= 2:
            locale = parts[-1]
            slug = str(Path(*parts[:-1]))
            res.append((slug, locale))
    return sorted(res)


def _get_unique_slugs() -> list[str]:
    """Get unique project slugs from data/."""
    return sorted(set(slug for slug, _ in _get_projects()))


def _resolve_locale(slug: str, args: list[str]) -> str | None:
    """Resolve locale for a project: from --locale, auto-detect, or prompt user."""
    loc = _extract_flag(args, "--locale")
    if loc:
        return loc

    slug_dir = DATA_DIR / slug
    if not slug_dir.exists():
        return get_locale()

    locale_dirs = sorted([
        d.name for d in slug_dir.iterdir()
        if d.is_dir() and (d / "strings.json").exists()
    ])

    if not locale_dirs:
        return get_locale()
    if len(locale_dirs) == 1:
        print(f"  Auto-selected locale: {locale_dirs[0]}")
        return locale_dirs[0]

    # Multiple locales — prompt user
    print(f"\n  Multiple locales found for '{slug}':")
    for i, l in enumerate(locale_dirs, 1):
        print(f"    {i}. {l}")
    print()
    choice = input(f"  Select locale [1-{len(locale_dirs)}]: ").strip()
    try:
        idx = int(choice) - 1
        if 0 <= idx < len(locale_dirs):
            return locale_dirs[idx]
    except ValueError:
        pass
    print("  Invalid selection.")
    return None


def _pick_slug(args: list[str], action_desc: str = "process") -> str | None:
    """Get slug from args, or auto-detect from data/ directory."""
    # Strip flags and their values (e.g. --batch 50, --locale ml)
    clean_args = []
    skip_next = False
    for a in args:
        if skip_next:
            skip_next = False
            continue
        if a.startswith("--"):
            skip_next = True
            continue
        clean_args.append(a)
    if clean_args:
        return clean_args[0]

    slugs = _get_unique_slugs()
    if not slugs:
        print("  No projects found in data/. Run 'fetch' first.")
        return None

    if len(slugs) == 1:
        print(f"  Auto-selected: {slugs[0]}")
        return slugs[0]

    # Show slugs with their available locales
    projects = _get_projects()
    slug_locales = {}
    for s, l in projects:
        slug_locales.setdefault(s, []).append(l)

    print(f"\n  Available projects:")
    for i, s in enumerate(slugs, 1):
        locales = ", ".join(slug_locales.get(s, []))
        print(f"    {i}. {s} [{locales}]")
    print(f"    a. All (run sequentially)")
    print()

    choice = input(f"  Select [1-{len(slugs)}/a]: ").strip().lower()
    if choice == "a":
        return "__all__"
    try:
        idx = int(choice) - 1
        if 0 <= idx < len(slugs):
            return slugs[idx]
    except ValueError:
        pass

    print("  Invalid selection.")
    return None


def _extract_flag(args: list[str], flag: str) -> str | None:
    """Extract a flag value like --locale hi from args."""
    if flag in args:
        idx = args.index(flag)
        if idx + 1 < len(args):
            val = args[idx + 1]
            return val
    return None


def cmd_init(args):
    """Interactive onboarding -- set up a new project to translate."""
    print("\n" + "=" * 50)
    print("  wp-translate-ai -- New Project Setup")
    print("=" * 50 + "\n")

    print("  Project type?")
    print("    1. Theme (wp-themes)")
    print("    2. Plugin (wp-plugins)")
    print("    3. Core (wp/dev)")
    print("    4. Enter URL directly")
    print()

    choice = input("  Select [1-4]: ").strip()

    if choice == "4":
        url = input("\n  GlotPress URL: ").strip()
        if not url:
            print("  No URL provided.")
            return 1
        target = url
    else:
        type_map = {"1": "wp-themes", "2": "wp-plugins", "3": "wp/dev"}
        proj_type = type_map.get(choice, "wp-themes")

        slug = input("\n  Project slug (e.g. twentyten, woocommerce): ").strip()
        if not slug:
            print("  No slug provided.")
            return 1
        target = f"{proj_type}/{slug}"

    loc = _extract_flag(args, "--locale") or get_locale()
    print(f"\n  Target Locale: {loc}")
    print(f"  Fetching: {target}")
    print("  " + "-" * 48)

    from lib.fetcher import fetch_project
    result = fetch_project(target, DATA_DIR, target_locale=loc)

    if result:
        slug_name = result.stem
        print("\n  Setup complete!")
        print("\n  Next steps:")
        print(f"    1. python3 wp-translate-ai.py translate {slug_name}")
        print("    2. AI agent processes data/<slug>/prompt.md")
        print(f"    3. python3 wp-translate-ai.py apply {slug_name}")
        print(f"    4. python3 wp-translate-ai.py submit {slug_name}")
    return 0


def cmd_fetch(args):
    if not args or (len(args) == 1 and args[0].startswith("--")):
        print("  Usage: wp-translate-ai.py fetch <url-or-slug> [--locale <code|slug>] [--limit <N>]")
        print("\n  Examples:")
        print("    fetch twentyten --locale ml        # Malayalam")
        print("    fetch wp-plugins/woocommerce --locale hi --limit 20")
        print("    fetch https://translate.wordpress.org/projects/wp-themes/twentyten/ml/default/")
        return 1

    loc = _extract_flag(args, "--locale") or get_locale()
    limit_val = _extract_flag(args, "--limit") or _extract_flag(args, "--max")
    limit = int(limit_val) if limit_val and limit_val.isdigit() else 0
    skip_args = {"--locale", loc, "--limit", "--max"}
    if limit_val:
        skip_args.add(limit_val)
    clean_targets = [a for a in args if not a.startswith("--") and a not in skip_args]

    from lib.fetcher import fetch_project
    for target in clean_targets:
        print(f"\n{'─'*50}")
        fetch_project(target, DATA_DIR, target_locale=loc, max_strings=limit)
    return 0


def cmd_translate(args):
    cfg = load_config()
    batch = cfg.get("default_batch_size", 15)

    if "--batch" in args:
        idx = args.index("--batch")
        if idx + 1 < len(args):
            val = args[idx + 1].strip().lower()
            batch = 0 if val in ("0", "all") else int(val)

    slug = _pick_slug(args, "translate")
    if slug is None:
        return 1

    from lib.translator import generate_prompt

    if slug == "__all__":
        for s, loc in _get_projects():
            print(f"\n{'─'*50}")
            print(f"  [{s}] [{loc}]")
            generate_prompt(s, DATA_DIR, CONTEXT_DIR, batch, target_locale=loc)
    else:
        loc = _resolve_locale(slug, args)
        if not loc:
            return 1
        generate_prompt(slug, DATA_DIR, CONTEXT_DIR, batch, target_locale=loc)
    return 0


def cmd_apply(args):
    slug = _pick_slug(args, "apply")
    if slug is None:
        return 1

    from lib.translator import apply_translations

    if slug == "__all__":
        for s, loc in _get_projects():
            print(f"\n{'─'*50}")
            print(f"  [{s}] [{loc}]")
            apply_translations(s, DATA_DIR, locale=loc)
    else:
        loc = _resolve_locale(slug, args)
        if not loc:
            return 1
        apply_translations(slug, DATA_DIR, locale=loc)
    return 0


def cmd_submit(args):
    port = 8787
    if "--port" in args:
        port = int(args[args.index("--port") + 1])

    slug = _pick_slug(args, "submit")
    if slug is None:
        return 1

    if slug == "__all__":
        print("  Submit must be run one project at a time.")
        print("  Please select a specific project.")
        return 1

    loc = _resolve_locale(slug, args)
    if not loc:
        return 1

    from lib.submitter import run_server
    run_server(slug, DATA_DIR, port, locale=loc)
    return 0


def cmd_status(args):
    if not DATA_DIR.exists():
        print("  No data found. Run 'fetch' first.")
        return 0

    clean_args = [a for a in args if not a.startswith("--")]

    proj_dirs = []
    if clean_args:
        target = clean_args[0].strip("/")
        d = DATA_DIR / target
        if d.exists() and (d / "strings.json").exists():
            proj_dirs = [d]
        elif d.exists():
            proj_dirs = sorted([p.parent for p in d.rglob("strings.json")])
        if not proj_dirs:
            print(f"  '{clean_args[0]}' not found.")
            return 1
    else:
        proj_dirs = sorted([p.parent for p in DATA_DIR.rglob("strings.json")])

    if not proj_dirs:
        print("  No data found. Run 'fetch' first.")
        return 0

    print(f"\n{'Project':<24}{'Locale':<8}{'Total':>6}{'Pending':>8}{'Translated':>11}{'Submitted':>10}")
    print("─" * 68)
    for d in proj_dirs:
        with open(d / "strings.json", encoding="utf-8") as fh:
            data = json.load(fh)
        s = data["strings"]
        total = len(s)
        translated = sum(1 for x in s if x.get("translation", "").strip())
        submitted = sum(1 for x in s if x.get("submitted"))
        pending = total - translated
        loc = data.get("project", {}).get("locale", d.name)
        print(f"{data['project']['slug']:<24}{loc:<8}{total:>6}{pending:>8}{translated:>11}{submitted:>10}")
    print()
    return 0


def cmd_add_locale(args):
    loc = None
    if "--locale" in args:
        loc = _extract_flag(args, "--locale")
    elif args:
        clean = [a for a in args if not a.startswith("--")]
        if clean:
            loc = clean[0]
    
    loc = loc or get_locale()
    print(f"\n  Initializing locale [{loc}]...")
    from lib.glossary import init_locale
    res = init_locale(CONTEXT_DIR, target_locale=loc)
    return 0 if res else 1


def cmd_fetch_glossary(args):
    loc = _extract_flag(args, "--locale") or get_locale()
    from lib.glossary import fetch_official_glossary
    res = fetch_official_glossary(CONTEXT_DIR, target_locale=loc)
    return 0 if res else 1


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 1

    cmds = {
        "init": cmd_init,
        "fetch": cmd_fetch,
        "fetch-glossary": cmd_fetch_glossary,
        "add-locale": cmd_add_locale,
        "create-locale": cmd_add_locale,
        "translate": cmd_translate,
        "apply": cmd_apply,
        "submit": cmd_submit,
        "status": cmd_status,
    }
    cmd = sys.argv[1]
    if cmd in cmds:
        return cmds[cmd](sys.argv[2:])
    print(f"  Unknown command: {cmd}")
    print(f"  Available: {', '.join(cmds)}")
    return 1



if __name__ == "__main__":
    raise SystemExit(main())
