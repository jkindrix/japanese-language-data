"""Word (JMdict) data transform.

Phase 1 deliverable. Reads the JMdict examples variant from
``sources/jmdict-simplified/jmdict-examples-eng.json.tgz`` (ingested via
scriptin/jmdict-simplified) and transforms it into our schema.

Output: ``data/core/words.json`` conforming to ``schemas/word.schema.json``.

The examples variant is chosen over the bare English variant because it
includes Tatoeba example sentences pre-linked to specific senses. This
saves a large amount of Phase 2 cross-linking work: the linkage from
word → example sentence is already present in the upstream data.

The transform preserves every JMdict field documented in the
jmdict-simplified TypeScript type definitions (kanji writings, kana
writings with applies-to relations, senses with parts of speech, fields,
dialects, misc, language source, glosses, related and antonym cross-
references) and augments each entry with:

    * ``jlpt_waller`` — filled in Phase 2 after the jlpt transform runs.
      Phase 1 output will have this as null.
    * ``frequency_media`` — filled in Phase 2 after the frequency
      transform runs. Phase 1 output will have this as null.

Example sentences embedded in the upstream file are extracted and also
written to ``data/corpus/sentences.json`` by the sentences transform.
The word-to-sentence cross-reference is written by ``cross_links.build``.
"""

from __future__ import annotations


def build() -> None:
    raise NotImplementedError(
        "words.build() is scheduled for Phase 1. Inputs: "
        "jmdict-examples-eng.json.tgz from jmdict-simplified. Output: "
        "data/core/words.json."
    )
