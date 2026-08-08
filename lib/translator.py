"""
Translation Engine — generates AI prompts and parses responses.

Workflow:
1. generate_prompt() → creates a prompt .md file in data/<slug>/
2. User feeds prompt to AI (Kiro, Claude, etc.)
3. AI returns JSON with translations
4. apply_translations() → merges AI output back into project JSON
"""

from __future__ import annotations

import json
from pathlib import Path


def _project_dir(slug: str, data_dir: Path) -> Path:
    return data_dir / slug


def _load_project(slug: str, data_dir: Path) -> tuple[Path, dict]:
    path = _project_dir(slug, data_dir) / "strings.json"
    if not path.exists():
        raise FileNotFoundError(f"'{slug}' not found. Run 'fetch' first.")
    with open(path, "r", encoding="utf-8") as f:
        return path, json.load(f)


def _load_prompt_template(context_dir: Path) -> str:
    path = context_dir / "prompt-template.md"
    if path.exists():
        return path.read_text(encoding="utf-8")
    return ""


def generate_prompt(slug: str, data_dir: Path, context_dir: Path, batch_size: int = 10):
    """Generate a translation prompt for the next batch of untranslated strings."""
    path, data = _load_project(slug, data_dir)
    proj_dir = _project_dir(slug, data_dir)
    strings = data["strings"]

    # Get untranslated strings
    pending = [s for s in strings if s["translation_status"] == "pending"]
    if not pending:
        submitted = sum(1 for s in strings if s.get("submitted"))
        if submitted < len(strings):
            print(f"  ✓ All {len(strings)} strings have been translated locally!")
            print(f"  ➜ Next step: Submit translations to GlotPress ({len(strings) - submitted} remaining to submit):")
            print(f"     python3 wp-ml-translate.py submit {slug}")
        else:
            print("  ✓ All translations completed and submitted!")
        return


    batch = pending[:batch_size]
    print(f"  {len(pending)} pending, {len(batch)} in this batch")

    # Load template
    template = _load_prompt_template(context_dir)

    # Build the prompt
    prompt_lines = []
    prompt_lines.append("# Malayalam Translation Request\n")

    if template:
        prompt_lines.append(template)
        prompt_lines.append("\n---\n")

    prompt_lines.append("## Strings to Translate\n")
    prompt_lines.append(f"Project: **{data['project']['name']}** ({data['project']['type']})\n")

    # Format strings for the prompt
    prompt_lines.append("```json")
    prompt_lines.append("[")
    for i, s in enumerate(batch):
        entry = {
            "id": s["id"],
            "original": s["original"],
            "context": s["context"],
            "comment": s["comment"],
            "references": s["references"],
            "glossary_hits": s["glossary_hits"],
            "placeholders": s["placeholders"],
        }
        if s["plural"]:
            entry["plural"] = s["plural"]
        comma = "," if i < len(batch) - 1 else ""
        prompt_lines.append(f"  {json.dumps(entry, ensure_ascii=False)}{comma}")
    prompt_lines.append("]")
    prompt_lines.append("```\n")

    prompt_lines.append("## Expected Output\n")
    prompt_lines.append("Return JSON only in this format:\n")
    prompt_lines.append("```json")
    prompt_lines.append("[")
    prompt_lines.append('  {"id": "...", "translation": "..."},')
    prompt_lines.append("  ...")
    prompt_lines.append("]")
    prompt_lines.append("```")

    # Write prompt file in project folder
    prompt_path = proj_dir / "prompt.md"
    prompt_path.write_text("\n".join(prompt_lines), encoding="utf-8")
    print(f"  ✓ Prompt file: {prompt_path}")
    print(f"    Feed this to AI, save output as 'data/{slug}/response.json'")
    print(f"    Then run: python3 wp-ml-translate.py apply {slug}")


def apply_translations(slug: str, data_dir: Path):
    """Apply AI-generated translations from response JSON back into project data."""
    path, data = _load_project(slug, data_dir)
    proj_dir = _project_dir(slug, data_dir)

    response_path = proj_dir / "response.json"
    if not response_path.exists():
        print(f"  ✗ 'data/{slug}/response.json' not found.")
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
    tr_map = {item["id"]: item["translation"] for item in translations if item.get("translation")}

    applied = 0
    for s in data["strings"]:
        if s["id"] in tr_map:
            s["translation"] = tr_map[s["id"]]
            s["translation_status"] = "ready"
            applied += 1

    # Save
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"  ✓ {applied} translations applied")

    # Archive response file
    response_path.rename(proj_dir / "response_applied.json")
    print(f"    Response file archived")
