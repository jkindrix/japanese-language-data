# Contributing

Thank you for considering contributing to the Japanese Language Data project. This document describes the kinds of contributions welcomed, how to make them, the standards we hold contributions to, and the specific areas where help is urgently needed.

Before reading anything else, please review:

- `README.md` for what this project is and is not
- `LICENSE` for the licensing under which contributions are accepted
- `docs/architecture.md` for the design principles
- `docs/gaps.md` for what we don't currently cover

By submitting a contribution, you agree that your contribution will be released under the same CC-BY-SA 4.0 license as the rest of the dataset.

---

## Urgent needs

### Native-speaker reviewers for grammar

The grammar dataset (Phase 3) is our largest original contribution and the area where we most need help. Entries in `data/grammar/grammar.json` carry a `review_status` field with these values:

- `draft` — written by the project author from English sources; not reviewed
- `community_reviewed` — checked by at least one community contributor who is not the original author
- `native_speaker_reviewed` — confirmed by a native Japanese speaker with teaching or linguistic background

At the time of any pre-1.0 release, most entries will be `draft`. The goal is for 1.0 to have all N5 and N4 entries at `native_speaker_reviewed`. **We need native-speaker reviewers to close this gap.**

If you are a native Japanese speaker (or a near-native equivalent with formal linguistic training) and are willing to review grammar entries, please open an issue titled `grammar-review: available` and let us know:

- Your background relevant to Japanese linguistics or language teaching
- How many entries per month you're willing to review
- Whether you want to review all levels or specific JLPT levels

Grammar review consists of reading an entry, checking the formation rule, checking the English explanation against your intuition, checking the example sentences for naturalness, and confirming or correcting the nuance/usage notes. A reviewer does not need to write original content.

### Error reports for existing upstream data

If you spot an error in any of our data that can be traced back to an upstream source (most of it), please report it:

- For typos, wrong readings, wrong meanings, wrong stroke counts, etc., in kanji/words/names data: the upstream is EDRDG. We will file these upstream at the end of each phase and track them in `docs/upstream-issues.md`.
- For wrong stroke order: upstream is KanjiVG.
- For wrong pitch accent: upstream is Kanjium.
- For wrong JLPT classification: upstream is Waller (tanos.co.uk).
- For wrong example sentence or translation: upstream is Tatoeba or the JMdict editor selection.

Filing with us is fine — we'll triage and file upstream. Include:

- The entry ID or lookup key
- What's wrong
- What it should be
- A source or reference supporting the correction

---

## Ways to contribute

### Data contributions

- **Original grammar curation** for Phase 3 (N3, N2, N1 levels, which are not prioritized for v1.0)
- **Example sentences** for grammar points, if you can provide natural Japanese sentences with attribution (Tatoeba contribution is preferred — we'll pull from upstream — but curated examples specific to grammar teaching are welcome)
- **Kana chart extensions** (e.g., obsolete kana, historical forms if relevant)
- **Cross-reference additions** — new kinds of cross-references that would be useful

### Code contributions

- **New upstream source integrations** — if you find a high-value source we're missing, propose it as a Phase 4 candidate (see `docs/phase4-candidates.md`) or, for smaller additions, submit a transform module directly
- **Pipeline improvements** — performance, reliability, error reporting, build time reduction
- **Schema improvements** — where the current schema can't represent a legitimate data pattern
- **Test coverage** — schema validation tests, transformation unit tests, integration tests
- **Build reproducibility improvements** — anything that makes `just build` more deterministic or debuggable

### Documentation contributions

- **Clarifications** to any document that was confusing
- **Examples** of how to consume the dataset in code (these might go in a new `docs/cookbook.md`)
- **Translation** of documentation into other languages

### Review contributions

- **Schema review** — catching edge cases we haven't modeled
- **License audit** — verifying our attribution meets upstream requirements
- **Data spot-checks** — randomly sampling entries and verifying correctness

---

## Workflow

1. **Discuss first for substantive changes.** If you're proposing a new feature, a new data source, a schema change, or any change that affects more than a handful of lines, open an issue first. This saves your time if the proposal would be rejected.
2. **Fork the repo.**
3. **Create a branch** named with a short descriptor, e.g., `grammar-N5-batch-3` or `fix-radical-mapping-for-亻`.
4. **Make changes.** Follow the style conventions below.
5. **Run the full pipeline** locally before submitting: `just fetch && just build && just validate && just stats`. Your changes should not introduce validation failures.
6. **Run tests**: `just test`.
7. **Commit** with conventional-commits style prefixes:
   - `feat:` new features, new data, new fields
   - `fix:` bug fixes, error corrections
   - `docs:` documentation only
   - `refactor:` code restructuring with no behavior change
   - `test:` test additions or changes
   - `chore:` tooling, build, dependencies, upstream pin bumps
8. **Push your branch and open a pull request.** Reference any issue it closes.

---

## Style conventions

### JSON

- Pretty-printed, 2-space indentation.
- `ensure_ascii=False` — UTF-8 native (no `\u` escapes for Japanese characters).
- Keys in lowercase snake_case.
- Arrays preferred over null for "empty list" semantics.
- Omit fields rather than including them with null values, except where the schema requires explicit null.

### Python

- Standard library preferred over third-party where practical.
- Type hints on all public functions.
- Docstrings on every module and every non-trivial function.
- 4-space indentation (PEP 8).
- Line length soft limit 100, hard limit 120.
- `from __future__ import annotations` at the top of every module for forward-reference-safe typing.

### Markdown

- GitHub-flavored.
- Headers use `#` not `===` or `---`.
- Line length: soft-wrap at reading comfort (~100 chars), hard-wrap never.
- Code blocks should have language identifiers.
- Internal links use relative paths.

### Commits

- Short descriptive subject line (50 chars soft, 72 hard)
- Blank line
- Body explaining the *why*, not the *what*
- Reference issues with `#NNN` if applicable
- Imperative mood: "add grammar entry for particle を", not "added" or "adds"

### Branches and pull requests

- Branches are named `<type>/<short-description>` where type is `feat`, `fix`, `docs`, etc.
- Pull requests reference the issue they close, summarize the changes, and describe how to test.
- PRs that touch multiple data domains should be split into domain-specific PRs where reasonable.

---

## Review standards

All data contributions should meet at minimum:

1. **Sourced**: Every claim has a citation to an upstream source, a published reference, or a clearly-marked-as-original curation flag.
2. **Schema-valid**: Passes `just validate` without errors.
3. **Diffable**: New or changed entries are visible in the git diff and can be reviewed line-by-line.
4. **Consistent**: Matches existing entries in style, formatting, and field usage.
5. **Non-redundant**: Doesn't duplicate information already in the file or cross-references.

Code contributions additionally need:

1. **Reproducible**: Running the code twice from a clean checkout produces identical output.
2. **No silent state**: No mutable globals, no filesystem writes outside the documented output paths, no network I/O outside `fetch.py`.
3. **Failure-loud**: Errors surface immediately with clear messages, rather than being silently swallowed.
4. **Tested**: New logic has corresponding tests in `tests/`.

Documentation contributions need:

1. **Accurate**: No claims we can't back up
2. **Matched style**: Consistent with the rest of the documentation

---

## What we will not accept

- Contributions under incompatible licenses (proprietary data, copyleft other than CC-BY-SA 4.0-compatible, or license-unclear data)
- Changes that break the schema without a corresponding version bump and changelog entry
- Changes that add features not discussed in an issue first
- Changes that silently remove attribution or credit
- Additions of languages other than Japanese (this is a Japanese dataset; multilingual coverage is specifically out of scope)
- Dependencies on third-party web services during the build (build must be reproducible from cached `sources/`)
- Large binary files committed to git (use external storage if needed)

---

## Code of conduct

Be kind. Assume good faith. Disagreements about data or technical approaches are fine and expected — disagreements about people are not. This project exists because people spent decades volunteering to make Japanese learning data open; carry that spirit forward.

If you see behavior that violates this, contact the project owner directly.

---

## Contact

- **Issues**: GitHub issues for anything public
- **Project owner**: Justin Kindrix
- **Urgent or private**: See repository settings for contact information

Thank you for contributing.
