# Changelog

## v1.1.0 — 2026-08-09

### Added & Improved

- **Sub-project support** — automatically detect and handle nested sub-project paths (e.g., `wp-plugins/gutenberg/stable`, `wp-plugins/gutenberg/dev`) in `fetcher` and CLI commands.
- **Improved completion UX** — `translate` command now detects when all local translations are ready and prompts the user directly to run `submit`.
- **Git ignore updates** — `.gitignore` updated to recursively exclude all generated project data subdirectories.
- **Agent workflow updates** — `AGENTS.md` updated to direct agents to launch submission when 100% of strings are translated locally.

## v1.0.0 — 2026-08-07


Initial release of wp-ml-translate toolkit.

### Features

- **CLI tool** (`wp-ml-translate.py`) with commands: `init`, `fetch`, `translate`, `apply`, `submit`, `status`
- **GlotPress fetcher** — scrapes pending ml_IN strings from any WordPress project (themes, plugins, core)
- **URL parser** — accepts full URLs, locale URLs, type/slug paths, or bare slugs
- **Translation engine** — generates AI prompts with rules, glossary, style guide, and context
- **Response parser** — merges AI translation output back into project data
- **Submit helper** — local browser UI for one-at-a-time GlotPress submission with clipboard copy and progress tracking
- **Per-project data** — each project gets its own folder under `data/<slug>/`
- **AI agent support** — `AGENTS.md` in root auto-loaded by IDEs (Cursor, Kiro, Antigravity, Windsurf, etc.)

### Translation Quality

- Prompt template enforces zero English script, natural Malayalam flow
- Mandatory glossary with 35+ WordPress terms
- Style guide per context type (UI labels, narratives, errors, meta)
- Format preservation rules (punctuation, structure, placeholders)
- Good/bad examples and common mistakes table

### Documentation

- `README.md` — quick start and example prompts
- `AGENTS.md` — AI agent execution instructions
- `docs/USAGE.md` — step-by-step workflow guide
- `docs/SETUP.md` — prerequisites, installation, troubleshooting
- `docs/ARCHITECTURE.md` — technical internals, data flow, components
- `context/prompt-template.md` — full translation rules and glossary
