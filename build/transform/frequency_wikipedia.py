"""Wikipedia-derived word frequency transform.

Computes word frequency by tokenizing the KFTT corpus (443,849 Japanese
sentences from Wikipedia Kyoto articles) with MeCab and counting lemma
occurrences. Matches against words.json for quality filtering.

This provides formally-written Japanese frequency data complementing
the spoken-media frequency (OpenSubtitles) and web frequency (Leeds).

Input:
    data/corpus/sentences-kftt.json  (KFTT Wikipedia sentences)
    data/core/words.json             (vocabulary matching)

Output: ``data/enrichment/frequency-wikipedia.json`` conforming to
``schemas/frequency.schema.json``.

Requires: mecab-python3, unidic-lite (pip install mecab-python3 unidic-lite)
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from build.pipeline import BUILD_DATE

REPO_ROOT = Path(__file__).resolve().parents[2]
KFTT_JSON = REPO_ROOT / "data" / "corpus" / "sentences-kftt.json"
WORDS_JSON = REPO_ROOT / "data" / "core" / "words.json"
OUT = REPO_ROOT / "data" / "enrichment" / "frequency-wikipedia.json"


def _tokenize_sentences(sentences: list[str]) -> Counter:
    """Tokenize sentences with MeCab and count lemma occurrences."""
    try:
        import MeCab
    except ImportError:
        raise ImportError(
            "MeCab is required for Wikipedia frequency extraction. "
            "Install with: pip install mecab-python3 unidic-lite"
        )

    tagger = MeCab.Tagger()
    lemma_counts: Counter = Counter()

    for sentence in sentences:
        parsed = tagger.parse(sentence)
        if not parsed:
            continue
        for line in parsed.strip().split("\n"):
            if line == "EOS" or line == "":
                continue
            parts = line.split("\t")
            if len(parts) < 4:
                continue
            # UniDic format: surface\treading\treading2\tlemma\tpos\t...
            surface = parts[0]
            lemma = parts[3]
            pos = parts[4] if len(parts) > 4 else ""
            # Skip particles, auxiliaries, punctuation, symbols
            if any(skip in pos for skip in ("助詞", "助動詞", "補助記号", "記号", "空白")):
                continue
            # UniDic uses katakana lemmas for proper nouns; fall back to
            # surface form when the lemma is pure katakana and the surface
            # contains kanji (so we match against words.json kanji entries)
            token = lemma
            if token and all("\u30a0" <= c <= "\u30ff" for c in token):
                if any("\u4e00" <= c <= "\u9fff" for c in surface):
                    token = surface
            if token and len(token) >= 1:
                lemma_counts[token] += 1

    return lemma_counts


def _build_word_lookup(words_data: dict) -> dict[str, tuple[str, str]]:
    """Build lemma -> (word_id, primary_reading) from words.json."""
    lookup: dict[str, tuple[str, str]] = {}
    for w in words_data.get("words", []):
        wid = w.get("id", "")
        if not wid:
            continue
        kana_list = w.get("kana", []) or []
        kanji_list = w.get("kanji", []) or []
        primary_reading = kana_list[0].get("text", "") if kana_list else ""

        for k in kanji_list:
            text = k.get("text", "")
            if text and text not in lookup:
                lookup[text] = (wid, primary_reading)
        for k in kana_list:
            text = k.get("text", "")
            if text and text not in lookup:
                lookup[text] = (wid, primary_reading)
    return lookup


def build() -> None:
    if not KFTT_JSON.exists():
        raise FileNotFoundError(
            f"KFTT corpus not found: {KFTT_JSON}. "
            f"Run the build pipeline to generate it (just build)."
        )
    if not WORDS_JSON.exists():
        raise FileNotFoundError(f"Required: {WORDS_JSON}")

    print("[freq-wp]  loading KFTT corpus")
    kftt_data = json.loads(KFTT_JSON.read_text(encoding="utf-8"))
    sentences = [s["japanese"] for s in kftt_data.get("sentences", []) if s.get("japanese")]
    print(f"[freq-wp]  {len(sentences):,} sentences")

    print("[freq-wp]  tokenizing with MeCab...")
    lemma_counts = _tokenize_sentences(sentences)
    print(f"[freq-wp]  {len(lemma_counts):,} unique lemmas")

    print("[freq-wp]  loading words.json for vocabulary matching")
    words_data = json.loads(WORDS_JSON.read_text(encoding="utf-8"))
    word_lookup = _build_word_lookup(words_data)
    print(f"[freq-wp]  {len(word_lookup):,} known word surface forms")

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

    print(f"[freq-wp]  {len(matched):,} words matched against vocabulary")
    if matched:
        print(f"[freq-wp]  top-10: {', '.join(e['text'] for e in matched[:10])}")

    output = {
        "metadata": {
            "source": "Wikipedia Japanese via KFTT corpus, tokenized with MeCab/UniDic",
            "source_url": "https://www.phontron.com/kftt/",
            "license": "CC-BY-SA 3.0 (KFTT) / CC-BY-SA 4.0 (Wikipedia)",
            "generated": BUILD_DATE,
            "count": len(matched),
            "corpus": (
                "Word frequencies from MeCab tokenization of the KFTT corpus "
                f"(443,849 Wikipedia Kyoto article sentences, {sum(lemma_counts.values()):,} "
                "total tokens). Lemmatized to dictionary form via UniDic. "
                "Represents formal/encyclopedic written Japanese. Complements "
                "frequency-newspaper.json (kanji), frequency-subtitles.json "
                "(spoken media), and frequency-web.json (web text)."
            ),
            "kind": "word",
            "tokenizer": "MeCab with unidic-lite dictionary",
            "total_tokens": sum(lemma_counts.values()),
            "unique_lemmas": len(lemma_counts),
            "attribution": (
                "Frequency data derived from the KFTT corpus "
                "(https://www.phontron.com/kftt/, CC-BY-SA 3.0), which contains "
                "Japanese Wikipedia article sentences. Tokenized with MeCab "
                "(https://taku910.github.io/mecab/) using the UniDic dictionary."
            ),
            "field_notes": {
                "text": "Lemma (dictionary form) as determined by MeCab/UniDic.",
                "reading": "Primary kana reading from words.json.",
                "rank": "Rank by Wikipedia occurrence count. 1 = most frequent.",
                "count": "Raw occurrence count in the KFTT Wikipedia corpus.",
            },
        },
        "entries": matched,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"[freq-wp]  wrote {OUT.relative_to(REPO_ROOT)}")
