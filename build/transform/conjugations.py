"""Conjugation table transform.

Auto-generates conjugation tables for Japanese verbs and adjectives
from JMdict entries using formal conjugation rules. Because the rules
are deterministic and well-documented, the generated tables do not
require native-speaker review — any incorrectness indicates a bug in
the rule implementation.

Input: ``sources/jmdict-simplified/jmdict-examples-eng.json.tgz``
Output: ``data/grammar/conjugations.json`` conforming to
``schemas/conjugations.schema.json``.

Supported word classes:
    * v1 — Ichidan (一段) verbs. Conjugate by dropping the final る.
    * v5u through v5m — Godan (五段) verbs by ending vowel/consonant.
    * v5r — Godan verbs ending in る (distinguished from v1 by POS).
    * vk — Kuru (来る) irregular.
    * vs-i — Suru-verb (compound -する).
    * adj-i — い-adjective.
    * adj-na — な-adjective (conjugates via copula forms).

For ichidan and godan verbs, this module generates:
    dictionary (plain non-past)
    polite_nonpast (-masu)
    polite_past (-mashita)
    polite_negative (-masen)
    polite_past_negative (-masendeshita)
    te_form (-te)
    ta_form (-ta)
    nai_form (-nai)
    nakatta_form (-nakatta)
    potential (-eru / -rareru)
    passive (-areru / -rareru)
    causative (-aseru / -saseru)
    imperative
    volitional (-ou / -you)
    conditional_ba (-ba)
    conditional_tara (-tara)

For i-adjectives: non-past, negative, past, past negative, adverbial, te-form.
For na-adjectives: covered via the copula.

Only entries that have a matching word class in their JMdict senses
and a kana reading are included. Entries with multiple senses having
different word classes receive a conjugation table for each applicable
class (rare; most entries have a single class).
"""

from __future__ import annotations
import logging

import json
from pathlib import Path
from build.pipeline import BUILD_DATE
from build.utils import load_json_from_tgz, is_common

log = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parents[2]
SOURCE_TGZ = REPO_ROOT / "sources" / "jmdict-simplified" / "jmdict-examples-eng.json.tgz"
OUT = REPO_ROOT / "data" / "grammar" / "conjugations.json"

# Vowel mappings for godan conjugation. Index by the final kana of the
# dictionary form (in u-row) to get the corresponding a-row, i-row,
# e-row, and o-row kana for conjugation.
# Each entry: u_kana -> (a_kana, i_kana, e_kana, o_kana)
GODAN_VOWEL_MAP: dict[str, tuple[str, str, str, str]] = {
    "う": ("わ", "い", "え", "お"),  # Note: わ, not あ, for historical reasons
    "く": ("か", "き", "け", "こ"),
    "ぐ": ("が", "ぎ", "げ", "ご"),
    "す": ("さ", "し", "せ", "そ"),
    "つ": ("た", "ち", "て", "と"),
    "ぬ": ("な", "に", "ね", "の"),
    "ぶ": ("ば", "び", "べ", "ぼ"),
    "む": ("ま", "み", "め", "も"),
    "る": ("ら", "り", "れ", "ろ"),
}

# JMdict POS tag → final kana expected for godan verbs
GODAN_POS_TO_ENDING = {
    "v5u": "う",
    "v5k": "く",
    "v5g": "ぐ",
    "v5s": "す",
    "v5t": "つ",
    "v5n": "ぬ",
    "v5b": "ぶ",
    "v5m": "む",
    "v5r": "る",
    # Special-ending godan classes (D1 fix). These share a base u-row
    # ending with a standard godan class but have irregular forms that
    # are applied as per-POS overrides in _conjugate_godan().
    "v5k-s": "く",   # 行く-style: te/ta use って/った
    "v5u-s": "う",   # 問う-style: te/ta use うて/うた
    "v5aru": "る",   # Honorific: いらっしゃる family; i-stem and imperative use い
    "v5r-i": "る",   # ある: suppletive negative (ない/なかった)
}

# Godan te-form and ta-form are irregular depending on ending:
#   う/つ/る → って/った
#   ぬ/ぶ/む → んで/んだ
#   く → いて/いた  (except 行く → 行って/行った, handled separately)
#   ぐ → いで/いだ
#   す → して/した
TE_FORM_TRANSFORMS: dict[str, tuple[str, str]] = {
    "う": ("って", "った"),
    "つ": ("って", "った"),
    "る": ("って", "った"),
    "ぬ": ("んで", "んだ"),
    "ぶ": ("んで", "んだ"),
    "む": ("んで", "んだ"),
    "く": ("いて", "いた"),
    "ぐ": ("いで", "いだ"),
    "す": ("して", "した"),
}


def _conjugate_ichidan(stem: str) -> dict[str, str]:
    """Ichidan verbs drop the final る and add simple endings."""
    # stem includes the る; we work with the part before it
    root = stem[:-1]  # e.g., "食べる" -> "食べ"
    return {
        "dictionary": stem,
        "polite_nonpast": root + "ます",
        "polite_past": root + "ました",
        "polite_negative": root + "ません",
        "polite_past_negative": root + "ませんでした",
        "te_form": root + "て",
        "ta_form": root + "た",
        "nai_form": root + "ない",
        "nakatta_form": root + "なかった",
        "potential": root + "られる",
        "passive": root + "られる",
        "causative": root + "させる",
        "imperative": root + "ろ",
        "volitional": root + "よう",
        "conditional_ba": root + "れば",
        "conditional_tara": root + "たら",
    }


def _conjugate_godan(stem: str, pos: str) -> dict[str, str] | None:
    """Godan verbs conjugate by shifting the vowel row of the final kana."""
    ending = GODAN_POS_TO_ENDING.get(pos)
    if not ending:
        return None
    if not stem.endswith(ending):
        # Defensive: stem must actually end with the expected kana
        return None
    root = stem[:-1]
    a_kana, i_kana, e_kana, o_kana = GODAN_VOWEL_MAP[ending]
    te, ta = TE_FORM_TRANSFORMS[ending]

    # Per-POS overrides for te/ta forms on special-ending godan classes (D1 fix)
    if pos == "v5k-s":
        # 行く, 逝く, 往く use って/った, not いて/いた
        te, ta = "って", "った"
    elif pos == "v5u-s":
        # 問う, 請う use うて/うた, not って/った
        te, ta = "うて", "うた"

    forms = {
        "dictionary": stem,
        "polite_nonpast": root + i_kana + "ます",
        "polite_past": root + i_kana + "ました",
        "polite_negative": root + i_kana + "ません",
        "polite_past_negative": root + i_kana + "ませんでした",
        "te_form": root + te,
        "ta_form": root + ta,
        "nai_form": root + a_kana + "ない",
        "nakatta_form": root + a_kana + "なかった",
        "potential": root + e_kana + "る",
        "passive": root + a_kana + "れる",
        "causative": root + a_kana + "せる",
        "imperative": root + e_kana,
        "volitional": root + o_kana + "う",
        "conditional_ba": root + e_kana + "ば",
        "conditional_tara": root + ta + "ら",
    }

    # Per-POS overrides that affect multiple form types (D1 fix)
    if pos == "v5aru":
        # Honorific godan: いらっしゃる, ござる, なさる, おっしゃる.
        # i-stem and imperative are い (not り) in these four verbs.
        forms["polite_nonpast"] = root + "います"
        forms["polite_past"] = root + "いました"
        forms["polite_negative"] = root + "いません"
        forms["polite_past_negative"] = root + "いませんでした"
        forms["imperative"] = root + "い"
    elif pos == "v5r-i":
        # "ある family" — the bare verb ある plus compounds that end in ある
        # (e.g., ことがある, である, でもある). The suppletive negative ない
        # REPLACES the final ある portion of the stem. For bare ある this
        # produces "" + "ない" = "ない"; for ことがある it produces
        # "ことが" + "ない" = "ことがない".
        #
        # B1 fix: the previous version set forms["nai_form"] = "ない" as a
        # literal, which was correct for bare ある but wrong for compounds.
        if stem.endswith("ある"):
            prefix = stem[:-2]
            forms["nai_form"] = prefix + "ない"
            forms["nakatta_form"] = prefix + "なかった"
            # Compound v5r-i entries (ことがある, である, でもある) do not
            # have well-formed potential/passive/causative/imperative/
            # volitional/conditional_ba forms — the bare verb ある is
            # itself restricted in these and compounds inherit the
            # restriction. The regular godan-r derivation produced
            # nonsensical output like ことがあれ (imperative of 事がある).
            # Blank them so downstream consumers can treat empty string
            # as "form not well-defined" instead of shipping wrong data.
            if prefix:
                for f in ("potential", "passive", "causative",
                          "imperative", "volitional", "conditional_ba"):
                    forms[f] = ""

    return forms


def _conjugate_suru_compound(stem: str) -> dict[str, str]:
    """Suru-verb compounds — conjugate the -する portion irregularly."""
    if not stem.endswith("する"):
        return {}
    root = stem[:-2]
    return {
        "dictionary": stem,
        "polite_nonpast": root + "します",
        "polite_past": root + "しました",
        "polite_negative": root + "しません",
        "polite_past_negative": root + "しませんでした",
        "te_form": root + "して",
        "ta_form": root + "した",
        "nai_form": root + "しない",
        "nakatta_form": root + "しなかった",
        "potential": root + "できる",
        "passive": root + "される",
        "causative": root + "させる",
        "imperative": root + "しろ",
        "volitional": root + "しよう",
        "conditional_ba": root + "すれば",
        "conditional_tara": root + "したら",
    }


def _conjugate_kuru() -> dict[str, str]:
    """The irregular verb くる."""
    return {
        "dictionary": "くる",
        "polite_nonpast": "きます",
        "polite_past": "きました",
        "polite_negative": "きません",
        "polite_past_negative": "きませんでした",
        "te_form": "きて",
        "ta_form": "きた",
        "nai_form": "こない",
        "nakatta_form": "こなかった",
        "potential": "こられる",
        "passive": "こられる",
        "causative": "こさせる",
        "imperative": "こい",
        "volitional": "こよう",
        "conditional_ba": "くれば",
        "conditional_tara": "きたら",
    }


def _conjugate_i_adjective(stem: str) -> dict[str, str] | None:
    """い-adjectives. Stem must end in い (but not -しい from な-adj historical)."""
    if not stem.endswith("い"):
        return None
    root = stem[:-1]
    return {
        "dictionary": stem,
        "negative": root + "くない",
        "past": root + "かった",
        "past_negative": root + "くなかった",
        "adverbial": root + "く",
        "te_form": root + "くて",
        "conditional_ba": root + "ければ",
        "conditional_tara": root + "かったら",
    }


def _conjugate_na_adjective(stem: str) -> dict[str, str]:
    """な-adjectives conjugate via the copula. Stem is the bare form."""
    return {
        "dictionary": stem + "だ",
        "polite_nonpast": stem + "です",
        "polite_past": stem + "でした",
        "polite_negative": stem + "ではありません",
        "polite_past_negative": stem + "ではありませんでした",
        "te_form": stem + "で",
        "nai_form": stem + "ではない",
        "attributive": stem + "な",  # Used to modify nouns
    }


def _load_source() -> dict:
    return load_json_from_tgz(SOURCE_TGZ)


def _is_common(word: dict) -> bool:
    return is_common(word)


def _longest_common_suffix_length(a: str, b: str) -> int:
    """Return the length of the longest common suffix between two strings.

    Used by the verb/adj-i display_forms heuristic to find where a
    kanji-prefix dictionary form diverges from its kana reading. For
    example, for 食べる / たべる, the common suffix is べる (length 2)
    and the kanji prefix is 食 (length 1).
    """
    i = 0
    while i < len(a) and i < len(b) and a[-1 - i] == b[-1 - i]:
        i += 1
    return i


def _replace_prefix_in_forms(
    forms: dict[str, str],
    old_prefix: str,
    new_prefix: str,
) -> dict[str, str]:
    """Return a new dict where every form that starts with ``old_prefix``
    has that prefix replaced with ``new_prefix``. Forms that don't start
    with ``old_prefix`` are kept unchanged (this is never wrong, only
    sometimes suboptimal — e.g., くる → きます where the kanji-reading
    stem shifts). Empty forms stay empty.
    """
    result: dict[str, str] = {}
    for name, form in forms.items():
        if not form:
            result[name] = form
        elif form.startswith(old_prefix):
            result[name] = new_prefix + form[len(old_prefix):]
        else:
            result[name] = form
    return result


def _display_forms_adj_na(
    dictionary_form: str,
    reading: str,
    forms: dict[str, str],
) -> dict[str, str]:
    """Class-aware branch for な-adjectives.

    Every adj-na form is ``reading + copula`` (です / だ / でした / etc.),
    so the full reading prefix is replaced with the dictionary_form.
    This handles compound readings like 大切 (たいせつ) → 大切です where
    the kanji and kana share no trailing character.
    """
    return _replace_prefix_in_forms(forms, old_prefix=reading, new_prefix=dictionary_form)


def _display_forms_common_suffix(
    dictionary_form: str,
    reading: str,
    forms: dict[str, str],
) -> dict[str, str]:
    """Common-suffix heuristic for verbs, adj-i, and other classes.

    Find the longest common suffix between dictionary_form and reading;
    the dictionary_form prefix before that is the kanji prefix, and the
    reading prefix before the same position is what conjugated forms
    begin with. Replace the reading prefix with the kanji prefix in
    each form.

    Returns a verbatim copy of ``forms`` when:
        * the common suffix is empty (nothing to align on)
        * the kanji prefix is empty (pure-kana dictionary form)
    """
    common_suffix_len = _longest_common_suffix_length(dictionary_form, reading)
    if common_suffix_len == 0:
        return dict(forms)
    kanji_prefix = dictionary_form[:-common_suffix_len]
    reading_prefix = reading[:-common_suffix_len]
    if not kanji_prefix:
        return dict(forms)
    return _replace_prefix_in_forms(forms, old_prefix=reading_prefix, new_prefix=kanji_prefix)


def _compute_display_forms(
    dictionary_form: str,
    reading: str,
    forms: dict[str, str],
    cls: str,
) -> dict[str, str]:
    """Return a companion dict to ``forms`` with the kanji prefix of the
    dictionary form preserved where possible.

    Dispatches to a class-specific helper:
        * ``adj-na`` uses the full-reading-prefix replacement strategy
          (because adj-na forms are always reading + copula)
        * every other class uses the longest-common-suffix heuristic

    For pure-kana dictionary forms, display_forms equals forms (no kanji
    to preserve). For forms whose leading characters don't match the
    expected reading prefix (e.g., くる → きます, where the kanji reading
    shifts between stems), the original kana form is preserved as-is.
    This is never wrong, only sometimes suboptimal.
    """
    if dictionary_form == reading:
        return dict(forms)
    if cls == "adj-na":
        return _display_forms_adj_na(dictionary_form, reading, forms)
    return _display_forms_common_suffix(dictionary_form, reading, forms)


def build() -> None:
    log.info(f"loading {SOURCE_TGZ.name}")
    source = _load_source()
    upstream_words = source.get("words", [])

    # Filter to common entries only (matching data/core/words.json)
    entries: list[dict] = []
    skipped = 0
    by_class: dict[str, int] = {}

    for w in upstream_words:
        if not _is_common(w):
            continue
        # Choose the primary kana reading as the conjugation stem
        kana_list = w.get("kana", []) or []
        if not kana_list:
            continue
        reading = kana_list[0].get("text", "")
        if not reading:
            continue
        primary_kanji = w.get("kanji", [{}])[0].get("text", "") if w.get("kanji") else ""
        wid = str(w.get("id", ""))

        # Determine word class from sense part-of-speech tags
        classes_seen: set[str] = set()
        for sense in w.get("sense", []) or []:
            for pos in sense.get("partOfSpeech", []) or []:
                classes_seen.add(pos)

        for cls in sorted(classes_seen):
            forms: dict[str, str] = {}
            if cls == "v1":
                forms = _conjugate_ichidan(reading)
            elif cls in GODAN_POS_TO_ENDING:
                result = _conjugate_godan(reading, cls)
                if result is not None:
                    forms = result
            elif cls == "vs-i":
                forms = _conjugate_suru_compound(reading)
            elif cls == "vk":
                # The only vk is くる
                if reading in ("くる", "来る"):
                    forms = _conjugate_kuru()
            elif cls == "adj-i":
                result = _conjugate_i_adjective(reading)
                if result is not None:
                    forms = result
            elif cls == "adj-na":
                forms = _conjugate_na_adjective(reading)

            if forms:
                dictionary_form = primary_kanji or reading
                entries.append({
                    "id": wid,
                    "dictionary_form": dictionary_form,
                    "reading": reading,
                    "class": cls,
                    "forms": forms,
                    "display_forms": _compute_display_forms(
                        dictionary_form, reading, forms, cls
                    ),
                })
                by_class[cls] = by_class.get(cls, 0) + 1
            else:
                skipped += 1

    log.info(f"generated {len(entries):,} conjugation tables")
    for cls in sorted(by_class):
        log.info(f"{cls}: {by_class[cls]:,}")
    if skipped:
        log.info(f"skipped {skipped:,} candidates (word class not supported or form mismatch)")

    output = {
        "metadata": {
            "source": "Auto-generated from JMdict verb and adjective entries",
            "license": "CC-BY-SA 4.0",
            "generated": BUILD_DATE,
            "count": len(entries),
            "conjugation_rules_reference": (
                "Conjugation rules encoded directly in build/transform/conjugations.py. "
                "They follow the standard ichidan/godan conjugation rules taught in any "
                "introductory Japanese grammar reference. Any incorrectness is a bug in "
                "the rule implementation, not in the data."
            ),
            "attribution": (
                "Conjugation tables auto-generated from JMdict verb and adjective "
                "entries (EDRDG License, CC-BY-SA 4.0). Rules are formally defined "
                "and deterministic; no native-speaker review is required for the "
                "conjugation logic itself."
            ),
            "field_notes": {
                "id": "JMdict entry ID (from words.json).",
                "dictionary_form": "The kanji writing of the lemma, or kana if kana-only.",
                "reading": "The kana reading used as the conjugation stem.",
                "class": "JMdict POS tag indicating the word class used for conjugation.",
                "forms": "Map from form name to conjugated kana form. Specific forms available depend on the word class.",
                "v1": "Ichidan verbs: 食べる, 見る, 起きる, etc.",
                "v5u-v5m": "Godan verbs grouped by the kana ending of the dictionary form.",
                "adj-i": "い-adjectives: 高い, 新しい, 小さい, etc.",
                "adj-na": "な-adjectives: 静か, 元気, etc. (conjugate via the copula).",
                "potential_ichidan_note": "Modern colloquial Japanese often drops the ら in ichidan potential forms (ら抜き言葉), e.g., 食べられる → 食べれる. We generate the traditional form; the ら-less form is grammatically nonstandard but widely used.",
            },
        },
        "entries": entries,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
        f.write("\n")
    log.info(f"wrote {OUT.relative_to(REPO_ROOT)}")
