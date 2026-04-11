"""JLPT classifications transform.

Phase 2 deliverable. Fetches Jonathan Waller's JLPT vocabulary, kanji,
and grammar lists from http://www.tanos.co.uk/jlpt/ and produces a
single structured classifications file.

Input: web pages at tanos.co.uk (scraped at Phase 2 build time; the
source list in ``build/fetch.py`` is extended in Phase 2 to include
the relevant URLs).

Output: ``data/enrichment/jlpt-classifications.json`` conforming to
``schemas/jlpt.schema.json``.

Each entry has the text, kind (kanji/vocab/grammar), level (N5–N1), and
source attribution. The metadata header includes an explicit disclaimer
that these classifications are community-reverse-engineered from past
test questions and are not JLPT-official; JLPT stopped publishing
official word lists in 2010.

After this transform runs, the kanji and word transforms (Phase 1) can
be re-run to populate their ``jlpt_waller`` fields by joining against
this classification file. Alternatively, the cross_links stage performs
the join in-memory at build time.

Grammar points from Waller's lists become the **seed** for the Phase 3
original grammar dataset — they are not themselves the grammar dataset,
which is written from scratch with proper schema, provenance, and
native-speaker review.
"""

from __future__ import annotations


def build() -> None:
    raise NotImplementedError(
        "jlpt.build() is scheduled for Phase 2. Input: tanos.co.uk "
        "scraped pages. Output: data/enrichment/jlpt-classifications.json."
    )
