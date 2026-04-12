"""Web-corpus word frequency transform (Leeds Internet Japanese).

Parses the Leeds University Internet Japanese Word Frequency List — a
web-crawled corpus of ~253 million tokens tokenized with ChaSen.
Provides web-register frequency as a complement to the newspaper-kanji
frequency (KANJIDIC2) and spoken-media frequency (OpenSubtitles).

Method: parse the ranked frequency file, match entries against
words.json vocabulary (by kanji writings and kana readings), and emit
only matched entries with assigned ranks.

Input:
    sources/leeds/internet-jp.num
    data/core/words.json (for vocabulary matching)

Output: ``data/enrichment/frequency-web.json`` conforming to
``schemas/frequency.schema.json``.
"""

from __future__ import annotations

import json
from pathlib import Path
from build.pipeline import BUILD_DATE

REPO_ROOT = Path(__file__).resolve().parents[2]
SOURCE_FILE = REPO_ROOT / "sources" / "leeds" / "internet-jp.num"
WORDS_JSON = REPO_ROOT / "data" / "core" / "words.json"
OUT = REPO_ROOT / "data" / "enrichment" / "frequency-web.json"

# Header lines to skip (4 lines of metadata)
HEADER_LINES = 4


def _parse_frequency_file(path: Path) -> list[tuple[str, float, int]]:
    """Parse the Leeds frequency format.

    Format: ``rank ipm lemma`` (space-delimited, 4-line header).
    Returns (lemma, ipm, rank) tuples sorted by rank.
    """
    entries: list[tuple[str, float, int]] = []
    lines = path.read_text(encoding="utf-8").splitlines()
    for line in lines[HEADER_LINES:]:
        line = line.strip()
        if not line:
            continue
        parts = line.split(None, 2)
        if len(parts) != 3:
            continue
        rank_str, ipm_str, lemma = parts
        try:
            rank = int(rank_str)
            ipm = float(ipm_str)
        except ValueError:
            continue
        # Filter: must contain at least one hiragana, katakana letter, or kanji
        if not any(
            "\u3040" <= c <= "\u309f"  # hiragana
            or "\u30a1" <= c <= "\u30f6"  # katakana letters (excludes ・ U+30FB)
            or "\u4e00" <= c <= "\u9fff"  # CJK kanji
            for c in lemma
        ):
            continue
        entries.append((lemma, ipm, rank))
    return entries


def _build_word_lookup(words_data: dict) -> dict[str, tuple[str, str]]:
    """Build text -> (word_id, primary_reading) from words.json."""
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
            f"Leeds frequency source not found: {SOURCE_FILE}. "
            f"Run 'just fetch' to download."
        )
    if not WORDS_JSON.exists():
        raise FileNotFoundError(f"Required: {WORDS_JSON}")

    print(f"[freq-w]   loading {SOURCE_FILE.name}")
    raw_entries = _parse_frequency_file(SOURCE_FILE)
    print(f"[freq-w]   {len(raw_entries):,} entries after Japanese text filter")

    print("[freq-w]   loading words.json for vocabulary matching")
    words_data = json.loads(WORDS_JSON.read_text(encoding="utf-8"))
    word_lookup = _build_word_lookup(words_data)
    print(f"[freq-w]   {len(word_lookup):,} known word surface forms")

    # Match against known vocabulary, preserving frequency order.
    seen_wids: set[str] = set()
    matched: list[dict] = []
    for lemma, ipm, original_rank in raw_entries:
        if lemma not in word_lookup:
            continue
        wid, reading = word_lookup[lemma]
        if wid in seen_wids:
            continue
        seen_wids.add(wid)
        matched.append({
            "text": lemma,
            "reading": reading,
            "rank": len(matched) + 1,
            "count": round(ipm * 253.07),  # approximate raw count from ipm
        })

    print(f"[freq-w]   {len(matched):,} words matched against vocabulary")
    if matched:
        print(f"[freq-w]   top-10: {', '.join(e['text'] for e in matched[:10])}")

    output = {
        "metadata": {
            "source": "Leeds University Internet Japanese Word Frequency List",
            "source_url": "http://corpus.leeds.ac.uk/frqc/internet-jp.num",
            "license": "Creative Commons Attribution (CC-BY)",
            "generated": BUILD_DATE,
            "count": len(matched),
            "corpus": (
                "Word frequencies from a 253-million-token web-crawled Japanese "
                "corpus tokenized with ChaSen. Lemmatized to dictionary forms. "
                "Covers web-text register (news, blogs, forums). Complements "
                "frequency-newspaper.json (kanji only, newspaper) and "
                "frequency-subtitles.json (spoken media)."
            ),
            "kind": "word",
            "corpus_size_tokens": 253071774,
            "attribution": (
                "Frequency data from the Leeds University corpus, "
                "compiled by Serge Sharoff. See: Sharoff, S. (2006) "
                "'Creating general-purpose corpora using automated search "
                "engine queries.' In M. Baroni and S. Bernardini (eds.) "
                "WaCky! Working papers on the Web as Corpus, "
                "Gedit, Bologna. http://corpus.leeds.ac.uk/"
            ),
            "field_notes": {
                "text": "Lemma (dictionary form) as tokenized by ChaSen.",
                "reading": "Primary kana reading from words.json.",
                "rank": "Rank by web frequency. 1 = most frequent in web corpus.",
                "count": "Approximate raw count (derived from ipm × corpus size).",
            },
        },
        "entries": matched,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"[freq-w]   wrote {OUT.relative_to(REPO_ROOT)}")
