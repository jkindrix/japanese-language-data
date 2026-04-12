"""Ateji (phonetic kanji spelling) extraction transform.

Filters JMdict entries to those where a kanji writing carries the
``ateji`` tag, indicating the kanji are used for their phonetic
value rather than their semantic meaning.

Ateji are a common source of confusion for learners: the kanji
in 出鱈目 (detarame, "nonsense") mean "exit-cod-eye" individually,
which provides no hint of the actual meaning. Recognizing ateji
helps learners avoid wasted effort analyzing kanji semantically
in words where the kanji serve only as phonetic markers.

Input: ``data/core/words.json``

Output: ``data/enrichment/ateji.json``
"""

from __future__ import annotations

import json
from pathlib import Path
from build.pipeline import BUILD_DATE

REPO_ROOT = Path(__file__).resolve().parents[2]
WORDS_JSON = REPO_ROOT / "data" / "core" / "words.json"
OUT = REPO_ROOT / "data" / "enrichment" / "ateji.json"


def _extract_ateji(words_data: dict) -> list[dict]:
    """Extract entries with ateji-tagged kanji writings."""
    entries: list[dict] = []
    for w in words_data.get("words", []):
        for k in w.get("kanji", []) or []:
            if "ateji" not in (k.get("tags", []) or []):
                continue

            kana_list = w.get("kana", []) or []
            primary_reading = kana_list[0].get("text", "") if kana_list else ""

            # Collect all meanings across senses
            meanings: list[str] = []
            for sense in w.get("sense", []) or []:
                for gloss in sense.get("gloss", []) or []:
                    text = gloss.get("text", "")
                    if text:
                        meanings.append(text)

            entries.append({
                "word_id": str(w.get("id", "")),
                "text": k.get("text", ""),
                "reading": primary_reading,
                "meanings": meanings[:5],
                "jlpt_waller": w.get("jlpt_waller"),
            })
            break  # one ateji writing per word is enough

    return sorted(entries, key=lambda e: e["text"])


def build() -> None:
    if not WORDS_JSON.exists():
        raise FileNotFoundError(f"Required: {WORDS_JSON}")

    print("[ateji]    loading words.json")
    words_data = json.loads(WORDS_JSON.read_text(encoding="utf-8"))
    entries = _extract_ateji(words_data)
    print(f"[ateji]    {len(entries):,} ateji entries extracted")

    output = {
        "metadata": {
            "source": "JMdict 'ateji' kanji writing tags via words.json",
            "source_url": "https://github.com/scriptin/jmdict-simplified",
            "license": "CC-BY-SA 4.0 (EDRDG License)",
            "generated": BUILD_DATE,
            "count": len(entries),
            "field_notes": {
                "word_id": "JMdict entry ID. Join with data/core/words.json for full entry.",
                "text": "The ateji kanji writing (phonetic, not semantic).",
                "reading": "Kana reading — this is the 'real' pronunciation the kanji approximate.",
                "meanings": "English glosses (up to 5). The meaning relates to the reading, not the individual kanji.",
                "jlpt_waller": "JLPT level if classified, null otherwise.",
            },
        },
        "entries": entries,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"[ateji]    wrote {OUT.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    build()
