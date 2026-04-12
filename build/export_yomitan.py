"""Export the dataset as a Yomitan-compatible dictionary ZIP.

Converts words.json and kanji.json into the Yomitan v3 dictionary format
(term_bank, kanji_bank, tag_bank, index.json) and packages them as a ZIP
file ready for import into Yomitan.

Output: ``dist/japanese-language-data.zip``

Run via ``just export-yomitan`` or ``python -m build.export_yomitan``.
"""

from __future__ import annotations

import json
import sys
import zipfile
from pathlib import Path

from build.constants import DATA_DIR, MANIFEST_PATH, REPO_ROOT

DIST_DIR = REPO_ROOT / "dist"
WORDS_JSON = DATA_DIR / "core" / "words.json"
KANJI_JSON = DATA_DIR / "core" / "kanji.json"
OUT_ZIP = DIST_DIR / "japanese-language-data.zip"

# Max entries per bank file (Yomitan convention)
BANK_SIZE = 10000


def _build_tag_bank(words_data: dict) -> list[list]:
    """Build tag definitions from JMdict tag abbreviations."""
    tags = words_data.get("metadata", {}).get("tags", {})
    bank: list[list] = []
    for abbr, full_name in sorted(tags.items()):
        # [name, category, order, notes, score]
        category = "partOfSpeech" if abbr.startswith("v") or abbr.startswith("adj") else "misc"
        bank.append([abbr, category, 0, full_name, 0])
    return bank


def _build_term_banks(words_data: dict) -> list[list[list]]:
    """Convert words.json entries to Yomitan term_bank arrays."""
    entries: list[list] = []
    for word in words_data.get("words", []):
        wid = word.get("id", "")
        seq = int(wid) if wid.isdigit() else 0

        # Collect all POS tags across senses
        all_pos: set[str] = set()
        definitions: list[str] = []
        for sense in word.get("sense", []) or []:
            pos_tags = sense.get("partOfSpeech", []) or []
            all_pos.update(pos_tags)
            for gloss in sense.get("gloss", []) or []:
                text = gloss.get("text", "")
                if text:
                    definitions.append(text)

        if not definitions:
            continue

        rules = " ".join(sorted(all_pos))
        definition_tags = rules  # POS tags serve as definition tags

        # Determine score from JLPT level (N5=5, N1=1, unlevel=0)
        jlpt = word.get("jlpt_waller")
        score = {"N5": 5, "N4": 4, "N3": 3, "N2": 2, "N1": 1}.get(jlpt or "", 0)

        # Generate one entry per kanji writing (with the primary kana reading)
        kana_list = word.get("kana", []) or []
        primary_reading = kana_list[0].get("text", "") if kana_list else ""

        kanji_list = word.get("kanji", []) or []
        if kanji_list:
            for k in kanji_list:
                term = k.get("text", "")
                if term:
                    entries.append([
                        term,
                        primary_reading,
                        definition_tags,
                        rules,
                        score,
                        definitions,
                        seq,
                        "",
                    ])
        else:
            # Kana-only word
            if primary_reading:
                entries.append([
                    primary_reading,
                    "",
                    definition_tags,
                    rules,
                    score,
                    definitions,
                    seq,
                    "",
                ])

    # Split into bank files of BANK_SIZE
    banks: list[list[list]] = []
    for i in range(0, len(entries), BANK_SIZE):
        banks.append(entries[i:i + BANK_SIZE])
    return banks


def _build_kanji_banks(kanji_data: dict) -> list[list[list]]:
    """Convert kanji.json entries to Yomitan kanji_bank arrays."""
    entries: list[list] = []
    for k in kanji_data.get("kanji", []):
        char = k.get("character", "")
        if not char:
            continue

        readings = k.get("readings", {}) or {}
        on = " ".join(readings.get("on", []) or [])
        kun = " ".join(readings.get("kun", []) or [])

        meanings = k.get("meanings", {}) or {}
        en_meanings = meanings.get("en", []) or []

        # Tags
        tags_list: list[str] = []
        grade = k.get("grade")
        if grade in (1, 2, 3, 4, 5, 6, 8):
            tags_list.append("joyo")
        if grade in (9, 10):
            tags_list.append("jinmeiyo")
        jlpt = k.get("jlpt_waller")
        if jlpt:
            tags_list.append(jlpt)
        tags_str = " ".join(tags_list)

        # Stats
        stats: dict[str, str] = {}
        if k.get("stroke_count"):
            stats["strokes"] = str(k["stroke_count"])
        if grade is not None:
            stats["grade"] = str(grade)
        freq = k.get("frequency")
        if freq is not None:
            stats["freq"] = str(freq)
        if jlpt:
            stats["jlpt"] = jlpt

        entries.append([char, on, kun, tags_str, en_meanings, stats])

    banks: list[list[list]] = []
    for i in range(0, len(entries), BANK_SIZE):
        banks.append(entries[i:i + BANK_SIZE])
    return banks


def export() -> None:
    """Build the Yomitan dictionary ZIP."""
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    version = manifest.get("version", "dev")

    print(f"[yomitan]  loading words and kanji data")
    words_data = json.loads(WORDS_JSON.read_text(encoding="utf-8"))
    kanji_data = json.loads(KANJI_JSON.read_text(encoding="utf-8"))

    # Build components
    tag_bank = _build_tag_bank(words_data)
    term_banks = _build_term_banks(words_data)
    kanji_banks = _build_kanji_banks(kanji_data)

    index = {
        "title": "Japanese Language Data",
        "revision": version,
        "format": 3,
        "author": "japanese-language-data project",
        "url": "https://github.com/jkindrix/japanese-language-data",
        "description": (
            f"Unified Japanese dataset v{version}: "
            f"{words_data['metadata']['count']:,} words, "
            f"{kanji_data['metadata']['count']:,} kanji. "
            f"From JMdict + KANJIDIC2."
        ),
        "attribution": "See ATTRIBUTION.md in the source repository.",
        "sourceLanguage": "ja",
        "targetLanguage": "en",
        "sequenced": True,
    }

    total_terms = sum(len(b) for b in term_banks)
    total_kanji = sum(len(b) for b in kanji_banks)
    print(f"[yomitan]  {total_terms:,} term entries, {total_kanji:,} kanji entries, {len(tag_bank):,} tags")

    # Write ZIP
    DIST_DIR.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(OUT_ZIP, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("index.json", json.dumps(index, ensure_ascii=False, indent=2))
        zf.writestr("tag_bank_1.json", json.dumps(tag_bank, ensure_ascii=False))
        for i, bank in enumerate(term_banks, 1):
            zf.writestr(f"term_bank_{i}.json", json.dumps(bank, ensure_ascii=False))
        for i, bank in enumerate(kanji_banks, 1):
            zf.writestr(f"kanji_bank_{i}.json", json.dumps(bank, ensure_ascii=False))

    size = OUT_ZIP.stat().st_size
    print(f"[yomitan]  wrote {OUT_ZIP.relative_to(REPO_ROOT)} ({size:,} bytes)")


def main() -> int:
    export()
    return 0


if __name__ == "__main__":
    sys.exit(main())
