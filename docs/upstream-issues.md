# Upstream issues log

This file tracks errors, gaps, and improvement suggestions discovered in upstream sources during this project's build phases. Items here are batched and filed upstream at the end of each phase, per the upstream contribution workflow described in `docs/architecture.md`.

## Phase 1–4 filing status (as of v0.4.0, 2026-04-11)

**Zero items have been filed to any upstream through Phase 4.** Honest accounting:

- **Phase 1 (core ingestion, v0.1.0)**: No substantive upstream defects identified. JMdict, KANJIDIC2, KRADFILE, and RADKFILE all parsed cleanly. Two internal schema gaps were discovered during kanjidic2 inspection (`skipMisclassification` and `morohashi` volume/page detail) — these are tracked in "Pending" below but are *our* schema gaps, not upstream defects, so there is nothing to file.
- **Phase 2 (enrichment, v0.2.0)**: No substantive upstream defects identified. Kanjium's `accents.txt` parsed cleanly. KanjiVG stroke counts differ from KANJIDIC2 for 109 characters (documented in `stroke-order-index.json` metadata.stroke_count_mismatches), but this is a known methodology difference (KanjiVG counts path elements; KANJIDIC2 gives canonical counts) rather than a defect — both sources are internally consistent.
- **Phase 3 (grammar, v0.3.0)**: No upstream interactions; grammar content is hand-curated from general knowledge. 6.6% of Waller vocab entries were initially misdescribed as "JMdict ID drift" in v0.2.0 CHANGELOG; this was corrected in v0.3.1 to reflect the actual cause (common-subset filtering). The correction was internal; nothing upstream to file.
- **Phase 4 (Wikipedia, v0.4.0)**: No substantive upstream defects identified in the Wikipedia Kangxi radicals article. 56 of 253 RADKFILE radicals do not appear in Wikipedia's Kangxi table, but this is a scope difference (Wikipedia covers the 214 classical radicals; RADKFILE includes ~40 Japanese dictionary variants) rather than an upstream defect.

**Design Principle 6 assessment**: the principle ("upstream contribution as ongoing obligation") is aspirational in practice during Phases 1–4. The rigorous defect-fix cycles occurred against *this project's* outputs and schemas, not against upstream data. If substantive upstream defects are discovered during future phases or user reports, they will be filed and tracked in this log. The principle is maintained as an ethical commitment even when there is nothing concrete to file.

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

## Pending

### [2026-04-11] our-schema: skipMisclassification field not captured in kanji query_codes

**Entry**: Applies to any kanji with a non-null `skipMisclassification` on a SKIP query code in KANJIDIC2.
**Issue**: The upstream KANJIDIC2 marks known SKIP code miscodings via `skipMisclassification` on some `queryCodes` entries (e.g., a SKIP code with `"skipMisclassification": "posn"` indicates the code follows a position-based misclassification). Our `kanji.schema.json` captures SKIP as a flat string and loses this nuance.
**Proposed fix**: Extend the schema's `query_codes.skip` field to optionally be an object `{value, misclassification}` instead of a bare string, or add a separate `query_codes.skip_misclassification` field. Minor-version schema bump.
**Status**: pending
**Filed**: not yet (this is an internal schema gap, not an upstream issue — tracked here for visibility)
**Discovered during**: Phase 1 kanjidic2 structure inspection

### [2026-04-11] our-schema: morohashi dictionary reference loses volume/page

**Entry**: Applies to any kanji with a `"type": "moro"` dictionary reference in KANJIDIC2.
**Issue**: The upstream structure is `{"type": "moro", "morohashi": {"volume": N, "page": M}, "value": "..."}`. Our `kanji.schema.json` records `dic_refs` as a flat string map, so only the value is preserved. Volume and page numbers are lost.
**Proposed fix**: Add an optional `dic_refs.moro_volume` and `dic_refs.moro_page` field, or restructure `dic_refs.moro` as an object. Minor-version schema bump.
**Status**: pending
**Filed**: not yet (internal schema gap)
**Discovered during**: Phase 1 kanjidic2 structure inspection

---

## Filed

_(Nothing filed yet.)_

---

## Resolved

_(Nothing resolved yet.)_

---

## Archived

_(Nothing archived yet.)_
