"""Radicals (KRADFILE + RADKFILE + Wikipedia Kangxi) transform.

Reads KRADFILE (kanji → component radicals) and RADKFILE (radical → kanji
containing it) from the jmdict-simplified JSON releases and combines them
into a single bidirectional radical dataset. Populates English meanings
and Kangxi radical numbers by parsing the Wikipedia 'Kangxi radicals'
article wikitext (pinned upstream revision).

Inputs:
    * ``sources/jmdict-simplified/kradfile.json.tgz``
    * ``sources/jmdict-simplified/radkfile.json.tgz``
    * ``sources/wikipedia/kangxi-radicals.wikitext`` (Wikipedia, CC-BY-SA 4.0)

Output: ``data/core/radicals.json`` conforming to
``schemas/radical.schema.json``.

The combined structure has two top-level views:
    * ``radicals`` — list of radical entries (from RADKFILE), each with
      radical character, stroke count, Kangxi number (from Wikipedia),
      English meanings (from Wikipedia), and the kanji that contain it.
    * ``kanji_to_radicals`` — map from each kanji to its component radicals
      (from KRADFILE). Inverse of the above.

Meaning and Kangxi-number population logic:

    1. Parse the Wikipedia 'Kangxi radicals' wikitable to extract the
       214 classical radicals plus their documented alternate forms
       (e.g., 人 with alternates 亻 and 𠆢).
    2. For each radical in RADKFILE, look up its character in the
       Wikipedia mapping (primary OR alternate form counts as a match)
       and populate classical_number + meanings if found.
    3. Characters that don't match directly stay with empty meanings
       and null classical_number — these are Japanese-dictionary-specific
       variants (simplified forms, katakana-shaped markers, etc.) that
       would require a curated alias table to bridge to Kangxi. That
       table is deferred as a future patch.

Coverage is reported in the metadata (radicals_with_meaning /
radicals_total) so consumers can see the exact state.
"""

from __future__ import annotations

import json
import re
import tarfile
from pathlib import Path
from datetime import date

REPO_ROOT = Path(__file__).resolve().parents[2]
KRADFILE_TGZ = REPO_ROOT / "sources" / "jmdict-simplified" / "kradfile.json.tgz"
RADKFILE_TGZ = REPO_ROOT / "sources" / "jmdict-simplified" / "radkfile.json.tgz"
WIKIPEDIA_WIKITEXT = REPO_ROOT / "sources" / "wikipedia" / "kangxi-radicals.wikitext"
OUT = REPO_ROOT / "data" / "core" / "radicals.json"

WIKIPEDIA_REVID = 1346511063
WIKIPEDIA_URL = (
    f"https://en.wikipedia.org/w/index.php?title=Kangxi_radicals&oldid={WIKIPEDIA_REVID}"
)


def _load_source(tgz_path: Path) -> dict:
    with tarfile.open(tgz_path, "r:gz") as tf:
        for member in tf.getmembers():
            if member.name.endswith(".json"):
                f = tf.extractfile(member)
                if f is None:
                    raise RuntimeError(f"Cannot extract {member.name}")
                return json.loads(f.read().decode("utf-8"))
    raise RuntimeError(f"No JSON file found in {tgz_path}")


# ---------------------------------------------------------------------------
# Wikipedia Kangxi radicals parser
# ---------------------------------------------------------------------------

_LANG_TEMPLATE_RE = re.compile(r"\{\{lang\|[^|}]+\|([^|}]+)\}\}")


def _extract_wikitable(wikitext: str) -> str:
    """Return the first ``{| class="wikitable ... |}`` block in wikitext.

    Handles nested tables by counting ``{|`` / ``|}`` pairs.
    """
    start = wikitext.find('{| class="wikitable')
    if start < 0:
        raise RuntimeError("Could not find the Kangxi radicals wikitable.")
    depth = 0
    i = start
    while i < len(wikitext):
        if wikitext[i:i + 2] == "{|":
            depth += 1
            i += 2
        elif wikitext[i:i + 2] == "|}":
            depth -= 1
            if depth == 0:
                return wikitext[start:i + 2]
            i += 2
        else:
            i += 1
    raise RuntimeError("Kangxi radicals wikitable has unbalanced table syntax.")


def _parse_row_cells(row: str) -> list[str]:
    """Split a wikitable row into its cells. Handles leading style attrs."""
    cells: list[str] = []
    current: str | None = None
    for line in row.split("\n"):
        if line.startswith("|"):
            if current is not None:
                cells.append(current)
            text = line[1:]  # drop leading |
            # Drop an optional leading "style=...|" attribute
            if text.startswith("style="):
                pipe_idx = text.find("|")
                if pipe_idx >= 0:
                    text = text[pipe_idx + 1:]
            current = text
        elif current is not None:
            current += " " + line
    if current is not None:
        cells.append(current)
    return cells


def _extract_radical_forms(cell: str) -> tuple[str | None, list[str]]:
    """From the 'Radical forms' cell of a Kangxi row, extract the primary
    radical character and any alternate forms.

    Wikipedia cells look like::

        '''<big>{{lang|zh-Hant|人}}<br/>({{lang|zh|亻}}、{{lang|zh|𠆢}})</big>'''

    Returns (primary, [alternates]). Alternates may be empty.
    """
    chars = _LANG_TEMPLATE_RE.findall(cell)
    primary: str | None = None
    alternates: list[str] = []
    for ch in chars:
        # Wikipedia cells can pack multiple chars inside a single {{lang}} via 、
        parts = [p.strip() for p in ch.split("、") if p.strip()]
        for p in parts:
            if primary is None:
                primary = p
            else:
                alternates.append(p)
    return primary, alternates


def _strip_wiki_markup(text: str) -> str:
    """Strip common wiki markup from a plain-text cell."""
    # [[link|display]] -> display
    text = re.sub(r"\[\[([^|\]]+)\|([^\]]+)\]\]", r"\2", text)
    # [[link]] -> link
    text = re.sub(r"\[\[([^\]]+)\]\]", r"\1", text)
    # triple and double quotes
    text = re.sub(r"'''", "", text)
    text = re.sub(r"''", "", text)
    # HTML tags
    text = re.sub(r"<[^>]+>", "", text)
    return text.strip()


def _parse_kangxi_wikitext(wikitext: str) -> dict[str, dict]:
    """Parse the Wikipedia Kangxi wikitable into a mapping.

    Returns a dict keyed by each radical character (primary OR alternate
    form) to a dict with:
        * number: Kangxi radical number (1-214)
        * meanings: list of English meanings (from the 'Meaning' column,
          split on commas if the column contains multiple words)
        * primary: the primary radical character for this number
        * stroke_count: as listed on Wikipedia (may differ from RADKFILE
          for a small number of characters; we DO NOT overwrite RADKFILE's
          stroke counts, which come from EDRDG)
    """
    table = _extract_wikitable(wikitext)
    rows = re.split(r"\n\|----\n", table)
    # First row is the header; skip it.
    mapping: dict[str, dict] = {}
    for row in rows[1:]:
        cells = _parse_row_cells(row)
        if len(cells) < 4:
            continue
        # Cell 0: [[Radical N|N]]
        m = re.search(r"\[\[Radical\s+(\d+)", cells[0])
        if not m:
            continue
        number = int(m.group(1))
        # Cell 1: primary + alternates
        primary, alternates = _extract_radical_forms(cells[1])
        if not primary:
            continue
        # Cell 2: stroke count (reference only; not written out)
        stroke_count: int | None = None
        sc_match = re.match(r"\s*(\d+)", cells[2])
        if sc_match:
            stroke_count = int(sc_match.group(1))
        # Cell 3: English meaning
        raw_meaning = _strip_wiki_markup(cells[3])
        meanings = [m.strip() for m in raw_meaning.split(",") if m.strip()]
        if not meanings:
            continue

        entry = {
            "number": number,
            "meanings": meanings,
            "primary": primary,
            "stroke_count": stroke_count,
        }
        mapping[primary] = entry
        for alt in alternates:
            # Alternates share the same meaning and Kangxi number as the primary
            mapping[alt] = entry
    return mapping


def _load_kangxi_mapping() -> dict[str, dict]:
    """Load and parse the Wikipedia Kangxi wikitext.

    Returns an empty dict if the source is not cached (allows radicals.build
    to run before the wikipedia-kangxi-radicals source is fetched, matching
    the project's progressive-enrichment pattern used in kanji.py).
    """
    if not WIKIPEDIA_WIKITEXT.exists():
        return {}
    wikitext = WIKIPEDIA_WIKITEXT.read_text(encoding="utf-8")
    return _parse_kangxi_wikitext(wikitext)


# ---------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------


def build() -> None:
    print(f"[radicals] loading {KRADFILE_TGZ.name} and {RADKFILE_TGZ.name}")
    krad = _load_source(KRADFILE_TGZ)
    radk = _load_source(RADKFILE_TGZ)

    kangxi_map = _load_kangxi_mapping()
    if kangxi_map:
        print(
            f"[radicals] loaded Wikipedia Kangxi mapping: "
            f"{len(kangxi_map):,} character → Kangxi entries "
            f"(214 primary + alternates)"
        )
    else:
        print("[radicals] Wikipedia Kangxi mapping unavailable — meanings will stay empty")

    kanji_to_radicals_raw = krad.get("kanji", {})
    kanji_to_radicals: dict[str, list[str]] = {
        k: list(v) for k, v in kanji_to_radicals_raw.items()
    }

    radicals_dict = radk.get("radicals", {})
    radicals_list: list[dict] = []
    matched = 0
    unmatched: list[str] = []
    for rad_char, rad_info in radicals_dict.items():
        kangxi_entry = kangxi_map.get(rad_char)
        classical_number = kangxi_entry["number"] if kangxi_entry else None
        meanings = list(kangxi_entry["meanings"]) if kangxi_entry else []
        if kangxi_entry:
            matched += 1
        else:
            unmatched.append(rad_char)
        radicals_list.append(
            {
                "radical": rad_char,
                "stroke_count": rad_info.get("strokeCount"),
                "classical_number": classical_number,
                "meanings": meanings,
                "kanji": list(rad_info.get("kanji", []) or []),
            }
        )

    total = len(radicals_list)
    coverage_pct = (100.0 * matched / total) if total else 0.0
    print(
        f"[radicals] kanji_to_radicals: {len(kanji_to_radicals):,}  "
        f"radicals: {total:,}  "
        f"with Kangxi mapping: {matched:,} ({coverage_pct:.1f}%)"
    )
    if unmatched:
        preview = "".join(unmatched[:20]) + ("..." if len(unmatched) > 20 else "")
        print(f"[radicals] radicals without Wikipedia match: {len(unmatched)} ({preview})")

    if kangxi_map:
        warning = (
            f"{matched} of {total} radicals ({coverage_pct:.1f}%) have English "
            f"meanings and Kangxi numbers populated from the Wikipedia 'Kangxi "
            f"radicals' article (CC-BY-SA 4.0, pinned to revision "
            f"{WIKIPEDIA_REVID}). The remaining {total - matched} radicals are "
            f"Japanese-dictionary-specific forms — simplified variants (e.g., "
            f"亀 for 龜), katakana-shaped markers (ノ, ハ, マ, ユ, ヨ), "
            f"fullwidth pipe (｜ for 丨), and other Nelson-style forms — which "
            f"have no direct match in the Wikipedia Kangxi table. Filling these "
            f"requires a curated variant-to-Kangxi alias table, deferred as a "
            f"future patch. See docs/phase4-candidates.md."
        )
    else:
        warning = (
            "Every radical entry in this file has an empty `meanings` array "
            "and `classical_number: null`. The Wikipedia Kangxi source is not "
            "cached; run `just fetch` first. See docs/phase4-candidates.md."
        )

    output = {
        "metadata": {
            "source": "KRADFILE + RADKFILE + Wikipedia Kangxi radicals",
            "source_url": "https://github.com/scriptin/jmdict-simplified",
            "license": (
                "CC-BY-SA 4.0: EDRDG License for KRADFILE/RADKFILE; "
                "CC-BY-SA 4.0 for Wikipedia-derived meanings and Kangxi numbers"
            ),
            "source_version_kradfile": krad.get("version", ""),
            "source_version_radkfile": radk.get("version", ""),
            "source_version_wikipedia": {
                "article": "Kangxi radicals",
                "revision": WIKIPEDIA_REVID,
                "url": WIKIPEDIA_URL,
            },
            "generated": date.today().isoformat(),
            "radicals_total": total,
            "radicals_with_meaning": matched,
            "radicals_meaning_coverage_pct": round(coverage_pct, 2),
            "attribution": (
                "This work uses KRADFILE and RADKFILE from the Electronic "
                "Dictionary Research and Development Group (EDRDG), used in "
                "conformance with the Group's license "
                "(https://www.edrdg.org/edrdg/licence.html). Radical English "
                "meanings and Kangxi radical numbers are derived from the "
                f"Wikipedia 'Kangxi radicals' article (revision {WIKIPEDIA_REVID}, "
                f"{WIKIPEDIA_URL}), used under CC-BY-SA 4.0. Wikipedia content "
                "is authored by Wikipedia contributors; see the article's "
                "revision history for attribution."
            ),
            "field_notes": {
                "radicals": "List view: each radical with stroke count (from RADKFILE), Kangxi number and meanings (from Wikipedia), and the kanji that contain it (from RADKFILE).",
                "kanji_to_radicals": "Inverse view: each kanji mapped to its component radicals. Derived from KRADFILE.",
                "classical_number": "Kangxi radical number (1–214). Sourced from the Wikipedia 'Kangxi radicals' article. Null for Japanese-dictionary-specific variants that do not appear in the Kangxi table.",
                "meanings": "English meanings. Sourced from the Wikipedia Kangxi article's 'Meaning' column, split on commas when the column contains multiple equivalent words (e.g., radical 10 儿 → ['son', 'legs']). Empty array for radicals not found in Wikipedia's Kangxi table.",
                "stroke_count": "Stroke count from RADKFILE (the authoritative source; Wikipedia's column is ignored to avoid conflicts).",
            },
            "warning": warning,
        },
        "radicals": radicals_list,
        "kanji_to_radicals": kanji_to_radicals,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"[radicals] wrote {OUT.relative_to(REPO_ROOT)}")
