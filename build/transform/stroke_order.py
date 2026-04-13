"""Stroke order transform.

Extracts the KanjiVG main ZIP archive and places one SVG per character
in ``data/enrichment/stroke-order/``, named by the character itself.
Also emits an index JSON mapping each character to its SVG filename,
stroke count (parsed from the SVG), and Unicode codepoint.

Input: ``sources/kanjivg/kanjivg-main.zip`` (~12.6 MB, 6,702 SVG files)

Outputs:
    * ``data/enrichment/stroke-order/<char>.svg`` — one per kanji; the
      file content is the raw SVG from KanjiVG with stroke order
      metadata embedded in the ``kvg:element`` and ``kvg:original``
      attributes.
    * ``data/enrichment/stroke-order-index.json`` — lookup per character
      to its SVG filename and stroke count.

KanjiVG files are named with zero-padded hex codepoints (e.g.,
``065e5.svg`` for 日). We filter to characters that appear in our
``data/core/kanji.json`` when it exists (ensuring the stroke-order
coverage aligns with our kanji dataset), else include every SVG in the
zip.

Stroke count is extracted by counting the number of ``<path>`` elements
in the SVG. This matches KanjiVG's convention: one path per stroke.
"""

from __future__ import annotations
import logging

import json
import re
import shutil
import zipfile
from pathlib import Path
from build.pipeline import BUILD_DATE

log = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parents[2]
SOURCE_ZIP = REPO_ROOT / "sources" / "kanjivg" / "kanjivg-main.zip"
OUT_DIR = REPO_ROOT / "data" / "enrichment" / "stroke-order"
OUT_INDEX = REPO_ROOT / "data" / "enrichment" / "stroke-order-index.json"
KANJI_JSON = REPO_ROOT / "data" / "core" / "kanji.json"

# Match <path ... /> elements (stroke paths in KanjiVG SVGs)
PATH_RE = re.compile(r"<path\b[^>]*\bid=", re.ASCII)

# KanjiVG filename format: 5+ hex digit lowercase codepoint with .svg
KANJIVG_NAME_RE = re.compile(r"^kanji/([0-9a-f]{5,}(?:-[A-Za-z]+)?)\.svg$")


def _codepoint_filename(ch: str) -> str:
    """Return the expected KanjiVG filename (without directory) for a char."""
    if len(ch) != 1:
        raise ValueError(f"Expected single-character input, got {ch!r}")
    return f"{ord(ch):05x}.svg"


def _load_kanji_set() -> set[str]:
    """Load the set of kanji characters we have in data/core/kanji.json.

    Returns an empty set if kanji.json does not yet exist (first-run).
    """
    if not KANJI_JSON.exists():
        return set()
    try:
        data = json.loads(KANJI_JSON.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return set()
    return {entry["character"] for entry in data.get("kanji", [])}


def _count_strokes(svg_text: str) -> int:
    """Count stroke paths in an SVG by counting <path> elements with id.

    KanjiVG uses one <path> per stroke and each has an id like
    ``kvg:XXXXX-s1``, ``kvg:XXXXX-s2``, etc.
    """
    return len(PATH_RE.findall(svg_text))


def build() -> None:
    log.info(f"extracting {SOURCE_ZIP.name}")

    # Ensure clean output directory — stroke order is a full re-extract
    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # Filter to characters in kanji.json if available
    kanji_set = _load_kanji_set()
    if kanji_set:
        log.info(f"filtering to {len(kanji_set):,} characters in data/core/kanji.json")
    else:
        log.info("[stroke]   no kanji.json found; including every SVG in the ZIP")

    # Build character-to-codepoint map for the filter
    expected_codepoints: set[str] | None = None
    if kanji_set:
        expected_codepoints = set()
        for ch in kanji_set:
            if len(ch) == 1:
                expected_codepoints.add(f"{ord(ch):05x}")

    index_entries: dict[str, dict] = {}
    total_svgs = 0
    written = 0

    with zipfile.ZipFile(SOURCE_ZIP) as zf:
        for member_name in zf.namelist():
            match = KANJIVG_NAME_RE.match(member_name)
            if not match:
                continue
            total_svgs += 1
            stem = match.group(1)
            # Skip variant files (those with a hyphen suffix like 065e5-Kaisho.svg)
            if "-" in stem:
                continue
            # Apply the kanji.json filter if we have one
            if expected_codepoints is not None and stem not in expected_codepoints:
                continue
            # Decode the codepoint to a character
            try:
                codepoint = int(stem, 16)
                char = chr(codepoint)
            except (ValueError, OverflowError):
                continue

            svg_bytes = zf.read(member_name)
            svg_text = svg_bytes.decode("utf-8")
            stroke_count = _count_strokes(svg_text)

            # Write the SVG under a human-friendly filename: the character itself
            # plus .svg. Fallback to the hex if the character is not safe for
            # filesystems (e.g., contains reserved chars — not a concern for kanji).
            out_filename = f"{char}.svg"
            out_path = OUT_DIR / out_filename
            out_path.write_bytes(svg_bytes)
            written += 1

            index_entries[char] = {
                "svg": out_filename,
                "stroke_count": stroke_count,
                "unicode": f"{codepoint:05x}",
            }

    log.info(f"total SVGs in ZIP: {total_svgs:,}  written: {written:,}")

    # For kanji in our dataset without a stroke order SVG, record them with svg=null.
    # Iterate in sorted order so the insertion sequence is deterministic: the
    # output must be byte-reproducible across rebuilds (see docs/architecture.md §1).
    if kanji_set:
        missing = 0
        for ch in sorted(kanji_set):
            if ch not in index_entries:
                missing += 1
                if len(ch) == 1:
                    index_entries[ch] = {
                        "svg": None,
                        "stroke_count": None,
                        "unicode": f"{ord(ch):05x}",
                    }
        log.info(f"kanji without SVG (recorded as null): {missing:,}")

    # Review recommendation #9: compute stroke-count mismatches against
    # KANJIDIC2 and record in metadata so consumers are aware that
    # KanjiVG's path-based stroke count can differ from KANJIDIC2's
    # canonical count in ~2% of cases. Consumers should prefer KANJIDIC2
    # for canonical counts.
    mismatches: list[dict] = []
    if KANJI_JSON.exists():
        kanji_doc = json.loads(KANJI_JSON.read_text(encoding="utf-8"))
        kanji_stroke_counts = {
            k["character"]: k["stroke_count"]
            for k in kanji_doc.get("kanji", [])
            if k.get("stroke_count") is not None
        }
        for ch, entry in index_entries.items():
            kvg_count = entry.get("stroke_count")
            if kvg_count is None:
                continue
            kd_count = kanji_stroke_counts.get(ch)
            if kd_count is None:
                continue
            if kvg_count != kd_count:
                mismatches.append({
                    "character": ch,
                    "kanjidic2_count": kd_count,
                    "kanjivg_count": kvg_count,
                })
        mismatches.sort(key=lambda m: m["character"])
        log.info(f"stroke-count mismatches vs KANJIDIC2: {len(mismatches):,}")

    warnings: list[str] = []
    if mismatches:
        warnings.append(
            f"{len(mismatches)} characters have a KanjiVG stroke count that differs "
            f"from KANJIDIC2's count (see stroke_count_mismatches below for details). "
            f"KANJIDIC2 is the canonical source; prefer data/core/kanji.json for stroke counts."
        )
    total_chars = len(index_entries)
    svg_available = sum(1 for e in index_entries.values() if e.get("svg") is not None)
    if total_chars > 0:
        coverage_pct = 100.0 * svg_available / total_chars
        if coverage_pct < 80:
            warnings.append(
                f"Only {svg_available:,}/{total_chars:,} ({coverage_pct:.1f}%) characters "
                f"in our kanji.json have a corresponding KanjiVG SVG. The remaining "
                f"{total_chars - svg_available:,} characters are recorded with svg=null "
                f"and have no stroke order data upstream."
            )

    output = {
        "metadata": {
            "source": "KanjiVG (non-variant main distribution)",
            "source_url": "https://kanjivg.tagaini.net/",
            "license": "CC-BY-SA 3.0 Unported",
            "source_version": "r20250816",
            "generated": BUILD_DATE,
            "count": len(index_entries),
            "svg_directory": "data/enrichment/stroke-order/",
            "attribution": (
                "Stroke order data (kanji vector graphics) from the KanjiVG "
                "project, by Ulrich Apel and contributors, released under "
                "CC-BY-SA 3.0. See https://kanjivg.tagaini.net/"
            ),
            "field_notes": {
                "svg": "Filename of the SVG file relative to svg_directory. Null if no stroke order data is available for this character.",
                "stroke_count": "Stroke count derived from counting <path> elements in the SVG. May differ from KANJIDIC2's stroke_count in edge cases; consumers should prefer KANJIDIC2 for canonical counts.",
                "unicode": "Unicode codepoint in lowercase hex (the KanjiVG filename stem).",
            },
            "warnings": warnings,
            "stroke_count_mismatches": mismatches,
        },
        # Emit characters in sorted Unicode-codepoint order so rebuilds
        # produce byte-identical output (see docs/architecture.md §1).
        "characters": dict(sorted(index_entries.items())),
    }

    OUT_INDEX.parent.mkdir(parents=True, exist_ok=True)
    with OUT_INDEX.open("w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
        f.write("\n")
    log.info(f"wrote {OUT_INDEX.relative_to(REPO_ROOT)} ({len(index_entries):,} entries)")
