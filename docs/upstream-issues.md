# Upstream issues log

This file tracks errors, gaps, and improvement suggestions discovered in upstream sources during this project's build phases. Items here are batched and filed upstream at the end of each phase, per the upstream contribution workflow described in `docs/architecture.md`.

## Phase 1–4 filing status (as of v0.8.0+, 2026-04-12)

**Zero *defect* items have been filed to any upstream through Phase 4, because no substantive upstream defects have been identified.** Two *feature requests* targeting `scriptin/jmdict-simplified` were filed on 2026-04-12 as issues [#36](https://github.com/scriptin/jmdict-simplified/issues/36) and [#37](https://github.com/scriptin/jmdict-simplified/issues/37) — they are schema exposure requests, not defect reports.

Honest accounting:

- **Phase 1 (core ingestion, v0.1.0)**: No substantive upstream defects identified. JMdict, KANJIDIC2, KRADFILE, and RADKFILE all parsed cleanly. Two internal schema gaps were discovered during kanjidic2 inspection (`skipMisclassification` and `morohashi` volume/page detail) — these are tracked in "Pending" below because the *information* is present in the upstream JSON but in a shape our schema cannot round-trip. Drafted issue text for both is in "Drafted" below.
- **Phase 2 (enrichment, v0.2.0)**: No substantive upstream defects identified. Kanjium's `accents.txt` parsed cleanly. KanjiVG stroke counts differ from KANJIDIC2 for 109 characters (documented in `stroke-order-index.json` metadata.stroke_count_mismatches), but this is a known methodology difference (KanjiVG counts path elements; KANJIDIC2 gives canonical counts) rather than a defect — both sources are internally consistent.
- **Phase 3 (grammar, v0.3.0)**: No upstream interactions; grammar content is hand-curated from general knowledge. 6.6% of Waller vocab entries were initially misdescribed as "JMdict ID drift" in v0.2.0 CHANGELOG; this was corrected in v0.3.1 to reflect the actual cause (common-subset filtering). The correction was internal; nothing upstream to file.
- **Phase 4 (Wikipedia + alias table, v0.4.0 + v0.7.1)**: No substantive upstream defects identified in the Wikipedia Kangxi radicals article. 56 of 253 RADKFILE radicals did not appear directly in Wikipedia's Kangxi table (v0.4.0 state); 45 of those were resolved in v0.7.1 via a curated alias table in `build/transform/radicals.py`, bringing coverage to 242/253. The remaining 11 are Nelson-style variants that are not Kangxi-classifiable — a scope difference, not an upstream defect.

**Design Principle 6 assessment**: the principle ("upstream contribution as ongoing obligation") is applied reactively. The rigorous defect-fix cycles occurred against *this project's* outputs and schemas because upstream (EDRDG, KanjiVG, Kanjium, Wikipedia) is well-maintained — there has been nothing concrete to file. If substantive upstream defects are discovered during future phases or user reports, they will be filed and tracked in this log. The two drafted schema-exposure feature requests below are the first Principle 6 actions that could plausibly be filed; the decision to file them has been deferred pending the project owner's discretion about whether to open issues on a single-maintainer upstream.

Each entry should include:

- **Date discovered**
- **Upstream project**
- **Entry/field identifier**
- **Description of the issue**
- **Proposed correction** (if known)
- **Status**: `pending` → `filed` → `resolved` → `archived`
- **Upstream URL** (once filed)

---

## Format

```markdown
### [YYYY-MM-DD] <upstream project>: <short description>

**Entry**: <ID or lookup key>
**Issue**: <what's wrong>
**Proposed fix**: <what it should be>
**Status**: pending
**Filed**: not yet
**Discovered during**: <phase / task>
```

---

## Pending (internal schema simplifications)

### [2026-04-11] our-schema: skipMisclassification field not captured in kanji query_codes

**Entry**: Applies to any kanji with a non-null `skipMisclassification` on a SKIP query code in KANJIDIC2.
**Issue**: The upstream JSON exposes `skipMisclassification` on `queryCodes` entries of `type: "skip"` with values `posn`, `stroke_count`, `stroke_and_posn`, `stroke_diff` (942 non-null across the full dataset). The field is documented in the upstream TypeScript type definitions (`Kanjidic2QueryCodeSkip`). Our `kanji.schema.json` captures SKIP as a flat string and deliberately drops this metadata — a schema simplification, not an upstream gap.
**Proposed fix (internal)**: Extend the schema's `query_codes.skip` field to optionally be an object `{value, misclassification}` instead of a bare string, or add a separate `query_codes.skip_misclassification` field. Minor-version schema bump.
**Status**: pending (internal) — deferred; low priority since misclassification codes are niche
**Discovered during**: Phase 1 kanjidic2 structure inspection

### [2026-04-11] our-schema: morohashi dictionary reference loses volume/page

**Entry**: Applies to any kanji with a `"type": "moro"` dictionary reference in KANJIDIC2.
**Issue**: The upstream JSON exposes `{"type": "moro", "morohashi": {"volume": N, "page": M}, "value": "..."}` with volume/page present on ~50% of moro references (6,220 of 12,438). The field is documented in the upstream TypeScript type definitions (`Kanjidic2DictionaryReferenceMorohashi`). Our `kanji.schema.json` records `dic_refs` as a flat string map, so only the value is preserved. This is our schema simplification, not an upstream gap.
**Proposed fix (internal)**: Add optional `dic_refs.moro_volume` and `dic_refs.moro_page` fields, or restructure `dic_refs.moro` as an object. Minor-version schema bump.
**Status**: pending (internal) — deferred; low priority unless a consumer needs full Morohashi references
**Discovered during**: Phase 1 kanjidic2 structure inspection

---

## Drafted (retracted)

Issues #36 and #37 were filed on 2026-04-12 against scriptin/jmdict-simplified, then retracted and closed on 2026-04-13 after investigation revealed both were based on our failure to read the upstream project's existing documentation and data.

- **#36** asked for `skipMisclassification` documentation — but the field was already documented in the upstream TypeScript type definitions (`Kanjidic2QueryCodeSkip`).
- **#37** asked for Morohashi volume/page exposure — but the `morohashi` sub-object with `{volume, page}` was already present in the JSON output. We didn't look at the data.

Both are our schema simplifications (we flatten to string maps), not upstream gaps. Draft text removed.

---

## Filed

_(Nothing currently filed. Issues #36 and #37 on scriptin/jmdict-simplified were retracted — see "Drafted (retracted)" above.)_

---

## Resolved

_(Nothing resolved yet.)_

---

## Archived

_(Nothing archived yet.)_
