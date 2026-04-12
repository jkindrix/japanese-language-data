"""Negative schema validation tests.

These tests verify that invalid data is correctly REJECTED by the
JSON schemas. The positive direction (valid data passes) is covered
by test_schemas.py and the build pipeline. This file covers the
negative direction: data that should fail validation actually does.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import jsonschema
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SCHEMAS_DIR = REPO_ROOT / "schemas"
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def _load_schema(name: str) -> dict:
    return json.loads((SCHEMAS_DIR / name).read_text(encoding="utf-8"))


def _validate(instance: dict, schema_name: str) -> None:
    schema = _load_schema(schema_name)
    jsonschema.validate(instance, schema)


def _expect_invalid(instance: dict, schema_name: str) -> None:
    schema = _load_schema(schema_name)
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(instance, schema)


# ---------------------------------------------------------------------------
# Grammar schema negative tests
# ---------------------------------------------------------------------------

class TestGrammarSchemaNegative:
    SCHEMA = "grammar.schema.json"

    def test_missing_metadata(self) -> None:
        _expect_invalid({"grammar_points": []}, self.SCHEMA)

    def test_missing_grammar_points(self) -> None:
        _expect_invalid({
            "metadata": {
                "source": "test", "license": "test", "generated": "2026-01-01",
                "count": 0, "field_notes": {},
            },
        }, self.SCHEMA)

    def test_entry_missing_required_fields(self) -> None:
        _expect_invalid({
            "metadata": {
                "source": "test", "license": "test", "generated": "2026-01-01",
                "count": 1, "field_notes": {},
            },
            "grammar_points": [
                {"id": "test"}  # missing pattern, level, etc.
            ],
        }, self.SCHEMA)

    def test_invalid_review_status(self) -> None:
        _expect_invalid({
            "metadata": {
                "source": "test", "license": "test", "generated": "2026-01-01",
                "count": 1, "field_notes": {},
            },
            "grammar_points": [{
                "id": "test", "pattern": "test", "level": "N5",
                "meaning_en": "test", "formation": "test",
                "examples": [{"japanese": "テスト", "english": "test", "source": "original"}],
                "review_status": "approved",  # invalid enum value
                "sources": ["test"],
            }],
        }, self.SCHEMA)


# ---------------------------------------------------------------------------
# Cross-refs schema negative tests
# ---------------------------------------------------------------------------

class TestCrossRefsSchemaNegative:
    SCHEMA = "cross-refs.schema.json"

    def test_missing_metadata(self) -> None:
        _expect_invalid({"mapping": {}}, self.SCHEMA)

    def test_missing_mapping(self) -> None:
        _expect_invalid({
            "metadata": {
                "source": "test", "license": "test", "generated": "2026-01-01",
                "count": 0, "field_notes": {},
            },
        }, self.SCHEMA)


# ---------------------------------------------------------------------------
# Kanji schema negative tests
# ---------------------------------------------------------------------------

class TestKanjiSchemaNegative:
    SCHEMA = "kanji.schema.json"

    def test_missing_metadata(self) -> None:
        _expect_invalid({"kanji": []}, self.SCHEMA)

    def test_missing_kanji_array(self) -> None:
        _expect_invalid({
            "metadata": {
                "source": "test", "license": "test", "generated": "2026-01-01",
                "count": 0, "field_notes": {},
            },
        }, self.SCHEMA)


# ---------------------------------------------------------------------------
# Word schema negative tests
# ---------------------------------------------------------------------------

class TestWordSchemaNegative:
    SCHEMA = "word.schema.json"

    def test_missing_metadata(self) -> None:
        _expect_invalid({"words": []}, self.SCHEMA)

    def test_missing_words_array(self) -> None:
        _expect_invalid({
            "metadata": {
                "source": "test", "license": "test", "generated": "2026-01-01",
                "count": 0, "field_notes": {},
            },
        }, self.SCHEMA)
