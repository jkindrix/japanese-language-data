"""KFTT (Kyoto Free Translation Task) sentence corpus transform.

Reads the KFTT parallel corpus (line-aligned .ja/.en text files from a
tar.gz archive) and produces a structured sentence JSON file.

Input: ``sources/kftt/kftt-data-1.0.tar.gz``

Output: ``data/corpus/sentences-kftt.json`` conforming to
``schemas/sentence.schema.json``.

The KFTT contains ~440,000 Japanese-English sentence pairs derived from
Wikipedia's Kyoto articles. Licensed CC-BY-SA 3.0 (NICT bilingual corpus).

We use the ``orig/`` (untokenized) files across all splits (train, dev,
test, tune) to maximize corpus size. Each line pair becomes one sentence
entry with a sequential ID prefixed ``kftt-`` to distinguish from
Tatoeba IDs.
"""

from __future__ import annotations

import json
import tarfile
from pathlib import Path
from build.pipeline import BUILD_DATE

REPO_ROOT = Path(__file__).resolve().parents[2]
SOURCE_TGZ = REPO_ROOT / "sources" / "kftt" / "kftt-data-1.0.tar.gz"
OUT = REPO_ROOT / "data" / "corpus" / "sentences-kftt.json"

# Splits to include (all of them for maximum coverage)
SPLITS = ["kyoto-train", "kyoto-dev", "kyoto-test", "kyoto-tune"]


def _read_lines_from_tar(tf: tarfile.TarFile, member_suffix: str) -> list[str]:
    """Read all lines from a tar member matching the given suffix."""
    for member in tf.getmembers():
        if member.name.endswith(member_suffix):
            f = tf.extractfile(member)
            if f is None:
                raise RuntimeError(f"Cannot extract {member.name}")
            return f.read().decode("utf-8").splitlines()
    raise RuntimeError(f"No member ending with {member_suffix!r} in archive")


def build() -> None:
    print(f"[kftt]     loading {SOURCE_TGZ.name}")
    if not SOURCE_TGZ.exists():
        raise FileNotFoundError(
            f"Source not cached: {SOURCE_TGZ} (run just fetch first)"
        )

    entries: list[dict] = []
    entry_id = 0

    with tarfile.open(SOURCE_TGZ, "r:gz") as tf:
        for split in SPLITS:
            ja_lines = _read_lines_from_tar(tf, f"data/orig/{split}.ja")
            en_lines = _read_lines_from_tar(tf, f"data/orig/{split}.en")

            if len(ja_lines) != len(en_lines):
                raise RuntimeError(
                    f"Line count mismatch in {split}: "
                    f"{len(ja_lines)} JA vs {len(en_lines)} EN"
                )

            split_count = 0
            for ja, en in zip(ja_lines, en_lines):
                ja = ja.strip()
                en = en.strip()
                if not ja:
                    continue
                entry_id += 1
                entries.append({
                    "id": f"kftt-{entry_id}",
                    "japanese": ja,
                    "english": en,
                    "translation_id": None,
                    "curated": False,
                    "license_flag": "CC-BY-SA-3.0",
                    "has_audio": False,
                    "japanese_contributor": None,
                    "english_contributor": None,
                })
                split_count += 1
            print(f"[kftt]       {split}: {split_count:,} pairs")

    print(f"[kftt]     total: {len(entries):,} sentence pairs")

    output = {
        "metadata": {
            "source": "KFTT (Kyoto Free Translation Task) v1.0",
            "source_url": "https://www.phontron.com/kftt/",
            "license": "CC-BY-SA 3.0 (NICT Japanese-English Bilingual Corpus of Wikipedia's Kyoto Articles)",
            "source_version": "1.0",
            "generated": BUILD_DATE,
            "count": len(entries),
            "attribution": (
                "Sentence pairs from the Kyoto Free Translation Task (KFTT), "
                "derived from NICT's Japanese-English Bilingual Corpus of "
                "Wikipedia's Kyoto Articles, licensed under CC-BY-SA 3.0. "
                "See https://www.phontron.com/kftt/"
            ),
            "field_notes": {
                "id": "Sequential ID prefixed 'kftt-' to distinguish from Tatoeba sentence IDs.",
                "japanese": "Raw (untokenized) Japanese text from KFTT orig/ split.",
                "english": "Aligned English translation.",
                "curated": "False — these are machine-aligned Wikipedia sentence pairs, not editor-curated.",
                "license_flag": "CC-BY-SA 3.0 for all KFTT sentences.",
            },
        },
        "sentences": entries,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
        f.write("\n")
    size = OUT.stat().st_size
    print(f"[kftt]     wrote {OUT.relative_to(REPO_ROOT)} ({size:,} bytes)")
