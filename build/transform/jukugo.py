"""Jukugo (multi-kanji compound) extraction transform.

Identifies words whose primary kanji writing contains two or more
kanji characters and emits a compound index with per-character
meaning decomposition. This enables "what compounds use this kanji?"
lookups and kanji-based vocabulary study.

Input:
    data/core/words.json
    data/core/kanji.json (for per-character meanings)

Output: ``data/enrichment/jukugo-compounds.json``
"""

from __future__ import annotations
import logging

import json
from pathlib import Path
from build.pipeline import BUILD_DATE

log = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parents[2]
WORDS_JSON = REPO_ROOT / "data" / "core" / "words.json"
KANJI_JSON = REPO_ROOT / "data" / "core" / "kanji.json"
OUT = REPO_ROOT / "data" / "enrichment" / "jukugo-compounds.json"


def _is_kanji(ch: str) -> bool:
    """True if ch is in a CJK kanji block."""
    code = ord(ch)
    return (
        0x4E00 <= code <= 0x9FFF
        or 0x3400 <= code <= 0x4DBF
        or 0xF900 <= code <= 0xFAFF
    )


def _extract_compounds(
    words_data: dict,
    kanji_meanings: dict[str, list[str]],
) -> list[dict]:
    """Extract multi-kanji compounds with per-character decomposition."""
    compounds: list[dict] = []
    for w in words_data.get("words", []):
        kanji_list = w.get("kanji", []) or []
        if not kanji_list:
            continue
        text = kanji_list[0].get("text", "")
        kanji_chars = [c for c in text if _is_kanji(c)]
        if len(kanji_chars) < 2:
            continue

        kana_list = w.get("kana", []) or []
        reading = kana_list[0].get("text", "") if kana_list else ""

        # First English meaning
        meaning = ""
        for s in w.get("sense", []) or []:
            for g in s.get("gloss", []) or []:
                if g.get("text"):
                    meaning = g["text"]
                    break
            if meaning:
                break

        # Per-character meanings from kanji.json
        components = []
        for ch in kanji_chars:
            ch_meanings = kanji_meanings.get(ch, [])
            components.append({
                "kanji": ch,
                "meanings": ch_meanings[:3],
            })

        compounds.append({
            "word_id": str(w.get("id", "")),
            "text": text,
            "reading": reading,
            "meaning": meaning,
            "kanji_count": len(kanji_chars),
            "kanji_sequence": kanji_chars,
            "components": components,
            "jlpt_waller": w.get("jlpt_waller"),
        })

    return sorted(compounds, key=lambda c: c["text"])


def build() -> None:
    if not WORDS_JSON.exists():
        raise FileNotFoundError(f"Required: {WORDS_JSON}")
    if not KANJI_JSON.exists():
        raise FileNotFoundError(f"Required: {KANJI_JSON}")

    log.info("[jukugo]   loading words and kanji data")
    words_data = json.loads(WORDS_JSON.read_text(encoding="utf-8"))
    kanji_data = json.loads(KANJI_JSON.read_text(encoding="utf-8"))

    kanji_meanings: dict[str, list[str]] = {}
    for k in kanji_data.get("kanji", []):
        ch = k.get("character", "")
        meanings = k.get("meanings", {}) or {}
        kanji_meanings[ch] = meanings.get("en", []) or []

    compounds = _extract_compounds(words_data, kanji_meanings)
    log.info(f"{len(compounds):,} multi-kanji compounds extracted")

    by_count = {}
    for c in compounds:
        n = c["kanji_count"]
        by_count[n] = by_count.get(n, 0) + 1
    for n in sorted(by_count):
        log.info(f"{n}-kanji: {by_count[n]:,}")

    output = {
        "metadata": {
            "source": "Derived from JMdict common vocabulary (words.json) + KANJIDIC2 kanji meanings (kanji.json)",
            "source_url": "https://github.com/scriptin/jmdict-simplified",
            "license": "CC-BY-SA 4.0 (EDRDG License)",
            "generated": BUILD_DATE,
            "count": len(compounds),
            "field_notes": {
                "word_id": "JMdict entry ID. Join with data/core/words.json for full entry.",
                "text": "Primary kanji writing of the compound.",
                "reading": "Primary kana reading.",
                "meaning": "First English gloss from JMdict.",
                "kanji_count": "Number of kanji characters in the compound.",
                "kanji_sequence": "Ordered list of kanji characters as they appear in the compound.",
                "components": "Per-character decomposition: each kanji with its top-3 standalone meanings from KANJIDIC2. Meanings may not directly relate to the compound meaning (especially for ateji or jukujikun).",
                "jlpt_waller": "JLPT level if classified, null otherwise.",
            },
        },
        "compounds": compounds,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
        f.write("\n")
    log.info(f"wrote {OUT.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    build()
