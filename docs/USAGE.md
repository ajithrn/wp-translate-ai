# Usage Guide

Step-by-step guide for translating WordPress projects into Malayalam.

---

## Workflow Overview

```
fetch → translate → apply → (repeat if needed) → submit
```

---

## 1. Fetch Pending Strings

Give a project URL or slug. The tool scrapes GlotPress and saves pending strings.

```bash
# By slug (assumes wp-themes)
python3 wp-ml-translate.py fetch twentyten

# By type/slug
python3 wp-ml-translate.py fetch wp-plugins/woocommerce

# By full URL
python3 wp-ml-translate.py fetch "https://translate.wordpress.org/projects/wp-themes/twentyten/ml/default/"

# Multiple projects at once
python3 wp-ml-translate.py fetch twentyten twentyeleven twentytwelve
```

Output: `data/<slug>/strings.json`

---

## 2. Generate Translation Prompt

Creates a prompt file with rules + glossary + a batch of strings for AI to translate.

```bash
# Default batch of 10
python3 wp-ml-translate.py translate twentyten

# Larger batch
python3 wp-ml-translate.py translate twentyten --batch 20
```

Output: `data/<slug>/prompt.md`

---

## 3. Feed Prompt to AI

### Option A: Using Kiro or AI-powered IDE
Just type:
```
"Translate this: https://translate.wordpress.org/projects/wp-themes/twentyten/ml/default/"
```
The agent reads AGENTS.md and handles everything automatically.

### Option B: Manual (any AI)
1. Open `data/<slug>/prompt.md`
2. Copy its full content
3. Paste into Claude / ChatGPT / any AI
4. Copy the JSON output
5. Save as `data/<slug>/response.json`

---

## 4. Apply Translations

Merges the AI response into the project data.

```bash
python3 wp-ml-translate.py apply twentyten
```

This updates `strings.json` — strings move from "pending" to "ready".

---

## 5. Repeat If Needed

If the project has more strings than one batch:

```bash
# Check what's left
python3 wp-ml-translate.py status twentyten

# Generate next batch
python3 wp-ml-translate.py translate twentyten --batch 20

# ... feed to AI, save response ...

python3 wp-ml-translate.py apply twentyten
```

Repeat until status shows 0 pending.

---

## 6. Submit to GlotPress

Once all strings are translated ("ready" status):

```bash
python3 wp-ml-translate.py submit twentyten
```

This opens a browser UI at `http://localhost:8787`:

| Action | What happens |
|--------|-------------|
| Click "തുറക്കുക + കോപ്പി" (or press `O`) | Copies translation to clipboard + opens GlotPress page |
| On GlotPress | Double-click string → Cmd+V paste → click "Suggest" |
| Click "സമർപ്പിച്ചു → അടുത്തത്" (or press `N`) | Marks done, shows next string |
| Click "ഒഴിവാക്കുക" (or press `S`) | Skips this string |

Progress is saved automatically. You can Ctrl+C and resume later.

---

## 7. Check Status

```bash
# All projects
python3 wp-ml-translate.py status

# Specific project
python3 wp-ml-translate.py status twentyten
```

Output shows: total strings, pending, translated, submitted.

---

## Interactive Setup

For first-time users, run the interactive wizard:

```bash
python3 wp-ml-translate.py init
```

It asks what type of project (theme/plugin/core/URL) and guides you through.

---

## Tips

- **Batch size**: 10-15 strings per batch gives best AI quality. Too large → quality drops.
- **Review before submit**: Read through `strings.json` or use "review" agent prompt before submitting.
- **Re-fetch**: Run fetch again to update stats and get any newly added strings.
- **Multiple projects**: Fetch several, then translate one by one.
- **Skipped strings**: They stay in the JSON. Come back to them anytime.
