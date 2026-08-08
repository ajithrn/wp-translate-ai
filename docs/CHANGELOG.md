# Changelog

## v2.0.0 — 2026-08-09

### Major Rebranding & Universal Multi-Locale Architecture

- **Rebranded to `wp-translate-ai`** — Primary entry point is `wp-translate-ai.py`. All documentation and internal modules updated.
- **Universal Locale Architecture** — Support for any GlotPress locale via `--locale <code|slug>` (`ml`, `hi`, `fr`, `es`, `de`, `ja`, etc.).
- **Automatic Glossary Scraper (`lib/glossary.py`)** — Added `fetch-glossary` command to pull official GlotPress glossaries dynamically into `context/locales/<locale>/glossary.json`.
- **Hierarchical Prompt System** — Standardized base technical rules in `context/prompt-template.md` (English titles/rules) combined with locale-specific style guides in `context/locales/<locale>/prompt-template.md`.
- **Agent Locale Initialization Workflow** — Updated `AGENTS.md` to allow AI agents to create new locales on demand (`add locale <code>`).
- **Global Configuration (`config.json` & `lib/config.py`)** — Configuration manager for default locale settings, batch sizes, and user agent parameters.
- **Trac Reference Link Extractor & On-Demand Inspection** — Scrapes exact WordPress Trac source URLs (`reference_url`) into `strings.json` for code inspection when strings are ambiguous.
- **Locale-Scoped Data Directory Layout** — Restructured storage hierarchy to `data/<slug>/<locale>/` (`strings.json`, `prompt.md`, `response.json`), allowing simultaneous translation of the same project into multiple languages without data collisions.
- **Benchmark Prompt Templates (`ml` & `hi`)** — Created benchmark native-script prompt templates for Malayalam (`ml`) and Hindi (`hi`) with style guides across 7 categories, formal register rules, mistake comparison tables, and HTML format preservation examples.
- **Automated Test Suite (`tests/test_suite.py`)** — Included a 20-test E2E test suite in the repository workspace covering config resolution, glossary fetching, project scraping, status table rendering, translation batch generation, response applying, and browser helper UI APIs.
- **Fetch `--limit` Flag** — `fetch` command now supports `--limit <N>` (or `--max <N>`) to cap the number of strings scraped, enabling fast partial fetches for large projects.
- **Progressive Save During Fetch** — Fetcher now incrementally saves `strings.json` after each scraped page batch, preventing data loss if a long scrape is interrupted.
- **Translation Preservation on Re-Fetch** — Re-fetching a project merges fresh strings with existing translations, ensuring previously translated/submitted strings are never lost.
- **Agent Response & Next Steps Guidelines** — Updated `AGENTS.md` specifying concise high-level summaries without string dump listings, and mandatory actionable next steps prompting (e.g. submit helper / next batch).

## v1.1.0 — 2026-08-09

### Added & Improved

- **Sub-project support** — automatically detect and handle nested sub-project paths (e.g., `wp-plugins/gutenberg/stable`, `wp-plugins/gutenberg/dev`) in `fetcher` and CLI commands.
- **Improved completion UX** — `translate` command now detects when all local translations are ready and prompts the user directly to run `submit`.
- **Git ignore updates** — `.gitignore` updated to recursively exclude all generated project data subdirectories.
- **Agent workflow updates** — `AGENTS.md` updated to direct agents to launch submission when 100% of strings are translated locally.

---

## v1.0.0 — 2026-08-07

Initial release of translation toolkit.
