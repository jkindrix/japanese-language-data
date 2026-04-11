"""Kana data transform.

Phase 1 deliverable. Unlike the other transforms, this one is hand-
curated rather than derived from an upstream source: there are only
~200 kana characters (46 hiragana + 46 katakana + dakuten/handakuten/
yōon variants) and manually-written data is both more accurate and
more pedagogically useful than any scraped source.

Output: ``data/core/kana.json`` conforming to ``schemas/kana.schema.json``.

The hand-written source data will live in this module (or a separate
``sources/kana-curated.json`` if it grows large enough to warrant
external storage). For Phase 1, the plan is to include at minimum:

    * 46 basic hiragana with romaji (Hepburn + Kunrei alternatives)
    * 46 basic katakana matched to hiragana
    * Dakuten forms (20 hiragana + 20 katakana)
    * Handakuten forms (5 hiragana + 5 katakana)
    * Yōon combinations (36 hiragana + 36 katakana)
    * Sokuon (っ / ッ)
    * The archaic kana ゐ, ゑ, ヰ, ヱ with historical notes
    * Long-vowel mark (ー) with usage notes

Each entry carries stroke count, Unicode codepoint, type classification,
and usage notes as described in the schema.
"""

from __future__ import annotations


def build() -> None:
    raise NotImplementedError(
        "kana.build() is scheduled for Phase 1. Hand-curated ~200-entry "
        "dataset; no upstream source to fetch."
    )
