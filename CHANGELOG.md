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

### Added

- Phase 0 foundation: repository scaffolding, documentation, schemas, and build pipeline skeleton.
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
- Tests directory skeleton for future schema validation tests.

### Known gaps (deliberate, to be addressed in later phases)

- No data files are built yet. `data/` subdirectories are empty except for `.gitkeep` files.
- Phase 1 (core foundation: kanji, words, names, radicals, sentences, kana) is not yet implemented.
- Phase 2 (enrichment: stroke order, pitch accent, frequency, JLPT, cross-linking) is not yet implemented.
- Phase 3 (grammar curation) is not yet implemented.
- Phase 4 candidates (classical handwriting, modern handwriting, Aozora Bunko texts, speech corpora, Wiktionary extraction, jinmeiyō names) are deferred; see `docs/phase4-candidates.md` for current thinking.

---

## Versioning policy

- **Every upstream rebuild** produces at minimum a patch release, with updated `manifest.json` source pins and a corresponding changelog entry.
- **Monthly rebuilds** are committed to, in accordance with EDRDG License §4 obligations. A release is tagged even if no substantive schema or content changes occurred, to demonstrate currency.
- **Schema-breaking changes** trigger a major version bump. Downstream consumers can pin to a specific major version for stability.
- **New data domains or new fields** trigger a minor version bump and are called out in this changelog.

Pre-1.0.0 versions (0.x.x) indicate that the dataset is still in active scaffolding and may undergo schema changes without a major version bump. Once the Phase 1–3 core is stable and schema-validated, v1.0.0 will be tagged.
