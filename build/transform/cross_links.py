"""Cross-reference generation.

Runs after every per-domain transform has completed and every core and
enrichment file exists in ``data/``. Reads those files and emits the
cross-reference indices in ``data/cross-refs/``.

Generated files:

    * ``data/cross-refs/kanji-to-words.json``
        For each kanji character, the list of word IDs whose entries
        contain that character in any kanji writing.

    * ``data/cross-refs/word-to-kanji.json``
        Inverse: each word ID → list of kanji characters it contains.

    * ``data/cross-refs/word-to-sentences.json``
        Each word ID → list of Tatoeba sentence IDs that illustrate it.
        Populated from the example references embedded in each word's
        senses (from jmdict-examples).

    * ``data/cross-refs/kanji-to-radicals.json``
        Each kanji → its component radicals, from KRADFILE (via
        data/core/radicals.json).

All cross-reference files conform to ``schemas/cross-refs.schema.json``.

The transform reads ``data/core/words.json`` (the common subset) for
the word cross-references. Consumers wanting the full 216k-entry cross-
references can re-run the pipeline with the full ``words-full.json`` as
an alternative input; we emit only the common-subset cross-references
to keep the committed files reasonable in size.
"""

from __future__ import annotations

import json
from pathlib import Path
from datetime import date

REPO_ROOT = Path(__file__).resolve().parents[2]
KANJI_JSON = REPO_ROOT / "data" / "core" / "kanji.json"
WORDS_JSON = REPO_ROOT / "data" / "core" / "words.json"
SENTENCES_JSON = REPO_ROOT / "data" / "corpus" / "sentences.json"
RADICALS_JSON = REPO_ROOT / "data" / "core" / "radicals.json"
OUT_DIR = REPO_ROOT / "data" / "cross-refs"


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _is_kanji_char(ch: str) -> bool:
    """True if ch is in a CJK kanji block (for cross-reference indexing)."""
    code = ord(ch)
    return (
        0x4E00 <= code <= 0x9FFF       # CJK Unified Ideographs
        or 0x3400 <= code <= 0x4DBF    # CJK Extension A
        or 0xF900 <= code <= 0xFAFF    # CJK Compatibility Ideographs
        or 0x20000 <= code <= 0x2A6DF  # CJK Extension B
        or 0x2A700 <= code <= 0x2EBEF  # CJK Extensions C-F
    )


def _build_word_cross_refs(words_data: dict) -> tuple[dict, dict, dict]:
    """Return (kanji_to_words, word_to_kanji, word_to_sentences)."""
    kanji_to_words: dict[str, list[str]] = {}
    word_to_kanji: dict[str, list[str]] = {}
    word_to_sentences: dict[str, list[str]] = {}

    for w in words_data.get("words", []):
        wid = w.get("id", "")
        if not wid:
            continue

        # Extract unique kanji characters from all kanji writings of this word
        seen_chars: list[str] = []
        seen_set: set[str] = set()
        for k in w.get("kanji", []) or []:
            for ch in k.get("text", ""):
                if _is_kanji_char(ch) and ch not in seen_set:
                    seen_set.add(ch)
                    seen_chars.append(ch)

        if seen_chars:
            word_to_kanji[wid] = seen_chars
            for ch in seen_chars:
                kanji_to_words.setdefault(ch, []).append(wid)

        # Extract sentence IDs from all senses
        sentence_ids: list[str] = []
        sentence_set: set[str] = set()
        for sense in w.get("sense", []) or []:
            for ex in sense.get("examples", []) or []:
                sid = ex.get("sentence_id", "")
                if sid and sid not in sentence_set:
                    sentence_set.add(sid)
                    sentence_ids.append(sid)
        if sentence_ids:
            word_to_sentences[wid] = sentence_ids

    return kanji_to_words, word_to_kanji, word_to_sentences


def _write_xref(out_path: Path, mapping: dict, direction: str, key_type: str, value_type: str, source_files: list[str], notes: dict | None = None) -> None:
    """Write a single cross-reference file per schemas/cross-refs.schema.json."""
    output = {
        "metadata": {
            "generated": date.today().isoformat(),
            "count": len(mapping),
            "direction": direction,
            "key_type": key_type,
            "value_type": value_type,
            "source_files": source_files,
            "field_notes": notes or {},
        },
        "mapping": mapping,
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"[xref]     wrote {out_path.relative_to(REPO_ROOT)} ({len(mapping):,} keys)")


def build() -> None:
    missing = []
    if not KANJI_JSON.exists():
        missing.append(str(KANJI_JSON.relative_to(REPO_ROOT)))
    if not WORDS_JSON.exists():
        missing.append(str(WORDS_JSON.relative_to(REPO_ROOT)))
    if not RADICALS_JSON.exists():
        missing.append(str(RADICALS_JSON.relative_to(REPO_ROOT)))
    if missing:
        raise FileNotFoundError(
            f"Cross-links stage requires these files to exist first: {missing}. "
            f"Run the preceding transforms before cross_links."
        )

    print("[xref]     loading words, kanji, radicals")
    words_data = _load_json(WORDS_JSON)
    radicals_data = _load_json(RADICALS_JSON)

    kanji_to_words, word_to_kanji, word_to_sentences = _build_word_cross_refs(words_data)
    print(
        f"[xref]     kanji→words: {len(kanji_to_words):,}  "
        f"words→kanji: {len(word_to_kanji):,}  "
        f"words→sentences: {len(word_to_sentences):,}"
    )

    # kanji-to-radicals comes directly from radicals.json
    kanji_to_radicals = radicals_data.get("kanji_to_radicals", {})
    print(f"[xref]     kanji→radicals: {len(kanji_to_radicals):,}")

    _write_xref(
        OUT_DIR / "kanji-to-words.json",
        kanji_to_words,
        "Kanji character → list of word IDs whose kanji writing contains that character.",
        "kanji_char",
        "word_id",
        ["data/core/words.json"],
        {"mapping": "Note: scope is the common-subset words.json. For the full 216k entries, re-run the pipeline against words-full.json or query that file directly."},
    )
    _write_xref(
        OUT_DIR / "word-to-kanji.json",
        word_to_kanji,
        "Word ID → list of kanji characters appearing in any kanji writing of that word.",
        "word_id",
        "kanji_char",
        ["data/core/words.json"],
    )
    _write_xref(
        OUT_DIR / "word-to-sentences.json",
        word_to_sentences,
        "Word ID → list of Tatoeba sentence IDs from editor-curated examples.",
        "word_id",
        "sentence_id",
        ["data/core/words.json", "data/corpus/sentences.json"],
        {"sentence_ids": "Resolve at https://tatoeba.org/en/sentences/show/<id> for audio, alternative translations, and community discussion."},
    )
    _write_xref(
        OUT_DIR / "kanji-to-radicals.json",
        kanji_to_radicals,
        "Kanji character → list of component radicals (from KRADFILE).",
        "kanji_char",
        "radical_char",
        ["data/core/radicals.json"],
    )
