"""Common Voice Japanese transcript extraction.

Extracts unique Japanese sentence transcripts from the Mozilla Common
Voice dataset's validated.tsv file. Only transcript text is used — no
audio data is stored or distributed.

Input:
    sources/common-voice/validated.tsv
    (manual download required — see docs/phase4-candidates.md)

Output: ``data/phase4/common-voice-transcripts.json``

The Common Voice dataset requires a Mozilla account to download.
After downloading, extract the archive and place the ``validated.tsv``
file at the path above, or run::

    tar -xzf cv-corpus-*.tar.gz --wildcards '*/validated.tsv'
    mkdir -p sources/common-voice
    mv cv-corpus-*/ja/validated.tsv sources/common-voice/

License: CC-0 (public domain).
"""

from __future__ import annotations

import csv
import json
import unicodedata
from pathlib import Path
from build.pipeline import BUILD_DATE

REPO_ROOT = Path(__file__).resolve().parents[2]
SOURCE_TSV = REPO_ROOT / "sources" / "common-voice" / "validated.tsv"
OUT = REPO_ROOT / "data" / "phase4" / "common-voice-transcripts.json"


def _normalize(text: str) -> str:
    """Normalize a transcript for deduplication."""
    return unicodedata.normalize("NFKC", text.strip())


def build() -> None:
    if not SOURCE_TSV.exists():
        raise FileNotFoundError(
            f"Common Voice source not found: {SOURCE_TSV}. "
            f"Download from https://commonvoice.mozilla.org/datasets "
            f"(requires Mozilla account), extract validated.tsv, and "
            f"place it at {SOURCE_TSV}. See docs/phase4-candidates.md."
        )

    print(f"[cv]       loading {SOURCE_TSV.name}")

    seen: dict[str, dict] = {}
    total_rows = 0
    with SOURCE_TSV.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            total_rows += 1
            sentence = row.get("sentence", "").strip()
            if not sentence:
                continue
            normalized = _normalize(sentence)
            if normalized in seen:
                seen[normalized]["vote_count"] += 1
                up = int(row.get("up_votes", 0) or 0)
                down = int(row.get("down_votes", 0) or 0)
                seen[normalized]["up_votes"] += up
                seen[normalized]["down_votes"] += down
                continue

            up = int(row.get("up_votes", 0) or 0)
            down = int(row.get("down_votes", 0) or 0)
            seen[normalized] = {
                "text": sentence,
                "text_normalized": normalized,
                "vote_count": 1,
                "up_votes": up,
                "down_votes": down,
                "gender": row.get("gender", ""),
                "age": row.get("age", ""),
            }

    entries = sorted(seen.values(), key=lambda e: -e["vote_count"])

    # Remove working fields
    for e in entries:
        del e["text_normalized"]

    print(f"[cv]       {total_rows:,} rows, {len(entries):,} unique transcripts")
    if entries:
        high_quality = sum(1 for e in entries if e["up_votes"] > e["down_votes"])
        print(f"[cv]       high-quality (up > down votes): {high_quality:,}")

    output = {
        "metadata": {
            "source": "Mozilla Common Voice Japanese",
            "source_url": "https://commonvoice.mozilla.org/datasets",
            "license": "CC-0 (public domain)",
            "generated": BUILD_DATE,
            "count": len(entries),
            "note": (
                "Unique Japanese sentence transcripts from the Mozilla Common Voice "
                "crowd-sourced speech dataset. Only transcript metadata is stored — "
                "no audio data. Sentences are deduplicated by NFKC-normalized text. "
                "Vote counts aggregate across all speakers who read the same sentence."
            ),
            "attribution": (
                "Sentence transcripts from Mozilla Common Voice "
                "(https://commonvoice.mozilla.org/), released under CC-0."
            ),
            "field_notes": {
                "text": "The sentence transcript as provided by Common Voice.",
                "vote_count": "Number of validated recordings of this sentence.",
                "up_votes": "Total upvotes across all recordings of this sentence.",
                "down_votes": "Total downvotes across all recordings.",
                "gender": "Gender of the first speaker who recorded this sentence (may be empty).",
                "age": "Age range of the first speaker (may be empty).",
            },
        },
        "transcripts": entries,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"[cv]       wrote {OUT.relative_to(REPO_ROOT)}")
