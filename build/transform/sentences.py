"""Example sentences transform.

Phase 1 deliverable. Extracts example sentences from the jmdict-examples
variant (which embeds Tatoeba sentences already linked to specific
JMdict senses) and writes them as a standalone sentence corpus file.

Input: ``sources/jmdict-simplified/jmdict-examples-eng.json.tgz``
    (same file consumed by words.build — cached extraction is fine)

Output: ``data/corpus/sentences.json`` conforming to
``schemas/sentence.schema.json``.

Each entry preserves the Tatoeba sentence ID so consumers can look
sentences up at https://tatoeba.org/en/sentences/show/<id> for audio,
alternative translations, and community discussion.

The sentences in this file are the **editor-curated** subset, marked
with ``curated: true``. They have been hand-selected by JMdict editors
for quality and relevance. Phase 2 may optionally add a second file,
``data/corpus/sentences-unfiltered.json``, containing the full Tatoeba
Japanese corpus (~200k+ sentences, variable quality) with
``curated: false`` for consumers needing broader coverage.

The word → sentence cross-reference (``data/cross-refs/word-to-sentences.json``)
is generated separately by ``cross_links.build``, which consumes both
this file and ``data/core/words.json``.
"""

from __future__ import annotations


def build() -> None:
    raise NotImplementedError(
        "sentences.build() is scheduled for Phase 1. Inputs: "
        "jmdict-examples-eng.json.tgz. Output: data/corpus/sentences.json."
    )
