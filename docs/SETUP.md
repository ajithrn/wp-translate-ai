# Setup & Prerequisites

---

## System Requirements

- **Python 3.10+** (stdlib only, no pip packages)
- **Internet** (for fetching from translate.wordpress.org)
- **Browser** (for the submit helper)
- **AI-powered IDE or agent** (for translation)

---

## Install Python

### macOS

```bash
# Check
python3 --version

# Install via Homebrew (if needed)
brew install python3
```

### Ubuntu / Debian

```bash
sudo apt update && sudo apt install python3
```

### Windows

Download from [python.org/downloads](https://www.python.org/downloads/). Check "Add Python to PATH" during install.

---

## Project Setup

```bash
git clone <repo-url> wp-ml-translation
cd wp-ml-translation
python3 wp-ml-translate.py status
```

No `pip install`, no virtual env, no build step.

---

## AI Agent Setup

This tool works with any AI-powered coding environment that reads workspace files. The `AGENTS.md` file in the project root gives the AI all the context it needs.

**Compatible with:**
- Cursor
- Kiro
- Antigravity
- Windsurf
- Cline / Roo Code
- Any IDE with AI chat that reads workspace files

**Manual workflow (any AI):**
- Claude, ChatGPT, Gemini, or any chat interface
- Run `python3 wp-ml-translate.py translate <slug>`
- Copy `data/<slug>/prompt.md` content → paste to AI → save output as `data/<slug>/response.json`

---

## GlotPress Account

Needed only for **submitting** (not for fetching or translating):

1. Create account at [login.wordpress.org](https://login.wordpress.org/)
2. Log in at [translate.wordpress.org](https://translate.wordpress.org/)
3. Now you can suggest translations

---

## Verify Setup

```bash
python3 --version          # 3.10+
python3 wp-ml-translate.py fetch twentyten    # should fetch strings
python3 wp-ml-translate.py status             # should show counts
```

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `python3: command not found` | Install Python (see above) |
| `HTTPError: 404` | Wrong slug — check at translate.wordpress.org |
| `ConnectionError` / timeout | Check internet, retry later |
| Browser doesn't open | Go to `http://localhost:8787` manually |
| `'<slug>' കണ്ടെത്തിയില്ല` | Run `fetch` first |
