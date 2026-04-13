"""JMnedict names transform.

Reads ``sources/jmdict-simplified/jmnedict-all.json.tgz`` (ingested via
scriptin/jmdict-simplified) and transforms it into our schema.

Output: ``data/optional/names.json`` conforming to
``schemas/name.schema.json``.

The output is gated behind the ``--with-names`` build flag and gitignored
because the file is large (~150 MB uncompressed) and only useful to
specific consumers (name lookup, NLP pipelines, OCR disambiguation).

Unlike words, proper names receive minimal augmentation — they are
reference data, not learning content. The transform preserves the
JMnedict structure (kanji writings, kana readings with applies-to
relations, translations with name-type tags) and adds only the standard
metadata header with attribution.
"""

from __future__ import annotations
import logging

import json
from pathlib import Path
from build.pipeline import BUILD_DATE
from build.utils import load_json_from_tgz

log = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parents[2]
SOURCE_TGZ = REPO_ROOT / "sources" / "jmdict-simplified" / "jmnedict-all.json.tgz"
OUT = REPO_ROOT / "data" / "optional" / "names.json"


def _transform_name(entry: dict) -> dict:
    """Transform a JMnedict entry into our schema form.

    The upstream structure matches our schema closely — we preserve it
    as-is, only converting the id to a string for consistency with the
    words transform.
    """
    return {
        "id": str(entry.get("id", "")),
        "kanji": list(entry.get("kanji", []) or []),
        "kana": list(entry.get("kana", []) or []),
        "translation": list(entry.get("translation", []) or []),
    }


def build() -> None:
    log.info(f"loading {SOURCE_TGZ.name}")
    source = load_json_from_tgz(SOURCE_TGZ)
    upstream_words = source.get("words", [])
    upstream_tags = source.get("tags", {}) or {}

    log.info(f"transforming {len(upstream_words):,} entries")
    entries = [_transform_name(w) for w in upstream_words]

    output = {
        "metadata": {
            "source": "JMnedict via scriptin/jmdict-simplified",
            "source_url": "https://github.com/scriptin/jmdict-simplified",
            "license": "CC-BY-SA 4.0 (EDRDG License)",
            "source_version": source.get("version", ""),
            "generated": BUILD_DATE,
            "count": len(entries),
            "tags": upstream_tags,
            "attribution": (
                "This work uses JMnedict from the Electronic Dictionary "
                "Research and Development Group (EDRDG), used in conformance "
                "with the Group's license "
                "(https://www.edrdg.org/edrdg/licence.html). Ingested via "
                "scriptin/jmdict-simplified "
                "(https://github.com/scriptin/jmdict-simplified)."
            ),
            "field_notes": {
                "id": "JMnedict entry ID, stable across upstream revisions.",
                "kanji": "Kanji writings of the name. May be empty for kana-only names.",
                "kana": "Kana readings with appliesToKanji relations to specific kanji writings. appliesToKanji=['*'] means the reading applies to all kanji writings.",
                "translation": "Translations with name-type tags (person, place, given, surname, company, etc.).",
                "translation.type": "JMnedict name-type tags: person (full name), given (given name), surname, place, company, organization, product, work, station, unclass (unclassified), etc.",
            },
        },
        "names": entries,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
        f.write("\n")
    size = OUT.stat().st_size
    log.info(f"wrote {OUT.relative_to(REPO_ROOT)} ({len(entries):,} entries, {size:,} bytes)")
