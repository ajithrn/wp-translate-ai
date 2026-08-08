# Usage Guide

Step-by-step guide for translating WordPress projects into any target language using **`wp-translate-ai`**.

---

## Workflow Overview

```
add-locale → fetch → translate → apply → (repeat if needed) → submit
```

---

## 1. Add / Initialize a Target Locale (`add-locale`)

Initialize a new language locale (e.g., Hindi `hi`, Spanish `es`, French `fr`, Malayalam `ml`):

```bash
# Initialize Hindi (fetches official GlotPress glossary & creates prompt template)
python3 wp-translate-ai.py add-locale hi

# Or via create-locale alias
python3 wp-translate-ai.py create-locale es
```

- Fetches official WordPress terminology into `context/locales/<locale>/glossary.json`.
- Creates/populates a language guideline file `context/locales/<locale>/prompt-template.md` with native script examples, formal register rules, and mistake comparison tables modeled after the gold-standard `context/locales/ml/prompt-template.md`.

---

## 2. Fetch Pending Strings

Give a project URL or slug. The tool scrapes GlotPress and saves pending strings for the target locale.

```bash
# Fetch with default locale (from config.json)
python3 wp-translate-ai.py fetch twentyten

# Fetch for a specific target locale
python3 wp-translate-ai.py fetch wp-plugins/woocommerce --locale hi

# By full GlotPress URL
python3 wp-translate-ai.py fetch "https://translate.wordpress.org/projects/wp-themes/twentyten/ml/default/"

# Multiple projects at once
python3 wp-translate-ai.py fetch twentyten twentyeleven twentytwelve --locale ml
```

Output: `data/<slug>/<locale>/strings.json`

---

## 3. Generate Translation Prompt

Creates a prompt batch file containing language-specific rules, glossary terms, and pending strings.

```bash
# Default batch size (15 strings)
python3 wp-translate-ai.py translate twentyten

# Target specific locale
python3 wp-translate-ai.py translate twentyten --locale hi

# Custom batch size (e.g. 50 strings)
python3 wp-translate-ai.py translate twentyten --batch 50

# All pending strings in one go
python3 wp-translate-ai.py translate twentyten --batch all
```

Output: `data/<slug>/<locale>/prompt.md` (inherits rules from `context/prompt-template.md` and `context/locales/<locale>/prompt-template.md`).

---

## 4. Feed Prompt to AI

### Option A: Using AI IDE Agents (Cursor, Antigravity, Kiro, Windsurf, etc.)
Just type naturally in your IDE chat:
```text
"Translate this: https://translate.wordpress.org/projects/wp-themes/twentyten/ml/default/"
"Translate all pending strings for twentyten in one go"
"Translate 50 pending strings for woocommerce"
"Continue translating twentytwentyfour"
"Add locale hi"
```
The agent reads `AGENTS.md` and executes the fetch/translate/apply cycle automatically.

### Option B: Manual (ChatGPT, Claude, Custom LLM)
1. Open `data/<slug>/<locale>/prompt.md`
2. Copy its full content
3. Paste into Claude / ChatGPT / any LLM
4. Copy the JSON response array
5. Save as `data/<slug>/<locale>/response.json`

---

## 5. Apply Translations

Merges the AI response back into the project data.

```bash
python3 wp-translate-ai.py apply twentyten
# Or specify locale
python3 wp-translate-ai.py apply twentyten --locale hi
```

This updates `data/<slug>/<locale>/strings.json` — strings move from `"pending"` to `"ready"`.

---

## 6. Repeat Until Local Translation Completes

If the project has more pending strings than one batch:

```bash
# Check what's left
python3 wp-translate-ai.py status twentyten

# Generate next batch
python3 wp-translate-ai.py translate twentyten --batch 20 --locale hi

# ... AI translates & saves data/<slug>/<locale>/response.json ...

python3 wp-translate-ai.py apply twentyten --locale hi
```

When 100% of strings are translated locally, `translate` will notify you to launch `submit`.

---

## 7. Submit to GlotPress

Once strings are ready to submit:

```bash
python3 wp-translate-ai.py submit twentyten
# Or specify locale explicitly
python3 wp-translate-ai.py submit twentyten --locale hi
```

This launches an interactive helper UI at `http://localhost:8787`:

| Keyboard Shortcut | Action | What happens |
| :--- | :--- | :--- |
| Press `O` | **Open & Copy** | Copies translation to clipboard + opens GlotPress edit string page |
| On GlotPress | Double-click string → Cmd+V / Ctrl+V paste → click "Suggest" |
| Press `N` | **Done → Next** | Marks string submitted and advances to next string |
| Press `S` | **Skip** | Skips string for later review |

Progress is saved automatically in `data/<slug>/<locale>/strings.json`. You can exit (`Ctrl+C`) and resume anytime.

---

## 8. Check Status

```bash
# View status across all local projects and target locales
python3 wp-translate-ai.py status

# View status for a specific project
python3 wp-translate-ai.py status twentyten
```

Output shows: Project slug, Target Locale, Total strings, Pending, Translated locally, and Submitted to GlotPress.

---

## Interactive Wizard

For first-time users, run the setup wizard:

```bash
python3 wp-translate-ai.py init
```

It prompts for project type, slug/URL, and target locale setting.
