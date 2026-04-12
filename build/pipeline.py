"""Build pipeline orchestrator.

Runs every transformation stage in the correct order:

    fetch → transform/{core} → transform/{enrichment} → cross_links → validate → stats

Individual stages can be run on their own for development. The full
pipeline is invoked via ``just build`` or ``python -m build.pipeline``.

Phase 0 status: This module contains the orchestration skeleton. The
individual transform modules are stubs that raise NotImplementedError
until Phase 1. The ``--dry-run`` flag lists the stages that would run
without executing them.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

REPO_ROOT = Path(__file__).resolve().parent.parent


@dataclass
class Stage:
    """A pipeline stage with a name, description, and entry-point callable.

    The callable should accept no arguments and return None on success.
    Stages are run in the order they are declared.
    """

    name: str
    description: str
    runner: Callable[[], None]
    phase: int  # which phase this stage is implemented in


def _placeholder(name: str, phase: int) -> Callable[[], None]:
    """Return a callable that raises a clear NotImplementedError."""

    def runner() -> None:
        raise NotImplementedError(
            f"Stage {name!r} is scheduled for Phase {phase}. "
            f"See docs/architecture.md for the phase roadmap."
        )

    return runner


def _build_stages() -> list[Stage]:
    """Build the stage list, importing transform modules lazily so the
    pipeline itself is importable even if a specific transform has
    import-time errors.
    """
    from build.transform import (
        conjugations,
        cross_links,
        expressions,
        frequency,
        grammar,
        jlpt,
        kana,
        kanji,
        names,
        pitch,
        radicals,
        sentences,
        stroke_order,
        words,
    )

    # Stage ordering is dependency-driven. A later stage may read the
    # OUTPUT of an earlier stage (as an optional enrichment input). A
    # clean-build run must put every stage after everything it depends
    # on, otherwise the first build produces different output than
    # subsequent builds (caught by the CI byte-reproducibility check).
    #
    # Known dependencies:
    #   * kanji → radicals (optional: radical_components enrichment)
    #   * kanji → jlpt       (optional: jlpt_waller enrichment)
    #   * words → jlpt       (optional: jlpt_waller enrichment)
    #   * stroke_order → kanji  (FILTER: only SVGs for characters in
    #     kanji.json are written; without kanji.json the stage emits
    #     every SVG in the archive, producing a 6,702-entry index
    #     instead of the 13,108-entry index and leaving ~280 non-kanji
    #     SVGs in data/enrichment/stroke-order/)
    #   * expressions → jlpt (optional: jlpt_waller enrichment)
    #   * cross_links → kanji, words, radicals, sentences
    #   * grammar → sentences (for Tatoeba linkage)
    return [
        # ---- Independent transforms (no reads from data/) ----
        Stage("kana", "Hand-curated hiragana/katakana dataset.", kana.build, phase=1),
        Stage("radicals", "Radical data from KRADFILE/RADKFILE.", radicals.build, phase=1),
        Stage("pitch", "Pitch accent data from Kanjium.", pitch.build, phase=2),
        Stage("jlpt", "JLPT level classifications from Waller.", jlpt.build, phase=2),
        Stage("frequency", "Frequency rankings (newspaper corpus from KANJIDIC2).", frequency.build, phase=2),
        Stage("sentences", "Example sentences from Tatoeba via jmdict-examples.", sentences.build, phase=1),
        Stage("conjugations", "Auto-generated verb and adjective conjugation tables.", conjugations.build, phase=3),
        # ---- Core transforms that read enrichment outputs ----
        Stage("kanji", "Kanji entries from KANJIDIC2, enriched with radical components and JLPT level.", kanji.build, phase=1),
        Stage("words", "Vocabulary from JMdict-examples, enriched with JLPT level.", words.build, phase=1),
        # ---- stroke_order MUST run after kanji (filters on kanji.json) ----
        Stage("stroke_order", "Stroke order SVGs from KanjiVG (filtered to characters in kanji.json).", stroke_order.build, phase=2),
        # ---- Cross-references (depend on core + enrichment data) ----
        Stage("cross_links", "Generate all cross-reference files.", cross_links.build, phase=2),
        # ---- Grammar (Phase 3 — original contribution + derivatives) ----
        Stage("grammar", "Curated Japanese grammar dataset (original, from grammar-curated/).", grammar.build, phase=3),
        Stage("expressions", "Lexicalized grammar patterns extracted from JMdict 'exp' entries.", expressions.build, phase=3),
        # ---- Names (optional, any phase) ----
        Stage("names", "Proper nouns from JMnedict (optional build target).", names.build, phase=1),
    ]


def run_pipeline(
    include_names: bool = False,
    dry_run: bool = False,
    only: list[str] | None = None,
) -> int:
    """Execute the pipeline stages.

    Args:
        include_names: If False, skip the ``names`` stage.
        dry_run: Print stages without running them.
        only: If non-empty, run only the named stages.

    Returns:
        Exit code: 0 on success, non-zero on failure.
    """
    stages = _build_stages()
    if not include_names:
        stages = [s for s in stages if s.name != "names"]
    if only:
        stages = [s for s in stages if s.name in only]

    print(f"Pipeline: {len(stages)} stages")
    for stage in stages:
        print(f"  [phase {stage.phase}] {stage.name} — {stage.description}")

    if dry_run:
        print("\n(dry run — no stages executed)")
        return 0

    print()
    failures: list[tuple[str, Exception]] = []
    for stage in stages:
        print(f"Running: {stage.name}")
        try:
            stage.runner()
            print(f"  ok: {stage.name}")
        except NotImplementedError as exc:
            print(f"  pending: {exc}")
        except Exception as exc:  # noqa: BLE001 — we want to collect all failures
            failures.append((stage.name, exc))
            print(f"  FAILED: {exc}")

    if failures:
        print(f"\n{len(failures)} stage(s) failed:")
        for name, exc in failures:
            print(f"  {name}: {exc}")
        return 1

    print("\nPipeline complete.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m build.pipeline",
        description="Run the Japanese Language Data build pipeline.",
    )
    parser.add_argument(
        "--with-names",
        action="store_true",
        help="Include the JMnedict names build (gitignored by default).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="List stages without running them.",
    )
    parser.add_argument(
        "--only",
        nargs="+",
        metavar="STAGE",
        help="Run only the named stages.",
    )
    args = parser.parse_args(argv)
    return run_pipeline(
        include_names=args.with_names,
        dry_run=args.dry_run,
        only=args.only,
    )


if __name__ == "__main__":
    sys.exit(main())
