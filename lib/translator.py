"""
Translation Engine — generates AI prompts and parses responses.

Workflow:
1. generate_prompt() -> creates a prompt .md file in data/<slug>/<locale>/
2. User feeds prompt to AI (Kiro, Claude, etc.)
3. AI returns JSON with translations
4. apply_translations() -> merges AI output back into project JSON
"""

from __future__ import annotations

import json
from pathlib import Path

def _project_dir(slug: str, data_dir: Path, locale: str) -> Path:
    return data_dir / slug / locale


def _load_project(slug: str, data_dir: Path, locale: str) -> tuple[Path, dict]:
    path = _project_dir(slug, data_dir, locale) / "strings.json"
    if not path.exists():
        raise FileNotFoundError(f"'{slug}' [{locale}] not found. Run 'fetch' first.")
    with open(path, "r", encoding="utf-8") as f:
        return path, json.load(f)


from lib.config import get_locale


def _load_prompt_template(context_dir: Path, locale: str | None = None) -> str:
    loc = locale or get_locale()
    parts = []

    base_path = context_dir / "prompt-template.md"
    if base_path.exists():
        parts.append(base_path.read_text(encoding="utf-8"))

    loc_path = context_dir / "locales" / loc / "prompt-template.md"
    if loc_path.exists():
        parts.append(loc_path.read_text(encoding="utf-8"))

    return "\n\n---\n\n".join(parts)




def _load_glossary(context_dir: Path, locale: str | None = None) -> dict[str, str]:
    loc = locale or get_locale()
    g_path = context_dir / "locales" / loc / "glossary.json"
    if g_path.exists():
        try:
            with open(g_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def generate_prompt(slug: str, data_dir: Path, context_dir: Path, batch_size: int = 10, target_locale: str | None = None):
    """Generate a translation prompt for the next batch of untranslated strings."""
    target_loc = target_locale or get_locale()
    path, data = _load_project(slug, data_dir, target_loc)
    proj_dir = _project_dir(slug, data_dir, target_loc)
    strings = data["strings"]

    # Get untranslated strings
    pending = [s for s in strings if s["translation_status"] == "pending"]
    if not pending:
        submitted = sum(1 for s in strings if s.get("submitted"))
        if submitted < len(strings):
            print(f"  ✓ All {len(strings)} strings have been translated locally!")
            print(f"  ➜ Next step: Submit translations to GlotPress ({len(strings) - submitted} remaining to submit):")
            print(f"     python3 wp-translate-ai.py submit {slug}")
        else:
            print("  ✓ All translations completed and submitted!")
        return

    batch = pending if batch_size <= 0 else pending[:batch_size]
    print(f"  {len(pending)} pending, {len(batch)} in this batch")

    # Load template and glossary
    template = _load_prompt_template(context_dir, locale=target_loc)
    glossary = _load_glossary(context_dir, locale=target_loc)

    # Build the prompt
    prompt_lines = []
    prompt_lines.append(f"# WordPress Translation Request [{target_loc}]\n")

    if template:
        prompt_lines.append(template)
        prompt_lines.append("\n---\n")

    if glossary:
        prompt_lines.append(f"### Official GlotPress Glossary Terms [{target_loc}]\n")
        prompt_lines.append("| Term | Target Translation |")
        prompt_lines.append("| :--- | :--- |")
        for k, v in list(glossary.items())[:40]:
            prompt_lines.append(f"| {k} | {v} |")
        prompt_lines.append("\n---\n")

    prompt_lines.append("## Strings to Translate\n")
    prompt_lines.append(f"Project: **{data['project']['name']}** ({data['project']['type']}) — Locale: **{target_loc}**\n")

    # Format strings for the prompt
    prompt_lines.append("```json")
    prompt_lines.append("[")
    for i, s in enumerate(batch):
        entry = {
            "id": s["id"],
            "original": s["original"],
        }
        if s.get("plural"):
            entry["plural"] = s["plural"]
        if s.get("context"):
            entry["context"] = s["context"]
        if s.get("comment"):
            entry["comment"] = s["comment"]
        if s.get("references"):
            entry["references"] = s["references"]
        if s.get("reference_url"):
            entry["reference_url"] = s["reference_url"]
        if s.get("glossary_hits"):
            entry["glossary_hits"] = s["glossary_hits"]
        if s.get("placeholders"):
            entry["placeholders"] = s["placeholders"]
        comma = "," if i < len(batch) - 1 else ""
        prompt_lines.append(f"  {json.dumps(entry, ensure_ascii=False)}{comma}")
    prompt_lines.append("]")
    prompt_lines.append("```\n")

    has_plurals = any(s.get("plural") for s in batch)

    prompt_lines.append("## Expected Output\n")
    prompt_lines.append("Return JSON only in this format:\n")
    prompt_lines.append("```json")
    prompt_lines.append("[")
    prompt_lines.append('  {"id": "...", "translation": "..."},')
    if has_plurals:
        prompt_lines.append('  {"id": "...", "translation": "<singular>", "plural_translation": "<plural>"},')
    prompt_lines.append("  ...")
    prompt_lines.append("]")
    prompt_lines.append("```\n")
    if has_plurals:
        prompt_lines.append("*Note: For strings containing a `plural` field, provide both `translation` (singular form) and `plural_translation` (plural form).*\n")

    # Write prompt file in project folder
    prompt_path = proj_dir / "prompt.md"
    prompt_path.write_text("\n".join(prompt_lines), encoding="utf-8")
    print(f"  ✓ Prompt file: {prompt_path}")
    print(f"    Feed this to AI, save output as 'data/{slug}/{target_loc}/response.json'")
    print(f"    Then run: python3 wp-translate-ai.py apply {slug} --locale {target_loc}")


def apply_translations(slug: str, data_dir: Path, locale: str | None = None):
    """Apply AI-generated translations from response JSON back into project data."""
    loc = locale or get_locale()
    path, data = _load_project(slug, data_dir, loc)
    proj_dir = _project_dir(slug, data_dir, loc)

    response_path = proj_dir / "response.json"
    if not response_path.exists():
        print(f"  ✗ 'data/{slug}/{loc}/response.json' not found.")
        print(f"    Save the AI output to that file first.")
        return

    with open(response_path, "r", encoding="utf-8") as f:
        content = f.read().strip()
        # Handle markdown code blocks in response
        if "```" in content:
            import re
            m = re.search(r"```(?:json)?\s*\n(.*?)\n```", content, re.S)
            if m:
                content = m.group(1)
        translations = json.loads(content)

    # Build lookup
    tr_map = {item["id"]: item for item in translations if item.get("translation")}

    applied = 0
    for s in data["strings"]:
        if s["id"] in tr_map:
            item = tr_map[s["id"]]
            s["translation"] = item["translation"]
            if item.get("plural_translation"):
                s["plural_translation"] = item["plural_translation"]
            s["translation_status"] = "ready"
            applied += 1

    # Save
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"  ✓ {applied} translations applied")

    # Archive response file (safely overwrite previous applied responses if present)
    response_path.replace(proj_dir / "response_applied.json")
    print(f"    Response file archived")
