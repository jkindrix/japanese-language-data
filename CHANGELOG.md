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

### Added (feature additions, chosen by the author for user-facing value)

- **Jinmeiyō kanji view** (`data/core/kanji-jinmeiyo.json`): derived filter of `kanji.json` to grades 9 and 10 only — the kanji approved for personal-name use in Japan but not included in the Jōyō list. **863 entries**, matching the official 2017 MEXT jinmeiyō list count. Built by the kanji transform from the same source as the main kanji.json, using the exact same schema. Included in `build/validate.py` and `build/stats.py`.
- **Tatoeba sentence linkage for grammar examples**: the grammar transform now reads `data/corpus/sentences.json` and attempts exact-text matching between curated grammar example sentences and Tatoeba sentences. When a match exists, the grammar example's `source` is updated from `"original"` to `"tatoeba"` and a `sentence_id` is populated. Initial match rate is **1.7%** (3 of 180 examples), which is expected because the N5/N4 examples were written for pedagogical clarity rather than to reproduce corpus entries. The infrastructure is in place: future patches can add Tatoeba-sourced examples directly to `grammar-curated/` (they will pass through unchanged), or a fuzzy-matching pass can be added. The grammar metadata now includes a `tatoeba_linkage` summary with `total_examples`, `linked_examples`, `link_rate_pct`, and `method`.

### Added (post-review follow-up, continued from v0.3.1)

- **`.github/workflows/build.yml`** — reproducibility smoke test CI workflow. Addresses the review's Reproducibility-dimension gap ("Missing: reproducibility smoke test in CI"). On every push to `main` and every pull request, the workflow performs a cold checkout, installs pinned dependencies, fetches upstream sources (SHA256-verified), runs the full build pipeline, validates every output against its schema, runs the test suite, and prints stats. Uses GitHub Actions cache for the `sources/` directory keyed on `manifest.json` hash to avoid re-downloading the 43 MB of upstream files on every run.
- **`just ci`** — local equivalent of the CI workflow: `just fetch && just build && just validate && just test && just stats`. Runs the same smoke test against the local checkout. Exits non-zero on any step failure.
- **Stroke-count mismatch metadata** on `data/enrichment/stroke-order-index.json`. Addresses the remaining part of the review's recommendation #9 (the optional `metadata.warnings` for silent gaps — D5 orphan characters and M6 empty radicals were addressed in v0.3.1; the 109 stroke-count mismatches between KanjiVG and KANJIDIC2 are addressed here). New metadata fields:
  - `metadata.warnings`: list of human-readable warnings, currently two: (1) the 109 stroke-count mismatches, (2) the 48.9% KanjiVG coverage.
  - `metadata.stroke_count_mismatches`: structured list of all 109 affected characters, each with the KANJIDIC2 canonical count and the KanjiVG path-element-count. Consumers joining kanji.json with stroke-order-index.json can now detect and handle these cases explicitly. KANJIDIC2 remains the canonical source for stroke count; the mismatch list is documentation of the known divergence.

### Changed

- `build/transform/stroke_order.py`: emits the new `warnings` and `stroke_count_mismatches` metadata fields. Reads `data/core/kanji.json` when it exists to compute mismatches; gracefully falls back to empty lists when kanji.json is not yet built.

---

## [0.3.1] — 2026-04-11

Post-review defect fixes. This patch addresses every defect and stale-metadata issue flagged in the external review of the v0.3.0 release (D1–D5 and M1–M6 from the review notes). No new data sources or schemas are added; existing data is corrected where the review identified a wrong output.

### Fixed

- **D1**: `build/transform/conjugations.py` now handles the special-ending godan verb classes `v5k-s`, `v5u-s`, `v5aru`, and `v5r-i`. The previous version silently dropped all verbs in these classes, including `行く` (the canonical `v5k-s` verb), because `GODAN_POS_TO_ENDING` had no entry for these POS tags. The fix adds them to the map and applies per-POS overrides in `_conjugate_godan`:
  - `v5k-s`: te/ta forms use って/った instead of いて/いた (for 行く, 逝く, 往く)
  - `v5u-s`: te/ta forms use うて/うた instead of って/った (for 問う, 請う)
  - `v5aru`: i-stem and imperative use い instead of り (for いらっしゃる, ござる, なさる, おっしゃる)
  - `v5r-i`: nai/nakatta forms use the suppletive ない/なかった (for ある)
  - The previous dead `if stem == "行く" ...` check in `_conjugate_godan` has been removed; it is replaced by the POS-based handling which covers all v5k-s verbs, not just `行く`.
- **D2**: Broken `related` cross-references in the curated grammar data. `counter-tsu` referenced `counter-objects-ko` (which doesn't exist); removed. `potential-form` referenced `dekiru-potential` (which doesn't exist); removed. `build/transform/grammar.py` now validates that every `related` id resolves to an existing grammar entry and fails the build with a clear error if not.
- **D3**: Corrected the stale "6.6% JMdict ID drift" explanation in both `CHANGELOG.md` [0.2.0] and `docs/sources.md`. The ~6.6% of Waller JLPT vocab entries that don't appear in `data/core/words.json` are NOT due to JMdict ID drift (all 8,279 Waller seq IDs exist in the full JMdict); they are entries outside the common subset our `words.json` ships. They can be joined against `words-full.json` or they stand alone in `jlpt-classifications.json`.
- **D4**: Non-deterministic `jlpt_waller` assignment for words whose JMdict ID covers multiple homographic variants. When a single `jmdict_seq` appeared in multiple Waller level CSVs (e.g., 会う at N5 and 遭う at N2 sharing seq 1198180), the previous `_load_vocab_jlpt_map` in both `build/transform/words.py` and `build/transform/expressions.py` used the last-iterated level, which was deterministic (stable across runs) but semantically wrong. The fix: for duplicate `jmdict_seq`, the easier level wins (N5 > N4 > N3 > N2 > N1). Pedagogically, this reflects the level at which a learner first encounters the common form of the word. Documented in the `jlpt_waller` field_note on `words.json`.
- **D5**: `build/transform/cross_links.py` now detects and records characters in `kanji-to-words.json` that have no corresponding entry in `kanji.json`. The fix loads `kanji.json`, computes the set of orphan characters (words-side kanji that KANJIDIC2 does not index), logs a warning with the first 20 orphans, and writes `metadata.orphan_count` and `metadata.orphan_chars` to `kanji-to-words.json`. Consumers joining these two files can detect the integrity gap at read time instead of silently missing lookups.
- **M1**: Bumped `schemaVersion` from `"0.0.0"` to `"0.3.0"` in every schema that was still stale: `kana`, `kanji`, `word`, `name`, `radical`, `sentence`, `pitch-accent`, `frequency`, `jlpt`, `stroke-order`, `grammar`, `cross-refs` (12 files). `expressions.schema.json` and `conjugations.schema.json` were already at `0.3.0` and are unchanged.
- **M2**: `schemas/grammar.schema.json` description no longer claims the grammar dataset is derived from Tae Kim. The stale description was a Phase 0 scaffolding artifact that contradicted the Phase 3 authorship statement and could be read as a license-risk inconsistency. The description now correctly states that the data is hand-curated from general, non-copyrightable facts and explicitly NOT derived from Tae Kim or other copyrighted sources.
- **M3**: `docs/gaps.md` "Native-speaker reviewed grammar" section no longer claims Tae Kim is a source. Same correction as M2 but in the gaps doc.
- **M4**: `docs/phase4-candidates.md` JPDB entry status changed from "PROMOTED to Phase 4" to "DEFERRED (license-blocked)". Phase 4 is not active; "PROMOTED" was misleading.
- **M6**: `build/transform/radicals.py` now emits a `warning` field in `data/core/radicals.json` metadata, explicitly stating that every radical's `meanings` array is empty and `classical_number` is null because RADKFILE does not provide those fields and no CC-BY-SA-compatible upstream joining source is currently integrated.

### Added

- **T1** (test-coverage gap from review): new `tests/test_data_integrity.py` with 5 targeted regression tests corresponding to D1, D2, D4, and D5. Each test reads a built data file and verifies an invariant that would have caught the original defect. Tests gracefully skip if the file has not been built, preserving the ability to run `pytest tests/` on a fresh checkout.
  - `test_d1_conjugations_covers_iku`: verifies 行く has a conjugation table and the te/ta forms are いって/いった
  - `test_d1_conjugations_covers_v5aru_and_v5r_i`: verifies at least one v5aru and one v5r-i verb is emitted
  - `test_d2_grammar_related_references_resolve`: verifies every grammar `related` id resolves
  - `test_d4_words_jlpt_easier_level_wins`: verifies word 1198180 has `jlpt_waller=N5`
  - `test_d5_kanji_to_words_orphan_count_matches`: verifies `orphan_count` metadata matches reality

### Changed

- `data/grammar/conjugations.json` regenerated: entries with `v5k-s`, `v5u-s`, `v5aru`, `v5r-i` classes are now emitted where previously silently dropped. New entries cover 行く and other verbs in these classes.
- `data/core/words.json`, `data/core/kanji.json`, `data/core/kanji-joyo.json`, `data/core/words-full.json` regenerated with deterministic D4 JLPT join. For words with multi-level JLPT entries, `jlpt_waller` now reflects the easier level.
- `data/cross-refs/kanji-to-words.json` regenerated with new `orphan_count` and `orphan_chars` metadata fields.
- `data/core/radicals.json` regenerated with new `warning` metadata field.
- `data/enrichment/stroke-order-index.json`, `data/enrichment/jlpt-classifications.json`, etc. regenerated; content is unchanged except for the `generated` date.
- `grammar-curated/n5.json` — removed broken reference to `counter-objects-ko`.
- `grammar-curated/n4.json` — removed broken reference to `dekiru-potential`.

### Not changed (deliberately)

- **M5**: The review's M5 recommendation was a 15-minute middle-ground for the case where D1 was NOT fixed. Since D1 is fully fixed in this patch, adding a "known exclusions" note for v5k-s/v5aru/v5r-i/v5u-s would be misleading — they are no longer excluded.
- **M7**: The review noted this as "minor, not a bug" (a forward reference to a planned `stroke-order-metadata.json` in `docs/gaps.md`). No fix applied.
- **Observations (the green section of the review)**: 48.9% KanjiVG coverage, 109 stroke-count mismatches, 14 empty Waller jmdict_seq, 0.7% expression JLPT coverage, draft review_status, kana stroke-count caveat, single-maintainer upstream risk, `frequency-modern.json` placeholder, `names.json` gitignored — none of these were flagged as defects; no changes applied.

---

## [0.3.0] — 2026-04-11

Phase 3 — Grammar foundation. First tranche of original grammar content plus derived grammar datasets (expressions and conjugations). **This is the largest amount of original content in the project.** Everything in the grammar dataset is written in our own words based on general, non-copyrightable facts about Japanese grammar; nothing is copied from Tae Kim's Guide (CC-BY-NC-SA, license incompatible with our CC-BY-SA 4.0 output) or any other copyrighted source.

### Added

- **Curated grammar dataset** (`data/grammar/grammar.json`): **81 grammar points** hand-written from the project author's general knowledge of Japanese, following the grammar schema. All entries are flagged `review_status: "draft"` — the aspiration is `native_speaker_reviewed`, but the project does not yet have a native-speaker review pipeline. See `docs/contributing.md` for the call to reviewers.
  - **N5**: 50 entries covering copula (です/だ/でした/ではありません), polite verb forms (ます/ました/ません/ませんでした), particles (は, が, を, に, で, と, の, へ, から, まで, も, か, ね, よ, や), demonstratives (これ/それ/あれ, この/その/あの, ここ/そこ/あそこ), existence (あります/います), te-form basics (-て, -てください, -ています), -ない form, -た form, i-adjective and na-adjective conjugations, volitional (ましょう/ましょうか), desire (-たい, がほしい), comparison (のほうが...より, 一番), counters (~つ, ~人), question words, and -ないでください.
  - **N4**: 31 entries covering potential form, passive form, causative form, -たことがある (experience), つもり (intention), と思う (opinion), と言う (quotation), だろう/でしょう (conjecture), かもしれない (possibility), はず (expectation), four conditionals (たら, ば, と, なら), volitional form, -てはいけない (prohibition), -てもいい (permission), -なければならない (obligation), -なくてもいい (lack of obligation), から/ので (because), が/けど (although), んです (explanation), なる/する (change/decision), verb-stem auxiliaries (-始める, -終わる, -すぎる, -やすい, -にくい), and noun-modifying clauses.
- **JMdict expressions dataset** (`data/grammar/expressions.json`): **13,220 entries** — every JMdict entry with at least one sense tagged `exp` (expression). 436 of these are marked common. Each entry preserves its JMdict ID for cross-reference with `words.json`, plus all kanji writings, kana readings, English meanings of exp-tagged senses, and any Waller JLPT classification that matches by JMdict ID.
- **Auto-generated conjugation tables** (`data/grammar/conjugations.json`): **3,492 entries** covering every supported word class in `words.json` (common subset). Generated using formal conjugation rules encoded in `build/transform/conjugations.py` — no native-speaker review needed for the rules themselves (any incorrectness indicates a bug in the rule implementation). Breakdown:
  - v1 (ichidan): 555
  - v5k, v5s, v5u, v5r, v5m, v5t, v5g, v5b, v5n: 1,143 total across godan classes
  - vs-i (suru-verb compounds): 12
  - vk (くる): 1
  - adj-i: 312
  - adj-na: 1,469
  - Generates up to 16 forms per entry (dictionary, polite non-past/past/negative/past-negative, te-form, ta-form, nai-form, nakatta-form, potential, passive, causative, imperative, volitional, conditional_ba, conditional_tara).
- **Grammar JLPT classifications** integrated into `data/enrichment/jlpt-classifications.json`: 81 new entries with `kind: grammar`, bringing the total classification count from 10,504 → **10,585**. Each grammar classification includes a `grammar_id` field that joins with `data/grammar/grammar.json`.
- New schemas: `schemas/expressions.schema.json` and `schemas/conjugations.schema.json` (Draft 2020-12). Expected count: 14 → **14** (confirmed by tests).
- New transforms: `build/transform/grammar.py`, `build/transform/expressions.py`, `build/transform/conjugations.py`. The grammar transform reads from the committed `grammar-curated/` directory and validates every entry.
- New committed directory: **`grammar-curated/`** — our original hand-written grammar entries in JSON format, one file per JLPT level (`n5.json`, `n4.json`). These are the authoritative inputs to the grammar transform and are edited directly when adding/correcting grammar points.

### Changed

- `build/transform/jlpt.py` now also reads `grammar-curated/*.json` and emits `kind: grammar` classifications in addition to `kind: vocab` (from stephenmk) and `kind: kanji` (from davidluzgouveia). The JLPT metadata `counts_by_kind_and_level` now tracks grammar counts per level.
- `build/pipeline.py` adds three new stages (grammar, expressions, conjugations) as Phase 3 transforms, running after the cross-reference stage.
- `build/validate.py` SCHEMA_MAP extended with grammar.json, expressions.json, and conjugations.json.
- `build/stats.py` TARGET_FILES extended with the three new grammar files.
- `tests/test_schemas.py` guardrail test updated to expect 14 schema files (added expressions and conjugations).
- README status and manifest version/phase updated to Phase 3 / v0.3.0.

### Content provenance statement

**All grammar explanations in `grammar-curated/*.json` are written in our own words based on general, well-known, non-copyrightable facts about Japanese grammar.** We explicitly did NOT consult any of the following during writing, because their licenses are incompatible with our CC-BY-SA 4.0 output:

- **Tae Kim's Guide to Japanese** — CC-BY-NC-SA 3.0 (the NC clause is irreconcilable with our CC-BY-SA 4.0 output; incorporating any derivative would contaminate our license chain)
- **Dictionary of Basic/Intermediate/Advanced Japanese Grammar** (Seiichi Makino and Michio Tsutsui) — proprietary
- **Handbook of Japanese Grammar Patterns** — proprietary
- **Hanabira's grammar content** — license unclear

Sources referenced in grammar entries are cited as "General Japanese grammar knowledge" — this is honest: the factual content (which particles mark what, how verbs conjugate, what patterns mean) is well-known linguistic fact, not a derivative of any specific copyrighted work.

### Example sentence source

**All 200+ example sentences in grammar.json are marked `source: "original"`.** They are written by the project author to illustrate the pattern in its typical use. They are NOT linked to Tatoeba sentence IDs in this release. A future patch (v0.3.x) could add Tatoeba cross-references via text-match lookup against `data/corpus/sentences.json` for exact or near-exact matches.

### Data summary

| File | Phase 2 → Phase 3 |
|---|---|
| All Phase 1 and 2 files | unchanged |
| `data/enrichment/jlpt-classifications.json` | 10,504 → **10,585** (+81 grammar) |
| `data/grammar/grammar.json` | new — 81 entries |
| `data/grammar/expressions.json` | new — 13,220 entries |
| `data/grammar/conjugations.json` | new — 3,492 entries |

**Total committed entries: 495,766** (up from 478,892 in v0.2.0).

### Deliberate scope choices (with 15-minute middle-grounds applied)

- **Coverage limited to ~15% of total JLPT grammar** (N5 essentials + N4 selections, not complete N5+N4). **Middle-ground applied**: entries are tagged with explicit level metadata; `review_coverage` summary in metadata shows 81 draft entries; `docs/gaps.md` already documents the grammar coverage gap and the native-speaker review gap. Future patches can incrementally fill in N3, N2, N1.
- **All examples are original**, not linked to Tatoeba. **Middle-ground applied**: the schema allows `source: "tatoeba"` with a `sentence_id` field, and a future build step could text-match and populate it. For this release, we ship original examples with honest provenance.
- **No content from proprietary or NC-licensed sources**. **Middle-ground applied**: source field on each entry honestly says "General Japanese grammar knowledge" — it does not falsely cite sources we did not actually open.
- **Native-speaker review not available**. **Middle-ground applied**: every entry has `review_status: "draft"`; `docs/contributing.md` has a prominent call for native-speaker reviewers; the schema supports a progressive workflow (draft → community_reviewed → native_speaker_reviewed).

### Known limitations

- **Grammar correctness is the weakest verification point.** The project author (Claude) has broad knowledge of Japanese grammar but is not a native speaker or professional linguist. Subtle errors in nuance, formality, or rare usage are possible. This is why every entry starts as draft.
- **Conjugation generation covers ~3,500 entries**, which is the conjugable subset of the common-subset words.json (22,580 entries). Entries that are nouns, adverbs, or verbs with unusual conjugation patterns are skipped. The skipped count (34,396) includes multi-POS iterations, not 34k distinct skipped words.
- **ら-abbreviated ichidan potential forms** (食べれる for 食べられる, widely used in modern colloquial Japanese but grammatically nonstandard) are NOT generated; only the traditional form with ら is emitted. Documented in conjugations.json field notes.
- **Grammar JLPT classifications are community-consensus level assignments.** The level field on each grammar point was chosen by the project author based on which JLPT level typically tests the pattern, not from a definitive JLPT-official source (which doesn't exist — see the jlpt.schema.json disclaimer).
- **Expressions dataset includes 13,220 entries, ~30x the grammar point count**, because JMdict's `exp` tag covers everything from functional grammar (e.g., 〜てください) to set phrases (いらっしゃいませ) to idioms. The expressions and grammar datasets overlap in coverage but serve different purposes: grammar is compositional pedagogy; expressions is lexical lookup.

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
- `build/transform/words.py` now reads `data/enrichment/jlpt-classifications.json` and populates `jlpt_waller` via the JMdict sequence ID join. 7,208 common-subset words (out of 22,580) and 7,747 full-dataset words are now classified to an N5-N1 level. The remaining ~6.6% of Waller entries don't appear in `words.json` because they are not in the common subset (they reference valid JMdict IDs that the common filter excludes); all 8,279 Waller seq IDs exist in the full JMdict.
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

- **JLPT vocab coverage gap**: ~6.6% of Waller's JLPT vocab entries cannot be joined to `data/core/words.json` by ID — not because of JMdict ID drift (all Waller seq IDs DO exist in the full JMdict) but because those entries are outside the common subset that `words.json` ships. They can be joined against `words-full.json` (gitignored build artifact) or stand alone in `jlpt-classifications.json`.
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
