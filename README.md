# wp-translate-ai

**Universal AI-Powered WordPress Translation Toolkit**

Fetch pending strings from WordPress.org GlotPress for any language/locale, translate using zero-API-key AI IDE agents, and submit back with a 1-click browser helper.

---

## Key Features

- **Universal Locale Support**: Supports all 200+ WordPress.org GlotPress locales (`ml`, `hi`, `fr`, `es`, `de`, `ja`, etc.).
- **Zero API Key Cost**: Designed to work natively with AI IDE agents (Cursor, Antigravity, Kiro, Windsurf, Claude, ChatGPT, etc.) — no API keys or paid subscriptions required.
- **1-Click Submit Helper**: Interactive local web app on `http://localhost:8787` for rapid review & GlotPress submission.
- **Context & Glossary Engine**: Auto-fetches official GlotPress terminology and enforces strict placeholder protection (`%1$s`, HTML tags) and register rules.

---

## Prerequisites

- **Python 3.10+** (standard library only — zero pip dependencies)
- **AI-Enabled IDE** (Antigravity, Cursor, Kiro, Windsurf, Claude Code, etc.) or standalone LLM.
- **GlotPress Account** (free account on login.wordpress.org, required only when submitting translations).

For detailed installation and setup instructions across macOS, Linux, and Windows, see [`docs/SETUP.md`](docs/SETUP.md).

---

## Quick Start — Using AI Agents (Recommended)

Clone the repository and open the workspace folder in your AI-enabled IDE (Antigravity, Cursor, Kiro, Windsurf, Claude Code, etc.):

```bash
git clone https://github.com/ajithrn/wp-translate-ai.git
cd wp-translate-ai
```

Then simply type naturally in your AI chat panel:

```text
# Translate by URL or slug
"Translate this: https://translate.wordpress.org/projects/wp-themes/twentyten/ml/default/"

# Custom batching & counts
"Translate all pending strings for twentyten in one go"
"Translate 50 pending strings for woocommerce"

# Add or initialize a new locale
"Add locale hi"

# Check progress & submit
"Show translation status"
"Submit twentyten translations"
```

The AI agent automatically loads [`AGENTS.md`](AGENTS.md) and executes the entire workflow in the background!

---

## Manual CLI Commands (Power Users)

If you prefer running commands directly in your terminal or standalone chat UIs:

```bash
# 1. Initialize locale (fetches glossary & creates prompt template)
python3 wp-translate-ai.py add-locale ml

# 2. Fetch pending strings for a project
python3 wp-translate-ai.py fetch twentyten --locale ml

# 3. Generate translation prompt batch for your AI agent (default: 15, or --batch all)
python3 wp-translate-ai.py translate twentyten --batch 15

# 4. Apply AI response JSON (saved at data/twentyten/ml/response.json)
python3 wp-translate-ai.py apply twentyten --locale ml

# 5. Launch 1-click submit helper browser UI
python3 wp-translate-ai.py submit twentyten

# 6. View translation progress across all local projects
python3 wp-translate-ai.py status

# 7. Run automated test suite
python3 tests/test_suite.py
```

For advanced CLI options and detailed step-by-step instructions, see [`docs/USAGE.md`](docs/USAGE.md).

---

## Documentation

| File | Description |
|------|-------------|
| [AGENTS.md](AGENTS.md) | Agent execution instructions (auto-loaded by AI IDEs) |
| [docs/USAGE.md](docs/USAGE.md) | Complete CLI command guide & workflow documentation |
| [docs/SETUP.md](docs/SETUP.md) | System requirements & installation instructions |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | System design, components, and data flow diagrams |
| [docs/CHANGELOG.md](docs/CHANGELOG.md) | Release history & version updates |
| [context/prompt-template.md](context/prompt-template.md) | Universal technical & placeholder rules |
| [context/locales/ml/prompt-template.md](context/locales/ml/prompt-template.md) | Malayalam translation style guide |
