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
from build.pipeline import BUILD_DATE

REPO_ROOT = Path(__file__).resolve().parents[2]
CURATED_DIR = REPO_ROOT / "grammar-curated"
OUT = REPO_ROOT / "data" / "grammar" / "grammar.json"
SENTENCES_JSON = REPO_ROOT / "data" / "corpus" / "sentences.json"
KFTT_JSON = REPO_ROOT / "data" / "corpus" / "sentences-kftt.json"

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

    The normalization performs these steps (in order):

        1. Strip outer whitespace.
        2. Strip leading/trailing quotation marks (「」『』""'').
        3. Normalize half-width katakana and digits to full-width via
           Unicode NFKC (width normalization only — this does NOT
           collapse kanji/kana equivalence).
        4. Strip trailing sentence-final punctuation (。、．，!?！？.,).
        5. Collapse internal runs of whitespace to a single space.

    Intentionally NOT normalized:

        * Kanji ↔ kana equivalence: two readings with different kanji
          count as different sentences and must not be collapsed.
        * Punctuation inside the sentence (commas, colons): they carry
          meaning.

    The goal is to close superficial formatting gaps (missing final
    period, half-width katakana, quotation-mark wrapping) without
    creating false positives. Conservative normalization is preferred
    because false positives would link a curated example to an unrelated
    Tatoeba sentence — a silent data corruption worse than a low link
    rate.
    """
    if not text:
        return ""
    import re
    import unicodedata
    normalized = text.strip()
    # Strip leading/trailing quotation marks.
    quote_chars = "「」『』""''\""
    normalized = normalized.strip(quote_chars)
    # Width-normalize half-width katakana and digits to full-width.
    normalized = unicodedata.normalize("NFKC", normalized)
    # Strip trailing sentence-final punct.
    while normalized and normalized[-1] in "。、．，!?！？.,":
        normalized = normalized[:-1]
    # Collapse runs of whitespace to single space.
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized


def _has_kanji(text: str) -> bool:
    """True if text contains at least one CJK kanji character."""
    return any("\u4e00" <= c <= "\u9fff" for c in text)


def _extract_japanese_core(pattern: str) -> str:
    """Extract the searchable Japanese portion from a grammar pattern string.

    Grammar patterns contain English metalanguage (e.g.,
    "Noun / V dict + に難くない"). This function extracts the longest
    contiguous run of Japanese characters — the functional part that
    would appear in an actual sentence.

    Returns the extracted string, or "" if no usable Japanese portion
    is found. Minimum length: 2 chars if kanji-containing, 3 chars
    if pure kana (to avoid matching ubiquitous particles like ない).
    """
    candidates = _extract_japanese_candidates(pattern)
    # Return the longest candidate (backward-compatible with callers
    # that expect a single string).
    return candidates[0] if candidates else ""


def _extract_japanese_candidates(pattern: str) -> list[str]:
    """Extract ALL searchable Japanese substrings from a pattern.

    Returns candidates sorted longest-first. Used by _find_pattern_matches
    to try multiple search terms per grammar point.
    """
    import re
    # Remove tilde markers
    p = pattern.replace("\u301c", "").replace("\uff5e", "")
    # Resolve parenthesized content: 末(に) → 末に
    p = re.sub(r"[（(]([^)）]+)[)）]", r"\1", p)
    # Split on / to get alternatives
    alternatives = [a.strip() for a in p.split("/")]
    # Collect all candidate runs
    raw_candidates: set[str] = set()
    for alt in alternatives:
        # Split on + to get segments
        segments = alt.split("+")
        for seg in segments:
            seg = seg.strip()
            runs = re.findall(
                r"[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF\u3000-\u303F\u30FC]+",
                seg,
            )
            for run in runs:
                clean = run.strip("\u3000\u3001\u3002")
                if not clean:
                    continue
                if len(clean) >= 2:
                    raw_candidates.add(clean)
    # Sort longest-first for best match quality
    return sorted(raw_candidates, key=len, reverse=True)


def _find_pattern_matches(
    entries: list[dict],
    sentences: list[tuple[str, str]],
    max_per_point: int = 5,
) -> tuple[dict[str, list[str]], int, int]:
    """Find Tatoeba sentences that contain each grammar point's pattern.

    Unlike _link_examples_to_tatoeba (which matches example *text*
    against sentence *text*), this function searches for the grammar
    *pattern string* within sentences. This yields much higher match
    rates because it finds sentences that demonstrate the grammar in
    natural use.

    Returns:
        pattern_matches: dict of grammar_id → list of sentence IDs
        matched_count: number of grammar points with ≥1 match
        total_matches: total sentence matches across all points
    """
    pattern_matches: dict[str, list[str]] = {}
    total_matches = 0
    matched_count = 0

    for entry in entries:
        candidates = _extract_japanese_candidates(entry.get("pattern", ""))
        if not candidates:
            continue
        matches: list[str] = []
        for cand in candidates:
            if len(matches) >= max_per_point:
                break
            for sid, text in sentences:
                if cand in text:
                    matches.append(sid)
                    if len(matches) >= max_per_point:
                        break
            if matches:
                break  # found matches with this candidate, stop trying others
        if matches:
            pattern_matches[entry["id"]] = matches
            total_matches += len(matches)
            matched_count += 1

    return pattern_matches, matched_count, total_matches


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
        import warnings
        warnings.warn(
            f"grammar-curated/ directory not found at {CURATED_DIR}. "
            f"grammar.json will be empty. If this is unexpected, check "
            f"that the repository is complete.",
            stacklevel=2,
        )
        print("[grammar]  WARNING: no curated directory found; emitting empty grammar.json")
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

    # Pattern-based sentence matching: search sentence corpora for sentences
    # that contain the grammar pattern's Japanese core. This is a separate,
    # higher-coverage linkage mechanism — grammar examples are constructed
    # for pedagogy and rarely match corpus text, but pattern-string search
    # finds natural usage of the grammar in real sentences.
    #
    # First pass: Tatoeba (higher quality, curated).
    # Second pass: KFTT (Wikipedia, more formal — catches N1 literary patterns
    # that don't appear in Tatoeba's conversational corpus).
    pattern_match_count = 0
    pattern_total_matches = 0
    if SENTENCES_JSON.exists() and entries:
        sentences_data = json.loads(SENTENCES_JSON.read_text(encoding="utf-8"))
        sentence_tuples = [
            (str(s["id"]), s["japanese"])
            for s in sentences_data.get("sentences", [])
        ]
        pattern_matches, pattern_match_count, pattern_total_matches = \
            _find_pattern_matches(entries, sentence_tuples)

        # Second pass: KFTT for grammar points still unmatched
        kftt_match_count = 0
        if KFTT_JSON.exists():
            kftt_data = json.loads(KFTT_JSON.read_text(encoding="utf-8"))
            kftt_tuples = [
                (str(s["id"]), s["japanese"])
                for s in kftt_data.get("sentences", [])
            ]
            # Only match entries not already matched by Tatoeba
            unmatched_entries = [e for e in entries if e["id"] not in pattern_matches]
            if unmatched_entries:
                kftt_matches, kftt_match_count, kftt_total = \
                    _find_pattern_matches(unmatched_entries, kftt_tuples)
                # Merge KFTT matches (prefix IDs with "kftt:" to distinguish source)
                for gid, sids in kftt_matches.items():
                    pattern_matches[gid] = [f"kftt:{sid}" for sid in sids]
                pattern_match_count += kftt_match_count
                pattern_total_matches += kftt_total

        # Store matches on each entry
        for entry in entries:
            entry["tatoeba_pattern_matches"] = pattern_matches.get(entry["id"], [])
        print(
            f"[grammar]  pattern matching: {pattern_match_count}/{len(entries)} "
            f"points matched ({100*pattern_match_count/len(entries):.1f}%), "
            f"{pattern_total_matches} total sentence matches"
            + (f" (incl. {kftt_match_count} from KFTT)" if kftt_match_count else "")
        )
    else:
        for entry in entries:
            entry["tatoeba_pattern_matches"] = []

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
            "generated": BUILD_DATE,
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
                "pattern_match_points": pattern_match_count,
                "pattern_match_total": pattern_total_matches,
                "pattern_match_pct": round(
                    100 * pattern_match_count / len(entries), 2
                ) if entries else 0,
                "pattern_match_method": (
                    "Separate from example-text linkage. Extracts the Japanese "
                    "core of each grammar pattern and searches sentences.json "
                    "for sentences containing it. Up to 5 matches per grammar "
                    "point. Stored in tatoeba_pattern_matches[] on each entry."
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
