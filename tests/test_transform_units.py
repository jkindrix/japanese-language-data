"""Unit tests for transformer functions (not integration tests against
built data files).

Rationale: the rest of the test suite exercises the transformer code
indirectly through built-data invariants. A subtle transformer bug has
to actually corrupt data to be caught that way. This file provides
function-level unit tests that run against the transformer logic in
isolation with canonical inputs, catching regressions earlier than the
data-integrity layer.

Scope for v0.4.x: conjugations._conjugate_godan for the edge cases that
previously regressed (B1, D1). This can be expanded to cover other
transformer functions (_extract_wikitable, _parse_row_cells, etc.) in
future patches.
"""

from __future__ import annotations

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
