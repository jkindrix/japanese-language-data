# Changelog

All notable changes to the Japanese Language Data project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). This project uses semantic versioning as defined in `docs/architecture.md`:

- **Major** (X.0.0): Schema-breaking changes that will require downstream code updates.
- **Minor** (0.X.0): New data domains, new fields, new sources, or substantial new data.
- **Patch** (0.0.X): Upstream data refreshes, bug fixes, documentation corrections, minor additions.

Unreleased changes accumulate under `[Unreleased]` until a version is tagged.

Upstream source versions used for each release are recorded in `manifest.json` at the time of the build and referenced in the relevant changelog entry.

---

## [Unreleased]

_No unreleased changes._

---

## [0.1.0] — 2026-04-11

Phase 1 — Core data foundation. First release that produces actual data files.

### Added

- **Kana dataset** (`data/core/kana.json`): 215 hand-curated entries covering basic hiragana/katakana, dakuten, handakuten, yōon combinations, sokuon, archaic kana, and the long-vowel mark. Includes stroke counts for base forms, Unicode codepoints, Hepburn and Kunrei-shiki romanizations, type classifications, and usage notes for non-obvious entries.
- **Kanji dataset** (`data/core/kanji.json`): 13,108 kanji characters from KANJIDIC2 (full character set, ingested via `scriptin/jmdict-simplified` 3.6.2). Each entry includes readings (on/kun in Japanese; pinyin/Korean/Vietnamese for cross-linguistic reference), multilingual meanings (en/fr/es/pt), stroke count, grade, JLPT (old system), frequency, radicals, nanori, variants, dictionary references (Heisig, Nelson, Halpern, Morohashi, etc.), and query codes (SKIP, Four Corner, Spahn/Hadamitzky, De Roo).
- **Jōyō kanji view** (`data/core/kanji-joyo.json`): Derived filter of `kanji.json` containing exactly 2,136 characters — the official 2010 MEXT Jōyō list (kyōiku grades 1-6 + secondary grade 8).
- **Words dataset — common subset** (`data/core/words.json`): 22,580 common JMdict entries (from jmdict-examples-eng 3.6.2). Includes every entry with at least one kanji or kana writing flagged as common in JMdict's news1/ichi1/spec1/gai1 priority markers. Each entry carries full JMdict sense structure plus editor-curated example sentence links to Tatoeba.
- **Words dataset — full** (`data/core/words-full.json`, gitignored): 216,173 entries. Built on demand via `just build`; gitignored because it exceeds typical git file size thresholds. Intended for release-artifact distribution.
- **Radicals dataset** (`data/core/radicals.json`): Bidirectional view combining KRADFILE (12,156 kanji → component radicals) and RADKFILE (253 radicals → kanji containing them).
- **Sentences dataset** (`data/corpus/sentences.json`): 25,980 unique example sentences (Japanese + English pairs) extracted from the editor-curated Tatoeba sentences embedded in jmdict-examples-eng. Deduplicated by Tatoeba sentence ID.
- `build/fetch.py`: Pinned fetcher with SHA256 verification for all 7 upstream source files.
- Phase 1 implementations of `build/transform/{kanji,words,sentences,radicals,kana}.py`.
- Schema fix: `kana.schema.json` now allows null `stroke_count` for yōon compound forms, which do not have a single canonical stroke count.
- Schema fix: `word.schema.json` `examples` items now have explicit required fields (`source`, `sentence_id`) and clearer field names (`word_form`, `japanese`, `english`).
- `data/core/kanji-joyo.json` and `data/core/words-full.json` added to `build/validate.py` SCHEMA_MAP and `build/stats.py` TARGET_FILES.
- `.gitignore`: `data/core/words-full.json` excluded (gitignored build artifact).
- Logged schema gaps (pitch accent `skipMisclassification` field, Morohashi volume/page) in `docs/upstream-issues.md`.
- Upstream source addition: `kanjidic2-all.json.tgz` (13,108 characters, all-language meanings) replacing `kanjidic2-en.json.tgz` (10,383 characters, English only). Net gain: 2,725 additional characters covered.

### Changed

- Bumped `manifest.json` version from `0.0.0` to `0.1.0` and phase from 0 to 1.
- README status line updated to reflect Phase 1 completion.
- `manifest.json` `sources` now contains verified SHA256 hashes for all 7 upstream pinned files.

### Data summary

Total committed entries across all Phase 1 files: **280,445**
- kana.json: 215 entries
- kanji.json: 13,108 entries (15.6 MB)
- kanji-joyo.json: 2,136 entries (3.5 MB)
- words.json: 22,580 common entries (44.4 MB)
- radicals.json: 253 radical entries + 12,156 kanji-component mappings (1.8 MB)
- sentences.json: 25,980 unique sentences (8.9 MB)

Total committed data: ~74 MB.
Total uncommitted build artifact (words-full.json): ~285 MB.

### Known gaps (deliberate, to be addressed in later phases)

- Phase 2 (enrichment: stroke order, pitch accent, frequency, JLPT, cross-linking) is not yet implemented. The `jlpt_waller` and `frequency_media` fields on word entries are null; `radical_components` on kanji entries is an empty array.
- Phase 3 (grammar curation) is not yet implemented.
- Phase 4 candidates (classical handwriting, modern handwriting, Aozora Bunko texts, speech corpora, Wiktionary extraction, jinmeiyō-specific view) are deferred; see `docs/phase4-candidates.md`.

---

## [0.0.0] — 2026-04-11

Phase 0 foundation: scaffolding, documentation, schemas, and build pipeline skeleton. No data files built.

### Added

- Repository scaffolding, documentation, schemas, and build pipeline skeleton.
- Project README, LICENSE with full EDRDG and upstream license obligations, ATTRIBUTION.md with per-source credits.
- Architecture documentation (`docs/architecture.md`) describing data layout, pipeline, versioning, and design principles.
- Source documentation (`docs/sources.md`) cataloging every upstream source with pinned URL, version, format, license, and expected transformations.
- Gap documentation (`docs/gaps.md`) explicitly naming what this dataset does not cover and why.
- Phase 4 candidate documentation (`docs/phase4-candidates.md`) cataloging future extension candidates.
- Contributing guide (`docs/contributing.md`) including the call-out for native-speaker grammar reviewers.
- Build guide (`docs/build.md`) describing the fetch → transform → validate → stats pipeline.
- Schema overview (`docs/schema.md`) explaining the schema design philosophy.
- Initial JSON Schema skeletons for every planned data file under `schemas/`.
- Build pipeline skeleton (`build/`) with `fetch.py`, `pipeline.py`, `validate.py`, `stats.py`, and transform module stubs for every data type.
- `justfile` with recipes for `fetch`, `build`, `validate`, `stats`, `clean`, and `test`.
- `manifest.json` tracking repo and upstream source versions.
- `.gitignore` and `.gitattributes` configured for the expected file types.
- Tests directory skeleton with 37 schema validation tests (all passing).

---

## Versioning policy

- **Every upstream rebuild** produces at minimum a patch release, with updated `manifest.json` source pins and a corresponding changelog entry.
- **Monthly rebuilds** are committed to, in accordance with EDRDG License §4 obligations. A release is tagged even if no substantive schema or content changes occurred, to demonstrate currency.
- **Schema-breaking changes** trigger a major version bump. Downstream consumers can pin to a specific major version for stability.
- **New data domains or new fields** trigger a minor version bump and are called out in this changelog.

Pre-1.0.0 versions (0.x.x) indicate that the dataset is still in active scaffolding and may undergo schema changes without a major version bump. Once the Phase 1–3 core is stable and schema-validated, v1.0.0 will be tagged.
