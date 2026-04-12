<!--
Thanks for contributing to japanese-language-data!

Before submitting, please check:
  - [ ] Your change follows the project's architecture (see docs/architecture.md)
  - [ ] `just build` passes
  - [ ] `just validate` passes
  - [ ] `just test` passes
  - [ ] `just ci` passes end-to-end and leaves git status clean
  - [ ] CHANGELOG.md has a new bullet under [Unreleased] explaining the why
  - [ ] No content from copyright-incompatible sources (Tae Kim, DoBJG, Handbook of JGP, WaniKani, etc.) — see docs/contributing.md
-->

## Summary

<!-- One or two sentences on what this PR does and why. -->

## Change type

- [ ] Data correction (fix an error in existing data)
- [ ] Grammar curation (new or updated entries in `grammar-curated/`)
- [ ] New upstream source (build/fetch.py pinned + transformer + schema)
- [ ] Schema change (requires docs/architecture.md "Versioning within the schema" note)
- [ ] Pipeline / transformer change (code in `build/`)
- [ ] Test addition or fix
- [ ] Documentation
- [ ] Build / CI
- [ ] Other:

## Files touched

<!-- A brief list of the most significant files, especially any new files. -->

## Verification

- [ ] `just build` succeeds
- [ ] `just validate` — 19/19 data files validate
- [ ] `just test` — all tests pass (count: )
- [ ] `just ci` — end-to-end, leaves git status clean (byte-reproducibility)
- [ ] `manifest.json.counts` accurate for any file-count changes
- [ ] `CHANGELOG.md` entry added under `[Unreleased]`

## License and provenance

- [ ] No content copied from CC-BY-NC, CC-BY-ND, or proprietary grammar references
- [ ] New upstream sources (if any) are CC-BY-SA 4.0 compatible and SHA256-pinned in `build/fetch.py`
- [ ] New data files carry a `metadata` block with source, license, and `field_notes`

## For grammar curation PRs

- [ ] New entries have `review_status: "draft"`
- [ ] Examples are `source: "original"` (or `"tatoeba"` with a real `sentence_id`)
- [ ] `related` cross-references resolve (the build will hard-fail otherwise)
- [ ] `sources` field uses the canonical string `"General Japanese grammar knowledge (non-copyrightable facts)."` — not copied from copyrighted references

## For grammar review PRs

<!--
Fill this in if your PR updates `review_status` on any grammar entry.
See docs/grammar-review.md for the full workflow and
docs/grammar-review-checklist.md for the per-entry checks.
-->

- [ ] I have read `docs/grammar-review.md` and `docs/grammar-review-checklist.md`
- [ ] My `reviewer_notes` entries follow the required format (`reviewer`, `date`, `note`)
- [ ] I used the appropriate review track (`community_reviewed` vs `native_speaker_reviewed`)
- [ ] I did not downgrade any prior review status
- [ ] `just test` passes locally — including `test_grammar_review_status_state_machine`

**Slice reviewed**:

<!-- Which slice did you cover? E.g., "n5.json entries 1–20" or "all sparse_examples outliers" -->

**Per-entry breakdown**:

| Status change | Count |
|---|---:|
| `draft` → `native_speaker_reviewed` | |
| `draft` → `community_reviewed` | |
| `draft` → `draft` (reviewed but flagged for rewrite) | |
| `draft` → `draft` (reviewed but not yet decided) | |

**Substantive findings** (if any):

<!--
Any cross-cutting observations: patterns of errors, systemic issues,
stylistic suggestions for the dataset as a whole. The author will use
these to open follow-up issues if needed.
-->

**Reviewer credit preference**:

- [ ] Real name in `reviewer_notes.reviewer` (specify): _____
- [ ] GitHub handle in `reviewer_notes.reviewer` (specify): _____
- [ ] Pseudonym in `reviewer_notes.reviewer` (specify): _____
- [ ] Anonymous — do not credit in README
- [ ] Credit in README's Reviewers section (name/handle): _____

## For schema changes

- [ ] Bumped `schemaVersion` in the affected schema file
- [ ] Updated `docs/architecture.md` if the change is structural
- [ ] Downstream consumers that key on `schemaVersion` will see the change

## Breaking changes

<!-- Any breaking changes for consumers? If yes, describe migration. -->

## Related issues

Closes # /  Refs #
