"""Coverage and count reporting.

Produces a build report showing entry counts per file, cross-reference
coverage, and enrichment completeness. Updates ``manifest.json`` with
the counts and build date from the current build.

This module also keeps ``manifest.json.generated`` in sync with the
current build date. Other fields (``version``, ``phase_description``,
source pins, etc.) are preserved; they are updated by the ``just bump-
release`` recipe or manually at release time.

Missing files (e.g., the gitignored ``data/optional/names.json`` when
not built) are reported as ``null`` rather than ``0`` so consumers can
distinguish "not built" from "built but empty".

Run via ``just stats`` or ``python -m build.stats``.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from build.pipeline import BUILD_DATE
from pathlib import Path

from build.constants import MANIFEST_PATH, REPO_ROOT


def _count_entries(data: dict, payload_key: str) -> int:
    """Count entries for various payload shapes."""
    payload = data.get(payload_key)
    if payload is None:
        return 0
    if isinstance(payload, list):
        return len(payload)
    if isinstance(payload, dict):
        return len(payload)
    return 0


# (relative path, payload key used in the schema)
TARGET_FILES: list[tuple[str, str]] = [
    ("data/core/kana.json", "kana"),
    ("data/core/kanji.json", "kanji"),
    ("data/core/kanji-joyo.json", "kanji"),
    ("data/core/kanji-jinmeiyo.json", "kanji"),
    ("data/core/words.json", "words"),
    ("data/core/words-full.json", "words"),
    ("data/core/radicals.json", "radicals"),
    ("data/optional/names.json", "names"),
    ("data/corpus/sentences.json", "sentences"),
    ("data/corpus/sentences-kftt.json", "sentences"),
    ("data/corpus/sentences-tatoeba-full.json", "sentences"),
    ("data/enrichment/pitch-accent.json", "entries"),
    ("data/enrichment/pitch-accent-wiktionary.json", "entries"),
    ("data/enrichment/frequency-newspaper.json", "entries"),
    ("data/enrichment/frequency-modern.json", "entries"),
    ("data/enrichment/frequency-corpus.json", "entries"),
    ("data/enrichment/frequency-subtitles.json", "entries"),
    ("data/enrichment/frequency-web.json", "entries"),
    ("data/enrichment/frequency-wikipedia.json", "entries"),
    ("data/enrichment/furigana.json", "entries"),
    ("data/enrichment/counter-words.json", "counter_words"),
    ("data/enrichment/ateji.json", "entries"),
    ("data/enrichment/jukugo-compounds.json", "compounds"),
    ("data/enrichment/jlpt-classifications.json", "classifications"),
    ("data/enrichment/stroke-order-index.json", "characters"),
    ("data/grammar/grammar.json", "grammar_points"),
    ("data/grammar/expressions.json", "expressions"),
    ("data/grammar/conjugations.json", "entries"),
    ("data/cross-refs/kanji-to-words.json", "mapping"),
    ("data/cross-refs/word-to-kanji.json", "mapping"),
    ("data/cross-refs/word-to-sentences.json", "mapping"),
    ("data/cross-refs/kanji-to-radicals.json", "mapping"),
    ("data/cross-refs/reading-to-words.json", "mapping"),
    ("data/cross-refs/radical-to-kanji.json", "mapping"),
    ("data/cross-refs/kanji-to-sentences.json", "mapping"),
    ("data/cross-refs/word-to-grammar.json", "mapping"),
]


def compute_counts() -> dict[str, int | None]:
    """Compute entry counts for every target data file.

    Returns a mapping from relative file path to entry count:

        * ``int`` ≥ 0 — the file exists and has that many entries
        * ``None`` — the file does not exist (e.g., gitignored and not built)
        * ``-1`` — the file exists but is unparseable (sentinel for errors)

    The ``None`` / ``0`` distinction matters for files that are
    conditionally built (``data/optional/names.json``) so that consumers
    and the ``just stats`` report can tell "not yet built" apart from
    "built with zero entries".
    """
    counts: dict[str, int | None] = {}
    for rel_path, payload_key in TARGET_FILES:
        full_path = REPO_ROOT / rel_path
        if not full_path.exists():
            counts[rel_path] = None
            continue
        try:
            data = json.loads(full_path.read_text(encoding="utf-8"))
            counts[rel_path] = _count_entries(data, payload_key)
        except json.JSONDecodeError:
            counts[rel_path] = -1  # sentinel for unreadable
    return counts


# Paths whose entries are derivative of another file in TARGET_FILES
# (filtered views of kanji.json). They should not be counted again when
# computing "unique committed entries".
DERIVED_PATHS = {
    "data/core/kanji-joyo.json",
    "data/core/kanji-jinmeiyo.json",
}

# Paths that are gitignored build artifacts, not committed to the repo.
GITIGNORED_PATHS = {
    "data/core/words-full.json",
}


def print_report(counts: dict[str, int | None]) -> None:
    print(f"{'File':<48} {'Entries':>12}")
    print(f"{'-' * 48} {'-' * 12}")
    for path, count in counts.items():
        if count is None:
            label = "(not built)"
        elif count == -1:
            label = "(error)"
        elif count == 0:
            label = "—"
        else:
            label = f"{count:,}"
        print(f"{path:<48} {label:>12}")
    total = sum(c for c in counts.values() if isinstance(c, int) and c > 0)
    unique_total = sum(
        c for p, c in counts.items()
        if isinstance(c, int) and c > 0 and p not in DERIVED_PATHS and p not in GITIGNORED_PATHS
    )
    print(f"{'-' * 48} {'-' * 12}")
    print(f"{'TOTAL (all rows)':<48} {total:>12,}")
    print(f"{'UNIQUE COMMITTED (excludes derivatives + gitignored)':<48} {unique_total:>12,}")


def update_manifest(counts: dict[str, int | None]) -> None:
    """Merge the computed counts and today's build date into manifest.json.

    All other fields — version, phase_description, sources, source hashes,
    grammar_curation_status, next_actions — are preserved. Those are
    edited by ``just bump-release`` or by hand at release time.
    """
    if MANIFEST_PATH.exists():
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    else:
        manifest = {}
    manifest["counts"] = counts
    manifest["generated"] = BUILD_DATE
    # Atomic write: write to a temp file in the same directory, then
    # rename.  This prevents a crash mid-write from corrupting the
    # manifest (the same pattern fetch.py uses for downloads).
    tmp_fd, tmp_path = tempfile.mkstemp(
        dir=MANIFEST_PATH.parent, suffix=".tmp",
    )
    try:
        with os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)
            f.write("\n")
        Path(tmp_path).replace(MANIFEST_PATH)
    except BaseException:
        Path(tmp_path).unlink(missing_ok=True)
        raise


def main() -> int:
    counts = compute_counts()
    print_report(counts)
    update_manifest(counts)
    if all(c is None or c == 0 for c in counts.values()):
        print(
            "\n(No data files built yet. Phase 0 is scaffolding only. "
            "Phase 1 will produce the first data files.)"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
