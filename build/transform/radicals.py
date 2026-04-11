"""Radicals (KRADFILE + RADKFILE) transform.

Phase 1 deliverable. Reads both KRADFILE (kanji → component radicals)
and RADKFILE (radical → kanji containing it) from the
jmdict-simplified JSON releases and combines them into a single
bidirectional radical dataset.

Inputs:
    * ``sources/jmdict-simplified/kradfile.json.tgz``
    * ``sources/jmdict-simplified/radkfile.json.tgz``

Output: ``data/core/radicals.json`` conforming to
``schemas/radical.schema.json``.

The combined structure has two top-level arrays/objects:

    * ``radicals`` — list of radical entries with the radical character,
      stroke count, classical (Kangxi) number, meanings, and the kanji
      that contain it (from RADKFILE).
    * ``kanji_to_radicals`` — lookup from each kanji to its component
      radicals (from KRADFILE).

These two views are redundant (derivable from each other) but both are
materialized for O(1) lookup in either direction, saving consumers from
having to compute the inverse at read time.

Phase 2 cross-links will additionally populate ``radical_components`` in
``data/core/kanji.json`` by joining this data into the kanji entries.
"""

from __future__ import annotations


def build() -> None:
    raise NotImplementedError(
        "radicals.build() is scheduled for Phase 1. Inputs: "
        "kradfile.json.tgz and radkfile.json.tgz from jmdict-simplified. "
        "Output: data/core/radicals.json."
    )
