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


# ---------------------------------------------------------------------------
# Sentence schema negative tests
# ---------------------------------------------------------------------------

class TestSentenceSchemaNegative:
    SCHEMA = "sentence.schema.json"

    def test_missing_metadata(self) -> None:
        _expect_invalid({"sentences": []}, self.SCHEMA)

    def test_invalid_license_flag(self) -> None:
        _expect_invalid({
            "metadata": {
                "source": "test", "license": "test", "generated": "2026-01-01",
                "count": 1, "field_notes": {},
            },
            "sentences": [{
                "id": "1234567",
                "japanese": "テスト文です。",
                "english": "This is a test sentence.",
                "curated": True,
                "license_flag": "INVALID",
            }],
        }, self.SCHEMA)


# ---------------------------------------------------------------------------
# Conjugations schema negative tests
# ---------------------------------------------------------------------------

class TestConjugationsSchemaNegative:
    SCHEMA = "conjugations.schema.json"

    def test_missing_metadata(self) -> None:
        _expect_invalid({"entries": []}, self.SCHEMA)

    def test_invalid_class_enum(self) -> None:
        _expect_invalid({
            "metadata": {
                "source": "test", "license": "test", "generated": "2026-01-01",
                "count": 1, "field_notes": {},
            },
            "entries": [{
                "id": "1000000",
                "dictionary_form": "食べる",
                "reading": "たべる",
                "class": "v99invalid",
                "forms": {},
            }],
        }, self.SCHEMA)


# ---------------------------------------------------------------------------
# Pitch accent schema negative tests
# ---------------------------------------------------------------------------

class TestPitchAccentSchemaNegative:
    SCHEMA = "pitch-accent.schema.json"

    def test_missing_metadata(self) -> None:
        _expect_invalid({"entries": []}, self.SCHEMA)

    def test_empty_pitch_positions(self) -> None:
        # pitch_positions has minItems:1 — empty array must be rejected
        _expect_invalid({
            "metadata": {
                "source": "test", "license": "test", "generated": "2026-01-01",
                "count": 1, "field_notes": {},
            },
            "entries": [{
                "word": "日本語",
                "reading": "にほんご",
                "pitch_positions": [],
            }],
        }, self.SCHEMA)


# ---------------------------------------------------------------------------
# JLPT schema negative tests
# ---------------------------------------------------------------------------

class TestJlptSchemaNegative:
    SCHEMA = "jlpt.schema.json"

    def test_missing_metadata(self) -> None:
        _expect_invalid({"classifications": []}, self.SCHEMA)

    def test_invalid_level(self) -> None:
        _expect_invalid({
            "metadata": {
                "source": "test", "license": "test", "generated": "2026-01-01",
                "count": 1, "field_notes": {}, "disclaimer": "community data",
            },
            "classifications": [{
                "text": "日",
                "kind": "kanji",
                "level": "N6",
            }],
        }, self.SCHEMA)

    def test_invalid_kind(self) -> None:
        _expect_invalid({
            "metadata": {
                "source": "test", "license": "test", "generated": "2026-01-01",
                "count": 1, "field_notes": {}, "disclaimer": "community data",
            },
            "classifications": [{
                "text": "日",
                "kind": "phrase",
                "level": "N5",
            }],
        }, self.SCHEMA)


# ---------------------------------------------------------------------------
# Frequency schema negative tests
# ---------------------------------------------------------------------------

class TestFrequencySchemaNegative:
    SCHEMA = "frequency.schema.json"

    def test_missing_metadata(self) -> None:
        _expect_invalid({"entries": []}, self.SCHEMA)

    def test_rank_zero(self) -> None:
        # rank has minimum:1 — zero must be rejected
        _expect_invalid({
            "metadata": {
                "source": "test", "license": "test", "generated": "2026-01-01",
                "count": 1, "field_notes": {},
                "corpus": "test corpus", "kind": "kanji",
            },
            "entries": [{
                "text": "日",
                "rank": 0,
            }],
        }, self.SCHEMA)


# ---------------------------------------------------------------------------
# Radical schema negative tests
# ---------------------------------------------------------------------------

class TestRadicalSchemaNegative:
    SCHEMA = "radical.schema.json"

    def test_missing_metadata(self) -> None:
        _expect_invalid({"radicals": [], "kanji_to_radicals": {}}, self.SCHEMA)


# ---------------------------------------------------------------------------
# Stroke order schema negative tests
# ---------------------------------------------------------------------------

class TestStrokeOrderSchemaNegative:
    SCHEMA = "stroke-order.schema.json"

    def test_missing_metadata(self) -> None:
        _expect_invalid({"characters": {}}, self.SCHEMA)


# ---------------------------------------------------------------------------
# Expressions schema negative tests
# ---------------------------------------------------------------------------

class TestExpressionsSchemaNegative:
    SCHEMA = "expressions.schema.json"

    def test_missing_metadata(self) -> None:
        _expect_invalid({"expressions": []}, self.SCHEMA)

    def test_extra_field_on_entry(self) -> None:
        # expressionEntry has additionalProperties:false — "bonus" must be rejected
        _expect_invalid({
            "metadata": {
                "source": "test", "license": "test", "generated": "2026-01-01",
                "count": 1, "field_notes": {},
            },
            "expressions": [{
                "id": "1000001",
                "text": "どういたしまして",
                "reading": "どういたしまして",
                "meanings": ["You're welcome"],
                "bonus": "not allowed",
            }],
        }, self.SCHEMA)


# ---------------------------------------------------------------------------
# Name schema negative tests
# ---------------------------------------------------------------------------

class TestNameSchemaNegative:
    SCHEMA = "name.schema.json"

    def test_missing_metadata(self) -> None:
        _expect_invalid({"names": []}, self.SCHEMA)


# ---------------------------------------------------------------------------
# Kana schema negative tests
# ---------------------------------------------------------------------------

class TestKanaSchemaNegative:
    SCHEMA = "kana.schema.json"

    def test_missing_metadata(self) -> None:
        _expect_invalid({"kana": []}, self.SCHEMA)


# ---------------------------------------------------------------------------
# Manifest schema negative tests
# ---------------------------------------------------------------------------

class TestManifestSchemaNegative:
    SCHEMA = "manifest.schema.json"

    def test_missing_version(self) -> None:
        # manifest requires "version" at the root level
        _expect_invalid({
            "project": "japanese-language-data",
            "phase": 4,
            "generated": "2026-01-01",
            "license": "CC-BY-SA 4.0",
            "sources": {},
            "counts": {},
        }, self.SCHEMA)
