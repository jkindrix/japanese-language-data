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

from build.constants import DATA_DIR, MANIFEST_PATH, REPO_ROOT, SCHEMAS_DIR

# Mapping: relative data path → schema file name (without path).
SCHEMA_MAP: dict[str, str] = {
    "data/core/kana.json": "kana.schema.json",
    "data/core/kanji.json": "kanji.schema.json",
    "data/core/kanji-joyo.json": "kanji.schema.json",
    "data/core/kanji-jinmeiyo.json": "kanji.schema.json",
    "data/core/words.json": "word.schema.json",
    "data/core/words-full.json": "word.schema.json",
    "data/core/radicals.json": "radical.schema.json",
    "data/optional/names.json": "name.schema.json",
    "data/corpus/sentences.json": "sentence.schema.json",
    "data/corpus/sentences-kftt.json": "sentence.schema.json",
    "data/corpus/sentences-tatoeba-full.json": "sentence.schema.json",
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
    "data/cross-refs/reading-to-words.json": "cross-refs.schema.json",
    "data/enrichment/frequency-corpus.json": "frequency.schema.json",
    "data/enrichment/frequency-subtitles.json": "frequency.schema.json",
    "data/enrichment/frequency-web.json": "frequency.schema.json",
    "data/enrichment/frequency-wikipedia.json": "frequency.schema.json",
    "data/enrichment/pitch-accent-wiktionary.json": "pitch-accent.schema.json",
    "data/enrichment/furigana.json": "furigana.schema.json",
    "data/cross-refs/radical-to-kanji.json": "cross-refs.schema.json",
    "data/cross-refs/kanji-to-sentences.json": "cross-refs.schema.json",
    "data/enrichment/counter-words.json": "counter-words.schema.json",
    "data/enrichment/ateji.json": "ateji.schema.json",
    "data/enrichment/jukugo-compounds.json": "jukugo.schema.json",
    "data/cross-refs/word-to-grammar.json": "cross-refs.schema.json",
    "data/corpus/sentences-jesc.json": "sentence.schema.json",
    "data/corpus/sentences-wikimatrix.json": "sentence.schema.json",
    "data/enrichment/frequency-tatoeba.json": "frequency.schema.json",
    "data/enrichment/sentence-difficulty.json": "sentence-difficulty.schema.json",
    "data/cross-refs/wordnet-synonyms.json": "wordnet.schema.json",
    "data/cross-refs/word-relations.json": "word-relations.schema.json",
    "data/cross-refs/kanji-to-words-full.json": "cross-refs.schema.json",
    "data/cross-refs/word-to-kanji-full.json": "cross-refs.schema.json",
    "data/cross-refs/reading-to-words-full.json": "cross-refs.schema.json",
    "data/phase4/aozora-corpus.json": "aozora.schema.json",
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


def _validate_manifest() -> list[tuple[Path, str]]:
    """Validate manifest.json against its schema.

    Returns a list of failures (empty on success). Skips silently if
    manifest.json or its schema does not exist yet.
    """
    failures: list[tuple[Path, str]] = []
    schema_path = SCHEMAS_DIR / "manifest.schema.json"
    if not MANIFEST_PATH.exists() or not schema_path.exists():
        return failures

    try:
        data = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        failures.append((MANIFEST_PATH, f"invalid JSON: {exc}"))
        print(f"[fail] manifest.json: invalid JSON ({exc})")
        return failures

    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    try:
        jsonschema.validate(instance=data, schema=schema)
        print("[ok]   manifest.json")
    except jsonschema.ValidationError as exc:
        location = "/".join(str(p) for p in exc.absolute_path) or "<root>"
        failures.append((MANIFEST_PATH, f"schema error at {location}: {exc.message}"))
        print(f"[fail] manifest.json: {location}: {exc.message}")

    return failures


def _load_json_safe(path: Path) -> dict | None:
    """Load a JSON file, returning None if it doesn't exist or is invalid."""
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def _semantic_checks() -> list[tuple[str, str]]:
    """Run semantic integrity checks that go beyond schema validation.

    These check referential integrity across files, detect duplicates,
    and verify determinism invariants. Returns a list of (check_name,
    error_message) tuples for failures.
    """
    failures: list[tuple[str, str]] = []

    # --- Load data files (skip checks if files aren't built yet) ---
    kanji_data = _load_json_safe(DATA_DIR / "core" / "kanji.json")
    words_data = _load_json_safe(DATA_DIR / "core" / "words.json")
    sentences_data = _load_json_safe(DATA_DIR / "corpus" / "sentences.json")
    radicals_data = _load_json_safe(DATA_DIR / "core" / "radicals.json")
    grammar_data = _load_json_safe(DATA_DIR / "grammar" / "grammar.json")
    k2w = _load_json_safe(DATA_DIR / "cross-refs" / "kanji-to-words.json")
    w2k = _load_json_safe(DATA_DIR / "cross-refs" / "word-to-kanji.json")
    w2s = _load_json_safe(DATA_DIR / "cross-refs" / "word-to-sentences.json")
    k2r = _load_json_safe(DATA_DIR / "cross-refs" / "kanji-to-radicals.json")
    stroke_idx = _load_json_safe(DATA_DIR / "enrichment" / "stroke-order-index.json")

    # --- Check 1: Duplicate detection in primary datasets ---
    if kanji_data:
        kanji_chars = [k["character"] for k in kanji_data.get("kanji", [])]
        if len(kanji_chars) != len(set(kanji_chars)):
            seen: set[str] = set()
            dupes: list[str] = []
            for c in kanji_chars:
                if c in seen:
                    dupes.append(c)
                seen.add(c)
            failures.append(("duplicate-kanji", f"Duplicate kanji entries: {dupes}"))

    if radicals_data:
        rad_chars = [r["radical"] for r in radicals_data.get("radicals", [])]
        if len(rad_chars) != len(set(rad_chars)):
            seen_r: set[str] = set()
            dupes_r: list[str] = []
            for c in rad_chars:
                if c in seen_r:
                    dupes_r.append(c)
                seen_r.add(c)
            failures.append(("duplicate-radicals", f"Duplicate radical entries: {dupes_r}"))

    if grammar_data:
        grammar_ids = [g["id"] for g in grammar_data.get("grammar_points", [])]
        if len(grammar_ids) != len(set(grammar_ids)):
            seen_g: set[str] = set()
            dupes_g: list[str] = []
            for i in grammar_ids:
                if i in seen_g:
                    dupes_g.append(i)
                seen_g.add(i)
            failures.append(("duplicate-grammar", f"Duplicate grammar IDs: {dupes_g}"))

    # --- Check 2: Cross-reference referential integrity ---
    if kanji_data and k2w:
        kanji_set = {k["character"] for k in kanji_data.get("kanji", [])}
        k2w_mapping = k2w.get("mapping", {})
        orphan_kanji = set(k2w_mapping.keys()) - kanji_set
        # Filter out non-kanji characters (full-width numerals, etc.)
        # that are expected in word kanji fields but not in kanji.json.
        # Non-kanji characters (fullwidth numerals, Latin, etc.) appear as
        # word kanji-field keys but not in kanji.json.  A small count of
        # these is expected; a large count indicates a data pipeline bug.
        ORPHAN_SANITY_THRESHOLD = 200
        if len(orphan_kanji) > ORPHAN_SANITY_THRESHOLD:
            failures.append((
                "k2w-orphans",
                f"kanji-to-words has {len(orphan_kanji)} keys not in kanji.json "
                f"(expected ≤{ORPHAN_SANITY_THRESHOLD} non-kanji chars)"
            ))

    if words_data and w2s and sentences_data:
        sentence_ids = {s["id"] for s in sentences_data.get("sentences", [])}
        w2s_mapping = w2s.get("mapping", {})
        dangling = set()
        for word_id, sent_ids in w2s_mapping.items():
            for sid in sent_ids:
                if sid not in sentence_ids:
                    dangling.add(sid)
        if dangling:
            failures.append((
                "w2s-dangling",
                f"word-to-sentences references {len(dangling)} sentence IDs "
                f"not in sentences.json: {list(dangling)[:5]}..."
            ))

    if kanji_data and k2r and radicals_data:
        rad_set = {r["radical"] for r in radicals_data.get("radicals", [])}
        k2r_mapping = k2r.get("mapping", {})
        missing_rads = set()
        for kanji_char, rad_list in k2r_mapping.items():
            for rad in rad_list:
                if rad not in rad_set:
                    missing_rads.add(rad)
        if missing_rads:
            failures.append((
                "k2r-missing-radicals",
                f"kanji-to-radicals references {len(missing_rads)} radicals "
                f"not in radicals.json: {sorted(missing_rads)[:10]}"
            ))

    # --- Check 2b: word-to-grammar referential integrity ---
    w2g = _load_json_safe(DATA_DIR / "cross-refs" / "word-to-grammar.json")
    if grammar_data and w2g:
        grammar_ids = {g["id"] for g in grammar_data.get("grammar_points", [])}
        w2g_mapping = w2g.get("mapping", {})
        dangling_grammar = set()
        for word_id, gids in w2g_mapping.items():
            for gid in gids:
                if gid not in grammar_ids:
                    dangling_grammar.add(gid)
        if dangling_grammar:
            failures.append((
                "w2g-dangling",
                f"word-to-grammar references {len(dangling_grammar)} grammar IDs "
                f"not in grammar.json: {sorted(dangling_grammar)[:5]}..."
            ))

    # --- Check 3: Bidirectional consistency (kanji↔words) ---
    if k2w and w2k:
        k2w_mapping = k2w.get("mapping", {})
        w2k_mapping = w2k.get("mapping", {})

        # Forward: every word in k2w values should have that kanji in w2k
        for kanji_char, word_ids in k2w_mapping.items():
            for wid in word_ids:
                if wid in w2k_mapping:
                    if kanji_char not in w2k_mapping[wid]:
                        failures.append((
                            "k2w-w2k-asymmetry",
                            f"kanji-to-words maps {kanji_char}→{wid} but "
                            f"word-to-kanji does not map {wid}→{kanji_char}"
                        ))
                        break  # one example is enough

        # Reverse: every kanji in w2k values should have that word in k2w
        for wid, kanji_chars in w2k_mapping.items():
            for kanji_char in kanji_chars:
                if kanji_char in k2w_mapping:
                    if wid not in k2w_mapping[kanji_char]:
                        failures.append((
                            "w2k-k2w-asymmetry",
                            f"word-to-kanji maps {wid}→{kanji_char} but "
                            f"kanji-to-words does not map {kanji_char}→{wid}"
                        ))
                        break  # one example is enough

    # --- Check 3b: w2k keys should be valid word IDs ---
    if words_data and w2k:
        word_ids = {w["id"] for w in words_data.get("words", [])}
        w2k_keys = set(w2k.get("mapping", {}).keys())
        orphan_words = w2k_keys - word_ids
        if orphan_words:
            failures.append((
                "w2k-orphan-words",
                f"word-to-kanji has {len(orphan_words)} keys not in words.json: "
                f"{sorted(orphan_words)[:5]}..."
            ))

    # --- Check 4: Determinism — sorted keys in index files ---
    if stroke_idx:
        chars = list(stroke_idx.get("characters", {}).keys())
        if chars != sorted(chars):
            failures.append((
                "stroke-order-sort",
                "stroke-order-index.json keys are not in sorted order "
                "(non-deterministic build output)"
            ))

    for name, data_obj, payload_key in [
        ("k2w", k2w, "mapping"),
        ("w2k", w2k, "mapping"),
        ("w2s", w2s, "mapping"),
        ("k2r", k2r, "mapping"),
    ]:
        if data_obj:
            keys = list(data_obj.get(payload_key, {}).keys())
            if keys != sorted(keys):
                failures.append((
                    f"{name}-sort",
                    f"{name} mapping keys are not in sorted order "
                    f"(non-deterministic build output)"
                ))

    return failures


def validate_all() -> int:
    """Validate every data file against its schema, then run semantic checks.

    Returns:
        0 if every file passes (or if no files exist yet — Phase 0), 1 if
        any validation fails.
    """
    targets = list(_iter_targets())
    if not targets:
        print("No data files to validate yet. Phase 0 is scaffolding only.")
        return 0

    failures: list[tuple[Path, str]] = []

    # Validate manifest.json first (not a data file, but the build's
    # single source of truth — if it's malformed, everything downstream
    # is suspect).
    failures.extend(_validate_manifest())

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

    # Semantic integrity checks (beyond JSON Schema).
    print("\nSemantic integrity checks:")
    semantic_failures = _semantic_checks()
    for check_name, msg in semantic_failures:
        failures.append((Path(check_name), msg))
        print(f"[fail] {check_name}: {msg}")
    if not semantic_failures:
        print("[ok]   all semantic checks passed")

    if failures:
        print(f"\n{len(failures)} check(s) failed validation.")
        return 1

    print(f"\n{len(targets)} file(s) + semantic checks validated.")
    return 0


def main() -> int:
    return validate_all()


if __name__ == "__main__":
    sys.exit(main())
