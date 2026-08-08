# AI Agent Prompts — wp-translate-ai

This file is automatically loaded by AI agents/IDEs. It tells the agent how to use the translation toolkit.

---

## Example User Prompts

These are the kinds of prompts a user will type. The agent should understand and execute them:

```
# First time — user gives a URL or slug to start
"Translate this: https://translate.wordpress.org/projects/wp-themes/twentyten/ml/default/"
"Translate pending strings for wp-themes/twentytwentyfour"
"Get pending translations for wp-plugins/woocommerce"
"Fetch Hindi translations for wp-plugins/woocommerce"
"Fetch official glossary for Hindi"
"Fetch glossary for Malayalam"

# Check what's already fetched
"Show translation status"
"What's the progress?"

# Continue a previously started project (only works if already fetched)
"Continue translating twentyten"
"Translate next batch for twentytwentyfour"

# Batch size / Count variations
"Translate all pending strings for twentyten in one go"
"Translate 50 pending strings for woocommerce"
"Translate next batch of 20 for twentytwentyfour"

# Submit completed translations
"Start submitting twentyten translations"
"Launch the submit helper for twentytwentyfour"

# Review before submitting
"Review the translations for twentyten before I submit"

# Add or set up a new locale (e.g. Hindi, Spanish, Italian, German)
"Add locale hi"
"Create new locale for Spanish"
"Set up locale it"
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
2. Check if `data/<slug>/<locale>/strings.json` exists
   - If NOT: run `python3 wp-translate-ai.py fetch <identifier>` (if user specified a count like "first 10 strings", pass `--limit 10` to fetch quickly without scraping the entire project)
   - If fetch fails with 404: ask the user for the correct project URL
3. Run: `python3 wp-translate-ai.py translate <slug> --batch <N|all>` (default: 15; if user asked for "50 strings", use `--batch 50`; if user asked for "all in one go", use `--batch all`)
4. Read the generated `data/<slug>/<locale>/prompt.md`
5. Follow ALL rules in that prompt file and translate the strings
6. Save output as `data/<slug>/<locale>/response.json` in this exact format:
   ```json
   [
     {"id": "12345", "translation": "..."}
   ]
   ```
7. Run: `python3 wp-translate-ai.py apply <slug>`
8. Run: `python3 wp-translate-ai.py status <slug>`
9. **Present Concise Summary & Next Steps**:
   - **Do NOT list individual translated strings** in the output response.
   - Show only high-level project status: Project Slug, Target Locale, Batch Count, Total Strings, Pending, and Translated.
   - **Provide Clear Next Steps**:
     - If **Pending > 0**: Offer to translate the next batch (`python3 wp-translate-ai.py translate <slug>`) or ask if the user wants to proceed automatically.
     - If **Pending == 0** (or user is ready to submit): Offer to launch the web submit helper (`python3 wp-translate-ai.py submit <slug>`) to submit translations to WordPress.org, and ask for confirmation before launching.

### Summary Output & Next Steps Standards

Whenever completing a translation step or status check:
- **Summary Format**: Focus strictly on general progress metrics (Total, Translated, Pending, Percentage). Keep response clean and readable.
- **Actionable Next Steps**: Always state the exact next CLI command (e.g. `translate`, `submit`, `review`) and offer to run it upon user confirmation.

### When user says "continue translating <slug>":

1. Check if `data/<slug>/<locale>/strings.json` exists
   - If NOT: tell the user "This project has not been fetched yet. Please provide a URL." and stop
2. Run `python3 wp-translate-ai.py status <slug>`
   - If **Pending == 0** (all strings translated locally): ask user for confirmation to launch the submit helper (`python3 wp-translate-ai.py submit <slug>`)
   - If **Pending > 0**: proceed with translation steps above

### When user says "show status" or "what's the progress":

Run: `python3 wp-translate-ai.py status`

### When user says "submit <slug>":

Run: `python3 wp-translate-ai.py submit <slug>`
Explain the browser workflow to the user.


### When user says "review <slug>":

Read `data/<slug>/<locale>/strings.json`, check all strings with `translation_status: "ready"` for:
- Unnatural/mechanical phrasing
- Placeholder mismatches
- Format/structure changes from original

### When user says "add locale <code>" or "create locale <language>":

1. Identify or ask for the 2-letter GlotPress locale code (e.g., `hi`, `es`, `it`, `de`, `fr`, `ur`, `ja`).
2. Run `python3 wp-translate-ai.py add-locale <code>` to fetch official GlotPress terms into `context/locales/<code>/glossary.json`.
3. Create a **comprehensive, fully-populated** `context/locales/<code>/prompt-template.md` modeled directly after `context/locales/ml/prompt-template.md`:
   - **MANDATORY**: Read `context/locales/ml/prompt-template.md` as the blueprint reference.
   - **MUST GENERATE REAL NATIVE SCRIPT EXAMPLES**: Do NOT leave generic English bullet points or placeholders! Translate and populate clear, authentic native-script examples in the target language (e.g., Hindi, Spanish, French, German) for **ALL** sections:
     1. **Header & Extension Note**: Link to `context/prompt-template.md`.
     2. **Strict Rules & Register**: Script rules and formal register definitions in native script (e.g., "आप/आपका" for Hindi, "Vous/Votre" for French, "Sie/Ihre" for German, "তাങ്കൾ/താങ്കളുടെ" for Malayalam).
     3. **Contextual Style Guide**: Native-script examples across 7 categories:
        - *UI Labels & Headers* (concise & direct native terms)
        - *Theme/Plugin Descriptions* (professional, engaging tone in native script)
        - *Error Messages / 404 Pages* (friendly & simple native phrasing)
        - *Narrative & Block Pattern Content* (expressive & natural native flow)
        - *Meta Text* (Posted on, Categories, Tags)
        - *Latin Lorem Ipsum* (leave untouched)
        - *Quotes* (expressive, living language in native script)
     4. **Common Mistakes to Avoid Table**: `Avoid This | Use This | Reason` comparison in target native script.
     5. **Format Preservation Examples**: Show Correct vs. Incorrect handling of HTML tags & placeholders in target native script.
     6. **Key Considerations**: Translator hints, Trac references, and plural handling.
4. Confirm to user: "Locale `<code>` initialized with official GlotPress glossary and comprehensive prompt template."

---

## Critical Translation Rules (Summary)

These are enforced via `context/prompt-template.md` and `context/locales/<locale>/prompt-template.md` but the agent MUST follow them:

1. **Minimal English script** — write standard UI terms, brand names, and product names (e.g. `Stripe Checkout` → `സ്ട്രൈപ്പ് ചെക്കൗട്ട്`, `WordPress` → `വേഡ്പ്രസ്സ്`) in the target locale's native script. Exception: ONLY technical acronyms/protocols stay in English (URL, HTML, CSS, PHP, FTP, HTTP, HTTPS, API, REST, RSS, JSON, SQL, XML, EDT, PM, AM) and font names (Source Serif Pro, Inter, etc.).
2. **Natural flow** — write as a native speaker of the target language would, not word-by-word
3. **Preserve format exactly** — same punctuation, quotes, sentence count as original
4. **Preserve placeholders** — %s, %1$s, HTML tags, &entities; — never change these
5. **Formal register** — always use the locale's formal register as defined in the locale prompt template
6. **Glossary mandatory** — use exact terms from the official GlotPress glossary in `context/locales/<locale>/glossary.json`

---

## File Locations

| File | Purpose |
|------|---------|
| `wp-translate-ai.py` | Main CLI entry point — run all commands through this |
| `context/prompt-template.md` | Full translation rules, glossary, examples |
| `data/<slug>/<locale>/strings.json` | Project data for a specific locale with all strings and their status |
| `data/<slug>/<locale>/prompt.md` | Generated prompt for AI (temporary) |
| `data/<slug>/<locale>/response.json` | AI output to apply (temporary) |
