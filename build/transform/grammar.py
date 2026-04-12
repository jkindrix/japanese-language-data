"""Grammar dataset transform.

Reads hand-curated grammar point JSON files from ``grammar-curated/``
and emits a validated, metadata-rich ``data/grammar/grammar.json``.

Input: ``grammar-curated/*.json`` — one file per curated grammar set
(typically organized by JLPT level, e.g., ``n5.json``, ``n4.json``).
Each file is a JSON array of grammar point entries matching the schema.

Output: ``data/grammar/grammar.json`` conforming to
``schemas/grammar.schema.json``.

Design notes:

    * Grammar entries are hand-written in our own words, citing only
      the general facts of Japanese grammar (well-known and not
      copyrightable).
    * No content is copied from Tae Kim's Guide (CC-BY-NC-SA, not
      compatible with our CC-BY-SA 4.0 output), Hanabira (unclear
      content license), Dictionary of Basic Japanese Grammar
      (proprietary), Handbook of Japanese Grammar Patterns
      (proprietary), or any other copyrighted grammar reference.
    * Every entry starts with ``review_status: "draft"``. The aspiration
      is ``native_speaker_reviewed`` but the project does not yet have
      a native-speaker review pipeline in place. See docs/contributing.md
      for the call to native-speaker reviewers.
    * Example sentences in the initial release are marked
      ``source: "original"`` — they are written by the project author,
      not retrieved from Tatoeba. A future patch could cross-reference
      original examples with matching Tatoeba sentences by text lookup.

The transform loads every .json file in the curated directory, merges
the entries, validates each against a minimum required field set,
computes review coverage stats, and writes the output.
"""

from __future__ import annotations

import json
from pathlib import Path
from datetime import date

REPO_ROOT = Path(__file__).resolve().parents[2]
CURATED_DIR = REPO_ROOT / "grammar-curated"
OUT = REPO_ROOT / "data" / "grammar" / "grammar.json"
SENTENCES_JSON = REPO_ROOT / "data" / "corpus" / "sentences.json"

REQUIRED_FIELDS = {"id", "pattern", "level", "meaning_en", "formation", "examples", "review_status", "sources"}


def _validate_entry(entry: dict, source_file: str) -> None:
    """Minimum-viable validation — the schema validator catches the rest."""
    missing = REQUIRED_FIELDS - entry.keys()
    if missing:
        raise ValueError(
            f"Grammar entry in {source_file} missing required fields: {sorted(missing)}\n"
            f"Entry id: {entry.get('id', '<no id>')}"
        )
    if not entry.get("examples"):
        raise ValueError(
            f"Grammar entry {entry.get('id')} in {source_file} has no examples."
        )


def _normalize_japanese_for_match(text: str) -> str:
    """Return a conservative normalized form of a Japanese sentence for matching.

    The normalization trims trailing sentence-final punctuation that is
    often missing or different between Tatoeba and curated examples
    (``。``, ``、``, full-width space), collapses internal whitespace to
    single characters, and strips outer whitespace. Nothing else.

    Intentionally NOT normalized:
        * Character case / width (half-width / full-width): Tatoeba
          already uses the conventional form most of the time and
          forcing a normalization would risk false matches.
        * Kanji ↔ kana equivalence: two readings with different kanji
          count as different sentences and must not be collapsed.
        * Punctuation inside the sentence (commas, colons): they carry
          meaning.

    The goal is to close the "missing final period" gap without creating
    any false positives. Conservative normalization is preferred because
    false positives would link a curated example to an unrelated Tatoeba
    sentence — a silent data corruption worse than a low link rate.
    """
    if not text:
        return ""
    normalized = text.strip()
    # Strip one trailing sentence-final punct if present.
    while normalized and normalized[-1] in "。、．，!?！？.,":
        normalized = normalized[:-1]
    # Collapse runs of whitespace to single space.
    import re
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized


def _load_tatoeba_text_index() -> tuple[dict[str, str], dict[str, str]]:
    """Build Japanese-text → Tatoeba-sentence-id indices from sentences.json.

    Returns (exact_index, normalized_index):

        * ``exact_index`` — verbatim Japanese text → sentence id
        * ``normalized_index`` — _normalize_japanese_for_match(text) → sentence id

    Exact-match wins when both indices disagree. Returns two empty
    dicts if sentences.json does not exist yet (backward-compatible
    with running grammar.build before sentences.build).

    Collisions (multiple sentences with identical normalized text)
    resolve to the first one encountered, which is deterministic given
    the upstream sorted output.
    """
    if not SENTENCES_JSON.exists():
        return {}, {}
    data = json.loads(SENTENCES_JSON.read_text(encoding="utf-8"))
    exact: dict[str, str] = {}
    normalized: dict[str, str] = {}
    for sentence in data.get("sentences", []):
        text = sentence.get("japanese", "")
        sid = sentence.get("id", "")
        if not text or not sid:
            continue
        if text not in exact:
            exact[text] = sid
        norm = _normalize_japanese_for_match(text)
        if norm and norm not in normalized:
            normalized[norm] = sid
    return exact, normalized


def _link_examples_to_tatoeba(
    entries: list[dict],
    text_index: dict[str, str],
    normalized_index: dict[str, str],
) -> tuple[int, int, int]:
    """Mutate grammar entries in place, populating sentence_id where the
    example's Japanese text matches a Tatoeba sentence.

    Matching is attempted in two passes per example:
        1. Exact-string match against ``text_index``.
        2. Normalized match against ``normalized_index`` (trailing
           punctuation and whitespace stripped).

    Returns (total_examples, linked_count, linked_via_normalization) for
    reporting. The third value is the subset of linked_count that hit
    only after normalization — useful for sanity-checking that the
    normalization pass is not overmatching.
    """
    total = 0
    linked = 0
    linked_via_norm = 0
    for entry in entries:
        for example in entry.get("examples", []):
            total += 1
            if example.get("source") == "tatoeba" and example.get("sentence_id"):
                # Already linked; leave alone (shouldn't happen in Phase 3 but
                # forward-compatible with future curated entries that reference
                # Tatoeba IDs directly)
                linked += 1
                continue
            japanese = example.get("japanese", "")
            sid = text_index.get(japanese)
            if not sid:
                sid = normalized_index.get(_normalize_japanese_for_match(japanese))
                if sid:
                    linked_via_norm += 1
            if sid:
                example["source"] = "tatoeba"
                example["sentence_id"] = sid
                linked += 1
    return total, linked, linked_via_norm


def build() -> None:
    print(f"[grammar]  loading curated files from {CURATED_DIR.relative_to(REPO_ROOT)}/")
    if not CURATED_DIR.exists():
        print(f"[grammar]  no curated directory found; emitting empty grammar.json")
        entries: list[dict] = []
    else:
        entries = []
        source_files = sorted(CURATED_DIR.glob("*.json"))
        print(f"[grammar]  found {len(source_files)} curated file(s)")
        seen_ids: set[str] = set()
        for sf in source_files:
            data = json.loads(sf.read_text(encoding="utf-8"))
            if not isinstance(data, list):
                raise ValueError(f"{sf} must be a JSON array of grammar entries")
            for entry in data:
                _validate_entry(entry, sf.name)
                gid = entry["id"]
                if gid in seen_ids:
                    raise ValueError(f"Duplicate grammar id {gid!r} in {sf.name}")
                seen_ids.add(gid)
                entries.append(entry)
            print(f"[grammar]    {sf.name}: {len(data):,} entries")

        # D2 fix: validate that every 'related' reference resolves to a known entry.
        # Broken cross-references are a hard error and fail the build.
        all_ids = {e["id"] for e in entries}
        for entry in entries:
            for rel_id in entry.get("related", []):
                if rel_id not in all_ids:
                    raise ValueError(
                        f"Grammar entry {entry['id']!r} references unknown related "
                        f"id {rel_id!r}. Either add the referenced entry or remove "
                        f"the broken reference from grammar-curated/."
                    )

    # Tatoeba sentence linkage: text-match grammar examples against the
    # sentences corpus and populate sentence_id where the Japanese text
    # matches. Low match rate is expected on initial curation (grammar
    # examples are written for pedagogy, not to match corpus entries),
    # but the mechanism is in place for future additions.
    #
    # Two-pass match: exact text, then conservatively-normalized text
    # (trailing punctuation and whitespace stripped). The normalization
    # pass is intentionally minimal — false positives would corrupt
    # the linkage silently, which is worse than a low match rate.
    exact_index, normalized_index = _load_tatoeba_text_index()
    linked_via_norm = 0
    if exact_index and entries:
        total_examples, linked_examples, linked_via_norm = _link_examples_to_tatoeba(
            entries, exact_index, normalized_index,
        )
        link_rate_pct = (100.0 * linked_examples / total_examples) if total_examples else 0.0
        print(
            f"[grammar]  Tatoeba linkage: {linked_examples}/{total_examples} "
            f"({link_rate_pct:.2f}%) examples matched "
            f"(exact + {linked_via_norm} via normalization)"
        )
    else:
        total_examples = sum(len(e.get("examples", [])) for e in entries)
        linked_examples = 0
        link_rate_pct = 0.0
        if not exact_index:
            print("[grammar]  Tatoeba linkage: skipped (sentences.json not built)")

    # Stats
    by_level: dict[str, int] = {}
    by_status: dict[str, int] = {"draft": 0, "community_reviewed": 0, "native_speaker_reviewed": 0}
    for e in entries:
        lvl = e.get("level", "")
        by_level[lvl] = by_level.get(lvl, 0) + 1
        st = e.get("review_status", "draft")
        by_status[st] = by_status.get(st, 0) + 1

    print(f"[grammar]  total entries: {len(entries):,}")
    for lvl in ("N5", "N4", "N3", "N2", "N1"):
        if lvl in by_level:
            print(f"[grammar]    {lvl}: {by_level[lvl]:,}")
    print(f"[grammar]  by review status: {by_status}")

    # Curation outliers — structural heuristics that flag entries a
    # reviewer might prioritize. These are NOT quality judgements; they
    # are purely counts of structural fields. A "sparse_examples" entry
    # is not wrong, it just has fewer examples than typical. Reviewers
    # can use these lists as triage signals.
    sparse_examples = sorted(
        e["id"] for e in entries
        if len(e.get("examples") or []) < 3
    )
    no_related = sorted(
        e["id"] for e in entries
        if not (e.get("related") or [])
    )
    no_formation_notes = sorted(
        e["id"] for e in entries
        if not (e.get("formation_notes") or [])
    )
    print(
        f"[grammar]  outliers: sparse_examples={len(sparse_examples)} "
        f"no_related={len(no_related)} "
        f"no_formation_notes={len(no_formation_notes)}"
    )

    output = {
        "metadata": {
            "source": "Hand-curated (project original) — see grammar-curated/ for input files",
            "license": "CC-BY-SA 4.0",
            "generated": date.today().isoformat(),
            "count": len(entries),
            "by_level": by_level,
            "review_coverage": by_status,
            "curation_outliers": {
                "description": (
                    "Structural-heuristic lists of entries reviewers may "
                    "wish to prioritize. These are NOT quality judgements — "
                    "they are pure counts of schema fields. A 'sparse_examples' "
                    "entry has fewer than 3 examples; 'no_related' has an "
                    "empty related array; 'no_formation_notes' has no "
                    "formation_notes entries. Most entries are structurally "
                    "uniform so these lists are short, and reviewing them "
                    "first gives a cheap reviewer signal about where the "
                    "curation is thinnest."
                ),
                "sparse_examples_count": len(sparse_examples),
                "sparse_examples": sparse_examples,
                "no_related_count": len(no_related),
                "no_related": no_related,
                "no_formation_notes_count": len(no_formation_notes),
                "no_formation_notes": no_formation_notes,
            },
            "tatoeba_linkage": {
                "total_examples": total_examples,
                "linked_examples": linked_examples,
                "linked_via_normalization": linked_via_norm,
                "link_rate_pct": round(link_rate_pct, 2),
                "method": (
                    "Two-pass text match against data/corpus/sentences.json: "
                    "first exact, then conservatively normalized (trailing "
                    "sentence-final punctuation and whitespace stripped). "
                    "Normalization never collapses kanji/kana variants or "
                    "changes width/case."
                ),
            },
            "authorship_statement": (
                "All grammar explanations are written in our own words based on "
                "general, well-known, non-copyrightable facts about Japanese "
                "grammar. We do not copy from Tae Kim's Guide to Japanese (CC-BY-"
                "NC-SA, license incompatible with our CC-BY-SA 4.0 output), "
                "Dictionary of Basic Japanese Grammar, Handbook of Japanese "
                "Grammar Patterns, or any other copyrighted source. Every entry "
                "is marked review_status=draft and awaits native-speaker review. "
                "See docs/contributing.md for the call to native-speaker reviewers."
            ),
            "attribution": (
                "Grammar dataset from the Japanese Language Data project "
                "(https://github.com/jkindrix/japanese-language-data), "
                "CC-BY-SA 4.0."
            ),
            "field_notes": {
                "id": "Stable project-assigned slug-form identifier. Used for cross-references.",
                "pattern": "The grammar pattern in Japanese notation (e.g., '～ください', 'AはBより形容詞').",
                "level": "Community-consensus JLPT level (N5-N1). Not JLPT-official.",
                "meaning_en": "Concise English explanation of what the pattern means or does.",
                "meaning_detailed": "Longer explanation of nuance, usage, and contrast with related patterns.",
                "formation": "How to form this pattern, written compactly (e.g., 'Verb-て-form + ください').",
                "formation_notes": "Additional notes on formation, irregular cases, and exceptions.",
                "formality": "Register: very_formal / formal / neutral / casual / intimate / vulgar.",
                "related": "IDs of related grammar points.",
                "examples": "Example sentences. Phase 3 examples are original (written by the project author, source: original). A future patch may cross-reference with Tatoeba sentence IDs by text match.",
                "review_status": "One of: draft (not reviewed), community_reviewed (checked by community contributor), native_speaker_reviewed (verified by a native Japanese speaker). ALL initial Phase 3 entries are draft.",
                "reviewer_notes": "Log of review comments. Empty on draft entries.",
                "sources": "References consulted (or in the case of Phase 3 initial entries, general background) when writing this entry. NOT a list of sources we copied — we did not copy. The source field is for transparency about provenance of the factual claims.",
            },
        },
        "grammar_points": entries,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"[grammar]  wrote {OUT.relative_to(REPO_ROOT)}")
