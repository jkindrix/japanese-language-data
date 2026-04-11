"""Kanji data transform.

Reads the KANJIDIC2 JSON from ``sources/jmdict-simplified/kanjidic2-all.json.tgz``
(ingested via scriptin/jmdict-simplified) and transforms it into our schema.

Outputs:
    * ``data/core/kanji.json`` — all 13,108 characters in KANJIDIC2
    * ``data/core/kanji-joyo.json`` — derived view filtered to Jōyō kanji
      (grade 1-6 kyōiku + grade 8 secondary), ~2,136 entries

Both conform to ``schemas/kanji.schema.json``. The Jōyō view is identical in
structure; it's just a filtered subset with its own metadata header.

Fields filled in later phases:
    * ``jlpt_waller`` — populated by Phase 2 jlpt transform (Waller lists)
    * ``radical_components`` — populated by Phase 2 cross_links from KRADFILE

The transform demuxes several upstream structures that pack multiple types
into a single list:
    * ``codepoints[]`` (keyed by type: ucs, jis208, jis212, jis213) → flat fields
    * ``radicals[]`` (keyed by type: classical, nelson_c) → radical object
    * ``readingMeaning.groups[].readings[]`` (mixed types: ja_on, ja_kun,
      pinyin, korean_r, korean_h, vietnam) → demuxed into readings and
      readings_cjk
    * ``readingMeaning.groups[].meanings[]`` (mixed languages) → demuxed
      into meanings dict by language
    * ``dictionaryReferences[]`` → flat ``dic_refs`` object (selected refs)
    * ``queryCodes[]`` → flat ``query_codes`` object

Known gaps tracked in ``docs/upstream-issues.md``:
    * SKIP codes with ``skipMisclassification`` flag: we keep only the
      primary SKIP code, dropping misclassification metadata.
    * Morohashi volume/page detail is dropped; only the value is kept.
"""

from __future__ import annotations

import json
import tarfile
from pathlib import Path
from datetime import date

REPO_ROOT = Path(__file__).resolve().parents[2]
SOURCE_TGZ = REPO_ROOT / "sources" / "jmdict-simplified" / "kanjidic2-all.json.tgz"
OUT_FULL = REPO_ROOT / "data" / "core" / "kanji.json"
OUT_JOYO = REPO_ROOT / "data" / "core" / "kanji-joyo.json"
OUT_JINMEIYO = REPO_ROOT / "data" / "core" / "kanji-jinmeiyo.json"

# Optional enrichment inputs produced by other transforms. kanji.build()
# will read these if they exist and populate the corresponding fields;
# otherwise those fields stay null/empty (backward-compatible with Phase 1).
JLPT_ENRICHMENT = REPO_ROOT / "data" / "enrichment" / "jlpt-classifications.json"
RADICALS_ENRICHMENT = REPO_ROOT / "data" / "core" / "radicals.json"

# Dictionary reference types to keep (from EDRDG License §8 contributors)
WANTED_DIC_REFS = {
    "nelson_c",
    "nelson_n",
    "halpern_njecd",
    "halpern_kkld_2ed",
    "heisig",
    "heisig6",
    "oneill_kk",
    "moro",
    "kodansha_compact",
    "henshall",
    "gakken",
}

WANTED_QUERY_CODES = {"skip", "four_corner", "sh_desc", "deroo"}

JOYO_GRADES = {1, 2, 3, 4, 5, 6, 8}
JINMEIYO_GRADES = {9, 10}  # Kanji approved for personal-name use (per the jinmeiyō list)


def _load_source() -> dict:
    """Extract and parse the KANJIDIC2 JSON from its tgz archive."""
    with tarfile.open(SOURCE_TGZ, "r:gz") as tf:
        # The archive contains exactly one .json file.
        for member in tf.getmembers():
            if member.name.endswith(".json"):
                f = tf.extractfile(member)
                if f is None:
                    raise RuntimeError(f"Cannot extract {member.name}")
                return json.loads(f.read().decode("utf-8"))
    raise RuntimeError(f"No JSON file found in {SOURCE_TGZ}")


def _load_kanji_jlpt_map() -> dict[str, str]:
    """Build a char → JLPT level map from the enrichment file if it exists."""
    if not JLPT_ENRICHMENT.exists():
        return {}
    data = json.loads(JLPT_ENRICHMENT.read_text(encoding="utf-8"))
    result: dict[str, str] = {}
    for entry in data.get("classifications", []):
        if entry.get("kind") == "kanji":
            text = entry.get("text", "")
            level = entry.get("level")
            if text and level:
                result[text] = level
    return result


def _load_radical_components_map() -> dict[str, list[str]]:
    """Build a kanji → component radicals map from radicals.json if it exists."""
    if not RADICALS_ENRICHMENT.exists():
        return {}
    data = json.loads(RADICALS_ENRICHMENT.read_text(encoding="utf-8"))
    return data.get("kanji_to_radicals", {}) or {}


def _transform_character(
    ch: dict,
    jlpt_map: dict[str, str] | None = None,
    radical_map: dict[str, list[str]] | None = None,
) -> dict:
    """Transform a single KANJIDIC2 character entry to our schema."""
    jlpt_map = jlpt_map or {}
    radical_map = radical_map or {}
    literal = ch["literal"]

    # Codepoints — demux by type
    unicode_hex = None
    jis208 = None
    jis212 = None
    jis213 = None
    for cp in ch.get("codepoints", []):
        t = cp.get("type")
        v = cp.get("value")
        if t == "ucs":
            unicode_hex = v
        elif t == "jis208":
            jis208 = v
        elif t == "jis212":
            jis212 = v
        elif t == "jis213":
            jis213 = v

    # Radicals — demux by type
    rad_classical = None
    rad_nelson = None
    for rad in ch.get("radicals", []):
        t = rad.get("type")
        v = rad.get("value")
        if t == "classical":
            rad_classical = v
        elif t == "nelson_c":
            rad_nelson = v

    # Misc (grade, stroke count, frequency, old JLPT, variants)
    misc = ch.get("misc", {}) or {}
    stroke_counts = misc.get("strokeCounts", []) or []
    stroke_count = stroke_counts[0] if stroke_counts else None
    stroke_count_variants = stroke_counts[1:] if len(stroke_counts) > 1 else []

    grade = misc.get("grade")
    jlpt_old = misc.get("jlptLevel")
    frequency = misc.get("frequency")

    variants = []
    for v in misc.get("variants", []) or []:
        variants.append({"type": v.get("type", ""), "value": v.get("value", "")})

    # Dictionary references — demux by type, keep only wanted ones
    dic_refs: dict[str, str] = {}
    for dr in ch.get("dictionaryReferences", []) or []:
        t = dr.get("type")
        if t in WANTED_DIC_REFS:
            value = dr.get("value")
            if value is not None:
                dic_refs[t] = str(value)

    # Query codes — take the primary (non-misclassified) SKIP code and
    # other wanted codes.
    query_codes: dict[str, str] = {}
    for qc in ch.get("queryCodes", []) or []:
        t = qc.get("type")
        if t not in WANTED_QUERY_CODES:
            continue
        # For SKIP codes, prefer the one without skipMisclassification.
        # See docs/upstream-issues.md for the schema gap.
        if t == "skip" and qc.get("skipMisclassification"):
            continue
        if t not in query_codes:
            query_codes[t] = str(qc.get("value", ""))

    # Readings and meanings — walk rmgroups, demux by type/lang
    on_readings: list[str] = []
    kun_readings: list[str] = []
    pinyin: list[str] = []
    korean_romanized: list[str] = []
    korean_hangul: list[str] = []
    vietnamese: list[str] = []
    meanings: dict[str, list[str]] = {"en": [], "fr": [], "es": [], "pt": []}

    reading_meaning = ch.get("readingMeaning") or {}
    for group in reading_meaning.get("groups", []) or []:
        for r in group.get("readings", []) or []:
            rt = r.get("type")
            val = r.get("value", "")
            if rt == "ja_on":
                on_readings.append(val)
            elif rt == "ja_kun":
                kun_readings.append(val)
            elif rt == "pinyin":
                pinyin.append(val)
            elif rt == "korean_r":
                korean_romanized.append(val)
            elif rt == "korean_h":
                korean_hangul.append(val)
            elif rt == "vietnam":
                vietnamese.append(val)
        for m in group.get("meanings", []) or []:
            lang = m.get("lang", "en")
            if lang in meanings:
                meanings[lang].append(m.get("value", ""))

    nanori = list(reading_meaning.get("nanori", []) or [])

    entry: dict = {
        "character": literal,
        "unicode": unicode_hex,
        "jis208": jis208,
        "stroke_count": stroke_count,
        "stroke_count_variants": stroke_count_variants,
        "grade": grade,
        "jlpt_old": jlpt_old,
        "jlpt_waller": jlpt_map.get(literal),  # None if no Waller classification
        "frequency": frequency,
        "radical": {
            "classical": rad_classical,
            "nelson": rad_nelson,
        },
        "radical_components": list(radical_map.get(literal, [])),
        "meanings": meanings,
        "readings": {
            "on": on_readings,
            "kun": kun_readings,
        },
        "readings_cjk": {
            "pinyin": pinyin,
            "korean_romanized": korean_romanized,
            "korean_hangul": korean_hangul,
            "vietnamese": vietnamese,
        },
        "nanori": nanori,
        "variants": variants,
        "dic_refs": dic_refs,
        "query_codes": query_codes,
    }

    # Include jis212/jis213 only if present (schema has them as optional)
    if jis212 is not None:
        entry["jis212"] = jis212
    if jis213 is not None:
        entry["jis213"] = jis213

    return entry


def _metadata(source_meta: dict, count: int, filter_note: str = "") -> dict:
    """Build the metadata header for the output file."""
    return {
        "source": "KANJIDIC2 via scriptin/jmdict-simplified",
        "source_url": "https://github.com/scriptin/jmdict-simplified",
        "license": "CC-BY-SA 4.0 (EDRDG License)",
        "source_version": source_meta.get("version", ""),
        "upstream_dict_date": source_meta.get("dictDate", ""),
        "upstream_database_version": source_meta.get("databaseVersion", ""),
        "upstream_file_version": source_meta.get("fileVersion"),
        "upstream_languages": source_meta.get("languages", []),
        "generated": date.today().isoformat(),
        "count": count,
        "filter": filter_note,
        "attribution": (
            "This work uses KANJIDIC2 from the Electronic Dictionary Research "
            "and Development Group (EDRDG), used in conformance with the "
            "Group's license. See https://www.edrdg.org/edrdg/licence.html. "
            "Per-field contributors: SKIP codes (Jack Halpern), pinyin "
            "(Christian Wittern and Koichi Yasuoka), Four Corner codes and "
            "Morohashi (Urs App), Spahn/Hadamitzky descriptors (Mark Spahn "
            "and Wolfgang Hadamitzky), Korean readings (Charles Muller), "
            "De Roo codes (Joseph De Roo)."
        ),
        "field_notes": {
            "grade": "Kanji grade. 1-6 = kyōiku (elementary year), 8 = secondary jōyō, 9-10 = jinmeiyō (name-use), null = non-list.",
            "jlpt_old": "Pre-2010 JLPT level, 1-4 (1 = advanced, 4 = beginner). Not the current N1-N5 system. Filled by Phase 2 jlpt_waller field for current classifications.",
            "jlpt_waller": "Current N1-N5 level from Jonathan Waller's JLPT lists (tanos.co.uk). Filled in Phase 2. Null in Phase 1 output.",
            "frequency": "Newspaper frequency rank, 1 = most common. Only populated for the top ~2,500 most common kanji.",
            "stroke_count": "Canonical stroke count. Additional accepted variants in stroke_count_variants.",
            "radical.classical": "Kangxi (classical) radical number, 1-214.",
            "radical.nelson": "Nelson classic radical number, where it differs from Kangxi.",
            "radical_components": "Component radicals from KRADFILE. Filled by Phase 2 cross_links. Empty array in Phase 1.",
            "meanings": "Multilingual meanings: en=English, fr=French, es=Spanish, pt=Portuguese. Not every kanji has entries in every language.",
            "readings.on": "On-yomi (Sino-Japanese), written in katakana.",
            "readings.kun": "Kun-yomi (native Japanese), in hiragana. Dots mark okurigana boundaries; hyphens mark prefix/suffix.",
            "readings_cjk": "Cross-linguistic readings (Mandarin pinyin, Korean romanized/hangul, Vietnamese) for reference. Not needed for Japanese learning but included for completeness.",
            "nanori": "Name-only readings used in personal and place names, not general vocabulary.",
            "dic_refs": "Selected dictionary reference indices. Includes Heisig (RTK), Nelson classic/new, Halpern (NJECD and KKLD 2nd ed), Morohashi, Kodansha Compact, Gakken, O'Neill, and Henshall.",
            "dic_refs.moro": "Morohashi Dai Kan-Wa Jiten entry number. Volume and page detail dropped in Phase 1 (see docs/upstream-issues.md).",
            "query_codes.skip": "SKIP code (Jack Halpern). Primary value only; skipMisclassification flag dropped in Phase 1 (see docs/upstream-issues.md).",
            "query_codes.four_corner": "Four Corner code (Urs App).",
            "query_codes.sh_desc": "Spahn/Hadamitzky descriptor.",
            "query_codes.deroo": "De Roo code.",
        },
    }


def build() -> None:
    """Build kanji.json and kanji-joyo.json from KANJIDIC2."""
    print(f"[kanji]    loading {SOURCE_TGZ.name}")
    source = _load_source()
    characters = source.get("characters", [])

    jlpt_map = _load_kanji_jlpt_map()
    radical_map = _load_radical_components_map()
    if jlpt_map:
        print(f"[kanji]    found JLPT enrichment: {len(jlpt_map):,} kanji classified")
    else:
        print("[kanji]    no JLPT enrichment file; jlpt_waller will be null")
    if radical_map:
        print(f"[kanji]    found radical enrichment: {len(radical_map):,} kanji → components")
    else:
        print("[kanji]    no radical enrichment file; radical_components will be empty")

    print(f"[kanji]    transforming {len(characters):,} characters")
    kanji_entries = [_transform_character(c, jlpt_map, radical_map) for c in characters]

    # Coverage stats
    enriched_jlpt = sum(1 for k in kanji_entries if k.get("jlpt_waller"))
    enriched_radicals = sum(1 for k in kanji_entries if k.get("radical_components"))
    print(f"[kanji]    enriched: jlpt_waller={enriched_jlpt:,} radical_components={enriched_radicals:,}")

    OUT_FULL.parent.mkdir(parents=True, exist_ok=True)
    output_full = {
        "metadata": _metadata(source, len(kanji_entries), filter_note="All KANJIDIC2 characters (no filter)."),
        "kanji": kanji_entries,
    }
    with OUT_FULL.open("w", encoding="utf-8") as f:
        json.dump(output_full, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"[kanji]    wrote {OUT_FULL.relative_to(REPO_ROOT)} ({len(kanji_entries):,} entries)")

    # Derived Jōyō view
    joyo_entries = [k for k in kanji_entries if k.get("grade") in JOYO_GRADES]
    output_joyo = {
        "metadata": _metadata(
            source,
            len(joyo_entries),
            filter_note="Jōyō kanji only: kyōiku (grades 1-6) and secondary (grade 8), per the 2010 MEXT revision.",
        ),
        "kanji": joyo_entries,
    }
    with OUT_JOYO.open("w", encoding="utf-8") as f:
        json.dump(output_joyo, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"[kanji]    wrote {OUT_JOYO.relative_to(REPO_ROOT)} ({len(joyo_entries):,} entries)")

    # Derived Jinmeiyō view (kanji approved for personal-name use)
    jinmeiyo_entries = [k for k in kanji_entries if k.get("grade") in JINMEIYO_GRADES]
    output_jinmeiyo = {
        "metadata": _metadata(
            source,
            len(jinmeiyo_entries),
            filter_note="Jinmeiyō kanji only: grades 9 and 10 in KANJIDIC2 (kanji approved for personal-name use in Japan but not included in the Jōyō list). Derived from the same source as kanji.json.",
        ),
        "kanji": jinmeiyo_entries,
    }
    with OUT_JINMEIYO.open("w", encoding="utf-8") as f:
        json.dump(output_jinmeiyo, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"[kanji]    wrote {OUT_JINMEIYO.relative_to(REPO_ROOT)} ({len(jinmeiyo_entries):,} entries)")
