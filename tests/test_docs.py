"""Documentation and release-metadata invariants.

These tests enforce that human-maintained documentation, release
metadata, and version strings stay coherent. They are cheap (no build,
no network) so they run on every ``just test`` and catch drift early.

Motivating incident: before v0.7.2 ``manifest.json.version`` sat at
``"0.4.1"`` while ``CHANGELOG.md`` reached ``[0.7.1]``. The ``README.md``
Status line, ``docs/phase4-candidates.md`` ADDRESSED entry,
``docs/sources.md`` coverage paragraph, and ``ATTRIBUTION.md`` coverage
section all likewise pointed at v0.4.0 state after v0.7.1 had shipped.
Automated release invariants prevent that from recurring.

See ``docs/release.md`` for the release workflow these tests back.
"""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
MANIFEST_PATH = REPO_ROOT / "manifest.json"
CHANGELOG_PATH = REPO_ROOT / "CHANGELOG.md"

# Matches ``## [N.N.N]`` with an optional ``— YYYY-MM-DD`` tail.
# ``## [Unreleased]`` is deliberately NOT matched — it is not a release.
VERSION_HEADER_RE = re.compile(
    r"^##\s*\[(\d+\.\d+\.\d+)\](?:\s*[—-]\s*(\d{4}-\d{2}-\d{2}))?\s*$",
    re.MULTILINE,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_manifest() -> dict:
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def _changelog_versions() -> list[tuple[str, str | None]]:
    """Return every ``[N.N.N]`` entry in CHANGELOG.md as (version, date)."""
    text = CHANGELOG_PATH.read_text(encoding="utf-8")
    return [(m.group(1), m.group(2)) for m in VERSION_HEADER_RE.finditer(text)]


def _latest_changelog_version() -> tuple[str, str | None]:
    versions = _changelog_versions()
    if not versions:
        raise RuntimeError("CHANGELOG.md has no concrete-version headers")
    return versions[0]


def _git_tags() -> list[str] | None:
    """Return the list of v<N>.<N>.<N> git tags, or None if git is unavailable."""
    try:
        result = subprocess.run(
            ["git", "tag", "-l", "v[0-9]*.[0-9]*.[0-9]*"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0:
        return None
    return [t.strip() for t in result.stdout.splitlines() if t.strip()]


# ---------------------------------------------------------------------------
# Release metadata invariants
# ---------------------------------------------------------------------------

def test_manifest_version_matches_changelog() -> None:
    """manifest.json.version must match the most-recent CHANGELOG [N.N.N] header.

    This is the primary drift-prevention test. Fix with ``just bump-release``.
    """
    manifest = _load_manifest()
    manifest_version = manifest.get("version", "")
    changelog_version, _ = _latest_changelog_version()
    assert manifest_version == changelog_version, (
        f"manifest.json.version={manifest_version!r} but the most-recent "
        f"CHANGELOG entry is [{changelog_version}]. Run `just bump-release` "
        f"to reconcile, or add a new [N.N.N] section to CHANGELOG.md."
    )


def test_manifest_phase_description_length_cap() -> None:
    """phase_description should be ≤600 characters.

    The cap forces freshness: long prose fields tend to accumulate
    historical detail instead of describing current state. If this test
    fails, rewrite the field to focus on what's true *now*.
    """
    manifest = _load_manifest()
    desc = manifest.get("phase_description", "")
    assert len(desc) <= 600, (
        f"manifest.json.phase_description is {len(desc)} chars (cap is 600). "
        f"Rewrite it to focus on the current release rather than accumulating "
        f"historical detail."
    )


def test_manifest_phase_description_mentions_current_version() -> None:
    """phase_description should reference the current manifest.version.

    If the version moved forward but the description still only mentions
    older versions, the narrative is stale.
    """
    manifest = _load_manifest()
    version = manifest.get("version", "")
    desc = manifest.get("phase_description", "")
    if not version or not desc:
        pytest.skip("manifest missing version or phase_description")
    assert version in desc, (
        f"manifest.json.phase_description does not mention current version "
        f"{version!r}. Rewrite the description to include it so consumers "
        f"reading the manifest can see what the current state is."
    )


def _is_gitignored(rel_path: str) -> bool:
    """Return True if *rel_path* is covered by .gitignore rules."""
    try:
        result = subprocess.run(
            ["git", "check-ignore", "-q", rel_path],
            cwd=REPO_ROOT,
            capture_output=True,
            timeout=5,
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def test_manifest_counts_match_reality() -> None:
    """Every count in manifest.json.counts must match the actual entries.

    For committed files that don't exist, the count should be null so
    consumers can distinguish "not yet built" from "built but empty".

    Gitignored files may carry a non-null count from the last full
    build — this is valid documentation of what the pipeline produces,
    even when the file isn't present locally.
    """
    manifest = _load_manifest()
    counts = manifest.get("counts", {})
    if not counts:
        pytest.skip("manifest.counts is empty — no data has been built yet")

    from build.stats import compute_counts
    live_counts = compute_counts()

    for rel_path, manifest_count in counts.items():
        live = live_counts.get(rel_path)
        # If the file doesn't exist, gitignored files may keep their
        # manifest count (documentation of a prior full build).
        # Committed files must have null when absent.
        if live is None:
            if _is_gitignored(rel_path):
                continue
            assert manifest_count is None, (
                f"manifest.counts[{rel_path!r}]={manifest_count} but the file "
                f"does not exist. Expected null. Run `just stats` to reconcile."
            )
            continue
        assert manifest_count == live, (
            f"manifest.counts[{rel_path!r}]={manifest_count} but the file "
            f"has {live} entries right now. Run `just stats` to reconcile."
        )


# ---------------------------------------------------------------------------
# CHANGELOG structural invariants
# ---------------------------------------------------------------------------

def test_changelog_headers_have_dates() -> None:
    """Every ``[N.N.N]`` entry in CHANGELOG.md must carry a YYYY-MM-DD date.

    The ``— YYYY-MM-DD`` suffix is part of the Keep-a-Changelog format
    we follow. A missing date is a signal of an incomplete release.
    """
    versions = _changelog_versions()
    assert versions, "CHANGELOG.md has no concrete-version headers"
    missing = [v for v, d in versions if d is None]
    assert not missing, (
        f"CHANGELOG.md version header(s) missing date: {missing}. "
        f"Add `— YYYY-MM-DD` to each `## [N.N.N]` header."
    )


def test_every_git_tag_has_changelog_entry() -> None:
    """Every v<N>.<N>.<N> git tag must have a corresponding CHANGELOG entry.

    If git is not available (not a git checkout, no git binary), the
    test is skipped — it is meaningful only when run against a real
    repository.
    """
    tags = _git_tags()
    if tags is None:
        pytest.skip("git not available — cannot enumerate tags")
    if not tags:
        pytest.skip("no v<N>.<N>.<N> tags yet (fresh repo)")

    changelog_versions = {v for v, _ in _changelog_versions()}
    missing = []
    for tag in tags:
        version = tag.lstrip("v")
        if version not in changelog_versions:
            missing.append(tag)
    assert not missing, (
        f"Git tag(s) present without a matching CHANGELOG entry: {missing}. "
        f"Every tagged release must have a `## [N.N.N]` section in "
        f"CHANGELOG.md."
    )


# ---------------------------------------------------------------------------
# Stale-reference guards for specific public-facing claims
# ---------------------------------------------------------------------------

# Files whose prose is "status-claiming" — they must describe the current
# state of the project, not a previous state. The guards below check them
# for stale radical coverage claims specifically; future guards can be
# added for other known drift points.
STATUS_FILES = (
    "README.md",
    "manifest.json",
    "docs/phase4-candidates.md",
    "docs/sources.md",
    "ATTRIBUTION.md",
)


def test_status_files_mention_current_radical_coverage() -> None:
    """Status-claiming files must mention the current radical coverage.

    As of v0.7.1, the radical dataset has 242/253 (95.7%) coverage. The
    files below are user-facing and must reflect current state.

    When radical coverage changes, update this test's expected substrings.
    """
    expected_fragments = ("242", "95.7%")
    for rel in STATUS_FILES:
        path = REPO_ROOT / rel
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        for fragment in expected_fragments:
            assert fragment in text, (
                f"{rel} does not mention the current radical coverage "
                f"fragment {fragment!r}. This file is a user-facing status "
                f"document and must reflect current state (242/253, 95.7%). "
                f"Update it and/or update this test if the coverage has "
                f"changed."
            )


def test_status_files_do_not_present_old_radical_coverage_as_current() -> None:
    """Status-claiming files must not present the old 77.9% coverage as current.

    They *may* reference the old state historically (e.g., "v0.4.0 had
    197/253 (77.9%), expanded in v0.7.1 to 242/253 (95.7%)") as long as
    the new state is also present. The earlier test catches the
    presence of the new state; this one catches the forbidden pattern
    of ONLY having the old state.
    """
    for rel in STATUS_FILES:
        path = REPO_ROOT / rel
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        has_old = "77.9%" in text or "197 of 253" in text or "197/253" in text
        has_new = "95.7%" in text or "242 of 253" in text or "242/253" in text
        if has_old:
            assert has_new, (
                f"{rel} references the old radical coverage (77.9% / 197/253) "
                f"without also referencing the current coverage (95.7% / "
                f"242/253). The old state is only allowed as a historical "
                f"marker alongside the new state, not on its own."
            )
