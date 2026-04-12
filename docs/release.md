# Release workflow

How to cut a release. This document exists because the version number, build date, release summary, and data files all need to stay in sync, and historically they drifted — `manifest.json` sat at `v0.4.1` for five version bumps while the `CHANGELOG.md` reached `v0.7.1`.

The workflow below single-sources every release-time fact through the `CHANGELOG.md` top entry. Automated checks catch drift; humans make the narrative decisions.

---

## What counts as a release

Any tag matching `v<N>.<N>.<N>` is a release. The rules, from `docs/architecture.md`:

- **PATCH**: upstream source refresh, bug fix, documentation correction, minor data addition
- **MINOR**: new data file, new field, new source, new cross-reference
- **MAJOR**: schema-breaking change

Every release gets a dedicated `[N.N.N]` section in `CHANGELOG.md` with a date and a human-written summary of what changed.

---

## The invariants

Enforced by tests in `tests/test_docs.py`:

- `manifest.json.version` equals the most-recent `## [N.N.N]` header in `CHANGELOG.md`
- `manifest.json.phase_description` is ≤600 characters (forces freshness — stale descriptions tend to accumulate)
- Every git tag `vN.N.N` has a matching `CHANGELOG.md` entry
- `manifest.json.counts` matches reality for every file it references (refreshed by `just stats`)

If any invariant drifts, `just test` fails with a clear message pointing at the offending file.

---

## The steps

### 0. Make sure the working tree is in the state you want to ship

```bash
git status                  # should be clean
.venv/bin/python -m pytest tests/ -v   # 62+ passing
just build                  # data files regenerated
just stats                  # counts refreshed in manifest.json
```

### 1. Draft the CHANGELOG entry

Edit `CHANGELOG.md`. Add a new section at the top of the `[Unreleased]` block:

```markdown
## [0.8.0] — 2026-05-01

<one-paragraph release summary>

### Added
- ...

### Changed
- ...

### Fixed
- ...

### Verification
- 62/62 tests pass
- N data files validate against their schemas
```

The date should be today. The body should explain *what* changed and *why*.

### 2. Reconcile `manifest.json`

```bash
just bump-release-dry-run    # shows the diff without writing
just bump-release            # writes the changes
```

This reads the top CHANGELOG version and updates:

- `manifest.json.version` to match
- `manifest.json.generated` to match the CHANGELOG date (or today if the date is missing)

It explicitly does NOT touch `phase_description`. If the bump recipe detects that `phase_description` still mentions the old version, it prints a warning; rewrite the field manually to describe the new state.

### 3. Update `phase_description` if the release changes the project's "current state" narrative

Open `manifest.json` and edit `phase_description`. Keep it under 600 characters. A good one:

- Opens with "Phase N active." (or the current phase)
- Summarizes the most recent content additions, with version numbers
- Flags the single biggest remaining gap
- Points at `docs/phase4-candidates.md` and `CHANGELOG.md`

### 4. Update any other status-line references

Files with "current state" prose that tends to drift:

- `README.md` line ~5 — the Status line under the project title
- `docs/phase4-candidates.md` — any "ADDRESSED (vX.Y.Z)" entries that changed
- `docs/sources.md` — coverage percentages
- `ATTRIBUTION.md` — coverage percentages

The `tests/test_docs.py::test_no_stale_radical_coverage_claim` guard catches the most common drift (the "197 of 253 radicals (77.9%)" incident that originally motivated this document). Other staleness has no automated catcher; grep for the old version number before tagging.

### 5. Rebuild, validate, test

```bash
just build && just validate && just stats && just test
```

All three should pass clean. If `just test` flags a drift (version mismatch, phase_description too long, tag without CHANGELOG), fix it and re-run.

### 6. Commit

```bash
git add -p  # review each change individually
git commit -m "chore(release): bump to v0.8.0"
```

Use a commit message that reflects the substance of the release, not just the version number, if the release is substantive. For a pure version bump with no content changes, `chore(release): bump to v0.8.0` is fine.

### 7. Tag and push

```bash
git tag -a v0.8.0 -m "Release v0.8.0"
git push origin main
git push origin v0.8.0
```

CI should go green on the tag push. If it doesn't, investigate before assuming the release is good.

### 8. Announce (if applicable)

For notable releases, update the GitHub Releases page with the CHANGELOG body copy-pasted in. For patch releases that are purely upstream refreshes, CI going green is sufficient.

---

## What the drift-prevention tests actually check

```python
# tests/test_docs.py

test_manifest_version_matches_changelog
    # manifest.json.version is the most-recent [N.N.N] in CHANGELOG.md

test_manifest_phase_description_length_cap
    # manifest.json.phase_description is ≤600 characters

test_manifest_counts_match_reality
    # For every file in manifest.counts that exists, the count is current

test_every_git_tag_has_changelog_entry
    # Every v<N>.<N>.<N> git tag has a matching [N.N.N] header

test_changelog_headers_have_dates
    # Every [N.N.N] header has a YYYY-MM-DD date
```

These run on every `just test` invocation and in CI. They are intentionally cheap (no network, no build) so they run fast and fail early.

---

## If you want to revert a mistake

If you tagged a release and want to unreleased it:

```bash
git tag -d vX.Y.Z          # local delete
git push origin :vX.Y.Z    # remote delete — risky, coordinate with team
```

Then in `CHANGELOG.md`, move the section back under `[Unreleased]` and run `just bump-release` again (or manually revert `manifest.json.version`). Do NOT do this for any release that has been publicly announced or consumed by downstream users — issue a patch release instead that fixes the mistake.

---

## See also

- `docs/architecture.md` — the design principles and versioning policy
- `CHANGELOG.md` — the source of truth for release history
- `build/bump_release.py` — the implementation backing `just bump-release`
- `tests/test_docs.py` — the drift-prevention tests
