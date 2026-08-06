#!/usr/bin/env python3
"""
wp-ml-translate — WordPress Malayalam Translation Toolkit

Usage:
    python3 wp-ml-translate.py init                   # Interactive project setup
    python3 wp-ml-translate.py fetch <url-or-slug>    # Fetch pending strings
    python3 wp-ml-translate.py translate [slug]       # Generate AI prompt
    python3 wp-ml-translate.py apply [slug]           # Apply AI translations
    python3 wp-ml-translate.py submit [slug]          # Submit via browser helper
    python3 wp-ml-translate.py status [slug]          # Show progress
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
CONTEXT_DIR = ROOT / "context"
sys.path.insert(0, str(ROOT))


def _get_projects() -> list[str]:
    """Get list of project slugs that have strings.json in data/."""
    if not DATA_DIR.exists():
        return []
    return sorted([
        d.name for d in DATA_DIR.iterdir()
        if d.is_dir() and (d / "strings.json").exists()
    ])


def _pick_slug(args: list[str], action_desc: str = "process") -> str | None:
    """Get slug from args, or auto-detect from data/ directory.
    
    If no args given and projects exist in data/, let user pick or run all.
    Returns slug string, or None if no projects found.
    """
    if args and not args[0].startswith("--"):
        return args[0]

    projects = _get_projects()
    if not projects:
        print("  No projects found in data/. Run 'fetch' first.")
        return None

    if len(projects) == 1:
        print(f"  Auto-selected: {projects[0]}")
        return projects[0]

    print(f"\n  Available projects:")
    for i, p in enumerate(projects, 1):
        print(f"    {i}. {p}")
    print(f"    a. All (run sequentially)")
    print()

    choice = input("  Select [1-{}/a]: ".format(len(projects))).strip().lower()
    if choice == "a":
        return "__all__"
    try:
        idx = int(choice) - 1
        if 0 <= idx < len(projects):
            return projects[idx]
    except ValueError:
        pass

    print("  Invalid selection.")
    return None


def cmd_init(args):
    """Interactive onboarding — set up a new project to translate."""
    print("\n" + "=" * 50)
    print("  wp-ml-translate — New Project Setup")
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

        slug = input(f"\n  Project slug (e.g. twentyten, woocommerce): ").strip()
        if not slug:
            print("  No slug provided.")
            return 1
        target = f"{proj_type}/{slug}"

    print(f"\n  Fetching: {target}")
    print("  " + "-" * 48)

    from lib.fetcher import fetch_project
    result = fetch_project(target, DATA_DIR)

    if result:
        slug_name = result.stem
        print(f"\n  Setup complete!")
        print(f"\n  Next steps:")
        print(f"    1. python3 wp-ml-translate.py translate {slug_name}")
        print(f"    2. Feed prompt to AI, save response")
        print(f"    3. python3 wp-ml-translate.py apply {slug_name}")
        print(f"    4. python3 wp-ml-translate.py submit {slug_name}")
    return 0


def cmd_fetch(args):
    if not args:
        print("  Usage: wp-ml-translate.py fetch <url-or-slug>")
        print("\n  Examples:")
        print("    fetch twentyten                    # wp-themes/twentyten")
        print("    fetch wp-themes/twentytwentyfour")
        print("    fetch wp-plugins/woocommerce")
        print("    fetch https://translate.wordpress.org/projects/wp-themes/twentyten/ml/default/")
        return 1
    from lib.fetcher import fetch_project
    for target in args:
        print(f"\n{'─'*50}")
        fetch_project(target, DATA_DIR)
    return 0


def cmd_translate(args):
    batch = 10
    if "--batch" in args:
        batch = int(args[args.index("--batch") + 1])
        args = [a for a in args if a != "--batch" and a != str(batch)]

    slug = _pick_slug(args, "translate")
    if slug is None:
        return 1

    from lib.translator import generate_prompt

    if slug == "__all__":
        for s in _get_projects():
            print(f"\n{'─'*50}")
            print(f"  [{s}]")
            generate_prompt(s, DATA_DIR, CONTEXT_DIR, batch)
    else:
        generate_prompt(slug, DATA_DIR, CONTEXT_DIR, batch)
    return 0


def cmd_apply(args):
    slug = _pick_slug(args, "apply")
    if slug is None:
        return 1

    from lib.translator import apply_translations

    if slug == "__all__":
        for s in _get_projects():
            print(f"\n{'─'*50}")
            print(f"  [{s}]")
            apply_translations(s, DATA_DIR)
    else:
        apply_translations(slug, DATA_DIR)
    return 0


def cmd_submit(args):
    port = 8787
    if "--port" in args:
        port = int(args[args.index("--port") + 1])
        args = [a for a in args if a != "--port" and a != str(port)]

    slug = _pick_slug(args, "submit")
    if slug is None:
        return 1

    if slug == "__all__":
        print("  Submit must be run one project at a time.")
        print("  Please select a specific project.")
        return 1

    from lib.submitter import run_server
    run_server(slug, DATA_DIR, port)
    return 0


def cmd_status(args):
    if not DATA_DIR.exists():
        print("  No data found. Run 'fetch' first.")
        return 0

    proj_dirs = []
    if args:
        d = DATA_DIR / args[0]
        if d.exists() and (d / "strings.json").exists():
            proj_dirs = [d]
        else:
            print(f"  '{args[0]}' not found.")
            return 1
    else:
        proj_dirs = sorted([d for d in DATA_DIR.iterdir()
                           if d.is_dir() and (d / "strings.json").exists()])

    if not proj_dirs:
        print("  No data found. Run 'fetch' first.")
        return 0

    print(f"\n{'Project':<24}{'Total':>6}{'Pending':>8}{'Translated':>11}{'Submitted':>10}")
    print("─" * 62)
    for d in proj_dirs:
        with open(d / "strings.json", encoding="utf-8") as fh:
            data = json.load(fh)
        s = data["strings"]
        total = len(s)
        translated = sum(1 for x in s if x.get("translation", "").strip())
        submitted = sum(1 for x in s if x.get("submitted"))
        pending = total - translated
        print(f"{data['project']['slug']:<24}{total:>6}{pending:>8}{translated:>11}{submitted:>10}")
    print()
    return 0


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 1

    cmds = {
        "init": cmd_init,
        "fetch": cmd_fetch,
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
