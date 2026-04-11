"""Grammar dataset transform.

Phase 3 deliverable — the project's most significant original
contribution. No authoritative open structured Japanese grammar dataset
exists; this module produces one.

Output: ``data/grammar/grammar.json`` conforming to
``schemas/grammar.schema.json``.

Sources consulted during curation (not copied from):

    * Tae Kim's Guide to Japanese (CC-licensed; used for cross-referencing
      pattern explanations and verifying formation rules)
    * Jonathan Waller's JLPT grammar lists (CC-BY; used as seed for
      level classification and pattern coverage)
    * JMdict ``exp`` (expression) entries (EDRDG / CC-BY-SA 4.0; used as
      the source of ~10,000 lexicalized grammar patterns)
    * Wiktionary Japanese entries (CC-BY-SA; cross-referenced for specific
      patterns)
    * Tatoeba sentences (CC-BY 2.0 FR; used as attested examples linked
      by sentence ID, not copied)

Proprietary references consulted for accuracy checks only, never copied:

    * Handbook of Japanese Grammar Patterns by Seiichi Makino and Michio
      Tsutsui (structure and scope reference only)
    * Dictionary of Basic/Intermediate/Advanced Japanese Grammar
      (same; reference only)
    * Native-speaker reviewers (when available) for final validation

The transform is largely manual: human-written grammar entries are
maintained in ``sources/grammar-curated/`` as YAML or Markdown files
that are easier to author and review than raw JSON. This module reads
those curated files and emits structured JSON per the schema.

Every entry carries:
    * A project-assigned stable ID (slug)
    * Pattern notation
    * Community-consensus JLPT level (with Waller as the source)
    * English meaning and detailed explanation (written in our own words)
    * Formation rule
    * Formality register
    * Cross-references to related patterns
    * Example sentences (linked to Tatoeba IDs where possible,
      original sentences marked as such)
    * Review status: draft → community_reviewed → native_speaker_reviewed
    * Explicit source list for the specific entry

Phase 3 targets ~140 entries for N5 and N4 (complete) at v0.3.0. N3, N2,
and N1 are filled in progressively across subsequent patch releases.

The conjugations and expressions sibling files (``conjugations.json``
and ``expressions.json``) are produced by other Phase 3 modules which
will be added when the grammar phase begins.
"""

from __future__ import annotations


def build() -> None:
    raise NotImplementedError(
        "grammar.build() is scheduled for Phase 3. Input: "
        "sources/grammar-curated/*.yaml (hand-authored). Output: "
        "data/grammar/grammar.json."
    )
