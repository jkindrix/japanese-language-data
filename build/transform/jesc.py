"""JESC (Japanese-English Subtitle Corpus) sentence transform.

Reads the JESC parallel corpus (tab-separated English-Japanese pairs
from a tar.gz archive) and produces a structured sentence JSON file.

Input: ``sources/jesc/raw.tar.gz``

Output: ``data/corpus/sentences-jesc.json`` conforming to
``schemas/sentence.schema.json``.

The JESC contains ~2.8 million conversational Japanese-English sentence
pairs derived from movie and TV subtitles. Licensed CC-BY-SA 4.0.

Reference: Pryzant et al. "JESC: Japanese-English Subtitle Corpus"
(arXiv:1710.10639). Project page: https://nlp.stanford.edu/projects/jesc/
"""

from __future__ import annotations

import json
import tarfile
from pathlib import Path

from build.pipeline import BUILD_DATE

REPO_ROOT = Path(__file__).resolve().parents[2]
SOURCE_TGZ = REPO_ROOT / "sources" / "jesc" / "raw.tar.gz"
OUT = REPO_ROOT / "data" / "corpus" / "sentences-jesc.json"


def build() -> None:
    print(f"[jesc]     loading {SOURCE_TGZ.name}")
    if not SOURCE_TGZ.exists():
        raise FileNotFoundError(
            f"Source not cached: {SOURCE_TGZ} (run just fetch first)"
        )

    entries: list[dict] = []
    entry_id = 0
    skipped = 0

    with tarfile.open(SOURCE_TGZ, "r:gz") as tf:
        # The archive contains a single file named "raw"
        for member in tf.getmembers():
            if member.isfile():
                f = tf.extractfile(member)
                if f is None:
                    continue
                raw = f.read().decode("utf-8")
                break
        else:
            raise RuntimeError("No file found inside JESC archive")

        for line in raw.splitlines():
            line = line.strip()
            if not line:
                continue
            parts = line.split("\t")
            if len(parts) != 2:
                skipped += 1
                continue

            en, ja = parts
            en = en.strip()
            ja = ja.strip()

            if not ja or not en:
                skipped += 1
                continue

            entry_id += 1
            entries.append({
                "id": f"jesc-{entry_id}",
                "japanese": ja,
                "english": en,
                "translation_id": None,
                "curated": False,
                "license_flag": "CC-BY-SA-4.0",
                "has_audio": False,
                "japanese_contributor": None,
                "english_contributor": None,
            })

    print(f"[jesc]     total: {len(entries):,} sentence pairs ({skipped:,} skipped)")

    output = {
        "metadata": {
            "source": "JESC (Japanese-English Subtitle Corpus)",
            "source_url": "https://nlp.stanford.edu/projects/jesc/",
            "license": "CC-BY-SA 4.0",
            "source_version": "1.0",
            "generated": BUILD_DATE,
            "count": len(entries),
            "attribution": (
                "Sentence pairs from the Japanese-English Subtitle Corpus "
                "(JESC), licensed under CC-BY-SA 4.0. "
                "Pryzant et al., arXiv:1710.10639. "
                "See https://nlp.stanford.edu/projects/jesc/"
            ),
            "field_notes": {
                "id": "Sequential ID prefixed 'jesc-' to distinguish from other corpus IDs.",
                "japanese": "Japanese subtitle text.",
                "english": "Aligned English subtitle text.",
                "curated": "False — these are subtitle-aligned pairs, not editor-curated.",
                "license_flag": "CC-BY-SA 4.0 for all JESC sentences.",
            },
        },
        "sentences": entries,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
        f.write("\n")
    size = OUT.stat().st_size
    print(f"[jesc]     wrote {OUT.relative_to(REPO_ROOT)} ({size:,} bytes)")
