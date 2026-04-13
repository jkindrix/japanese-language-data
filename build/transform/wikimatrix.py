"""WikiMatrix ja-en sentence corpus transform.

Reads the WikiMatrix parallel corpus (line-aligned .en/.ja text files
from a zip archive) and produces a structured sentence JSON file.

Input: ``sources/wikimatrix/en-ja.txt.zip``

Output: ``data/corpus/sentences-wikimatrix.json`` conforming to
``schemas/sentence.schema.json``.

WikiMatrix contains ~852K Japanese-English sentence pairs mined from
Wikipedia using multilingual sentence embeddings (LASER). Licensed
CC-BY-SA 4.0 (inherits from Wikipedia).

Reference: Schwenk et al. "WikiMatrix: Mining 135M Parallel Sentences
in 1620 Language Pairs from Wikipedia" (EACL 2021).
"""

from __future__ import annotations
import logging

import json
import zipfile
from pathlib import Path

from build.pipeline import BUILD_DATE

log = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parents[2]
SOURCE_ZIP = REPO_ROOT / "sources" / "wikimatrix" / "en-ja.txt.zip"
OUT = REPO_ROOT / "data" / "corpus" / "sentences-wikimatrix.json"


def build() -> None:
    log.info(f"loading {SOURCE_ZIP.name}")
    if not SOURCE_ZIP.exists():
        raise FileNotFoundError(
            f"Source not cached: {SOURCE_ZIP} (run just fetch first)"
        )

    ja_lines: list[str] = []
    en_lines: list[str] = []

    with zipfile.ZipFile(SOURCE_ZIP) as zf:
        for name in zf.namelist():
            if name.endswith(".ja"):
                ja_lines = zf.read(name).decode("utf-8").splitlines()
            elif name.endswith(".en"):
                en_lines = zf.read(name).decode("utf-8").splitlines()

    if not ja_lines or not en_lines:
        raise RuntimeError("Could not find .ja and .en files in WikiMatrix archive")

    if len(ja_lines) != len(en_lines):
        raise RuntimeError(
            f"Line count mismatch: {len(ja_lines)} JA vs {len(en_lines)} EN"
        )

    entries: list[dict] = []
    entry_id = 0
    skipped = 0

    for ja, en in zip(ja_lines, en_lines):
        ja = ja.strip()
        en = en.strip()
        if not ja or not en:
            skipped += 1
            continue
        entry_id += 1
        entries.append({
            "id": f"wikimatrix-{entry_id}",
            "japanese": ja,
            "english": en,
            "translation_id": None,
            "curated": False,
            "license_flag": "CC-BY-SA-4.0",
            "has_audio": False,
            "japanese_contributor": None,
            "english_contributor": None,
        })

    log.info(f"total: {len(entries):,} sentence pairs ({skipped:,} skipped)")

    output = {
        "metadata": {
            "source": "WikiMatrix v1 (ja-en via OPUS)",
            "source_url": "https://opus.nlpl.eu/WikiMatrix.php",
            "license": "CC-BY-SA 4.0 (derived from Wikipedia)",
            "source_version": "1",
            "generated": BUILD_DATE,
            "count": len(entries),
            "attribution": (
                "Sentence pairs from WikiMatrix (Schwenk et al., EACL 2021), "
                "mined from Wikipedia using LASER multilingual sentence embeddings. "
                "Licensed under CC-BY-SA 4.0. Distributed via OPUS."
            ),
            "field_notes": {
                "id": "Sequential ID prefixed 'wikimatrix-' to distinguish from other corpus IDs.",
                "japanese": "Japanese sentence text mined from Wikipedia.",
                "english": "Aligned English sentence text.",
                "curated": "False — these are embedding-aligned pairs, not editor-curated.",
                "license_flag": "CC-BY-SA 4.0 for all WikiMatrix sentences.",
            },
        },
        "sentences": entries,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
        f.write("\n")
    size = OUT.stat().st_size
    log.info(f"wrote {OUT.relative_to(REPO_ROOT)} ({size:,} bytes)")
