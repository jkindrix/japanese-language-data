"""Kanji data transform.

Phase 1 deliverable. Reads the KANJIDIC2 JSON from
``sources/jmdict-simplified/kanjidic2-en.json.tgz`` (ingested via
scriptin/jmdict-simplified) and transforms it into our schema.

Output: ``data/core/kanji.json`` conforming to ``schemas/kanji.schema.json``.

The upstream KANJIDIC2 JSON already has most of what we need. Our
transform adds:

    * ``jlpt_waller`` — current N1-N5 level from Jonathan Waller's JLPT
      lists (filled after the jlpt transform runs in Phase 2; Phase 1
      output will have this field as null).
    * ``radical_components`` — from KRADFILE (filled during the radicals
      transform; Phase 1 output will have this field as empty array).
    * Normalized ``meanings`` structure keyed by language.
    * Consistent ``field_notes`` in the metadata header.
    * Attribution for KANJIDIC2 per-field contributors (Halpern SKIP,
      App Four Corner, Spahn/Hadamitzky descriptors, Muller Korean, De
      Roo codes) — recorded in the metadata per the EDRDG License §8.

The transform preserves KANJIDIC2's native ordering (Unicode codepoint
within the filtered set) unless a specific ordering is requested.
"""

from __future__ import annotations


def build() -> None:
    raise NotImplementedError(
        "kanji.build() is scheduled for Phase 1. Inputs: kanjidic2-en.json.tgz "
        "from jmdict-simplified. Output: data/core/kanji.json."
    )
