"""Pitch accent transform.

Phase 2 deliverable. Parses the Kanjium ``accents.txt`` TSV file and
produces a structured pitch accent JSON file.

Input: ``sources/kanjium/accents.txt``

Output: ``data/enrichment/pitch-accent.json`` conforming to
``schemas/pitch-accent.schema.json``.

The Kanjium format is simple tab-separated values:

    <word>\\t<kana_reading>\\t<mora_positions>

where mora_positions is a comma-separated list of integers. A value of
0 means heiban (flat, no drop); a value of N means the accent falls
after the Nth mora. Multiple values indicate multiple acceptable
patterns.

The transform:
    * Reads each line, skipping blanks and comments
    * Parses mora position lists into integer arrays
    * Emits structured entries per the pitch accent schema
    * Records the upstream source commit hash in metadata for
      reproducibility

Known limitation: the Kanjium dataset is roughly frozen at 2022, so
vocabulary added after that year lacks pitch accent data. The metadata
``coverage_date`` field records this limitation explicitly. A Phase 4
candidate is scraping Wiktionary or OJAD to fill the post-2022 gap.
"""

from __future__ import annotations


def build() -> None:
    raise NotImplementedError(
        "pitch.build() is scheduled for Phase 2. Input: "
        "sources/kanjium/accents.txt. Output: "
        "data/enrichment/pitch-accent.json."
    )
