"""Schema integrity tests.

Verify that every JSON Schema file in ``schemas/`` is itself a valid
JSON document and a valid JSON Schema (Draft 2020-12). These tests are
independent of the data build: they run even when no data has been
generated yet (which is the case during Phase 0).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

try:
    from jsonschema import Draft202012Validator
except ImportError:  # pragma: no cover
    pytest.skip("jsonschema not installed", allow_module_level=True)

REPO_ROOT = Path(__file__).resolve().parent.parent
SCHEMAS_DIR = REPO_ROOT / "schemas"


def _schema_files() -> list[Path]:
    return sorted(SCHEMAS_DIR.glob("*.schema.json"))


@pytest.mark.parametrize("schema_path", _schema_files(), ids=lambda p: p.name)
def test_schema_is_valid_json(schema_path: Path) -> None:
    """Every schema file must be parseable as JSON."""
    text = schema_path.read_text(encoding="utf-8")
    schema = json.loads(text)
    assert isinstance(schema, dict), f"{schema_path.name} is not a JSON object"


@pytest.mark.parametrize("schema_path", _schema_files(), ids=lambda p: p.name)
def test_schema_is_valid_draft_2020_12(schema_path: Path) -> None:
    """Every schema file must be a valid Draft 2020-12 JSON Schema."""
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)


@pytest.mark.parametrize("schema_path", _schema_files(), ids=lambda p: p.name)
def test_schema_has_required_metadata(schema_path: Path) -> None:
    """Every schema should declare $schema, $id, title, and description."""
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    for field in ("$schema", "$id", "title", "description"):
        assert field in schema, f"{schema_path.name} missing {field}"


def test_all_schemas_are_present() -> None:
    """Guardrail: expected schema files exist.

    If you add a new schema, add it here too so we catch accidental
    deletions or renames.
    """
    expected_names = {
        "ateji.schema.json",
        "conjugations.schema.json",
        "counter-words.schema.json",
        "cross-refs.schema.json",
        "expressions.schema.json",
        "frequency.schema.json",
        "furigana.schema.json",
        "grammar.schema.json",
        "jlpt.schema.json",
        "kana.schema.json",
        "kanji.schema.json",
        "manifest.schema.json",
        "name.schema.json",
        "pitch-accent.schema.json",
        "radical.schema.json",
        "sentence.schema.json",
        "stroke-order.schema.json",
        "word.schema.json",
    }
    found_names = {p.name for p in _schema_files()}
    missing = expected_names - found_names
    extra = found_names - expected_names
    assert not missing, f"Missing expected schemas: {sorted(missing)}"
    assert not extra, f"Unexpected schemas present: {sorted(extra)} (update this test if intentional)"
