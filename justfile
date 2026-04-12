# ============================================================================
# JAPANESE LANGUAGE DATA — Build recipes
# ============================================================================
#
# Usage:
#   just              Show available recipes
#   just fetch        Download upstream sources
#   just build        Run the full pipeline
#   just validate     Schema-check every built data file
#   just stats        Print counts and coverage
#   just test         Run the test suite
#   just clean        Remove built data files (keeps sources/ cache)
#   just clean-all    Remove built data AND sources/ cache
#
# Requirements:
#   - Python 3.10+ (tested on 3.11)
#   - venv created and activated:
#       python3 -m venv .venv && . .venv/bin/activate
#       pip install -r build/requirements.txt
#
# ============================================================================

set shell := ["bash", "-euo", "pipefail", "-c"]

# ANSI colors
bold   := '\033[1m'
cyan   := '\033[0;36m'
green  := '\033[0;32m'
yellow := '\033[0;33m'
red    := '\033[0;31m'
reset  := '\033[0m'

# Python invocation — use venv if present, else system
python := if path_exists(".venv/bin/python") == "true" { ".venv/bin/python" } else { "python3" }

# ============================================================================
# HELP
# ============================================================================

# Show available recipes
[group('help')]
default:
    @just --list

# ============================================================================
# BUILD PIPELINE
# ============================================================================

# Download upstream sources into sources/ (with hash verification)
[group('build')]
fetch:
    @printf '{{cyan}}==> Fetching upstream sources{{reset}}\n'
    {{python}} -m build.fetch

# Run the full build pipeline (fetch → transform → validate → cross-link → stats)
[group('build')]
build:
    @printf '{{cyan}}==> Building dataset{{reset}}\n'
    {{python}} -m build.pipeline
    @just validate
    @just stats

# Run the full build including JMnedict names (gitignored output)
[group('build')]
build-names:
    @printf '{{cyan}}==> Building dataset with JMnedict names{{reset}}\n'
    {{python}} -m build.pipeline --with-names
    @just validate
    @just stats

# Preview what the pipeline would do without running it
[group('build')]
dry-run:
    {{python}} -m build.pipeline --dry-run

# Run a specific stage only (e.g., just run-stage kanji)
[group('build')]
run-stage STAGE:
    {{python}} -m build.pipeline --only {{STAGE}}

# ============================================================================
# VALIDATION & REPORTING
# ============================================================================

# Schema-validate every data file
[group('validate')]
validate:
    @printf '{{cyan}}==> Validating data files against schemas{{reset}}\n'
    {{python}} -m build.validate

# Print entry counts and coverage stats; updates manifest.json
[group('validate')]
stats:
    @printf '{{cyan}}==> Computing stats{{reset}}\n'
    {{python}} -m build.stats

# Run the test suite
[group('validate')]
test:
    @printf '{{cyan}}==> Running tests{{reset}}\n'
    {{python}} -m pytest tests/ -v

# Run the test suite with code coverage report
[group('validate')]
test-cov:
    @printf '{{cyan}}==> Running tests with coverage{{reset}}\n'
    {{python}} -m pytest tests/ -v --cov=build --cov-report=term-missing

# Reproducibility smoke test: fetch → build → validate → test → stats → reproducibility check. Matches .github/workflows/build.yml.
[group('validate')]
ci:
    @printf '{{cyan}}==> CI smoke test: fetch → build → validate → test → stats → reproducibility{{reset}}\n'
    @just fetch
    @just build
    @just validate
    @just test
    @just stats
    @printf '{{cyan}}==> Byte-reproducibility check (second build + hash diff){{reset}}\n'
    find data -type f \( -name '*.json' -o -name '*.svg' \) | sort | xargs sha256sum > /tmp/jld-hashes-1.txt
    {{python}} -m build.pipeline
    find data -type f \( -name '*.json' -o -name '*.svg' \) | sort | xargs sha256sum > /tmp/jld-hashes-2.txt
    diff /tmp/jld-hashes-1.txt /tmp/jld-hashes-2.txt
    @printf '{{green}}==> CI smoke test PASSED (byte-reproducible){{reset}}\n'

# ============================================================================
# CLEANUP
# ============================================================================

# Remove all built data files (preserves sources/ cache)
[group('clean')]
clean:
    @printf '{{yellow}}==> Removing built data files{{reset}}\n'
    find data -type f \( -name '*.json' -o -name '*.svg' \) -delete
    @printf '{{green}}Done. sources/ cache is preserved.{{reset}}\n'

# Remove built data AND upstream sources cache (forces full re-fetch on next build)
[group('clean')]
clean-all:
    @printf '{{red}}==> Removing all built data and sources cache{{reset}}\n'
    find data -type f \( -name '*.json' -o -name '*.svg' \) -delete
    find sources -type f -delete 2>/dev/null || true
    @printf '{{green}}Done. Next build will re-fetch everything.{{reset}}\n'

# ============================================================================
# CODE QUALITY
# ============================================================================

# Lint Python code with ruff
[group('quality')]
lint:
    @printf '{{cyan}}==> Linting Python code{{reset}}\n'
    {{python}} -m ruff check build/ tests/

# Auto-fix lint issues
[group('quality')]
lint-fix:
    @printf '{{cyan}}==> Auto-fixing lint issues{{reset}}\n'
    {{python}} -m ruff check --fix build/ tests/

# Verify source cache hashes without downloading
[group('quality')]
check-sources:
    @printf '{{cyan}}==> Verifying source cache integrity{{reset}}\n'
    {{python}} -c "from build.fetch import _load_manifest, _sha256, SOURCES, SOURCES_DIR; import sys; m = _load_manifest(); errs = 0; [print(f'[ok]   {s.name}') if (SOURCES_DIR / s.cache_path).exists() and _sha256(SOURCES_DIR / s.cache_path) == m.get('sources', {}).get(s.name, {}).get('sha256') else (print(f'[FAIL] {s.name}: missing or hash mismatch'), setattr(sys, '_err', True)) for s in SOURCES]; sys.exit(1 if getattr(sys, '_err', False) else 0)"

# ============================================================================
# DEVELOPMENT
# ============================================================================

# Set up the Python environment
[group('dev')]
setup:
    @printf '{{cyan}}==> Creating venv and installing dependencies{{reset}}\n'
    python3 -m venv .venv
    .venv/bin/pip install --upgrade pip
    .venv/bin/pip install -r build/requirements.txt
    @printf '{{green}}Done. Activate with:  . .venv/bin/activate{{reset}}\n'

# Show Python and tool versions used for this build
[group('dev')]
versions:
    @printf '{{cyan}}Python:{{reset}}   '; {{python}} --version
    @printf '{{cyan}}Just:{{reset}}     '; just --version
    @printf '{{cyan}}Git:{{reset}}      '; git --version
    @printf '{{cyan}}Pytest:{{reset}}   '; {{python}} -m pytest --version 2>/dev/null || echo '(not installed)'

# ============================================================================
# EXPORT
# ============================================================================

# Export as Yomitan-compatible dictionary ZIP
[group('export')]
export-yomitan:
    @printf '{{cyan}}==> Exporting Yomitan dictionary{{reset}}\n'
    {{python}} -m build.export_yomitan

# Export as a single SQLite database (all tables + cross-reference indices)
[group('export')]
export-sqlite:
    @printf '{{cyan}}==> Exporting SQLite database{{reset}}\n'
    {{python}} -m build.export_sqlite

# ============================================================================
# RELEASE
# ============================================================================

# Bump manifest.json.version to match the most-recent CHANGELOG [N.N.N] header.
# The phase_description must be updated by hand — this recipe refuses to run if
# it detects staleness so the human operator confirms the release narrative.
# See docs/release.md for the full release workflow.
[group('release')]
bump-release:
    @printf '{{cyan}}==> Reconciling manifest.json.version with CHANGELOG.md{{reset}}\n'
    {{python}} -m build.bump_release
    @printf '{{green}}Done. Now review manifest.json.phase_description and CHANGELOG.md, then tag the release.{{reset}}\n'

# Show what the release bump would do without writing files
[group('release')]
bump-release-dry-run:
    {{python}} -m build.bump_release --dry-run
