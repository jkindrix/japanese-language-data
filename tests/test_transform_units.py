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


def test_replace_prefix_preserves_empty() -> None:
    from build.transform.conjugations import _replace_prefix_in_forms
    forms = {"a": "", "b": "たべます"}
    result = _replace_prefix_in_forms(forms, "たべ", "食べ")
    assert result["a"] == ""
    assert result["b"] == "食べます"


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


# ===========================================================================
# Standard godan subtypes — one representative verb per class
# ===========================================================================

def test_conjugate_godan_v5k_kaku() -> None:
    """v5k (standard く-ending): 書く conjugation."""
    from build.transform.conjugations import _conjugate_godan
    forms = _conjugate_godan("かく", "v5k")
    assert forms is not None
    assert forms["te_form"] == "かいて", f"v5k te_form: expected かいて, got {forms['te_form']!r}"
    assert forms["ta_form"] == "かいた", f"v5k ta_form: expected かいた, got {forms['ta_form']!r}"
    assert forms["nai_form"] == "かかない", f"v5k nai_form: expected かかない, got {forms['nai_form']!r}"
    assert forms["polite_nonpast"] == "かきます", f"v5k polite_nonpast: expected かきます, got {forms['polite_nonpast']!r}"


def test_conjugate_godan_v5g_oyogu() -> None:
    """v5g (ぐ-ending): 泳ぐ conjugation."""
    from build.transform.conjugations import _conjugate_godan
    forms = _conjugate_godan("およぐ", "v5g")
    assert forms is not None
    assert forms["te_form"] == "およいで", f"v5g te_form: expected およいで, got {forms['te_form']!r}"
    assert forms["ta_form"] == "およいだ", f"v5g ta_form: expected およいだ, got {forms['ta_form']!r}"
    assert forms["nai_form"] == "およがない", f"v5g nai_form: expected およがない, got {forms['nai_form']!r}"
    assert forms["polite_nonpast"] == "およぎます", f"v5g polite_nonpast: expected およぎます, got {forms['polite_nonpast']!r}"


def test_conjugate_godan_v5s_hanasu() -> None:
    """v5s (す-ending): 話す conjugation."""
    from build.transform.conjugations import _conjugate_godan
    forms = _conjugate_godan("はなす", "v5s")
    assert forms is not None
    assert forms["te_form"] == "はなして", f"v5s te_form: expected はなして, got {forms['te_form']!r}"
    assert forms["ta_form"] == "はなした", f"v5s ta_form: expected はなした, got {forms['ta_form']!r}"
    assert forms["nai_form"] == "はなさない", f"v5s nai_form: expected はなさない, got {forms['nai_form']!r}"
    assert forms["polite_nonpast"] == "はなします", f"v5s polite_nonpast: expected はなします, got {forms['polite_nonpast']!r}"


def test_conjugate_godan_v5t_motsu() -> None:
    """v5t (つ-ending): 持つ conjugation."""
    from build.transform.conjugations import _conjugate_godan
    forms = _conjugate_godan("もつ", "v5t")
    assert forms is not None
    assert forms["te_form"] == "もって", f"v5t te_form: expected もって, got {forms['te_form']!r}"
    assert forms["ta_form"] == "もった", f"v5t ta_form: expected もった, got {forms['ta_form']!r}"
    assert forms["nai_form"] == "もたない", f"v5t nai_form: expected もたない, got {forms['nai_form']!r}"
    assert forms["polite_nonpast"] == "もちます", f"v5t polite_nonpast: expected もちます, got {forms['polite_nonpast']!r}"


def test_conjugate_godan_v5n_shinu() -> None:
    """v5n (ぬ-ending): 死ぬ conjugation."""
    from build.transform.conjugations import _conjugate_godan
    forms = _conjugate_godan("しぬ", "v5n")
    assert forms is not None
    assert forms["te_form"] == "しんで", f"v5n te_form: expected しんで, got {forms['te_form']!r}"
    assert forms["ta_form"] == "しんだ", f"v5n ta_form: expected しんだ, got {forms['ta_form']!r}"
    assert forms["nai_form"] == "しなない", f"v5n nai_form: expected しなない, got {forms['nai_form']!r}"
    assert forms["polite_nonpast"] == "しにます", f"v5n polite_nonpast: expected しにます, got {forms['polite_nonpast']!r}"


def test_conjugate_godan_v5b_asobu() -> None:
    """v5b (ぶ-ending): 遊ぶ conjugation."""
    from build.transform.conjugations import _conjugate_godan
    forms = _conjugate_godan("あそぶ", "v5b")
    assert forms is not None
    assert forms["te_form"] == "あそんで", f"v5b te_form: expected あそんで, got {forms['te_form']!r}"
    assert forms["ta_form"] == "あそんだ", f"v5b ta_form: expected あそんだ, got {forms['ta_form']!r}"
    assert forms["nai_form"] == "あそばない", f"v5b nai_form: expected あそばない, got {forms['nai_form']!r}"
    assert forms["polite_nonpast"] == "あそびます", f"v5b polite_nonpast: expected あそびます, got {forms['polite_nonpast']!r}"


def test_conjugate_godan_v5m_yomu() -> None:
    """v5m (む-ending): 読む conjugation."""
    from build.transform.conjugations import _conjugate_godan
    forms = _conjugate_godan("よむ", "v5m")
    assert forms is not None
    assert forms["te_form"] == "よんで", f"v5m te_form: expected よんで, got {forms['te_form']!r}"
    assert forms["ta_form"] == "よんだ", f"v5m ta_form: expected よんだ, got {forms['ta_form']!r}"
    assert forms["nai_form"] == "よまない", f"v5m nai_form: expected よまない, got {forms['nai_form']!r}"
    assert forms["polite_nonpast"] == "よみます", f"v5m polite_nonpast: expected よみます, got {forms['polite_nonpast']!r}"


def test_conjugate_godan_v5u_kau() -> None:
    """v5u (standard う-ending, not v5u-s): 買う conjugation.

    Key distinguisher from v5u-s: te/ta use って/った (not うて/うた),
    and nai uses わない (historical わ-row).
    """
    from build.transform.conjugations import _conjugate_godan
    forms = _conjugate_godan("かう", "v5u")
    assert forms is not None
    assert forms["te_form"] == "かって", f"v5u te_form: expected かって, got {forms['te_form']!r}"
    assert forms["ta_form"] == "かった", f"v5u ta_form: expected かった, got {forms['ta_form']!r}"
    assert forms["nai_form"] == "かわない", f"v5u nai_form: expected かわない, got {forms['nai_form']!r}"
    assert forms["polite_nonpast"] == "かいます", f"v5u polite_nonpast: expected かいます, got {forms['polite_nonpast']!r}"


def test_conjugate_godan_v5r_hashiru() -> None:
    """v5r (standard る-ending, not v5r-i): 走る conjugation."""
    from build.transform.conjugations import _conjugate_godan
    forms = _conjugate_godan("はしる", "v5r")
    assert forms is not None
    assert forms["te_form"] == "はしって", f"v5r te_form: expected はしって, got {forms['te_form']!r}"
    assert forms["ta_form"] == "はしった", f"v5r ta_form: expected はしった, got {forms['ta_form']!r}"
    assert forms["nai_form"] == "はしらない", f"v5r nai_form: expected はしらない, got {forms['nai_form']!r}"
    assert forms["polite_nonpast"] == "はしります", f"v5r polite_nonpast: expected はしります, got {forms['polite_nonpast']!r}"


# ===========================================================================
# Ichidan — full 16-form coverage for 食べる
# ===========================================================================

def test_conjugate_ichidan_taberu_all_forms() -> None:
    """Verify all 16 conjugation slots for 食べる (たべる), including the
    less-commonly tested conditional and passive/causative slots."""
    from build.transform.conjugations import _conjugate_ichidan
    forms = _conjugate_ichidan("たべる")
    assert forms["dictionary"] == "たべる", f"dictionary: {forms['dictionary']!r}"
    assert forms["polite_nonpast"] == "たべます", f"polite_nonpast: {forms['polite_nonpast']!r}"
    assert forms["polite_past"] == "たべました", f"polite_past: {forms['polite_past']!r}"
    assert forms["polite_negative"] == "たべません", f"polite_negative: {forms['polite_negative']!r}"
    assert forms["polite_past_negative"] == "たべませんでした", f"polite_past_negative: {forms['polite_past_negative']!r}"
    assert forms["te_form"] == "たべて", f"te_form: {forms['te_form']!r}"
    assert forms["ta_form"] == "たべた", f"ta_form: {forms['ta_form']!r}"
    assert forms["nai_form"] == "たべない", f"nai_form: {forms['nai_form']!r}"
    assert forms["nakatta_form"] == "たべなかった", f"nakatta_form: {forms['nakatta_form']!r}"
    assert forms["potential"] == "たべられる", f"potential: {forms['potential']!r}"
    assert forms["passive"] == "たべられる", f"passive: {forms['passive']!r}"
    assert forms["causative"] == "たべさせる", f"causative: {forms['causative']!r}"
    assert forms["imperative"] == "たべろ", f"imperative: {forms['imperative']!r}"
    assert forms["volitional"] == "たべよう", f"volitional: {forms['volitional']!r}"
    assert forms["conditional_ba"] == "たべれば", f"conditional_ba: {forms['conditional_ba']!r}"
    assert forms["conditional_tara"] == "たべたら", f"conditional_tara: {forms['conditional_tara']!r}"


# ===========================================================================
# Kuru — untested form assertions
# ===========================================================================

def test_conjugate_kuru_extended_forms() -> None:
    """Verify the kuru forms not covered by test_conjugate_kuru_irregular_forms."""
    from build.transform.conjugations import _conjugate_kuru
    forms = _conjugate_kuru()
    assert forms["potential"] == "こられる", f"potential: {forms['potential']!r}"
    assert forms["causative"] == "こさせる", f"causative: {forms['causative']!r}"
    assert forms["conditional_ba"] == "くれば", f"conditional_ba: {forms['conditional_ba']!r}"
    assert forms["conditional_tara"] == "きたら", f"conditional_tara: {forms['conditional_tara']!r}"
    assert forms["imperative"] == "こい", f"imperative: {forms['imperative']!r}"
    assert forms["volitional"] == "こよう", f"volitional: {forms['volitional']!r}"
    assert forms["passive"] == "こられる", f"passive: {forms['passive']!r}"


# ===========================================================================
# build/utils.py shared utility functions
# ===========================================================================

def test_load_json_from_tgz_extracts_json(tmp_path) -> None:
    """load_json_from_tgz should extract and parse the first JSON in the archive."""
    import io
    import tarfile as tarfile_mod

    from build.utils import load_json_from_tgz

    payload = {"hello": "world", "number": 42}
    tgz_path = tmp_path / "test.json.tgz"

    buf = io.BytesIO()
    with tarfile_mod.open(fileobj=buf, mode="w:gz") as tf:
        data = json.dumps(payload).encode("utf-8")
        info = tarfile_mod.TarInfo(name="test.json")
        info.size = len(data)
        tf.addfile(info, io.BytesIO(data))
    tgz_path.write_bytes(buf.getvalue())

    result = load_json_from_tgz(tgz_path)
    assert result == payload, f"expected {payload!r}, got {result!r}"


def test_load_json_from_tgz_no_json_raises(tmp_path) -> None:
    """load_json_from_tgz should raise RuntimeError when no JSON member exists."""
    import io
    import tarfile as tarfile_mod

    from build.utils import load_json_from_tgz

    tgz_path = tmp_path / "empty.tgz"

    buf = io.BytesIO()
    with tarfile_mod.open(fileobj=buf, mode="w:gz") as tf:
        data = b"not json at all"
        info = tarfile_mod.TarInfo(name="readme.txt")
        info.size = len(data)
        tf.addfile(info, io.BytesIO(data))
    tgz_path.write_bytes(buf.getvalue())

    with pytest.raises(RuntimeError, match="No JSON file found"):
        load_json_from_tgz(tgz_path)


def test_load_vocab_jlpt_map_missing_file_returns_empty(tmp_path) -> None:
    """load_vocab_jlpt_map with a missing path should return an empty dict."""
    from build.utils import load_vocab_jlpt_map

    missing = tmp_path / "does-not-exist.json"
    result = load_vocab_jlpt_map(missing)
    assert result == {}, f"expected empty dict, got {result!r}"


def test_load_vocab_jlpt_map_easier_level_wins(tmp_path) -> None:
    """D4 easier-level-wins: when the same jmdict_seq appears at N2 and N5,
    N5 (the easier level) must win regardless of which is encountered first."""
    from build.utils import load_vocab_jlpt_map

    fake = tmp_path / "jlpt.json"
    fake.write_text(
        json.dumps({
            "metadata": {"source": "test", "license": "test",
                         "generated": "2026-04-12", "count": 2, "field_notes": {}},
            "classifications": [
                {"kind": "vocab", "jmdict_seq": "9999999", "level": "N2", "text": "遭う"},
                {"kind": "vocab", "jmdict_seq": "9999999", "level": "N5", "text": "会う"},
            ],
        }),
        encoding="utf-8",
    )
    result = load_vocab_jlpt_map(fake)
    assert result.get("9999999") == "N5", \
        f"N5 should win over N2 (easier wins), got {result.get('9999999')!r}"


def test_is_common_true_from_utils() -> None:
    """is_common returns True when any kanji writing is flagged common."""
    from build.utils import is_common

    word = {"kanji": [{"text": "食べる", "common": True}], "kana": []}
    assert is_common(word) is True, "expected True for common kanji writing"


def test_is_common_false_from_utils() -> None:
    """is_common returns False when no writing is flagged common."""
    from build.utils import is_common

    word = {"kanji": [{"text": "食べる", "common": False}], "kana": []}
    assert is_common(word) is False, "expected False for non-common writing"


def test_is_common_kana_only_common(tmp_path) -> None:
    """is_common returns True for a kana-only word flagged common."""
    from build.utils import is_common

    word = {"kanji": [], "kana": [{"text": "ある", "common": True}]}
    assert is_common(word) is True, "expected True for common kana-only word"


def test_is_common_empty_word(tmp_path) -> None:
    """is_common returns False for a word with no kanji or kana entries."""
    from build.utils import is_common

    word = {"kanji": [], "kana": []}
    assert is_common(word) is False, "expected False for word with no writings"


# ===========================================================================
# build/bump_release.py
# ===========================================================================

def test_latest_changelog_version_returns_version_string() -> None:
    """latest_changelog_version should return a semver string matching the
    actual top CHANGELOG entry."""
    from build.bump_release import latest_changelog_version

    version, date_str = latest_changelog_version()
    # Must be a non-empty semver-like string
    assert version, "expected a non-empty version string from CHANGELOG"
    parts = version.split(".")
    assert len(parts) == 3, f"expected N.N.N version, got {version!r}"
    for part in parts:
        assert part.isdigit(), f"version part {part!r} is not a digit in {version!r}"


def test_version_header_re_matches_full_header() -> None:
    """VERSION_HEADER_RE must match '## [0.7.2] — 2026-04-12' and extract
    both the version number and the date."""
    from build.bump_release import VERSION_HEADER_RE

    line = "## [0.7.2] — 2026-04-12"
    m = VERSION_HEADER_RE.search(line)
    assert m is not None, f"VERSION_HEADER_RE should match {line!r} but did not"
    assert m.group(1) == "0.7.2", f"expected version '0.7.2', got {m.group(1)!r}"
    assert m.group(2) == "2026-04-12", f"expected date '2026-04-12', got {m.group(2)!r}"


def test_version_header_re_rejects_unreleased() -> None:
    """VERSION_HEADER_RE must NOT match '## [Unreleased]' — that is not a
    concrete release and must be skipped by latest_changelog_version."""
    from build.bump_release import VERSION_HEADER_RE

    line = "## [Unreleased]"
    m = VERSION_HEADER_RE.search(line)
    assert m is None, f"VERSION_HEADER_RE should not match {line!r} but did: {m!r}"


def test_load_manifest_returns_dict_with_version() -> None:
    """_load_manifest should return a dict that has a 'version' key."""
    from build.bump_release import _load_manifest

    manifest = _load_manifest()
    assert isinstance(manifest, dict), f"expected dict, got {type(manifest)!r}"
    assert "version" in manifest, "manifest should have a 'version' key"
    assert isinstance(manifest["version"], str), \
        f"manifest['version'] should be a string, got {type(manifest['version'])!r}"


# ===========================================================================
# build/transform/jlpt.py — JLPT parsers
# ===========================================================================

def test_parse_vocab_csv_basic(tmp_path) -> None:
    """_parse_vocab_csv should parse a stephenmk-format CSV into entries."""
    import csv as csv_mod
    from build.transform.jlpt import _parse_vocab_csv

    csv_path = tmp_path / "n5.csv"
    rows = [
        {"jmdict_seq": "1000220", "kana": "あした", "kanji": "明日",
         "waller_definition": "tomorrow"},
        {"jmdict_seq": "1588800", "kana": "いぬ", "kanji": "",
         "waller_definition": "dog"},
    ]
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv_mod.DictWriter(
            f, fieldnames=["jmdict_seq", "kana", "kanji", "waller_definition"]
        )
        writer.writeheader()
        writer.writerows(rows)

    entries = _parse_vocab_csv(csv_path, "N5", "2026-04-12")

    assert len(entries) == 2, f"expected 2 entries, got {len(entries)}"

    # First entry has a kanji writing — that should become text
    e0 = entries[0]
    assert e0["text"] == "明日", f"expected text='明日', got {e0['text']!r}"
    assert e0["reading"] == "あした", f"expected reading='あした', got {e0['reading']!r}"
    assert e0["level"] == "N5", f"expected level='N5', got {e0['level']!r}"
    assert e0["kind"] == "vocab", f"expected kind='vocab', got {e0['kind']!r}"
    assert e0["jmdict_seq"] == "1000220", f"expected jmdict_seq='1000220', got {e0['jmdict_seq']!r}"
    assert e0["meaning_en"] == "tomorrow", f"expected meaning_en='tomorrow', got {e0['meaning_en']!r}"

    # Second entry has no kanji writing — kana should become text
    e1 = entries[1]
    assert e1["text"] == "いぬ", f"kana-only: expected text='いぬ', got {e1['text']!r}"


def test_parse_kanji_jlpt_basic(tmp_path) -> None:
    """_parse_kanji_jlpt should emit kind='kanji' entries for characters with
    a non-null jlpt_new field, and skip those without one."""
    from build.transform.jlpt import _parse_kanji_jlpt

    kanji_json = tmp_path / "kanji-data.json"
    kanji_json.write_text(
        json.dumps({
            "一": {"jlpt_new": 5, "meanings": ["one", "one radical"]},
            "語": {"jlpt_new": 4, "meanings": ["language", "word"]},
            "𠀀": {"jlpt_new": None, "meanings": []},   # no JLPT level — should be skipped
        }),
        encoding="utf-8",
    )

    entries = _parse_kanji_jlpt(kanji_json, "2026-04-12")

    # Only the two characters with a non-null jlpt_new should appear
    assert len(entries) == 2, f"expected 2 entries, got {len(entries)}"

    texts = {e["text"] for e in entries}
    assert "一" in texts, "'一' should be in kanji JLPT entries"
    assert "語" in texts, "'語' should be in kanji JLPT entries"
    assert "𠀀" not in texts, "'𠀀' (no JLPT level) should be excluded"

    # Spot-check field values for 一
    ichi = next(e for e in entries if e["text"] == "一")
    assert ichi["level"] == "N5", f"expected level='N5', got {ichi['level']!r}"
    assert ichi["kind"] == "kanji", f"expected kind='kanji', got {ichi['kind']!r}"
    assert ichi["meaning_en"] == "one", f"expected meaning_en='one', got {ichi['meaning_en']!r}"


def test_parse_curated_grammar_basic(tmp_path, monkeypatch) -> None:
    """_parse_curated_grammar should read *.json files from GRAMMAR_CURATED_DIR
    and emit kind='grammar' entries for each valid grammar point."""
    import build.transform.jlpt as jlpt_mod
    from build.transform.jlpt import _parse_curated_grammar

    grammar_dir = tmp_path / "grammar-curated"
    grammar_dir.mkdir()

    # Write a two-entry grammar file
    gp_data = [
        {
            "id": "te-form-request",
            "pattern": "〜てください",
            "level": "N5",
            "meaning_en": "please do ~",
        },
        {
            "id": "nai-form-prohibition",
            "pattern": "〜てはいけない",
            "level": "N4",
            "meaning_en": "must not ~",
        },
    ]
    (grammar_dir / "n5-n4.json").write_text(
        json.dumps(gp_data), encoding="utf-8"
    )

    # Write a non-list file — should be silently skipped
    (grammar_dir / "invalid.json").write_text(
        json.dumps({"not": "a list"}), encoding="utf-8"
    )

    # Patch the module-level constant so the function reads our tmp dir
    monkeypatch.setattr(jlpt_mod, "GRAMMAR_CURATED_DIR", grammar_dir)

    entries = _parse_curated_grammar("2026-04-12")

    assert len(entries) == 2, f"expected 2 grammar entries, got {len(entries)}"

    ids = {e["grammar_id"] for e in entries}
    assert "te-form-request" in ids, "'te-form-request' missing from entries"
    assert "nai-form-prohibition" in ids, "'nai-form-prohibition' missing from entries"

    e0 = next(e for e in entries if e["grammar_id"] == "te-form-request")
    assert e0["kind"] == "grammar", f"expected kind='grammar', got {e0['kind']!r}"
    assert e0["level"] == "N5", f"expected level='N5', got {e0['level']!r}"
    assert e0["text"] == "〜てください", f"expected text='〜てください', got {e0['text']!r}"
    assert e0["meaning_en"] == "please do ~", f"expected meaning_en='please do ~', got {e0['meaning_en']!r}"


def test_parse_curated_grammar_missing_dir(monkeypatch) -> None:
    """_parse_curated_grammar should return an empty list when GRAMMAR_CURATED_DIR
    does not exist (e.g. in a stripped checkout)."""
    import build.transform.jlpt as jlpt_mod
    from build.transform.jlpt import _parse_curated_grammar
    from pathlib import Path

    monkeypatch.setattr(jlpt_mod, "GRAMMAR_CURATED_DIR", Path("/nonexistent/grammar-curated"))

    entries = _parse_curated_grammar("2026-04-12")
    assert entries == [], f"expected empty list for missing dir, got {entries!r}"


# ---------------------------------------------------------------------------
# cross_links._is_kanji_char — CJK block detection
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("char, expected", [
    ("亜", True),      # CJK Unified Ideographs (U+4E00-U+9FFF)
    ("食", True),
    ("龍", True),
    ("𠂉", True),      # CJK Extension B (U+20000-U+2A6DF)
    ("a", False),       # Latin
    ("A", False),
    ("ぁ", False),      # Hiragana
    ("ア", False),      # Katakana
    ("1", False),       # Digit
    ("Ａ", False),      # Fullwidth Latin
    ("１", False),      # Fullwidth digit
])
def test_is_kanji_char(char: str, expected: bool) -> None:
    from build.transform.cross_links import _is_kanji_char
    assert _is_kanji_char(char) is expected, (
        f"_is_kanji_char({char!r}) should be {expected}"
    )


# ---------------------------------------------------------------------------
# cross_links._build_word_cross_refs — core cross-reference logic
# ---------------------------------------------------------------------------

def test_build_word_cross_refs_basic() -> None:
    """Cross-ref builder extracts kanji-to-word and word-to-kanji mappings."""
    from build.transform.cross_links import _build_word_cross_refs

    words_data = {"words": [
        {
            "id": "100",
            "kanji": [{"text": "漢字"}],
            "kana": [{"text": "かんじ"}],
            "sense": [{"examples": [{"sentence_id": "s1"}]}],
        },
        {
            "id": "200",
            "kanji": [{"text": "漢方"}],
            "kana": [{"text": "かんぽう"}],
            "sense": [],
        },
    ]}
    k2w, w2k, w2s = _build_word_cross_refs(words_data)

    # 漢 appears in both words
    assert "漢" in k2w
    assert set(k2w["漢"]) == {"100", "200"}

    # 字 only in first word
    assert "字" in k2w
    assert k2w["字"] == ["100"]

    # Word-to-kanji mappings
    assert set(w2k["100"]) == {"漢", "字"}
    assert set(w2k["200"]) == {"漢", "方"}

    # Word-to-sentences
    assert w2s["100"] == ["s1"]
    assert "200" not in w2s


def test_build_word_cross_refs_kana_only() -> None:
    """Kana-only words produce no kanji cross-refs."""
    from build.transform.cross_links import _build_word_cross_refs

    words_data = {"words": [
        {
            "id": "300",
            "kanji": [],
            "kana": [{"text": "ああ"}],
            "sense": [],
        },
    ]}
    k2w, w2k, w2s = _build_word_cross_refs(words_data)
    assert k2w == {}
    assert w2k == {}
    assert w2s == {}


def test_build_word_cross_refs_deduplicates_sentence_ids() -> None:
    """Sentence IDs should be deduplicated across senses."""
    from build.transform.cross_links import _build_word_cross_refs

    words_data = {"words": [
        {
            "id": "400",
            "kanji": [{"text": "食"}],
            "kana": [{"text": "しょく"}],
            "sense": [
                {"examples": [{"sentence_id": "s1"}, {"sentence_id": "s2"}]},
                {"examples": [{"sentence_id": "s1"}]},  # duplicate
            ],
        },
    ]}
    _, _, w2s = _build_word_cross_refs(words_data)
    assert sorted(w2s["400"]) == ["s1", "s2"]


# ---------------------------------------------------------------------------
# cross_links._build_reading_to_words — reading reverse index
# ---------------------------------------------------------------------------

def test_build_reading_to_words_basic() -> None:
    """Reading-to-words maps kana readings to word IDs."""
    from build.transform.cross_links import _build_reading_to_words

    words_data = {"words": [
        {"id": "100", "kana": [{"text": "かん"}]},
        {"id": "200", "kana": [{"text": "かん"}]},  # same reading
        {"id": "300", "kana": [{"text": "はな"}]},
    ]}
    r2w = _build_reading_to_words(words_data)
    assert set(r2w["かん"]) == {"100", "200"}
    assert r2w["はな"] == ["300"]


def test_build_reading_to_words_deduplicates() -> None:
    """Same word ID should not appear twice under same reading."""
    from build.transform.cross_links import _build_reading_to_words

    words_data = {"words": [
        {"id": "100", "kana": [{"text": "かん"}, {"text": "かん"}]},  # dupe
    ]}
    r2w = _build_reading_to_words(words_data)
    assert r2w["かん"] == ["100"]  # not ["100", "100"]


# ---------------------------------------------------------------------------
# names._transform_name — safe conversion
# ---------------------------------------------------------------------------

def test_transform_name_complete_entry() -> None:
    from build.transform.names import _transform_name

    entry = {
        "id": 12345,
        "kanji": [{"text": "太郎"}],
        "kana": [{"text": "たろう"}],
        "translation": [{"text": "Taro"}],
    }
    result = _transform_name(entry)
    assert result["id"] == "12345"  # converted to string
    assert result["kanji"] == [{"text": "太郎"}]
    assert result["kana"] == [{"text": "たろう"}]
    assert result["translation"] == [{"text": "Taro"}]


def test_transform_name_none_fields() -> None:
    from build.transform.names import _transform_name

    entry = {"id": 0, "kanji": None, "kana": None, "translation": None}
    result = _transform_name(entry)
    assert result["id"] == "0"
    assert result["kanji"] == []
    assert result["kana"] == []
    assert result["translation"] == []


def test_transform_name_missing_fields() -> None:
    from build.transform.names import _transform_name

    result = _transform_name({})
    assert result["id"] == ""
    assert result["kanji"] == []
    assert result["kana"] == []
    assert result["translation"] == []


# ---------------------------------------------------------------------------
# export_yomitan — tag bank, term banks, kanji banks
# ---------------------------------------------------------------------------

def test_yomitan_build_tag_bank() -> None:
    from build.export_yomitan import _build_tag_bank

    words_data = {
        "metadata": {
            "tags": {
                "v1": "Ichidan verb",
                "n": "Noun",
                "adj-i": "I-adjective",
            }
        }
    }
    bank = _build_tag_bank(words_data)
    assert len(bank) == 3

    # Sorted by abbreviation
    names = [entry[0] for entry in bank]
    assert names == ["adj-i", "n", "v1"]

    # Category logic: v* and adj* -> partOfSpeech, else misc
    adj_entry = next(e for e in bank if e[0] == "adj-i")
    assert adj_entry[1] == "partOfSpeech"

    n_entry = next(e for e in bank if e[0] == "n")
    assert n_entry[1] == "misc"

    v_entry = next(e for e in bank if e[0] == "v1")
    assert v_entry[1] == "partOfSpeech"


def test_yomitan_build_term_banks_kanji_word() -> None:
    from build.export_yomitan import _build_term_banks

    words_data = {
        "words": [
            {
                "id": "1000",
                "jlpt_waller": "N5",
                "kanji": [{"text": "食べる"}],
                "kana": [{"text": "たべる"}],
                "sense": [{
                    "partOfSpeech": ["v1"],
                    "gloss": [{"text": "to eat"}],
                }],
            },
        ]
    }
    banks = _build_term_banks(words_data)
    assert len(banks) == 1
    assert len(banks[0]) == 1

    entry = banks[0][0]
    assert entry[0] == "食べる"          # term
    assert entry[1] == "たべる"          # reading
    assert entry[4] == 5                 # N5 score
    assert entry[5] == ["to eat"]        # definitions
    assert entry[6] == 1000              # sequence


def test_yomitan_build_term_banks_kana_only() -> None:
    from build.export_yomitan import _build_term_banks

    words_data = {
        "words": [
            {
                "id": "2000",
                "jlpt_waller": None,
                "kanji": [],
                "kana": [{"text": "ああ"}],
                "sense": [{
                    "partOfSpeech": ["intj"],
                    "gloss": [{"text": "ah"}],
                }],
            },
        ]
    }
    banks = _build_term_banks(words_data)
    entry = banks[0][0]
    assert entry[0] == "ああ"            # term = kana
    assert entry[1] == ""                # empty reading for kana-only
    assert entry[4] == 0                 # no JLPT = score 0


def test_yomitan_build_term_banks_no_definitions_skipped() -> None:
    from build.export_yomitan import _build_term_banks

    words_data = {
        "words": [
            {
                "id": "3000",
                "jlpt_waller": None,
                "kanji": [{"text": "空"}],
                "kana": [{"text": "から"}],
                "sense": [{"partOfSpeech": ["n"], "gloss": []}],
            },
        ]
    }
    banks = _build_term_banks(words_data)
    # No definitions -> entry should be skipped
    total_entries = sum(len(b) for b in banks)
    assert total_entries == 0


def test_yomitan_build_term_banks_splits_into_bank_size() -> None:
    from build.export_yomitan import _build_term_banks, BANK_SIZE

    # Create more words than BANK_SIZE
    words = []
    for i in range(BANK_SIZE + 5):
        words.append({
            "id": str(i),
            "jlpt_waller": None,
            "kanji": [{"text": f"字{i}"}],
            "kana": [{"text": f"じ{i}"}],
            "sense": [{"partOfSpeech": ["n"], "gloss": [{"text": f"def{i}"}]}],
        })
    banks = _build_term_banks({"words": words})
    assert len(banks) == 2
    assert len(banks[0]) == BANK_SIZE
    assert len(banks[1]) == 5


def test_yomitan_build_kanji_banks_joyo() -> None:
    from build.export_yomitan import _build_kanji_banks

    kanji_data = {
        "kanji": [
            {
                "character": "食",
                "grade": 2,
                "jlpt_waller": "N5",
                "readings": {"on": ["ショク", "ジキ"], "kun": ["く.う", "た.べる"]},
                "meanings": {"en": ["eat", "food"]},
                "stroke_count": 9,
                "frequency": 328,
            },
        ]
    }
    banks = _build_kanji_banks(kanji_data)
    entry = banks[0][0]
    assert entry[0] == "食"
    assert "ショク" in entry[1]       # on readings
    assert "た.べる" in entry[2]      # kun readings
    assert "joyo" in entry[3]          # tags
    assert "N5" in entry[3]
    assert entry[4] == ["eat", "food"]
    assert entry[5]["strokes"] == "9"
    assert entry[5]["grade"] == "2"
    assert entry[5]["freq"] == "328"
    assert entry[5]["jlpt"] == "N5"


def test_yomitan_build_kanji_banks_jinmeiyo() -> None:
    from build.export_yomitan import _build_kanji_banks

    kanji_data = {
        "kanji": [
            {
                "character": "亮",
                "grade": 9,
                "jlpt_waller": None,
                "readings": {"on": ["リョウ"], "kun": []},
                "meanings": {"en": ["clear"]},
                "stroke_count": 9,
                "frequency": None,
            },
        ]
    }
    banks = _build_kanji_banks(kanji_data)
    entry = banks[0][0]
    assert "jinmeiyo" in entry[3]
    assert "freq" not in entry[5]  # no frequency


def test_yomitan_build_kanji_banks_empty_char_skipped() -> None:
    from build.export_yomitan import _build_kanji_banks

    kanji_data = {"kanji": [{"character": "", "grade": None, "jlpt_waller": None,
                              "readings": {}, "meanings": {}, "stroke_count": None,
                              "frequency": None}]}
    banks = _build_kanji_banks(kanji_data)
    total = sum(len(b) for b in banks)
    assert total == 0


# ---------------------------------------------------------------------------
# stats._count_entries — polymorphic entry counting
# ---------------------------------------------------------------------------

def test_count_entries_list_payload() -> None:
    from build.stats import _count_entries
    assert _count_entries({"words": [1, 2, 3]}, "words") == 3


def test_count_entries_dict_payload() -> None:
    from build.stats import _count_entries
    assert _count_entries({"mapping": {"a": [], "b": []}}, "mapping") == 2


def test_count_entries_none_payload() -> None:
    from build.stats import _count_entries
    assert _count_entries({"words": None}, "words") == 0


def test_count_entries_missing_key() -> None:
    from build.stats import _count_entries
    assert _count_entries({}, "words") == 0


# ---------------------------------------------------------------------------
# bump_release — version regex parsing
# ---------------------------------------------------------------------------

def test_latest_changelog_version_with_date(tmp_path: Path, monkeypatch) -> None:
    import build.bump_release as br
    changelog = tmp_path / "CHANGELOG.md"
    changelog.write_text(
        "# Changelog\n\n## [Unreleased]\n\n## [1.2.3] — 2026-04-12\n\nContent\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(br, "CHANGELOG_PATH", changelog)

    version, date_str = br.latest_changelog_version()
    assert version == "1.2.3"
    assert date_str == "2026-04-12"


def test_latest_changelog_version_without_date(tmp_path: Path, monkeypatch) -> None:
    import build.bump_release as br
    changelog = tmp_path / "CHANGELOG.md"
    changelog.write_text("## [0.1.0]\nContent\n", encoding="utf-8")
    monkeypatch.setattr(br, "CHANGELOG_PATH", changelog)

    version, date_str = br.latest_changelog_version()
    assert version == "0.1.0"
    assert date_str is None


def test_latest_changelog_version_no_match_raises(tmp_path: Path, monkeypatch) -> None:
    import build.bump_release as br
    changelog = tmp_path / "CHANGELOG.md"
    changelog.write_text("## [Unreleased]\nNo versions\n", encoding="utf-8")
    monkeypatch.setattr(br, "CHANGELOG_PATH", changelog)

    with pytest.raises(RuntimeError, match="No concrete-version header"):
        br.latest_changelog_version()


def test_bump_dry_run_no_changes(tmp_path: Path, monkeypatch) -> None:
    import build.bump_release as br
    manifest_path = tmp_path / "manifest.json"
    changelog_path = tmp_path / "CHANGELOG.md"

    manifest_path.write_text(
        json.dumps({"version": "1.0.0", "generated": "2026-04-12",
                     "phase_description": "test v1.0.0"}),
        encoding="utf-8",
    )
    changelog_path.write_text("## [1.0.0] — 2026-04-12\n", encoding="utf-8")

    monkeypatch.setattr(br, "MANIFEST_PATH", manifest_path)
    monkeypatch.setattr(br, "CHANGELOG_PATH", changelog_path)

    rc = br.bump(dry_run=True)
    assert rc == 0


def test_bump_updates_version(tmp_path: Path, monkeypatch) -> None:
    import build.bump_release as br
    manifest_path = tmp_path / "manifest.json"
    changelog_path = tmp_path / "CHANGELOG.md"

    manifest_path.write_text(
        json.dumps({"version": "0.9.0", "generated": "2026-01-01",
                     "phase_description": "old"}),
        encoding="utf-8",
    )
    changelog_path.write_text("## [1.0.0] — 2026-04-12\n", encoding="utf-8")

    monkeypatch.setattr(br, "MANIFEST_PATH", manifest_path)
    monkeypatch.setattr(br, "CHANGELOG_PATH", changelog_path)

    rc = br.bump(dry_run=False)
    assert rc == 0

    updated = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert updated["version"] == "1.0.0"
    assert updated["generated"] == "2026-04-12"


# ---------------------------------------------------------------------------
# grammar._normalize_japanese_for_match — normalization for Tatoeba matching
# ---------------------------------------------------------------------------

def test_normalize_japanese_strips_trailing_punctuation() -> None:
    from build.transform.grammar import _normalize_japanese_for_match
    assert _normalize_japanese_for_match("食べる。") == "食べる"
    assert _normalize_japanese_for_match("食べる、") == "食べる"
    assert _normalize_japanese_for_match("食べる.") == "食べる"


def test_normalize_japanese_strips_whitespace() -> None:
    from build.transform.grammar import _normalize_japanese_for_match
    assert _normalize_japanese_for_match("  食べる  ") == "食べる"


def test_normalize_japanese_noop_for_clean_input() -> None:
    from build.transform.grammar import _normalize_japanese_for_match
    assert _normalize_japanese_for_match("食べる") == "食べる"


# ---------------------------------------------------------------------------
# grammar._validate_entry — structural validation
# ---------------------------------------------------------------------------

def test_validate_entry_valid() -> None:
    from build.transform.grammar import _validate_entry
    entry = {
        "id": "test-1",
        "pattern": "〜てください",
        "meaning_en": "please do ~",
        "level": "N5",
        "formation": "Verb て-form + ください",
        "examples": [{"ja": "食べてください", "en": "Please eat."}],
        "review_status": "draft",
        "sources": ["General knowledge"],
    }
    # Should not raise
    _validate_entry(entry, "test.json")


def test_validate_entry_missing_required_field() -> None:
    from build.transform.grammar import _validate_entry
    entry = {
        "id": "test-2",
        # missing pattern
        "meaning_en": "please do ~",
        "level": "N5",
        "formation": "test",
        "examples": [{"ja": "test", "en": "test"}],
        "review_status": "draft",
        "sources": ["test"],
    }
    with pytest.raises(ValueError, match="missing required fields"):
        _validate_entry(entry, "test.json")


def test_validate_entry_no_examples() -> None:
    from build.transform.grammar import _validate_entry
    entry = {
        "id": "test-3",
        "pattern": "〜てください",
        "meaning_en": "please do ~",
        "level": "N5",
        "formation": "test",
        "examples": [],
        "review_status": "draft",
        "sources": ["test"],
    }
    with pytest.raises(ValueError, match="has no examples"):
        _validate_entry(entry, "test.json")


# ---------------------------------------------------------------------------
# conjugations — additional verb type coverage
# ---------------------------------------------------------------------------

def test_conjugate_ichidan_basic() -> None:
    """Standard ichidan verb 食べる."""
    from build.transform.conjugations import _conjugate_ichidan
    forms = _conjugate_ichidan("たべる")
    assert forms is not None
    assert forms["te_form"] == "たべて"
    assert forms["nai_form"] == "たべない"
    assert forms["polite_nonpast"] == "たべます"
    assert forms["potential"] == "たべられる"
    assert forms["passive"] == "たべられる"
    assert forms["causative"] == "たべさせる"
    assert forms["volitional"] == "たべよう"
    assert forms["imperative"] == "たべろ"
    assert forms["conditional_ba"] == "たべれば"
    assert forms["conditional_tara"] == "たべたら"
    assert forms["ta_form"] == "たべた"


def test_conjugate_ichidan_short() -> None:
    """Ichidan verbs with stem of length 1 (e.g., 見る = みる)."""
    from build.transform.conjugations import _conjugate_ichidan
    forms = _conjugate_ichidan("みる")
    assert forms is not None
    assert forms["te_form"] == "みて"
    assert forms["nai_form"] == "みない"
    assert forms["polite_nonpast"] == "みます"


def test_conjugate_godan_v5g() -> None:
    """v5g (g-column) godan verb: 泳ぐ."""
    from build.transform.conjugations import _conjugate_godan
    forms = _conjugate_godan("およぐ", "v5g")
    assert forms is not None
    assert forms["te_form"] == "およいで"
    assert forms["ta_form"] == "およいだ"
    assert forms["nai_form"] == "およがない"
    assert forms["polite_nonpast"] == "およぎます"


def test_conjugate_godan_v5s() -> None:
    """v5s (s-column) godan verb: 話す."""
    from build.transform.conjugations import _conjugate_godan
    forms = _conjugate_godan("はなす", "v5s")
    assert forms is not None
    assert forms["te_form"] == "はなして"
    assert forms["ta_form"] == "はなした"
    assert forms["nai_form"] == "はなさない"
    assert forms["polite_nonpast"] == "はなします"


def test_conjugate_godan_v5t() -> None:
    """v5t (t-column) godan verb: 待つ."""
    from build.transform.conjugations import _conjugate_godan
    forms = _conjugate_godan("まつ", "v5t")
    assert forms is not None
    assert forms["te_form"] == "まって"
    assert forms["ta_form"] == "まった"
    assert forms["nai_form"] == "またない"


def test_conjugate_godan_v5n() -> None:
    """v5n (n-column) godan verb: 死ぬ."""
    from build.transform.conjugations import _conjugate_godan
    forms = _conjugate_godan("しぬ", "v5n")
    assert forms is not None
    assert forms["te_form"] == "しんで"
    assert forms["ta_form"] == "しんだ"
    assert forms["nai_form"] == "しなない"


def test_conjugate_godan_v5b() -> None:
    """v5b (b-column) godan verb: 遊ぶ."""
    from build.transform.conjugations import _conjugate_godan
    forms = _conjugate_godan("あそぶ", "v5b")
    assert forms is not None
    assert forms["te_form"] == "あそんで"
    assert forms["ta_form"] == "あそんだ"
    assert forms["nai_form"] == "あそばない"


def test_conjugate_godan_v5m() -> None:
    """v5m (m-column) godan verb: 読む."""
    from build.transform.conjugations import _conjugate_godan
    forms = _conjugate_godan("よむ", "v5m")
    assert forms is not None
    assert forms["te_form"] == "よんで"
    assert forms["ta_form"] == "よんだ"
    assert forms["nai_form"] == "よまない"


def test_conjugate_godan_v5r() -> None:
    """v5r (r-column, regular) godan verb: 取る."""
    from build.transform.conjugations import _conjugate_godan
    forms = _conjugate_godan("とる", "v5r")
    assert forms is not None
    assert forms["te_form"] == "とって"
    assert forms["ta_form"] == "とった"
    assert forms["nai_form"] == "とらない"
    assert forms["polite_nonpast"] == "とります"


def test_conjugate_godan_v5u() -> None:
    """v5u (u-column, regular) godan verb: 買う."""
    from build.transform.conjugations import _conjugate_godan
    forms = _conjugate_godan("かう", "v5u")
    assert forms is not None
    assert forms["te_form"] == "かって"
    assert forms["ta_form"] == "かった"
    assert forms["nai_form"] == "かわない"


def test_conjugate_suru_compound() -> None:
    """suru compound verb: 勉強する."""
    from build.transform.conjugations import _conjugate_suru_compound
    forms = _conjugate_suru_compound("べんきょうする")
    assert forms is not None
    assert forms["te_form"] == "べんきょうして"
    assert forms["nai_form"] == "べんきょうしない"
    assert forms["polite_nonpast"] == "べんきょうします"
    assert forms["passive"] == "べんきょうされる"
    assert forms["causative"] == "べんきょうさせる"
    assert forms["potential"] == "べんきょうできる"


def test_conjugate_kuru() -> None:
    """Irregular verb 来る (くる)."""
    from build.transform.conjugations import _conjugate_kuru
    forms = _conjugate_kuru()
    assert forms is not None
    assert forms["te_form"] == "きて"
    assert forms["nai_form"] == "こない"
    assert forms["polite_nonpast"] == "きます"
    assert forms["ta_form"] == "きた"
    assert forms["passive"] == "こられる"


def test_conjugate_i_adjective() -> None:
    """i-adjective: 高い."""
    from build.transform.conjugations import _conjugate_i_adjective
    forms = _conjugate_i_adjective("たかい")
    assert forms is not None
    assert forms["te_form"] == "たかくて"
    assert forms["negative"] == "たかくない"
    assert forms["past"] == "たかかった"
    assert forms["past_negative"] == "たかくなかった"
    assert forms["adverbial"] == "たかく"
    assert forms["conditional_ba"] == "たかければ"
    assert forms["conditional_tara"] == "たかかったら"


def test_conjugate_na_adjective() -> None:
    """na-adjective: 静か."""
    from build.transform.conjugations import _conjugate_na_adjective
    forms = _conjugate_na_adjective("しずか")
    assert forms is not None
    assert forms["te_form"] == "しずかで"
    assert forms["nai_form"] == "しずかではない"
    assert forms["dictionary"] == "しずかだ"
    assert forms["attributive"] == "しずかな"
    assert forms["polite_nonpast"] == "しずかです"
    assert forms["polite_past"] == "しずかでした"


# ---------------------------------------------------------------------------
# conjugations — display_forms helpers
# ---------------------------------------------------------------------------

def test_longest_common_suffix_length() -> None:
    from build.transform.conjugations import _longest_common_suffix_length
    assert _longest_common_suffix_length("食べる", "たべる") == 2  # べる
    assert _longest_common_suffix_length("abc", "def") == 0      # nothing
    assert _longest_common_suffix_length("abc", "abc") == 3      # all
    assert _longest_common_suffix_length("", "abc") == 0


def test_replace_prefix_in_forms() -> None:
    from build.transform.conjugations import _replace_prefix_in_forms
    forms = {"te_form": "たべて", "empty": ""}
    result = _replace_prefix_in_forms(forms, "たべ", "食べ")
    assert result["te_form"] == "食べて"
    assert result["empty"] == ""


def test_replace_prefix_no_match() -> None:
    from build.transform.conjugations import _replace_prefix_in_forms
    forms = {"te_form": "きて"}  # くる → きて, prefix changed
    result = _replace_prefix_in_forms(forms, "たべ", "食べ")
    assert result["te_form"] == "きて"  # unchanged


def test_display_forms_adj_na() -> None:
    from build.transform.conjugations import _display_forms_adj_na
    forms = {"dictionary": "しずかだ", "te_form": "しずかで", "attributive": "しずかな"}
    result = _display_forms_adj_na("静か", "しずか", forms)
    assert result["dictionary"] == "静かだ"
    assert result["te_form"] == "静かで"
    assert result["attributive"] == "静かな"


def test_display_forms_common_suffix_verb() -> None:
    from build.transform.conjugations import _display_forms_common_suffix
    forms = {"te_form": "たべて", "nai_form": "たべない"}
    result = _display_forms_common_suffix("食べる", "たべる", forms)
    assert result["te_form"] == "食べて"
    assert result["nai_form"] == "食べない"


def test_display_forms_common_suffix_no_match() -> None:
    from build.transform.conjugations import _display_forms_common_suffix
    forms = {"te_form": "きて"}
    result = _display_forms_common_suffix("xyz", "abc", forms)
    # No common suffix → verbatim copy
    assert result["te_form"] == "きて"


def test_display_forms_common_suffix_pure_kana() -> None:
    from build.transform.conjugations import _display_forms_common_suffix
    forms = {"te_form": "たべて"}
    result = _display_forms_common_suffix("たべる", "たべる", forms)
    # Same dict/reading → no replacement needed (kanji_prefix is empty)
    assert result["te_form"] == "たべて"


def test_compute_display_forms_dispatch() -> None:
    """_compute_display_forms dispatches adj-na vs. other classes correctly."""
    from build.transform.conjugations import _compute_display_forms

    na_forms = {"dictionary": "しずかだ", "te_form": "しずかで"}
    result_na = _compute_display_forms("静か", "しずか", na_forms, "adj-na")
    assert result_na["dictionary"] == "静かだ"

    verb_forms = {"te_form": "たべて"}
    result_verb = _compute_display_forms("食べる", "たべる", verb_forms, "v1")
    assert result_verb["te_form"] == "食べて"

    # Pure kana → display_forms == forms
    kana_forms = {"te_form": "たべて"}
    result_kana = _compute_display_forms("たべる", "たべる", kana_forms, "v1")
    assert result_kana["te_form"] == "たべて"


# ---------------------------------------------------------------------------
# stats — compute_counts and update_manifest
# ---------------------------------------------------------------------------

def test_compute_counts_against_real_data() -> None:
    """compute_counts on real data should produce non-zero counts for core files."""
    from build.stats import compute_counts
    counts = compute_counts()
    # Core files must exist and have entries
    assert counts.get("data/core/words.json", 0) > 0
    assert counts.get("data/core/kanji.json", 0) > 0


def test_update_manifest_atomic_write(tmp_path: Path) -> None:
    """update_manifest should atomically write to manifest.json."""
    import build.stats as stats_mod

    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps({"version": "test"}), encoding="utf-8")

    from unittest.mock import patch
    with patch.object(stats_mod, "MANIFEST_PATH", manifest_path):
        stats_mod.update_manifest({"data/core/words.json": 100})

    result = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert result["counts"] == {"data/core/words.json": 100}
    assert "generated" in result
    assert result["version"] == "test"  # preserved


def test_print_report_various_counts(capsys) -> None:
    from build.stats import print_report
    counts = {
        "data/core/words.json": 1000,
        "data/optional/names.json": None,
        "data/core/broken.json": -1,
        "data/core/empty.json": 0,
    }
    print_report(counts)
    captured = capsys.readouterr()
    assert "1,000" in captured.out
    assert "(not built)" in captured.out
    assert "(error)" in captured.out


# ---------------------------------------------------------------------------
# frequency_corpus — surface form collection
# ---------------------------------------------------------------------------

def test_collect_surface_forms_basic() -> None:
    from build.transform.frequency_corpus import _collect_surface_forms
    words_data = {"words": [
        {
            "id": "100",
            "kanji": [{"text": "漢字"}],
            "kana": [{"text": "かんじ"}],
        },
        {
            "id": "200",
            "kanji": [],
            "kana": [{"text": "ああ"}],  # too short (< 3 chars)
        },
        {
            "id": "300",
            "kanji": [],
            "kana": [{"text": "ありがとう"}],  # 5 chars, included
        },
    ]}
    forms = _collect_surface_forms(words_data)
    assert "漢字" in forms  # 2-char kanji
    assert "ああ" not in forms  # too short kana
    assert "ありがとう" in forms  # 5-char kana


def test_collect_surface_forms_single_kanji_excluded() -> None:
    from build.transform.frequency_corpus import _collect_surface_forms
    words_data = {"words": [
        {"id": "100", "kanji": [{"text": "食"}], "kana": [{"text": "しょく"}]},
    ]}
    forms = _collect_surface_forms(words_data)
    assert "食" not in forms  # single kanji excluded
    assert "しょく" in forms   # 3+ char kana included


# ---------------------------------------------------------------------------
# check_upstream — version extraction
# ---------------------------------------------------------------------------

def test_extract_version_from_url() -> None:
    from build.check_upstream import _extract_version_from_url
    url = "https://github.com/foo/bar/releases/download/3.6.2%2B20260406/file.json"
    result = _extract_version_from_url(url, "3.")
    assert "3." in result


# ---------------------------------------------------------------------------
# export_sqlite — schema creation
# ---------------------------------------------------------------------------

def test_sqlite_schema_creation(tmp_path: Path) -> None:
    import sqlite3
    from build.export_sqlite import _create_schema
    db_path = tmp_path / "test.sqlite"
    conn = sqlite3.connect(str(db_path))
    _create_schema(conn)
    # Verify tables exist
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = {row[0] for row in cursor.fetchall()}
    assert "words" in tables
    assert "kanji" in tables
    assert "sentences" in tables
    assert "grammar" in tables
    assert "pitch_accent" in tables
    assert "furigana" in tables
    assert "kanji_to_words" in tables
    conn.close()
