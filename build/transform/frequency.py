"""Frequency transform.

Phase 2 scope: KANJIDIC2 newspaper frequency only. Modern media
frequency (JPDB) is deferred to Phase 4 pending license clarification
with the upstream maintainers; see docs/phase4-candidates.md.

Input: ``sources/jmdict-simplified/kanjidic2-all.json.tgz``

Output: ``data/enrichment/frequency-newspaper.json`` conforming to
``schemas/frequency.schema.json``.

Extracts the ``misc.frequency`` field from every KANJIDIC2 entry that
has one (typically the top ~2,500 most common kanji, ranked by
appearances in a newspaper corpus from the early 2000s). The rank is
preserved, and entries without a frequency rank are not emitted.
"""

from __future__ import annotations

import json
import tarfile
from pathlib import Path
from datetime import date

REPO_ROOT = Path(__file__).resolve().parents[2]
SOURCE_TGZ = REPO_ROOT / "sources" / "jmdict-simplified" / "kanjidic2-all.json.tgz"
OUT = REPO_ROOT / "data" / "enrichment" / "frequency-newspaper.json"


def _load_source() -> dict:
    with tarfile.open(SOURCE_TGZ, "r:gz") as tf:
        for member in tf.getmembers():
            if member.name.endswith(".json"):
                f = tf.extractfile(member)
                if f is None:
                    raise RuntimeError(f"Cannot extract {member.name}")
                return json.loads(f.read().decode("utf-8"))
    raise RuntimeError(f"No JSON file found in {SOURCE_TGZ}")


def build() -> None:
    print(f"[freq]     loading {SOURCE_TGZ.name}")
    source = _load_source()
    characters = source.get("characters", [])

    entries: list[dict] = []
    for ch in characters:
        misc = ch.get("misc", {}) or {}
        freq = misc.get("frequency")
        if freq is None:
            continue
        entries.append({
            "text": ch["literal"],
            "reading": None,
            "rank": freq,
            "count": None,
        })

    entries.sort(key=lambda e: e["rank"])
    print(f"[freq]     extracted {len(entries):,} ranked kanji")

    output = {
        "metadata": {
            "source": "KANJIDIC2 newspaper frequency field",
            "source_url": "https://www.edrdg.org/wiki/index.php/KANJIDIC_Project",
            "license": "CC-BY-SA 4.0 (EDRDG License)",
            "source_version": source.get("version", ""),
            "generated": date.today().isoformat(),
            "count": len(entries),
            "corpus": (
                "Newspaper corpus analysis. Represents the most frequently "
                "used kanji in Japanese newspapers. Only the top ~2,500 most "
                "common kanji are ranked; rarer kanji have no frequency data."
            ),
            "kind": "kanji",
            "attribution": (
                "Frequency data extracted from KANJIDIC2 (Electronic Dictionary "
                "Research and Development Group), used in conformance with the "
                "EDRDG License. See https://www.edrdg.org/edrdg/licence.html"
            ),
            "field_notes": {
                "text": "The kanji character.",
                "rank": "Frequency rank in the newspaper corpus. 1 = most common.",
                "count": "Raw occurrence count. Not provided by KANJIDIC2; always null here.",
                "corpus": "This is a newspaper corpus from roughly the early 2000s. For modern media (light novels, anime, manga, drama), see docs/phase4-candidates.md — a modern frequency source is deferred pending license clarification of available options.",
            },
        },
        "entries": entries,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"[freq]     wrote {OUT.relative_to(REPO_ROOT)}")
