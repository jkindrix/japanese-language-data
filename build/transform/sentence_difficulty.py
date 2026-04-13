"""Sentence difficulty scoring transform.

Computes an estimated JLPT difficulty level for each sentence in the
Tatoeba curated corpus based on the vocabulary and kanji it contains.

Method: for each sentence, find all known vocabulary words (by surface-
form substring match), look up their JLPT levels, and assign the
sentence's difficulty as the hardest (highest N-number, i.e., N1 is
hardest) JLPT level required to understand it.

Input:
    data/corpus/sentences.json
    data/core/words.json
    data/enrichment/jlpt-classifications.json

Output: ``data/enrichment/sentence-difficulty.json``
"""

from __future__ import annotations
import logging

import json
from pathlib import Path
from build.pipeline import BUILD_DATE

log = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parents[2]
SENTENCES_JSON = REPO_ROOT / "data" / "corpus" / "sentences.json"
WORDS_JSON = REPO_ROOT / "data" / "core" / "words.json"
JLPT_JSON = REPO_ROOT / "data" / "enrichment" / "jlpt-classifications.json"
OUT = REPO_ROOT / "data" / "enrichment" / "sentence-difficulty.json"

LEVEL_ORDER = {"N5": 1, "N4": 2, "N3": 3, "N2": 4, "N1": 5}
LEVEL_FROM_INT = {1: "N5", 2: "N4", 3: "N3", 4: "N2", 5: "N1"}


def _build_word_jlpt_lookup(words_data: dict, jlpt_data: dict) -> dict[str, str]:
    """Build surface-form → JLPT level lookup.

    Maps kanji writings (≥2 chars) and kana readings (≥3 chars) to their
    JLPT level. Uses the easier (higher N-number) level when a word
    appears at multiple levels.
    """
    # Build word_id → JLPT level from classifications
    id_to_level: dict[str, str] = {}
    for entry in jlpt_data.get("classifications", []):
        if entry.get("kind") == "vocab":
            seq = entry.get("jmdict_seq", "")
            level = entry.get("level", "")
            if not seq or not level:
                continue
            if seq not in id_to_level or LEVEL_ORDER.get(level, 99) < LEVEL_ORDER.get(id_to_level[seq], 99):
                id_to_level[seq] = level

    # Build surface-form → level
    lookup: dict[str, str] = {}
    for w in words_data.get("words", []):
        wid = w.get("id", "")
        level = id_to_level.get(wid)
        if not level:
            continue
        for k in w.get("kanji", []) or []:
            text = k.get("text", "")
            if text and len(text) >= 2 and text not in lookup:
                lookup[text] = level
        for k in w.get("kana", []) or []:
            text = k.get("text", "")
            if text and len(text) >= 3 and text not in lookup:
                lookup[text] = level
    return lookup


def _build_kanji_jlpt_lookup(jlpt_data: dict) -> dict[str, str]:
    """Build kanji character → JLPT level lookup."""
    lookup: dict[str, str] = {}
    for entry in jlpt_data.get("classifications", []):
        if entry.get("kind") == "kanji":
            text = entry.get("text", "")
            level = entry.get("level", "")
            if text and level:
                lookup[text] = level
    return lookup


def _score_sentence(
    japanese: str,
    word_lookup: dict[str, str],
    kanji_lookup: dict[str, str],
) -> tuple[str | None, int, list[str]]:
    """Score a sentence's difficulty.

    Returns (level, level_int, matched_words).
    """
    max_level = 0
    matched: list[str] = []

    # Check vocabulary matches
    for text, level in word_lookup.items():
        if text in japanese:
            lvl = LEVEL_ORDER.get(level, 0)
            if lvl > max_level:
                max_level = lvl
            matched.append(text)

    # Check individual kanji
    for char in japanese:
        if char in kanji_lookup:
            lvl = LEVEL_ORDER.get(kanji_lookup[char], 0)
            if lvl > max_level:
                max_level = lvl

    if max_level == 0:
        return None, 0, matched
    return LEVEL_FROM_INT[max_level], max_level, matched


def build() -> None:
    for req in (SENTENCES_JSON, WORDS_JSON, JLPT_JSON):
        if not req.exists():
            raise FileNotFoundError(f"Required: {req}")

    log.info("[diff]     loading data")
    sentences_data = json.loads(SENTENCES_JSON.read_text(encoding="utf-8"))
    words_data = json.loads(WORDS_JSON.read_text(encoding="utf-8"))
    jlpt_data = json.loads(JLPT_JSON.read_text(encoding="utf-8"))

    word_lookup = _build_word_jlpt_lookup(words_data, jlpt_data)
    kanji_lookup = _build_kanji_jlpt_lookup(jlpt_data)
    log.info(f"{len(word_lookup):,} word forms, {len(kanji_lookup):,} kanji with JLPT levels")

    entries: list[dict] = []
    level_counts: dict[str, int] = {"N5": 0, "N4": 0, "N3": 0, "N2": 0, "N1": 0, "unscored": 0}

    for s in sentences_data.get("sentences", []):
        sid = s.get("id", "")
        japanese = s.get("japanese", "")
        if not japanese:
            continue

        level, level_int, _ = _score_sentence(japanese, word_lookup, kanji_lookup)

        entries.append({
            "sentence_id": sid,
            "estimated_level": level,
            "level_numeric": level_int,
        })

        if level:
            level_counts[level] += 1
        else:
            level_counts["unscored"] += 1

    log.info(f"scored {len(entries):,} sentences")
    for lvl in ("N5", "N4", "N3", "N2", "N1", "unscored"):
        log.info(f"{lvl}: {level_counts[lvl]:,}")

    output = {
        "metadata": {
            "source": "Derived from sentences.json + JLPT classifications",
            "license": "CC-BY-SA 4.0",
            "generated": BUILD_DATE,
            "count": len(entries),
            "level_distribution": level_counts,
            "methodology": (
                "Each sentence is scored by finding the hardest JLPT level "
                "required to understand it. Vocabulary is matched by surface-form "
                "substring (kanji ≥2 chars, kana ≥3 chars). Individual kanji are "
                "also checked. The sentence's level is the maximum JLPT level "
                "across all matched vocabulary and kanji. Sentences with no "
                "JLPT-classified content are marked null (unscored)."
            ),
            "field_notes": {
                "sentence_id": "Tatoeba sentence ID (join with sentences.json).",
                "estimated_level": "Estimated JLPT level (N5=easiest, N1=hardest). Null if no JLPT vocabulary found.",
                "level_numeric": "Numeric difficulty: 1=N5, 2=N4, 3=N3, 4=N2, 5=N1, 0=unscored.",
            },
        },
        "entries": entries,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
        f.write("\n")
    log.info(f"wrote {OUT.relative_to(REPO_ROOT)}")
