"""Frequency transform.

Phase 2 deliverable. Produces two distinct frequency files:

    * ``data/enrichment/frequency-newspaper.json`` — derived from the
      ``freq`` field in KANJIDIC2 entries (newspaper corpus rank, top
      ~2,500 kanji only).
    * ``data/enrichment/frequency-modern.json`` — derived from the JPDB
      frequency list (https://github.com/MarvNC/jpdb-freq-list), which
      ranks words by occurrence in light novels, visual novels, anime,
      and drama.

Both files conform to ``schemas/frequency.schema.json`` with different
``kind`` metadata values (kanji vs word) and different ``corpus``
descriptions.

The newspaper frequency is extracted during the kanji transform stage
but written by this module for consistency. The modern frequency
requires fetching the latest JPDB release from MarvNC's repository,
which is added to ``build/fetch.py`` in Phase 2 (it is not in Phase 1's
source list).
"""

from __future__ import annotations


def build() -> None:
    raise NotImplementedError(
        "frequency.build() is scheduled for Phase 2. Outputs: "
        "data/enrichment/frequency-newspaper.json (from KANJIDIC2) and "
        "data/enrichment/frequency-modern.json (from JPDB)."
    )
