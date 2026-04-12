"""JLPT classifications transform.

Produces a unified JLPT classification file covering vocabulary and
kanji, derived from Jonathan Waller's JLPT Resources via two reliable
distribution channels:

    1. ``stephenmk/yomitan-jlpt-vocab`` CSV files (N5-N1 vocabulary),
       licensed CC-BY-SA 4.0. Each line is:
         ``jmdict_seq,kana,kanji,waller_definition``
       where jmdict_seq matches the JMdict ID used in our words.json.

    2. ``davidluzgouveia/kanji-data`` kanji.json (kanji JLPT levels).
       We extract ONLY the ``jlpt_new`` field per kanji; we deliberately
       ignore the WaniKani-derived fields because their license is not
       compatible with our CC-BY-SA output.

Grammar JLPT classifications are deferred to Phase 3, where the grammar
dataset itself is built. The JLPT schema supports ``kind: grammar`` so
grammar entries can be added in Phase 3 without a schema change.

Input:
    * ``sources/waller-jlpt/n{5,4,3,2,1}.csv``
    * ``sources/waller-jlpt/kanji-data.json``

Output: ``data/enrichment/jlpt-classifications.json`` conforming to
``schemas/jlpt.schema.json``.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from build.pipeline import BUILD_DATE

REPO_ROOT = Path(__file__).resolve().parents[2]
VOCAB_DIR = REPO_ROOT / "sources" / "waller-jlpt"
KANJI_JSON = REPO_ROOT / "sources" / "waller-jlpt" / "kanji-data.json"
GRAMMAR_CURATED_DIR = REPO_ROOT / "grammar-curated"
OUT = REPO_ROOT / "data" / "enrichment" / "jlpt-classifications.json"

VOCAB_FILES = {
    "N5": "n5.csv",
    "N4": "n4.csv",
    "N3": "n3.csv",
    "N2": "n2.csv",
    "N1": "n1.csv",
}


def _parse_vocab_csv(path: Path, level: str, retrieved: str) -> list[dict]:
    """Parse a stephenmk JLPT vocab CSV into classification entries."""
    entries: list[dict] = []
    with path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            kanji = row.get("kanji", "").strip()
            kana = row.get("kana", "").strip()
            definition = row.get("waller_definition", "").strip()
            jmdict_seq = row.get("jmdict_seq", "").strip()
            # Prefer the kanji writing; fall back to kana for kana-only words
            text = kanji if kanji else kana
            entries.append({
                "text": text,
                "reading": kana,
                "kind": "vocab",
                "level": level,
                "meaning_en": definition,
                "jmdict_seq": jmdict_seq,  # extra field, useful for word join
                "source_retrieved": retrieved,
            })
    return entries


def _parse_curated_grammar(retrieved: str) -> list[dict]:
    """Read hand-curated grammar points from grammar-curated/*.json and
    emit JLPT classification entries for each one.

    These entries are project-original (CC-BY-SA 4.0 directly, not
    derived from Waller or other sources). They share the same schema
    as vocab and kanji classifications but have kind=grammar.
    """
    entries: list[dict] = []
    if not GRAMMAR_CURATED_DIR.exists():
        return entries
    for path in sorted(GRAMMAR_CURATED_DIR.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            continue
        for gp in data:
            gid = gp.get("id")
            pattern = gp.get("pattern", "")
            level = gp.get("level")
            meaning = gp.get("meaning_en", "")
            if not gid or not level:
                continue
            entries.append({
                "text": pattern,
                "reading": None,
                "kind": "grammar",
                "level": level,
                "meaning_en": meaning,
                "grammar_id": gid,
                "source_retrieved": retrieved,
            })
    return entries


def _parse_kanji_jlpt(path: Path, retrieved: str) -> list[dict]:
    """Parse davidluzgouveia kanji.json for the jlpt_new field.

    Ignores all other fields. Yields entries with kind='kanji' for every
    kanji that has a non-null jlpt_new value.
    """
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    entries: list[dict] = []
    for char, info in data.items():
        jlpt_new = info.get("jlpt_new")
        if jlpt_new is None:
            continue
        level = f"N{jlpt_new}"
        # Use the first English meaning as a brief gloss (authoritative
        # meanings live in kanji.json; this is just for convenience)
        meanings = info.get("meanings") or []
        meaning_en = meanings[0] if meanings else None
        entries.append({
            "text": char,
            "reading": None,
            "kind": "kanji",
            "level": level,
            "meaning_en": meaning_en,
            "source_retrieved": retrieved,
        })
    return entries


def build() -> None:
    retrieved = BUILD_DATE

    print("[jlpt]     parsing Waller vocab CSVs (via stephenmk/yomitan-jlpt-vocab)")
    all_classifications: list[dict] = []
    per_level_counts: dict[str, int] = {}
    for level, filename in VOCAB_FILES.items():
        path = VOCAB_DIR / filename
        if not path.exists():
            print(f"[jlpt]     WARNING: missing {path}, skipping {level}")
            continue
        vocab_entries = _parse_vocab_csv(path, level, retrieved)
        per_level_counts[f"vocab_{level}"] = len(vocab_entries)
        all_classifications.extend(vocab_entries)
        print(f"[jlpt]       {level} vocab: {len(vocab_entries):,}")

    print("[jlpt]     parsing kanji JLPT levels (via davidluzgouveia/kanji-data)")
    kanji_entries = _parse_kanji_jlpt(KANJI_JSON, retrieved)
    # Count per level
    from collections import Counter
    kanji_level_counts = Counter(e["level"] for e in kanji_entries)
    for level in ("N1", "N2", "N3", "N4", "N5"):
        per_level_counts[f"kanji_{level}"] = kanji_level_counts.get(level, 0)
        print(f"[jlpt]       {level} kanji: {kanji_level_counts.get(level, 0):,}")
    all_classifications.extend(kanji_entries)

    print("[jlpt]     parsing curated grammar JLPT levels (from grammar-curated/)")
    grammar_entries = _parse_curated_grammar(retrieved)
    grammar_level_counts = Counter(e["level"] for e in grammar_entries)
    for level in ("N5", "N4", "N3", "N2", "N1"):
        per_level_counts[f"grammar_{level}"] = grammar_level_counts.get(level, 0)
        print(f"[jlpt]       {level} grammar: {grammar_level_counts.get(level, 0):,}")
    all_classifications.extend(grammar_entries)

    print(f"[jlpt]     total: {len(all_classifications):,}")

    output = {
        "metadata": {
            "source": (
                "Jonathan Waller JLPT Resources, distributed via "
                "stephenmk/yomitan-jlpt-vocab (vocab) and "
                "davidluzgouveia/kanji-data (kanji)"
            ),
            "source_url": "http://www.tanos.co.uk/jlpt/",
            "license": "CC-BY 4.0 (original Waller data) / CC-BY-SA 4.0 (redistribution)",
            "source_version_vocab": "stephenmk/yomitan-jlpt-vocab main (pinned via SHA256)",
            "source_version_kanji": "davidluzgouveia/kanji-data master (pinned via SHA256)",
            "generated": retrieved,
            "count": len(all_classifications),
            "counts_by_kind_and_level": per_level_counts,
            "attribution": (
                "JLPT classifications adapted from Jonathan Waller's JLPT "
                "Resources at http://www.tanos.co.uk/jlpt/ under CC-BY. "
                "Vocabulary data distributed via stephenmk/yomitan-jlpt-vocab "
                "(CC-BY-SA 4.0). Kanji classifications extracted from "
                "davidluzgouveia/kanji-data (code MIT, Waller data CC-BY). "
                "Only the jlpt_new field was used from davidluzgouveia; "
                "WaniKani-derived fields were deliberately ignored due to "
                "incompatible license."
            ),
            "disclaimer": (
                "These classifications are community-reverse-engineered from "
                "past JLPT test questions and are NOT JLPT-official. JLPT "
                "stopped publishing official vocabulary lists in 2010. Edge "
                "cases between levels are particularly uncertain; some entries "
                "are disputed in the community. Treat these as the best "
                "available community consensus, not canonical truth."
            ),
            "field_notes": {
                "text": "The kanji character, word (kanji writing), or grammar pattern.",
                "reading": "For vocabulary, the kana reading. Null for kanji and grammar entries.",
                "kind": "Entry kind: 'vocab', 'kanji', or 'grammar'.",
                "level": "JLPT level N5 (beginner) to N1 (advanced). Not JLPT-official.",
                "meaning_en": "Short English gloss for convenience. Authoritative meanings live in data/core/kanji.json, data/core/words.json, and data/grammar/grammar.json.",
                "jmdict_seq": "On vocab entries only: the JMdict entry ID. Can be joined with data/core/words.json via the id field.",
                "grammar_id": "On grammar entries only: the project-assigned grammar point ID. Can be joined with data/grammar/grammar.json via the id field.",
                "source_retrieved": "Date this entry was retrieved from the upstream distribution.",
            },
        },
        "classifications": all_classifications,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"[jlpt]     wrote {OUT.relative_to(REPO_ROOT)}")
