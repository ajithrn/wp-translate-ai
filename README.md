# wp-ml-translate

WordPress Malayalam (ml_IN) translation toolkit. Fetches pending strings from GlotPress, translates using AI, submits back.

## Quick Start

```bash
python3 wp-ml-translate.py fetch twentyten
python3 wp-ml-translate.py translate twentyten
# → feed prompt to AI → save response
python3 wp-ml-translate.py apply twentyten
python3 wp-ml-translate.py submit twentyten
```

## Requirements

- Python 3.10+ (stdlib only)
- Any AI-powered IDE or agent (Cursor, Kiro, Antigravity, Windsurf, Claude, ChatGPT, etc.)

## Usage

Give a URL or slug → the tool does the rest:

```bash
python3 wp-ml-translate.py fetch twentyten
python3 wp-ml-translate.py fetch wp-plugins/woocommerce
python3 wp-ml-translate.py fetch "https://translate.wordpress.org/projects/wp-themes/twentyten/ml/default/"
python3 wp-ml-translate.py status
```

## With AI Agents

If your IDE supports agent files, just type naturally:

```
"Translate this: https://translate.wordpress.org/projects/wp-themes/twentyten/ml/default/"
"Translate pending strings for wp-plugins/woocommerce"
"Show translation status"
"Continue translating twentyten"    ← only after initial fetch
"Submit twentyten translations"
```

The agent reads `AGENTS.md` and handles everything.

## Docs

| File | What |
|------|------|
| [AGENTS.md](AGENTS.md) | Agent instructions (auto-loaded by IDEs) |
| [docs/USAGE.md](docs/USAGE.md) | Step-by-step workflow |
| [docs/SETUP.md](docs/SETUP.md) | Prerequisites + troubleshooting |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Technical internals |
| [context/prompt-template.md](context/prompt-template.md) | Translation rules + glossary |
