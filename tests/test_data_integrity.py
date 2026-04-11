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
