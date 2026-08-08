# AI Agent Prompts — wp-ml-translate

This file is automatically loaded by AI agents/IDEs. It tells the agent how to use the translation toolkit.

---

## Example User Prompts

These are the kinds of prompts a user will type. The agent should understand and execute them:

```
# First time — user gives a URL or slug to start
"Translate this: https://translate.wordpress.org/projects/wp-themes/twentyten/ml/default/"
"Translate pending strings for wp-themes/twentytwentyfour"
"Get pending Malayalam translations for wp-plugins/woocommerce"

# Check what's already fetched
"Show translation status"
"What's the progress?"

# Continue a previously started project (only works if already fetched)
"Continue translating twentyten"
"Translate next batch for twentytwentyfour"

# Submit completed translations
"Start submitting twentyten translations"
"Launch the submit helper for twentytwentyfour"

# Review before submitting
"Review the translations for twentyten before I submit"
```

**Important:** If the user says "translate <slug>" but `data/<slug>/strings.json` doesn't exist, run `fetch` first. If fetch fails (slug not found), ask the user for the correct URL.

---

## How URLs Map to Projects

The tool auto-detects project type and slug from any URL format:

| User gives | Detected type | Detected slug |
|------------|---------------|---------------|
| `https://translate.wordpress.org/projects/wp-themes/twentyten/ml/default/` | wp-themes | twentyten |
| `https://translate.wordpress.org/projects/wp-plugins/woocommerce/ml/default/` | wp-plugins | woocommerce |
| `https://translate.wordpress.org/locale/ml/default/wp-themes/twentyten/` | wp-themes | twentyten |
| `wp-themes/twentytwentyfour` | wp-themes | twentytwentyfour |
| `wp-plugins/jetpack` | wp-plugins | jetpack |
| `twentyten` (bare slug) | wp-themes | twentyten |

**Listing pages** like `/locale/ml/default/wp-themes/?filter=&s=Twenty` are NOT single projects. Tell the user to provide specific project URLs or slugs.

---

## Agent Execution Guide

### When user says "translate this <URL>" or "translate <slug>":

1. Parse the URL/slug to get the project identifier
2. Check if `data/<slug>/strings.json` exists
   - If NOT: run `python3 wp-ml-translate.py fetch <identifier>` first
   - If fetch fails with 404: ask the user for the correct project URL
3. Run: `python3 wp-ml-translate.py translate <slug> --batch 15`
4. Read the generated `data/<slug>/prompt.md`
5. Follow ALL rules in that prompt file and translate the strings
6. Save output as `data/<slug>/response.json` in this exact format:
   ```json
   [
     {"id": "12345", "translation": "മലയാള വിവർത്തനം"},
     {"id": "12346", "translation": "..."}
   ]
   ```
7. Run: `python3 wp-ml-translate.py apply <slug>`
8. Run: `python3 wp-ml-translate.py status <slug>`
9. If pending strings remain, repeat from step 3

### When user says "continue translating <slug>":

1. Check if `data/<slug>/strings.json` exists
   - If NOT: tell the user "ഈ പ്രോജക്ട് ഇതുവരെ fetch ചെയ്തിട്ടില്ല. URL നൽകൂ." and stop
2. Run `python3 wp-ml-translate.py status <slug>`
   - If **Pending == 0** (all strings translated locally): launch submission with `python3 wp-ml-translate.py submit <slug>`
   - If **Pending > 0**: proceed with step 3 above (translate & apply next batch)

### When user says "show status" or "what's the progress":

Run: `python3 wp-ml-translate.py status`

### When user says "submit <slug>":

Run: `python3 wp-ml-translate.py submit <slug>`
Explain the browser workflow to the user.


### When user says "review <slug>":

Read `data/<slug>/strings.json`, check all strings with `translation_status: "ready"` for:
- English script present (should be zero)
- Unnatural/mechanical phrasing
- Placeholder mismatches
- Format/structure changes from original

---

## Critical Translation Rules (Summary)

These are enforced via `context/prompt-template.md` but the agent MUST follow them:

1. **Minimal English script** — all text in മലയാള ലിപി (menu→മെനു, WordPress→വേഡ്പ്രസ്സ്). Exception: technical acronyms/protocols stay in English (URL, HTML, CSS, PHP, FTP, HTTP, HTTPS, API, REST, RSS, JSON, SQL, XML, EDT, PM, AM) and font names (Source Serif Pro, Inter, etc.)
2. **Natural flow** — write as a native Malayalam speaker would, not word-by-word
3. **Preserve format exactly** — same punctuation, quotes, sentence count as original
4. **Preserve placeholders** — %s, %1$s, HTML tags, &entities; — never change these
5. **Formal register** — താങ്കൾ/താങ്കളുടെ always, never നിങ്ങൾ
6. **Glossary mandatory** — use exact terms from the glossary table in prompt-template.md

---

## File Locations

| File | Purpose |
|------|---------|
| `wp-ml-translate.py` | CLI entry point — run all commands through this |
| `context/prompt-template.md` | Full translation rules, glossary, examples |
| `data/<slug>/strings.json` | Project data with all strings and their status |
| `data/<slug>/prompt.md` | Generated prompt for AI (temporary) |
| `data/<slug>/response.json` | AI output to apply (temporary) |
