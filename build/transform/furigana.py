"""Furigana alignment transform.

Maps individual kanji within compound words to their readings. This enables
ruby text rendering (furigana above kanji) and per-character reading lookups.

Source: JmdictFurigana by Doublevil (CC-BY-SA, derived from JMdict).
https://github.com/Doublevil/JmdictFurigana

Input: ``sources/jmdict-furigana/JmdictFurigana.json``
       ``data/core/words.json`` (for filtering to common subset)

Output: ``data/enrichment/furigana.json``
"""

from __future__ import annotations
import logging

import json
import zipfile
from pathlib import Path
from build.pipeline import BUILD_DATE

log = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parents[2]
SOURCE_ZIP = REPO_ROOT / "sources" / "jmdict-furigana" / "JmdictFurigana.json.zip"
# Fallback: unzipped JSON for backward compatibility with pre-fetch.py setups
SOURCE_JSON = REPO_ROOT / "sources" / "jmdict-furigana" / "JmdictFurigana.json"
WORDS_JSON = REPO_ROOT / "data" / "core" / "words.json"
OUT = REPO_ROOT / "data" / "enrichment" / "furigana.json"


def _load_source() -> list:
    """Load JmdictFurigana entries from the zip or fallback to raw JSON."""
    if SOURCE_ZIP.exists():
        with zipfile.ZipFile(SOURCE_ZIP) as zf:
            for name in zf.namelist():
                if name.endswith(".json"):
                    raw = zf.read(name).decode("utf-8-sig")
                    return json.loads(raw)
        raise RuntimeError(f"No JSON file found in {SOURCE_ZIP}")
    if SOURCE_JSON.exists():
        raw = SOURCE_JSON.read_text(encoding="utf-8-sig")
        return json.loads(raw)
    raise FileNotFoundError(
        f"JmdictFurigana source not found. Run `just fetch` first."
    )


def build() -> None:
    log.info(f"loading JmdictFurigana")
    source_entries = _load_source()
    log.info(f"{len(source_entries):,} upstream entries")

    # Load words.json to get the set of known word texts
    if WORDS_JSON.exists():
        words_data = json.loads(WORDS_JSON.read_text(encoding="utf-8"))
        # Build a set of (text, reading) pairs from words.json
        known_pairs: set[tuple[str, str]] = set()
        for w in words_data.get("words", []):
            for k in w.get("kanji", []) or []:
                kanji_text = k.get("text", "")
                for kn in w.get("kana", []) or []:
                    kana_text = kn.get("text", "")
                    if kanji_text and kana_text:
                        known_pairs.add((kanji_text, kana_text))
        log.info(f"{len(known_pairs):,} known (text, reading) pairs from words.json")
    else:
        known_pairs = None

    # Transform and filter
    entries: list[dict] = []
    for src in source_entries:
        text = src.get("text", "")
        reading = src.get("reading", "")
        furigana = src.get("furigana", [])

        if not text or not reading or not furigana:
            continue

        # Skip entries with no kanji segments (pure kana — no furigana needed)
        has_kanji_segment = any("rt" in seg for seg in furigana)
        if not has_kanji_segment:
            continue

        # If we have words.json, filter to known vocabulary
        if known_pairs is not None and (text, reading) not in known_pairs:
            continue

        entries.append({
            "text": text,
            "reading": reading,
            "segments": furigana,
        })

    log.info(f"{len(entries):,} entries after filtering")

    output = {
        "metadata": {
            "source": "JmdictFurigana by Doublevil",
            "source_url": "https://github.com/Doublevil/JmdictFurigana",
            "license": "CC-BY-SA 4.0 (derived from JMdict, EDRDG License)",
            "generated": BUILD_DATE,
            "count": len(entries),
            "attribution": (
                "Furigana alignment data from JmdictFurigana by Doublevil "
                "(https://github.com/Doublevil/JmdictFurigana), distributed "
                "under CC-BY-SA (derived from JMdict). Used in conformance "
                "with the EDRDG License."
            ),
            "field_notes": {
                "text": "Kanji writing of the word (matches words.json kanji text).",
                "reading": "Full kana reading of the word.",
                "segments": (
                    "Ordered array of reading segments. Each segment has: "
                    "'ruby' (the text segment, kanji or kana) and optionally "
                    "'rt' (the furigana reading for kanji segments). Kana-only "
                    "segments omit 'rt'. For jukujikun readings (e.g., 大人=おとな), "
                    "multiple kanji may share a single 'rt' value."
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
