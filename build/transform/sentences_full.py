"""Full Tatoeba sentence corpus transform.

Downloads and processes the complete Tatoeba Japanese sentence corpus
with English translations. This is separate from (and much larger than)
the JMdict-curated subset in sentences.json — it includes all Japanese
sentences contributed to Tatoeba regardless of whether they were linked
to JMdict entries by editors.

Input:
    sources/tatoeba-full/jpn_sentences.tsv.bz2
    sources/tatoeba-full/eng_sentences.tsv.bz2
    sources/tatoeba-full/links.csv
    data/corpus/sentences.json  (to mark curated overlap)

Output: ``data/corpus/sentences-tatoeba-full.json`` conforming to
``schemas/sentence.schema.json``.

License: CC-BY 2.0 FR (Tatoeba sentence text).
"""

from __future__ import annotations

import bz2
import json
from pathlib import Path
from build.pipeline import BUILD_DATE

REPO_ROOT = Path(__file__).resolve().parents[2]
SOURCE_DIR = REPO_ROOT / "sources" / "tatoeba-full"
JPN_BZ2 = SOURCE_DIR / "jpn_sentences.tsv.bz2"
ENG_BZ2 = SOURCE_DIR / "eng_sentences.tsv.bz2"
LINKS_CSV = SOURCE_DIR / "links.csv"
CURATED_JSON = REPO_ROOT / "data" / "corpus" / "sentences.json"
OUT = REPO_ROOT / "data" / "corpus" / "sentences-tatoeba-full.json"


def _load_sentences(path: Path) -> dict[str, str]:
    """Load sentences from a bz2-compressed TSV. Returns id → text."""
    sentences: dict[str, str] = {}
    raw = bz2.decompress(path.read_bytes()).decode("utf-8")
    for line in raw.splitlines():
        parts = line.split("\t")
        if len(parts) >= 3:
            sentences[parts[0]] = parts[2]
    return sentences


def _load_links(path: Path, jpn_ids: set[str], eng_ids: set[str]) -> dict[str, list[str]]:
    """Load translation links. Returns jpn_id → [eng_id, ...]."""
    links: dict[str, list[str]] = {}
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            parts = line.strip().split("\t")
            if len(parts) < 2:
                continue
            sid, tid = parts[0], parts[1]
            if sid in jpn_ids and tid in eng_ids:
                links.setdefault(sid, []).append(tid)
    return links


def build() -> None:
    for required in (JPN_BZ2, ENG_BZ2, LINKS_CSV):
        if not required.exists():
            raise FileNotFoundError(
                f"Tatoeba full corpus source not found: {required}. "
                f"Download from https://downloads.tatoeba.org/exports/"
            )

    print("[sent-f]   loading Japanese sentences")
    jpn = _load_sentences(JPN_BZ2)
    print(f"[sent-f]   {len(jpn):,} Japanese sentences")

    print("[sent-f]   loading English sentences")
    eng = _load_sentences(ENG_BZ2)
    print(f"[sent-f]   {len(eng):,} English sentences")

    print("[sent-f]   loading translation links (this takes a moment)")
    jpn_ids = set(jpn.keys())
    eng_ids = set(eng.keys())
    links = _load_links(LINKS_CSV, jpn_ids, eng_ids)
    linked_count = sum(1 for v in links.values() if v)
    print(f"[sent-f]   {linked_count:,} Japanese sentences have English translations")

    # Load curated IDs to mark overlap
    curated_ids: set[str] = set()
    if CURATED_JSON.exists():
        curated = json.loads(CURATED_JSON.read_text(encoding="utf-8"))
        curated_ids = {s["id"] for s in curated.get("sentences", [])}
        print(f"[sent-f]   {len(curated_ids):,} curated sentence IDs (for overlap marking)")

    # Build entries — only include sentences that have an English translation
    entries: list[dict] = []
    for sid in sorted(jpn.keys(), key=lambda x: int(x) if x.isdigit() else 0):
        eng_ids_for_sentence = links.get(sid, [])
        if not eng_ids_for_sentence:
            continue  # skip sentences without English translation

        # Use the first English translation
        eng_text = eng.get(eng_ids_for_sentence[0], "")

        entries.append({
            "id": sid,
            "japanese": jpn[sid],
            "english": eng_text,
            "translation_id": eng_ids_for_sentence[0],
            "curated": sid in curated_ids,
            "license_flag": "CC-BY-2.0-FR",
            "has_audio": False,
            "japanese_contributor": None,
            "english_contributor": None,
        })

    print(f"[sent-f]   {len(entries):,} JP-EN sentence pairs")
    curated_overlap = sum(1 for e in entries if e["curated"])
    print(f"[sent-f]   {curated_overlap:,} overlap with curated subset")

    output = {
        "metadata": {
            "source": "Tatoeba full Japanese corpus with English translations",
            "source_url": "https://tatoeba.org/",
            "license": "CC-BY 2.0 FR",
            "generated": BUILD_DATE,
            "count": len(entries),
            "attribution": (
                "Sentences from the Tatoeba Project (https://tatoeba.org/), "
                "contributed by volunteers worldwide, licensed under CC-BY 2.0 FR. "
                "This file contains the complete Japanese sentence corpus with "
                "English translations — a superset of the JMdict-curated subset "
                "in sentences.json."
            ),
            "field_notes": {
                "id": "Tatoeba sentence ID. View at https://tatoeba.org/en/sentences/show/<id>.",
                "japanese": "Japanese sentence text as contributed to Tatoeba.",
                "english": "English translation (first available link).",
                "translation_id": "Tatoeba ID of the English translation sentence.",
                "curated": "True if this sentence also appears in the JMdict-curated subset (sentences.json).",
                "license_flag": "CC-BY 2.0 FR for all Tatoeba sentences.",
            },
        },
        "sentences": entries,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
        f.write("\n")
    size = OUT.stat().st_size
    print(f"[sent-f]   wrote {OUT.relative_to(REPO_ROOT)} ({size:,} bytes, {size/1024/1024:.1f} MB)")
