"""Schema validation for all output JSON files.

Reads every file in ``data/`` that has a corresponding schema in
``schemas/`` and validates it against that schema. Fails loudly if any
file does not validate.

Mapping of data files to schemas is maintained in the SCHEMA_MAP
constant. Adding a new data file means adding a line to the map.

Run via ``just validate`` or ``python -m build.validate``.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Iterator

try:
    import jsonschema
except ImportError:  # pragma: no cover
    print("ERROR: jsonschema not installed. Run: pip install -r build/requirements.txt")
    raise

REPO_ROOT = Path(__file__).resolve().parent.parent
SCHEMAS_DIR = REPO_ROOT / "schemas"
DATA_DIR = REPO_ROOT / "data"

# Mapping: relative data path → schema file name (without path).
SCHEMA_MAP: dict[str, str] = {
    "data/core/kana.json": "kana.schema.json",
    "data/core/kanji.json": "kanji.schema.json",
    "data/core/kanji-joyo.json": "kanji.schema.json",
    "data/core/words.json": "word.schema.json",
    "data/core/words-full.json": "word.schema.json",
    "data/core/radicals.json": "radical.schema.json",
    "data/optional/names.json": "name.schema.json",
    "data/corpus/sentences.json": "sentence.schema.json",
    "data/enrichment/pitch-accent.json": "pitch-accent.schema.json",
    "data/enrichment/frequency-newspaper.json": "frequency.schema.json",
    "data/enrichment/frequency-modern.json": "frequency.schema.json",
    "data/enrichment/jlpt-classifications.json": "jlpt.schema.json",
    "data/enrichment/stroke-order-index.json": "stroke-order.schema.json",
    "data/grammar/grammar.json": "grammar.schema.json",
    "data/grammar/expressions.json": "expressions.schema.json",
    "data/grammar/conjugations.json": "conjugations.schema.json",
    "data/cross-refs/kanji-to-words.json": "cross-refs.schema.json",
    "data/cross-refs/word-to-kanji.json": "cross-refs.schema.json",
    "data/cross-refs/word-to-sentences.json": "cross-refs.schema.json",
    "data/cross-refs/kanji-to-radicals.json": "cross-refs.schema.json",
}


def _load_schema(name: str) -> dict:
    path = SCHEMAS_DIR / name
    if not path.exists():
        raise FileNotFoundError(f"Schema not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _iter_targets() -> Iterator[tuple[Path, dict]]:
    """Yield (data_file, schema) for every existing target."""
    for rel_path, schema_name in SCHEMA_MAP.items():
        data_path = REPO_ROOT / rel_path
        if not data_path.exists():
            continue
        schema = _load_schema(schema_name)
        yield data_path, schema


def validate_all() -> int:
    """Validate every data file against its schema.

    Returns:
        0 if every file passes (or if no files exist yet — Phase 0), 1 if
        any validation fails.
    """
    targets = list(_iter_targets())
    if not targets:
        print("No data files to validate yet. Phase 0 is scaffolding only.")
        return 0

    failures: list[tuple[Path, str]] = []
    for data_path, schema in targets:
        rel = data_path.relative_to(REPO_ROOT)
        try:
            data = json.loads(data_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            failures.append((data_path, f"invalid JSON: {exc}"))
            print(f"[fail] {rel}: invalid JSON ({exc})")
            continue

        try:
            jsonschema.validate(instance=data, schema=schema)
            print(f"[ok]   {rel}")
        except jsonschema.ValidationError as exc:
            location = "/".join(str(p) for p in exc.absolute_path) or "<root>"
            failures.append((data_path, f"schema error at {location}: {exc.message}"))
            print(f"[fail] {rel}: {location}: {exc.message}")

    if failures:
        print(f"\n{len(failures)} file(s) failed validation.")
        return 1

    print(f"\n{len(targets)} file(s) validated.")
    return 0


def main() -> int:
    return validate_all()


if __name__ == "__main__":
    sys.exit(main())
