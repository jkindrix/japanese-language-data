"""JESC-derived conversational word frequency transform.

Computes word frequency by tokenizing the JESC corpus (2,801,388
Japanese-English subtitle sentence pairs from movies and TV) with
MeCab and counting lemma occurrences. Matches against words.json
for quality filtering.

This provides colloquial/conversational frequency data complementing
the formal Wikipedia frequency and the web-text Leeds frequency.
JESC subtitles represent casual spoken Japanese — a register that
learners encounter in daily media consumption.

Input:
    data/corpus/sentences-jesc.json  (JESC subtitle sentences)
    data/core/words.json             (vocabulary matching)

Output: ``data/enrichment/frequency-jesc.json`` conforming to
``schemas/frequency.schema.json``.

Requires: mecab-python3, unidic-lite (pip install mecab-python3 unidic-lite)
"""

from __future__ import annotations
import logging

import json
from collections import Counter
from pathlib import Path

from build.pipeline import BUILD_DATE
from build.transform.frequency_wikipedia import _tokenize_sentences, _build_word_lookup

log = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parents[2]
JESC_JSON = REPO_ROOT / "data" / "corpus" / "sentences-jesc.json"
WORDS_JSON = REPO_ROOT / "data" / "core" / "words.json"
OUT = REPO_ROOT / "data" / "enrichment" / "frequency-jesc.json"


def build() -> None:
    if not JESC_JSON.exists():
        raise FileNotFoundError(
            f"JESC corpus not found: {JESC_JSON}. "
            f"Run the build pipeline to generate it (just build)."
        )
    if not WORDS_JSON.exists():
        raise FileNotFoundError(f"Required: {WORDS_JSON}")

    log.info("loading JESC corpus")
    jesc_data = json.loads(JESC_JSON.read_text(encoding="utf-8"))
    sentences = [s["japanese"] for s in jesc_data.get("sentences", []) if s.get("japanese")]
    log.info(f"{len(sentences):,} sentences")

    log.info("tokenizing with MeCab (this may take several minutes)...")
    lemma_counts = _tokenize_sentences(sentences)
    log.info(f"{len(lemma_counts):,} unique lemmas, {sum(lemma_counts.values()):,} total tokens")

    log.info("loading words.json for vocabulary matching")
    words_data = json.loads(WORDS_JSON.read_text(encoding="utf-8"))
    word_lookup = _build_word_lookup(words_data)

    # Match against known vocabulary
    seen_wids: set[str] = set()
    matched: list[dict] = []
    for lemma, count in lemma_counts.most_common():
        if lemma not in word_lookup:
            continue
        wid, reading = word_lookup[lemma]
        if wid in seen_wids:
            continue
        seen_wids.add(wid)
        matched.append({
            "text": lemma,
            "reading": reading,
            "rank": len(matched) + 1,
            "count": count,
        })

    log.info(f"{len(matched):,} words matched against vocabulary")
    if matched:
        log.info(f"top-10: {', '.join(e['text'] for e in matched[:10])}")

    output = {
        "metadata": {
            "source": "JESC subtitle corpus, tokenized with MeCab/UniDic",
            "source_url": "https://nlp.stanford.edu/projects/jesc/",
            "license": "CC-BY-SA 4.0",
            "generated": BUILD_DATE,
            "count": len(matched),
            "corpus": (
                "Word frequencies from MeCab tokenization of the JESC corpus "
                f"({len(sentences):,} movie/TV subtitle sentences, "
                f"{sum(lemma_counts.values()):,} total tokens). Lemmatized to "
                "dictionary form via UniDic. Represents colloquial/conversational "
                "spoken Japanese as used in movies, TV dramas, and anime subtitles."
            ),
            "kind": "word",
            "tokenizer": "MeCab with unidic-lite dictionary",
            "total_tokens": sum(lemma_counts.values()),
            "unique_lemmas": len(lemma_counts),
            "attribution": (
                "Frequency data derived from the JESC corpus "
                "(https://nlp.stanford.edu/projects/jesc/, CC-BY-SA 4.0). "
                "Tokenized with MeCab using the UniDic dictionary."
            ),
            "field_notes": {
                "text": "Lemma (dictionary form) as determined by MeCab/UniDic.",
                "reading": "Primary kana reading from words.json.",
                "rank": "Rank by JESC occurrence count. 1 = most frequent.",
                "count": "Raw occurrence count in the JESC subtitle corpus.",
            },
        },
        "entries": matched,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
        f.write("\n")
    log.info(f"wrote {OUT.relative_to(REPO_ROOT)}")
