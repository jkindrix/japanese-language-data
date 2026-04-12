"""Unit tests for transformer functions (not integration tests against
built data files).

Rationale: the rest of the test suite exercises the transformer code
indirectly through built-data invariants. A subtle transformer bug has
to actually corrupt data to be caught that way. This file provides
function-level unit tests that run against the transformer logic in
isolation with canonical inputs, catching regressions earlier than the
data-integrity layer.

Scope: algorithmic / parsing helpers that have edge cases beyond
"reads a file and walks it." Currently covered:

    * kana._codepoint_hex, _build_basic, _build_dakuten, _build_sokuon,
      _build_archaic, _build_long_vowel
    * kanji._transform_character, _metadata
    * words._transform_example, _transform_word, _is_common,
      _load_vocab_jlpt_map
    * radicals._parse_kangxi_wikitext, _extract_radical_forms,
      _strip_wiki_markup
    * pitch._count_morae, _parse_positions
    * stroke_order._count_strokes, _codepoint_filename
    * conjugations._conjugate_godan, _conjugate_ichidan,
      _conjugate_suru_compound, _conjugate_kuru, _conjugate_i_adjective,
      _conjugate_na_adjective, _longest_common_suffix_length,
      _replace_prefix_in_forms, _display_forms_adj_na,
      _display_forms_common_suffix
    * grammar._validate_entry, _normalize_japanese_for_match
    * cross_links._is_kanji_char, _build_word_cross_refs
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
# Ensure the build package is importable even when tests are run from a
# directory that doesn't already have it on sys.path.
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


# ---------------------------------------------------------------------------
# _conjugate_godan edge cases (B1 / D1 regression territory)
# ---------------------------------------------------------------------------

def test_conjugate_godan_v5k_s_iku_te_ta_forms() -> None:
    """v5k-s must use って/った for te/ta forms (not いて/いた).
    Covers the 行く irregularity that D1 previously missed entirely and
    B1's regression re-verified."""
    from build.transform.conjugations import _conjugate_godan
    forms = _conjugate_godan("いく", "v5k-s")
    assert forms is not None
    assert forms["te_form"] == "いって", f"expected いって, got {forms['te_form']!r}"
    assert forms["ta_form"] == "いった", f"expected いった, got {forms['ta_form']!r}"
    assert forms["polite_nonpast"] == "いきます"
    assert forms["nai_form"] == "いかない"


def test_conjugate_godan_v5u_s_tou_te_ta_forms() -> None:
    """v5u-s must use うて/うた for te/ta forms (not って/った).
    Covers 問う / 請う which D1 previously missed entirely."""
    from build.transform.conjugations import _conjugate_godan
    forms = _conjugate_godan("とう", "v5u-s")
    assert forms is not None
    assert forms["te_form"] == "とうて", f"expected とうて, got {forms['te_form']!r}"
    assert forms["ta_form"] == "とうた", f"expected とうた, got {forms['ta_form']!r}"
    assert forms["polite_nonpast"] == "といます"


def test_conjugate_godan_v5aru_i_stem_and_imperative() -> None:
    """v5aru honorific verbs use い (not り) for polite forms and
    imperative. Covers いらっしゃる, ござる, なさる, おっしゃる."""
    from build.transform.conjugations import _conjugate_godan
    forms = _conjugate_godan("いらっしゃる", "v5aru")
    assert forms is not None
    assert forms["polite_nonpast"] == "いらっしゃいます"
    assert forms["polite_past"] == "いらっしゃいました"
    assert forms["polite_negative"] == "いらっしゃいません"
    assert forms["imperative"] == "いらっしゃい"
    # Regular godan-r forms survive for other slots
    assert forms["te_form"] == "いらっしゃって"
    assert forms["nai_form"] == "いらっしゃらない"


def test_conjugate_godan_v5r_i_bare_aru_suppletive_negative() -> None:
    """v5r-i bare ある: nai_form and nakatta_form are suppletive ない /
    なかった (not あらない / あらなかった). B1 regression probe."""
    from build.transform.conjugations import _conjugate_godan
    forms = _conjugate_godan("ある", "v5r-i")
    assert forms is not None
    assert forms["nai_form"] == "ない", f"bare ある should produce nai_form=ない, got {forms['nai_form']!r}"
    assert forms["nakatta_form"] == "なかった"
    # Bare ある keeps its regular forms for polite/te/ta (still in active use)
    assert forms["te_form"] == "あって"
    assert forms["polite_nonpast"] == "あります"
    # Bare ある KEEPS its imperative/potential/volitional since prefix is empty.
    # The blanking is only for COMPOUND v5r-i (ことがある, である, でもある).
    assert forms["imperative"] == "あれ"
    assert forms["volitional"] == "あろう"


def test_conjugate_godan_v5r_i_compound_koto_ga_aru_prefix() -> None:
    """v5r-i compound ことがある: nai_form must be ことがない (not ない,
    which was the B1 bug). And the compound's imperative/potential/
    passive/causative/volitional/conditional_ba must be blank because
    they are not well-formed for ある compounds (previously produced
    nonsensical ことがあれ etc.)."""
    from build.transform.conjugations import _conjugate_godan
    forms = _conjugate_godan("ことがある", "v5r-i")
    assert forms is not None
    assert forms["nai_form"] == "ことがない", \
        f"expected ことがない, got {forms['nai_form']!r}"
    assert forms["nakatta_form"] == "ことがなかった"
    # The compound blanks out the not-well-formed slots
    for slot in ("imperative", "potential", "passive",
                 "causative", "volitional", "conditional_ba"):
        assert forms[slot] == "", \
            f"compound v5r-i {slot} should be empty, got {forms[slot]!r}"
    # But te_form and polite forms remain well-formed
    assert forms["te_form"] == "ことがあって"
    assert forms["polite_nonpast"] == "ことがあります"


# ---------------------------------------------------------------------------
# radicals._parse_kangxi_wikitext — Wikipedia wikitable parser
# ---------------------------------------------------------------------------

# A fragment that mimics the Wikipedia "Kangxi radicals" wikitable shape:
# radical 1 with no alternates, radical 9 with two alternates, radical 85
# with one alternate. The parser has to handle cells with {{lang}} templates,
# multi-character alternate lists separated by 、, comma-separated meanings,
# and row separators.
_KANGXI_WIKITABLE_FRAGMENT = """\
Some intro paragraph.

{| class="wikitable sortable"
! N !! Radical !! Strokes !! Meaning
|----
| [[Radical 1|1]]
| '''<big>{{lang|zh-Hant|一}}</big>'''
| 1
| [[one]]
|----
| [[Radical 9|9]]
| '''<big>{{lang|zh-Hant|人}}<br/>({{lang|zh|亻}}、{{lang|zh|𠆢}})</big>'''
| 2
| [[man]], person
|----
| [[Radical 85|85]]
| '''<big>{{lang|zh-Hant|水}}<br/>({{lang|zh|氵}})</big>'''
| 4
| [[water]]
|}

Epilogue text after the table.
"""


def test_parse_kangxi_wikitext_extracts_primary_and_alternates() -> None:
    """The wikitable parser should extract primary radicals and all alternate
    forms keyed under the same Kangxi number and meanings."""
    from build.transform.radicals import _parse_kangxi_wikitext
    mapping = _parse_kangxi_wikitext(_KANGXI_WIKITABLE_FRAGMENT)

    # Primary characters are present
    assert "一" in mapping, "radical 1 primary (一) missing"
    assert "人" in mapping, "radical 9 primary (人) missing"
    assert "水" in mapping, "radical 85 primary (水) missing"

    # Alternates share the primary's entry
    assert "亻" in mapping, "radical 9 alternate (亻) missing"
    assert "𠆢" in mapping, "radical 9 alternate (𠆢) missing"
    assert "氵" in mapping, "radical 85 alternate (氵) missing"

    # Numbers are correct
    assert mapping["一"]["number"] == 1
    assert mapping["人"]["number"] == 9
    assert mapping["亻"]["number"] == 9
    assert mapping["𠆢"]["number"] == 9
    assert mapping["水"]["number"] == 85
    assert mapping["氵"]["number"] == 85

    # Primary is tracked
    assert mapping["亻"]["primary"] == "人"
    assert mapping["氵"]["primary"] == "水"

    # Meanings split on comma
    assert mapping["一"]["meanings"] == ["one"]
    assert "man" in mapping["人"]["meanings"]
    assert "person" in mapping["人"]["meanings"]
    assert mapping["水"]["meanings"] == ["water"]


def test_parse_kangxi_wikitext_empty_input_returns_empty_dict() -> None:
    """A wikitext with no wikitable should raise, per the parser contract."""
    from build.transform.radicals import _parse_kangxi_wikitext
    with pytest.raises(RuntimeError, match="Kangxi radicals wikitable"):
        _parse_kangxi_wikitext("just some text, no wikitable")


# ---------------------------------------------------------------------------
# pitch._count_morae — small-kana / sokuon / long-vowel edge cases
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "reading,expected",
    [
        ("さくら", 3),        # simple: sa-ku-ra
        ("きょう", 2),        # yōon: kyō fuses き+ょ into 1 mora, + う
        ("しゃ", 1),          # yōon alone
        ("がっこう", 4),      # sokuon counts: ga-t-ko-u
        ("コーヒー", 4),      # long-vowel mark ー counts: ko-o-hi-i
        ("にっぽん", 4),      # ni-t-po-n
        ("ちょうちょ", 3),    # chō-u-cho: ちょ(1) + う(1) + ちょ(1) = 3
        ("", 0),              # empty
        ("あ", 1),            # single
    ],
)
def test_count_morae(reading: str, expected: int) -> None:
    """Mora counting must skip small kana (yōon) but count sokuon っ and
    the long-vowel mark ー as independent morae."""
    from build.transform.pitch import _count_morae
    assert _count_morae(reading) == expected, f"{reading!r} expected {expected} morae"


# ---------------------------------------------------------------------------
# stroke_order._count_strokes — SVG path counting
# ---------------------------------------------------------------------------

def test_count_strokes_matches_kvg_path_ids() -> None:
    """The stroke counter should match the number of <path> elements that
    carry an id attribute, which is KanjiVG's one-path-per-stroke convention."""
    from build.transform.stroke_order import _count_strokes
    svg = """<svg xmlns="http://www.w3.org/2000/svg" xmlns:kvg="http://kanjivg.tagaini.net">
  <g id="kvg:065e5">
    <path id="kvg:065e5-s1" d="M10,10 L50,10"/>
    <path id="kvg:065e5-s2" d="M50,10 L50,50"/>
    <path id="kvg:065e5-s3" d="M50,50 L10,50"/>
    <path id="kvg:065e5-s4" d="M10,10 L10,50"/>
  </g>
</svg>"""
    assert _count_strokes(svg) == 4


def test_count_strokes_ignores_paths_without_id() -> None:
    """Decorative paths (no id attribute) should not be counted."""
    from build.transform.stroke_order import _count_strokes
    svg = """<svg>
  <path d="M0,0 L10,10"/>
  <path id="kvg:xxx-s1" d="M0,0 L10,10"/>
  <path id="kvg:xxx-s2" d="M0,0 L10,10"/>
</svg>"""
    assert _count_strokes(svg) == 2


def test_count_strokes_empty_svg_returns_zero() -> None:
    """Empty or path-less SVG should return 0."""
    from build.transform.stroke_order import _count_strokes
    assert _count_strokes("<svg></svg>") == 0


# ---------------------------------------------------------------------------
# words._load_vocab_jlpt_map — D4 easier-level-wins tie-break
# ---------------------------------------------------------------------------

def _write_fake_jlpt(path: Path, classifications: list[dict]) -> None:
    """Write a minimal JLPT classifications file the transform can read."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps({
            "metadata": {
                "source": "test fixture",
                "license": "test",
                "generated": "2026-04-12",
                "count": len(classifications),
                "field_notes": {},
            },
            "classifications": classifications,
        }),
        encoding="utf-8",
    )


def test_load_vocab_jlpt_map_easier_level_wins_when_n5_first(tmp_path, monkeypatch) -> None:
    """When a jmdict_seq appears at two levels, the easier one (higher
    N-number) wins regardless of encounter order. D4 regression."""
    import build.transform.words as words_mod

    fake = tmp_path / "jlpt.json"
    _write_fake_jlpt(fake, [
        {"kind": "vocab", "jmdict_seq": "1198180", "level": "N5", "text": "会う"},
        {"kind": "vocab", "jmdict_seq": "1198180", "level": "N2", "text": "遭う"},
    ])
    monkeypatch.setattr(words_mod, "JLPT_ENRICHMENT", fake)
    result = words_mod._load_vocab_jlpt_map()
    assert result["1198180"] == "N5", \
        f"N5 should win over N2 (easier wins), got {result['1198180']!r}"


def test_load_vocab_jlpt_map_easier_level_wins_when_n2_first(tmp_path, monkeypatch) -> None:
    """Same as above but with N2 encountered first — the tie-break must
    replace the existing entry when a strictly easier level arrives."""
    import build.transform.words as words_mod

    fake = tmp_path / "jlpt.json"
    _write_fake_jlpt(fake, [
        {"kind": "vocab", "jmdict_seq": "1198180", "level": "N2", "text": "遭う"},
        {"kind": "vocab", "jmdict_seq": "1198180", "level": "N5", "text": "会う"},
    ])
    monkeypatch.setattr(words_mod, "JLPT_ENRICHMENT", fake)
    result = words_mod._load_vocab_jlpt_map()
    assert result["1198180"] == "N5", \
        f"N5 should replace earlier N2 (easier wins), got {result['1198180']!r}"


def test_load_vocab_jlpt_map_ignores_non_vocab_kinds(tmp_path, monkeypatch) -> None:
    """kanji and grammar entries must not pollute the vocab map."""
    import build.transform.words as words_mod

    fake = tmp_path / "jlpt.json"
    _write_fake_jlpt(fake, [
        {"kind": "kanji", "text": "一", "level": "N5"},
        {"kind": "grammar", "grammar_id": "desu-polite-copula", "level": "N5"},
        {"kind": "vocab", "jmdict_seq": "123456", "level": "N3", "text": "テスト"},
    ])
    monkeypatch.setattr(words_mod, "JLPT_ENRICHMENT", fake)
    result = words_mod._load_vocab_jlpt_map()
    assert result == {"123456": "N3"}, \
        f"only vocab entries should appear, got {result!r}"


def test_load_vocab_jlpt_map_handles_missing_file(tmp_path, monkeypatch) -> None:
    """No enrichment file → empty dict (backward-compatible with Phase 1 build)."""
    import build.transform.words as words_mod
    monkeypatch.setattr(words_mod, "JLPT_ENRICHMENT", tmp_path / "does-not-exist.json")
    assert words_mod._load_vocab_jlpt_map() == {}


# ===========================================================================
# kana transform functions
# ===========================================================================

def test_codepoint_hex_basic_hiragana() -> None:
    from build.transform.kana import _codepoint_hex
    assert _codepoint_hex("あ") == "3042"
    assert _codepoint_hex("ん") == "3093"


def test_codepoint_hex_katakana() -> None:
    from build.transform.kana import _codepoint_hex
    assert _codepoint_hex("ア") == "30a2"
    assert _codepoint_hex("ン") == "30f3"


def test_codepoint_hex_kanji() -> None:
    from build.transform.kana import _codepoint_hex
    assert _codepoint_hex("日") == "65e5"


def test_build_basic_returns_92_entries() -> None:
    """46 hiragana + 46 katakana = 92 entries."""
    from build.transform.kana import _build_basic
    entries = _build_basic()
    assert len(entries) == 92
    scripts = {e["script"] for e in entries}
    assert scripts == {"hiragana", "katakana"}
    for e in entries:
        assert e["type"] == "base"
        assert isinstance(e["stroke_count"], int)
        assert e["stroke_count"] > 0


def test_build_dakuten_returns_40_entries() -> None:
    """20 voiced hiragana + 20 voiced katakana = 40."""
    from build.transform.kana import _build_dakuten
    entries = _build_dakuten()
    assert len(entries) == 40
    for e in entries:
        assert e["type"] == "dakuten"


def test_build_sokuon_returns_2_entries() -> None:
    from build.transform.kana import _build_sokuon
    entries = _build_sokuon()
    assert len(entries) == 2
    chars = {e["character"] for e in entries}
    assert "っ" in chars
    assert "ッ" in chars


def test_build_archaic_includes_wi_we() -> None:
    from build.transform.kana import _build_archaic
    entries = _build_archaic()
    chars = {e["character"] for e in entries}
    assert "ゐ" in chars
    assert "ゑ" in chars
    assert "ヰ" in chars
    assert "ヱ" in chars
    assert len(entries) == 4


def test_build_long_vowel_single_entry() -> None:
    from build.transform.kana import _build_long_vowel
    entries = _build_long_vowel()
    assert len(entries) == 1
    assert entries[0]["character"] == "ー"


# ===========================================================================
# kanji transform functions
# ===========================================================================

def test_transform_character_basic_fields() -> None:
    """Verify _transform_character extracts readings, meanings, stroke count."""
    from build.transform.kanji import _transform_character
    ch = {
        "literal": "亜",
        "codepoints": [{"type": "ucs", "value": "4e9c"}],
        "radicals": [
            {"type": "classical", "value": "7"},
            {"type": "nelson_c", "value": "1"},
        ],
        "misc": {"strokeCounts": [7], "grade": 8},
        "readingMeaning": {
            "groups": [{
                "readings": [
                    {"type": "ja_on", "value": "ア"},
                ],
                "meanings": [
                    {"lang": "en", "value": "Asia"},
                    {"lang": "en", "value": "rank next"},
                ],
            }],
        },
    }
    result = _transform_character(ch)
    assert result["character"] == "亜"
    assert result["stroke_count"] == 7
    assert result["grade"] == 8
    assert result["radical"]["classical"] == "7"
    assert result["radical"]["nelson"] == "1"
    assert "Asia" in result["meanings"]["en"]
    assert "ア" in result["readings"]["on"]


def test_transform_character_with_jlpt_enrichment() -> None:
    from build.transform.kanji import _transform_character
    ch = {
        "literal": "食",
        "codepoints": [{"type": "ucs", "value": "98df"}],
        "radicals": [{"type": "classical", "value": "184"}],
        "misc": {"strokeCounts": [9]},
        "readingMeaning": {
            "groups": [{
                "readings": [
                    {"type": "ja_on", "value": "ショク"},
                    {"type": "ja_kun", "value": "た.べる"},
                ],
                "meanings": [{"lang": "en", "value": "eat"}],
            }],
        },
    }
    result = _transform_character(ch, jlpt_map={"食": "N4"})
    assert result["jlpt_waller"] == "N4"


def test_transform_character_minimal_entry() -> None:
    """Sparse entries should not crash — missing fields get None."""
    from build.transform.kanji import _transform_character
    ch = {
        "literal": "𠀀",
        "codepoints": [],
        "radicals": [],
        "misc": {},
    }
    result = _transform_character(ch)
    assert result["character"] == "𠀀"
    assert result["stroke_count"] is None
    assert result["grade"] is None


# ===========================================================================
# words transform functions
# ===========================================================================

def test_transform_example_tatoeba() -> None:
    from build.transform.words import _transform_example
    ex = {
        "source": {"type": "tatoeba", "value": 12345},
        "text": "食べる",
        "sentences": [
            {"lang": "jpn", "text": "りんごを食べる。"},
            {"lang": "eng", "text": "I eat an apple."},
        ],
    }
    result = _transform_example(ex)
    assert result["source"] == "tatoeba"
    assert result["sentence_id"] == "12345"
    assert result["japanese"] == "りんごを食べる。"
    assert result["english"] == "I eat an apple."


def test_transform_word_basic() -> None:
    from build.transform.words import _transform_word
    w = {
        "id": "1000220",
        "kanji": [{"text": "明日", "common": True}],
        "kana": [{"text": "あした", "common": True}],
        "sense": [{"gloss": [{"lang": "eng", "text": "tomorrow"}]}],
    }
    result = _transform_word(w)
    assert result["id"] == "1000220"
    assert result["kanji"][0]["text"] == "明日"
    assert result["jlpt_waller"] is None  # no map provided


def test_transform_word_with_jlpt() -> None:
    from build.transform.words import _transform_word
    w = {"id": "1000220", "kanji": [], "kana": [{"text": "あした"}], "sense": []}
    result = _transform_word(w, jlpt_map={"1000220": "N5"})
    assert result["jlpt_waller"] == "N5"


def test_is_common_true() -> None:
    from build.transform.words import _is_common
    assert _is_common({"kanji": [{"text": "食", "common": True}], "kana": []})


def test_is_common_false() -> None:
    from build.transform.words import _is_common
    assert not _is_common({"kanji": [{"text": "食", "common": False}], "kana": []})
    assert not _is_common({"kanji": [], "kana": []})


# ===========================================================================
# radicals transform functions
# ===========================================================================

def test_strip_wiki_markup_links() -> None:
    from build.transform.radicals import _strip_wiki_markup
    assert _strip_wiki_markup("[[one]]") == "one"
    # Wiki syntax: [[link|display]] → display text is kept
    assert _strip_wiki_markup("[[link|display]]") == "display"


def test_strip_wiki_markup_bold_italic() -> None:
    from build.transform.radicals import _strip_wiki_markup
    assert _strip_wiki_markup("'''bold'''") == "bold"
    assert _strip_wiki_markup("''italic''") == "italic"


def test_extract_radical_forms_primary_and_alternates() -> None:
    from build.transform.radicals import _extract_radical_forms
    # Simulate a cell with primary + alternates
    cell = "'''<big>{{lang|zh-Hant|人}}<br/>({{lang|zh|亻}}、{{lang|zh|𠆢}})</big>'''"
    primary, alternates = _extract_radical_forms(cell)
    assert primary == "人"
    assert "亻" in alternates
    assert "𠆢" in alternates


def test_extract_radical_forms_primary_only() -> None:
    from build.transform.radicals import _extract_radical_forms
    cell = "'''<big>{{lang|zh-Hant|一}}</big>'''"
    primary, alternates = _extract_radical_forms(cell)
    assert primary == "一"
    assert alternates == []


# ===========================================================================
# pitch transform functions
# ===========================================================================

def test_parse_positions_single() -> None:
    from build.transform.pitch import _parse_positions
    assert _parse_positions("0") == [0]


def test_parse_positions_multiple() -> None:
    from build.transform.pitch import _parse_positions
    assert _parse_positions("1,2,3") == [1, 2, 3]


def test_parse_positions_empty() -> None:
    from build.transform.pitch import _parse_positions
    assert _parse_positions("") == []


def test_parse_positions_skips_invalid() -> None:
    from build.transform.pitch import _parse_positions
    assert _parse_positions("1,x,2") == [1, 2]


# ===========================================================================
# stroke_order transform functions
# ===========================================================================

def test_codepoint_filename_kanji() -> None:
    from build.transform.stroke_order import _codepoint_filename
    # 日 = U+65E5
    result = _codepoint_filename("日")
    assert result == "065e5.svg"


def test_codepoint_filename_ascii() -> None:
    from build.transform.stroke_order import _codepoint_filename
    result = _codepoint_filename("A")
    assert result == "00041.svg"


# ===========================================================================
# conjugations transform functions (beyond godan)
# ===========================================================================

def test_conjugate_ichidan_taberu() -> None:
    from build.transform.conjugations import _conjugate_ichidan
    forms = _conjugate_ichidan("たべる")
    assert forms["dictionary"] == "たべる"
    assert forms["polite_nonpast"] == "たべます"
    assert forms["te_form"] == "たべて"
    assert forms["nai_form"] == "たべない"
    assert forms["potential"] == "たべられる"
    assert forms["imperative"] == "たべろ"


def test_conjugate_ichidan_miru() -> None:
    from build.transform.conjugations import _conjugate_ichidan
    forms = _conjugate_ichidan("みる")
    assert forms["polite_nonpast"] == "みます"
    assert forms["nai_form"] == "みない"


def test_conjugate_suru_compound() -> None:
    from build.transform.conjugations import _conjugate_suru_compound
    forms = _conjugate_suru_compound("べんきょうする")
    assert forms["polite_nonpast"] == "べんきょうします"
    assert forms["te_form"] == "べんきょうして"
    assert forms["nai_form"] == "べんきょうしない"
    assert forms["potential"] == "べんきょうできる"


def test_conjugate_suru_compound_not_suru() -> None:
    from build.transform.conjugations import _conjugate_suru_compound
    assert _conjugate_suru_compound("たべる") == {}


def test_conjugate_kuru_irregular_forms() -> None:
    from build.transform.conjugations import _conjugate_kuru
    forms = _conjugate_kuru()
    assert forms["dictionary"] == "くる"
    assert forms["nai_form"] == "こない"
    assert forms["te_form"] == "きて"
    assert forms["polite_nonpast"] == "きます"
    assert forms["imperative"] == "こい"
    assert forms["volitional"] == "こよう"


def test_conjugate_i_adjective_takai() -> None:
    from build.transform.conjugations import _conjugate_i_adjective
    forms = _conjugate_i_adjective("たかい")
    assert forms is not None
    assert forms["negative"] == "たかくない"
    assert forms["past"] == "たかかった"
    assert forms["adverbial"] == "たかく"
    assert forms["te_form"] == "たかくて"


def test_conjugate_i_adjective_not_i_ending() -> None:
    from build.transform.conjugations import _conjugate_i_adjective
    assert _conjugate_i_adjective("しずか") is None


def test_conjugate_na_adjective() -> None:
    from build.transform.conjugations import _conjugate_na_adjective
    forms = _conjugate_na_adjective("しずか")
    assert forms["dictionary"] == "しずかだ"
    assert forms["polite_nonpast"] == "しずかです"
    assert forms["polite_past"] == "しずかでした"
    assert forms["attributive"] == "しずかな"


def test_longest_common_suffix_length() -> None:
    from build.transform.conjugations import _longest_common_suffix_length
    assert _longest_common_suffix_length("食べる", "たべる") == 2  # べる
    assert _longest_common_suffix_length("abc", "xyz") == 0
    assert _longest_common_suffix_length("abc", "abc") == 3
    assert _longest_common_suffix_length("", "") == 0


def test_replace_prefix_in_forms() -> None:
    from build.transform.conjugations import _replace_prefix_in_forms
    forms = {"a": "たべます", "b": "たべた", "c": "きます"}
    result = _replace_prefix_in_forms(forms, "たべ", "食べ")
    assert result["a"] == "食べます"
    assert result["b"] == "食べた"
    assert result["c"] == "きます"  # no match, unchanged


def test_replace_prefix_preserves_empty() -> None:
    from build.transform.conjugations import _replace_prefix_in_forms
    forms = {"a": "", "b": "たべます"}
    result = _replace_prefix_in_forms(forms, "たべ", "食べ")
    assert result["a"] == ""
    assert result["b"] == "食べます"


def test_display_forms_adj_na() -> None:
    from build.transform.conjugations import _display_forms_adj_na
    forms = {
        "dictionary": "しずかだ",
        "polite_nonpast": "しずかです",
        "attributive": "しずかな",
    }
    result = _display_forms_adj_na("静か", "しずか", forms)
    assert result["polite_nonpast"] == "静かです"
    assert result["attributive"] == "静かな"


def test_display_forms_common_suffix() -> None:
    from build.transform.conjugations import _display_forms_common_suffix
    forms = {
        "dictionary": "たべる",
        "polite_nonpast": "たべます",
        "nai_form": "たべない",
    }
    result = _display_forms_common_suffix("食べる", "たべる", forms)
    assert result["polite_nonpast"] == "食べます"
    assert result["nai_form"] == "食べない"


# ===========================================================================
# grammar transform functions
# ===========================================================================

def test_validate_entry_complete() -> None:
    from build.transform.grammar import _validate_entry
    entry = {
        "id": "test-entry",
        "pattern": "test",
        "level": "N5",
        "meaning_en": "test meaning",
        "formation": "test formation",
        "examples": [{"japanese": "テスト", "english": "test"}],
        "review_status": "draft",
        "sources": ["test"],
    }
    # Should not raise
    _validate_entry(entry, "test.json")


def test_validate_entry_missing_fields() -> None:
    from build.transform.grammar import _validate_entry
    entry = {"id": "test-entry", "pattern": "test"}
    with pytest.raises(ValueError, match="missing required fields"):
        _validate_entry(entry, "test.json")


def test_validate_entry_empty_examples() -> None:
    from build.transform.grammar import _validate_entry
    entry = {
        "id": "test-entry",
        "pattern": "test",
        "level": "N5",
        "meaning_en": "test meaning",
        "formation": "test formation",
        "examples": [],
        "review_status": "draft",
        "sources": ["test"],
    }
    with pytest.raises(ValueError, match="no examples"):
        _validate_entry(entry, "test.json")


def test_normalize_japanese_strips_trailing_punct() -> None:
    from build.transform.grammar import _normalize_japanese_for_match
    assert _normalize_japanese_for_match("テストです。") == "テストです"
    assert _normalize_japanese_for_match("テストです！") == "テストです"


def test_normalize_japanese_collapses_whitespace() -> None:
    from build.transform.grammar import _normalize_japanese_for_match
    assert _normalize_japanese_for_match("  テスト  です  ") == "テスト です"


def test_normalize_japanese_strips_quotes() -> None:
    from build.transform.grammar import _normalize_japanese_for_match
    assert _normalize_japanese_for_match("「テストです」") == "テストです"


def test_normalize_japanese_nfkc_width() -> None:
    """Half-width katakana should be normalized to full-width."""
    from build.transform.grammar import _normalize_japanese_for_match
    # ﾃｽﾄ is half-width katakana for テスト
    assert _normalize_japanese_for_match("ﾃｽﾄ") == "テスト"


def test_normalize_japanese_empty() -> None:
    from build.transform.grammar import _normalize_japanese_for_match
    assert _normalize_japanese_for_match("") == ""


# ===========================================================================
# cross_links transform functions
# ===========================================================================

def test_is_kanji_char_cjk() -> None:
    from build.transform.cross_links import _is_kanji_char
    assert _is_kanji_char("漢") is True
    assert _is_kanji_char("字") is True
    assert _is_kanji_char("日") is True


def test_is_kanji_char_kana() -> None:
    from build.transform.cross_links import _is_kanji_char
    assert _is_kanji_char("あ") is False
    assert _is_kanji_char("ア") is False


def test_is_kanji_char_ascii() -> None:
    from build.transform.cross_links import _is_kanji_char
    assert _is_kanji_char("A") is False
    assert _is_kanji_char("1") is False


def test_build_word_cross_refs_basic() -> None:
    """Verify cross-reference index generation from synthetic words data."""
    from build.transform.cross_links import _build_word_cross_refs
    words_data = {
        "words": [
            {
                "id": "100",
                "kanji": [{"text": "漢字"}],
                "kana": [{"text": "かんじ"}],
                "sense": [{
                    "examples": [
                        {"sentence_id": "456"},
                    ],
                }],
            },
            {
                "id": "200",
                "kanji": [{"text": "日本"}],
                "kana": [{"text": "にほん"}],
                "sense": [],
            },
        ],
    }
    k2w, w2k, w2s = _build_word_cross_refs(words_data)
    # kanji-to-words
    assert "漢" in k2w
    assert "100" in k2w["漢"]
    assert "字" in k2w
    assert "100" in k2w["字"]
    assert "日" in k2w
    assert "200" in k2w["日"]
    assert "本" in k2w
    assert "200" in k2w["本"]
    # word-to-kanji
    assert w2k["100"] == ["漢", "字"]
    assert w2k["200"] == ["日", "本"]
    # word-to-sentences
    assert w2s["100"] == ["456"]
    assert "200" not in w2s  # no examples


def test_build_word_cross_refs_kana_only() -> None:
    """Kana-only words should not create kanji cross-refs."""
    from build.transform.cross_links import _build_word_cross_refs
    words_data = {
        "words": [
            {
                "id": "300",
                "kanji": [],
                "kana": [{"text": "すし"}],
                "sense": [],
            },
        ],
    }
    k2w, w2k, w2s = _build_word_cross_refs(words_data)
    assert "300" not in w2k
    assert len(k2w) == 0
