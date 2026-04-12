"""Release-version reconciliation for manifest.json.

Reads ``CHANGELOG.md``, finds the most recent ``## [N.N.N]`` header, and
updates ``manifest.json.version`` and ``manifest.json.generated`` to
match. Refuses to silently touch ``phase_description`` — that field is a
narrative summary and must be re-written by hand at release time so the
human operator confirms the release story is accurate.

Runs as ``just bump-release`` or ``python -m build.bump_release``. Pass
``--dry-run`` to see what would change without writing files.

Usage:

    just bump-release           # update manifest to match CHANGELOG top
    just bump-release-dry-run   # show the diff without writing

Rationale:

    Before v0.7.2 the manifest drifted to v0.4.1 while the CHANGELOG
    reached v0.7.1. A test (test_manifest_version_matches_changelog)
    enforces the invariant; this recipe makes reconciling cheap.

    ``phase_description`` is explicitly NOT auto-derived. See
    ``docs/release.md`` for the full release workflow including the
    manual step of rewriting that field.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
MANIFEST_PATH = REPO_ROOT / "manifest.json"
CHANGELOG_PATH = REPO_ROOT / "CHANGELOG.md"

# Matches ``## [N.N.N]`` or ``## [N.N.N] — YYYY-MM-DD``. Rejects
# ``## [Unreleased]`` deliberately — that is not a concrete release.
VERSION_HEADER_RE = re.compile(
    r"^##\s*\[(\d+\.\d+\.\d+)\](?:\s*[—-]\s*(\d{4}-\d{2}-\d{2}))?\s*$",
    re.MULTILINE,
)


def latest_changelog_version() -> tuple[str, str | None]:
    """Return (version, date) for the most-recent CHANGELOG [N.N.N] header.

    Raises if CHANGELOG.md has no concrete-version header.
    """
    text = CHANGELOG_PATH.read_text(encoding="utf-8")
    for match in VERSION_HEADER_RE.finditer(text):
        version = match.group(1)
        date_str = match.group(2)  # may be None if the header has no date
        return version, date_str
    raise RuntimeError(
        f"No concrete-version header found in {CHANGELOG_PATH}. "
        f"Expected a line like '## [0.7.1] — 2026-04-12'."
    )


def _load_manifest() -> dict:
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def _save_manifest(manifest: dict) -> None:
    MANIFEST_PATH.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def bump(dry_run: bool = False) -> int:
    manifest = _load_manifest()
    current_version = manifest.get("version", "")
    current_generated = manifest.get("generated", "")
    current_phase_desc = manifest.get("phase_description", "")

    new_version, changelog_date = latest_changelog_version()
    new_generated = changelog_date or date.today().isoformat()

    changes: list[str] = []
    if current_version != new_version:
        changes.append(f"version:           {current_version!r} -> {new_version!r}")
    if current_generated != new_generated:
        changes.append(f"generated:         {current_generated!r} -> {new_generated!r}")

    if not changes:
        print(
            f"manifest.json is already up to date "
            f"(version={current_version}, generated={current_generated}). "
            f"Nothing to do."
        )
        return 0

    print(f"Latest CHANGELOG version: {new_version} ({changelog_date or '(no date)'})")
    print("Changes:")
    for line in changes:
        print(f"  {line}")

    # Soft check: phase_description should be ≤600 chars (enforced by
    # test_manifest_phase_description_length_cap). This recipe flags it
    # loudly but does not rewrite it.
    desc_len = len(current_phase_desc)
    if desc_len > 600:
        print(
            f"  WARNING: phase_description is {desc_len} chars (>600). "
            f"Rewrite it to summarize the current release before tagging."
        )

    # Heuristic stale-reference check: if phase_description still
    # mentions the previous version as the current state, flag it.
    if current_version and current_version in current_phase_desc and new_version not in current_phase_desc:
        print(
            f"  WARNING: phase_description mentions the previous version "
            f"({current_version}) but not the new one ({new_version}). "
            f"It probably needs rewriting."
        )

    if dry_run:
        print("\n(dry run — manifest.json NOT written)")
        return 0

    manifest["version"] = new_version
    manifest["generated"] = new_generated
    _save_manifest(manifest)
    print("\nmanifest.json updated. Next steps:")
    print("  1. Review manifest.json.phase_description and rewrite if stale.")
    print("  2. Run `just build` to regenerate data files with the new date.")
    print("  3. Run `just test` to confirm the invariant tests pass.")
    print("  4. Commit the manifest + data changes.")
    print("  5. Tag and push: git tag v{v} && git push --tags".format(v=new_version))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m build.bump_release",
        description="Reconcile manifest.json.version with the CHANGELOG top entry.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would change without writing manifest.json.",
    )
    args = parser.parse_args(argv)
    return bump(dry_run=args.dry_run)


if __name__ == "__main__":
    sys.exit(main())
