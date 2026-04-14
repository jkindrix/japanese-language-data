"""Export the dataset as Anki .apkg flashcard decks.

Generates three subdecks:
    * Vocabulary — word + reading → definitions, JLPT, pitch accent
    * Kanji — character → readings, meanings, stroke count, grade
    * Grammar — pattern → meaning, formation, example sentence

Output: ``dist/japanese-language-data.apkg``

Run via ``just export-anki`` or ``python -m build.export_anki``.

Requires: genanki (pip install genanki)
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import genanki

from build.constants import DATA_DIR, MANIFEST_PATH, REPO_ROOT
from build.pitch_lookup import load_merged_pitch, format_pitch_string

DIST_DIR = REPO_ROOT / "dist"
OUT_APKG = DIST_DIR / "japanese-language-data.apkg"

# Stable model IDs (generated once, never change — Anki uses these to
# track note types across imports)
VOCAB_MODEL_ID = 1607392319
KANJI_MODEL_ID = 1607392320
GRAMMAR_MODEL_ID = 1607392321

# Stable deck IDs
DECK_ID_ROOT = 2059400110
DECK_ID_VOCAB = 2059400111
DECK_ID_KANJI = 2059400112
DECK_ID_GRAMMAR = 2059400113


def _load_json(path: Path) -> dict | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _build_vocab_model() -> genanki.Model:
    return genanki.Model(
        VOCAB_MODEL_ID,
        "JLD Vocabulary",
        fields=[
            {"name": "Word"},
            {"name": "Reading"},
            {"name": "Definitions"},
            {"name": "JLPT"},
            {"name": "Pitch"},
            {"name": "WordID"},
        ],
        templates=[{
            "name": "Word → Meaning",
            "qfmt": (
                '<div style="font-size:48px;text-align:center">{{Word}}</div>'
                '<div style="font-size:24px;text-align:center;color:#666">{{Reading}}</div>'
            ),
            "afmt": (
                '{{FrontSide}}<hr id="answer">'
                '<div style="font-size:20px">{{Definitions}}</div>'
                '<div style="font-size:14px;color:#888;margin-top:8px">'
                '{{#JLPT}}JLPT: {{JLPT}} | {{/JLPT}}'
                '{{#Pitch}}Pitch: {{Pitch}}{{/Pitch}}'
                '</div>'
            ),
        }],
        css=(
            ".card { font-family: 'Noto Sans JP', 'Hiragino Sans', "
            "'Meiryo', sans-serif; }"
        ),
    )


def _build_kanji_model() -> genanki.Model:
    return genanki.Model(
        KANJI_MODEL_ID,
        "JLD Kanji",
        fields=[
            {"name": "Character"},
            {"name": "OnReadings"},
            {"name": "KunReadings"},
            {"name": "Meanings"},
            {"name": "StrokeCount"},
            {"name": "Grade"},
            {"name": "JLPT"},
        ],
        templates=[{
            "name": "Kanji → Readings & Meaning",
            "qfmt": '<div style="font-size:96px;text-align:center">{{Character}}</div>',
            "afmt": (
                '{{FrontSide}}<hr id="answer">'
                '<div style="font-size:18px"><b>ON:</b> {{OnReadings}}</div>'
                '<div style="font-size:18px"><b>KUN:</b> {{KunReadings}}</div>'
                '<div style="font-size:20px;margin-top:8px">{{Meanings}}</div>'
                '<div style="font-size:14px;color:#888;margin-top:8px">'
                'Strokes: {{StrokeCount}} | '
                '{{#Grade}}Grade: {{Grade}} | {{/Grade}}'
                '{{#JLPT}}JLPT: {{JLPT}}{{/JLPT}}'
                '</div>'
            ),
        }],
        css=(
            ".card { font-family: 'Noto Sans JP', 'Hiragino Sans', "
            "'Meiryo', sans-serif; }"
        ),
    )


def _build_grammar_model() -> genanki.Model:
    return genanki.Model(
        GRAMMAR_MODEL_ID,
        "JLD Grammar",
        fields=[
            {"name": "Pattern"},
            {"name": "Meaning"},
            {"name": "Formation"},
            {"name": "Example_JA"},
            {"name": "Example_EN"},
            {"name": "Level"},
        ],
        templates=[{
            "name": "Pattern → Meaning",
            "qfmt": (
                '<div style="font-size:36px;text-align:center">{{Pattern}}</div>'
                '<div style="font-size:14px;text-align:center;color:#888">{{Level}}</div>'
            ),
            "afmt": (
                '{{FrontSide}}<hr id="answer">'
                '<div style="font-size:20px">{{Meaning}}</div>'
                '<div style="font-size:16px;color:#666;margin-top:8px">'
                '<b>Formation:</b> {{Formation}}</div>'
                '<div style="font-size:18px;margin-top:12px">'
                '{{Example_JA}}<br>'
                '<span style="color:#666">{{Example_EN}}</span></div>'
            ),
        }],
        css=(
            ".card { font-family: 'Noto Sans JP', 'Hiragino Sans', "
            "'Meiryo', sans-serif; }"
        ),
    )


def export() -> None:
    """Build the Anki .apkg package."""
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    version = manifest.get("version", "dev")

    vocab_model = _build_vocab_model()
    kanji_model = _build_kanji_model()
    grammar_model = _build_grammar_model()

    deck_vocab = genanki.Deck(DECK_ID_VOCAB, f"Japanese Language Data v{version}::Vocabulary")
    deck_kanji = genanki.Deck(DECK_ID_KANJI, f"Japanese Language Data v{version}::Kanji")
    deck_grammar = genanki.Deck(DECK_ID_GRAMMAR, f"Japanese Language Data v{version}::Grammar")

    # Load enrichment lookups — shared pitch accent loader (union merge)
    # Anki uses word-only key (no reading) since cards are keyed by word text.
    # For words with multiple readings, this picks up all positions across readings.
    merged = load_merged_pitch()
    pitch_lookup: dict[str, str] = {}
    for (word, _reading), positions in merged.items():
        formatted = format_pitch_string(positions)
        if word not in pitch_lookup:
            pitch_lookup[word] = formatted
        else:
            # Union positions across readings for the same word text
            existing = set(int(p) for p in pitch_lookup[word].split("/"))
            existing.update(positions)
            pitch_lookup[word] = format_pitch_string(sorted(existing))

    # Vocabulary cards
    words_data = _load_json(DATA_DIR / "core" / "words.json")
    vocab_count = 0
    if words_data:
        for w in words_data.get("words", []):
            kanji_list = w.get("kanji", []) or []
            kana_list = w.get("kana", []) or []
            word_text = kanji_list[0].get("text", "") if kanji_list else (
                kana_list[0].get("text", "") if kana_list else ""
            )
            reading = kana_list[0].get("text", "") if kana_list else ""

            defs = []
            for sense in w.get("sense", []) or []:
                for gloss in sense.get("gloss", []) or []:
                    t = gloss.get("text", "")
                    if t:
                        defs.append(t)
            if not defs or not word_text:
                continue

            jlpt = w.get("jlpt_waller") or ""
            pitch = pitch_lookup.get(word_text, "")
            wid = str(w.get("id", ""))

            note = genanki.Note(
                model=vocab_model,
                fields=[word_text, reading, "; ".join(defs[:5]), jlpt, pitch, wid],
                tags=[f"jlpt-{jlpt.lower()}" if jlpt else "no-jlpt"],
            )
            deck_vocab.add_note(note)
            vocab_count += 1

    # Kanji cards
    kanji_data = _load_json(DATA_DIR / "core" / "kanji.json")
    kanji_count = 0
    if kanji_data:
        for k in kanji_data.get("kanji", []):
            char = k.get("character", "")
            if not char:
                continue
            readings = k.get("readings", {}) or {}
            meanings = k.get("meanings", {}) or {}
            on = ", ".join(readings.get("on", []) or [])
            kun = ", ".join(readings.get("kun", []) or [])
            en = ", ".join(meanings.get("en", []) or [])
            strokes = str(k.get("stroke_count", ""))
            grade = str(k.get("grade", "")) if k.get("grade") else ""
            jlpt = k.get("jlpt_waller") or ""

            note = genanki.Note(
                model=kanji_model,
                fields=[char, on, kun, en, strokes, grade, jlpt],
                tags=[f"jlpt-{jlpt.lower()}" if jlpt else "no-jlpt",
                      f"grade-{grade}" if grade else "no-grade"],
            )
            deck_kanji.add_note(note)
            kanji_count += 1

    # Grammar cards
    grammar_data = _load_json(DATA_DIR / "grammar" / "grammar.json")
    grammar_count = 0
    if grammar_data:
        for gp in grammar_data.get("grammar_points", []):
            pattern = gp.get("pattern", "")
            meaning = gp.get("meaning_en", "")
            formation = gp.get("formation", "")
            level = gp.get("level", "")
            examples = gp.get("examples", []) or []

            ex_ja = examples[0].get("japanese", "") if examples else ""
            ex_en = examples[0].get("english", "") if examples else ""

            note = genanki.Note(
                model=grammar_model,
                fields=[pattern, meaning, formation, ex_ja, ex_en, level],
                tags=[f"jlpt-{level.lower()}" if level else "no-level"],
            )
            deck_grammar.add_note(note)
            grammar_count += 1

    # Package
    DIST_DIR.mkdir(parents=True, exist_ok=True)
    package = genanki.Package([deck_vocab, deck_kanji, deck_grammar])
    package.write_to_file(str(OUT_APKG))

    size = OUT_APKG.stat().st_size
    print(f"[anki]     vocabulary: {vocab_count:,} cards")
    print(f"[anki]     kanji: {kanji_count:,} cards")
    print(f"[anki]     grammar: {grammar_count:,} cards")
    print(f"[anki]     wrote {OUT_APKG.relative_to(REPO_ROOT)} ({size:,} bytes, {size/1024/1024:.1f} MB)")


def main() -> int:
    export()
    return 0


if __name__ == "__main__":
    sys.exit(main())
