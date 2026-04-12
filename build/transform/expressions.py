"""Expression extraction transform.

Filters the JMdict source to entries that carry the ``exp`` (expression)
part-of-speech tag and emits them as a separate lexicalized-grammar
dataset.

Unlike the curated grammar dataset in ``data/grammar/grammar.json``,
which provides compositional grammar patterns with formation rules,
this file is a straightforward filter of JMdict's own expression
entries. Each entry retains its full JMdict identifier for joining
with ``data/core/words.json``.

Input: ``sources/jmdict-simplified/jmdict-examples-eng.json.tgz``

Output: ``data/grammar/expressions.json`` conforming to
``schemas/expressions.schema.json``.
"""

from __future__ import annotations

import json
from pathlib import Path
from build.pipeline import BUILD_DATE
from build.utils import load_json_from_tgz, load_vocab_jlpt_map, is_common

REPO_ROOT = Path(__file__).resolve().parents[2]
SOURCE_TGZ = REPO_ROOT / "sources" / "jmdict-simplified" / "jmdict-examples-eng.json.tgz"
OUT = REPO_ROOT / "data" / "grammar" / "expressions.json"
JLPT_ENRICHMENT = REPO_ROOT / "data" / "enrichment" / "jlpt-classifications.json"


def _load_source() -> dict:
    return load_json_from_tgz(SOURCE_TGZ)


def _load_vocab_jlpt_map() -> dict[str, str]:
    return load_vocab_jlpt_map(JLPT_ENRICHMENT)


def _is_common(word: dict) -> bool:
    return is_common(word)


def build() -> None:
    print(f"[exp]      loading {SOURCE_TGZ.name}")
    source = _load_source()
    upstream_words = source.get("words", [])

    jlpt_map = _load_vocab_jlpt_map()

    expressions: list[dict] = []
    for w in upstream_words:
        # Collect all senses that have 'exp' as a part of speech
        exp_meanings: list[str] = []
        exp_misc: list[str] = []
        for sense in w.get("sense", []) or []:
            if "exp" not in (sense.get("partOfSpeech", []) or []):
                continue
            for g in sense.get("gloss", []) or []:
                text = g.get("text", "")
                if text:
                    exp_meanings.append(text)
            for m in sense.get("misc", []) or []:
                if m not in exp_misc:
                    exp_misc.append(m)
        if not exp_meanings:
            continue

        kanji_list = [k.get("text", "") for k in w.get("kanji", []) or []]
        kana_list = [k.get("text", "") for k in w.get("kana", []) or []]

        primary_text = kanji_list[0] if kanji_list else (kana_list[0] if kana_list else "")
        primary_reading = kana_list[0] if kana_list else ""

        wid = str(w.get("id", ""))
        expressions.append({
            "id": wid,
            "text": primary_text,
            "reading": primary_reading,
            "all_kanji_writings": kanji_list,
            "all_kana_readings": kana_list,
            "meanings": exp_meanings,
            "common": _is_common(w),
            "misc": exp_misc,
            "jlpt_waller": jlpt_map.get(wid),
        })

    total = len(expressions)
    common_count = sum(1 for e in expressions if e["common"])
    print(f"[exp]      extracted {total:,} expressions  (common: {common_count:,})")

    output = {
        "metadata": {
            "source": "JMdict 'exp' (expression) part-of-speech entries via scriptin/jmdict-simplified",
            "source_url": "https://github.com/scriptin/jmdict-simplified",
            "license": "CC-BY-SA 4.0 (EDRDG License)",
            "source_version": source.get("version", ""),
            "upstream_dict_date": source.get("dictDate", ""),
            "generated": BUILD_DATE,
            "count": total,
            "attribution": (
                "Expressions extracted from JMdict (Electronic Dictionary "
                "Research and Development Group). Used in conformance with "
                "the EDRDG License. See https://www.edrdg.org/edrdg/licence.html"
            ),
            "field_notes": {
                "id": "JMdict entry ID. Can be joined with data/core/words.json via the id field.",
                "text": "Primary kanji writing, or kana if the expression is kana-only.",
                "reading": "Primary kana reading.",
                "all_kanji_writings": "Every kanji writing of the expression. Empty for kana-only expressions.",
                "all_kana_readings": "Every kana reading of the expression.",
                "meanings": "English glosses from senses that carry the 'exp' part-of-speech tag. Multiple glosses are separate senses or translations within a sense.",
                "common": "True if any writing or reading is flagged common in JMdict priority markers.",
                "misc": "Additional misc tags from JMdict (politeness, archaic, slang, etc.).",
                "jlpt_waller": "Waller JLPT level if this expression is in Waller's vocabulary list. Null otherwise.",
            },
        },
        "expressions": expressions,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"[exp]      wrote {OUT.relative_to(REPO_ROOT)}")
