# Upstream issues log

This file tracks errors, gaps, and improvement suggestions discovered in upstream sources during this project's build phases. Items here are batched and filed upstream at the end of each phase, per the upstream contribution workflow described in `docs/architecture.md`.

## Phase 1–4 filing status (as of v0.7.1, 2026-04-12)

**Zero *defect* items have been filed to any upstream through Phase 4, because no substantive upstream defects have been identified.** Two *feature requests* targeting `scriptin/jmdict-simplified` have been drafted and are queued in "Drafted, pending-decision-to-file" below — they are schema exposure requests, not defect reports.

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

## Pending (internal schema gaps — drafted upstream text below)

### [2026-04-11] our-schema: skipMisclassification field not captured in kanji query_codes

**Entry**: Applies to any kanji with a non-null `skipMisclassification` on a SKIP query code in KANJIDIC2.
**Issue**: The upstream KANJIDIC2 marks known SKIP code miscodings via `skipMisclassification` on some `queryCodes` entries (e.g., a SKIP code with `"skipMisclassification": "posn"` indicates the code follows a position-based misclassification). Our `kanji.schema.json` captures SKIP as a flat string and loses this nuance.
**Proposed fix (internal)**: Extend the schema's `query_codes.skip` field to optionally be an object `{value, misclassification}` instead of a bare string, or add a separate `query_codes.skip_misclassification` field. Minor-version schema bump.
**Status**: pending (internal)
**Filed**: see drafted text below
**Discovered during**: Phase 1 kanjidic2 structure inspection

### [2026-04-11] our-schema: morohashi dictionary reference loses volume/page

**Entry**: Applies to any kanji with a `"type": "moro"` dictionary reference in KANJIDIC2.
**Issue**: The upstream structure is `{"type": "moro", "morohashi": {"volume": N, "page": M}, "value": "..."}`. Our `kanji.schema.json` records `dic_refs` as a flat string map, so only the value is preserved. Volume and page numbers are lost.
**Proposed fix (internal)**: Add an optional `dic_refs.moro_volume` and `dic_refs.moro_page` field, or restructure `dic_refs.moro` as an object. Minor-version schema bump.
**Status**: pending (internal)
**Filed**: see drafted text below
**Discovered during**: Phase 1 kanjidic2 structure inspection

---

## Drafted, pending-decision-to-file

These are pre-written GitHub issue bodies targeting `scriptin/jmdict-simplified`. They are feature requests asking the upstream to consider documenting or exposing existing fields more prominently. The project owner can copy-paste either one into a new GitHub issue at https://github.com/scriptin/jmdict-simplified/issues when ready; the decision to file has been deferred because (a) the information is not *missing* upstream, only *shaped* in a way our schema does not round-trip, and (b) the upstream is a single-maintainer project and we want to be courteous about volume of open issues.

These are the first Principle 6 drafts. Filing them is discretionary.

### Draft A — `skipMisclassification` documentation

**Target repo**: `scriptin/jmdict-simplified`
**Target issue title**: `[docs] Field reference for queryCodes[].skipMisclassification`
**Labels** (suggested): `documentation`, `kanjidic2`

**Body**:

> Hi! First, thanks for jmdict-simplified — we ingest it for the Japanese Language Data project (https://github.com/jkindrix/japanese-language-data) and it has been the single biggest shortcut in our pipeline.
>
> While inspecting the KANJIDIC2 JSON output, we noticed that `queryCodes[]` entries of `type: "skip"` sometimes carry a `skipMisclassification` field with values like `"posn"`, `"stroke_count"`, etc. We do not see this field documented in the jmdict-simplified schema/README, and it took a bit of digging to understand that it corresponds to Jack Halpern's SKIP-code known-miscoding annotations in the upstream XML (`<q_code skip_misclass="...">`).
>
> Would you consider adding a sentence to the README or type docs explaining what the field means and when it appears? We would be happy to submit a PR if that would be helpful — we just want to make sure the field is documented as an intentional part of the JSON shape rather than a pass-through we might accidentally lose in our own schema.
>
> For reference, the upstream XML documentation is at https://www.edrdg.org/kanjidic/kanjidic2_dtdh.html (under `q_code`).
>
> Thanks again.

### Draft B — Morohashi volume/page exposure

**Target repo**: `scriptin/jmdict-simplified`
**Target issue title**: `[enhancement?] Expose morohashi volume/page in dictionaryReferences[type=moro]`
**Labels** (suggested): `kanjidic2`, `enhancement`

**Body**:

> Hi! Another small one from downstream (https://github.com/jkindrix/japanese-language-data).
>
> The Morohashi Daikanwa index (`<dic_ref dr_type="moro" m_vol="..." m_page="...">`) appears in the KANJIDIC2 XML with volume and page metadata in addition to the entry number. In the jmdict-simplified JSON output we see the `value` field but not the volume/page detail. Looking at the transform code briefly, it seems like the volume/page may already be parsed but collapsed into the primary value — please correct me if I am misreading.
>
> Would you consider exposing `morohashi_volume` and `morohashi_page` as separate fields on the `dictionaryReferences[]` entry for `type: "moro"`? Our use case is joining kanji to the full Morohashi reference (a scholarly dictionary), and losing the volume/page means consumers can't do that join without going back to the XML.
>
> If this is not worth the scope expansion in your schema, no problem at all — we can parse the raw XML ourselves for the handful of consumers who want this. Filing in case it is an easy win for future users.
>
> Thanks for the project!

---

## Filed

_(Nothing filed yet.)_

---

## Resolved

_(Nothing resolved yet.)_

---

## Archived

_(Nothing archived yet.)_
