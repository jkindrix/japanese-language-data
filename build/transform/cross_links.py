"""Cross-reference generation.

Phase 2 deliverable. Runs after every per-domain transform has completed
and every output file exists in ``data/``. Reads those files and emits
the cross-reference indices in ``data/cross-refs/``.

Generated files:

    * ``data/cross-refs/kanji-to-words.json``
        For each kanji character, the list of word IDs whose entries
        contain that character in any kanji writing. Enables "show me
        all the words using this kanji" in O(1).

    * ``data/cross-refs/word-to-kanji.json``
        Inverse: each word ID → list of kanji characters it contains.
        Derivable from ``words.json`` but materialized for consumer
        convenience.

    * ``data/cross-refs/word-to-sentences.json``
        Each word ID → list of Tatoeba sentence IDs that illustrate it.
        Initially populated from the example references embedded in
        ``jmdict-examples-eng`` (the editor-curated subset).

    * ``data/cross-refs/kanji-to-radicals.json``
        Each kanji → its component radicals, from KRADFILE.

All cross-reference files conform to ``schemas/cross-refs.schema.json``.

This stage is idempotent: re-running it produces identical output given
identical inputs.

Future cross-references to add in later phases:

    * ``grammar-to-sentences.json`` — grammar pattern → example sentences
    * ``word-to-grammar.json`` — word → grammar patterns that affect it
    * ``reading-to-words.json`` — kana reading → words with that reading
"""

from __future__ import annotations


def build() -> None:
    raise NotImplementedError(
        "cross_links.build() is scheduled for Phase 2. Depends on every "
        "core and enrichment transform being complete first. Outputs: "
        "four files in data/cross-refs/."
    )
