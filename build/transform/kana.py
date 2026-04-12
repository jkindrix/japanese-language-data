"""Kana data transform (hand-curated).

Unlike the other transforms, this one is not derived from an upstream
source. There are only ~215 kana characters and variants, and a hand-
curated dataset is more accurate and pedagogically useful than any
scraped source would be.

Output: ``data/core/kana.json`` conforming to ``schemas/kana.schema.json``.

The data is generated programmatically from base tables in this module:

    * 46 basic hiragana / 46 basic katakana (matched pairs)
    * 20 dakuten (voiced) hiragana / 20 dakuten katakana
    * 5 handakuten (semi-voiced) hiragana / 5 handakuten katakana
    * 21 yōon (palatalized) hiragana / 21 yōon katakana
    * 9 dakuten-yōon hiragana / 9 dakuten-yōon katakana
    * 3 handakuten-yōon hiragana / 3 handakuten-yōon katakana
    * 1 sokuon (っ / ッ) in each script
    * 4 archaic kana (ゐ, ゑ, ヰ, ヱ)
    * 1 long vowel mark (ー)

Total: ~215 entries.

Stroke counts are the author's best knowledge based on standard kana
instruction tables. Any errors should be reported so they can be
corrected upstream (docs/upstream-issues.md) and in the next patch.

Romaji uses Hepburn as the primary system (with long vowels as double
vowels, not macrons, for ASCII safety). Where Kunrei-shiki or Nihon-shiki
differs, the alternative is listed in ``romaji_alt``.
"""

from __future__ import annotations

import json
from pathlib import Path
from build.pipeline import BUILD_DATE

REPO_ROOT = Path(__file__).resolve().parents[2]
OUT = REPO_ROOT / "data" / "core" / "kana.json"


# =============================================================================
# Base tables: 46 hiragana and 46 katakana in a row-by-row grid.
# Each entry: (hiragana, katakana, hepburn, kunrei_alt, hira_strokes, kata_strokes)
# kunrei_alt is None if Hepburn and Kunrei agree; otherwise the Kunrei form.
# =============================================================================
BASIC_KANA = [
    # Vowels
    ("あ", "ア", "a",   None, 3, 2),
    ("い", "イ", "i",   None, 2, 2),
    ("う", "ウ", "u",   None, 2, 3),
    ("え", "エ", "e",   None, 2, 3),
    ("お", "オ", "o",   None, 3, 3),
    # K-row
    ("か", "カ", "ka",  None, 3, 2),
    ("き", "キ", "ki",  None, 4, 3),
    ("く", "ク", "ku",  None, 1, 2),
    ("け", "ケ", "ke",  None, 3, 3),
    ("こ", "コ", "ko",  None, 2, 2),
    # S-row
    ("さ", "サ", "sa",  None, 3, 3),
    ("し", "シ", "shi", "si", 1, 3),
    ("す", "ス", "su",  None, 2, 2),
    ("せ", "セ", "se",  None, 3, 2),
    ("そ", "ソ", "so",  None, 1, 2),
    # T-row
    ("た", "タ", "ta",  None, 4, 3),
    ("ち", "チ", "chi", "ti", 2, 3),
    ("つ", "ツ", "tsu", "tu", 1, 3),
    ("て", "テ", "te",  None, 1, 3),
    ("と", "ト", "to",  None, 2, 2),
    # N-row
    ("な", "ナ", "na",  None, 4, 2),
    ("に", "ニ", "ni",  None, 3, 2),
    ("ぬ", "ヌ", "nu",  None, 2, 2),
    ("ね", "ネ", "ne",  None, 2, 4),
    ("の", "ノ", "no",  None, 1, 1),
    # H-row
    ("は", "ハ", "ha",  None, 3, 2),
    ("ひ", "ヒ", "hi",  None, 1, 2),
    ("ふ", "フ", "fu",  "hu", 4, 1),
    ("へ", "ヘ", "he",  None, 1, 1),
    ("ほ", "ホ", "ho",  None, 4, 4),
    # M-row
    ("ま", "マ", "ma",  None, 3, 2),
    ("み", "ミ", "mi",  None, 2, 3),
    ("む", "ム", "mu",  None, 3, 2),
    ("め", "メ", "me",  None, 2, 2),
    ("も", "モ", "mo",  None, 3, 3),
    # Y-row (y-sounds)
    ("や", "ヤ", "ya",  None, 3, 2),
    ("ゆ", "ユ", "yu",  None, 2, 2),
    ("よ", "ヨ", "yo",  None, 2, 3),
    # R-row
    ("ら", "ラ", "ra",  None, 2, 2),
    ("り", "リ", "ri",  None, 2, 2),
    ("る", "ル", "ru",  None, 2, 2),
    ("れ", "レ", "re",  None, 2, 1),
    ("ろ", "ロ", "ro",  None, 1, 3),
    # W-row
    ("わ", "ワ", "wa",  None, 2, 2),
    ("を", "ヲ", "wo",  "o", 3, 3),  # Hepburn often writes as "o"; kunrei "wo"
    # N
    ("ん", "ン", "n",   None, 1, 2),
]

# Base → dakuten mapping. The dakuten variant of か is が, etc.
DAKUTEN_MAP = [
    # K → G
    ("か", "カ", "が", "ガ", "ga"),
    ("き", "キ", "ぎ", "ギ", "gi"),
    ("く", "ク", "ぐ", "グ", "gu"),
    ("け", "ケ", "げ", "ゲ", "ge"),
    ("こ", "コ", "ご", "ゴ", "go"),
    # S → Z (shi → ji)
    ("さ", "サ", "ざ", "ザ", "za"),
    ("し", "シ", "じ", "ジ", "ji"),      # kunrei: zi
    ("す", "ス", "ず", "ズ", "zu"),
    ("せ", "セ", "ぜ", "ゼ", "ze"),
    ("そ", "ソ", "ぞ", "ゾ", "zo"),
    # T → D (chi → dji/ji, tsu → dzu/zu)
    ("た", "タ", "だ", "ダ", "da"),
    ("ち", "チ", "ぢ", "ヂ", "ji"),      # kunrei: di; rarely used
    ("つ", "ツ", "づ", "ヅ", "zu"),      # kunrei: du; rarely used
    ("て", "テ", "で", "デ", "de"),
    ("と", "ト", "ど", "ド", "do"),
    # H → B
    ("は", "ハ", "ば", "バ", "ba"),
    ("ひ", "ヒ", "び", "ビ", "bi"),
    ("ふ", "フ", "ぶ", "ブ", "bu"),
    ("へ", "ヘ", "べ", "ベ", "be"),
    ("ほ", "ホ", "ぼ", "ボ", "bo"),
]

# Base → handakuten mapping. Only the h-row has handakuten.
HANDAKUTEN_MAP = [
    ("は", "ハ", "ぱ", "パ", "pa"),
    ("ひ", "ヒ", "ぴ", "ピ", "pi"),
    ("ふ", "フ", "ぷ", "プ", "pu"),
    ("へ", "ヘ", "ぺ", "ペ", "pe"),
    ("ほ", "ホ", "ぽ", "ポ", "po"),
]

# Yōon: base consonant + small ya/yu/yo. e.g., きゃ = ki + small ya.
# Entries: (base hira, base kata, yōon hira, yōon kata, hepburn romaji)
YOON_BASE = [
    # K-row
    ("き", "キ", "きゃ", "キャ", "kya"),
    ("き", "キ", "きゅ", "キュ", "kyu"),
    ("き", "キ", "きょ", "キョ", "kyo"),
    # S-row (shi → sha/shu/sho)
    ("し", "シ", "しゃ", "シャ", "sha"),
    ("し", "シ", "しゅ", "シュ", "shu"),
    ("し", "シ", "しょ", "ショ", "sho"),
    # T-row (chi → cha/chu/cho)
    ("ち", "チ", "ちゃ", "チャ", "cha"),
    ("ち", "チ", "ちゅ", "チュ", "chu"),
    ("ち", "チ", "ちょ", "チョ", "cho"),
    # N-row
    ("に", "ニ", "にゃ", "ニャ", "nya"),
    ("に", "ニ", "にゅ", "ニュ", "nyu"),
    ("に", "ニ", "にょ", "ニョ", "nyo"),
    # H-row
    ("ひ", "ヒ", "ひゃ", "ヒャ", "hya"),
    ("ひ", "ヒ", "ひゅ", "ヒュ", "hyu"),
    ("ひ", "ヒ", "ひょ", "ヒョ", "hyo"),
    # M-row
    ("み", "ミ", "みゃ", "ミャ", "mya"),
    ("み", "ミ", "みゅ", "ミュ", "myu"),
    ("み", "ミ", "みょ", "ミョ", "myo"),
    # R-row
    ("り", "リ", "りゃ", "リャ", "rya"),
    ("り", "リ", "りゅ", "リュ", "ryu"),
    ("り", "リ", "りょ", "リョ", "ryo"),
]

# Dakuten yōon: base consonant with dakuten + small ya/yu/yo
YOON_DAKUTEN = [
    # G-row
    ("ぎ", "ギ", "ぎゃ", "ギャ", "gya"),
    ("ぎ", "ギ", "ぎゅ", "ギュ", "gyu"),
    ("ぎ", "ギ", "ぎょ", "ギョ", "gyo"),
    # J-row (from ji)
    ("じ", "ジ", "じゃ", "ジャ", "ja"),   # kunrei: zya
    ("じ", "ジ", "じゅ", "ジュ", "ju"),   # kunrei: zyu
    ("じ", "ジ", "じょ", "ジョ", "jo"),   # kunrei: zyo
    # B-row
    ("び", "ビ", "びゃ", "ビャ", "bya"),
    ("び", "ビ", "びゅ", "ビュ", "byu"),
    ("び", "ビ", "びょ", "ビョ", "byo"),
]

# Handakuten yōon (p-row)
YOON_HANDAKUTEN = [
    ("ぴ", "ピ", "ぴゃ", "ピャ", "pya"),
    ("ぴ", "ピ", "ぴゅ", "ピュ", "pyu"),
    ("ぴ", "ピ", "ぴょ", "ピョ", "pyo"),
]

# Kunrei alternatives for yōon (where Hepburn uses sh/ch/j/f)
KUNREI_YOON = {
    "sha": "sya", "shu": "syu", "sho": "syo",
    "cha": "tya", "chu": "tyu", "cho": "tyo",
    "ja": "zya", "ju": "zyu", "jo": "zyo",
}

# Archaic kana (no longer in modern use; preserved for historical texts).
ARCHAIC = [
    # (character, script, romaji, stroke_count, unicode, notes)
    ("ゐ", "hiragana", "wi", 2, "3090", "Archaic. Obsolete in modern Japanese (post-1946 orthography reform); replaced by い in most contexts. Still appears in historical texts and some proper names."),
    ("ゑ", "hiragana", "we", 3, "3091", "Archaic. Obsolete in modern Japanese (post-1946 orthography reform); replaced by え in most contexts. Still appears in historical texts."),
    ("ヰ", "katakana", "wi", 4, "30F0", "Archaic. Obsolete counterpart to ゐ."),
    ("ヱ", "katakana", "we", 3, "30F1", "Archaic. Obsolete counterpart to ゑ. Occasionally seen in brand names (e.g., ヱビス beer)."),
]


def _codepoint_hex(ch: str) -> str:
    """Return the Unicode codepoint of a single character as lowercase hex."""
    if len(ch) == 1:
        return f"{ord(ch):04x}"
    # Multi-codepoint (e.g., yōon composed of two code units) — return sequence.
    return "+".join(f"{ord(c):04x}" for c in ch)


def _build_basic() -> list[dict]:
    """Build entries for the 46+46 basic kana."""
    entries: list[dict] = []
    for hira, kata, hepburn, kunrei, hira_strokes, kata_strokes in BASIC_KANA:
        alt = [kunrei] if kunrei and kunrei != hepburn else []
        entries.append({
            "character": hira,
            "script": "hiragana",
            "romaji": hepburn,
            "romaji_alt": alt,
            "type": "base",
            "stroke_count": hira_strokes,
            "unicode": _codepoint_hex(hira),
        })
        entries.append({
            "character": kata,
            "script": "katakana",
            "romaji": hepburn,
            "romaji_alt": alt,
            "type": "base",
            "stroke_count": kata_strokes,
            "unicode": _codepoint_hex(kata),
        })
    return entries


def _build_dakuten() -> list[dict]:
    """Build entries for the 20+20 dakuten kana."""
    entries: list[dict] = []
    # Build a lookup for base stroke counts
    base_strokes: dict[str, int] = {}
    for hira, kata, _, _, hs, ks in BASIC_KANA:
        base_strokes[hira] = hs
        base_strokes[kata] = ks

    kunrei_dakuten = {"ji": "zi", "zu": "zu"}  # ji ← shi is zi; zu ← su stays zu

    for base_hira, base_kata, dhira, dkata, romaji in DAKUTEN_MAP:
        # Dakuten adds 2 strokes (two small dots)
        hs = (base_strokes.get(base_hira, 0) or 0) + 2
        ks = (base_strokes.get(base_kata, 0) or 0) + 2
        alt_kunrei = kunrei_dakuten.get(romaji)
        alt = [alt_kunrei] if alt_kunrei and alt_kunrei != romaji else []
        entries.append({
            "character": dhira,
            "script": "hiragana",
            "romaji": romaji,
            "romaji_alt": alt,
            "type": "dakuten",
            "base": base_hira,
            "stroke_count": hs,
            "unicode": _codepoint_hex(dhira),
        })
        entries.append({
            "character": dkata,
            "script": "katakana",
            "romaji": romaji,
            "romaji_alt": alt,
            "type": "dakuten",
            "base": base_kata,
            "stroke_count": ks,
            "unicode": _codepoint_hex(dkata),
        })
    return entries


def _build_handakuten() -> list[dict]:
    """Build entries for the 5+5 handakuten kana."""
    entries: list[dict] = []
    base_strokes: dict[str, int] = {}
    for hira, kata, _, _, hs, ks in BASIC_KANA:
        base_strokes[hira] = hs
        base_strokes[kata] = ks

    for base_hira, base_kata, phira, pkata, romaji in HANDAKUTEN_MAP:
        # Handakuten adds 1 stroke (the small circle)
        hs = (base_strokes.get(base_hira, 0) or 0) + 1
        ks = (base_strokes.get(base_kata, 0) or 0) + 1
        entries.append({
            "character": phira,
            "script": "hiragana",
            "romaji": romaji,
            "romaji_alt": [],
            "type": "handakuten",
            "base": base_hira,
            "stroke_count": hs,
            "unicode": _codepoint_hex(phira),
        })
        entries.append({
            "character": pkata,
            "script": "katakana",
            "romaji": romaji,
            "romaji_alt": [],
            "type": "handakuten",
            "base": base_kata,
            "stroke_count": ks,
            "unicode": _codepoint_hex(pkata),
        })
    return entries


def _build_yoon(table: list[tuple], type_name: str) -> list[dict]:
    """Build yōon entries. stroke_count is null (compound form)."""
    entries: list[dict] = []
    for base_hira, base_kata, yhira, ykata, romaji in table:
        alt_kunrei = KUNREI_YOON.get(romaji)
        alt = [alt_kunrei] if alt_kunrei and alt_kunrei != romaji else []
        entries.append({
            "character": yhira,
            "script": "hiragana",
            "romaji": romaji,
            "romaji_alt": alt,
            "type": type_name,
            "base": base_hira,
            "stroke_count": None,
            "unicode": _codepoint_hex(yhira),
            "usage_notes": "Yōon (palatalized) compound. Written as the base kana plus small ya/yu/yo.",
        })
        entries.append({
            "character": ykata,
            "script": "katakana",
            "romaji": romaji,
            "romaji_alt": alt,
            "type": type_name,
            "base": base_kata,
            "stroke_count": None,
            "unicode": _codepoint_hex(ykata),
            "usage_notes": "Yōon (palatalized) compound. Written as the base kana plus small ya/yu/yo.",
        })
    return entries


def _build_sokuon() -> list[dict]:
    return [
        {
            "character": "っ",
            "script": "hiragana",
            "romaji": "",
            "romaji_alt": [],
            "type": "sokuon",
            "stroke_count": 1,
            "unicode": _codepoint_hex("っ"),
            "usage_notes": "Small tsu. Indicates a doubled consonant (gemination), written as っ before the consonant it doubles. Transcribed as a doubled consonant in romaji (e.g., きっぷ kippu).",
        },
        {
            "character": "ッ",
            "script": "katakana",
            "romaji": "",
            "romaji_alt": [],
            "type": "sokuon",
            "stroke_count": 1,
            "unicode": _codepoint_hex("ッ"),
            "usage_notes": "Katakana small tsu. Same function as っ; gemination in loanwords and emphatic writing.",
        },
    ]


def _build_archaic() -> list[dict]:
    entries: list[dict] = []
    for ch, script, romaji, strokes, unicode_hex, notes in ARCHAIC:
        entries.append({
            "character": ch,
            "script": script,
            "romaji": romaji,
            "romaji_alt": [],
            "type": "other",
            "stroke_count": strokes,
            "unicode": unicode_hex.lower(),
            "usage_notes": notes,
        })
    return entries


def _build_long_vowel() -> list[dict]:
    return [
        {
            "character": "ー",
            "script": "katakana",
            "romaji": "",
            "romaji_alt": [],
            "type": "other",
            "stroke_count": 1,
            "unicode": "30fc",
            "usage_notes": "Chōonpu (long vowel mark). Lengthens the preceding vowel in katakana (e.g., コーヒー kōhī). Typically only used in katakana; long vowels in hiragana are written by doubling or with an extra vowel kana.",
        },
    ]


def build() -> None:
    print("[kana]     building hand-curated kana dataset")
    entries: list[dict] = []
    entries.extend(_build_basic())
    entries.extend(_build_dakuten())
    entries.extend(_build_handakuten())
    entries.extend(_build_yoon(YOON_BASE, "yoon"))
    entries.extend(_build_yoon(YOON_DAKUTEN, "yoon_dakuten"))
    entries.extend(_build_yoon(YOON_HANDAKUTEN, "yoon_handakuten"))
    entries.extend(_build_sokuon())
    entries.extend(_build_archaic())
    entries.extend(_build_long_vowel())

    hira_count = sum(1 for e in entries if e["script"] == "hiragana")
    kata_count = sum(1 for e in entries if e["script"] == "katakana")
    print(f"[kana]     total: {len(entries)}  hiragana: {hira_count}  katakana: {kata_count}")

    output = {
        "metadata": {
            "source": "Hand-curated (project original)",
            "license": "CC-BY-SA 4.0",
            "generated": BUILD_DATE,
            "count": len(entries),
            "field_notes": {
                "character": "The kana character itself. Yōon entries (e.g., きゃ) are two-codepoint strings.",
                "script": "Which script the entry belongs to: hiragana or katakana.",
                "romaji": "Hepburn romanization. Doubled consonants for sokuon; double-vowel for long vowels (kōhī = ko-u-hi-i).",
                "romaji_alt": "Alternative romanizations where Hepburn and Kunrei-shiki differ (e.g., shi vs si, fu vs hu, ja vs zya).",
                "type": "Entry classification: base, dakuten, handakuten, yoon, yoon_dakuten, yoon_handakuten, sokuon, or other (archaic, long vowel mark).",
                "base": "For derived forms (dakuten/handakuten/yōon), the base kana this is derived from.",
                "stroke_count": "Standard stroke count. Null for yōon compound forms (because they are composed of two base kana, each with its own stroke count).",
                "unicode": "Lowercase hex Unicode codepoint. For multi-codepoint forms (yōon), the codepoints are joined with '+'.",
                "usage_notes": "Human-readable notes on when and how the entry is used. Present only where there is something non-obvious to say.",
            },
            "authorship_caveat": "Stroke counts and romanizations are the author's best knowledge. Corrections welcome via docs/contributing.md and docs/upstream-issues.md.",
        },
        "kana": entries,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"[kana]     wrote {OUT.relative_to(REPO_ROOT)}")
