# Build guide

How to rebuild the Japanese Language Data dataset from a clean clone. This document is for contributors and for anyone who wants to verify that the published dataset matches what the current pipeline produces from current upstream sources.

---

## Prerequisites

- **Python 3.10+** (tested on 3.11)
- **git 2.30+**
- **just 1.14+** (https://github.com/casey/just)
- **curl** or **wget** for downloading upstream sources
- **~2 GB free disk space** (for cached sources and built data)
- **An internet connection** (for the initial fetch)

No JVM, no Gradle, no Node.js, no Docker, no databases. The entire pipeline is Python plus `curl`.

---

## First-time setup

```bash
# Clone the repository
git clone https://github.com/jkindrix/japanese-language-data.git
cd japanese-language-data

# Create a Python virtual environment
python3 -m venv .venv
. .venv/bin/activate

# Install pipeline dependencies
pip install -r build/requirements.txt
```

You should see a small number of packages install: `requests`, `jsonschema`, `pytest`, and any transitive dependencies.

---

## The build pipeline

The pipeline is a sequence of stages, each available as a `just` recipe. Running `just` with no arguments lists every available recipe. Running `just build` executes the full pipeline.

### Stage 1: Fetch upstream sources

```bash
just fetch
```

This downloads every upstream source pinned in `build/fetch.py` into the `sources/` directory and verifies the SHA256 hash of each. If a file is already cached and its hash matches the pin, it is not re-downloaded. If a hash mismatch is detected, the build aborts with an error — this means either the upstream source has been updated (and a deliberate pin bump is needed) or the cached file is corrupted.

Expected total download: ~30 MB compressed across all sources.

Expected elapsed time: 1–3 minutes on a typical broadband connection for first fetch; instant on subsequent runs when cache is valid.

### Stage 2: Transform

```bash
just build
```

This runs every transformation module in the correct order. Each module reads its inputs from `sources/`, emits JSON files to `data/`, and adds a metadata header crediting upstream sources.

The order is:

1. Core data: `kana`, `kanji`, `words`, `radicals`, `sentences`
2. Names (if `just build-names` is used, or `--with-names` flag is set)
3. Enrichment: `stroke_order`, `pitch`, `frequency`, `jlpt`
4. Cross-references: generated last, after all core and enrichment data is available

Expected elapsed time: 2–5 minutes on a typical laptop for the core build; an additional 1–2 minutes if names are included.

### Stage 3: Validate

```bash
just validate
```

This runs every built file against its schema in `schemas/`. Any validation error fails the build with the specific entry and field highlighted. A valid build produces no output.

In practice, `just build` runs validation automatically at the end of each transform, so `just validate` is useful primarily when you want to re-check existing outputs without re-running the transforms.

### Stage 4: Stats

```bash
just stats
```

Prints a coverage and count report:

- Number of entries per file
- Percentage of kanji with stroke-order SVGs
- Percentage of words with pitch accent data
- Percentage of words with frequency data
- Percentage of words with JLPT classification
- Percentage of grammar points at each review status
- Total built file size

Also updates `manifest.json` with the current counts and build date.

### Stage 5: Test

```bash
just test
```

Runs the test suite in `tests/`. This is independent of the build pipeline — tests run against the committed schemas and small fixture data, not against the full built dataset. Use this to verify schema changes or transformation logic without rebuilding.

---

## Common workflows

### "I just want to rebuild from scratch"

```bash
just clean       # remove everything in data/ that's not .gitkeep
just fetch       # re-fetch or verify sources
just build       # rebuild everything
just stats       # verify counts
```

### "I changed a transformation module"

```bash
just build       # re-run transforms (fetch is cached)
just validate    # ensure schema compliance
just stats       # verify counts didn't change unexpectedly
just test        # run unit tests for the module
```

### "I want to upgrade an upstream source"

```bash
# Edit build/fetch.py to update the URL and/or version string
# Delete the cached copy:
rm -f sources/<name>/*

# Re-fetch and observe the new hash:
just fetch
# The build will fail because manifest.json still has the old hash

# Update manifest.json with the new hash (the build error will print it)
# Re-run
just fetch && just build && just validate && just stats

# Check the git diff to see what changed in the data
git diff data/

# Commit the upgrade
git add build/fetch.py manifest.json data/ CHANGELOG.md
git commit -m "chore: bump <source> to <new version>"
```

### "I want to build with JMnedict included"

```bash
just build-names
```

This runs the standard `just build` and additionally builds `data/optional/names.json`. The output is gitignored by default.

### "The build failed — what now?"

1. **Hash mismatch** during fetch: an upstream source has been updated. Decide whether to pin-bump (see above) or wait for a stable release.
2. **Schema validation failure**: the output doesn't match the schema. Either the transform logic is wrong (fix the transform) or the schema is wrong (fix the schema). Do not suppress the validation error.
3. **Transform error**: read the stack trace. The error will identify which source file and which entry caused the failure. Common causes: upstream data format changed, upstream added new fields we don't handle, upstream has a malformed entry that needs to be skipped with a warning.
4. **Test failure**: the test will point to the expected vs. actual discrepancy. Investigate whether the test is wrong or the code is wrong.

For any failure you cannot diagnose, open an issue with the full error output.

---

## Reproducibility guarantees

From a clean clone, running:

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r build/requirements.txt
just fetch
just build
```

...should produce a `data/` directory whose every file matches the committed version byte-for-byte, provided that:

- The upstream source URLs are still reachable AND serve the same content at the pinned hashes
- The Python version and standard library behave identically (unlikely to cause differences in our case)

If this ever fails, it is a reproducibility bug and should be reported as an issue. In practice, the only reason for failure is upstream sources going away — in which case we will need to mirror them to our own release artifacts.

---

## Python environment details

### Why venv and not poetry/pdm/uv?

Simplicity. The venv + requirements.txt approach has zero extra tooling, works on every Python installation, and has been stable for over a decade. Contributors don't need to install anything beyond Python and pip.

If a specific situation emerges where a more sophisticated dependency manager is needed (e.g., dev dependencies vs. runtime dependencies with lock files), we may revisit this decision. For now, simple is better.

### Required packages

See `build/requirements.txt` for the authoritative list. Current runtime dependencies are:

- `requests` — HTTP downloads in `fetch.py`
- `jsonschema` — schema validation in `validate.py`

Development/test dependencies:

- `pytest` — test runner

All are pinned to specific versions in `build/requirements.txt` for reproducibility.

---

## Disk space

Approximate disk usage after a complete build:

- `sources/` — ~50 MB (cached compressed downloads)
- `data/core/` — ~150 MB (words and kanji are the biggest)
- `data/enrichment/` — ~30 MB (stroke order SVGs are the biggest)
- `data/corpus/` — ~20 MB (sentences)
- `data/grammar/` — ~5 MB (sparse until Phase 3 fills in)
- `data/cross-refs/` — ~10 MB
- `data/optional/names.json` (if built) — ~150 MB

Total committed data: ~200 MB. Total with sources and optional: ~400 MB. Well within any modern system.

---

## What if I want to fork and customize?

Go ahead. The whole project is CC-BY-SA 4.0 and the pipeline is deliberately simple to modify:

- **To drop a source**: remove its entries from `build/fetch.py` and its transform module
- **To add a source**: add fetch entries, write a transform module, add a schema, register it in `build/pipeline.py`
- **To change a schema**: edit `schemas/<name>.schema.json`, update transforms, bump schema version
- **To add a language** (e.g., Japanese-German focus): switch `jmdict-eng` to `jmdict-ger` in `fetch.py`, adjust transforms
- **To change output format** (e.g., emit Parquet instead of JSON): write a new transform stage that reads our JSON and emits the target format

Forks must preserve the attribution and license per CC-BY-SA 4.0, but beyond that, customize freely.
