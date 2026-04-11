"""Stroke order transform.

Phase 2 deliverable. Extracts the KanjiVG ZIP archive and places each
per-character SVG file in ``data/enrichment/stroke-order/``, filtering
to CJK Unified Ideograph code points (and optionally Extensions A/B in
later phases).

Input: ``sources/kanjivg/kanjivg-main.zip``

Outputs:
    * ``data/enrichment/stroke-order/<char>.svg`` — one SVG per kanji.
      Files are named with the kanji character directly (preserving the
      original zero-padded hex filename is possible as an option if
      UTF-8 filenames are problematic for any consumer).
    * ``data/enrichment/stroke-order-index.json`` — lookup mapping each
      kanji character to its SVG filename and stroke count, conforming
      to ``schemas/stroke-order.schema.json``.

KanjiVG contains some characters outside the CJK Unified Ideograph
range — hiragana, katakana, punctuation, variant forms. Phase 2 includes
CJK Unified Ideographs (U+4E00–U+9FFF) and kanji for kana variants. A
later phase can extend to Extensions A, B, and beyond if needed.

Characters that appear in ``data/core/kanji.json`` but have no SVG in
KanjiVG are recorded in the index with ``svg: null`` so consumers can
distinguish "no stroke order available" from "bug in data".
"""

from __future__ import annotations


def build() -> None:
    raise NotImplementedError(
        "stroke_order.build() is scheduled for Phase 2. Input: "
        "kanjivg-main.zip. Outputs: data/enrichment/stroke-order/*.svg "
        "and data/enrichment/stroke-order-index.json."
    )
