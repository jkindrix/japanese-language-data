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

    output = {
        "metadata": {
            "source": "Hand-curated (project original) — see grammar-curated/ for input files",
            "license": "CC-BY-SA 4.0",
            "generated": date.today().isoformat(),
            "count": len(entries),
            "by_level": by_level,
            "review_coverage": by_status,
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
