"""JMnedict names transform.

Phase 1 deliverable, but gated behind the ``--with-names`` build flag.
Output is gitignored (``data/optional/names.json``) because the file is
large (~150 MB uncompressed) and only useful to specific consumers
(name lookup, NLP pipelines, OCR disambiguation).

Reads ``sources/jmdict-simplified/jmnedict-all.json.tgz`` (ingested via
scriptin/jmdict-simplified) and transforms it into our schema.

Output: ``data/optional/names.json`` conforming to
``schemas/name.schema.json``.

Unlike words, proper names receive minimal augmentation — they are
reference data, not learning content. The transform preserves the
JMnedict structure (kanji writings, kana readings with applies-to
relations, translations with name-type tags) and adds only the standard
metadata header with attribution.
"""

from __future__ import annotations


def build() -> None:
    raise NotImplementedError(
        "names.build() is scheduled for Phase 1 (optional build target, "
        "requires --with-names flag). Inputs: jmnedict-all.json.tgz. "
        "Output: data/optional/names.json (gitignored)."
    )
