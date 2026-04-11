"""Coverage and count reporting.

Produces a build report showing entry counts per file, cross-reference
coverage, and enrichment completeness. Updates ``manifest.json`` with
the counts from the current build.

Run via ``just stats`` or ``python -m build.stats``.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "data"
MANIFEST_PATH = REPO_ROOT / "manifest.json"


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
    ("data/core/words.json", "words"),
    ("data/core/radicals.json", "radicals"),
    ("data/optional/names.json", "names"),
    ("data/corpus/sentences.json", "sentences"),
    ("data/enrichment/pitch-accent.json", "entries"),
    ("data/enrichment/frequency-newspaper.json", "entries"),
    ("data/enrichment/frequency-modern.json", "entries"),
    ("data/enrichment/jlpt-classifications.json", "classifications"),
    ("data/enrichment/stroke-order-index.json", "characters"),
    ("data/grammar/grammar.json", "grammar_points"),
    ("data/cross-refs/kanji-to-words.json", "mapping"),
    ("data/cross-refs/word-to-kanji.json", "mapping"),
    ("data/cross-refs/word-to-sentences.json", "mapping"),
    ("data/cross-refs/kanji-to-radicals.json", "mapping"),
]


def compute_counts() -> dict[str, int]:
    counts: dict[str, int] = {}
    for rel_path, payload_key in TARGET_FILES:
        full_path = REPO_ROOT / rel_path
        if not full_path.exists():
            counts[rel_path] = 0
            continue
        try:
            data = json.loads(full_path.read_text(encoding="utf-8"))
            counts[rel_path] = _count_entries(data, payload_key)
        except json.JSONDecodeError:
            counts[rel_path] = -1  # sentinel for unreadable
    return counts


def print_report(counts: dict[str, int]) -> None:
    print(f"{'File':<48} {'Entries':>12}")
    print(f"{'-' * 48} {'-' * 12}")
    for path, count in counts.items():
        label = "—" if count == 0 else (f"(error)" if count == -1 else f"{count:,}")
        print(f"{path:<48} {label:>12}")
    total = sum(c for c in counts.values() if c > 0)
    print(f"{'-' * 48} {'-' * 12}")
    print(f"{'TOTAL':<48} {total:>12,}")


def update_manifest(counts: dict[str, int]) -> None:
    if MANIFEST_PATH.exists():
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    else:
        manifest = {}
    manifest["counts"] = counts
    MANIFEST_PATH.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    counts = compute_counts()
    print_report(counts)
    update_manifest(counts)
    if all(c == 0 for c in counts.values()):
        print(
            "\n(No data files built yet. Phase 0 is scaffolding only. "
            "Phase 1 will produce the first data files.)"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
