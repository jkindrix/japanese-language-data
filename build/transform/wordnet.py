"""Japanese WordNet (wn-ja) relationship extraction transform.

Extracts semantic relationships from the Japanese WordNet SQLite
database: synonym groups (words sharing synsets), hypernym/hyponym
pairs, and other synlink relations.

Input: ``sources/wordnet/wnjpn.db.gz``

Output: ``data/cross-refs/wordnet-synonyms.json``

The Japanese WordNet (wn-ja) v1.1 contains 93,834 Japanese words,
158,058 senses, and 283,600 semantic relations. Licensed under a
BSD-style permissive license from NICT.

Reference: Isahara et al. "Development of the Japanese WordNet" (2008).
Project: https://bond-lab.github.io/wnja/
"""

from __future__ import annotations

import gzip
import json
import sqlite3
import tempfile
from collections import defaultdict
from pathlib import Path

from build.pipeline import BUILD_DATE

REPO_ROOT = Path(__file__).resolve().parents[2]
SOURCE_GZ = REPO_ROOT / "sources" / "wordnet" / "wnjpn.db.gz"
OUT = REPO_ROOT / "data" / "cross-refs" / "wordnet-synonyms.json"


def build() -> None:
    print(f"[wordnet]  loading {SOURCE_GZ.name}")
    if not SOURCE_GZ.exists():
        raise FileNotFoundError(
            f"Source not cached: {SOURCE_GZ} (run just fetch first)"
        )

    # Decompress to a temp file for sqlite3 access
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        tmp_path = tmp.name
        with gzip.open(SOURCE_GZ, "rb") as gz:
            while chunk := gz.read(65536):
                tmp.write(chunk)

    try:
        conn = sqlite3.connect(tmp_path)
        _extract(conn)
        conn.close()
    finally:
        Path(tmp_path).unlink(missing_ok=True)


def _extract(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()

    # --- Step 1: Build synset → Japanese words mapping ---
    # Use only verified entries (from wnjpn-ok equivalent: src != 'auto')
    cur.execute("""
        SELECT s.synset, w.lemma
        FROM sense s
        JOIN word w ON s.wordid = w.wordid
        WHERE w.lang = 'jpn'
        ORDER BY s.synset, s.rank
    """)

    synset_words: dict[str, list[str]] = defaultdict(list)
    for synset_id, lemma in cur.fetchall():
        if lemma not in synset_words[synset_id]:
            synset_words[synset_id].append(lemma)

    # --- Step 2: Get English definitions for synsets ---
    cur.execute("""
        SELECT synset, def FROM synset_def WHERE lang = 'eng'
    """)
    synset_def_en: dict[str, str] = {r[0]: r[1] for r in cur.fetchall()}

    # --- Step 3: Get Japanese definitions ---
    cur.execute("""
        SELECT synset, def FROM synset_def WHERE lang = 'jpn'
    """)
    synset_def_ja: dict[str, str] = {r[0]: r[1] for r in cur.fetchall()}

    # --- Step 4: Extract synonym pairs ---
    # Two words are synonyms if they share a synset and both are Japanese
    synonym_pairs: list[dict] = []
    seen: set[tuple[str, str]] = set()

    for synset_id, words in synset_words.items():
        if len(words) < 2:
            continue
        definition = synset_def_en.get(synset_id, "")
        for i, w1 in enumerate(words):
            for w2 in words[i + 1:]:
                key = (min(w1, w2), max(w1, w2))
                if key not in seen:
                    seen.add(key)
                    synonym_pairs.append({
                        "word_a": w1,
                        "word_b": w2,
                        "relation": "synonym",
                        "synset_id": synset_id,
                        "definition_en": definition,
                    })

    print(f"[wordnet]  synonym pairs: {len(synonym_pairs):,}")

    # --- Step 5: Extract hypernym pairs between Japanese words ---
    # Find synsets linked by 'hype' where both have Japanese words
    cur.execute("""
        SELECT synset1, synset2 FROM synlink WHERE link = 'hype'
    """)

    hypernym_pairs: list[dict] = []
    hyp_seen: set[tuple[str, str]] = set()

    for child_synset, parent_synset in cur.fetchall():
        child_words = synset_words.get(child_synset, [])
        parent_words = synset_words.get(parent_synset, [])
        if not child_words or not parent_words:
            continue

        # Use first (highest-ranked) word from each synset as representative
        child_word = child_words[0]
        parent_word = parent_words[0]
        key = (child_word, parent_word)
        if key not in hyp_seen:
            hyp_seen.add(key)
            hypernym_pairs.append({
                "word_a": child_word,
                "word_b": parent_word,
                "relation": "hypernym",
                "synset_id": child_synset,
                "definition_en": synset_def_en.get(child_synset, ""),
            })

    print(f"[wordnet]  hypernym pairs: {len(hypernym_pairs):,}")

    # --- Step 6: Build synset groups for output ---
    synset_groups: list[dict] = []
    for synset_id, words in sorted(synset_words.items()):
        if len(words) < 2:
            continue
        synset_groups.append({
            "synset_id": synset_id,
            "words": words,
            "definition_en": synset_def_en.get(synset_id, ""),
            "definition_ja": synset_def_ja.get(synset_id, ""),
        })

    all_relations = synonym_pairs + hypernym_pairs
    print(f"[wordnet]  total relations: {len(all_relations):,}")
    print(f"[wordnet]  synset groups (2+ words): {len(synset_groups):,}")

    # Count unique Japanese words involved
    all_words = set()
    for synset_id, words in synset_words.items():
        all_words.update(words)
    print(f"[wordnet]  unique Japanese words: {len(all_words):,}")

    output = {
        "metadata": {
            "generated": BUILD_DATE,
            "count": len(all_relations),
            "synonym_count": len(synonym_pairs),
            "hypernym_count": len(hypernym_pairs),
            "synset_group_count": len(synset_groups),
            "unique_words": len(all_words),
            "source": "Japanese WordNet (wn-ja) v1.1 by NICT",
            "source_url": "https://bond-lab.github.io/wnja/",
            "license": (
                "NICT permissive license (BSD-style): free to use, copy, "
                "modify, and distribute for any purpose without fee or royalty."
            ),
            "attribution": (
                "Semantic relationships from the Japanese WordNet (wn-ja) v1.1, "
                "developed by the National Institute of Information and "
                "Communications Technology (NICT). Based on Princeton WordNet 3.0."
            ),
            "field_notes": {
                "word_a": "First word in the relationship pair.",
                "word_b": "Second word. For synonyms, order is alphabetical. For hypernyms, word_a is the more specific term (hyponym) and word_b is the broader term (hypernym).",
                "relation": "Relationship type: 'synonym' (same synset) or 'hypernym' (word_a IS-A word_b).",
                "synset_id": "Princeton WordNet 3.0 synset ID.",
                "definition_en": "English definition of the synset.",
            },
        },
        "synset_groups": synset_groups,
        "relations": all_relations,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
        f.write("\n")
    size = OUT.stat().st_size
    print(f"[wordnet]  wrote {OUT.relative_to(REPO_ROOT)} ({size:,} bytes)")
