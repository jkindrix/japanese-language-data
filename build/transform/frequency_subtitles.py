"""Subtitle-corpus word frequency transform.

Computes word frequency rankings from the OpenSubtitles corpus via
hermitdave/FrequencyWords. This provides modern spoken-media frequency
data (movies, TV, anime subtitles) — the closest openly-licensed
substitute for the license-blocked JPDB modern media frequency.

Method: parse the pre-counted frequency file, match entries against
words.json vocabulary (by kanji writings and kana readings), and emit
only matched entries with assigned ranks.

Input:
    sources/opensubtitles/ja_full.txt
    data/core/words.json (for vocabulary matching)

Output: ``data/enrichment/frequency-subtitles.json`` conforming to
``schemas/frequency.schema.json``.
"""

from __future__ import annotations
import logging

import json
import re
from pathlib import Path
from build.pipeline import BUILD_DATE

log = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parents[2]
SOURCE_FILE = REPO_ROOT / "sources" / "opensubtitles" / "ja_full.txt"
WORDS_JSON = REPO_ROOT / "data" / "core" / "words.json"
OUT = REPO_ROOT / "data" / "enrichment" / "frequency-subtitles.json"

# Minimum character length for a valid frequency entry.
MIN_LENGTH = 2


def _is_japanese_text(text: str) -> bool:
    """Return True if text contains Japanese script and is not pure punctuation."""
    if len(text) < MIN_LENGTH:
        return False
    if re.match(r"^[\W\d\s]+$", text):
        return False
    return any(
        "\u3040" <= c <= "\u30ff"  # hiragana + katakana
        or "\u4e00" <= c <= "\u9fff"  # CJK Unified Ideographs
        for c in text
    )


def _parse_frequency_file(path: Path) -> list[tuple[str, int]]:
    """Parse the FrequencyWords format: one 'text count' pair per line."""
    entries: list[tuple[str, int]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        # Split on the last space (text may contain spaces)
        parts = line.rsplit(" ", 1)
        if len(parts) != 2:
            continue
        text, count_str = parts
        try:
            count = int(count_str)
        except ValueError:
            continue
        if _is_japanese_text(text):
            entries.append((text, count))
    return entries


def _build_word_lookup(words_data: dict) -> dict[str, tuple[str, str]]:
    """Build text → (word_id, primary_reading) from words.json.

    Includes all kanji writings and kana readings as lookup keys.
    """
    lookup: dict[str, tuple[str, str]] = {}
    for w in words_data.get("words", []):
        wid = w.get("id", "")
        if not wid:
            continue
        kana_list = w.get("kana", []) or []
        kanji_list = w.get("kanji", []) or []
        primary_reading = kana_list[0].get("text", "") if kana_list else ""

        for k in kanji_list:
            text = k.get("text", "")
            if text and text not in lookup:
                lookup[text] = (wid, primary_reading)
        for k in kana_list:
            text = k.get("text", "")
            if text and text not in lookup:
                lookup[text] = (wid, primary_reading)
    return lookup


def build() -> None:
    if not SOURCE_FILE.exists():
        raise FileNotFoundError(
            f"OpenSubtitles frequency source not found: {SOURCE_FILE}. "
            f"Run 'just fetch' to download."
        )
    if not WORDS_JSON.exists():
        raise FileNotFoundError(f"Required: {WORDS_JSON}")

    log.info(f"loading {SOURCE_FILE.name}")
    raw_entries = _parse_frequency_file(SOURCE_FILE)
    log.info(f"{len(raw_entries):,} entries after Japanese text filter")

    log.info("[freq-s]   loading words.json for vocabulary matching")
    words_data = json.loads(WORDS_JSON.read_text(encoding="utf-8"))
    word_lookup = _build_word_lookup(words_data)
    log.info(f"{len(word_lookup):,} known word surface forms")

    # Match against known vocabulary, preserving frequency order.
    # Track matched word IDs to avoid duplicate entries (multiple
    # surface forms of the same word).
    seen_wids: set[str] = set()
    matched: list[tuple[str, int, str, str]] = []  # (text, count, wid, reading)
    for text, count in raw_entries:
        if text not in word_lookup:
            continue
        wid, reading = word_lookup[text]
        if wid in seen_wids:
            continue
        seen_wids.add(wid)
        matched.append((text, count, wid, reading))

    # Already in frequency order (source file is pre-sorted by count desc)
    entries: list[dict] = []
    for rank, (text, count, wid, reading) in enumerate(matched, 1):
        entries.append({
            "text": text,
            "reading": reading,
            "rank": rank,
            "count": count,
        })

    log.info(f"{len(entries):,} words matched against vocabulary")
    if entries:
        log.info(f"top-10: {', '.join(e['text'] for e in entries[:10])}")

    output = {
        "metadata": {
            "source": "OpenSubtitles 2018 word frequency via hermitdave/FrequencyWords",
            "source_url": "https://github.com/hermitdave/FrequencyWords",
            "license": "CC-BY-SA 4.0 (FrequencyWords content); MIT (FrequencyWords code). Data derived from OpenSubtitles parallel corpus.",
            "generated": BUILD_DATE,
            "count": len(entries),
            "corpus": (
                "Word frequencies from OpenSubtitles 2018 Japanese subtitle corpus. "
                "Covers spoken/media Japanese: movies, TV drama, anime. "
                "Pre-tokenized by OpenSubtitles; matched against JMdict vocabulary "
                f"({len(word_lookup):,} surface forms) to filter tokenization noise. "
                f"{len(entries):,} of {len(raw_entries):,} raw entries matched."
            ),
            "kind": "word",
            "attribution": (
                "Frequency data from FrequencyWords by Hermit Dave "
                "(https://github.com/hermitdave/FrequencyWords, CC-BY-SA 4.0), "
                "derived from the OpenSubtitles parallel corpus "
                "(https://www.opensubtitles.org/). Matched against JMdict "
                "vocabulary for quality filtering."
            ),
            "field_notes": {
                "text": "Primary writing of the word (kanji or kana, matching a words.json entry).",
                "reading": "Primary kana reading of the word.",
                "rank": "Rank by subtitle occurrence count. 1 = most frequent in subtitles.",
                "count": "Raw occurrence count in the OpenSubtitles 2018 Japanese corpus.",
                "methodology": (
                    "Pre-counted frequencies from OpenSubtitles, filtered to entries "
                    "matching known JMdict vocabulary. Tokenization is upstream "
                    "(OpenSubtitles); we match surface forms against words.json kanji "
                    "writings and kana readings. Reflects spoken/media register, not "
                    "written/formal register — complements frequency-newspaper.json "
                    "(kanji) and frequency-corpus.json (Tatoeba sentences)."
                ),
            },
        },
        "entries": entries,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
        f.write("\n")
    log.info(f"wrote {OUT.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    build()
