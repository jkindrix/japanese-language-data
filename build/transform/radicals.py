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
from build.pipeline import BUILD_DATE

REPO_ROOT = Path(__file__).resolve().parents[2]
KRADFILE_TGZ = REPO_ROOT / "sources" / "jmdict-simplified" / "kradfile.json.tgz"
RADKFILE_TGZ = REPO_ROOT / "sources" / "jmdict-simplified" / "radkfile.json.tgz"
WIKIPEDIA_WIKITEXT = REPO_ROOT / "sources" / "wikipedia" / "kangxi-radicals.wikitext"
OUT = REPO_ROOT / "data" / "core" / "radicals.json"

WIKIPEDIA_REVID = 1346511063
WIKIPEDIA_URL = (
    f"https://en.wikipedia.org/w/index.php?title=Kangxi_radicals&oldid={WIKIPEDIA_REVID}"
)


# ---------------------------------------------------------------------------
# Variant-to-Kangxi alias table (v0.7.x Phase 4 expansion)
# ---------------------------------------------------------------------------
#
# RADKFILE's radical set includes 56 characters that are NOT found in the
# Wikipedia Kangxi radicals table (neither primary form nor documented
# alternate). These are Japanese-dictionary-specific variants:
#
#   * Simplified shinjitai forms whose traditional kyūjitai is in Kangxi
#     (e.g., 亀 for 龜, 麦 for 麥, 歯 for 齒).
#   * Radical-in-compound variants like 氵 (water), 忄 (heart), 扌 (hand),
#     艹 (grass), 阝 (city/mound), 犭 (dog), 礻 (spirit), 疒 (sickness),
#     辶 (walk). RADKFILE sometimes represents these using a representative
#     kanji containing the variant (e.g., 忙 standing for 忄/心; 汁 for
#     氵/水; 邦 for right-side 阝/邑; 阡 for left-side 阝/阜).
#   * Katakana-shaped positional markers (｜, ノ, ハ, ヨ) and Nelson-style
#     component indicators (个 for 人, etc.).
#
# This table maps each such variant to its Kangxi radical number. When a
# radical's character is missing from the Wikipedia primary/alternate
# mapping but appears in this table, the build copies the meaning and
# classical_number from the Kangxi primary entry.
#
# Not all 56 unmatched radicals are included. Entries below are
# high-confidence mappings where the connection to a specific Kangxi
# radical is unambiguous. Ambiguous Nelson-style variants (e.g., マ, ユ,
# 尚, 杰, 奄, 無) are omitted and remain unmatched — better to be honest
# about what we don't know than to assign an arbitrary parent.
KANGXI_ALIASES: dict[str, int] = {
    # Positional / shape markers → Kangxi primary
    "｜": 2,    # fullwidth pipe → 丨 (line)
    "ノ": 4,    # katakana-shaped → 丿 (slash)
    "ハ": 12,   # katakana-shaped → 八 (eight)
    "ヨ": 58,   # katakana-shaped → 彐 (snout)

    # Nelson-style representatives — kanji that contain a specific radical
    # component, treated as the "radical" in RADKFILE's list
    "忙": 61,   # ← 忄 variant → 心 (heart)
    "扎": 64,   # ← 扌 variant → 手 (hand)
    "汁": 85,   # ← 氵 variant → 水 (water)
    "滴": 85,   # ← 氵 variant → 水 (water)
    "犯": 94,   # ← 犭 variant → 犬 (dog)
    "艾": 140,  # ← 艹 variant → 艸 (grass)
    "邦": 163,  # ← 阝 right variant → 邑 (city)
    "阡": 170,  # ← 阝 left variant → 阜 (mound)
    "礼": 113,  # ← 礻 variant → 示 (spirit/altar)
    "疔": 104,  # ← 疒 representative → 疒 (sickness)
    "込": 162,  # ← 辶 variant → 辵 (walk)
    "攵": 66,   # ← attribution variant → 攴 (rap)

    # Shinjitai simplified forms → kyūjitai Kangxi radicals
    "麦": 199,  # simplified of 麥 (wheat)
    "亀": 213,  # simplified of 龜 (turtle)
    "黄": 201,  # simplified of 黃 (yellow)
    "黒": 203,  # simplified of 黑 (black)
    "竜": 212,  # simplified of 龍 (dragon)
    "歯": 211,  # simplified of 齒 (tooth)

    # Kanji-as-component indicators where the contained Kangxi radical is clear
    "冊": 13,   # contains 冂 (down box)
    "買": 154,  # contains 貝 (shell)
    "品": 30,   # contains 口 (mouth, three-fold)
    "岡": 46,   # contains 山 (mountain)
    "元": 10,   # contains 儿 (legs)
    "亡": 8,    # starts with 亠 (lid)
    "勿": 20,   # visual shape of 勹 (wrap)
    "尤": 43,   # variant of 尢 (lame)
    "屯": 45,   # variant of 屮 (sprout)
    "已": 49,   # variant of 己 (self)
    "乞": 5,    # contains 乙 (second)
    "也": 5,    # 乙-family variant
    "化": 9,    # contains 亻 → 人 (man)
    "个": 9,    # Nelson-style variant of 人 (man)
    "免": 10,   # contains 儿 (legs)
    "及": 29,   # contains 又 (again)
    "九": 5,    # 乙-family curve variant
    "乃": 4,    # 丿-family shape
    "久": 4,    # 丿-family shape
    "巨": 22,   # 匚-family shape (right-open box)
    "并": 12,   # simplification related to 八 / 幷
    "刈": 18,   # contains 刂 variant → 刀 (knife)
    "初": 18,   # contains 刀 (knife)
}


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
        import warnings
        warnings.warn(
            f"Wikipedia Kangxi source not found at {WIKIPEDIA_WIKITEXT}. "
            f"Radical meanings and Kangxi numbers will be empty. "
            f"Run `just fetch` to download upstream sources.",
            stacklevel=2,
        )
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

    # Build an auxiliary index from Kangxi number → primary entry so the
    # alias table can resolve variant → number → meanings in one hop.
    kangxi_by_number: dict[int, dict] = {}
    for entry in kangxi_map.values():
        number = entry["number"]
        if number not in kangxi_by_number:
            kangxi_by_number[number] = entry

    kanji_to_radicals_raw = krad.get("kanji", {})
    kanji_to_radicals: dict[str, list[str]] = {
        k: list(v) for k, v in kanji_to_radicals_raw.items()
    }

    radicals_dict = radk.get("radicals", {})
    radicals_list: list[dict] = []
    matched = 0
    matched_via_alias = 0
    unmatched: list[str] = []
    for rad_char, rad_info in radicals_dict.items():
        kangxi_entry = kangxi_map.get(rad_char)
        aliased_via_alias_table = False
        if kangxi_entry is None and rad_char in KANGXI_ALIASES:
            alias_number = KANGXI_ALIASES[rad_char]
            kangxi_entry = kangxi_by_number.get(alias_number)
            if kangxi_entry is not None:
                aliased_via_alias_table = True
        classical_number = kangxi_entry["number"] if kangxi_entry else None
        meanings = list(kangxi_entry["meanings"]) if kangxi_entry else []
        if kangxi_entry:
            matched += 1
            if aliased_via_alias_table:
                matched_via_alias += 1
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
        f"with Kangxi mapping: {matched:,} ({coverage_pct:.1f}%, "
        f"of which {matched_via_alias} via the curated alias table)"
    )
    if unmatched:
        preview = "".join(unmatched[:20]) + ("..." if len(unmatched) > 20 else "")
        print(f"[radicals] radicals without Wikipedia match: {len(unmatched)} ({preview})")

    if kangxi_map:
        warning = (
            f"{matched} of {total} radicals ({coverage_pct:.1f}%) have English "
            f"meanings and Kangxi numbers populated. The Wikipedia 'Kangxi "
            f"radicals' article (CC-BY-SA 4.0, revision {WIKIPEDIA_REVID}) "
            f"supplies the primary 214 Kangxi radicals and their documented "
            f"alternate forms. A curated variant-to-Kangxi alias table in "
            f"build/transform/radicals.py (KANGXI_ALIASES, {len(KANGXI_ALIASES)} "
            f"entries) bridges Japanese-dictionary-specific variants — "
            f"simplified shinjitai (亀→龜, 麦→麥, 歯→齒), radical-in-compound "
            f"variants (汁→水 via 氵, 忙→心 via 忄, 邦→邑 via right-side 阝), "
            f"and positional markers (｜→丨, ノ→丿, ハ→八, ヨ→彐) — to their "
            f"Kangxi parents. The remaining {total - matched} radicals are "
            f"Nelson-style variants whose Kangxi attribution is ambiguous "
            f"(e.g., マ, ユ, 尚, 奄, 杰, 無) and are left unmatched honestly "
            f"rather than assigned arbitrary parents. See "
            f"docs/phase4-candidates.md."
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
            "generated": BUILD_DATE,
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
