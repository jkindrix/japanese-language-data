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
    ("data/enrichment/sentence-difficulty.json", "entries"),
    ("data/enrichment/frequency-tatoeba.json", "entries"),
    ("data/enrichment/frequency-jesc.json", "entries"),
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
    ("data/cross-refs/grammar-to-sentences.json", "mapping"),
    ("data/cross-refs/sentence-to-words.json", "mapping"),
    ("data/cross-refs/grammar-to-words.json", "mapping"),
    ("data/cross-refs/kanji-to-sentences-full.json", "mapping"),
    ("data/cross-refs/word-relations.json", "relations"),
    ("data/corpus/sentences-jesc.json", "sentences"),
    ("data/corpus/sentences-wikimatrix.json", "sentences"),
    ("data/cross-refs/wordnet-synonyms.json", "relations"),
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
    "data/corpus/sentences-kftt.json",
    "data/corpus/sentences-tatoeba-full.json",
    "data/corpus/sentences-jesc.json",
    "data/corpus/sentences-wikimatrix.json",
    "data/enrichment/sentence-difficulty.json",
    "data/enrichment/frequency-tatoeba.json",
    "data/enrichment/frequency-jesc.json",
    "data/cross-refs/wordnet-synonyms.json",
    "data/cross-refs/kanji-to-words-full.json",
    "data/cross-refs/word-to-kanji-full.json",
    "data/cross-refs/reading-to-words-full.json",
    "data/cross-refs/kanji-to-sentences-full.json",
    "data/optional/names.json",
}


def compute_stroke_order_coverage() -> dict[str, dict]:
    """Compute stroke order SVG coverage per Joyo grade.

    Returns a dict with per-grade counts and an overall summary.
    Requires both kanji.json and stroke-order-index.json to exist.
    """
    kanji_path = REPO_ROOT / "data" / "core" / "kanji.json"
    stroke_path = REPO_ROOT / "data" / "enrichment" / "stroke-order-index.json"
    if not kanji_path.exists() or not stroke_path.exists():
        return {}

    kanji_data = json.loads(kanji_path.read_text(encoding="utf-8"))
    stroke_data = json.loads(stroke_path.read_text(encoding="utf-8"))
    characters = stroke_data.get("characters", {})

    # Group kanji by grade. Joyo = grades 1-6, 8. Jinmeiyo = grades 9, 10.
    JOYO_GRADES = {1, 2, 3, 4, 5, 6, 8}
    grade_chars: dict[int, list[str]] = {}
    for k in kanji_data.get("kanji", []):
        grade = k.get("grade")
        if grade is not None:
            grade_chars.setdefault(grade, []).append(k["character"])

    result: dict[str, dict] = {}
    joyo_total = 0
    joyo_with_svg = 0
    for grade in sorted(grade_chars):
        chars = grade_chars[grade]
        with_svg = sum(
            1 for ch in chars
            if ch in characters and characters[ch].get("svg") is not None
        )
        label = f"grade_{grade}"
        result[label] = {
            "total": len(chars),
            "with_svg": with_svg,
            "coverage_pct": round(100.0 * with_svg / len(chars), 1) if chars else 0,
        }
        if grade in JOYO_GRADES:
            joyo_total += len(chars)
            joyo_with_svg += with_svg

    # Joyo summary (grades 1-6, 8 only)
    result["joyo_total"] = {
        "total": joyo_total,
        "with_svg": joyo_with_svg,
        "coverage_pct": round(100.0 * joyo_with_svg / joyo_total, 1) if joyo_total else 0,
    }

    # Overall (all kanji in index)
    all_total = len(characters)
    all_with_svg = sum(1 for e in characters.values() if e.get("svg") is not None)
    result["all_kanji"] = {
        "total": all_total,
        "with_svg": all_with_svg,
        "coverage_pct": round(100.0 * all_with_svg / all_total, 1) if all_total else 0,
    }

    return result


def compute_grammar_review_status() -> dict[str, dict]:
    """Compute grammar review status breakdown by JLPT level.

    Returns a dict with per-level and overall counts of draft,
    community_reviewed, and native_speaker_reviewed entries.
    """
    grammar_path = REPO_ROOT / "data" / "grammar" / "grammar.json"
    if not grammar_path.exists():
        return {}

    data = json.loads(grammar_path.read_text(encoding="utf-8"))
    points = data.get("grammar_points", [])

    level_status: dict[str, dict[str, int]] = {}
    for p in points:
        level = p.get("jlpt_level", "unknown")
        status = p.get("review_status", "draft")
        bucket = level_status.setdefault(level, {"draft": 0, "community_reviewed": 0, "native_speaker_reviewed": 0, "total": 0})
        bucket[status] = bucket.get(status, 0) + 1
        bucket["total"] += 1

    # Add overall totals
    overall = {"draft": 0, "community_reviewed": 0, "native_speaker_reviewed": 0, "total": 0}
    for bucket in level_status.values():
        for key in overall:
            overall[key] += bucket[key]
    level_status["all"] = overall

    return level_status


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

    # Stroke order coverage by grade
    stroke_cov = compute_stroke_order_coverage()
    if stroke_cov:
        print()
        print("Stroke order SVG coverage:")
        grade_labels = {1: "Grade 1", 2: "Grade 2", 3: "Grade 3", 4: "Grade 4",
                        5: "Grade 5", 6: "Grade 6", 8: "Secondary Joyo",
                        9: "Jinmeiyo (9)", 10: "Jinmeiyo (10)"}
        joyo_grades = sorted(k for k in stroke_cov if k.startswith("grade_") and int(k.split("_")[1]) in {1, 2, 3, 4, 5, 6, 8})
        jinmeiyo_grades = sorted(k for k in stroke_cov if k.startswith("grade_") and int(k.split("_")[1]) in {9, 10})
        for key in joyo_grades:
            grade_num = int(key.split("_")[1])
            info = stroke_cov[key]
            label = grade_labels.get(grade_num, f"Grade {grade_num}")
            print(f"  {label:<20} {info['with_svg']:>5}/{info['total']:<5} ({info['coverage_pct']}%)")
        joyo = stroke_cov.get("joyo_total", {})
        if joyo:
            print(f"  {'Joyo total':<20} {joyo['with_svg']:>5}/{joyo['total']:<5} ({joyo['coverage_pct']}%)")
        if jinmeiyo_grades:
            for key in jinmeiyo_grades:
                grade_num = int(key.split("_")[1])
                info = stroke_cov[key]
                label = grade_labels.get(grade_num, f"Grade {grade_num}")
                print(f"  {label:<20} {info['with_svg']:>5}/{info['total']:<5} ({info['coverage_pct']}%)")
        all_k = stroke_cov.get("all_kanji", {})
        if all_k:
            print(f"  {'All KANJIDIC2':<20} {all_k['with_svg']:>5}/{all_k['total']:<5} ({all_k['coverage_pct']}%)")

    # Grammar review status
    grammar_status = compute_grammar_review_status()
    if grammar_status:
        print()
        print("Grammar review status:")
        for level in ["N5", "N4", "N3", "N2", "N1"]:
            info = grammar_status.get(level, {})
            if not info:
                continue
            reviewed = info.get("community_reviewed", 0) + info.get("native_speaker_reviewed", 0)
            print(f"  {level:<5} {reviewed:>3}/{info['total']:<3} reviewed  ({info.get('native_speaker_reviewed', 0)} native, {info.get('community_reviewed', 0)} community, {info.get('draft', 0)} draft)")
        overall = grammar_status.get("all", {})
        if overall:
            reviewed = overall.get("community_reviewed", 0) + overall.get("native_speaker_reviewed", 0)
            print(f"  {'Total':<5} {reviewed:>3}/{overall['total']:<3} reviewed")


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

    # Add enrichment quality metrics
    stroke_cov = compute_stroke_order_coverage()
    if stroke_cov:
        manifest["stroke_order_coverage"] = stroke_cov

    grammar_status = compute_grammar_review_status()
    if grammar_status:
        manifest["grammar_review_status"] = grammar_status
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
