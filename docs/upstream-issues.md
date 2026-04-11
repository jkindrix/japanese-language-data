# Upstream issues log

This file tracks errors, gaps, and improvement suggestions discovered in upstream sources during this project's build phases. Items here are batched and filed upstream at the end of each phase, per the upstream contribution workflow described in `docs/architecture.md`.

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
