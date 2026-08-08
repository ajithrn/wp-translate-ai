# Setup & Prerequisites

---

## System Requirements

- **Python 3.10+** (stdlib only, zero external pip packages)
- **Internet Connection** (for fetching from `translate.wordpress.org`)
- **Web Browser** (for the submit helper interface)
- **AI Environment** (Cursor, Antigravity, Kiro, Windsurf, Claude, ChatGPT, etc.)

---

## Install Python

### macOS

```bash
# Check installed version
python3 --version

# Install/update via Homebrew
brew install python3
```

### Ubuntu / Debian

```bash
sudo apt update && sudo apt install python3
```

### Windows

Download from [python.org/downloads](https://www.python.org/downloads/). Ensure "Add Python to PATH" is checked during installation.

---

## Installation & Setup

```bash
git clone https://github.com/ajithrn/wp-translate-ai.git
cd wp-translate-ai
python3 wp-translate-ai.py status
```

No `pip install`, no virtualenv, no external build steps.

---

## AI Agent Setup

This toolkit is designed for **Zero-API-Key** operation. It works natively with any AI-powered coding assistant that reads workspace context. The `AGENTS.md` file in the root directory instructs AI agents automatically.

**Natively Supported IDEs & Agents:**
- Antigravity
- Cursor
- Kiro
- Windsurf
- Claude Code / Cline / Roo Code

**Manual Workflow (Any AI Chat UI):**
- ChatGPT, Claude, Gemini, etc.
- Run `python3 wp-translate-ai.py translate <slug> --locale <locale>`
- Copy `data/<slug>/<locale>/prompt.md` content -> paste to AI -> save response as `data/<slug>/<locale>/response.json`

---

## GlotPress Account Setup

Needed only for **submitting** translations to WordPress.org (not required for fetching or translating):

1. Create a free account at [login.wordpress.org](https://login.wordpress.org/)
2. Log in at [translate.wordpress.org](https://translate.wordpress.org/)
3. You can now submit translation suggestions via the browser helper (`http://localhost:8787`).

---

## Verify Setup

```bash
python3 --version                             # Must be 3.10+
python3 wp-translate-ai.py add-locale ml      # Should download official terms & initialize locale
python3 wp-translate-ai.py fetch twentyten --locale ml   # Should scrape & parse pending strings
python3 wp-translate-ai.py status              # Should display translation status table
python3 tests/test_suite.py                  # Should run automated E2E test suite (20 tests)
```

---

## Troubleshooting

| Problem | Solution |
| :--- | :--- |
| `python3: command not found` | Install Python 3.10+ (see instructions above) |
| `HTTPError: 404` | Invalid project slug/type. Check exact URL at translate.wordpress.org |
| `ConnectionError` / Timeout | Check internet connection or retry in a few moments |
| Submit server browser tab doesn't open | Open `http://localhost:8787` manually in your browser |
| Project not found in `data/` | Run `python3 wp-translate-ai.py fetch <slug>` first |
