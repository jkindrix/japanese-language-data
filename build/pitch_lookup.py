"""Shared pitch accent lookup builder.

Loads and merges pitch accent data from Kanjium and Wiktionary into a
single lookup, using union semantics for overlapping entries. This is
the single source of truth for how pitch accent sources are combined —
all export scripts (Yomitan, Anki, SQLite) use this module instead of
implementing their own merge logic.

Union semantics: if Kanjium says [0, 2] and Wiktionary says [0, 3] for
the same (word, reading) pair, the merged result is [0, 2, 3]. Both
sources are high-quality; disagreements represent genuine accent
variation in Japanese, not errors.
"""

from __future__ import annotations

import json
from pathlib import Path

from build.constants import DATA_DIR

PITCH_JSON = DATA_DIR / "enrichment" / "pitch-accent.json"
PITCH_WIKT_JSON = DATA_DIR / "enrichment" / "pitch-accent-wiktionary.json"


class PitchEntry:
    """Merged pitch accent entry with positions and mora count."""

    __slots__ = ("positions", "mora_count")

    def __init__(self, positions: set[int], mora_count: int | None) -> None:
        self.positions = positions
        self.mora_count = mora_count


def load_merged_pitch(
    kanjium_path: Path | None = None,
    wiktionary_path: Path | None = None,
) -> dict[tuple[str, str], list[int]]:
    """Load and merge pitch accent data from all sources.

    Returns a dict mapping ``(word, reading)`` to a sorted list of
    accent positions (integers). Union semantics: positions from all
    sources are combined.

    Paths default to the module-level PITCH_JSON / PITCH_WIKT_JSON
    at call time (not definition time) so monkeypatching works in tests.
    Explicit paths override for direct testability.
    """
    if kanjium_path is None:
        kanjium_path = PITCH_JSON
    if wiktionary_path is None:
        wiktionary_path = PITCH_WIKT_JSON

    merged: dict[tuple[str, str], set[int]] = {}

    for path in (kanjium_path, wiktionary_path):
        if not path.exists():
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        for e in data.get("entries", []):
            word = e.get("word", "")
            reading = e.get("reading", "")
            positions = e.get("pitch_positions", [])
            if word and positions:
                key = (word, reading)
                if key not in merged:
                    merged[key] = set(positions)
                else:
                    merged[key].update(positions)

    return {k: sorted(v) for k, v in merged.items()}


def load_merged_pitch_full(
    kanjium_path: Path | None = None,
    wiktionary_path: Path | None = None,
) -> dict[tuple[str, str], PitchEntry]:
    """Load and merge pitch accent data, preserving mora_count.

    Like ``load_merged_pitch`` but returns ``PitchEntry`` objects that
    include the mora count from the first source that provided it.
    Used by the SQLite export which stores mora_count per entry.
    """
    if kanjium_path is None:
        kanjium_path = PITCH_JSON
    if wiktionary_path is None:
        wiktionary_path = PITCH_WIKT_JSON

    merged: dict[tuple[str, str], PitchEntry] = {}

    for path in (kanjium_path, wiktionary_path):
        if not path.exists():
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        for e in data.get("entries", []):
            word = e.get("word", "")
            reading = e.get("reading", "")
            positions = e.get("pitch_positions", [])
            mora_count = e.get("mora_count")
            if word and positions:
                key = (word, reading)
                if key not in merged:
                    merged[key] = PitchEntry(set(positions), mora_count)
                else:
                    merged[key].positions.update(positions)
                    if merged[key].mora_count is None and mora_count is not None:
                        merged[key].mora_count = mora_count

    return merged


def format_pitch_string(positions: list[int]) -> str:
    """Format a list of positions as a compact slash-separated string.

    Example: [0, 2, 3] → "0/2/3"
    """
    return "/".join(str(p) for p in positions)
