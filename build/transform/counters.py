"""Counter-word extraction transform.

Filters JMdict entries to those carrying the ``ctr`` (counter)
part-of-speech tag and emits a dedicated index for counter-word
study and lookup.

Japanese counter words (josushi) are a persistent difficulty for
learners — there are hundreds of them, each used with specific
categories of objects, and choosing the wrong one sounds unnatural.
Having a focused, queryable index enables study apps and grammar
tools to surface the right counter for a given context.

Input: ``data/core/words.json``

Output: ``data/enrichment/counter-words.json``
"""

from __future__ import annotations

import json
from pathlib import Path
from build.pipeline import BUILD_DATE

REPO_ROOT = Path(__file__).resolve().parents[2]
WORDS_JSON = REPO_ROOT / "data" / "core" / "words.json"
OUT = REPO_ROOT / "data" / "enrichment" / "counter-words.json"


def _extract_counters(words_data: dict) -> list[dict]:
    """Extract counter-word entries from words.json."""
    counters: list[dict] = []
    for w in words_data.get("words", []):
        # Check if any sense has 'ctr' POS
        ctr_meanings: list[str] = []
        all_pos: list[str] = []
        for sense in w.get("sense", []) or []:
            pos_tags = sense.get("partOfSpeech", []) or []
            all_pos.extend(pos_tags)
            if "ctr" not in pos_tags:
                continue
            for gloss in sense.get("gloss", []) or []:
                text = gloss.get("text", "")
                if text:
                    ctr_meanings.append(text)
        if not ctr_meanings:
            continue

        kanji_list = w.get("kanji", []) or []
        kana_list = w.get("kana", []) or []
        primary_text = kanji_list[0].get("text", "") if kanji_list else (
            kana_list[0].get("text", "") if kana_list else ""
        )
        primary_reading = kana_list[0].get("text", "") if kana_list else ""

        counters.append({
            "word_id": str(w.get("id", "")),
            "text": primary_text,
            "reading": primary_reading,
            "meanings": ctr_meanings,
            "jlpt_waller": w.get("jlpt_waller"),
        })

    return sorted(counters, key=lambda c: c["text"])


def build() -> None:
    if not WORDS_JSON.exists():
        raise FileNotFoundError(f"Required: {WORDS_JSON}")

    print("[ctr]      loading words.json")
    words_data = json.loads(WORDS_JSON.read_text(encoding="utf-8"))
    counters = _extract_counters(words_data)
    print(f"[ctr]      {len(counters):,} counter words extracted")

    output = {
        "metadata": {
            "source": "JMdict 'ctr' (counter) part-of-speech entries via words.json",
            "source_url": "https://github.com/scriptin/jmdict-simplified",
            "license": "CC-BY-SA 4.0 (EDRDG License)",
            "generated": BUILD_DATE,
            "count": len(counters),
            "field_notes": {
                "word_id": "JMdict entry ID. Join with data/core/words.json for full entry.",
                "text": "Primary kanji or kana writing of the counter.",
                "reading": "Primary kana reading.",
                "meanings": "English glosses from senses carrying the 'ctr' POS tag.",
                "jlpt_waller": "JLPT level if classified, null otherwise.",
            },
        },
        "counter_words": counters,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"[ctr]      wrote {OUT.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    build()
