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
import json
import logging
import sys
import time
import traceback
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeout
from dataclasses import dataclass
from datetime import date
from typing import Callable


log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Stage timeout (seconds). Generous for any transform; prevents a hung
# stage from blocking the pipeline indefinitely.
# ---------------------------------------------------------------------------
STAGE_TIMEOUT: int = 300

# ---------------------------------------------------------------------------
# DAG dependency enforcement
# ---------------------------------------------------------------------------
# Each key is a stage name; its value is the set of stages that MUST
# appear before it in the stage list. This is enforced at pipeline
# startup — a mis-ordered stage list raises immediately rather than
# producing a subtly incorrect build.
#
# Rationale: git log shows that implicit ordering already caused a real
# bug (stroke_order vs kanji). Comments-as-documentation is not enough.

STAGE_DEPENDENCIES: dict[str, set[str]] = {
    "kanji": {"radicals", "jlpt"},
    "words": {"jlpt"},
    "stroke_order": {"kanji"},
    "expressions": {"jlpt"},
    "cross_links": {"kanji", "words", "radicals", "sentences", "grammar"},
    "frequency_subtitles": {"words"},
    "counters": {"words"},
    "ateji": {"words"},
    "jukugo": {"words", "kanji"},
    "grammar": {"sentences"},
}


def _validate_stage_ordering(stages: list[Stage]) -> None:
    """Verify that the stage list respects STAGE_DEPENDENCIES.

    Raises ValueError with a clear message if any stage appears before
    a dependency it requires.
    """
    stage_positions = {s.name: i for i, s in enumerate(stages)}
    for stage_name, deps in STAGE_DEPENDENCIES.items():
        if stage_name not in stage_positions:
            continue  # stage filtered out (e.g., --only)
        pos = stage_positions[stage_name]
        for dep in sorted(deps):
            if dep not in stage_positions:
                continue  # dependency filtered out — OK for --only runs
            if stage_positions[dep] >= pos:
                raise ValueError(
                    f"Stage ordering violation: '{stage_name}' (position {pos}) "
                    f"depends on '{dep}' (position {stage_positions[dep]}), "
                    f"but '{dep}' appears later. Reorder the stage list in "
                    f"_build_stages()."
                )


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
        ateji,
        conjugations,
        counters,
        cross_links,
        expressions,
        frequency,
        frequency_subtitles,
        grammar,
        jukugo,
        jlpt,
        kana,
        kanji,
        kftt,
        names,
        pitch,
        radicals,
        sentences,
        stroke_order,
        words,
    )

    # Stage ordering is dependency-driven and enforced by
    # _validate_stage_ordering() against STAGE_DEPENDENCIES above.
    # A later stage may read the OUTPUT of an earlier stage (as an
    # optional enrichment input). A clean-build run must put every
    # stage after everything it depends on, otherwise the first build
    # produces different output than subsequent builds (caught by the
    # CI byte-reproducibility check).
    return [
        # ---- Independent transforms (no reads from data/) ----
        Stage("kana", "Hand-curated hiragana/katakana dataset.", kana.build, phase=1),
        Stage("radicals", "Radical data from KRADFILE/RADKFILE.", radicals.build, phase=1),
        Stage("pitch", "Pitch accent data from Kanjium.", pitch.build, phase=2),
        Stage("jlpt", "JLPT level classifications from Waller.", jlpt.build, phase=2),
        Stage("frequency", "Frequency rankings (newspaper corpus from KANJIDIC2).", frequency.build, phase=2),
        Stage("sentences", "Example sentences from Tatoeba via jmdict-examples.", sentences.build, phase=1),
        Stage("kftt", "KFTT parallel corpus (~440k JP-EN sentence pairs from Wikipedia Kyoto articles).", kftt.build, phase=4),
        Stage("conjugations", "Auto-generated verb and adjective conjugation tables.", conjugations.build, phase=3),
        # ---- Core transforms that read enrichment outputs ----
        Stage("kanji", "Kanji entries from KANJIDIC2, enriched with radical components and JLPT level.", kanji.build, phase=1),
        Stage("words", "Vocabulary from JMdict-examples, enriched with JLPT level.", words.build, phase=1),
        # ---- stroke_order MUST run after kanji (enforced by STAGE_DEPENDENCIES) ----
        Stage("stroke_order", "Stroke order SVGs from KanjiVG (filtered to characters in kanji.json).", stroke_order.build, phase=2),
        # ---- Enrichment that depends on core data ----
        Stage("frequency_subtitles", "Word frequency from OpenSubtitles 2018 media corpus.", frequency_subtitles.build, phase=4),
        Stage("counters", "Counter-word (josushi) index extracted from JMdict 'ctr' POS tag.", counters.build, phase=4),
        Stage("ateji", "Ateji (phonetic kanji spelling) index from JMdict kanji tags.", ateji.build, phase=4),
        Stage("jukugo", "Multi-kanji compound (jukugo) index with per-character decomposition.", jukugo.build, phase=4),
        # ---- Grammar (Phase 3 — must run before cross_links for word-to-grammar index) ----
        Stage("grammar", "Curated Japanese grammar dataset (original, from grammar-curated/).", grammar.build, phase=3),
        Stage("expressions", "Lexicalized grammar patterns extracted from JMdict 'exp' entries.", expressions.build, phase=3),
        # ---- Cross-references (depend on core + enrichment + grammar data) ----
        Stage("cross_links", "Generate all cross-reference files.", cross_links.build, phase=2),
        # ---- Names (optional, any phase) ----
        Stage("names", "Proper nouns from JMnedict (optional build target).", names.build, phase=1),
    ]


def run_pipeline(
    include_names: bool = False,
    dry_run: bool = False,
    only: list[str] | None = None,
    verbose: bool = False,
) -> int:
    """Execute the pipeline stages.

    Args:
        include_names: If False, skip the ``names`` stage.
        dry_run: Print stages without running them.
        only: If non-empty, run only the named stages.
        verbose: If True, enable DEBUG-level logging.

    Returns:
        Exit code: 0 on success, non-zero on failure.
    """
    # Configure structured logging for pipeline orchestration.
    logging.basicConfig(
        format="%(asctime)s %(levelname)-5s %(name)s: %(message)s",
        datefmt="%H:%M:%S",
        level=logging.DEBUG if verbose else logging.INFO,
    )

    stages = _build_stages()
    if not include_names:
        stages = [s for s in stages if s.name != "names"]
    if only:
        stages = [s for s in stages if s.name in only]

    # Enforce the dependency DAG before running anything. This catches
    # mis-ordered stages at startup rather than producing subtly wrong
    # output that only appears as a byte-diff failure in CI.
    _validate_stage_ordering(stages)

    # Capture the build date once at pipeline start. This eliminates the
    # cross-midnight race condition where a long-running build could
    # write different dates into different output files.
    build_date = date.today().isoformat()

    log.info("Pipeline: %d stages (build date: %s)", len(stages), build_date)
    for stage in stages:
        log.info("  [phase %d] %s — %s", stage.phase, stage.name, stage.description)

    if dry_run:
        log.info("(dry run — no stages executed)")
        return 0

    # Make the build date available to transforms via module-level
    # import. Transforms that write metadata.generated should use
    # ``from build.pipeline import BUILD_DATE`` instead of calling
    # date.today() independently. This is set once here and never
    # changes during a pipeline run.
    global BUILD_DATE  # noqa: PLW0603
    BUILD_DATE = build_date

    print()
    failures: list[tuple[str, Exception]] = []
    total_elapsed = 0.0
    for stage in stages:
        log.info("Running: %s", stage.name)
        t0 = time.monotonic()
        try:
            # Run the stage with a timeout to prevent indefinite hangs.
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(stage.runner)
                future.result(timeout=STAGE_TIMEOUT)
            elapsed = time.monotonic() - t0
            total_elapsed += elapsed
            log.info("  ok: %s (%.1fs)", stage.name, elapsed)
        except NotImplementedError as exc:
            elapsed = time.monotonic() - t0
            total_elapsed += elapsed
            log.info("  pending: %s", exc)
        except FuturesTimeout:
            elapsed = time.monotonic() - t0
            total_elapsed += elapsed
            timeout_exc = TimeoutError(
                f"Stage '{stage.name}' timed out after {STAGE_TIMEOUT}s"
            )
            failures.append((stage.name, timeout_exc))
            log.error("  TIMEOUT: %s (after %ds)", stage.name, STAGE_TIMEOUT)
        except (RuntimeError, ValueError, FileNotFoundError, OSError,
                KeyError, TypeError, json.JSONDecodeError) as exc:
            elapsed = time.monotonic() - t0
            total_elapsed += elapsed
            failures.append((stage.name, exc))
            log.error("  FAILED: %s (%.1fs)", exc, elapsed)
        except Exception as exc:
            elapsed = time.monotonic() - t0
            total_elapsed += elapsed
            failures.append((stage.name, exc))
            log.error(
                "  FAILED (unexpected %s): %s (%.1fs)",
                type(exc).__name__, exc, elapsed,
            )
            traceback.print_exc()

    if failures:
        log.error(
            "%d stage(s) failed (%.1fs total):", len(failures), total_elapsed,
        )
        for name, exc in failures:
            log.error("  %s: %s", name, exc)
        return 1

    log.info("Pipeline complete (%.1fs total).", total_elapsed)
    return 0


# Build date for the current pipeline run. Set by run_pipeline() at
# startup. Transforms should import this instead of calling
# date.today() independently to avoid cross-midnight inconsistency.
BUILD_DATE: str = date.today().isoformat()


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
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable DEBUG-level logging.",
    )
    args = parser.parse_args(argv)
    return run_pipeline(
        include_names=args.with_names,
        dry_run=args.dry_run,
        only=args.only,
        verbose=args.verbose,
    )


if __name__ == "__main__":
    sys.exit(main())
