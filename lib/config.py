"""
Configuration & Locale Manager for wp-translate-ai
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONFIG_FILE = ROOT / "config.json"

DEFAULT_CONFIG = {
    "default_locale": "ml",
    "default_set_slug": "default",
    "default_batch_size": 15,
    "user_agent": "wp-translate-ai/2.0",
}


def load_config() -> dict:
    """Load configuration from config.json with fallback defaults."""
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return {**DEFAULT_CONFIG, **data}
        except Exception:
            pass
    return DEFAULT_CONFIG.copy()


def get_locale(args_locale: str | None = None) -> str:
    """Get target locale code from CLI args or config."""
    if args_locale:
        return args_locale.strip().lower()
    return load_config().get("default_locale", "ml")
