"""Data integrity regression tests.

Each test here corresponds to a specific defect that was previously
observed and fixed. The tests run against built data files when they
exist and gracefully skip otherwise, so ``pytest tests/`` remains
runnable without having built the dataset.

See CHANGELOG.md [0.3.1] for the original defect descriptions.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent


def _load_if_exists(path: Path) -> dict | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# D1: v5k-s, v5u-s, v5aru, v5r-i conjugation coverage
# ---------------------------------------------------------------------------

def test_d1_conjugations_covers_iku() -> None:
    """D1 regression: 行く (JMdict v5k-s) must have a conjugation table
    with the irregular te/ta forms いって/いった, not the standard
    godan-k forms いいて/いいた."""
    data = _load_if_exists(REPO_ROOT / "data" / "grammar" / "conjugations.json")
    if data is None:
        pytest.skip("conjugations.json not built yet")
    entries = data.get("entries", [])
    iku_entries = [e for e in entries if e.get("dictionary_form") == "行く"]
    assert iku_entries, "D1 regression: 行く has no conjugation table"
    iku = iku_entries[0]
    assert iku["class"] == "v5k-s", f"行く should be class v5k-s, got {iku['class']!r}"
    forms = iku["forms"]
    assert forms.get("te_form") == "いって", \
        f"行く te_form should be いって, got {forms.get('te_form')!r}"
    assert forms.get("ta_form") == "いった", \
        f"行く ta_form should be いった, got {forms.get('ta_form')!r}"
    assert forms.get("polite_nonpast") == "いきます"


def test_d1_conjugations_covers_v5aru_and_v5r_i() -> None:
    """D1 regression: at least one v5aru and one v5r-i verb must have a
    conjugation table. Verifies the pipeline emits these classes."""
    data = _load_if_exists(REPO_ROOT / "data" / "grammar" / "conjugations.json")
    if data is None:
        pytest.skip("conjugations.json not built yet")
    classes_present = {e.get("class") for e in data.get("entries", [])}
    assert "v5aru" in classes_present, \
        "D1 regression: no v5aru conjugation emitted (いらっしゃる, ござる family)"
    assert "v5r-i" in classes_present, \
        "D1 regression: no v5r-i conjugation emitted (ある family)"


# ---------------------------------------------------------------------------
# B1: v5r-i compound verbs must strip the ある suffix in nai_form and must
# not emit nonsensical potential/passive/causative/imperative/volitional
# forms for compound ある-based entries.
# ---------------------------------------------------------------------------

def test_b1_v5r_i_nai_form_has_correct_prefix() -> None:
    """B1 regression: compound v5r-i verbs (ことがある, である, etc.)
    must have nai_form prefixed with the stem minus 'ある', not the
    bare literal 'ない'."""
    data = _load_if_exists(REPO_ROOT / "data" / "grammar" / "conjugations.json")
    if data is None:
        pytest.skip("conjugations.json not built yet")
    for e in data.get("entries", []):
        if e.get("class") != "v5r-i":
            continue
        reading = e.get("reading", "")
        nai = e.get("forms", {}).get("nai_form", "")
        if reading == "ある":
            assert nai == "ない", f"ある should have nai_form=ない, got {nai!r}"
        else:
            assert reading.endswith("ある"), \
                f"v5r-i entry {reading!r} unexpectedly does not end in ある"
            expected_prefix = reading[:-2]
            assert nai.startswith(expected_prefix) and nai.endswith("ない"), \
                f"v5r-i {reading!r} nai_form should start with {expected_prefix!r} " \
                f"and end with ない, got {nai!r}"


def test_b1_v5r_i_compound_has_no_malformed_imperatives() -> None:
    """B1 regression: compound v5r-i verbs must not emit nonsensical
    imperative/potential/passive/causative/volitional forms. For
    compound v5r-i these should be empty strings."""
    data = _load_if_exists(REPO_ROOT / "data" / "grammar" / "conjugations.json")
    if data is None:
        pytest.skip("conjugations.json not built yet")
    for e in data.get("entries", []):
        if e.get("class") != "v5r-i":
            continue
        if e.get("reading") == "ある":
            # Bare ある: reference case; bare ある is also restricted but
            # the plan scopes this check to compound entries only.
            continue
        forms = e.get("forms", {})
        for f in ("imperative", "potential", "passive",
                  "causative", "volitional"):
            value = forms.get(f, "")
            assert value == "", \
                f"{e.get('reading')!r} {f} should be empty (not well-formed), got {value!r}"


# ---------------------------------------------------------------------------
# M1: display_forms companion field preserves the kanji prefix of the
# dictionary_form. Representative checks for v1, v5k-s, adj-i, adj-na.
# The adj-na case is the zero-common-suffix branch (class-aware), the
# others are the common-suffix heuristic.
# ---------------------------------------------------------------------------

def test_m1_display_forms_preserves_kanji_prefix() -> None:
    """M1: display_forms should preserve the kanji prefix of dictionary_form
    for at least one representative per word class.

    Tests:
      * 食べる (v1)      te_form display == 食べて
      * 行く (v5k-s)     te_form display == 行って
      * 高い (adj-i)     past display == 高かった
      * 綺麗 (adj-na)    polite_nonpast display == 綺麗です
      * 大切 (adj-na)    polite_nonpast display == 大切です (zero-common-suffix case)
    """
    data = _load_if_exists(REPO_ROOT / "data" / "grammar" / "conjugations.json")
    if data is None:
        pytest.skip("conjugations.json not built yet")

    def find(dictionary_form: str, cls: str) -> dict:
        for e in data.get("entries", []):
            if e.get("dictionary_form") == dictionary_form and e.get("class") == cls:
                return e
        raise AssertionError(f"M1 test probe {dictionary_form} ({cls}) not found")

    cases = [
        ("食べる", "v1",      "te_form",        "食べて"),
        ("行く",   "v5k-s",   "te_form",        "行って"),
        ("高い",   "adj-i",   "past",           "高かった"),
        ("綺麗",   "adj-na",  "polite_nonpast", "綺麗です"),
        ("大切",   "adj-na",  "polite_nonpast", "大切です"),
    ]
    for df, cls, form_name, expected in cases:
        e = find(df, cls)
        assert "display_forms" in e, \
            f"M1: {df} ({cls}) entry is missing the display_forms field"
        actual = e["display_forms"].get(form_name)
        assert actual == expected, \
            f"M1: {df} ({cls}) display_forms.{form_name} " \
            f"expected {expected!r}, got {actual!r}"


# ---------------------------------------------------------------------------
# Determinism: stroke-order-index.json characters keys must appear in
# sorted Unicode-codepoint order. Enforces byte-reproducibility (see
# docs/architecture.md §1) — without the fix, the transform iterated a
# Python set and produced different key orderings across rebuilds.
# ---------------------------------------------------------------------------

def test_stroke_order_characters_keys_are_sorted() -> None:
    """The characters map in stroke-order-index.json must have its keys
    in sorted Unicode-codepoint order. Regression guard for the
    non-deterministic set iteration previously in stroke_order.py's
    missing-kanji loop.

    If keys are not sorted, rebuilds can emit the same content in
    different order, violating docs/architecture.md §1 (byte
    reproducibility).
    """
    data = _load_if_exists(REPO_ROOT / "data" / "enrichment" / "stroke-order-index.json")
    if data is None:
        pytest.skip("stroke-order-index.json not built yet")
    keys = list(data.get("characters", {}).keys())
    expected = sorted(keys)
    assert keys == expected, (
        f"stroke-order-index.json characters keys are not in sorted order. "
        f"First divergence at index {next((i for i, (a, b) in enumerate(zip(keys, expected)) if a != b), -1)}: "
        f"got {keys[:5]!r}... expected {expected[:5]!r}..."
    )


# ---------------------------------------------------------------------------
# D2: grammar related-reference resolution
# ---------------------------------------------------------------------------

def test_d2_grammar_related_references_resolve() -> None:
    """D2 regression: every 'related' id in grammar.json must resolve
    to an existing grammar entry."""
    data = _load_if_exists(REPO_ROOT / "data" / "grammar" / "grammar.json")
    if data is None:
        pytest.skip("grammar.json not built yet")
    all_ids = {e["id"] for e in data.get("grammar_points", [])}
    for entry in data.get("grammar_points", []):
        for rel_id in entry.get("related", []):
            assert rel_id in all_ids, \
                f"D2 regression: entry {entry['id']!r} references unknown related id {rel_id!r}"


# ---------------------------------------------------------------------------
# D4: deterministic JLPT join — easier level wins
# ---------------------------------------------------------------------------

def test_d4_words_jlpt_easier_level_wins() -> None:
    """D4 regression: for words whose JMdict ID is shared across multiple
    JLPT levels (homographic variants), the jlpt_waller field should hold
    the easier level (higher N-number, closer to beginner).

    Uses jmdict_seq 1198180 (会う/遭う, shared between N5 and N2) as the
    canonical probe. After the fix, words.json[id=1198180].jlpt_waller
    should be N5, not N2.
    """
    jlpt = _load_if_exists(REPO_ROOT / "data" / "enrichment" / "jlpt-classifications.json")
    words = _load_if_exists(REPO_ROOT / "data" / "core" / "words.json")
    if jlpt is None or words is None:
        pytest.skip("jlpt-classifications.json or words.json not built yet")

    # Confirm the test probe actually has multiple levels in the classifications
    probe_levels = set()
    for entry in jlpt.get("classifications", []):
        if entry.get("kind") == "vocab" and entry.get("jmdict_seq") == "1198180":
            probe_levels.add(entry.get("level"))
    if len(probe_levels) < 2:
        pytest.skip(f"test probe 1198180 has only one level: {probe_levels}")

    # Verify the word entry was tagged with the easier level
    for w in words.get("words", []):
        if w.get("id") == "1198180":
            level = w.get("jlpt_waller")
            assert level == "N5", \
                f"D4 regression: 1198180 should have jlpt_waller=N5 (easier level wins), got {level!r}"
            return
    pytest.skip("word 1198180 not in common subset")


# ---------------------------------------------------------------------------
# D5: kanji-to-words orphan count recorded
# ---------------------------------------------------------------------------

def test_d5_kanji_to_words_orphan_count_matches() -> None:
    """D5 regression: characters in kanji-to-words.json that are not in
    kanji.json ('orphans') must be counted in the file's metadata, so
    consumers can detect this integrity gap at read time."""
    xref = _load_if_exists(REPO_ROOT / "data" / "cross-refs" / "kanji-to-words.json")
    kanji = _load_if_exists(REPO_ROOT / "data" / "core" / "kanji.json")
    if xref is None or kanji is None:
        pytest.skip("kanji-to-words.json or kanji.json not built yet")

    kanji_set = {k["character"] for k in kanji.get("kanji", [])}
    actual_orphans = sorted(ch for ch in xref.get("mapping", {}) if ch not in kanji_set)
    metadata = xref.get("metadata", {})

    assert "orphan_count" in metadata, \
        "D5 regression: orphan_count missing from kanji-to-words.json metadata"
    assert metadata["orphan_count"] == len(actual_orphans), \
        f"D5 regression: metadata.orphan_count={metadata['orphan_count']} != actual {len(actual_orphans)}"


# ---------------------------------------------------------------------------
# M4: invariant tests (not tied to a specific past defect; these are the
# pure invariants that should hold on every build)
# ---------------------------------------------------------------------------

def test_invariant_jlpt_waller_values_valid() -> None:
    """Every jlpt_waller value on kanji and word entries must be in
    {N1,N2,N3,N4,N5} or null. Any other value would be a pipeline bug."""
    valid = {None, "N1", "N2", "N3", "N4", "N5"}
    for path, payload_key in (
        (REPO_ROOT / "data" / "core" / "kanji.json", "kanji"),
        (REPO_ROOT / "data" / "core" / "words.json", "words"),
    ):
        data = _load_if_exists(path)
        if data is None:
            continue
        for entry in data.get(payload_key, []):
            value = entry.get("jlpt_waller")
            assert value in valid, \
                f"{path.name} entry has invalid jlpt_waller={value!r}"


def test_invariant_word_to_sentences_ids_exist() -> None:
    """Every sentence_id in word-to-sentences.json must exist in
    sentences.json. A dangling reference would be a cross-link bug."""
    xref = _load_if_exists(REPO_ROOT / "data" / "cross-refs" / "word-to-sentences.json")
    sentences = _load_if_exists(REPO_ROOT / "data" / "corpus" / "sentences.json")
    if xref is None or sentences is None:
        pytest.skip("files not built")
    known_ids = {s["id"] for s in sentences.get("sentences", [])}
    for word_id, sentence_ids in xref.get("mapping", {}).items():
        for sid in sentence_ids:
            assert sid in known_ids, \
                f"word_id {word_id} references unknown sentence_id {sid}"


def test_invariant_grammar_jlpt_ids_resolve() -> None:
    """Every grammar_id in jlpt-classifications.json (kind=grammar)
    must resolve to a grammar point in grammar.json."""
    jlpt = _load_if_exists(REPO_ROOT / "data" / "enrichment" / "jlpt-classifications.json")
    grammar = _load_if_exists(REPO_ROOT / "data" / "grammar" / "grammar.json")
    if jlpt is None or grammar is None:
        pytest.skip("files not built")
    known = {gp["id"] for gp in grammar.get("grammar_points", [])}
    for entry in jlpt.get("classifications", []):
        if entry.get("kind") != "grammar":
            continue
        gid = entry.get("grammar_id")
        assert gid in known, \
            f"jlpt grammar classification references unknown grammar_id {gid!r}"


def test_radicals_wikipedia_coverage_above_threshold() -> None:
    """v0.4.0 regression: radicals.json must have at least 77% of its 253
    entries populated with Kangxi numbers and English meanings from
    Wikipedia. If the parser regresses or the Wikipedia pin drifts, this
    test fails before the build ships."""
    data = _load_if_exists(REPO_ROOT / "data" / "core" / "radicals.json")
    if data is None:
        pytest.skip("radicals.json not built yet")
    radicals = data.get("radicals", [])
    assert radicals, "radicals list is empty"
    with_meaning = sum(1 for r in radicals if r.get("meanings"))
    with_classical = sum(1 for r in radicals if r.get("classical_number") is not None)
    total = len(radicals)
    # Coverage floor is 77% — actual ingestion at v0.4.0 is 77.9% (197/253).
    # If this drops, either Wikipedia's pinned revision is missing data
    # or the parser has regressed.
    assert with_meaning >= int(total * 0.77), \
        f"radicals meaning coverage {with_meaning}/{total} below 77% threshold"
    assert with_classical == with_meaning, \
        f"classical_number coverage ({with_classical}) should equal meaning " \
        f"coverage ({with_meaning}) — they are populated together"
    # Spot checks: canonical radicals must be populated with correct values.
    by_char = {r["radical"]: r for r in radicals}
    for ch, expected_number, expected_meaning in (
        ("一", 1, "one"),
        ("人", 9, "man"),
        ("水", 85, "water"),
    ):
        entry = by_char.get(ch)
        assert entry is not None, f"radical {ch!r} missing from radicals.json"
        assert entry["classical_number"] == expected_number, \
            f"radical {ch!r} should have Kangxi #{expected_number}, got {entry['classical_number']!r}"
        assert expected_meaning in entry["meanings"], \
            f"radical {ch!r} meanings should include {expected_meaning!r}, got {entry['meanings']!r}"


def test_invariant_word_to_kanji_inverse_of_kanji_to_words() -> None:
    """word-to-kanji should be the exact inverse of kanji-to-words
    restricted to non-orphan characters. For every (kanji -> word_id)
    in kanji-to-words, there should be a matching (word_id -> kanji)
    in word-to-kanji."""
    k2w = _load_if_exists(REPO_ROOT / "data" / "cross-refs" / "kanji-to-words.json")
    w2k = _load_if_exists(REPO_ROOT / "data" / "cross-refs" / "word-to-kanji.json")
    if k2w is None or w2k is None:
        pytest.skip("files not built")
    w2k_map = w2k.get("mapping", {})
    for kanji, word_ids in k2w.get("mapping", {}).items():
        for wid in word_ids:
            assert kanji in w2k_map.get(wid, []), \
                f"Inverse mismatch: {kanji!r} in kanji-to-words[{wid}] " \
                f"but not in word-to-kanji[{wid}]"
