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
from build.pipeline import BUILD_DATE

REPO_ROOT = Path(__file__).resolve().parents[2]
KANJI_JSON = REPO_ROOT / "data" / "core" / "kanji.json"
WORDS_JSON = REPO_ROOT / "data" / "core" / "words.json"
WORDS_FULL_JSON = REPO_ROOT / "data" / "core" / "words-full.json"
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


def _build_reading_to_words(words_data: dict) -> dict[str, list[str]]:
    """Build a kana-reading → word ID reverse lookup.

    For each word, every kana reading is mapped to that word's ID. This
    enables IME-style lookup: given a reading (e.g., "はし"), retrieve
    all word IDs that have that reading (橋, 箸, 端, etc.).

    Duplicate IDs under the same reading are suppressed.
    """
    reading_to_words: dict[str, list[str]] = {}
    for w in words_data.get("words", []):
        wid = w.get("id", "")
        if not wid:
            continue
        seen: set[str] = set()
        for kana in w.get("kana", []) or []:
            text = kana.get("text", "")
            if text and text not in seen:
                seen.add(text)
                reading_to_words.setdefault(text, []).append(wid)
    return reading_to_words


def _write_xref(out_path: Path, mapping: dict, direction: str, key_type: str, value_type: str, source_files: list[str], notes: dict | None = None, extra_metadata: dict | None = None) -> None:
    """Write a single cross-reference file per schemas/cross-refs.schema.json.

    Keys in *mapping* are sorted for deterministic output — the built
    JSON is byte-identical across runs regardless of dict insertion order.
    """
    # Sort mapping keys for deterministic output.
    mapping = dict(sorted(mapping.items()))
    output_metadata = {
        "generated": BUILD_DATE,
        "count": len(mapping),
        "direction": direction,
        "key_type": key_type,
        "value_type": value_type,
        "source_files": source_files,
        "field_notes": notes or {},
        "source": (
            "Derived cross-reference built from "
            + ", ".join(source_files)
            + " by build/transform/cross_links.py."
        ),
        "license": (
            "CC-BY-SA 4.0. Inherits from the source files (EDRDG License / "
            "CC-BY-SA 4.0) and the pipeline code license (CC-BY-SA 4.0). "
            "See LICENSE and ATTRIBUTION.md for upstream details."
        ),
    }
    if extra_metadata:
        output_metadata.update(extra_metadata)
    output = {
        "metadata": output_metadata,
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
    kanji_data = _load_json(KANJI_JSON)
    kanji_char_set = {k["character"] for k in kanji_data.get("kanji", [])}

    kanji_to_words, word_to_kanji, word_to_sentences = _build_word_cross_refs(words_data)
    reading_to_words = _build_reading_to_words(words_data)
    print(
        f"[xref]     kanji→words: {len(kanji_to_words):,}  "
        f"words→kanji: {len(word_to_kanji):,}  "
        f"words→sentences: {len(word_to_sentences):,}  "
        f"reading→words: {len(reading_to_words):,}"
    )

    # D5 fix: characters that appear in word kanji writings but are not in
    # kanji.json are "orphan" references. Record the count (and the specific
    # characters, up to a limit) in the kanji-to-words.json metadata so
    # consumers can detect this integrity gap at read time.
    orphan_chars = sorted(ch for ch in kanji_to_words if ch not in kanji_char_set)
    if orphan_chars:
        print(
            f"[xref]     WARNING: {len(orphan_chars)} characters in kanji-to-words "
            f"are not in kanji.json: {''.join(orphan_chars[:20])}"
            + ("..." if len(orphan_chars) > 20 else "")
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
        {
            "mapping": "Note: scope is the common-subset words.json. For the full 216k entries, re-run the pipeline against words-full.json or query that file directly.",
            "orphan_chars": "Characters that appear in a word's kanji writing but are not present in data/core/kanji.json. These are rare/archaic CJK characters that JMdict uses but KANJIDIC2 does not index. Consumers joining this file with kanji.json should handle the orphan case (lookup will miss).",
        },
        extra_metadata={
            "orphan_count": len(orphan_chars),
            "orphan_chars": orphan_chars,
        },
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
    _write_xref(
        OUT_DIR / "reading-to-words.json",
        reading_to_words,
        "Kana reading → list of word IDs with that reading (IME-style reverse lookup).",
        "reading",
        "word_id",
        ["data/core/words.json"],
        {"mapping": "Each kana reading maps to all word IDs that include it as a kana writing. Use for dictionary-style lookup by pronunciation."},
    )

    # Full-JMdict cross-references (gitignored, built on demand alongside
    # words-full.json). These cover the entire 216k-entry JMdict, not just
    # the 23k common subset. Much higher kanji-to-words coverage.
    if WORDS_FULL_JSON.exists():
        print("[xref]     building full-JMdict cross-references (from words-full.json)")
        words_full_data = _load_json(WORDS_FULL_JSON)
        full_k2w, full_w2k, full_w2s = _build_word_cross_refs(words_full_data)
        full_r2w = _build_reading_to_words(words_full_data)
        full_orphans = sorted(ch for ch in full_k2w if ch not in kanji_char_set)
        print(
            f"[xref]     full: kanji→words: {len(full_k2w):,}  "
            f"words→kanji: {len(full_w2k):,}  "
            f"words→sentences: {len(full_w2s):,}  "
            f"reading→words: {len(full_r2w):,}"
        )
        _write_xref(
            OUT_DIR / "kanji-to-words-full.json",
            full_k2w,
            "Kanji character → list of ALL word IDs (full 216k JMdict, not just common subset).",
            "kanji_char", "word_id",
            ["data/core/words-full.json"],
            extra_metadata={"orphan_count": len(full_orphans), "orphan_chars": full_orphans[:50]},
        )
        _write_xref(
            OUT_DIR / "word-to-kanji-full.json",
            full_w2k,
            "Word ID → list of kanji characters (full JMdict).",
            "word_id", "kanji_char",
            ["data/core/words-full.json"],
        )
        _write_xref(
            OUT_DIR / "reading-to-words-full.json",
            full_r2w,
            "Kana reading → list of word IDs (full JMdict).",
            "reading", "word_id",
            ["data/core/words-full.json"],
        )
