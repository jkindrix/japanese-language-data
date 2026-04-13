"""Word relationship extraction transform.

Extracts cross-reference relationships from JMdict sense data:
    * ``related`` (see-also references between words)
    * ``antonym`` (antonym pairs)

These are editor-curated semantic relationships embedded in JMdict
senses. Each relationship points from one word to another by text
(and optionally sense number).

Input: ``data/core/words.json``

Output: ``data/cross-refs/word-relations.json``
"""

from __future__ import annotations
import logging

import json
from pathlib import Path
from build.pipeline import BUILD_DATE

log = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parents[2]
WORDS_JSON = REPO_ROOT / "data" / "core" / "words.json"
OUT = REPO_ROOT / "data" / "cross-refs" / "word-relations.json"


def build() -> None:
    if not WORDS_JSON.exists():
        raise FileNotFoundError(f"Required: {WORDS_JSON}")

    log.info("[rel]      loading words.json")
    words_data = json.loads(WORDS_JSON.read_text(encoding="utf-8"))

    # Build text → word_id lookup for resolving references
    text_to_id: dict[str, str] = {}
    for w in words_data.get("words", []):
        wid = w.get("id", "")
        for k in w.get("kanji", []) or []:
            text = k.get("text", "")
            if text and text not in text_to_id:
                text_to_id[text] = wid
        for k in w.get("kana", []) or []:
            text = k.get("text", "")
            if text and text not in text_to_id:
                text_to_id[text] = wid

    related_pairs: list[dict] = []
    antonym_pairs: list[dict] = []
    unresolved = 0

    for w in words_data.get("words", []):
        wid = w.get("id", "")
        kanji_list = w.get("kanji", []) or []
        source_text = kanji_list[0].get("text", "") if kanji_list else (
            w.get("kana", [{}])[0].get("text", "") if w.get("kana") else ""
        )

        for sense in w.get("sense", []) or []:
            for ref in sense.get("related", []) or []:
                target_text = ref[0] if ref else ""
                target_id = text_to_id.get(target_text)
                if target_id:
                    related_pairs.append({
                        "source_id": wid,
                        "source_text": source_text,
                        "target_id": target_id,
                        "target_text": target_text,
                        "relation": "related",
                    })
                else:
                    unresolved += 1

            for ref in sense.get("antonym", []) or []:
                target_text = ref[0] if ref else ""
                target_id = text_to_id.get(target_text)
                if target_id:
                    antonym_pairs.append({
                        "source_id": wid,
                        "source_text": source_text,
                        "target_id": target_id,
                        "target_text": target_text,
                        "relation": "antonym",
                    })
                else:
                    unresolved += 1

    # Deduplicate (same pair can appear from multiple senses)
    seen: set[tuple] = set()
    deduped: list[dict] = []
    for pair in related_pairs + antonym_pairs:
        key = (pair["source_id"], pair["target_id"], pair["relation"])
        if key not in seen:
            seen.add(key)
            deduped.append(pair)

    log.info(f"related: {len(related_pairs):,} raw → {sum(1 for p in deduped if p['relation'] == 'related'):,} deduped")
    log.info(f"antonym: {len(antonym_pairs):,} raw → {sum(1 for p in deduped if p['relation'] == 'antonym'):,} deduped")
    log.info(f"unresolved references: {unresolved:,}")

    output = {
        "metadata": {
            "generated": BUILD_DATE,
            "count": len(deduped),
            "source": "JMdict cross-references (related + antonym fields) via words.json",
            "license": "CC-BY-SA 4.0 (EDRDG License)",
            "related_count": sum(1 for p in deduped if p["relation"] == "related"),
            "antonym_count": sum(1 for p in deduped if p["relation"] == "antonym"),
            "unresolved_count": unresolved,
            "attribution": (
                "Semantic relationships from JMdict (EDRDG). These are "
                "editor-curated 'see also' and 'antonym' links between entries."
            ),
            "field_notes": {
                "source_id": "Word ID of the source entry.",
                "source_text": "Primary text of the source word.",
                "target_id": "Word ID of the target entry.",
                "target_text": "Text used in the JMdict cross-reference.",
                "relation": "Relationship type: 'related' (see-also) or 'antonym'.",
            },
        },
        "relations": deduped,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
        f.write("\n")
    log.info(f"wrote {OUT.relative_to(REPO_ROOT)}")
