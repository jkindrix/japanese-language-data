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
- [ ] `sources` field honestly cites "General Japanese grammar knowledge" — not copied from copyrighted references

## For schema changes

- [ ] Bumped `schemaVersion` in the affected schema file
- [ ] Updated `docs/architecture.md` if the change is structural
- [ ] Downstream consumers that key on `schemaVersion` will see the change

## Breaking changes

<!-- Any breaking changes for consumers? If yes, describe migration. -->

## Related issues

Closes # /  Refs #
