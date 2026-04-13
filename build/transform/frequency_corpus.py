"""Corpus-derived word frequency transform.

Computes word frequency by counting how many sentences in our corpora
(Tatoeba + optionally KFTT) contain each vocabulary word. This supplements
the thin KANJIDIC2 newspaper frequency (2,501 kanji only) with word-level
frequency data derived from our own openly-licensed sentence corpus.

Method: for each sentence, tokenize by matching against known vocabulary
(words.json). A word is "present" in a sentence if any of its kanji writings
or kana readings appear as a substring of the Japanese text. This is a
simple surface-form match, not morphological analysis — it overcounts for
short words and undercounts for inflected forms. But for frequency ranking
purposes, it produces usable results from purely open data.

Input:
    data/core/words.json
    data/corpus/sentences.json
    data/corpus/sentences-kftt.json (optional, used if present)

Output: ``data/enrichment/frequency-corpus.json`` conforming to
``schemas/frequency.schema.json``.
"""

from __future__ import annotations
import logging

import json
from pathlib import Path
from build.pipeline import BUILD_DATE

log = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parents[2]
WORDS_JSON = REPO_ROOT / "data" / "core" / "words.json"
SENTENCES_JSON = REPO_ROOT / "data" / "corpus" / "sentences.json"
KFTT_JSON = REPO_ROOT / "data" / "corpus" / "sentences-kftt.json"
OUT = REPO_ROOT / "data" / "enrichment" / "frequency-corpus.json"


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _collect_surface_forms(words_data: dict) -> dict[str, tuple[str, str, str]]:
    """Build a map from surface form → (word_id, primary_text, primary_reading).

    We collect kanji writings (≥2 chars to avoid single-kanji false
    positives) and kana readings (≥3 chars to avoid ubiquitous particles).
    """
    forms: dict[str, tuple[str, str, str]] = {}
    for w in words_data.get("words", []):
        wid = w.get("id", "")
        if not wid:
            continue
        kana_list = w.get("kana", []) or []
        kanji_list = w.get("kanji", []) or []
        primary_reading = kana_list[0].get("text", "") if kana_list else ""
        primary_text = kanji_list[0].get("text", "") if kanji_list else primary_reading

        for k in kanji_list:
            text = k.get("text", "")
            if text and len(text) >= 2 and text not in forms:
                forms[text] = (wid, primary_text, primary_reading)

        for k in kana_list:
            text = k.get("text", "")
            if text and len(text) >= 3 and text not in forms:
                forms[text] = (wid, primary_text, primary_reading)

    return forms


def build() -> None:
    if not WORDS_JSON.exists():
        raise FileNotFoundError(f"Required: {WORDS_JSON}")
    if not SENTENCES_JSON.exists():
        raise FileNotFoundError(f"Required: {SENTENCES_JSON}")

    log.info("[freq-c]   loading words and sentences")
    words_data = _load_json(WORDS_JSON)
    sentences_data = _load_json(SENTENCES_JSON)

    sentences = [s.get("japanese", "") for s in sentences_data.get("sentences", [])]
    corpus_sources = ["data/corpus/sentences.json"]

    # Note: KFTT (443K sentences) is excluded from frequency computation
    # because the O(sentences × surface_forms) matching is too slow without
    # a morphological analyzer. The 25K Tatoeba sentences provide a
    # reasonable conversational-frequency signal. KFTT could be added later
    # with an Aho-Corasick implementation or MeCab tokenization.

    total_sentences = len(sentences)
    log.info(f"{total_sentences:,} sentences loaded from {len(corpus_sources)} source(s)")

    surface_forms = _collect_surface_forms(words_data)
    log.info(f"{len(surface_forms):,} surface forms to match")

    # Build metadata maps before matching
    word_readings: dict[str, str] = {}
    word_texts: dict[str, str] = {}
    for form, (wid, primary_text, reading) in surface_forms.items():
        word_readings[wid] = reading
        word_texts[wid] = primary_text

    # Sort forms longest-first so longer matches take priority.
    forms_sorted = sorted(surface_forms.items(), key=lambda x: len(x[0]), reverse=True)

    # Count occurrences: how many sentences contain each word.
    word_counts: dict[str, int] = {}
    for ja_text in sentences:
        if not ja_text:
            continue
        matched_wids: set[str] = set()
        for form, (wid, _, _) in forms_sorted:
            if wid not in matched_wids and form in ja_text:
                matched_wids.add(wid)
                word_counts[wid] = word_counts.get(wid, 0) + 1

    # Sort by count descending, assign ranks
    ranked = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)
    entries: list[dict] = []
    for rank, (wid, count) in enumerate(ranked, 1):
        entries.append({
            "text": word_texts.get(wid, wid),
            "reading": word_readings.get(wid),
            "rank": rank,
            "count": count,
        })

    log.info(f"{len(entries):,} words ranked by corpus frequency")
    if entries:
        log.info(f"top-10: {', '.join(e['text'] for e in entries[:10])}")

    output = {
        "metadata": {
            "source": "Corpus-derived word frequency from project sentence data",
            "license": "CC-BY-SA 4.0",
            "generated": BUILD_DATE,
            "count": len(entries),
            "corpus": (
                f"Derived from {total_sentences:,} sentences across "
                + " + ".join(corpus_sources)
                + ". Surface-form substring matching (not morphological analysis). "
                "Overcounts short words whose readings match grammatical substrings; "
                "undercounts inflected forms. Top-ranked entries may be false positives. "
                "For reliable word frequency, prefer MeCab-tokenized lists."
            ),
            "kind": "word",
            "attribution": (
                "Frequency counts derived from Tatoeba (CC-BY-2.0-FR) and KFTT "
                "(CC-BY-SA 3.0) sentence corpora aggregated by this project."
            ),
            "field_notes": {
                "text": "JMdict word ID (join with data/core/words.json).",
                "reading": "Primary kana reading of the word.",
                "rank": "Rank by sentence count. 1 = appears in the most sentences.",
                "count": "Number of sentences containing this word (surface-form match).",
                "methodology": (
                    "Simple substring matching of kanji writings (≥2 chars) and kana "
                    "readings (≥3 chars) against sentence Japanese text. Not morphological "
                    "analysis — inflected forms are undercounted, and words whose kana "
                    "readings match common grammatical substrings are overcounted "
                    "(e.g., してい matches していた, ました matches the verb ending). "
                    "Top-ranked entries may be false positives. For reliable rankings, "
                    "prefer the MeCab-tokenized frequency lists (frequency-wikipedia.json, "
                    "frequency-jesc.json, frequency-tatoeba.json)."
                ),
            },
        },
        "entries": entries,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
        f.write("\n")
    log.info(f"wrote {OUT.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    build()
