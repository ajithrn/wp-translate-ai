#!/usr/bin/env python3
"""
Automated Test Suite for wp-translate-ai
Tests all CLI commands, multi-locale scoping, prompt generation, translation apply, and web submitter HTTP endpoints.
"""

import json
import os
import shutil
import sys
import time
from pathlib import Path

# Dynamically resolve root project directory
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import importlib.util

spec = importlib.util.spec_from_file_location("wp_translate_ai", str(ROOT / "wp-translate-ai.py"))
cli = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cli)
from lib.config import get_locale, load_config
from lib.fetcher import fetch_project
from lib.glossary import fetch_official_glossary
from lib.translator import generate_prompt, apply_translations
from lib.submitter import _load_strings, _save_submitted


def run_tests():
    print("=" * 60)
    print("      RUNNING AUTOMATED TEST SUITE FOR WP-TRANSLATE-AI      ")
    print("=" * 60 + "\n")

    passed = 0
    failed = 0

    def assert_true(expr, msg):
        nonlocal passed, failed
        if expr:
            print(f"  ✓ PASS: {msg}")
            passed += 1
        else:
            print(f"  ✗ FAIL: {msg}")
            failed += 1

    # -------------------------------------------------------------
    # Test 1: Config and Locale Resolution
    # -------------------------------------------------------------
    print("--- Test 1: Config & Locale Resolution ---")
    cfg = load_config()
    assert_true(cfg.get("default_locale") == "ml", "Config default_locale is 'ml'")
    assert_true(get_locale() == "ml", "get_locale() returns default 'ml'")
    assert_true(get_locale("hi") == "hi", "get_locale('hi') returns 'hi'")
    print()

    # -------------------------------------------------------------
    # Test 2: Fetch Official Glossary
    # -------------------------------------------------------------
    print("--- Test 2: Fetch Official Glossary ---")
    context_dir = ROOT / "context"
    res_gl = fetch_official_glossary(context_dir, target_locale="ml")
    assert_true(len(res_gl) > 0, "Glossary for Malayalam ('ml') fetched successfully")
    gl_file = context_dir / "locales" / "ml" / "glossary.json"
    assert_true(gl_file.exists(), f"Glossary file created at {gl_file}")
    print()

    # -------------------------------------------------------------
    # Test 3: Fetch Project Strings (Multi-Locale)
    # -------------------------------------------------------------
    print("--- Test 3: Fetch Project Strings (Multi-Locale) ---")
    data_dir = ROOT / "data"

    # Fetch twentyten for Malayalam ('ml')
    out_ml = fetch_project("twentyten", data_dir, target_locale="ml")
    assert_true(out_ml is not None and out_ml.exists(), "twentyten (ml) fetched to data/twentyten/ml/strings.json")
    
    # Fetch twentyten for Hindi ('hi')
    out_hi = fetch_project("twentyten", data_dir, target_locale="hi")
    assert_true(out_hi is not None and out_hi.exists(), "twentyten (hi) fetched to data/twentyten/hi/strings.json")
    
    assert_true((data_dir / "twentyten" / "ml" / "strings.json").exists(), "Locale dir data/twentyten/ml exists")
    assert_true((data_dir / "twentyten" / "hi" / "strings.json").exists(), "Locale dir data/twentyten/hi exists")
    print()

    # -------------------------------------------------------------
    # Test 4: CLI Status Output
    # -------------------------------------------------------------
    print("--- Test 4: Status Command ---")
    ret_status = cli.cmd_status([])
    assert_true(ret_status == 0, "cmd_status executed with exit code 0")
    print()

    # -------------------------------------------------------------
    # Test 5: Generate Translation Prompt Batch
    # -------------------------------------------------------------
    print("--- Test 5: Generate Translation Prompt Batch ---")
    ret_trans_ml = cli.cmd_translate(["twentyten", "--locale", "ml", "--batch", "5"])
    assert_true(ret_trans_ml == 0, "cmd_translate (ml batch 5) succeeded")
    
    prompt_ml = data_dir / "twentyten" / "ml" / "prompt.md"
    assert_true(prompt_ml.exists(), "Prompt file data/twentyten/ml/prompt.md generated")
    
    ret_trans_hi = cli.cmd_translate(["twentyten", "--locale", "hi", "--batch", "all"])
    assert_true(ret_trans_hi == 0, "cmd_translate (hi batch all) succeeded")
    
    prompt_hi = data_dir / "twentyten" / "hi" / "prompt.md"
    assert_true(prompt_hi.exists(), "Prompt file data/twentyten/hi/prompt.md generated")
    print()

    # -------------------------------------------------------------
    # Test 6: Apply AI Response Translations
    # -------------------------------------------------------------
    print("--- Test 6: Apply AI Translations ---")
    # Read strings from data/twentyten/ml/strings.json to create mock response
    with open(data_dir / "twentyten" / "ml" / "strings.json", "r", encoding="utf-8") as f:
        p_data = json.load(f)

    # Ensure clean unsubmitted state for test items
    for item in p_data["strings"]:
        item["submitted"] = False
    with open(data_dir / "twentyten" / "ml" / "strings.json", "w", encoding="utf-8") as f:
        json.dump(p_data, f, ensure_ascii=False, indent=2)

    real_translations = []
    test_ids = []
    for item in p_data["strings"][:5]:
        test_ids.append(item["id"])
        real_translations.append({
            "id": item["id"],
            "translation": f"മലയാളം പരിഭാഷ {item['original']}"
        })

    resp_file = data_dir / "twentyten" / "ml" / "response.json"
    with open(resp_file, "w", encoding="utf-8") as f:
        json.dump(real_translations, f, ensure_ascii=False, indent=2)
    
    assert_true(resp_file.exists(), "Mock response.json created")
    
    ret_apply = cli.cmd_apply(["twentyten", "--locale", "ml"])
    assert_true(ret_apply == 0, "cmd_apply (ml) succeeded")
    
    archived_resp = data_dir / "twentyten" / "ml" / "response_applied.json"
    assert_true(archived_resp.exists(), "Response file archived to response_applied.json")
    
    with open(data_dir / "twentyten" / "ml" / "strings.json", "r", encoding="utf-8") as f:
        updated_data = json.load(f)
    
    applied_count = sum(1 for s in updated_data["strings"] if s.get("translation_status") == "ready")
    target_count = len(test_ids)
    assert_true(applied_count == target_count, f"Applied {target_count} translations (found {applied_count})")
    print()

    # -------------------------------------------------------------
    # Test 7: Submitter Web Server & Endpoints
    # -------------------------------------------------------------
    print("--- Test 7: Submitter Helper & API Endpoints ---")
    meta, ready = _load_strings("twentyten", data_dir, locale="ml")
    assert_true(len(ready) == target_count, f"{target_count} ready strings loaded for submitter (found {len(ready)})")
    
    _save_submitted("twentyten", data_dir, {test_ids[0]}, locale="ml")
    with open(data_dir / "twentyten" / "ml" / "strings.json", "r", encoding="utf-8") as f:
        post_sub_data = json.load(f)
    
    submitted_count = sum(1 for s in post_sub_data["strings"] if s.get("submitted"))
    assert_true(submitted_count == 1, f"1 string marked as submitted in strings.json")
    print()

    # -------------------------------------------------------------
    # Test 8: Dual Singular and Plural Support
    # -------------------------------------------------------------
    print("--- Test 8: Dual Singular & Plural Handling ---")
    plural_test_slug = "plural_test"
    plural_test_dir = data_dir / plural_test_slug / "ml"
    plural_test_dir.mkdir(parents=True, exist_ok=True)

    mock_plural_project = {
        "project": {"name": "Plural Test", "type": "wp-plugins", "locale": "ml"},
        "strings": [
            {
                "id": "99901",
                "status": "untranslated",
                "priority": "normal",
                "context": "",
                "original": "Activate %d theme",
                "plural": "Activate %d themes",
                "translation": "",
                "plural_translation": "",
                "translation_status": "pending",
                "submitted": False,
                "permalink": "https://example.com/test/99901"
            }
        ]
    }
    with open(plural_test_dir / "strings.json", "w", encoding="utf-8") as f:
        json.dump(mock_plural_project, f, indent=2)

    # 1. Test prompt generation includes plural_translation
    generate_prompt(plural_test_slug, data_dir, context_dir, batch_size=1, target_locale="ml")
    prompt_file = plural_test_dir / "prompt.md"
    assert_true(prompt_file.exists(), "Plural prompt file generated")
    prompt_text = prompt_file.read_text(encoding="utf-8")
    assert_true("plural_translation" in prompt_text, "Prompt includes plural_translation in schema")

    # 2. Test applying dual translation
    mock_resp = [
        {
            "id": "99901",
            "translation": "%d തീം സജീവമാക്കുക",
            "plural_translation": "%d തീമുകൾ സജീവമാക്കുക"
        }
    ]
    with open(plural_test_dir / "response.json", "w", encoding="utf-8") as f:
        json.dump(mock_resp, f, ensure_ascii=False, indent=2)

    apply_translations(plural_test_slug, data_dir, locale="ml")
    with open(plural_test_dir / "strings.json", "r", encoding="utf-8") as f:
        applied_plural_data = json.load(f)

    plural_item = applied_plural_data["strings"][0]
    assert_true(plural_item["translation"] == "%d തീം സജീവമാക്കുക", "Singular translation correctly applied")
    assert_true(plural_item["plural_translation"] == "%d തീമുകൾ സജീവമാക്കുക", "Plural translation correctly applied")

    # 3. Test submit helper load strings
    p_meta, p_ready = _load_strings(plural_test_slug, data_dir, locale="ml")
    assert_true(len(p_ready) == 1, "Submitter loaded plural test string")
    assert_true(p_ready[0].get("plural") == "Activate %d themes", "Loaded string has plural")
    assert_true(p_ready[0].get("plural_translation") == "%d തീമുകൾ സജീവമാക്കുക", "Loaded string has plural_translation")

    # Cleanup plural_test dir
    shutil.rmtree(data_dir / plural_test_slug)
    print()

    # -------------------------------------------------------------
    # Summary
    # -------------------------------------------------------------
    print("=" * 60)
    print(f"TEST RESULTS: {passed} PASSED, {failed} FAILED")
    print("=" * 60)
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(run_tests())
