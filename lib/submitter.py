#!/usr/bin/env python3
"""
GlotPress Translation Submission Helper

A local web server that shows one translated string at a time.
- Opens the GlotPress URL in a new browser tab
- Copies the translation to clipboard automatically
- Click "Done -> Next" to mark current as submitted and advance
- Progress is saved back to strings.json

Usage (via main CLI):
    python3 wp-translate-ai.py submit <slug> [--port 8787]
"""

from __future__ import annotations

import json
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse


def _load_strings(slug: str, data_dir: Path, locale: str = "") -> tuple[dict, list[dict]]:
    """Load project data and return (project_meta, ready_strings)."""
    strings_file = data_dir / slug / locale / "strings.json"
    with open(strings_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    project = data["project"]
    # Only show strings that have translations and aren't yet submitted
    ready = [
        s for s in data["strings"]
        if s.get("translation", "").strip() and not s.get("submitted", False)
    ]
    return project, ready


def _save_submitted(slug: str, data_dir: Path, submitted_ids: set, locale: str = ""):
    """Mark strings as submitted in the strings.json file."""
    strings_file = data_dir / slug / locale / "strings.json"
    with open(strings_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    for s in data["strings"]:
        if s["id"] in submitted_ids:
            s["submitted"] = True

    with open(strings_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def _build_html(slug: str, project: dict) -> str:
    """Build the submission helper HTML page."""
    loc = project.get("locale", "target locale").upper()
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Submit: {slug} — WP Translation Helper</title>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #1a1a2e;
            color: #e0e0e0;
            min-height: 100vh;
            padding: 20px;
        }}
        .container {{ max-width: 900px; margin: 0 auto; }}
        .header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            padding: 15px 20px;
            background: #16213e;
            border-radius: 10px;
        }}
        .header h1 {{ font-size: 1.3em; color: #4fc3f7; }}
        .progress-bar {{
            width: 200px;
            height: 8px;
            background: #333;
            border-radius: 4px;
            overflow: hidden;
        }}
        .progress-bar-fill {{
            height: 100%;
            background: linear-gradient(90deg, #4fc3f7, #00e676);
            transition: width 0.3s;
        }}
        .progress-text {{ font-size: 0.85em; color: #aaa; margin-top: 4px; text-align: right; }}
        .card {{
            background: #16213e;
            border-radius: 12px;
            padding: 25px;
            margin-bottom: 15px;
            border: 1px solid #2a3a5e;
        }}
        .card-label {{
            font-size: 0.75em;
            text-transform: uppercase;
            letter-spacing: 1px;
            color: #888;
            margin-bottom: 8px;
        }}
        .theme-badge {{
            display: inline-block;
            padding: 3px 10px;
            background: #0a3d62;
            color: #4fc3f7;
            border-radius: 12px;
            font-size: 0.8em;
            margin-bottom: 10px;
        }}
        .original-text {{
            font-size: 1em;
            line-height: 1.6;
            color: #ccc;
            padding: 12px;
            background: #0f1a2e;
            border-radius: 8px;
            border-left: 3px solid #4fc3f7;
            word-break: break-word;
            max-height: 150px;
            overflow-y: auto;
        }}
        .translation-text {{
            font-size: 1.1em;
            line-height: 1.8;
            color: #fff;
            padding: 15px;
            background: #0f2a1e;
            border-radius: 8px;
            border-left: 3px solid #00e676;
            word-break: break-word;
            max-height: 200px;
            overflow-y: auto;
        }}
        .meta-row {{
            display: flex;
            gap: 15px;
            flex-wrap: wrap;
            margin-top: 10px;
        }}
        .meta-item {{
            font-size: 0.8em;
            color: #888;
        }}
        .meta-item strong {{ color: #aaa; }}
        .actions {{
            display: flex;
            gap: 12px;
            align-items: center;
            margin-top: 20px;
        }}
        .btn {{
            padding: 12px 24px;
            border: none;
            border-radius: 8px;
            font-size: 1em;
            cursor: pointer;
            font-weight: 600;
            transition: all 0.2s;
        }}
        .btn-primary {{
            background: #00e676;
            color: #1a1a2e;
        }}
        .btn-primary:hover {{ background: #69f0ae; transform: translateY(-1px); }}
        .btn-secondary {{
            background: #4fc3f7;
            color: #1a1a2e;
        }}
        .btn-secondary:hover {{ background: #81d4fa; transform: translateY(-1px); }}
        .btn-skip {{
            background: transparent;
            color: #ff8a65;
            border: 1px solid #ff8a65;
        }}
        .btn-skip:hover {{ background: #ff8a6510; }}
        .copy-toast {{
            position: fixed;
            top: 20px;
            right: 20px;
            background: #00e676;
            color: #1a1a2e;
            padding: 10px 20px;
            border-radius: 8px;
            font-weight: 600;
            display: none;
            z-index: 999;
            animation: fadeIn 0.3s;
        }}
        @keyframes fadeIn {{ from {{ opacity: 0; transform: translateY(-10px); }} to {{ opacity: 1; transform: translateY(0); }} }}
        .done-screen {{
            text-align: center;
            padding: 60px 20px;
        }}
        .done-screen h2 {{ color: #00e676; font-size: 2em; margin-bottom: 10px; }}
        .done-screen p {{ color: #aaa; font-size: 1.1em; }}
        .keyboard-hint {{
            font-size: 0.75em;
            color: #666;
            margin-top: 8px;
        }}
        .keyboard-hint kbd {{
            background: #333;
            padding: 2px 6px;
            border-radius: 3px;
            border: 1px solid #555;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Submit: {slug}</h1>
            <div>
                <div class="progress-bar">
                    <div class="progress-bar-fill" id="progressFill"></div>
                </div>
                <div class="progress-text" id="progressText"></div>
            </div>
        </div>
        <div id="content"></div>
    </div>
    <div class="copy-toast" id="toast">Translation copied to clipboard!</div>

    <script>
        let data = null;

        async function loadData() {{
            const resp = await fetch('/api/current');
            data = await resp.json();
            render();
        }}

        function render() {{
            const total = data.total;
            const submitted = data.submitted_count;
            const pct = total > 0 ? (submitted / total * 100) : 0;

            document.getElementById('progressFill').style.width = pct + '%';
            document.getElementById('progressText').textContent =
                submitted + ' / ' + total + ' submitted (' + Math.round(pct) + '%)';

            if (!data.current) {{
                document.getElementById('content').innerHTML = `
                    <div class="done-screen">
                        <h2>All done!</h2>
                        <p>All ${{total}} translations have been submitted.</p>
                    </div>
                `;
                return;
            }}

            const s = data.current;
            const origDisplay = escapeHtml(s.original).substring(0, 500);
            const transDisplay = escapeHtml(s.translation);

            document.getElementById('content').innerHTML = `
                <div class="card">
                    <div class="card-label">Original String</div>
                    <span class="theme-badge">{slug}</span>
                    <span class="meta-item" style="margin-left:10px"><strong>ID:</strong> ${{s.id}}</span>
                    <div class="original-text" style="margin-top:10px">${{origDisplay}}</div>
                    ${{s.context ? `<div class="meta-row"><div class="meta-item"><strong>Context:</strong> ${{escapeHtml(s.context)}}</div></div>` : ''}}
                </div>

                <div class="card">
                    <div class="card-label">Target Translation ({loc})</div>
                    <div class="translation-text">${{transDisplay}}</div>
                </div>

                <div class="actions">
                    <button class="btn btn-secondary" onclick="openAndCopy()">
                        Open GlotPress & Copy
                    </button>
                    <button class="btn btn-primary" onclick="markDoneNext()">
                        Done \\u2192 Next
                    </button>
                    <button class="btn btn-skip" onclick="skipNext()">
                        Skip
                    </button>
                </div>
                <div class="keyboard-hint">
                    Shortcuts: <kbd>O</kbd> Open & Copy | <kbd>N</kbd> Done \\u2192 Next | <kbd>S</kbd> Skip
                </div>
            `;
        }}

        function escapeHtml(text) {{
            if (!text) return '';
            return text.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
        }}

        async function openAndCopy() {{
            if (!data.current) return;
            try {{
                await navigator.clipboard.writeText(data.current.translation);
                showToast('Translation copied to clipboard!');
            }} catch(e) {{
                const ta = document.createElement('textarea');
                ta.value = data.current.translation;
                document.body.appendChild(ta);
                ta.select();
                document.execCommand('copy');
                document.body.removeChild(ta);
                showToast('Translation copied to clipboard!');
            }}
            window.open(data.current.permalink, '_blank');
        }}

        async function markDoneNext() {{
            if (!data.current) return;
            const resp = await fetch('/api/done', {{ method: 'POST' }});
            data = await resp.json();
            render();
        }}

        async function skipNext() {{
            if (!data.current) return;
            const resp = await fetch('/api/skip', {{ method: 'POST' }});
            data = await resp.json();
            render();
        }}

        function showToast(msg) {{
            const t = document.getElementById('toast');
            t.textContent = msg;
            t.style.display = 'block';
            setTimeout(() => {{ t.style.display = 'none'; }}, 2500);
        }}

        document.addEventListener('keydown', (e) => {{
            if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
            if (e.key === 'o' || e.key === 'O') openAndCopy();
            if (e.key === 'n' || e.key === 'N') markDoneNext();
            if (e.key === 's' || e.key === 'S') skipNext();
        }});

        loadData();
    </script>
</body>
</html>"""


class _Handler(BaseHTTPRequestHandler):
    slug = ""
    locale = ""
    data_dir = None
    strings = []
    current_index = 0
    submitted_ids = set()

    def log_message(self, format, *args):
        pass  # Suppress default logging

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path in ("/", "/index.html"):
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            html = _build_html(_Handler.slug, getattr(_Handler, "project", {}))
            self.wfile.write(html.encode("utf-8"))
        elif parsed.path == "/api/current":
            self._send_state()
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/done":
            idx = _Handler.current_index
            if idx < len(_Handler.strings):
                sid = _Handler.strings[idx]["id"]
                _Handler.submitted_ids.add(sid)
                _Handler.current_index = idx + 1
                # Skip already-submitted
                while (_Handler.current_index < len(_Handler.strings) and
                       _Handler.strings[_Handler.current_index]["id"] in _Handler.submitted_ids):
                    _Handler.current_index += 1
                # Persist
                _save_submitted(_Handler.slug, _Handler.data_dir, _Handler.submitted_ids, locale=_Handler.locale)
            self._send_state()
        elif parsed.path == "/api/skip":
            _Handler.current_index += 1
            while (_Handler.current_index < len(_Handler.strings) and
                   _Handler.strings[_Handler.current_index]["id"] in _Handler.submitted_ids):
                _Handler.current_index += 1
            self._send_state()
        else:
            self.send_response(404)
            self.end_headers()

    def _send_state(self):
        idx = _Handler.current_index
        current = _Handler.strings[idx] if idx < len(_Handler.strings) else None
        resp = {
            "total": len(_Handler.strings),
            "submitted_count": len(_Handler.submitted_ids),
            "current_index": idx,
            "current": current,
        }
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(json.dumps(resp, ensure_ascii=False).encode("utf-8"))


def run_server(slug: str, data_dir: Path, port: int = 8787, locale: str = ""):
    """Start the submission helper server for a project."""
    print(f"\n  Loading translations for '{slug}' [{locale}]...")

    project, ready_strings = _load_strings(slug, data_dir, locale=locale)

    if not ready_strings:
        print("  No translated strings ready for submission.")
        print("  Run 'translate' first to generate translations.")
        return

    _Handler.slug = slug
    _Handler.locale = locale
    _Handler.project = project
    _Handler.data_dir = data_dir
    _Handler.strings = ready_strings
    _Handler.current_index = 0
    _Handler.submitted_ids = set()

    total = len(ready_strings)
    print(f"  {total} strings ready for submission")
    print(f"\n  Opening http://localhost:{port} in your browser...\n")
    print("  Workflow:")
    print("    1. Click 'Open GlotPress & Copy' — opens the translate page, copies translation")
    print("    2. On GlotPress: double-click the string, paste (Cmd+V), click 'Suggest'")
    print("    3. Back here: click 'Done → Next' to advance")
    print(f"\n  Press Ctrl+C to stop.\n")

    server = HTTPServer(("localhost", port), _Handler)
    webbrowser.open(f"http://localhost:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  Stopped. Progress saved.")
        server.server_close()
