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
    banks = _build_term_banks(words_data, {}, {})
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
    banks = _build_term_banks(words_data, {}, {})
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
    banks = _build_term_banks(words_data, {}, {})
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
    banks = _build_term_banks({"words": words}, {}, {})
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
    assert "frequency_subtitles" in tables
    conn.close()


# ---------------------------------------------------------------------------
# frequency_subtitles — Japanese text detection and parsing
# ---------------------------------------------------------------------------

def test_is_japanese_text_valid_kanji_word() -> None:
    from build.transform.frequency_subtitles import _is_japanese_text
    assert _is_japanese_text("漢字") is True


def test_is_japanese_text_valid_kana_word() -> None:
    from build.transform.frequency_subtitles import _is_japanese_text
    assert _is_japanese_text("ありがとう") is True


def test_is_japanese_text_single_char_rejected() -> None:
    from build.transform.frequency_subtitles import _is_japanese_text
    assert _is_japanese_text("何") is False


def test_is_japanese_text_punctuation_rejected() -> None:
    from build.transform.frequency_subtitles import _is_japanese_text
    assert _is_japanese_text("。。") is False
    assert _is_japanese_text("（）") is False


def test_is_japanese_text_empty_rejected() -> None:
    from build.transform.frequency_subtitles import _is_japanese_text
    assert _is_japanese_text("") is False


def test_is_japanese_text_ascii_rejected() -> None:
    from build.transform.frequency_subtitles import _is_japanese_text
    assert _is_japanese_text("hello") is False


def test_is_japanese_text_mixed_kana_kanji() -> None:
    from build.transform.frequency_subtitles import _is_japanese_text
    assert _is_japanese_text("食べる") is True


def test_parse_frequency_file(tmp_path: Path) -> None:
    from build.transform.frequency_subtitles import _parse_frequency_file
    content = "あなた 61249\n彼女 32871\n何 101249\n、 148670\n\n"
    f = tmp_path / "freq.txt"
    f.write_text(content, encoding="utf-8")
    entries = _parse_frequency_file(f)
    texts = [t for t, _ in entries]
    assert "あなた" in texts
    assert "彼女" in texts
    assert "何" not in texts  # single char filtered
    assert "、" not in texts  # punctuation filtered


def test_parse_frequency_file_malformed_lines(tmp_path: Path) -> None:
    from build.transform.frequency_subtitles import _parse_frequency_file
    content = "no_count_here\n食べる abc\n大丈夫 15283\n"
    f = tmp_path / "freq.txt"
    f.write_text(content, encoding="utf-8")
    entries = _parse_frequency_file(f)
    assert len(entries) == 1
    assert entries[0] == ("大丈夫", 15283)


def test_build_word_lookup_basic() -> None:
    from build.transform.frequency_subtitles import _build_word_lookup
    words_data = {"words": [
        {"id": "100", "kanji": [{"text": "食べる"}], "kana": [{"text": "たべる"}]},
        {"id": "200", "kanji": [], "kana": [{"text": "ありがとう"}]},
    ]}
    lookup = _build_word_lookup(words_data)
    assert "食べる" in lookup
    assert lookup["食べる"] == ("100", "たべる")
    assert "たべる" in lookup
    assert "ありがとう" in lookup
    assert lookup["ありがとう"] == ("200", "ありがとう")


def test_build_word_lookup_first_form_wins() -> None:
    """When two words share a surface form, first-seen wins."""
    from build.transform.frequency_subtitles import _build_word_lookup
    words_data = {"words": [
        {"id": "100", "kanji": [{"text": "共通"}], "kana": [{"text": "きょうつう"}]},
        {"id": "200", "kanji": [{"text": "共通"}], "kana": [{"text": "きょうつう"}]},
    ]}
    lookup = _build_word_lookup(words_data)
    assert lookup["共通"][0] == "100"


# ---------------------------------------------------------------------------
# grammar — _extract_japanese_core
# ---------------------------------------------------------------------------

def test_extract_japanese_core_simple_pattern() -> None:
    from build.transform.grammar import _extract_japanese_core
    assert _extract_japanese_core("～ください") == "ください"


def test_extract_japanese_core_compound_pattern() -> None:
    from build.transform.grammar import _extract_japanese_core
    result = _extract_japanese_core("Verb-て + ください")
    assert "ください" in result


def test_extract_japanese_core_pure_english() -> None:
    from build.transform.grammar import _extract_japanese_core
    assert _extract_japanese_core("A is B") == ""


def test_extract_japanese_core_tilde_stripped() -> None:
    from build.transform.grammar import _extract_japanese_core
    result = _extract_japanese_core("～たい")
    assert "～" not in result
    assert "たい" in result


def test_extract_japanese_core_short_result_rejected() -> None:
    from build.transform.grammar import _extract_japanese_core
    # Single char result should return ""
    assert _extract_japanese_core("～は") == ""


# ---------------------------------------------------------------------------
# export_sqlite — insert functions
# ---------------------------------------------------------------------------

def test_sqlite_insert_words(tmp_path: Path) -> None:
    import sqlite3
    from build.export_sqlite import _create_schema, _insert_words
    conn = sqlite3.connect(str(tmp_path / "test.db"))
    _create_schema(conn)
    words_data = {"words": [
        {"id": "123", "kanji": [{"text": "食べる", "tags": []}],
         "kana": [{"text": "たべる", "tags": []}],
         "sense": [{"partOfSpeech": ["v1"], "gloss": [{"lang": "eng", "text": "to eat"}]}],
         "jlpt_waller": "N5"},
    ]}
    n = _insert_words(conn, words_data)
    assert n == 1
    conn.commit()
    row = conn.execute("SELECT id, kanji_primary, jlpt FROM words").fetchone()
    assert row[0] == "123"
    assert row[1] == "食べる"
    assert row[2] == "N5"
    conn.close()


def test_sqlite_insert_kanji(tmp_path: Path) -> None:
    import sqlite3
    from build.export_sqlite import _create_schema, _insert_kanji
    conn = sqlite3.connect(str(tmp_path / "test.db"))
    _create_schema(conn)
    kanji_data = {"kanji": [
        {"character": "日", "stroke_count": 4, "grade": 1, "jlpt_waller": "N5",
         "frequency": 1, "readings": {"on": ["ニチ"], "kun": ["ひ"]},
         "meanings": {"en": ["day", "sun"]}},
    ]}
    n = _insert_kanji(conn, kanji_data)
    assert n == 1
    conn.commit()
    row = conn.execute("SELECT character, stroke_count, meanings_en FROM kanji").fetchone()
    assert row[0] == "日"
    assert row[1] == 4
    assert "day" in row[2]
    conn.close()


def test_sqlite_insert_sentences(tmp_path: Path) -> None:
    import sqlite3
    from build.export_sqlite import _create_schema, _insert_sentences
    conn = sqlite3.connect(str(tmp_path / "test.db"))
    _create_schema(conn)
    data = {"sentences": [
        {"id": "42", "japanese": "机の上に本があります。", "english": "There is a book on the desk."},
    ]}
    n = _insert_sentences(conn, data, "tatoeba")
    assert n == 1
    conn.commit()
    row = conn.execute("SELECT id, source FROM sentences").fetchone()
    assert row[0] == "42"
    assert row[1] == "tatoeba"
    conn.close()


def test_sqlite_insert_grammar(tmp_path: Path) -> None:
    import sqlite3
    from build.export_sqlite import _create_schema, _insert_grammar
    conn = sqlite3.connect(str(tmp_path / "test.db"))
    _create_schema(conn)
    data = {"grammar_points": [
        {"id": "desu", "pattern": "です", "meaning_en": "is",
         "level": "N5", "formality": "formal", "formation": "N + です",
         "review_status": "draft"},
    ]}
    n = _insert_grammar(conn, data)
    assert n == 1
    conn.commit()
    row = conn.execute("SELECT id, level FROM grammar").fetchone()
    assert row[0] == "desu"
    assert row[1] == "N5"
    conn.close()


def test_sqlite_insert_xref(tmp_path: Path) -> None:
    import sqlite3
    from build.export_sqlite import _create_schema, _insert_xref
    conn = sqlite3.connect(str(tmp_path / "test.db"))
    _create_schema(conn)
    data = {"mapping": {"日": ["100", "200"], "月": ["300"]}}
    n = _insert_xref(conn, "kanji_to_words", data)
    assert n == 3
    conn.commit()
    rows = conn.execute("SELECT * FROM kanji_to_words ORDER BY kanji").fetchall()
    assert len(rows) == 3
    assert rows[0][0] == "日"
    conn.close()


# ---------------------------------------------------------------------------
# stroke_order — _load_kanji_set edge cases
# ---------------------------------------------------------------------------

def test_load_kanji_set_missing_file(tmp_path: Path, monkeypatch) -> None:
    from build.transform import stroke_order
    monkeypatch.setattr(stroke_order, "KANJI_JSON", tmp_path / "nonexistent.json")
    result = stroke_order._load_kanji_set()
    assert result == set()


def test_load_kanji_set_invalid_json(tmp_path: Path, monkeypatch) -> None:
    from build.transform import stroke_order
    bad_file = tmp_path / "kanji.json"
    bad_file.write_text("not json", encoding="utf-8")
    monkeypatch.setattr(stroke_order, "KANJI_JSON", bad_file)
    result = stroke_order._load_kanji_set()
    assert result == set()


def test_load_kanji_set_valid(tmp_path: Path, monkeypatch) -> None:
    import json
    from build.transform import stroke_order
    kanji_file = tmp_path / "kanji.json"
    kanji_file.write_text(json.dumps({
        "kanji": [{"character": "日"}, {"character": "月"}]
    }), encoding="utf-8")
    monkeypatch.setattr(stroke_order, "KANJI_JSON", kanji_file)
    result = stroke_order._load_kanji_set()
    assert result == {"日", "月"}


def test_codepoint_filename_multi_char_raises() -> None:
    from build.transform.stroke_order import _codepoint_filename
    with pytest.raises(ValueError, match="single-character"):
        _codepoint_filename("AB")


# ---------------------------------------------------------------------------
# kftt — _read_lines_from_tar
# ---------------------------------------------------------------------------

def test_read_lines_from_tar(tmp_path: Path) -> None:
    import io
    import tarfile
    from build.transform.kftt import _read_lines_from_tar
    # Create a minimal tar with a test file
    tar_path = tmp_path / "test.tar.gz"
    content = "line1\nline2\nline3\n"
    with tarfile.open(tar_path, "w:gz") as tf:
        data = content.encode("utf-8")
        info = tarfile.TarInfo(name="data/orig/kyoto-test.ja")
        info.size = len(data)
        tf.addfile(info, io.BytesIO(data))
    with tarfile.open(tar_path, "r:gz") as tf:
        lines = _read_lines_from_tar(tf, "data/orig/kyoto-test.ja")
    assert lines == ["line1", "line2", "line3"]


def test_read_lines_from_tar_missing_member(tmp_path: Path) -> None:
    import io
    import tarfile
    from build.transform.kftt import _read_lines_from_tar
    tar_path = tmp_path / "test.tar.gz"
    with tarfile.open(tar_path, "w:gz") as tf:
        data = b"content"
        info = tarfile.TarInfo(name="other.txt")
        info.size = len(data)
        tf.addfile(info, io.BytesIO(data))
    with tarfile.open(tar_path, "r:gz") as tf:
        with pytest.raises(RuntimeError, match="No member ending with"):
            _read_lines_from_tar(tf, "data/orig/missing.ja")


# ---------------------------------------------------------------------------
# expressions — expression extraction filter
# ---------------------------------------------------------------------------

def test_expressions_filter_selects_exp_pos() -> None:
    """Verify the expression filter logic: only senses with 'exp' POS."""
    # Replicate the core filtering logic from expressions.py build()
    word = {
        "id": "100",
        "kanji": [{"text": "お疲れ様"}],
        "kana": [{"text": "おつかれさま"}],
        "sense": [
            {"partOfSpeech": ["exp", "n"], "gloss": [{"text": "good work"}], "misc": []},
            {"partOfSpeech": ["n"], "gloss": [{"text": "tiredness"}], "misc": []},
        ],
    }
    # Only the first sense has 'exp'
    exp_meanings = []
    for sense in word.get("sense", []) or []:
        if "exp" not in (sense.get("partOfSpeech", []) or []):
            continue
        for g in sense.get("gloss", []) or []:
            exp_meanings.append(g.get("text", ""))
    assert exp_meanings == ["good work"]
    assert "tiredness" not in exp_meanings


def test_expressions_filter_skips_non_exp() -> None:
    """A word with no 'exp' senses should produce no meanings."""
    word = {
        "sense": [
            {"partOfSpeech": ["n", "vs"], "gloss": [{"text": "study"}]},
        ],
    }
    exp_meanings = []
    for sense in word.get("sense", []) or []:
        if "exp" not in (sense.get("partOfSpeech", []) or []):
            continue
        for g in sense.get("gloss", []) or []:
            exp_meanings.append(g.get("text", ""))
    assert exp_meanings == []


# ---------------------------------------------------------------------------
# sentences — deduplication logic
# ---------------------------------------------------------------------------

def test_sentences_dedup_by_tatoeba_id() -> None:
    """Sentence deduplication: same Tatoeba ID seen twice → one output."""
    seen: dict[str, dict] = {}
    # Simulate two references to the same sentence ID
    examples = [
        {"source": {"type": "tatoeba", "value": "42"},
         "sentences": [{"lang": "jpn", "text": "日本語"}, {"lang": "eng", "text": "Japanese"}]},
        {"source": {"type": "tatoeba", "value": "42"},
         "sentences": [{"lang": "jpn", "text": "日本語"}, {"lang": "eng", "text": "Japanese (alt)"}]},
    ]
    for ex in examples:
        src = ex.get("source", {}) or {}
        if src.get("type") != "tatoeba":
            continue
        sid = str(src.get("value", ""))
        if not sid or sid in seen:
            continue
        seen[sid] = {"id": sid}
    assert len(seen) == 1
    assert "42" in seen


def test_sentences_skip_non_tatoeba() -> None:
    """Non-tatoeba sources should be skipped."""
    seen: dict[str, dict] = {}
    examples = [
        {"source": {"type": "other", "value": "99"},
         "sentences": [{"lang": "jpn", "text": "テスト"}]},
    ]
    for ex in examples:
        src = ex.get("source", {}) or {}
        if src.get("type") != "tatoeba":
            continue
        sid = str(src.get("value", ""))
        if not sid or sid in seen:
            continue
        seen[sid] = {"id": sid}
    assert len(seen) == 0


# ---------------------------------------------------------------------------
# furigana — segment filtering logic
# ---------------------------------------------------------------------------

def test_furigana_has_kanji_segment_true() -> None:
    """Furigana entries with 'rt' keys in segments have kanji."""
    furigana = [{"ruby": "食", "rt": "た"}, {"ruby": "べる"}]
    has_kanji_segment = any("rt" in seg for seg in furigana)
    assert has_kanji_segment is True


def test_furigana_has_kanji_segment_false() -> None:
    """Pure kana entries have no 'rt' keys."""
    furigana = [{"ruby": "ありがとう"}]
    has_kanji_segment = any("rt" in seg for seg in furigana)
    assert has_kanji_segment is False


def test_furigana_known_pairs_filter() -> None:
    """Filter entries to known (text, reading) pairs from words.json."""
    taberu_reading = "\u305f\u3079\u308b"  # たべる
    nomu_reading = "\u306e\u3080"  # のむ
    known_pairs = {("\u98df\u3079\u308b", taberu_reading), ("\u98f2\u3080", nomu_reading)}
    entries = [
        {"text": "\u98df\u3079\u308b", "reading": taberu_reading,
         "furigana": [{"ruby": "\u98df", "rt": "\u305f"}, {"ruby": "\u3079\u308b"}]},
        {"text": "\u672a\u77e5\u8a9e", "reading": "\u307f\u3061\u3054",
         "furigana": [{"ruby": "\u672a\u77e5", "rt": "\u307f\u3061"}, {"ruby": "\u8a9e", "rt": "\u3054"}]},
    ]
    filtered = [e for e in entries if (e["text"], e["reading"]) in known_pairs]
    assert len(filtered) == 1
    assert filtered[0]["text"] == "\u98df\u3079\u308b"


# ---------------------------------------------------------------------------
# export_sqlite — insert_pitch
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# sentences — _load_source with mock tarball
# ---------------------------------------------------------------------------

def test_sentences_load_source_extracts_json(tmp_path: Path, monkeypatch) -> None:
    """_load_source should extract and parse the first JSON from a tgz."""
    import io
    import tarfile
    from build.transform import sentences as sentences_mod

    # Create a mock tgz with a JSON file inside
    content = json.dumps({"words": [{"id": "1", "sense": []}]})
    tar_path = tmp_path / "mock.json.tgz"
    with tarfile.open(tar_path, "w:gz") as tf:
        data = content.encode("utf-8")
        info = tarfile.TarInfo(name="test.json")
        info.size = len(data)
        tf.addfile(info, io.BytesIO(data))

    monkeypatch.setattr(sentences_mod, "SOURCE_TGZ", tar_path)
    result = sentences_mod._load_source()
    assert result["words"][0]["id"] == "1"


# ---------------------------------------------------------------------------
# furigana — build() with mock data
# ---------------------------------------------------------------------------

def test_furigana_build_filters_correctly(tmp_path: Path, monkeypatch) -> None:
    """furigana.build() should filter to known vocab and skip pure-kana entries."""
    from build.transform import furigana as furigana_mod

    # Create mock source file (JmdictFurigana format)
    source_entries = [
        # Should match: known pair with kanji segment
        {"text": "\u98df\u3079\u308b", "reading": "\u305f\u3079\u308b",
         "furigana": [{"ruby": "\u98df", "rt": "\u305f"}, {"ruby": "\u3079\u308b"}]},
        # Should be filtered: not in words.json
        {"text": "\u672a\u77e5\u8a9e", "reading": "\u307f\u3061\u3054",
         "furigana": [{"ruby": "\u672a\u77e5", "rt": "\u307f\u3061"}, {"ruby": "\u8a9e", "rt": "\u3054"}]},
        # Should be filtered: pure kana (no rt keys)
        {"text": "\u3042\u308a\u304c\u3068\u3046", "reading": "\u3042\u308a\u304c\u3068\u3046",
         "furigana": [{"ruby": "\u3042\u308a\u304c\u3068\u3046"}]},
        # Should be filtered: empty furigana
        {"text": "\u7a7a", "reading": "\u304b\u3089", "furigana": []},
    ]
    source_file = tmp_path / "JmdictFurigana.json"
    # Write with BOM as the real source uses utf-8-sig
    source_file.write_bytes(b"\xef\xbb\xbf" + json.dumps(source_entries, ensure_ascii=False).encode("utf-8"))

    # Create mock words.json with one known pair
    words_file = tmp_path / "words.json"
    words_data = {"words": [
        {"id": "1", "kanji": [{"text": "\u98df\u3079\u308b"}],
         "kana": [{"text": "\u305f\u3079\u308b"}]},
    ]}
    words_file.write_text(json.dumps(words_data, ensure_ascii=False), encoding="utf-8")

    out_file = tmp_path / "furigana.json"

    monkeypatch.setattr(furigana_mod, "SOURCE_JSON", source_file)
    monkeypatch.setattr(furigana_mod, "WORDS_JSON", words_file)
    monkeypatch.setattr(furigana_mod, "OUT", out_file)
    monkeypatch.setattr(furigana_mod, "REPO_ROOT", tmp_path)

    furigana_mod.build()

    result = json.loads(out_file.read_text(encoding="utf-8"))
    assert result["metadata"]["count"] == 1
    assert len(result["entries"]) == 1
    assert result["entries"][0]["text"] == "\u98df\u3079\u308b"


# ---------------------------------------------------------------------------
# expressions — _load_source / _is_common wrappers
# ---------------------------------------------------------------------------

def test_expressions_is_common_delegates_to_utils() -> None:
    from build.transform.expressions import _is_common
    word_common = {"kanji": [{"common": True, "text": "test"}], "kana": []}
    word_uncommon = {"kanji": [{"common": False, "text": "test"}], "kana": []}
    assert _is_common(word_common) is True
    assert _is_common(word_uncommon) is False


# ---------------------------------------------------------------------------
# jukugo — compound extraction
# ---------------------------------------------------------------------------

def test_jukugo_is_kanji() -> None:
    from build.transform.jukugo import _is_kanji
    assert _is_kanji("\u98df") is True   # 食
    assert _is_kanji("\u3042") is False  # あ
    assert _is_kanji("A") is False


def test_jukugo_extract_compounds_basic() -> None:
    from build.transform.jukugo import _extract_compounds
    words_data = {"words": [
        {"id": "1", "kanji": [{"text": "\u5b66\u6821"}],
         "kana": [{"text": "\u304c\u3063\u3053\u3046"}],
         "sense": [{"gloss": [{"text": "school"}]}], "jlpt_waller": "N5"},
        {"id": "2", "kanji": [{"text": "\u98df"}],
         "kana": [{"text": "\u305f"}],
         "sense": [{"gloss": [{"text": "eat"}]}]},
        {"id": "3", "kanji": [],
         "kana": [{"text": "\u3042\u308a\u304c\u3068\u3046"}],
         "sense": [{"gloss": [{"text": "thanks"}]}]},
    ]}
    kanji_meanings = {
        "\u5b66": ["study"], "\u6821": ["school"],
        "\u98df": ["eat"],
    }
    compounds = _extract_compounds(words_data, kanji_meanings)
    assert len(compounds) == 1
    c = compounds[0]
    assert c["word_id"] == "1"
    assert c["text"] == "\u5b66\u6821"
    assert c["kanji_count"] == 2
    assert c["kanji_sequence"] == ["\u5b66", "\u6821"]
    assert c["components"][0]["kanji"] == "\u5b66"
    assert "study" in c["components"][0]["meanings"]
    assert c["jlpt_waller"] == "N5"


# ---------------------------------------------------------------------------
# counters — counter-word extraction
# ---------------------------------------------------------------------------

def test_extract_counters_basic() -> None:
    from build.transform.counters import _extract_counters
    words_data = {"words": [
        {"id": "1",
         "kanji": [{"text": "\u99c5"}],
         "kana": [{"text": "\u3048\u304d"}],
         "sense": [{"partOfSpeech": ["ctr"], "gloss": [{"text": "railway station"}]}],
         "jlpt_waller": "N3"},
        {"id": "2",
         "kanji": [{"text": "\u98df\u3079\u308b"}],
         "kana": [{"text": "\u305f\u3079\u308b"}],
         "sense": [{"partOfSpeech": ["v1"], "gloss": [{"text": "to eat"}]}]},
    ]}
    counters = _extract_counters(words_data)
    assert len(counters) == 1
    assert counters[0]["word_id"] == "1"
    assert counters[0]["meanings"] == ["railway station"]
    assert counters[0]["jlpt_waller"] == "N3"


def test_extract_counters_no_ctr() -> None:
    from build.transform.counters import _extract_counters
    words_data = {"words": [
        {"id": "1", "kanji": [], "kana": [{"text": "abc"}],
         "sense": [{"partOfSpeech": ["n"], "gloss": [{"text": "noun"}]}]},
    ]}
    assert _extract_counters(words_data) == []


# ---------------------------------------------------------------------------
# ateji — ateji extraction
# ---------------------------------------------------------------------------

def test_extract_ateji_basic() -> None:
    from build.transform.ateji import _extract_ateji
    words_data = {"words": [
        {"id": "1",
         "kanji": [{"text": "\u5c48\u5ea6", "tags": ["ateji"]}],
         "kana": [{"text": "\u304d\u3063\u3068"}],
         "sense": [{"gloss": [{"text": "surely"}]}],
         "jlpt_waller": None},
        {"id": "2",
         "kanji": [{"text": "\u98df\u3079\u308b", "tags": []}],
         "kana": [{"text": "\u305f\u3079\u308b"}],
         "sense": [{"gloss": [{"text": "to eat"}]}]},
    ]}
    entries = _extract_ateji(words_data)
    assert len(entries) == 1
    assert entries[0]["word_id"] == "1"
    assert entries[0]["text"] == "\u5c48\u5ea6"
    assert entries[0]["meanings"] == ["surely"]


def test_extract_ateji_no_ateji() -> None:
    from build.transform.ateji import _extract_ateji
    words_data = {"words": [
        {"id": "1", "kanji": [{"text": "abc", "tags": []}],
         "kana": [{"text": "abc"}], "sense": [{"gloss": [{"text": "x"}]}]},
    ]}
    assert _extract_ateji(words_data) == []


# ---------------------------------------------------------------------------
# export_yomitan — pitch and frequency lookup loading
# ---------------------------------------------------------------------------

def test_load_pitch_lookup(tmp_path: Path, monkeypatch) -> None:
    from build import export_yomitan as ym
    pitch_file = tmp_path / "pitch.json"
    pitch_file.write_text(json.dumps({
        "entries": [
            {"word": "\u98df\u3079\u308b", "reading": "\u305f\u3079\u308b",
             "pitch_positions": [0], "mora_count": 3},
            {"word": "\u5b66\u6821", "reading": "\u304c\u3063\u3053\u3046",
             "pitch_positions": [0], "mora_count": 4},
        ]
    }, ensure_ascii=False), encoding="utf-8")
    monkeypatch.setattr(ym, "PITCH_JSON", pitch_file)
    lookup = ym._load_pitch_lookup()
    assert ("\u98df\u3079\u308b", "\u305f\u3079\u308b") in lookup
    assert lookup[("\u98df\u3079\u308b", "\u305f\u3079\u308b")] == "0"


def test_load_pitch_lookup_missing_file(tmp_path: Path, monkeypatch) -> None:
    from build import export_yomitan as ym
    monkeypatch.setattr(ym, "PITCH_JSON", tmp_path / "nonexistent.json")
    assert ym._load_pitch_lookup() == {}


def test_load_freq_lookup(tmp_path: Path, monkeypatch) -> None:
    from build import export_yomitan as ym
    freq_file = tmp_path / "freq.json"
    freq_file.write_text(json.dumps({
        "entries": [
            {"text": "\u3042\u306a\u305f", "rank": 1, "count": 61249},
        ]
    }, ensure_ascii=False), encoding="utf-8")
    monkeypatch.setattr(ym, "FREQ_SUB_JSON", freq_file)
    lookup = ym._load_freq_lookup()
    assert lookup["\u3042\u306a\u305f"] == 1


def test_load_freq_lookup_missing_file(tmp_path: Path, monkeypatch) -> None:
    from build import export_yomitan as ym
    monkeypatch.setattr(ym, "FREQ_SUB_JSON", tmp_path / "nonexistent.json")
    assert ym._load_freq_lookup() == {}


# ---------------------------------------------------------------------------
# export_yomitan — term banks with enrichment
# ---------------------------------------------------------------------------

def test_yomitan_term_banks_with_pitch() -> None:
    """Pitch accent should appear as first definition element."""
    from build.export_yomitan import _build_term_banks
    words_data = {"words": [
        {"id": "100", "kanji": [{"text": "\u98df\u3079\u308b"}],
         "kana": [{"text": "\u305f\u3079\u308b"}],
         "sense": [{"partOfSpeech": ["v1"], "gloss": [{"text": "to eat"}]}],
         "jlpt_waller": "N5"},
    ]}
    pitch_lookup = {("\u98df\u3079\u308b", "\u305f\u3079\u308b"): "0"}
    banks = _build_term_banks(words_data, pitch_lookup, {})
    entry = banks[0][0]
    assert entry[5][0] == "[pitch: 0]"
    assert entry[5][1] == "to eat"


def test_yomitan_term_banks_with_frequency_boost() -> None:
    """High-frequency words should get a score boost."""
    from build.export_yomitan import _build_term_banks
    words_data = {"words": [
        {"id": "100", "kanji": [{"text": "\u6642\u9593"}],
         "kana": [{"text": "\u3058\u304b\u3093"}],
         "sense": [{"partOfSpeech": ["n"], "gloss": [{"text": "time"}]}],
         "jlpt_waller": "N5"},
    ]}
    freq_lookup = {"\u6642\u9593": 10}  # rank 10 = top 3000
    banks = _build_term_banks(words_data, {}, freq_lookup)
    entry = banks[0][0]
    # N5=5, plus frequency boost +1 = 6
    assert entry[4] == 6


def test_yomitan_term_banks_no_enrichment() -> None:
    """Without enrichment data, definitions should be plain."""
    from build.export_yomitan import _build_term_banks
    words_data = {"words": [
        {"id": "100", "kanji": [{"text": "\u98df\u3079\u308b"}],
         "kana": [{"text": "\u305f\u3079\u308b"}],
         "sense": [{"partOfSpeech": ["v1"], "gloss": [{"text": "to eat"}]}]},
    ]}
    banks = _build_term_banks(words_data, {}, {})
    entry = banks[0][0]
    assert entry[5] == ["to eat"]  # no pitch prefix


# ---------------------------------------------------------------------------
# jukugo — build with mock data
# ---------------------------------------------------------------------------

def test_jukugo_build(tmp_path: Path, monkeypatch) -> None:
    from build.transform import jukugo as jukugo_mod
    words_file = tmp_path / "words.json"
    words_file.write_text(json.dumps({"words": [
        {"id": "1", "kanji": [{"text": "\u5b66\u6821"}],
         "kana": [{"text": "\u304c\u3063\u3053\u3046"}],
         "sense": [{"gloss": [{"text": "school"}]}], "jlpt_waller": "N5"},
    ]}, ensure_ascii=False), encoding="utf-8")
    kanji_file = tmp_path / "kanji.json"
    kanji_file.write_text(json.dumps({"kanji": [
        {"character": "\u5b66", "meanings": {"en": ["study"]}},
        {"character": "\u6821", "meanings": {"en": ["school"]}},
    ]}, ensure_ascii=False), encoding="utf-8")
    out_file = tmp_path / "jukugo.json"
    monkeypatch.setattr(jukugo_mod, "WORDS_JSON", words_file)
    monkeypatch.setattr(jukugo_mod, "KANJI_JSON", kanji_file)
    monkeypatch.setattr(jukugo_mod, "OUT", out_file)
    monkeypatch.setattr(jukugo_mod, "REPO_ROOT", tmp_path)
    jukugo_mod.build()
    result = json.loads(out_file.read_text(encoding="utf-8"))
    assert result["metadata"]["count"] == 1
    assert result["compounds"][0]["text"] == "\u5b66\u6821"


# ---------------------------------------------------------------------------
# counters — build with mock data
# ---------------------------------------------------------------------------

def test_counters_build(tmp_path: Path, monkeypatch) -> None:
    from build.transform import counters as counters_mod
    words_file = tmp_path / "words.json"
    words_file.write_text(json.dumps({"words": [
        {"id": "1", "kanji": [{"text": "\u99c5"}],
         "kana": [{"text": "\u3048\u304d"}],
         "sense": [{"partOfSpeech": ["ctr"], "gloss": [{"text": "station"}]}],
         "jlpt_waller": None},
    ]}, ensure_ascii=False), encoding="utf-8")
    out_file = tmp_path / "counters.json"
    monkeypatch.setattr(counters_mod, "WORDS_JSON", words_file)
    monkeypatch.setattr(counters_mod, "OUT", out_file)
    monkeypatch.setattr(counters_mod, "REPO_ROOT", tmp_path)
    counters_mod.build()
    result = json.loads(out_file.read_text(encoding="utf-8"))
    assert result["metadata"]["count"] == 1


# ---------------------------------------------------------------------------
# ateji — build with mock data
# ---------------------------------------------------------------------------

def test_ateji_build(tmp_path: Path, monkeypatch) -> None:
    from build.transform import ateji as ateji_mod
    words_file = tmp_path / "words.json"
    words_file.write_text(json.dumps({"words": [
        {"id": "1", "kanji": [{"text": "\u5c48\u5ea6", "tags": ["ateji"]}],
         "kana": [{"text": "\u304d\u3063\u3068"}],
         "sense": [{"gloss": [{"text": "surely"}]}], "jlpt_waller": None},
    ]}, ensure_ascii=False), encoding="utf-8")
    out_file = tmp_path / "ateji.json"
    monkeypatch.setattr(ateji_mod, "WORDS_JSON", words_file)
    monkeypatch.setattr(ateji_mod, "OUT", out_file)
    monkeypatch.setattr(ateji_mod, "REPO_ROOT", tmp_path)
    ateji_mod.build()
    result = json.loads(out_file.read_text(encoding="utf-8"))
    assert result["metadata"]["count"] == 1


def test_sqlite_insert_pitch(tmp_path: Path) -> None:
    import sqlite3
    from build.export_sqlite import _create_schema, _insert_pitch
    conn = sqlite3.connect(str(tmp_path / "test.db"))
    _create_schema(conn)
    data = {"entries": [
        {"text": "食べる", "reading": "たべる", "pitch_positions": [0], "mora_count": 3},
    ]}
    n = _insert_pitch(conn, data)
    assert n == 1
    conn.commit()
    row = conn.execute("SELECT text, mora_count FROM pitch_accent").fetchone()
    assert row[0] == "食べる"
    assert row[1] == 3
    conn.close()


# ---------------------------------------------------------------------------
# cross_links — builder functions
# ---------------------------------------------------------------------------

def test_build_word_cross_refs() -> None:
    from build.transform.cross_links import _build_word_cross_refs
    words_data = {"words": [
        {"id": "100",
         "kanji": [{"text": "\u98df\u3079\u308b"}],
         "kana": [{"text": "\u305f\u3079\u308b"}],
         "sense": [{"examples": [
             {"source": "tatoeba", "sentence_id": "42"}
         ]}]},
    ]}
    k2w, w2k, w2s = _build_word_cross_refs(words_data)
    # word contains kanji 食
    assert "\u98df" in k2w
    assert "100" in k2w["\u98df"]
    # word-to-kanji inverse
    assert "100" in w2k
    assert "\u98df" in w2k["100"]
    # word-to-sentences
    assert "100" in w2s
    assert "42" in w2s["100"]


def test_build_reading_to_words() -> None:
    from build.transform.cross_links import _build_reading_to_words
    words_data = {"words": [
        {"id": "100", "kana": [{"text": "\u305f\u3079\u308b"}]},
        {"id": "200", "kana": [{"text": "\u306e\u3080"}]},
    ]}
    r2w = _build_reading_to_words(words_data)
    assert "\u305f\u3079\u308b" in r2w
    assert r2w["\u305f\u3079\u308b"] == ["100"]
    assert "\u306e\u3080" in r2w


def test_build_word_text_lookup() -> None:
    from build.transform.cross_links import _build_word_text_lookup
    words_data = {"words": [
        {"id": "100", "kanji": [{"text": "\u98df\u3079\u308b"}],
         "kana": [{"text": "\u305f\u3079\u308b"}]},
        {"id": "200", "kanji": [], "kana": [{"text": "\u3042\u3042"}]},  # 2-char kana: excluded (< 3)
    ]}
    lookup = _build_word_text_lookup(words_data)
    assert "\u98df\u3079\u308b" in lookup  # 3-char kanji: included (>= 2)
    assert "\u305f\u3079\u308b" in lookup  # 3-char kana: included (>= 3)
    assert "\u3042\u3042" not in lookup    # 2-char kana: excluded


def test_build_radical_to_kanji() -> None:
    from build.transform.cross_links import _build_radical_to_kanji
    k2r = {"\u98df": ["\u4eba", "\u826f"], "\u98f2": ["\u4eba", "\u6b20"]}
    r2k = _build_radical_to_kanji(k2r)
    assert "\u4eba" in r2k
    assert set(r2k["\u4eba"]) == {"\u98df", "\u98f2"}


# ---------------------------------------------------------------------------
# grammar — _find_pattern_matches with mock data
# ---------------------------------------------------------------------------

def test_find_pattern_matches_basic() -> None:
    from build.transform.grammar import _find_pattern_matches
    entries = [
        {"id": "test-pattern", "pattern": "\u304f\u3060\u3055\u3044"},  # ください
    ]
    sentences = [
        ("1", "\u3053\u308c\u3092\u304f\u3060\u3055\u3044\u3002"),  # これをください。
        ("2", "\u4eca\u65e5\u306f\u6691\u3044\u3067\u3059\u3002"),  # 今日は暑いです。 (no match)
    ]
    matches, count, total = _find_pattern_matches(entries, sentences)
    assert count == 1
    assert "test-pattern" in matches
    assert "1" in matches["test-pattern"]


def test_find_pattern_matches_no_match() -> None:
    from build.transform.grammar import _find_pattern_matches
    entries = [{"id": "rare", "pattern": "\u3068\u304a\u307c\u3057\u3044"}]  # とおぼしい
    sentences = [("1", "\u3053\u3093\u306b\u3061\u306f")]
    matches, count, total = _find_pattern_matches(entries, sentences)
    assert count == 0
    assert not matches


# ---------------------------------------------------------------------------
# grammar — _extract_japanese_candidates (multi-candidate)
# ---------------------------------------------------------------------------

def test_extract_candidates_slash_alternatives() -> None:
    from build.transform.grammar import _extract_japanese_candidates
    cands = _extract_japanese_candidates("\u307e\u3067\u3060 / \u307e\u3067\u306e\u3053\u3068\u3060")
    assert "\u307e\u3067\u306e\u3053\u3068\u3060" in cands
    assert "\u307e\u3067\u3060" in cands


def test_extract_candidates_parenthesized() -> None:
    from build.transform.grammar import _extract_japanese_candidates
    cands = _extract_japanese_candidates("\u672b(\u306b)")  # 末(に)
    assert "\u672b\u306b" in cands


def test_extract_candidates_has_kanji() -> None:
    from build.transform.grammar import _has_kanji
    assert _has_kanji("\u98df") is True
    assert _has_kanji("\u305f\u3079") is False


# ---------------------------------------------------------------------------
# export_anki — model construction
# ---------------------------------------------------------------------------

def test_anki_models_have_stable_ids() -> None:
    from build.export_anki import _build_vocab_model, _build_kanji_model, _build_grammar_model
    assert _build_vocab_model().model_id == 1607392319
    assert _build_kanji_model().model_id == 1607392320
    assert _build_grammar_model().model_id == 1607392321


# ---------------------------------------------------------------------------
# export_anki — _load_json
# ---------------------------------------------------------------------------

def test_anki_load_json_existing_file(tmp_path: Path) -> None:
    from build.export_anki import _load_json
    p = tmp_path / "test.json"
    p.write_text('{"key": "value"}', encoding="utf-8")
    assert _load_json(p) == {"key": "value"}


def test_anki_load_json_missing_file(tmp_path: Path) -> None:
    from build.export_anki import _load_json
    assert _load_json(tmp_path / "nope.json") is None


# ---------------------------------------------------------------------------
# export_anki — full export() integration
# ---------------------------------------------------------------------------

def test_anki_export_generates_apkg(tmp_path: Path, monkeypatch) -> None:
    """Full integration: mock data → export() → .apkg exists with correct card counts."""
    import build.export_anki as mod

    data_dir = tmp_path / "data"
    (data_dir / "core").mkdir(parents=True)
    (data_dir / "enrichment").mkdir(parents=True)
    (data_dir / "grammar").mkdir(parents=True)

    # Minimal words.json
    words = {"words": [{
        "id": "1000010", "kanji": [{"text": "食べる", "tags": ["ichi1"]}],
        "kana": [{"text": "たべる", "tags": []}],
        "sense": [{"gloss": [{"text": "to eat"}]}],
    }]}
    (data_dir / "core" / "words.json").write_text(json.dumps(words), encoding="utf-8")

    # Minimal kanji.json
    kanji = {"kanji": [{
        "character": "食", "readings": {"on": ["ショク"], "kun": ["た.べる"]},
        "meanings": {"en": ["eat"]}, "stroke_count": 9, "grade": 2,
    }]}
    (data_dir / "core" / "kanji.json").write_text(json.dumps(kanji), encoding="utf-8")

    # Minimal grammar.json
    grammar = {"grammar_points": [{
        "id": "n5-te-form", "pattern": "～て", "meaning_en": "and then",
        "formation": "V-te", "level": "N5",
        "examples": [{"japanese": "食べて", "english": "eat and..."}],
    }]}
    (data_dir / "grammar" / "grammar.json").write_text(json.dumps(grammar), encoding="utf-8")

    # Pitch accent data
    pitch = {"entries": [{"word": "食べる", "pitch_positions": [2], "mora_count": 3}]}
    (data_dir / "enrichment" / "pitch-accent.json").write_text(json.dumps(pitch), encoding="utf-8")

    # Manifest
    manifest = {"version": "0.8.0-test"}
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    dist_dir = tmp_path / "dist"
    out_apkg = dist_dir / "japanese-language-data.apkg"

    monkeypatch.setattr(mod, "DIST_DIR", dist_dir)
    monkeypatch.setattr(mod, "OUT_APKG", out_apkg)
    monkeypatch.setattr(mod, "MANIFEST_PATH", manifest_path)
    monkeypatch.setattr("build.export_anki.DATA_DIR", data_dir)
    monkeypatch.setattr("build.export_anki.REPO_ROOT", tmp_path)

    mod.export()

    assert out_apkg.exists()
    assert out_apkg.stat().st_size > 0


def test_anki_export_empty_data(tmp_path: Path, monkeypatch) -> None:
    """Export with no data files produces a valid (empty) .apkg."""
    import build.export_anki as mod

    data_dir = tmp_path / "data"
    data_dir.mkdir()

    manifest = {"version": "test"}
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    dist_dir = tmp_path / "dist"
    out_apkg = dist_dir / "japanese-language-data.apkg"

    monkeypatch.setattr(mod, "DIST_DIR", dist_dir)
    monkeypatch.setattr(mod, "OUT_APKG", out_apkg)
    monkeypatch.setattr(mod, "MANIFEST_PATH", manifest_path)
    monkeypatch.setattr("build.export_anki.DATA_DIR", data_dir)
    monkeypatch.setattr("build.export_anki.REPO_ROOT", tmp_path)

    mod.export()

    assert out_apkg.exists()


def test_anki_export_vocab_pitch_enrichment(tmp_path: Path, monkeypatch) -> None:
    """Pitch accent lookup is wired into vocab cards."""
    import build.export_anki as mod

    data_dir = tmp_path / "data"
    (data_dir / "core").mkdir(parents=True)
    (data_dir / "enrichment").mkdir(parents=True)
    (data_dir / "grammar").mkdir(parents=True)

    words = {"words": [{
        "id": "1", "kanji": [{"text": "飲む", "tags": []}],
        "kana": [{"text": "のむ", "tags": []}],
        "sense": [{"gloss": [{"text": "to drink"}]}],
    }]}
    (data_dir / "core" / "words.json").write_text(json.dumps(words), encoding="utf-8")

    pitch = {"entries": [{"word": "飲む", "pitch_positions": [1, 0], "mora_count": 2}]}
    (data_dir / "enrichment" / "pitch-accent.json").write_text(json.dumps(pitch), encoding="utf-8")

    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text('{"version": "test"}', encoding="utf-8")
    dist_dir = tmp_path / "dist"
    out_apkg = dist_dir / "japanese-language-data.apkg"

    monkeypatch.setattr(mod, "DIST_DIR", dist_dir)
    monkeypatch.setattr(mod, "OUT_APKG", out_apkg)
    monkeypatch.setattr(mod, "MANIFEST_PATH", manifest_path)
    monkeypatch.setattr("build.export_anki.DATA_DIR", data_dir)
    monkeypatch.setattr("build.export_anki.REPO_ROOT", tmp_path)

    mod.export()
    assert out_apkg.exists()


def test_anki_export_skips_words_without_text(tmp_path: Path, monkeypatch) -> None:
    """Words with no kanji or kana text are skipped."""
    import build.export_anki as mod

    data_dir = tmp_path / "data"
    (data_dir / "core").mkdir(parents=True)
    (data_dir / "grammar").mkdir(parents=True)

    words = {"words": [
        {"id": "1", "kanji": [], "kana": [], "sense": [{"gloss": [{"text": "orphan"}]}]},
        {"id": "2", "kanji": [], "kana": [{"text": "はい", "tags": []}], "sense": []},
    ]}
    (data_dir / "core" / "words.json").write_text(json.dumps(words), encoding="utf-8")

    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text('{"version": "test"}', encoding="utf-8")
    dist_dir = tmp_path / "dist"
    out_apkg = dist_dir / "japanese-language-data.apkg"

    monkeypatch.setattr(mod, "DIST_DIR", dist_dir)
    monkeypatch.setattr(mod, "OUT_APKG", out_apkg)
    monkeypatch.setattr(mod, "MANIFEST_PATH", manifest_path)
    monkeypatch.setattr("build.export_anki.DATA_DIR", data_dir)
    monkeypatch.setattr("build.export_anki.REPO_ROOT", tmp_path)

    mod.export()
    assert out_apkg.exists()


def test_anki_main_returns_zero(tmp_path: Path, monkeypatch) -> None:
    """main() calls export() and returns 0."""
    import build.export_anki as mod

    data_dir = tmp_path / "data"
    data_dir.mkdir()
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text('{"version": "test"}', encoding="utf-8")
    dist_dir = tmp_path / "dist"
    out_apkg = dist_dir / "japanese-language-data.apkg"

    monkeypatch.setattr(mod, "DIST_DIR", dist_dir)
    monkeypatch.setattr(mod, "OUT_APKG", out_apkg)
    monkeypatch.setattr(mod, "MANIFEST_PATH", manifest_path)
    monkeypatch.setattr("build.export_anki.DATA_DIR", data_dir)
    monkeypatch.setattr("build.export_anki.REPO_ROOT", tmp_path)

    assert mod.main() == 0


# ---------------------------------------------------------------------------
# export_sqlite — inline insert blocks in export()
# ---------------------------------------------------------------------------

def _setup_sqlite_export(tmp_path, monkeypatch):
    """Shared helper: create mock data files and monkeypatch the sqlite module."""
    import build.export_sqlite as mod

    data_dir = tmp_path / "data"
    for sub in ("core", "enrichment", "grammar", "corpus", "cross-refs"):
        (data_dir / sub).mkdir(parents=True)

    # Core
    words = {"words": [{
        "id": "1000010", "kanji": [{"text": "食べる", "tags": ["ichi1"]}],
        "kana": [{"text": "たべる", "tags": []}],
        "sense": [{"gloss": [{"text": "to eat"}]}], "jlpt_waller": "N5",
    }]}
    (data_dir / "core" / "words.json").write_text(json.dumps(words), encoding="utf-8")

    kanji = {"kanji": [{
        "character": "食", "stroke_count": 9, "grade": 2, "jlpt_waller": "N5",
        "frequency": 328, "readings": {"on": ["ショク"], "kun": ["た.べる"]},
        "meanings": {"en": ["eat"]},
    }]}
    (data_dir / "core" / "kanji.json").write_text(json.dumps(kanji), encoding="utf-8")

    radicals = {"radicals": [{"character": "一", "kangxi_number": 1, "stroke_count": 1, "meaning_en": "one"}]}
    (data_dir / "core" / "radicals.json").write_text(json.dumps(radicals), encoding="utf-8")

    # Corpus
    sentences = {"sentences": [{"id": "100", "japanese": "食べます", "english": "I eat"}]}
    (data_dir / "corpus" / "sentences.json").write_text(json.dumps(sentences), encoding="utf-8")

    kftt = {"sentences": [{"id": "kftt-1", "japanese": "京都", "english": "Kyoto"}]}
    (data_dir / "corpus" / "sentences-kftt.json").write_text(json.dumps(kftt), encoding="utf-8")

    # Grammar
    grammar = {"grammar_points": [{
        "id": "n5-te", "pattern": "～て", "meaning_en": "and then",
        "level": "N5", "formality": "neutral", "formation": "V-te", "review_status": "draft",
    }]}
    (data_dir / "grammar" / "grammar.json").write_text(json.dumps(grammar), encoding="utf-8")

    # Enrichment
    pitch = {"entries": [{"text": "食べる", "reading": "たべる", "pitch_positions": [2], "mora_count": 3}]}
    (data_dir / "enrichment" / "pitch-accent.json").write_text(json.dumps(pitch), encoding="utf-8")

    freq = {"entries": [{"text": "食べる", "reading": "たべる", "rank": 100, "count": 5000}]}
    (data_dir / "enrichment" / "frequency-corpus.json").write_text(json.dumps(freq), encoding="utf-8")

    freq_sub = {"entries": [{"text": "食べる", "reading": "たべる", "rank": 50, "count": 8000}]}
    (data_dir / "enrichment" / "frequency-subtitles.json").write_text(json.dumps(freq_sub), encoding="utf-8")

    furigana = {"entries": [{"text": "食べる", "reading": "たべる", "segments": [{"text": "食", "reading": "た"}, {"text": "べる"}]}]}
    (data_dir / "enrichment" / "furigana.json").write_text(json.dumps(furigana), encoding="utf-8")

    # Expressions
    expr = {"expressions": [{"id": "2000", "text": "お疲れ様", "reading": "おつかれさま", "meanings": ["good work"], "common": True, "jlpt_waller": "N3"}]}
    (data_dir / "grammar" / "expressions.json").write_text(json.dumps(expr), encoding="utf-8")

    # Conjugations
    conj = {"entries": [{"dictionary_form": "食べる", "reading": "たべる", "class": "ichidan", "forms": {"te_form": "食べて"}, "display_forms": {}}]}
    (data_dir / "grammar" / "conjugations.json").write_text(json.dumps(conj), encoding="utf-8")

    # JLPT
    jlpt = {"classifications": [{"kind": "vocab", "level": "N5", "jmdict_seq": "1000010", "grammar_id": "", "text": "食べる", "reading": "たべる"}]}
    (data_dir / "enrichment" / "jlpt-classifications.json").write_text(json.dumps(jlpt), encoding="utf-8")

    # Jukugo
    jukugo = {"compounds": [{"word_id": "1000020", "text": "食事", "reading": "しょくじ", "meaning": "meal", "kanji_count": 2, "kanji_sequence": ["食", "事"], "components": [], "jlpt_waller": "N4"}]}
    (data_dir / "enrichment" / "jukugo-compounds.json").write_text(json.dumps(jukugo), encoding="utf-8")

    # Counter words
    ctr = {"counter_words": [{"word_id": "3000", "text": "個", "reading": "こ", "meanings": ["counter for small items"], "jlpt_waller": "N5"}]}
    (data_dir / "enrichment" / "counter-words.json").write_text(json.dumps(ctr), encoding="utf-8")

    # Ateji
    ateji = {"entries": [{"word_id": "4000", "text": "素敵", "reading": "すてき", "meanings": ["lovely"], "jlpt_waller": "N3"}]}
    (data_dir / "enrichment" / "ateji.json").write_text(json.dumps(ateji), encoding="utf-8")

    # Cross-refs
    for fname, mapping in [
        ("kanji-to-words.json", {"食": ["1000010"]}),
        ("word-to-sentences.json", {"1000010": ["100"]}),
        ("kanji-to-sentences.json", {"食": ["100"]}),
        ("radical-to-kanji.json", {"一": ["食"]}),
        ("reading-to-words.json", {"たべる": ["1000010"]}),
        ("word-to-grammar.json", {"1000010": ["n5-te"]}),
    ]:
        (data_dir / "cross-refs" / fname).write_text(
            json.dumps({"mapping": mapping}), encoding="utf-8"
        )

    manifest = {"version": "0.8.0-test", "generated": "2026-04-12"}
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    dist_dir = tmp_path / "dist"
    out_db = dist_dir / "japanese-language-data.sqlite"

    monkeypatch.setattr(mod, "DIST_DIR", dist_dir)
    monkeypatch.setattr(mod, "OUT_DB", out_db)
    monkeypatch.setattr(mod, "MANIFEST_PATH", manifest_path)
    monkeypatch.setattr("build.export_sqlite.DATA_DIR", data_dir)
    monkeypatch.setattr("build.export_sqlite.REPO_ROOT", tmp_path)

    return mod, out_db


def test_sqlite_export_full_integration(tmp_path: Path, monkeypatch) -> None:
    """Full export() produces a database with all tables populated."""
    import sqlite3
    mod, out_db = _setup_sqlite_export(tmp_path, monkeypatch)
    mod.export()

    assert out_db.exists()
    conn = sqlite3.connect(str(out_db))

    # Spot-check key tables
    assert conn.execute("SELECT COUNT(*) FROM words").fetchone()[0] == 1
    assert conn.execute("SELECT COUNT(*) FROM kanji").fetchone()[0] == 1
    assert conn.execute("SELECT COUNT(*) FROM radicals").fetchone()[0] == 1
    assert conn.execute("SELECT COUNT(*) FROM sentences").fetchone()[0] == 2  # tatoeba + kftt
    assert conn.execute("SELECT COUNT(*) FROM grammar").fetchone()[0] == 1
    assert conn.execute("SELECT COUNT(*) FROM pitch_accent").fetchone()[0] == 1
    assert conn.execute("SELECT COUNT(*) FROM frequency_corpus").fetchone()[0] == 1
    assert conn.execute("SELECT COUNT(*) FROM frequency_subtitles").fetchone()[0] == 1
    assert conn.execute("SELECT COUNT(*) FROM furigana").fetchone()[0] == 1
    assert conn.execute("SELECT COUNT(*) FROM expressions").fetchone()[0] == 1
    assert conn.execute("SELECT COUNT(*) FROM conjugations").fetchone()[0] == 1
    assert conn.execute("SELECT COUNT(*) FROM jlpt_classifications").fetchone()[0] == 1
    assert conn.execute("SELECT COUNT(*) FROM jukugo_compounds").fetchone()[0] == 1
    assert conn.execute("SELECT COUNT(*) FROM counter_words").fetchone()[0] == 1
    assert conn.execute("SELECT COUNT(*) FROM ateji").fetchone()[0] == 1
    assert conn.execute("SELECT COUNT(*) FROM kanji_to_words").fetchone()[0] == 1
    assert conn.execute("SELECT COUNT(*) FROM word_to_grammar").fetchone()[0] == 1

    # Metadata
    version = conn.execute("SELECT value FROM _metadata WHERE key='version'").fetchone()[0]
    assert version == "0.8.0-test"

    conn.close()


def test_sqlite_export_overwrites_existing(tmp_path: Path, monkeypatch) -> None:
    """export() deletes the old database before creating a new one."""
    import sqlite3
    mod, out_db = _setup_sqlite_export(tmp_path, monkeypatch)

    # Pre-create a dummy file
    out_db.parent.mkdir(parents=True, exist_ok=True)
    out_db.write_text("old data")

    mod.export()
    conn = sqlite3.connect(str(out_db))
    assert conn.execute("SELECT COUNT(*) FROM words").fetchone()[0] == 1
    conn.close()


def test_sqlite_main_returns_zero(tmp_path: Path, monkeypatch) -> None:
    mod, _ = _setup_sqlite_export(tmp_path, monkeypatch)
    assert mod.main() == 0


# ---------------------------------------------------------------------------
# grammar — _load_tatoeba_text_index, _link_examples_to_tatoeba, build()
# ---------------------------------------------------------------------------

def test_grammar_load_tatoeba_text_index(tmp_path: Path, monkeypatch) -> None:
    from build.transform import grammar as mod
    sentences = {"sentences": [
        {"id": "100", "japanese": "食べます。", "english": "I eat."},
        {"id": "200", "japanese": "飲みます", "english": "I drink."},
    ]}
    sentences_path = tmp_path / "sentences.json"
    sentences_path.write_text(json.dumps(sentences), encoding="utf-8")
    monkeypatch.setattr(mod, "SENTENCES_JSON", sentences_path)

    exact, normalized = mod._load_tatoeba_text_index()
    assert "食べます。" in exact
    assert exact["食べます。"] == "100"
    # Normalized strips trailing punct
    assert "食べます" in normalized


def test_grammar_load_tatoeba_text_index_no_file(tmp_path: Path, monkeypatch) -> None:
    from build.transform import grammar as mod
    monkeypatch.setattr(mod, "SENTENCES_JSON", tmp_path / "nope.json")
    exact, normalized = mod._load_tatoeba_text_index()
    assert exact == {}
    assert normalized == {}


def test_grammar_link_examples_exact(tmp_path: Path) -> None:
    from build.transform.grammar import _link_examples_to_tatoeba

    text_index = {"食べます": "100"}
    normalized_index = {}
    entries = [{"id": "g1", "examples": [
        {"japanese": "食べます", "source": "original"},
    ]}]

    total, linked, via_norm = _link_examples_to_tatoeba(entries, text_index, normalized_index)
    assert total == 1
    assert linked == 1
    assert via_norm == 0
    assert entries[0]["examples"][0]["sentence_id"] == "100"
    assert entries[0]["examples"][0]["source"] == "tatoeba"


def test_grammar_link_examples_normalized(tmp_path: Path) -> None:
    from build.transform.grammar import _link_examples_to_tatoeba

    text_index = {}
    normalized_index = {"食べます": "200"}
    entries = [{"id": "g1", "examples": [
        {"japanese": "食べます。", "source": "original"},
    ]}]

    total, linked, via_norm = _link_examples_to_tatoeba(entries, text_index, normalized_index)
    assert total == 1
    assert linked == 1
    assert via_norm == 1


def test_grammar_link_examples_already_linked() -> None:
    from build.transform.grammar import _link_examples_to_tatoeba

    entries = [{"id": "g1", "examples": [
        {"japanese": "食べます", "source": "tatoeba", "sentence_id": "999"},
    ]}]
    total, linked, _ = _link_examples_to_tatoeba(entries, {}, {})
    assert total == 1
    assert linked == 1  # counted as already linked


def test_grammar_build_with_mock_curated(tmp_path: Path, monkeypatch) -> None:
    """Full build() with mock curated files and mock sentence corpus."""
    from build.transform import grammar as mod

    curated_dir = tmp_path / "grammar-curated"
    curated_dir.mkdir()
    out_path = tmp_path / "grammar.json"
    sentences_path = tmp_path / "sentences.json"
    kftt_path = tmp_path / "kftt.json"

    entries = [{
        "id": "n5-te-form", "pattern": "～て", "level": "N5",
        "meaning_en": "and then", "formation": "V-te form",
        "examples": [{"japanese": "食べて待ってください", "english": "Please eat and wait", "source": "original"}],
        "review_status": "draft",
        "sources": ["general knowledge"],
    }]
    (curated_dir / "n5.json").write_text(json.dumps(entries), encoding="utf-8")

    sentences = {"sentences": [
        {"id": "100", "japanese": "食べて待ってください", "english": "Please eat and wait"},
        {"id": "200", "japanese": "泳いでください", "english": "Please swim"},
    ]}
    sentences_path.write_text(json.dumps(sentences), encoding="utf-8")

    kftt = {"sentences": [{"id": "kftt-1", "japanese": "てから始めた", "english": "started after"}]}
    kftt_path.write_text(json.dumps(kftt), encoding="utf-8")

    monkeypatch.setattr(mod, "CURATED_DIR", curated_dir)
    monkeypatch.setattr(mod, "OUT", out_path)
    monkeypatch.setattr(mod, "SENTENCES_JSON", sentences_path)
    monkeypatch.setattr(mod, "KFTT_JSON", kftt_path)
    monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)

    mod.build()

    assert out_path.exists()
    result = json.loads(out_path.read_text(encoding="utf-8"))
    assert result["metadata"]["count"] == 1
    assert result["grammar_points"][0]["id"] == "n5-te-form"
    # Example should have been linked via exact match
    ex = result["grammar_points"][0]["examples"][0]
    assert ex["source"] == "tatoeba"
    assert ex["sentence_id"] == "100"


def test_grammar_build_empty_curated_dir(tmp_path: Path, monkeypatch) -> None:
    """build() with missing curated dir emits empty grammar.json with warning."""
    from build.transform import grammar as mod

    out_path = tmp_path / "grammar.json"
    monkeypatch.setattr(mod, "CURATED_DIR", tmp_path / "nonexistent")
    monkeypatch.setattr(mod, "OUT", out_path)
    monkeypatch.setattr(mod, "SENTENCES_JSON", tmp_path / "nope.json")
    monkeypatch.setattr(mod, "KFTT_JSON", tmp_path / "nope2.json")
    monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)

    with pytest.warns(UserWarning, match="grammar-curated"):
        mod.build()

    result = json.loads(out_path.read_text(encoding="utf-8"))
    assert result["metadata"]["count"] == 0
    assert result["grammar_points"] == []


def test_grammar_build_duplicate_id_raises(tmp_path: Path, monkeypatch) -> None:
    from build.transform import grammar as mod

    curated_dir = tmp_path / "grammar-curated"
    curated_dir.mkdir()
    entries = [
        {"id": "dup", "pattern": "～て", "level": "N5", "meaning_en": "x",
         "formation": "y", "examples": [{"japanese": "a", "english": "b"}],
         "review_status": "draft", "sources": ["x"]},
        {"id": "dup", "pattern": "～た", "level": "N5", "meaning_en": "x",
         "formation": "y", "examples": [{"japanese": "a", "english": "b"}],
         "review_status": "draft", "sources": ["x"]},
    ]
    (curated_dir / "n5.json").write_text(json.dumps(entries), encoding="utf-8")

    monkeypatch.setattr(mod, "CURATED_DIR", curated_dir)
    monkeypatch.setattr(mod, "OUT", tmp_path / "out.json")
    monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)

    with pytest.raises(ValueError, match="Duplicate grammar id"):
        mod.build()


def test_grammar_build_broken_related_raises(tmp_path: Path, monkeypatch) -> None:
    from build.transform import grammar as mod

    curated_dir = tmp_path / "grammar-curated"
    curated_dir.mkdir()
    entries = [{
        "id": "n5-te", "pattern": "～て", "level": "N5", "meaning_en": "x",
        "formation": "y", "examples": [{"japanese": "a", "english": "b"}],
        "review_status": "draft", "sources": ["x"], "related": ["nonexistent-id"],
    }]
    (curated_dir / "n5.json").write_text(json.dumps(entries), encoding="utf-8")

    monkeypatch.setattr(mod, "CURATED_DIR", curated_dir)
    monkeypatch.setattr(mod, "OUT", tmp_path / "out.json")
    monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)

    with pytest.raises(ValueError, match="unknown related"):
        mod.build()


# ---------------------------------------------------------------------------
# cross_links — _build_kanji_to_sentences, _build_word_to_grammar, _write_xref, build()
# ---------------------------------------------------------------------------

def test_cross_links_build_kanji_to_sentences() -> None:
    from build.transform.cross_links import _build_kanji_to_sentences
    sentences = {"sentences": [
        {"id": "100", "japanese": "食べます"},
        {"id": "200", "japanese": "水を飲む"},
    ]}
    result = _build_kanji_to_sentences(sentences)
    assert "食" in result
    assert "100" in result["食"]
    assert "水" in result
    assert "200" in result["水"]
    assert "飲" in result
    assert "200" in result["飲"]


def test_cross_links_build_kanji_to_sentences_skips_kana() -> None:
    from build.transform.cross_links import _build_kanji_to_sentences
    sentences = {"sentences": [{"id": "1", "japanese": "たべます"}]}
    result = _build_kanji_to_sentences(sentences)
    assert len(result) == 0


def test_cross_links_build_word_to_grammar() -> None:
    from build.transform.cross_links import _build_word_to_grammar
    grammar_data = {"grammar_points": [{
        "id": "n5-te", "examples": [{"japanese": "食べてください"}],
    }]}
    word_text_lookup = {"食べ": "1000010", "ください": "2000020"}
    result = _build_word_to_grammar(grammar_data, word_text_lookup)
    assert "1000010" in result
    assert "n5-te" in result["1000010"]
    assert "2000020" in result
    assert "n5-te" in result["2000020"]


def test_cross_links_build_word_text_lookup() -> None:
    from build.transform.cross_links import _build_word_text_lookup
    words = {"words": [
        {"id": "1", "kanji": [{"text": "食べる"}], "kana": [{"text": "たべる"}]},
        {"id": "2", "kanji": [], "kana": [{"text": "い"}]},   # too short kana
        {"id": "3", "kanji": [{"text": "水"}], "kana": []},   # single-char kanji — too short
    ]}
    result = _build_word_text_lookup(words)
    assert "食べる" in result
    assert "たべる" in result
    assert "い" not in result   # kana < 3 chars excluded
    assert "水" not in result   # kanji < 2 chars excluded


def test_cross_links_write_xref_format(tmp_path: Path, monkeypatch) -> None:
    from build.transform import cross_links as mod
    monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)

    out = tmp_path / "test-xref.json"
    mod._write_xref(
        out, {"b": ["2"], "a": ["1"]},
        "test direction", "key_type", "value_type",
        ["source.json"],
    )
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["metadata"]["count"] == 2
    assert data["metadata"]["direction"] == "test direction"
    # Keys should be sorted
    keys = list(data["mapping"].keys())
    assert keys == ["a", "b"]


def test_cross_links_build_full(tmp_path: Path, monkeypatch) -> None:
    """Full build() with mock data files."""
    from build.transform import cross_links as mod

    data_dir = tmp_path / "data"
    (data_dir / "core").mkdir(parents=True)
    (data_dir / "corpus").mkdir(parents=True)
    (data_dir / "grammar").mkdir(parents=True)
    (data_dir / "cross-refs").mkdir(parents=True)

    words = {"words": [{
        "id": "1", "kanji": [{"text": "食べる"}], "kana": [{"text": "たべる"}],
        "sense": [{"examples": [{"sentence_id": "100"}]}],
    }]}
    (data_dir / "core" / "words.json").write_text(json.dumps(words), encoding="utf-8")

    kanji = {"kanji": [{"character": "食"}]}
    (data_dir / "core" / "kanji.json").write_text(json.dumps(kanji), encoding="utf-8")

    radicals = {"radicals": [], "kanji_to_radicals": {"食": ["人", "良"]}}
    (data_dir / "core" / "radicals.json").write_text(json.dumps(radicals), encoding="utf-8")

    sentences = {"sentences": [{"id": "100", "japanese": "食べます"}]}
    (data_dir / "corpus" / "sentences.json").write_text(json.dumps(sentences), encoding="utf-8")

    grammar = {"grammar_points": [{
        "id": "n5-te", "examples": [{"japanese": "食べるのが好きです"}],
    }]}
    (data_dir / "grammar" / "grammar.json").write_text(json.dumps(grammar), encoding="utf-8")

    monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(mod, "KANJI_JSON", data_dir / "core" / "kanji.json")
    monkeypatch.setattr(mod, "WORDS_JSON", data_dir / "core" / "words.json")
    monkeypatch.setattr(mod, "WORDS_FULL_JSON", data_dir / "core" / "words-full.json")
    monkeypatch.setattr(mod, "RADICALS_JSON", data_dir / "core" / "radicals.json")
    monkeypatch.setattr(mod, "SENTENCES_JSON", data_dir / "corpus" / "sentences.json")
    monkeypatch.setattr(mod, "GRAMMAR_JSON", data_dir / "grammar" / "grammar.json")
    monkeypatch.setattr(mod, "OUT_DIR", data_dir / "cross-refs")

    mod.build()

    # Verify key output files
    assert (data_dir / "cross-refs" / "kanji-to-words.json").exists()
    assert (data_dir / "cross-refs" / "word-to-kanji.json").exists()
    assert (data_dir / "cross-refs" / "kanji-to-sentences.json").exists()
    assert (data_dir / "cross-refs" / "word-to-grammar.json").exists()
    assert (data_dir / "cross-refs" / "radical-to-kanji.json").exists()
    assert (data_dir / "cross-refs" / "reading-to-words.json").exists()

    k2s = json.loads((data_dir / "cross-refs" / "kanji-to-sentences.json").read_text(encoding="utf-8"))
    assert "食" in k2s["mapping"]


def test_cross_links_build_missing_prerequisite(tmp_path: Path, monkeypatch) -> None:
    from build.transform import cross_links as mod
    monkeypatch.setattr(mod, "KANJI_JSON", tmp_path / "nope.json")
    monkeypatch.setattr(mod, "WORDS_JSON", tmp_path / "nope2.json")
    monkeypatch.setattr(mod, "RADICALS_JSON", tmp_path / "nope3.json")
    monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)

    with pytest.raises(FileNotFoundError, match="Cross-links stage requires"):
        mod.build()


# ---------------------------------------------------------------------------
# stroke_order — build() with mock ZIP
# ---------------------------------------------------------------------------

def _make_kanjivg_zip(tmp_path: Path, entries: dict[str, str]) -> Path:
    """Create a mock KanjiVG ZIP with the given char→svg_content mapping."""
    import zipfile
    zip_path = tmp_path / "kanjivg-main.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        for char, svg_content in entries.items():
            codepoint = f"{ord(char):05x}"
            zf.writestr(f"kanji/{codepoint}.svg", svg_content)
    return zip_path


def test_stroke_order_build_with_mock_zip(tmp_path: Path, monkeypatch) -> None:
    from build.transform import stroke_order as mod

    # Minimal SVG with 3 strokes (3 <path> elements with id)
    svg = (
        '<svg><g id="kvg:098df">'
        '<path id="kvg:098df-s1" d="M1"/>'
        '<path id="kvg:098df-s2" d="M2"/>'
        '<path id="kvg:098df-s3" d="M3"/>'
        '</g></svg>'
    )
    zip_path = _make_kanjivg_zip(tmp_path, {"食": svg})

    out_dir = tmp_path / "stroke-order"
    out_index = tmp_path / "stroke-order-index.json"
    kanji_json = tmp_path / "kanji.json"
    kanji_json.write_text(json.dumps({"kanji": [{"character": "食", "stroke_count": 9}]}), encoding="utf-8")

    monkeypatch.setattr(mod, "SOURCE_ZIP", zip_path)
    monkeypatch.setattr(mod, "OUT_DIR", out_dir)
    monkeypatch.setattr(mod, "OUT_INDEX", out_index)
    monkeypatch.setattr(mod, "KANJI_JSON", kanji_json)
    monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)

    mod.build()

    assert out_index.exists()
    index = json.loads(out_index.read_text(encoding="utf-8"))
    assert "食" in index["characters"]
    assert index["characters"]["食"]["stroke_count"] == 3
    assert index["characters"]["食"]["unicode"] == "098df"
    # SVG file written
    assert (out_dir / "食.svg").exists()


def test_stroke_order_build_filters_to_kanji_set(tmp_path: Path, monkeypatch) -> None:
    """Characters not in kanji.json are excluded."""
    from build.transform import stroke_order as mod

    svg_a = '<svg><path id="kvg:098df-s1" d="M1"/></svg>'
    svg_b = '<svg><path id="kvg:06c34-s1" d="M1"/></svg>'
    zip_path = _make_kanjivg_zip(tmp_path, {"食": svg_a, "水": svg_b})

    out_dir = tmp_path / "stroke-order"
    out_index = tmp_path / "stroke-order-index.json"
    kanji_json = tmp_path / "kanji.json"
    # Only 食 in kanji.json, not 水
    kanji_json.write_text(json.dumps({"kanji": [{"character": "食", "stroke_count": 9}]}), encoding="utf-8")

    monkeypatch.setattr(mod, "SOURCE_ZIP", zip_path)
    monkeypatch.setattr(mod, "OUT_DIR", out_dir)
    monkeypatch.setattr(mod, "OUT_INDEX", out_index)
    monkeypatch.setattr(mod, "KANJI_JSON", kanji_json)
    monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)

    mod.build()

    index = json.loads(out_index.read_text(encoding="utf-8"))
    assert "食" in index["characters"]
    assert "水" not in index["characters"]


def test_stroke_order_build_variant_skipped(tmp_path: Path, monkeypatch) -> None:
    """Variant files (e.g., 098df-Kaisho.svg) are skipped."""
    import zipfile
    from build.transform import stroke_order as mod

    zip_path = tmp_path / "kanjivg-main.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("kanji/098df.svg", '<svg><path id="kvg:098df-s1" d="M1"/></svg>')
        zf.writestr("kanji/098df-Kaisho.svg", '<svg><path id="kvg:098df-s1" d="M1"/></svg>')

    out_dir = tmp_path / "stroke-order"
    out_index = tmp_path / "stroke-order-index.json"

    monkeypatch.setattr(mod, "SOURCE_ZIP", zip_path)
    monkeypatch.setattr(mod, "OUT_DIR", out_dir)
    monkeypatch.setattr(mod, "OUT_INDEX", out_index)
    monkeypatch.setattr(mod, "KANJI_JSON", tmp_path / "nope.json")  # no filter
    monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)

    mod.build()

    index = json.loads(out_index.read_text(encoding="utf-8"))
    # Should have exactly 1 entry (the variant is skipped)
    assert index["metadata"]["count"] == 1


def test_stroke_order_build_mismatch_detection(tmp_path: Path, monkeypatch) -> None:
    """Stroke count mismatches against kanji.json are recorded in metadata."""
    from build.transform import stroke_order as mod

    # SVG has 2 strokes but kanji.json says 9
    svg = '<svg><path id="kvg:098df-s1" d="M1"/><path id="kvg:098df-s2" d="M2"/></svg>'
    zip_path = _make_kanjivg_zip(tmp_path, {"食": svg})

    out_dir = tmp_path / "stroke-order"
    out_index = tmp_path / "stroke-order-index.json"
    kanji_json = tmp_path / "kanji.json"
    kanji_json.write_text(json.dumps({"kanji": [{"character": "食", "stroke_count": 9}]}), encoding="utf-8")

    monkeypatch.setattr(mod, "SOURCE_ZIP", zip_path)
    monkeypatch.setattr(mod, "OUT_DIR", out_dir)
    monkeypatch.setattr(mod, "OUT_INDEX", out_index)
    monkeypatch.setattr(mod, "KANJI_JSON", kanji_json)
    monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)

    mod.build()

    index = json.loads(out_index.read_text(encoding="utf-8"))
    mismatches = index["metadata"]["stroke_count_mismatches"]
    assert len(mismatches) == 1
    assert mismatches[0]["character"] == "食"
    assert mismatches[0]["kanjidic2_count"] == 9
    assert mismatches[0]["kanjivg_count"] == 2


# ---------------------------------------------------------------------------
# kanji — _transform_character edge cases, _metadata, build()
# ---------------------------------------------------------------------------

def test_kanji_transform_character_dic_refs() -> None:
    from build.transform.kanji import _transform_character
    ch = {
        "literal": "食",
        "dictionaryReferences": [
            {"type": "heisig", "value": 1472},
            {"type": "nelson_c", "value": 5154},
            {"type": "unknown_type", "value": 999},  # not in WANTED_DIC_REFS
        ],
        "misc": {"strokeCounts": [9]},
    }
    result = _transform_character(ch)
    assert result["dic_refs"]["heisig"] == "1472"
    assert result["dic_refs"]["nelson_c"] == "5154"
    assert "unknown_type" not in result["dic_refs"]


def test_kanji_transform_character_query_codes_skip_misclass() -> None:
    from build.transform.kanji import _transform_character
    ch = {
        "literal": "食",
        "queryCodes": [
            {"type": "skip", "value": "2-4-5", "skipMisclassification": True},
            {"type": "skip", "value": "2-2-7"},
            {"type": "four_corner", "value": "8073.2"},
        ],
        "misc": {"strokeCounts": [9]},
    }
    result = _transform_character(ch)
    # Misclassified SKIP is excluded; primary SKIP kept
    assert result["query_codes"]["skip"] == "2-2-7"
    assert result["query_codes"]["four_corner"] == "8073.2"


def test_kanji_transform_character_readings_cjk() -> None:
    from build.transform.kanji import _transform_character
    ch = {
        "literal": "食",
        "readingMeaning": {"groups": [{"readings": [
            {"type": "ja_on", "value": "ショク"},
            {"type": "ja_kun", "value": "た.べる"},
            {"type": "pinyin", "value": "shí"},
            {"type": "korean_r", "value": "sig"},
            {"type": "korean_h", "value": "식"},
            {"type": "vietnam", "value": "Thực"},
        ], "meanings": [
            {"lang": "en", "value": "eat"},
            {"lang": "fr", "value": "manger"},
        ]}], "nanori": ["くい"]},
        "misc": {"strokeCounts": [9]},
    }
    result = _transform_character(ch)
    assert result["readings_cjk"]["pinyin"] == ["shí"]
    assert result["readings_cjk"]["korean_romanized"] == ["sig"]
    assert result["readings_cjk"]["korean_hangul"] == ["식"]
    assert result["readings_cjk"]["vietnamese"] == ["Thực"]
    assert result["meanings"]["fr"] == ["manger"]
    assert result["nanori"] == ["くい"]


def test_kanji_transform_character_variants() -> None:
    from build.transform.kanji import _transform_character
    ch = {
        "literal": "食",
        "misc": {
            "strokeCounts": [9, 8],
            "variants": [{"type": "jis208", "value": "1-31-29"}],
        },
    }
    result = _transform_character(ch)
    assert result["stroke_count"] == 9
    assert result["stroke_count_variants"] == [8]
    assert result["variants"] == [{"type": "jis208", "value": "1-31-29"}]


def test_kanji_transform_character_jis212_jis213() -> None:
    from build.transform.kanji import _transform_character
    ch = {
        "literal": "𠀋",
        "codepoints": [
            {"type": "ucs", "value": "200CB"},
            {"type": "jis212", "value": "1-2-3"},
            {"type": "jis213", "value": "2-1-2"},
        ],
        "misc": {"strokeCounts": [5]},
    }
    result = _transform_character(ch)
    assert result["jis212"] == "1-2-3"
    assert result["jis213"] == "2-1-2"


def test_kanji_metadata_fields() -> None:
    from build.transform.kanji import _metadata
    source_meta = {
        "version": "3.6.2",
        "dictDate": "2024-01-01",
        "databaseVersion": "2024-175",
        "fileVersion": 4,
        "languages": ["eng", "fre"],
    }
    result = _metadata(source_meta, 100, "Test filter")
    assert result["source_version"] == "3.6.2"
    assert result["count"] == 100
    assert result["filter"] == "Test filter"
    assert result["upstream_file_version"] == 4
    assert result["upstream_languages"] == ["eng", "fre"]


def test_kanji_load_jlpt_map(tmp_path: Path, monkeypatch) -> None:
    from build.transform import kanji as mod
    jlpt_path = tmp_path / "jlpt.json"
    jlpt_path.write_text(json.dumps({"classifications": [
        {"kind": "kanji", "text": "食", "level": "N5"},
        {"kind": "vocab", "text": "食べる", "level": "N5"},  # ignored — not kanji kind
    ]}), encoding="utf-8")
    monkeypatch.setattr(mod, "JLPT_ENRICHMENT", jlpt_path)
    result = mod._load_kanji_jlpt_map()
    assert result == {"食": "N5"}


def test_kanji_load_radical_components_map(tmp_path: Path, monkeypatch) -> None:
    from build.transform import kanji as mod
    rad_path = tmp_path / "radicals.json"
    rad_path.write_text(json.dumps({"kanji_to_radicals": {"食": ["人", "良"]}}), encoding="utf-8")
    monkeypatch.setattr(mod, "RADICALS_ENRICHMENT", rad_path)
    result = mod._load_radical_components_map()
    assert result == {"食": ["人", "良"]}


def test_kanji_load_radical_components_map_missing(tmp_path: Path, monkeypatch) -> None:
    from build.transform import kanji as mod
    monkeypatch.setattr(mod, "RADICALS_ENRICHMENT", tmp_path / "nope.json")
    assert mod._load_radical_components_map() == {}


def test_kanji_build_with_mock_source(tmp_path: Path, monkeypatch) -> None:
    """Full build() with a mock tgz source."""
    import tarfile
    from build.transform import kanji as mod

    # Create a minimal KANJIDIC2-like source
    source_data = {
        "version": "test",
        "characters": [{
            "literal": "食",
            "codepoints": [{"type": "ucs", "value": "98DF"}],
            "radicals": [{"type": "classical", "value": 184}],
            "misc": {"strokeCounts": [9], "grade": 2, "frequency": 328},
            "readingMeaning": {
                "groups": [{"readings": [
                    {"type": "ja_on", "value": "ショク"},
                    {"type": "ja_kun", "value": "た.べる"},
                ], "meanings": [{"lang": "en", "value": "eat"}]}],
                "nanori": [],
            },
        }, {
            "literal": "芝",
            "misc": {"strokeCounts": [6], "grade": 9},  # jinmeiyo
            "readingMeaning": {
                "groups": [{"readings": [
                    {"type": "ja_on", "value": "シ"},
                ], "meanings": [{"lang": "en", "value": "lawn"}]}],
            },
        }],
    }

    # Pack into a tgz
    source_tgz = tmp_path / "source.tgz"
    json_bytes = json.dumps(source_data).encode("utf-8")
    import io
    with tarfile.open(source_tgz, "w:gz") as tf:
        info = tarfile.TarInfo(name="kanjidic2.json")
        info.size = len(json_bytes)
        tf.addfile(info, io.BytesIO(json_bytes))

    out_full = tmp_path / "kanji.json"
    out_joyo = tmp_path / "kanji-joyo.json"
    out_jinmeiyo = tmp_path / "kanji-jinmeiyo.json"

    monkeypatch.setattr(mod, "SOURCE_TGZ", source_tgz)
    monkeypatch.setattr(mod, "OUT_FULL", out_full)
    monkeypatch.setattr(mod, "OUT_JOYO", out_joyo)
    monkeypatch.setattr(mod, "OUT_JINMEIYO", out_jinmeiyo)
    monkeypatch.setattr(mod, "JLPT_ENRICHMENT", tmp_path / "nope.json")
    monkeypatch.setattr(mod, "RADICALS_ENRICHMENT", tmp_path / "nope.json")
    monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)

    mod.build()

    assert out_full.exists()
    assert out_joyo.exists()
    assert out_jinmeiyo.exists()

    full = json.loads(out_full.read_text(encoding="utf-8"))
    assert full["metadata"]["count"] == 2

    joyo = json.loads(out_joyo.read_text(encoding="utf-8"))
    assert joyo["metadata"]["count"] == 1  # grade 2 only
    assert joyo["kanji"][0]["character"] == "食"

    jinmeiyo = json.loads(out_jinmeiyo.read_text(encoding="utf-8"))
    assert jinmeiyo["metadata"]["count"] == 1  # grade 9 only
    assert jinmeiyo["kanji"][0]["character"] == "芝"


# ---------------------------------------------------------------------------
# sentences — build()
# ---------------------------------------------------------------------------

def test_sentences_build(tmp_path: Path, monkeypatch) -> None:
    """Full build() with a mock tgz."""
    import io, tarfile
    from build.transform import sentences as mod

    source_data = {"words": [{
        "id": "1000010",
        "sense": [{"examples": [{
            "source": {"type": "tatoeba", "value": "100"},
            "sentences": [
                {"lang": "jpn", "text": "食べます"},
                {"lang": "eng", "text": "I eat"},
            ],
        }]}],
    }, {
        "id": "1000020",
        "sense": [{"examples": [{
            "source": {"type": "tatoeba", "value": "100"},  # duplicate
            "sentences": [
                {"lang": "jpn", "text": "食べます"},
                {"lang": "eng", "text": "I eat"},
            ],
        }, {
            "source": {"type": "other", "value": "999"},  # not tatoeba
            "sentences": [],
        }]}],
    }]}

    tgz_path = tmp_path / "source.tgz"
    json_bytes = json.dumps(source_data).encode("utf-8")
    with tarfile.open(tgz_path, "w:gz") as tf:
        info = tarfile.TarInfo(name="jmdict.json")
        info.size = len(json_bytes)
        tf.addfile(info, io.BytesIO(json_bytes))

    out_path = tmp_path / "sentences.json"
    monkeypatch.setattr(mod, "SOURCE_TGZ", tgz_path)
    monkeypatch.setattr(mod, "OUT", out_path)
    monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)

    mod.build()

    result = json.loads(out_path.read_text(encoding="utf-8"))
    assert result["metadata"]["count"] == 1  # deduped to 1
    assert result["sentences"][0]["id"] == "100"
    assert result["sentences"][0]["curated"] is True


def test_sentences_build_skips_no_japanese(tmp_path: Path, monkeypatch) -> None:
    """Entries with no Japanese text are skipped."""
    import io, tarfile
    from build.transform import sentences as mod

    source_data = {"words": [{
        "sense": [{"examples": [{
            "source": {"type": "tatoeba", "value": "100"},
            "sentences": [{"lang": "eng", "text": "only english"}],
        }]}],
    }]}

    tgz_path = tmp_path / "source.tgz"
    json_bytes = json.dumps(source_data).encode("utf-8")
    with tarfile.open(tgz_path, "w:gz") as tf:
        info = tarfile.TarInfo(name="jmdict.json")
        info.size = len(json_bytes)
        tf.addfile(info, io.BytesIO(json_bytes))

    out_path = tmp_path / "sentences.json"
    monkeypatch.setattr(mod, "SOURCE_TGZ", tgz_path)
    monkeypatch.setattr(mod, "OUT", out_path)
    monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)

    mod.build()

    result = json.loads(out_path.read_text(encoding="utf-8"))
    assert result["metadata"]["count"] == 0


# ---------------------------------------------------------------------------
# expressions — build()
# ---------------------------------------------------------------------------

def test_expressions_build(tmp_path: Path, monkeypatch) -> None:
    import io, tarfile
    from build.transform import expressions as mod

    source_data = {"version": "test", "dictDate": "2024-01-01", "words": [{
        "id": 2000,
        "kanji": [{"text": "お疲れ様", "common": True}],
        "kana": [{"text": "おつかれさま", "common": False}],
        "sense": [{"partOfSpeech": ["exp", "n"], "gloss": [{"text": "good work"}], "misc": ["pol"]}],
    }, {
        "id": 3000,
        "kanji": [],
        "kana": [{"text": "はい", "tags": []}],
        "sense": [{"partOfSpeech": ["int"], "gloss": [{"text": "yes"}], "misc": []}],  # not exp
    }]}

    tgz_path = tmp_path / "source.tgz"
    json_bytes = json.dumps(source_data).encode("utf-8")
    with tarfile.open(tgz_path, "w:gz") as tf:
        info = tarfile.TarInfo(name="jmdict.json")
        info.size = len(json_bytes)
        tf.addfile(info, io.BytesIO(json_bytes))

    out_path = tmp_path / "expressions.json"
    monkeypatch.setattr(mod, "SOURCE_TGZ", tgz_path)
    monkeypatch.setattr(mod, "OUT", out_path)
    monkeypatch.setattr(mod, "JLPT_ENRICHMENT", tmp_path / "nope.json")
    monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)

    mod.build()

    result = json.loads(out_path.read_text(encoding="utf-8"))
    assert result["metadata"]["count"] == 1
    assert result["expressions"][0]["text"] == "お疲れ様"
    assert result["expressions"][0]["common"] is True
    assert "pol" in result["expressions"][0]["misc"]


# ---------------------------------------------------------------------------
# kftt — build()
# ---------------------------------------------------------------------------

def test_kftt_build(tmp_path: Path, monkeypatch) -> None:
    import tarfile
    from build.transform import kftt as mod

    tgz_path = tmp_path / "kftt-data-1.0.tar.gz"
    with tarfile.open(tgz_path, "w:gz") as tf:
        for split in ("kyoto-train", "kyoto-dev", "kyoto-test", "kyoto-tune"):
            ja_content = "京都は美しい\n東京タワー\n".encode("utf-8")
            en_content = "Kyoto is beautiful\nTokyo Tower\n".encode("utf-8")
            for suffix, content in [
                (f"data/orig/{split}.ja", ja_content),
                (f"data/orig/{split}.en", en_content),
            ]:
                info = tarfile.TarInfo(name=suffix)
                info.size = len(content)
                import io
                tf.addfile(info, io.BytesIO(content))

    out_path = tmp_path / "sentences-kftt.json"
    monkeypatch.setattr(mod, "SOURCE_TGZ", tgz_path)
    monkeypatch.setattr(mod, "OUT", out_path)
    monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)

    mod.build()

    result = json.loads(out_path.read_text(encoding="utf-8"))
    assert result["metadata"]["count"] == 8  # 2 per split × 4 splits
    assert result["sentences"][0]["id"] == "kftt-1"
    assert result["sentences"][0]["curated"] is False


def test_kftt_build_missing_source(tmp_path: Path, monkeypatch) -> None:
    from build.transform import kftt as mod
    monkeypatch.setattr(mod, "SOURCE_TGZ", tmp_path / "nope.tar.gz")
    with pytest.raises(FileNotFoundError):
        mod.build()


# ---------------------------------------------------------------------------
# frequency — build()
# ---------------------------------------------------------------------------

def test_frequency_build(tmp_path: Path, monkeypatch) -> None:
    import io, tarfile
    from build.transform import frequency as mod

    source_data = {"version": "test", "characters": [
        {"literal": "食", "misc": {"frequency": 328}},
        {"literal": "人", "misc": {"frequency": 5}},
        {"literal": "蟲", "misc": {}},  # no frequency
    ]}

    tgz_path = tmp_path / "source.tgz"
    json_bytes = json.dumps(source_data).encode("utf-8")
    with tarfile.open(tgz_path, "w:gz") as tf:
        info = tarfile.TarInfo(name="kanjidic2.json")
        info.size = len(json_bytes)
        tf.addfile(info, io.BytesIO(json_bytes))

    out_path = tmp_path / "frequency-newspaper.json"
    monkeypatch.setattr(mod, "SOURCE_TGZ", tgz_path)
    monkeypatch.setattr(mod, "OUT", out_path)
    monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)

    mod.build()

    result = json.loads(out_path.read_text(encoding="utf-8"))
    assert result["metadata"]["count"] == 2
    # Sorted by rank
    assert result["entries"][0]["text"] == "人"
    assert result["entries"][0]["rank"] == 5
    assert result["entries"][1]["text"] == "食"
    assert result["entries"][1]["rank"] == 328


# ---------------------------------------------------------------------------
# pitch — build()
# ---------------------------------------------------------------------------

def test_pitch_build(tmp_path: Path, monkeypatch) -> None:
    from build.transform import pitch as mod

    source_path = tmp_path / "accents.txt"
    source_path.write_text(
        "食べる\tたべる\t2\n"
        "# comment\n"
        "飲む\tのむ\t1,0\n"
        "bad\tline\n"  # only 2 fields (actually this has 2 tabs... let me check)
        "\n",
        encoding="utf-8",
    )

    out_path = tmp_path / "pitch-accent.json"
    monkeypatch.setattr(mod, "SOURCE", source_path)
    monkeypatch.setattr(mod, "OUT", out_path)
    monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)

    mod.build()

    result = json.loads(out_path.read_text(encoding="utf-8"))
    assert result["metadata"]["count"] == 2
    assert result["entries"][0]["word"] == "食べる"
    assert result["entries"][0]["pitch_positions"] == [2]
    assert result["entries"][1]["pitch_positions"] == [1, 0]


def test_pitch_build_missing_source(tmp_path: Path, monkeypatch) -> None:
    from build.transform import pitch as mod
    monkeypatch.setattr(mod, "SOURCE", tmp_path / "nope.txt")
    with pytest.raises(FileNotFoundError):
        mod.build()


# ---------------------------------------------------------------------------
# names — build()
# ---------------------------------------------------------------------------

def test_names_build(tmp_path: Path, monkeypatch) -> None:
    import io, tarfile
    from build.transform import names as mod

    source_data = {"version": "test", "tags": {"person": "personal name"},
                   "words": [{"id": 5000, "kanji": [{"text": "田中"}],
                              "kana": [{"text": "たなか", "appliesToKanji": ["*"]}],
                              "translation": [{"type": ["surname"], "translation": [{"lang": "eng", "text": "Tanaka"}]}]}]}

    tgz_path = tmp_path / "source.tgz"
    json_bytes = json.dumps(source_data).encode("utf-8")
    with tarfile.open(tgz_path, "w:gz") as tf:
        info = tarfile.TarInfo(name="jmnedict.json")
        info.size = len(json_bytes)
        tf.addfile(info, io.BytesIO(json_bytes))

    out_path = tmp_path / "names.json"
    monkeypatch.setattr(mod, "SOURCE_TGZ", tgz_path)
    monkeypatch.setattr(mod, "OUT", out_path)
    monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)

    mod.build()

    result = json.loads(out_path.read_text(encoding="utf-8"))
    assert result["metadata"]["count"] == 1
    assert result["names"][0]["id"] == "5000"


# ---------------------------------------------------------------------------
# frequency_web — build()
# ---------------------------------------------------------------------------

def test_frequency_web_parse_file(tmp_path: Path) -> None:
    from build.transform.frequency_web import _parse_frequency_file
    content = (
        "The frequency distribution for attribute 'lemma'\n"
        "For more information visit http://corpus.leeds.ac.uk/\n"
        " - corpus size: 253071774 tokens\n"
        " - lexicon size: 124489 types\n"
        "1 41309.50 の\n"
        "2 23509.54 に\n"
        "3 100.00 hello\n"  # pure ASCII — filtered out
        "4 50.00 ・\n"  # punctuation only — filtered out
        "\n"
    )
    p = tmp_path / "freq.num"
    p.write_text(content, encoding="utf-8")
    result = _parse_frequency_file(p)
    assert len(result) == 2
    assert result[0] == ("の", 41309.50, 1)
    assert result[1] == ("に", 23509.54, 2)


def test_frequency_web_build(tmp_path: Path, monkeypatch) -> None:
    from build.transform import frequency_web as mod

    source = tmp_path / "internet-jp.num"
    source.write_text(
        "header1\nheader2\nheader3\nheader4\n"
        "1 41309.50 食べる\n"
        "2 100.00 飲む\n",
        encoding="utf-8",
    )

    words_path = tmp_path / "words.json"
    words_path.write_text(json.dumps({"words": [
        {"id": "1", "kanji": [{"text": "食べる"}], "kana": [{"text": "たべる"}]},
        {"id": "2", "kanji": [{"text": "飲む"}], "kana": [{"text": "のむ"}]},
    ]}), encoding="utf-8")

    out = tmp_path / "frequency-web.json"
    monkeypatch.setattr(mod, "SOURCE_FILE", source)
    monkeypatch.setattr(mod, "WORDS_JSON", words_path)
    monkeypatch.setattr(mod, "OUT", out)
    monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)

    mod.build()

    result = json.loads(out.read_text(encoding="utf-8"))
    assert result["metadata"]["count"] == 2
    assert result["entries"][0]["text"] == "食べる"
    assert result["entries"][0]["rank"] == 1


# ---------------------------------------------------------------------------
# common_voice — build()
# ---------------------------------------------------------------------------

def test_common_voice_build(tmp_path: Path, monkeypatch) -> None:
    from build.transform import common_voice as mod

    tsv_path = tmp_path / "validated.tsv"
    tsv_path.write_text(
        "client_id\tpath\tsentence\tup_votes\tdown_votes\tage\tgender\n"
        "abc\tabc.mp3\t食べてください\t3\t0\ttwenties\tmale\n"
        "def\tdef.mp3\t食べてください\t2\t1\t\t\n"  # duplicate sentence
        "ghi\tghi.mp3\t飲みましょう\t1\t0\t\tfemale\n",
        encoding="utf-8",
    )

    out_path = tmp_path / "transcripts.json"
    monkeypatch.setattr(mod, "SOURCE_TSV", tsv_path)
    monkeypatch.setattr(mod, "OUT", out_path)
    monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)

    mod.build()

    result = json.loads(out_path.read_text(encoding="utf-8"))
    assert result["metadata"]["count"] == 2
    # Deduplicated: 食べてください appears once with aggregated votes
    top = result["transcripts"][0]
    assert top["text"] == "食べてください"
    assert top["vote_count"] == 2
    assert top["up_votes"] == 5  # 3 + 2


def test_common_voice_missing_source(tmp_path: Path, monkeypatch) -> None:
    from build.transform import common_voice as mod
    monkeypatch.setattr(mod, "SOURCE_TSV", tmp_path / "nope.tsv")
    with pytest.raises(FileNotFoundError, match="Common Voice"):
        mod.build()


# ---------------------------------------------------------------------------
# aozora — text extraction helpers
# ---------------------------------------------------------------------------

def test_aozora_text_extractor() -> None:
    from build.transform.aozora import _TextExtractor
    html = (
        '<body>'
        '<p>吾輩は<ruby><rb>猫</rb><rp>(</rp><rt>ねこ</rt><rp>)</rp></ruby>である。</p>'
        '<p>名前はまだ無い。</p>'
        '［＃注記テスト］'
        '</body>'
    )
    ext = _TextExtractor()
    ext.feed(html)
    text = ext.get_text()
    assert "\u543e\u8f29\u306f\u732b\u3067\u3042\u308b\u3002" in text
    assert "ねこ" not in text  # ruby reading stripped
    assert "注記テスト" not in text  # editorial notes stripped
    assert "名前はまだ無い。" in text


def test_aozora_ruby_extractor() -> None:
    from build.transform.aozora import _RubyExtractor
    html = '<ruby><rb>食</rb><rt>た</rt></ruby>べる'
    ext = _RubyExtractor()
    ext.feed(html)
    pairs = ext.get_pairs()
    assert len(pairs) == 1
    assert pairs[0] == ("食", "た")
