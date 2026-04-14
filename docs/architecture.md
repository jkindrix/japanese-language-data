# Architecture

This document describes how the Japanese Language Data project is organized: the design principles, the directory layout and what lives where, the build pipeline from upstream fetch to validated output, and the versioning strategy.

If you are contributing to the project, reading this document is the prerequisite for proposing any structural change. If you are consuming the dataset as data, you can skim the "Directory layout" and "Cross-references" sections and skip the rest.

---

## Design principles

The project is organized around six principles, listed in priority order. When two principles come into tension, the higher-listed one wins.

### 1. Reproducibility over convenience

Every byte of built data must be reproducible by running the pipeline from a clean clone. There is no manual step anywhere in the build. If a human hand touched a file in `data/`, either that file is explicitly human-curated content (grammar, kana, learner-facing explanations) or it is a bug. Source downloads are cached and SHA256-verified; upstream versions are pinned in `manifest.json`. If an upstream source changes, we bump the pin deliberately, rebuild, review the diff, and commit — in that order.

### 2. Honest provenance over polished presentation

Every data file carries metadata identifying its source(s), versions, build date, and (where applicable) the confidence or curation status of its entries. When a fact came from community data, we say so. When an entry is inferred or auto-generated, we say so. When we do not know something, we say so rather than fill in plausible-sounding guesses. A user should never be confused about where any given datum came from.

### 3. Composition over monolith

The dataset is many small, purpose-specific JSON files rather than one mega-file. A consumer needing only kanji reads `data/core/kanji.json` and never touches the grammar file. A consumer building a reading assistant reads the cross-refs and sentences without loading pitch accent. This principle shapes the directory layout, the schema design, and the cross-linking strategy.

### 4. Schema-enforced correctness

Every output file validates against an explicit JSON Schema in `schemas/`. A build that produces schema-invalid output fails loudly. Schemas are versioned; breaking schema changes force a major version bump; additive schema changes force a minor version bump. This is how we ensure the data remains stable enough to build tools on top of it over years.

### 5. Cross-linking as first-class data

The value-add of this project over individual upstream sources is the cross-references between them. Kanji → words that use it. Word → kanji it contains. Word → example sentences from Tatoeba. Word → grammar pattern that governs it. Kanji → component radicals. Grammar pattern → example sentences illustrating it. Every cross-link is generated deterministically during the build and stored in `data/cross-refs/` as a first-class data product, not as a side-effect of some other file.

### 6. Upstream contribution as ongoing obligation

When this project discovers errors, gaps, or improvements in upstream sources, those findings are logged in `docs/upstream-issues.md` and filed upstream at the end of each build phase. We are downstream consumers of the open Japanese data ecosystem, and we pay rent by contributing fixes back. This is an ethical principle and an operational one: the better the upstream sources are, the better our dataset is.

---

## Directory layout

```
japanese-language-data/
├── README.md                  Project overview and quick start
├── LICENSE                    CC-BY-SA 4.0 + upstream license obligations
├── ATTRIBUTION.md             Per-source attribution wording
├── CHANGELOG.md               Version history with upstream pins
├── CODE_OF_CONDUCT.md         Community code of conduct
├── manifest.json              Current repo version, source pins, build date, counts
│
├── docs/                      Documentation of every non-obvious thing
│   ├── architecture.md        This file
│   ├── build.md               How to rebuild from scratch
│   ├── call-for-reviewers.md  Recruitment pitch for grammar reviewers
│   ├── contributing.md        How to contribute
│   ├── cookbook.md             Code examples (Python, JS, jq)
│   ├── downstream.md          Guide for downstream consumers
│   ├── gaps.md                What we don't cover, and why
│   ├── grammar-review.md      Grammar reviewer workflow
│   ├── grammar-review-checklist.md  Per-entry review checklist
│   ├── phase4-candidates.md   Deferred data domains under consideration
│   ├── release.md             Release process and drift prevention
│   ├── schema.md              Schema design philosophy
│   ├── sources.md             Every upstream source in detail
│   └── upstream-issues.md     Log of errors/gaps to file upstream
│
├── schemas/                   JSON Schema files (Draft 2020-12)
│   ├── aozora.schema.json
│   ├── ateji.schema.json
│   ├── conjugations.schema.json
│   ├── counter-words.schema.json
│   ├── cross-refs.schema.json
│   ├── expressions.schema.json
│   ├── frequency.schema.json
│   ├── furigana.schema.json
│   ├── grammar.schema.json
│   ├── jlpt.schema.json
│   ├── jukugo.schema.json
│   ├── kana.schema.json
│   ├── kanji.schema.json
│   ├── manifest.schema.json
│   ├── name.schema.json
│   ├── pitch-accent.schema.json
│   ├── radical.schema.json
│   ├── sentence-difficulty.schema.json
│   ├── sentence.schema.json
│   ├── stroke-order.schema.json
│   ├── word-relations.schema.json
│   ├── wordnet.schema.json
│   └── word.schema.json
│
├── build/                     Reproducible pipeline source code
│   ├── __init__.py
│   ├── bump_release.py        Version bump automation
│   ├── check_upstream.py      Upstream source freshness checker
│   ├── constants.py           Shared path constants
│   ├── export_anki.py         Anki .apkg deck export
│   ├── export_sqlite.py       SQLite database export
│   ├── export_yomitan.py      Yomitan dictionary export
│   ├── fetch.py               Download + cache upstream sources
│   ├── pipeline.py            Orchestrate the full build
│   ├── utils.py               Shared transform utilities
│   ├── validate.py            Schema validation of every output
│   ├── stats.py               Coverage and count reporting
│   ├── requirements.txt       Pinned Python dependencies
│   └── transform/             Per-domain transformation modules
│       ├── __init__.py
│       ├── aozora.py
│       ├── ateji.py
│       ├── common_voice.py
│       ├── conjugations.py
│       ├── counters.py
│       ├── cross_links.py
│       ├── expressions.py
│       ├── frequency.py
│       ├── frequency_corpus.py
│       ├── frequency_jesc.py
│       ├── frequency_subtitles.py
│       ├── frequency_web.py
│       ├── frequency_wikipedia.py
│       ├── furigana.py
│       ├── grammar.py
│       ├── jesc.py
│       ├── jlpt.py
│       ├── jukugo.py
│       ├── kana.py
│       ├── kanji.py
│       ├── kftt.py
│       ├── names.py
│       ├── pitch.py
│       ├── radicals.py
│       ├── sentence_difficulty.py
│       ├── sentences.py
│       ├── sentences_full.py
│       ├── stroke_order.py
│       ├── wikimatrix.py
│       ├── wordnet.py
│       ├── word_relations.py
│       └── words.py
│
├── sources/                   (gitignored) Cached upstream downloads
│                              Reproducible from manifest.json pins
│
├── data/                      The actual committed dataset
│   ├── core/                  Foundation layer
│   │   ├── kana.json
│   │   ├── kanji.json
│   │   ├── kanji-jinmeiyo.json
│   │   ├── kanji-joyo.json
│   │   ├── radicals.json
│   │   ├── words.json
│   │   ├── words-full.json
│   │   └── (names.json in data/optional/, not here)
│   ├── enrichment/            Derived or augmenting metadata
│   │   ├── stroke-order/          Per-character SVG files from KanjiVG
│   │   ├── stroke-order-index.json
│   │   ├── ateji.json
│   │   ├── counter-words.json
│   │   ├── frequency-corpus.json
│   │   ├── frequency-jesc.json
│   │   ├── frequency-newspaper.json
│   │   ├── frequency-subtitles.json
│   │   ├── frequency-tatoeba.json
│   │   ├── frequency-web.json
│   │   ├── frequency-wikipedia.json
│   │   ├── furigana.json
│   │   ├── jlpt-classifications.json
│   │   ├── jukugo-compounds.json
│   │   ├── pitch-accent.json
│   │   ├── pitch-accent-wiktionary.json
│   │   └── sentence-difficulty.json
│   ├── corpus/                Example data
│   │   ├── sentences.json         Tatoeba JA–EN pairs
│   │   ├── sentences-jesc.json
│   │   ├── sentences-kftt.json
│   │   ├── sentences-tatoeba-full.json
│   │   └── sentences-wikimatrix.json
│   ├── grammar/               Original curation (Phase 3)
│   │   ├── grammar.json
│   │   ├── conjugations.json
│   │   └── expressions.json
│   ├── cross-refs/            Cross-reference indices
│   │   ├── grammar-to-sentences.json
│   │   ├── grammar-to-words.json
│   │   ├── kanji-to-radicals.json
│   │   ├── kanji-to-sentences.json
│   │   ├── kanji-to-sentences-full.json
│   │   ├── kanji-to-words.json
│   │   ├── kanji-to-words-full.json
│   │   ├── radical-to-kanji.json
│   │   ├── reading-to-words.json
│   │   ├── reading-to-words-full.json
│   │   ├── sentence-to-words.json
│   │   ├── word-relations.json
│   │   ├── word-to-grammar.json
│   │   ├── word-to-kanji.json
│   │   ├── word-to-kanji-full.json
│   │   ├── word-to-sentences.json
│   │   └── wordnet-synonyms.json
│   ├── optional/              (gitignored) Opt-in large data
│   │   └── names.json         JMnedict, ~720k entries
│   └── phase4/                Phase 4 pipeline outputs
│       └── aozora-corpus.json Curated Aozora Bunko literary corpus
│
├── dist/                      Exported distribution formats
│   ├── japanese-language-data.apkg    Anki flashcard deck
│   ├── japanese-language-data.sqlite  SQLite database
│   └── japanese-language-data.zip     Bundled ZIP archive
│
├── tests/                     Pytest test suite (520 tests)
│   ├── __init__.py
│   ├── test_data_integrity.py   Regression tests and data invariants
│   ├── test_docs.py             Documentation and release metadata
│   ├── test_infrastructure.py   Pipeline DAG, fetch, validation tests
│   ├── test_phase4_transforms.py  Phase 4 transform tests
│   ├── test_schema_negative.py  Negative validation tests
│   ├── test_schemas.py          Schema self-validity tests
│   └── test_transform_units.py  Transform function unit tests
│
├── grammar-curated/           Hand-curated grammar input files
│   ├── n1.json                N1 grammar points (139 entries)
│   ├── n2.json                N2 grammar points (150 entries)
│   ├── n3.json                N3 grammar points (139 entries)
│   ├── n4.json                N4 grammar points (91 entries)
│   └── n5.json                N5 grammar points (76 entries)
│
├── scratch/                   (gitignored) Experiments and one-offs
│
├── .github/                   CI workflow + issue/PR templates
│   ├── workflows/build.yml    CI pipeline with reproducibility check
│   ├── ISSUE_TEMPLATE/        6 issue templates + config.yml chooser
│   ├── PULL_REQUEST_TEMPLATE.md
│   └── dependabot.yml         Dependency update automation
│
├── justfile                   Task runner recipes
├── pyproject.toml             Pytest + coverage configuration
├── .python-version            Python version pin (3.11)
├── .gitignore
└── .gitattributes
```

### Why this layout

- **`data/core/` vs. `data/enrichment/`**: Core files are the foundational facts (kanji character, word entries, radicals). Enrichment files are metadata *about* those foundations (how a character is written, how a word is pronounced, how common it is, what level it's at). A consumer can load core without loading enrichment, and some use cases (e.g., morphological parsing) only need core.
- **`data/corpus/` separate from `data/core/`**: Example sentences are a different kind of thing — they're the language in use, not language metadata. Many consumers don't need them.
- **`data/grammar/` separate from everything else**: Grammar is the project's original contribution (Phase 3) and has different provenance, different quality guarantees, and different update rhythms. Keeping it separate makes it easy to exclude, easy to version independently, and easy to iterate on without disturbing the rest.
- **`data/cross-refs/` as its own tree**: Cross-references are derived data, deterministically generated from the other files. They get their own location so consumers know they're not source data and so the build pipeline knows they must be regenerated whenever upstream data changes.
- **`data/optional/` gitignored by default**: JMnedict is 146 MB uncompressed and useful only to specific consumers (name-lookup, NLP pipelines). It's built on demand via `just build-names` and never committed to git.

---

## The build pipeline

The build is a single directed acyclic graph of transformations. Running `just build` (or equivalently `python -m build.pipeline`) executes every stage in the correct order.

### Pipeline stages

```
┌────────────┐   ┌──────────────┐   ┌───────────────┐   ┌─────────────┐   ┌─────────┐
│  fetch.py  │──▶│  transform/  │──▶│  validate.py  │──▶│  cross_     │──▶│  stats  │
│            │   │              │   │               │   │  links.py   │   │         │
│ downloads  │   │ per-source   │   │ every output  │   │ generates   │   │ reports │
│ and caches │   │ transformers │   │ validated     │   │ the x-refs  │   │ counts  │
│ upstream   │   │ emit JSON    │   │ against its   │   │ between all │   │ and     │
│ sources    │   │ to data/     │   │ schema        │   │ data types  │   │ coverage│
└────────────┘   └──────────────┘   └───────────────┘   └─────────────┘   └─────────┘
      │                  │                  │                  │                │
      ▼                  ▼                  ▼                  ▼                ▼
  sources/           data/core/          (in-memory          data/cross-    manifest.json
  (gitignored)       data/enrichment/    validation,          refs/          (build date,
                     data/corpus/        errors fail          (committed)    source pins,
                     data/grammar/        the build)                         row counts)
                     (committed)
```

### Fetch (`build/fetch.py`)

`fetch.py` holds a list of upstream sources with pinned URLs, expected SHA256 hashes, and target filenames in `sources/`. On invocation, it checks each source: if the cached copy exists and its hash matches the pin, it is used; otherwise, it is downloaded and verified. Hash mismatches are fatal — a wrong hash means upstream has changed and we need a conscious pin bump, not a silent update.

The list of pinned sources lives in `build/fetch.py` as Python constants. An upgrade to a newer upstream version is a single-line change plus a `manifest.json` update plus a changelog entry.

### Transform (`build/transform/*`)

Each data domain has its own transformer module. A transformer reads one or more files from `sources/`, produces one or more files in `data/`, and emits a metadata header on each output file crediting its source(s).

Transformers are independent: `kanji.py` does not know about `words.py`. This lets us rebuild individual domains without re-running the whole pipeline, and it lets us swap upstream sources without a cascading rewrite.

### Validate (`build/validate.py`)

Every file emitted to `data/` is validated against its schema in `schemas/` before the build can proceed. Validation errors fail the build loudly with the offending entry highlighted. A build that completes without errors is guaranteed to produce schema-valid output.

### Cross-links (`build/transform/cross_links.py`)

After all per-domain files are built and validated, `cross_links.py` reads them and emits the cross-reference indices in `data/cross-refs/`. Because this stage has every data file available, it can build O(1) lookup tables from any entity to any related entity. This is the stage that makes the dataset more than the sum of its parts.

### Stats (`build/stats.py`)

Final stage. Prints and writes a coverage report: number of entries per file, percentage of kanji with stroke-order SVGs, percentage of words with pitch accent data, percentage of grammar points with example sentences, and so on. Updates `manifest.json` counts.

---

## Schema philosophy

Every data file is JSON with a consistent structure:

```json
{
  "metadata": {
    "source": "…",
    "source_url": "…",
    "license": "…",
    "source_version": "…",
    "generated": "YYYY-MM-DD",
    "count": 0,
    "field_notes": { "field_name": "explanation of meaning, units, edge cases" }
  },
  "<payload_key>": [ /* or { /* entries */ } */ ]
}
```

The `metadata.field_notes` section is important: it is inline schema documentation that any consumer can read without external references. A field like `jlpt_old` carries a note explaining that it is the pre-2010 JLPT level system, not the current N1–N5 — so nobody can mistake one for the other.

Empty arrays are preferred over `null`. Missing fields are preferred to `null` fields. This follows the same philosophy as `jmdict-simplified` upstream and makes consumers simpler. Every item in every collection has the same shape, with no "inherit from previous" implicit fields.

Schemas use JSON Schema Draft 2020-12. Every schema is self-contained (no `$ref` into external documents for now, for portability). Schemas are placed in `schemas/` alongside each other and tested in `tests/test_schemas.py`.

### Versioning within the schema

Every schema declares a `schemaVersion`. **Schemas version independently from the repo (`manifest.json.version`) and from each other.** The `schemaVersion` on a given schema reflects the repo version at the time the schema's structure, semantics, or documentation was last meaningfully updated — not the current repo version.

Concretely: if `radical.schema.json` changed semantics in v0.4.0 (`meanings` and `classical_number` went from empty-by-default to populated-by-default), it is bumped to `"0.4.0"`. If `word.schema.json` was last meaningfully updated in v0.3.0 and has seen no structural or semantic change since, it stays at `"0.3.0"` even though the repo has since advanced to v0.4.0. This is intentional: bumping schema versions on every repo release would produce noise and diminish the signal value of the field.

Consumers that need to handle multiple schema versions can key on this field per schema. A schema with `schemaVersion: "0.3.0"` on a repo tagged `v0.4.0` means "this schema has not changed since v0.3.0 and is stable against it."

A reviewer who finds the distribution of schema versions across files confusing should interpret it as a feature, not a drift: schemas that have moved have newer versions, schemas that are stable have older ones.

---

## Versioning policy

The project uses semantic versioning (`MAJOR.MINOR.PATCH`) with the following rules:

- **MAJOR**: Schema-breaking changes that would cause downstream parsers to fail. Bumped rarely and deliberately. Pre-1.0.0 (the current state), any change may be schema-breaking and not trigger a major bump — consumers should pin to a specific version.
- **MINOR**: New data files, new fields in existing files, new sources, or new cross-reference types. Additive by definition; downstream parsers keep working but may not consume the new content.
- **PATCH**: Upstream source refreshes, bug fixes, documentation corrections, content additions that don't change schemas. This is the most common version bump, happening at least monthly in accordance with EDRDG License §4.

Every release is tagged in git (`v0.1.0`, etc.) and each tag has a corresponding entry in `CHANGELOG.md` and an updated `manifest.json` with the upstream source versions used.

### Phase timeline

- **Phase 0**: Scaffolding, documentation, schemas, pipeline skeleton. No data files yet. Versions 0.0.x.
- **Phase 1**: Core foundation — kanji, words, names (optional), radicals, sentences, kana, and their cross-links. First build that produces usable data. Target version 0.1.0.
- **Phase 2**: Enrichment — stroke order, pitch accent, frequency, JLPT. Cross-link expansion. Target version 0.2.0.
- **Phase 3**: Grammar dataset — original curation, JMdict expression extraction, conjugation generation. This is the original-work phase. Target version 0.3.0 for initial release, with incremental patch versions as coverage fills in.
- **Phase 4** (current): Supplementary data sources and extended coverage. Delivered: KFTT corpus (443,849 sentences), JESC subtitle corpus (2,801,388 sentences), WikiMatrix (851,706 sentences), full Tatoeba corpus (232,368 sentences), Japanese WordNet (596,612 semantic relations), JmdictFurigana (28,920 entries), 7 word frequency lists, Wiktionary pitch accent (12,788 entries), counter-words (125), ateji (239), jukugo compounds (14,350), word relations (2,283 pairs), sentence difficulty scoring (4,355,291 entries), 7 new cross-reference indices, exports (Anki .apkg, SQLite, Yomitan). Pipelines ready: Common Voice JA transcripts, Aozora Bunko curated corpus (47 works). See `docs/phase4-candidates.md`.
- **1.0.0**: Tagged when Phases 1–3 have stable schemas, complete core coverage, and the grammar dataset has reached its first stable milestone (N5 and N4 fully covered with native-speaker review, at minimum).

---

## Cross-references

The cross-reference files in `data/cross-refs/` are the project's main value-add. Consumers building any Japanese-language tool will rely on them heavily. This section describes what each one contains.

### `kanji-to-words.json`

Maps every kanji character to the list of word IDs in `data/core/words.json` whose `kanji` field contains that character. Enables "show me all the words using this kanji" lookups in O(1).

### `word-to-kanji.json`

Inverse of the above: maps every word ID to the list of kanji characters in any of its writings. Technically derivable at read time from `words.json` itself, but materializing it saves consumers from having to iterate.

### `word-to-sentences.json`

Maps every word ID to the list of Tatoeba sentence IDs that are confirmed examples of that word. Initially populated from the `jmdict-examples-eng` variant (editor-curated); may be extended in later phases.

### `kanji-to-radicals.json`

Maps every kanji to its component radicals using KRADFILE. Used for radical-based lookup and for teaching kanji composition.

Delivered cross-references beyond the core set:

- `word-to-grammar.json`: word → grammar patterns that reference it in examples (1,577 words, delivered in Phase 3)
- `grammar-to-words.json`: grammar pattern → words referenced in its examples
- `grammar-to-sentences.json`: grammar pattern → example sentence IDs
- `reading-to-words.json`: kana reading → word IDs (IME-style reverse lookup, 24,927 readings)
- `reading-to-words-full.json`: full-corpus variant of reading-to-words
- `kanji-to-words-full.json`: full-corpus variant of kanji-to-words
- `kanji-to-sentences.json`: kanji → example sentence IDs
- `kanji-to-sentences-full.json`: full-corpus variant of kanji-to-sentences
- `word-to-kanji-full.json`: full-corpus variant of word-to-kanji
- `radical-to-kanji.json`: radical → kanji containing it (reverse of kanji-to-radicals)
- `sentence-to-words.json`: sentence → word IDs it contains
- `word-relations.json`: semantic word relationships
- `wordnet-synonyms.json`: WordNet-derived synonym mappings

Future cross-references may include:

- `kanji-to-compounds.json`: kanji → list of multi-kanji compounds containing it

---

## Upstream contribution workflow

As stated in Design Principle 6, this project contributes fixes back to upstream sources. The workflow is:

1. During any phase, if a transformation module or validation step detects a likely error in upstream data (missing field, inconsistent encoding, outdated info), it logs the finding to `docs/upstream-issues.md` with the specific entry, the likely issue, and the expected correction.
2. At the end of each phase build, the accumulated upstream issues are reviewed and filed as issues or patches against the relevant upstream projects.
3. Once filed, the issue is marked with the upstream URL in `docs/upstream-issues.md` so we can track resolution.
4. When an upstream fix is merged, the next pin bump picks up the correction automatically, and the resolved entry is archived.

This keeps the contribution work asynchronous from the build work and avoids derailing phase progress on upstream PR cycles.
