"""Wiktionary pitch accent supplement transform.

Extracts pitch accent data from the kaikki.org/wiktextract Japanese
Wiktionary JSONL, converts accent type tags to numeric mora positions
matching the Kanjium convention, and deduplicates against the Kanjium
dataset by (word, reading) pair.

Input: ``sources/wiktionary-pitch/ja-extract.jsonl.gz``

Output: ``data/enrichment/pitch-accent-wiktionary.json`` conforming to
``schemas/pitch-accent.schema.json``.

This module supplements the Kanjium pitch accent data with entries that
have pitch accent in Wiktionary but not in Kanjium. It produces a
separate file rather than merging into pitch-accent.json, preserving
clear provenance. Export modules (Yomitan, SQLite, Anki) merge the two
at export time using union semantics.

The extraction also logs overlap statistics — entries where both sources
have data for the same (word, reading) pair — so that disagreements
between sources can be monitored.
"""

from __future__ import annotations
import logging

import gzip
import json
import re
from pathlib import Path
from build.pipeline import BUILD_DATE

log = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parents[2]
SOURCE = REPO_ROOT / "sources" / "wiktionary-pitch" / "ja-extract.jsonl.gz"
KANJIUM_PATH = REPO_ROOT / "data" / "enrichment" / "pitch-accent.json"
OUT = REPO_ROOT / "data" / "enrichment" / "pitch-accent-wiktionary.json"

# Unicode characters used for moraic nasal (ん) in kaikki.org romanization
_NASAL_CHARS = re.compile(r"[\u0144\u01f9]")  # ń (U+0144), ǹ (U+01F9)

# Downstep mark used in kaikki.org romanization
_DOWNSTEP = "\ua71c"

# Small kana that merge with the preceding mora (yōon, etc.)
_SMALL_KANA = set("ゃゅょぁぃぅぇぉゎャュョァィゥェォヮ")

# Vowels in kaikki.org romanization (including accented forms)
_VOWEL_RE = re.compile(
    r"[aeiou\u00e0\u00e1\u00e8\u00e9\u00ec\u00ed\u00f2\u00f3\u00f9\u00fa]",
    re.IGNORECASE,
)

# Geminate consonants (っ represented as doubled consonants)
_GEMINATE_RE = re.compile(r"([bcdfghjklmnpqrstvwxyz])\1", re.IGNORECASE)


def _count_morae(reading: str) -> int:
    """Count morae in a kana reading."""
    if not reading:
        return 0
    return sum(1 for c in reading if c not in _SMALL_KANA)


def _parse_roman_position(roman: str) -> int | None:
    """Extract mora position from kaikki.org romanization with downstep mark.

    Counts vowels (syllable nuclei), moraic nasals (ń/ǹ for ん), and
    geminate consonants (doubled consonants for っ) in the prefix before
    the downstep mark ꜜ (U+A71C).
    """
    if not roman or _DOWNSTEP not in roman:
        return None
    prefix = roman.split(_DOWNSTEP)[0]
    vowels = len(_VOWEL_RE.findall(prefix))
    geminates = len(_GEMINATE_RE.findall(prefix))
    nasals = len(_NASAL_CHARS.findall(prefix))
    total = vowels + geminates + nasals
    return total if total > 0 else None


def _load_kanjium_lookup() -> dict[tuple[str, str], list[int]]:
    """Load Kanjium entries as (word, reading) → pitch_positions lookup."""
    if not KANJIUM_PATH.exists():
        return {}
    data = json.loads(KANJIUM_PATH.read_text(encoding="utf-8"))
    lookup: dict[tuple[str, str], list[int]] = {}
    for e in data.get("entries", []):
        key = (e.get("word", ""), e.get("reading", ""))
        lookup[key] = sorted(e.get("pitch_positions", []))
    return lookup


def build() -> None:
    log.info(f"loading {SOURCE.name}")
    if not SOURCE.exists():
        raise FileNotFoundError(
            f"Source not cached: {SOURCE} (run just fetch first)"
        )

    kanjium = _load_kanjium_lookup()
    log.info(f"Kanjium lookup: {len(kanjium):,} (word, reading) pairs")

    # Extract all pitch accent entries from Wiktionary
    wikt_entries: dict[tuple[str, str], dict] = {}
    total_ja = 0
    skipped_no_position = 0

    with gzip.open(SOURCE, "rt", encoding="utf-8") as f:
        for line in f:
            entry = json.loads(line)
            if entry.get("lang_code") != "ja":
                continue
            total_ja += 1
            word = entry.get("word", "")
            if not word:
                continue

            for s in entry.get("sounds", []):
                tags = s.get("tags", [])
                if "Tokyo" not in tags:
                    continue
                reading = s.get("other", "")
                roman = s.get("roman", "")
                mora_count = _count_morae(reading) if reading else _count_morae(word)

                position = None
                if "Heiban" in tags:
                    position = 0
                elif "Atamadaka" in tags:
                    position = 1
                elif "Odaka" in tags:
                    position = mora_count if mora_count else None
                elif "Nakadaka" in tags:
                    position = _parse_roman_position(roman)

                if position is None:
                    skipped_no_position += 1
                    continue
                if not reading:
                    reading = ""

                key = (word, reading)
                if key not in wikt_entries:
                    wikt_entries[key] = {
                        "word": word,
                        "reading": reading,
                        "pitch_positions": [position],
                        "mora_count": mora_count or None,
                    }
                elif position not in wikt_entries[key]["pitch_positions"]:
                    wikt_entries[key]["pitch_positions"].append(position)

    log.info(
        f"Wiktionary: {total_ja:,} JA entries scanned, "
        f"{len(wikt_entries):,} with pitch accent, "
        f"{skipped_no_position:,} skipped (no position)"
    )

    # Compute overlap statistics before filtering
    overlap_keys = set(kanjium.keys()) & set(wikt_entries.keys())
    agree = 0
    disagree = 0
    kanjium_extra_positions = 0
    wikt_extra_positions = 0
    for key in overlap_keys:
        k_pos = sorted(kanjium[key])
        w_pos = sorted(wikt_entries[key]["pitch_positions"])
        if k_pos == w_pos:
            agree += 1
        else:
            disagree += 1
            k_set = set(k_pos)
            w_set = set(w_pos)
            if w_set - k_set:
                wikt_extra_positions += 1
            if k_set - w_set:
                kanjium_extra_positions += 1

    log.info(
        f"Overlap: {len(overlap_keys):,} shared (word, reading) pairs — "
        f"{agree:,} agree, {disagree:,} disagree "
        f"({kanjium_extra_positions} Kanjium-extra, {wikt_extra_positions} Wikt-extra)"
    )

    # Filter to entries NOT in Kanjium by (word, reading) pair
    supplement = sorted(
        (e for key, e in wikt_entries.items() if key not in kanjium),
        key=lambda e: e["word"],
    )

    log.info(f"Supplement entries (not in Kanjium): {len(supplement):,}")

    output = {
        "metadata": {
            "source": "Japanese Wiktionary via kaikki.org/wiktextract",
            "source_url": "https://kaikki.org/dictionary/downloads/ja/ja-extract.jsonl.gz",
            "license": "CC-BY-SA 4.0",
            "generated": BUILD_DATE,
            "count": len(supplement),
            "note": (
                "Pitch accent data extracted from Japanese Wiktionary (ja.wiktionary.org) "
                "via the kaikki.org/wiktextract pre-processed JSONL. Only Tokyo standard "
                "accent is included. Accent type tags (Heiban, Atamadaka, Nakadaka, Odaka) "
                "are converted to numeric mora positions matching the Kanjium convention. "
                "Entries are deduplicated against the Kanjium dataset by (word, reading) "
                "pair — this file contains only supplementary coverage for entries not "
                "in Kanjium."
            ),
            "attribution": (
                "Pitch accent data from Japanese Wiktionary (ja.wiktionary.org), "
                "extracted via wiktextract (https://github.com/tatuylonen/wiktextract). "
                "Content is CC-BY-SA 4.0 per Wikimedia Foundation terms."
            ),
            "field_notes": {
                "word": "Word spelling from Wiktionary.",
                "reading": "Kana reading from Wiktionary pronunciation section.",
                "pitch_positions": "Mora positions (0=heiban, 1=atamadaka, N=drop after Nth mora).",
                "mora_count": "Number of morae in the reading.",
            },
            "overlap_stats": {
                "shared_entries": len(overlap_keys),
                "agreements": agree,
                "disagreements": disagree,
                "kanjium_extra_positions": kanjium_extra_positions,
                "wiktionary_extra_positions": wikt_extra_positions,
                "note": (
                    "Statistics for (word, reading) pairs present in both Kanjium and "
                    "Wiktionary. Disagreements include cases where one source records "
                    "additional accepted accent patterns (subset differences) and cases "
                    "where the sources record genuinely different positions. Both are "
                    "expected — pitch accent in Japanese has real variation."
                ),
            },
        },
        "entries": supplement,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
        f.write("\n")
    log.info(f"wrote {OUT.relative_to(REPO_ROOT)} ({len(supplement):,} entries)")
