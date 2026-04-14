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

def test_stroke_order_index_is_filtered_to_kanji_json_characters() -> None:
    """Stroke-order index must only contain characters that appear in kanji.json.

    Regression guard for the pipeline-ordering bug fixed in v0.7.2: if
    stroke_order.build() runs BEFORE kanji.build(), kanji.json does not
    exist, _load_kanji_set() returns an empty set, and no filter is
    applied. The result is that the stroke-order/ directory and the
    stroke-order-index.json index include ~286 non-kanji SVGs (digits,
    Latin letters, iteration marks, etc.) that are not in the kanji
    dataset.

    This test asserts that every character in the stroke-order index
    is either in kanji.json (a known kanji) OR the character is
    explicitly one we chose to include as a non-kanji (currently: none).
    If the filter regresses, the index will contain characters like '0'
    or 'A' or 'ー' and this test will fail with those characters listed.
    """
    index = _load_if_exists(REPO_ROOT / "data" / "enrichment" / "stroke-order-index.json")
    kanji = _load_if_exists(REPO_ROOT / "data" / "core" / "kanji.json")
    if index is None or kanji is None:
        pytest.skip("stroke-order-index.json or kanji.json not built yet")
    kanji_chars = {k["character"] for k in kanji.get("kanji", [])}
    index_chars = set(index.get("characters", {}).keys())
    non_kanji = sorted(ch for ch in index_chars if ch not in kanji_chars)
    assert not non_kanji, (
        f"stroke-order-index.json contains {len(non_kanji)} characters "
        f"not present in kanji.json: {''.join(non_kanji[:30])}"
        f"{'…' if len(non_kanji) > 30 else ''}. This means stroke_order "
        f"ran before kanji in the pipeline, an ordering regression. See "
        f"build/pipeline.py stage order."
    )


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


def test_grammar_tatoeba_linkage_floor() -> None:
    """Tatoeba linkage must not silently regress.

    The grammar dataset is built with a two-pass text-match against
    sentences.json (exact, then conservatively normalized). The absolute
    number of linked examples has been stable at 4 since the mechanism
    was introduced in v0.3.2 — the curated examples are pedagogically
    written, so hits are rare but the ones that match are stable
    (sentences like 机の上に本があります。).

    This test asserts an absolute floor of 3 linked examples: if a
    future transform change or a curated-edit somehow drops the
    mechanism entirely, the count will hit 0 and this test catches it.
    We use an absolute count rather than a percentage because the
    denominator (total examples) grows with every batch, which would
    mask a regression in the absolute mechanism.
    """
    data = _load_if_exists(REPO_ROOT / "data" / "grammar" / "grammar.json")
    if data is None:
        pytest.skip("grammar.json not built yet")
    linkage = data.get("metadata", {}).get("tatoeba_linkage") or {}
    total = linkage.get("total_examples", 0)
    linked = linkage.get("linked_examples", 0)
    linked_via_norm = linkage.get("linked_via_normalization", 0)
    assert isinstance(linked, int) and linked >= 3, (
        f"Tatoeba linkage dropped to {linked}/{total} examples. "
        f"The floor is 3 (stable since v0.3.2). If a curated example "
        f"that previously matched was edited, find a new exact match or "
        f"adjust the floor deliberately in this test."
    )
    # linked_via_normalization is tracked but not asserted — it may
    # legitimately be 0 if the curated examples and Tatoeba sentences
    # have identical trailing punctuation (which is the current case).
    assert isinstance(linked_via_norm, int) and linked_via_norm >= 0


def test_grammar_curated_sources_are_canonical() -> None:
    """All grammar-curated/*.json sources entries must use the canonical form.

    Prior to v0.7.2 cleanup, two distinct source strings coexisted:

        "General Japanese grammar knowledge."
        "General Japanese grammar knowledge (non-copyrightable facts)."

    N1/N2/N3 used the long form; N4/N5 used the short form. The long
    form is the canonical one because it is legally explicit about why
    no attribution is required (facts about grammar are not
    copyrightable). This test prevents the short form from re-appearing.
    """
    curated_dir = REPO_ROOT / "grammar-curated"
    if not curated_dir.exists():
        pytest.skip("grammar-curated/ not present")
    canonical = "General Japanese grammar knowledge (non-copyrightable facts)."
    forbidden = "General Japanese grammar knowledge."
    offenders: list[str] = []
    for path in sorted(curated_dir.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            continue
        for entry in data:
            sources = entry.get("sources") or []
            for source in sources:
                if source == forbidden:
                    offenders.append(f"{path.name}:{entry.get('id', '<no id>')}")
    assert not offenders, (
        f"grammar-curated entries using the short (non-canonical) source "
        f"string: {offenders[:10]}{'…' if len(offenders) > 10 else ''}. "
        f"Replace with the canonical form: {canonical!r}."
    )


def test_grammar_review_status_state_machine() -> None:
    """A non-draft review_status must be backed by reviewer_notes.

    The schema enum allows {draft, community_reviewed, native_speaker_reviewed}.
    An entry claiming `community_reviewed` or `native_speaker_reviewed`
    without any reviewer_notes is a state-machine violation — the state
    transition should always leave behind a record of who reviewed what
    and when.

    This is an operational pre-condition for the review pipeline
    described in docs/grammar-review.md. It is safe on the current
    dataset (all 595 entries are still `draft`) and will guard against
    a malformed merge the first time an actual reviewer files their PR.
    """
    data = _load_if_exists(REPO_ROOT / "data" / "grammar" / "grammar.json")
    if data is None:
        pytest.skip("grammar.json not built yet")
    for entry in data.get("grammar_points", []):
        status = entry.get("review_status", "draft")
        if status == "draft":
            continue
        notes = entry.get("reviewer_notes") or []
        assert notes, (
            f"grammar entry {entry.get('id')!r} has review_status={status!r} "
            f"but no reviewer_notes. Non-draft status must be backed by at "
            f"least one reviewer note recording who reviewed the entry, "
            f"when, and what they said. See docs/grammar-review.md."
        )
        # Each note must carry reviewer, date, note
        for i, note in enumerate(notes):
            assert isinstance(note, dict), \
                f"grammar entry {entry.get('id')!r} reviewer_notes[{i}] must be an object"
            for required in ("reviewer", "date", "note"):
                assert note.get(required), (
                    f"grammar entry {entry.get('id')!r} reviewer_notes[{i}] "
                    f"missing required field {required!r}"
                )


def test_radicals_wikipedia_coverage_above_threshold() -> None:
    """v0.4.0 regression (raised at v0.7.x): radicals.json must have at
    least 95% of its 253 entries populated with Kangxi numbers and
    English meanings. v0.4.0 shipped 77.9% (197/253) from Wikipedia
    alone; v0.7.x added a curated variant-to-Kangxi alias table
    (KANGXI_ALIASES in build/transform/radicals.py) that lifted this to
    95.7% (242/253). If coverage drops below 95%, either Wikipedia's
    pinned revision is missing data, the parser has regressed, or the
    alias table has been truncated."""
    data = _load_if_exists(REPO_ROOT / "data" / "core" / "radicals.json")
    if data is None:
        pytest.skip("radicals.json not built yet")
    radicals = data.get("radicals", [])
    assert radicals, "radicals list is empty"
    with_meaning = sum(1 for r in radicals if r.get("meanings"))
    with_classical = sum(1 for r in radicals if r.get("classical_number") is not None)
    total = len(radicals)
    # Coverage floor is 95% — actual ingestion at v0.7.x is 95.7% (242/253).
    # The remaining 11 unmatched entries (マ, ユ, 尚, 杰, 井, 五, 巴, 禹, 世,
    # 奄, 無) are Nelson-style variants whose Kangxi attribution is
    # ambiguous and are deliberately left unmatched.
    assert with_meaning >= int(total * 0.95), \
        f"radicals meaning coverage {with_meaning}/{total} below 95% threshold"
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
    in word-to-kanji, and vice-versa. Symmetry in both directions
    catches bugs where the two indices diverge because one was built
    from a different source than the other."""
    k2w = _load_if_exists(REPO_ROOT / "data" / "cross-refs" / "kanji-to-words.json")
    w2k = _load_if_exists(REPO_ROOT / "data" / "cross-refs" / "word-to-kanji.json")
    if k2w is None or w2k is None:
        pytest.skip("files not built")
    k2w_map = k2w.get("mapping", {})
    w2k_map = w2k.get("mapping", {})

    # Forward: every (kanji, wid) in k2w must appear as (wid, kanji) in w2k
    for kanji, word_ids in k2w_map.items():
        for wid in word_ids:
            assert kanji in w2k_map.get(wid, []), \
                f"Inverse mismatch (forward): {kanji!r} in kanji-to-words[{wid}] " \
                f"but not in word-to-kanji[{wid}]"

    # Reverse: every (wid, kanji) in w2k must appear as (kanji, wid) in k2w
    for wid, kanji_list in w2k_map.items():
        for kanji in kanji_list:
            assert wid in k2w_map.get(kanji, []), \
                f"Inverse mismatch (reverse): {kanji!r} in word-to-kanji[{wid}] " \
                f"but {wid!r} not in kanji-to-words[{kanji}]"


# ---------------------------------------------------------------------------
# Metadata consistency across all data files
# ---------------------------------------------------------------------------

_DATA_FILES = [
    "data/core/kana.json",
    "data/core/kanji.json",
    "data/core/words.json",
    "data/core/radicals.json",
    "data/corpus/sentences.json",
    "data/enrichment/pitch-accent.json",
    "data/enrichment/frequency-newspaper.json",
    "data/enrichment/frequency-corpus.json",
    "data/enrichment/frequency-subtitles.json",
    "data/enrichment/furigana.json",
    "data/enrichment/counter-words.json",
    "data/enrichment/ateji.json",
    "data/enrichment/jukugo-compounds.json",
    "data/enrichment/jlpt-classifications.json",
    "data/enrichment/stroke-order-index.json",
    "data/grammar/grammar.json",
    "data/grammar/expressions.json",
    "data/grammar/conjugations.json",
    "data/cross-refs/kanji-to-words.json",
    "data/cross-refs/word-to-kanji.json",
    "data/cross-refs/word-to-sentences.json",
    "data/cross-refs/kanji-to-radicals.json",
    "data/cross-refs/reading-to-words.json",
    "data/cross-refs/radical-to-kanji.json",
    "data/cross-refs/kanji-to-sentences.json",
]


def test_all_data_files_have_open_license() -> None:
    """Every committed data file must declare an open license (CC-BY-SA,
    CC-BY, CC0, or MIT). Sentences use CC-BY 2.0 FR from Tatoeba;
    frequency-subtitles uses MIT (FrequencyWords)."""
    for rel_path in _DATA_FILES:
        path = REPO_ROOT / rel_path
        if not path.exists():
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        meta = data.get("metadata", {})
        license_val = meta.get("license", "")
        assert any(tag in license_val for tag in ("CC-BY-SA", "CC-BY", "CC0", "MIT")), \
            f"{rel_path}: metadata.license should contain an open license, got {license_val!r}"


def test_all_data_files_have_generated_date() -> None:
    """Every committed data file must have a YYYY-MM-DD generated date."""
    import re
    date_re = re.compile(r"^\d{4}-\d{2}-\d{2}$")
    for rel_path in _DATA_FILES:
        path = REPO_ROOT / rel_path
        if not path.exists():
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        generated = data.get("metadata", {}).get("generated", "")
        assert date_re.match(generated), \
            f"{rel_path}: metadata.generated should be YYYY-MM-DD, got {generated!r}"


def test_all_data_files_have_nonempty_source() -> None:
    """Every committed data file must have a non-empty source field."""
    for rel_path in _DATA_FILES:
        path = REPO_ROOT / rel_path
        if not path.exists():
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        source = data.get("metadata", {}).get("source", "")
        assert source, f"{rel_path}: metadata.source is empty"


def test_all_data_files_count_matches_entries() -> None:
    """metadata.count should match the actual number of entries."""
    # Map of file -> (payload_key, is_dict)
    payload_keys = {
        "data/core/kana.json": "kana",
        "data/core/kanji.json": "kanji",
        "data/core/words.json": "words",
        "data/core/radicals.json": "radicals",
        "data/corpus/sentences.json": "sentences",
        "data/enrichment/pitch-accent.json": "entries",
        "data/enrichment/frequency-newspaper.json": "entries",
        "data/enrichment/jlpt-classifications.json": "classifications",
        "data/enrichment/stroke-order-index.json": "characters",
        "data/grammar/grammar.json": "grammar_points",
        "data/grammar/expressions.json": "expressions",
        "data/grammar/conjugations.json": "entries",
        "data/cross-refs/kanji-to-words.json": "mapping",
        "data/cross-refs/word-to-kanji.json": "mapping",
        "data/cross-refs/word-to-sentences.json": "mapping",
        "data/cross-refs/kanji-to-radicals.json": "mapping",
    }
    for rel_path, key in payload_keys.items():
        path = REPO_ROOT / rel_path
        if not path.exists():
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        meta_count = data.get("metadata", {}).get("count")
        if meta_count is None:
            continue  # some files may not have count in metadata
        payload = data.get(key, {})
        actual = len(payload) if payload else 0
        assert meta_count == actual, \
            f"{rel_path}: metadata.count={meta_count} but actual={actual}"


# ---------------------------------------------------------------------------
# Build-date consistency: all committed data files should have the same
# metadata.generated date (matching manifest.json.generated). A mismatch
# means some stages were rebuilt but not others — run `just build` to fix.
# ---------------------------------------------------------------------------

def test_committed_data_files_have_consistent_build_dates() -> None:
    """All committed data files must have the same metadata.generated date.

    This catches partial rebuilds where code was changed and some stages
    re-ran but others didn't, leaving baked-in metadata stale.
    Fix: run ``just build`` to rebuild all stages consistently.
    """
    manifest_path = REPO_ROOT / "manifest.json"
    if not manifest_path.exists():
        pytest.skip("manifest.json not found")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    expected_date = manifest.get("generated")
    if not expected_date:
        pytest.skip("manifest.json has no generated date")

    # Gitignored files are excluded — they're built on demand and may
    # legitimately have different dates or not exist at all.
    gitignored = {
        "data/core/words-full.json",
        "data/corpus/sentences-kftt.json",
        "data/corpus/sentences-tatoeba-full.json",
        "data/corpus/sentences-jesc.json",
        "data/corpus/sentences-wikimatrix.json",
        "data/enrichment/sentence-difficulty.json",
        "data/enrichment/frequency-tatoeba.json",
        "data/enrichment/frequency-jesc.json",
        "data/cross-refs/wordnet-synonyms.json",
        "data/cross-refs/kanji-to-words-full.json",
        "data/cross-refs/word-to-kanji-full.json",
        "data/cross-refs/reading-to-words-full.json",
        "data/cross-refs/kanji-to-sentences-full.json",
        "data/optional/names.json",
    }

    mismatches: list[str] = []
    import glob
    for path_str in sorted(glob.glob("data/**/*.json", recursive=True)):
        rel = str(Path(path_str))
        if rel in gitignored or rel.startswith("data/phase4/"):
            continue
        try:
            data = json.loads(Path(path_str).read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        generated = data.get("metadata", {}).get("generated")
        if generated and generated != expected_date:
            mismatches.append(f"{rel}: generated={generated} (expected {expected_date})")

    assert mismatches == [], (
        "Some data files have a different metadata.generated date than "
        f"manifest.json ({expected_date}). This means a partial rebuild "
        "occurred. Run `just build` to rebuild all stages consistently.\n"
        + "\n".join(mismatches)
    )
