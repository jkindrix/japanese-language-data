# Schema design

This document describes the design philosophy behind the JSON schemas in `schemas/`, the conventions every schema follows, and how schemas evolve over time. If you are contributing a new schema or modifying an existing one, read this first.

For architectural context, see `docs/architecture.md`. For the schemas themselves, see the `schemas/` directory.

---

## Philosophy

### JSON first, structured second

The dataset emits JSON because JSON is the lingua franca of structured data: every programming language can read it, every text editor can view it, every version control system can diff it. We do not emit Protocol Buffers, MessagePack, Parquet, or SQLite as primary outputs. JSON is the canonical form; other formats are downstream conversions.

### Explicit over implicit

Every field is declared. Empty arrays are preferred over missing keys. Arrays are preferred over null where either would work. A consumer should never need to know "if this key is missing, assume X" — the schema and the data make the structure explicit.

This follows the same principle as `scriptin/jmdict-simplified` upstream, which we ingest. It makes our transforms simpler (no inheritance-from-previous logic) and our consumers simpler (no default-handling logic).

### Human-readable field names

`strokeCount`, not `sc`. `romaji_reading`, not `rr`. The extra bytes on the wire are cheap; the cognitive cost of decoding cryptic abbreviations is not. Field names are snake_case by project convention.

### Inline documentation via `field_notes`

Every file emitted to `data/` carries a `metadata.field_notes` object that documents any field whose meaning is not self-evident from its name. A consumer can read the field notes alongside the data and not need to refer to external documentation.

Example:

```json
{
  "metadata": {
    "field_notes": {
      "jlpt_old": "Pre-2010 four-level JLPT system (1 = advanced, 4 = beginner). Not the current N1–N5 system, which is tracked separately in jlpt_waller.",
      "frequency": "Rank in frequency of use in newspapers, 1 = most common. Only populated for the ~2,500 most common kanji."
    }
  }
}
```

This is redundant with the JSON Schema files in `schemas/`, but the redundancy is deliberate: field notes travel with the data, schemas are a separate artifact.

### Schema versioning

Every schema declares a `schemaVersion` (in its `$id` or as a top-level field) that matches the repo's version at the time of last schema update. Breaking schema changes force a major version bump and are documented in `CHANGELOG.md`.

---

## Conventions every schema follows

### Top-level structure

Every data file has exactly these top-level keys:

```json
{
  "metadata": { ... },
  "<payload_key>": [ ... ] | { ... }
}
```

`metadata` is always present and always has at least these fields:

- `source` (string): The name of the upstream source
- `source_url` (string): URL of the upstream project
- `license` (string): SPDX identifier or canonical license name
- `source_version` (string): The pinned version we ingested
- `generated` (string, ISO 8601 date): The date this file was built
- `count` (integer): The number of entries in the payload
- `field_notes` (object): Inline field documentation (see above)

Additional metadata fields may be present for specific files (e.g., `editors_note`, `build_hash`, `warnings`).

The `payload_key` names the actual data:

- `kanji` for `kanji.json`
- `words` for `words.json`
- `sentences` for `sentences.json`
- etc.

The payload is usually an array. Lookup files (like `stroke-order-index.json`) may be an object keyed by identifier.

### Entry structure

Every entry in a payload has a stable identifier when possible:

- Words use the JMdict `id` field
- Kanji use the character itself as the primary key (it is unique within the set)
- Sentences use IDs in `{source}-{n}` format (e.g., `tatoeba-74694`, `kftt-1`)
- Grammar points use a project-assigned UUID or slug

Entries have a consistent shape within a file. Optional fields are either always present with empty values or always absent (we prefer always-present-with-empty-values, per the "explicit over implicit" principle).

### Cross-references

Cross-references use stable identifiers, not embedded full entries. For example, `kanji-to-words.json` references word IDs, not inline word objects:

```json
{
  "日": ["1234567", "2345678", "3456789"]
}
```

This keeps the cross-reference files small and prevents data duplication.

### Language and encoding

All text is UTF-8. All Japanese is written in the native script (no romaji transliteration in primary data — romaji fields exist separately where relevant).

Numeric fields use actual JSON numbers, not strings, unless the field is explicitly a coded identifier (e.g., a dictionary reference number that might have letters).

Dates use ISO 8601 format (`YYYY-MM-DD` or full timestamps with timezone).

---

## Per-schema overview

### `kana.schema.json`

Structure for `data/core/kana.json`. Each entry describes one kana character (hiragana or katakana) with its romaji, romanization system, type (base/dakuten/handakuten/yōon), stroke count, and notes on usage. This file is hand-curated and small (~200 entries).

### `kanji.schema.json`

Structure for `data/core/kanji.json`. Each entry is one kanji with readings, meanings, stroke count, grade, frequency, JLPT classifications (both old and new), radical components, dictionary references, query codes (SKIP, four-corner, Spahn/Hadamitzky, De Roo), and variant forms. Derived from KANJIDIC2.

### `word.schema.json`

Structure for `data/core/words.json`. Each entry is a JMdict word with kanji writings, kana writings (with applies-to relations), senses (with parts of speech, fields, dialects, misc tags, related/antonym cross-references, and translations), language-source notes for loanwords, and example sentence links. Derived from JMdict via jmdict-simplified.

### `name.schema.json`

Structure for `data/optional/names.json`. Simpler than word entries — proper nouns have kanji, kana readings, name type (person/place/company), and optional translation. Derived from JMnedict.

### `radical.schema.json`

Structure for `data/core/radicals.json`. Bidirectional: each radical has a number (Kangxi), stroke count, meaning, and the list of kanji containing it. Each kanji also appears in a lookup section with its component radicals. Derived from KRADFILE and RADKFILE.

### `sentence.schema.json`

Structure for `data/corpus/sentences.json`. Each entry is a Japanese–English sentence pair with Tatoeba IDs, text in both languages, optional audio URLs, curation flag (editor-selected vs. full corpus), and contributor attribution.

### `pitch-accent.schema.json`

Structure for `data/enrichment/pitch-accent.json`. Each entry maps a word (in kanji + kana form) to its pitch accent mora positions, with source attribution. Derived from Kanjium.

### `frequency.schema.json`

Generic structure for frequency-ranking files. Used by `frequency-newspaper.json` (KANJIDIC2 kanji), `frequency-subtitles.json` (OpenSubtitles spoken media), and `frequency-corpus.json` (Tatoeba-derived). Each entry has the lookup key (word or kanji), the rank (1 = most common), and the corpus identifier.

### `jlpt.schema.json`

Structure for `data/enrichment/jlpt-classifications.json`. Each entry has the text, kind (kanji/vocab/grammar), level (N5–N1), and source (currently always "waller-tanos").

### `stroke-order.schema.json`

Structure for `data/enrichment/stroke-order-index.json`. Maps each character to its SVG filename (or null if missing) and total stroke count. The actual SVG files live in `data/enrichment/stroke-order/` as separate files and are not validated by the schema (they are SVG, not JSON).

### `grammar.schema.json`

Structure for `data/grammar/grammar.json`. Each entry is an original-curation grammar point with: ID, pattern (e.g., "～ない"), level (N5–N1), meaning in English, formation rule, formality register, related patterns, example sentences (linked to Tatoeba IDs where possible), review status, and source references. This schema will see the most iteration during Phase 3.

### `cross-refs.schema.json`

Structure for files in `data/cross-refs/`. All cross-reference files follow the same pattern: an object mapping a lookup key to an array of target identifiers.

---

## Adding a new schema

1. **Write the schema** as a file in `schemas/<name>.schema.json`, following the conventions above.
2. **Include it in tests** — add a test case in `tests/test_schemas.py` that loads the schema and verifies it is itself a valid JSON Schema.
3. **Document it** — add a section to this file describing what it represents.
4. **Use it** — add validation calls in `build/validate.py` for any file expected to conform to the new schema.
5. **Bump the minor version** — new schemas are additive and warrant a minor version bump.

## Modifying an existing schema

Changes are classified as:

- **Additive** (new optional field, new enum value, relaxed constraints): safe; bump minor version.
- **Documentation-only** (descriptions, titles): no version bump needed, but commit with a `docs:` prefix.
- **Breaking** (removing a field, tightening constraints, changing types): requires major version bump and a documented migration path in the changelog.

Never change a schema without also updating every transform module and every data file that it validates.

---

## Why not Pydantic / TypedDict / ...?

JSON Schema is the lingua franca for schema specification — every language has a validator, every IDE can use it for completion, every contributor can read it without learning a new DSL.

We could additionally emit Python Pydantic models, TypeScript interfaces, or other language-native types for downstream consumers who want them. That is a good Phase 4 addition (schema-to-language type generation). For now, JSON Schema is sufficient and universal.

---

## What's validated and what isn't

- **Validated**: All files in `data/` whose format is JSON. Every build stage runs validation before committing outputs.
- **Not validated by schemas**: SVG files in `data/enrichment/stroke-order/` (they are SVG, not JSON; their XML is validated separately during the transform).
- **Not validated at all**: Upstream source files in `sources/`. These are consumed as-is and any format error is surfaced as a transform error.

Validation is not a substitute for tests. Tests verify that transforms produce the correct output; validation verifies that the output matches the declared shape. Both layers are needed.
