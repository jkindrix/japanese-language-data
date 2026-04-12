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

    * conjugations._conjugate_godan        (irregular godan edge cases)
    * radicals._parse_kangxi_wikitext      (Wikipedia wikitable parser)
    * pitch._count_morae                   (small-kana / sokuon / long vowel)
    * stroke_order._count_strokes          (SVG path counting)
    * words._load_vocab_jlpt_map           (D4 easier-level-wins tie-break)
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
