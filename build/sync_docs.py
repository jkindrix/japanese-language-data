"""Synchronize documentation counts with manifest.json.

Reads the entry counts from manifest.json and updates markdown tables
in README.md and docs/downstream.md so that counts never drift from
the build output. Also verifies prose count references in other docs
and warns about drift without auto-editing.

Run via ``just sync-docs`` or ``python -m build.sync_docs``.
Called automatically at the end of ``just stats``.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from build.constants import MANIFEST_PATH, REPO_ROOT


def _load_counts() -> dict[str, int]:
    """Load manifest counts, filtering to int values only."""
    if not MANIFEST_PATH.exists():
        return {}
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    return {
        path: count
        for path, count in manifest.get("counts", {}).items()
        if isinstance(count, int) and count > 0
    }


def _format_count(n: int) -> str:
    """Format an integer with comma thousands separator."""
    return f"{n:,}"


# ---------------------------------------------------------------------------
# Table syncing — README.md and docs/downstream.md
# ---------------------------------------------------------------------------

# Regex: markdown table row with a data path (backticked) and a comma-formatted
# integer count. Captures: (prefix including path cell), (the count), (rest).
#
# README format:  | `data/core/words.json` | Source | 23,119 | ✓ | desc |
# Downstream:     | `words.json` | 23,119 | 1.2 MB | 5 MB |

_TABLE_ROW_RE = re.compile(
    r"^(\|[^|]*`([a-z/_.-]+\.json)`[^|]*(?:\|[^|]*)?)\|\s*([\d,]+)\s*\|(.*)$"
)


def _match_path_to_manifest(
    cell_path: str, counts: dict[str, int],
) -> int | None:
    """Resolve a path fragment from a table cell to a manifest count.

    Table cells may use full paths (``data/core/words.json``) or bare
    filenames (``words.json``). Try exact match first, then suffix match.
    """
    # Exact match
    if cell_path in counts:
        return counts[cell_path]
    # Suffix match (downstream.md uses bare filenames)
    for manifest_path, count in counts.items():
        if manifest_path.endswith("/" + cell_path) or manifest_path.endswith(cell_path):
            return count
    return None


def sync_table_counts(file_path: Path, counts: dict[str, int]) -> list[str]:
    """Update count columns in markdown tables to match manifest.

    Returns a list of human-readable change descriptions. Writes the
    file only if changes were made.
    """
    text = file_path.read_text(encoding="utf-8")
    lines = text.split("\n")
    changes: list[str] = []

    for i, line in enumerate(lines):
        m = _TABLE_ROW_RE.match(line)
        if not m:
            continue
        prefix, cell_path, old_count_str, suffix = m.groups()
        manifest_count = _match_path_to_manifest(cell_path, counts)
        if manifest_count is None:
            continue
        new_count_str = _format_count(manifest_count)
        if old_count_str.strip() == new_count_str:
            continue
        # Rebuild the line with the updated count
        lines[i] = f"{prefix}| {new_count_str} |{suffix}"
        try:
            rel = file_path.relative_to(REPO_ROOT)
        except ValueError:
            rel = file_path.name
        changes.append(
            f"  {rel}:{i+1}: {cell_path}: "
            f"{old_count_str.strip()} → {new_count_str}"
        )

    if changes:
        file_path.write_text("\n".join(lines), encoding="utf-8")
    return changes


# ---------------------------------------------------------------------------
# Prose verification — warn about counts that may have drifted
# ---------------------------------------------------------------------------

# Known prose count references: (doc_glob, regex_near_filename, manifest_key).
# The regex should match a sentence fragment containing both the filename hint
# and a comma-formatted number. We extract the number and compare to manifest.
PROSE_CHECKS: list[tuple[str, str, str]] = [
    (
        "docs/architecture.md",
        r"Wiktionary pitch accent \(([\d,]+) entries\)",
        "data/enrichment/pitch-accent-wiktionary.json",
    ),
    (
        "docs/sources.md",
        r"supplementary pitch accent for ([\d,]+) words",
        "data/enrichment/pitch-accent-wiktionary.json",
    ),
]


def verify_prose_counts(counts: dict[str, int]) -> list[str]:
    """Check known prose count references against manifest.

    Returns a list of warning strings for mismatches. Does NOT modify
    any files — prose counts require human judgment to update because
    they're embedded in natural language.
    """
    warnings: list[str] = []
    for doc_path_str, pattern, manifest_key in PROSE_CHECKS:
        doc_path = REPO_ROOT / doc_path_str
        if not doc_path.exists():
            continue
        expected = counts.get(manifest_key)
        if expected is None:
            continue
        text = doc_path.read_text(encoding="utf-8")
        for m in re.finditer(pattern, text):
            found = int(m.group(1).replace(",", ""))
            if found != expected:
                # Find line number
                line_no = text[:m.start()].count("\n") + 1
                warnings.append(
                    f"  {doc_path_str}:{line_no}: "
                    f"says {_format_count(found)} but manifest has "
                    f"{_format_count(expected)} for {manifest_key}"
                )
    return warnings


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

# Files to sync (table counts auto-updated)
SYNC_FILES = [
    REPO_ROOT / "README.md",
    REPO_ROOT / "docs" / "downstream.md",
]


def sync(verify_only: bool = False) -> int:
    """Sync doc counts with manifest.json.

    Args:
        verify_only: If True, report mismatches but don't write files.

    Returns:
        0 if everything is in sync, 1 if mismatches were found/fixed.
    """
    counts = _load_counts()
    if not counts:
        print("[sync-docs] No counts in manifest.json — run `just stats` first.")
        return 1

    had_changes = False

    # Table syncing
    for file_path in SYNC_FILES:
        if not file_path.exists():
            continue
        if verify_only:
            # Read-only check: parse tables and compare without writing
            text = file_path.read_text(encoding="utf-8")
            for i, line in enumerate(text.split("\n")):
                m = _TABLE_ROW_RE.match(line)
                if not m:
                    continue
                _, cell_path, old_count_str, _ = m.groups()
                manifest_count = _match_path_to_manifest(cell_path, counts)
                if manifest_count is None:
                    continue
                if old_count_str.strip() != _format_count(manifest_count):
                    rel = file_path.relative_to(REPO_ROOT)
                    print(
                        f"[drift]    {rel}:{i+1}: {cell_path}: "
                        f"{old_count_str.strip()} ≠ {_format_count(manifest_count)}"
                    )
                    had_changes = True
        else:
            changes = sync_table_counts(file_path, counts)
            if changes:
                had_changes = True
                for c in changes:
                    print(f"[synced]  {c}")

    # Prose verification (always read-only)
    prose_warnings = verify_prose_counts(counts)
    if prose_warnings:
        had_changes = True
        print("[prose drift — manual update needed]")
        for w in prose_warnings:
            print(w)

    if not had_changes:
        print("[sync-docs] All doc counts match manifest.")

    return 1 if had_changes else 0


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(
        prog="python -m build.sync_docs",
        description="Sync documentation counts with manifest.json.",
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Check for drift without writing files.",
    )
    args = parser.parse_args()
    return sync(verify_only=args.verify)


if __name__ == "__main__":
    sys.exit(main())
