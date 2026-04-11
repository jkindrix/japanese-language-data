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

## [0.2.0] — 2026-04-11

Phase 2 — Enrichment and cross-references. All Phase 1 files are re-emitted with enrichment fields populated; six new enrichment and cross-reference files are added. Total committed data entries: 478,892 (up from 280,445 in v0.1.0).

### Added

- **Stroke order SVGs** (`data/enrichment/stroke-order/*.svg`): 6,416 individual SVG files from the KanjiVG `main` (non-variant) distribution r20250816. Files are named with the kanji character itself (e.g., `日.svg`). License: CC-BY-SA 3.0 Unported, upgraded to CC-BY-SA 4.0 in our CC-BY-SA 4.0 aggregate output per CC compatibility rules.
- **Stroke order index** (`data/enrichment/stroke-order-index.json`): 13,108 entries — one per kanji in our `kanji.json`. Each entry maps a character to its SVG filename (or null if no stroke order data exists upstream) and a stroke count derived from counting `<path>` elements in the SVG.
- **Pitch accent data** (`data/enrichment/pitch-accent.json`): 124,011 entries from Kanjium `accents.txt` (126 malformed upstream lines skipped). Each entry has the word, kana reading, pitch accent mora positions, and a derived mora count. Coverage date documented as approximately 2022 (Kanjium upstream is currently stale).
- **JLPT classifications** (`data/enrichment/jlpt-classifications.json`): 10,504 total classifications combining:
  - Vocabulary: 8,293 entries (N5=684, N4=640, N3=1,730, N2=1,812, N1=3,427) sourced from Jonathan Waller's JLPT Resources via `stephenmk/yomitan-jlpt-vocab` (CC-BY-SA 4.0). Each entry carries the JMdict sequence ID for clean join with `words.json`.
  - Kanji: 2,211 entries (N5=79, N4=166, N3=367, N2=367, N1=1,232) extracted from `davidluzgouveia/kanji-data` `jlpt_new` field only. WaniKani-derived fields deliberately ignored due to incompatible license.
  - Grammar: deferred to Phase 3 (schema supports `kind: grammar`).
- **Newspaper frequency rankings** (`data/enrichment/frequency-newspaper.json`): 2,501 ranked kanji extracted from KANJIDIC2 `misc.frequency` field. Represents a newspaper corpus from roughly the early 2000s. Modern media frequency (JPDB) is deferred to Phase 4.
- **Cross-reference indices** in `data/cross-refs/`:
  - `kanji-to-words.json` — 3,533 kanji characters mapped to the common-subset word IDs that contain them
  - `word-to-kanji.json` — 18,084 word IDs mapped to their component kanji characters
  - `word-to-sentences.json` — 14,550 word IDs mapped to their editor-curated Tatoeba sentence IDs
  - `kanji-to-radicals.json` — 12,156 kanji mapped to their component radicals from KRADFILE
- Six new upstream sources pinned in `build/fetch.py` with SHA256 verification:
  - `waller-jlpt-vocab-{n5,n4,n3,n2,n1}` — stephenmk CSV files for each level
  - `waller-jlpt-kanji` — davidluzgouveia kanji.json for kanji classifications
- Phase 2 transform implementations in `build/transform/`: `stroke_order.py`, `pitch.py`, `jlpt.py`, `frequency.py`, and `cross_links.py` replacing their Phase 0 stubs.

### Changed

- **Pipeline order reorganized** in `build/pipeline.py` so that independent transforms (kana, radicals, stroke_order, pitch, jlpt, frequency) run before main transforms (kanji, words, sentences) that consume their output. This enables kanji and words to read enrichment data during their build.
- `build/transform/kanji.py` now reads `data/enrichment/jlpt-classifications.json` and `data/core/radicals.json` if they exist, and populates `jlpt_waller` and `radical_components` fields per entry. Backward-compatible: if enrichment files are absent, those fields remain null/empty as in Phase 1. 2,211 kanji now have `jlpt_waller` populated (N5-N1 classifications), and 12,156 kanji have `radical_components` populated.
- `build/transform/words.py` now reads `data/enrichment/jlpt-classifications.json` and populates `jlpt_waller` via the JMdict sequence ID join. 7,208 common-subset words (out of 22,580) and 7,747 full-dataset words are now classified to an N5-N1 level. The remaining ~6.6% mismatch between upstream JLPT CSV entries and our word IDs is due to JMdict ID drift across JMdict revisions — not a data error.
- `data/core/kanji.json`, `data/core/kanji-joyo.json`, `data/core/words.json` are updated in place with the newly-populated enrichment fields. `data/core/words-full.json` (gitignored) is similarly updated.
- README status updated to reflect Phase 2 completion.

### Data summary

| File | Entries | Notes |
|---|---:|---|
| `data/core/kana.json` | 215 | unchanged |
| `data/core/kanji.json` | 13,108 | enriched: 2,211 jlpt_waller, 12,156 radical_components |
| `data/core/kanji-joyo.json` | 2,136 | derived view, enriched |
| `data/core/words.json` | 22,580 | enriched: 7,208 jlpt_waller |
| `data/core/words-full.json` | 216,173 | gitignored; enriched: 7,747 jlpt_waller |
| `data/core/radicals.json` | 253 radicals + 12,156 mappings | unchanged |
| `data/corpus/sentences.json` | 25,980 | unchanged |
| `data/enrichment/stroke-order/*.svg` | 6,416 SVG files | new |
| `data/enrichment/stroke-order-index.json` | 13,108 | new |
| `data/enrichment/pitch-accent.json` | 124,011 | new |
| `data/enrichment/frequency-newspaper.json` | 2,501 | new |
| `data/enrichment/jlpt-classifications.json` | 10,504 | new |
| `data/cross-refs/kanji-to-words.json` | 3,533 | new |
| `data/cross-refs/word-to-kanji.json` | 18,084 | new |
| `data/cross-refs/word-to-sentences.json` | 14,550 | new |
| `data/cross-refs/kanji-to-radicals.json` | 12,156 | new |

**Total committed entries: 478,892** (plus 6,416 SVG files).

### Deliberate deferrals (with 15-minute middle-grounds applied)

- **Modern media frequency (JPDB/Kuuuube)**: deferred to Phase 4. Both `MarvNC/jpdb-freq-list` and `Kuuuube/yomitan-dictionaries` lack explicit license files; the underlying JPDB.io corpus derives from copyrighted media. Documented as a Phase 4 candidate with license clarification required. Phase 2 ships only newspaper frequency, which is CC-BY-SA via EDRDG.
- **Grammar JLPT classifications**: the `jlpt-classifications.json` schema already supports `kind: grammar`; Phase 2 only populates `vocab` and `kanji` kinds. Grammar entries will be added in Phase 3 alongside the grammar dataset itself.
- **Radical meanings and Kangxi numbers**: RADKFILE does not provide these. The `radicals.json` file has empty `meanings` arrays and null `classical_number` fields. Joining from external sources (Wikipedia radical table, Unicode CJK Radical Supplement block) is a Phase 4 candidate.

### Known limitations

- **JLPT vocab mismatch**: 6.6% of Waller's JLPT vocab entries reference JMdict IDs that no longer match current JMdict entries (likely due to upstream ID drift across JMdict revisions). These entries are still included in `jlpt-classifications.json` but cannot be joined with `words.json` by ID. A later patch release could improve the match by using text-based fallback matching (by kanji + kana), at the cost of potential false positives.
- **Cross-references are scoped to the common-subset words**: `kanji-to-words.json` and `word-to-kanji.json` reference the common-subset word IDs in `words.json`. Consumers wanting full 216k cross-references should re-run the pipeline against `words-full.json`.
- **Stroke order count may differ from KANJIDIC2**: we derive stroke counts by counting SVG path elements in KanjiVG, which can differ by ±1 from KANJIDIC2 in edge cases (e.g., how a cross-stroke is counted). Consumers should prefer KANJIDIC2's `stroke_count` in `kanji.json` as the canonical count.
- **Pitch accent data is ~2022 vintage** (upstream Kanjium is currently stale). Vocabulary added to Japanese after 2022 lacks pitch accent entries. Documented in `docs/gaps.md` and `pitch-accent.json` metadata.

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
