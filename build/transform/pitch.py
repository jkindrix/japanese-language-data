"""Pitch accent transform.

Parses the Kanjium ``accents.txt`` TSV file and produces a structured
pitch accent JSON file.

Input: ``sources/kanjium/accents.txt``

Output: ``data/enrichment/pitch-accent.json`` conforming to
``schemas/pitch-accent.schema.json``.

Kanjium format (tab-separated, one entry per line):

    <word>\\t<kana_reading>\\t<mora_positions>

where mora_positions is a comma-separated list of integers. A value of
0 means heiban (flat, no drop); a value of N means the accent falls
after the Nth mora. Multiple values indicate multiple accepted
patterns.

Known limitation: the Kanjium dataset is roughly frozen at 2022, so
vocabulary added after that year lacks pitch accent data. This is noted
in the metadata ``coverage_date`` field.
"""

from __future__ import annotations

import json
from pathlib import Path
from build.pipeline import BUILD_DATE

REPO_ROOT = Path(__file__).resolve().parents[2]
SOURCE = REPO_ROOT / "sources" / "kanjium" / "accents.txt"
OUT = REPO_ROOT / "data" / "enrichment" / "pitch-accent.json"


def _parse_positions(s: str) -> list[int]:
    """Parse a comma-separated list of mora positions into integers."""
    positions: list[int] = []
    for part in s.split(","):
        part = part.strip()
        if not part:
            continue
        try:
            positions.append(int(part))
        except ValueError:
            # Skip malformed positions (ignore non-integer content)
            continue
    return positions


def _count_morae(reading: str) -> int:
    """Count the morae in a kana reading.

    Morae are counted by skipping small kana (ゃゅょぁぃぅぇぉゎ and their
    katakana equivalents), which merge with the preceding mora. The long-
    vowel mark ー counts as one mora. Sokuon (っ) counts as one mora.
    """
    small_kana = set("ゃゅょぁぃぅぇぉゎャュョァィゥェォヮ")
    count = 0
    for char in reading:
        if char in small_kana:
            continue
        count += 1
    return count


def build() -> None:
    print(f"[pitch]    loading {SOURCE.name}")
    if not SOURCE.exists():
        raise FileNotFoundError(f"Source not cached: {SOURCE} (run just fetch first)")

    entries: list[dict] = []
    malformed_lines = 0
    with SOURCE.open("r", encoding="utf-8") as f:
        for line_no, raw in enumerate(f, 1):
            line = raw.rstrip("\n\r")
            if not line or line.startswith("#"):
                continue
            parts = line.split("\t")
            if len(parts) < 3:
                malformed_lines += 1
                continue
            word = parts[0]
            reading = parts[1]
            positions_str = parts[2]
            positions = _parse_positions(positions_str)
            if not positions:
                malformed_lines += 1
                continue
            entries.append({
                "word": word,
                "reading": reading,
                "pitch_positions": positions,
                "mora_count": _count_morae(reading) or None,
            })

    print(f"[pitch]    parsed {len(entries):,} entries  (malformed skipped: {malformed_lines:,})")

    output = {
        "metadata": {
            "source": "Kanjium accents.txt",
            "source_url": "https://github.com/mifunetoshiro/kanjium",
            "license": "CC-BY-SA 4.0",
            "source_version": "master branch (commit pinned via fetch.py SHA256)",
            "generated": BUILD_DATE,
            "count": len(entries),
            "coverage_date": "approximately 2022 (upstream last substantive update)",
            "attribution": (
                "Pitch accent data from the Kanjium project by mifunetoshiro "
                "and contributors, released under CC-BY-SA 4.0. See "
                "https://github.com/mifunetoshiro/kanjium"
            ),
            "field_notes": {
                "word": "Word spelling as it appears in Kanjium. Usually contains kanji; some entries are kana-only.",
                "reading": "Kana-only reading used for pitch accent alignment.",
                "pitch_positions": "Mora positions where the accent falls. 0 = heiban (flat, no drop). N > 0 = accent falls after the Nth mora. Multiple values indicate multiple accepted patterns.",
                "mora_count": "Number of morae in the reading, computed by skipping small kana (yōon, sokuon). Null if could not be determined.",
                "coverage_date": "The upstream Kanjium data is roughly frozen at 2022. Vocabulary added to Japanese after this date is unlikely to have pitch accent here.",
            },
        },
        "entries": entries,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"[pitch]    wrote {OUT.relative_to(REPO_ROOT)}")
