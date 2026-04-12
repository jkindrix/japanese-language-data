"""Word (JMdict) data transform.

Reads the JMdict examples variant from
``sources/jmdict-simplified/jmdict-examples-eng.json.tgz`` and transforms
it into our schema.

Outputs:
    * ``data/core/words.json`` — common-only subset (~15-20k entries), the
      primary committed file
    * ``data/core/words-full.json`` — full 216k-entry dataset, gitignored
      (150+ MB), built on demand and published as a release artifact

An entry is considered "common" if ANY of its kanji writings or kana
writings have ``common: true`` in the upstream data. This matches the
``jmdict-eng-common`` filter used by scriptin/jmdict-simplified
(news1/ichi1/spec1/gai1 priority markers).

Fields augmented by our transform beyond raw upstream data:
    * ``jlpt_waller`` — null in Phase 1; populated by Phase 2 jlpt transform.
    * ``frequency_media`` — null in Phase 1; populated by Phase 2 frequency
      transform.

Each sense's ``examples`` array is transformed from the upstream nested
structure into our schema's flatter form:

    upstream:  {"source": {"type": "tatoeba", "value": "162365"},
                "text": "<word form>",
                "sentences": [{"lang": "jpn", "text": "..."},
                              {"lang": "eng", "text": "..."}]}

    our form:  {"source": "tatoeba",
                "sentence_id": "162365",
                "word_form": "<word form>",
                "japanese": "...",
                "english": "..."}
"""

from __future__ import annotations

import json
import tarfile
from pathlib import Path
from build.pipeline import BUILD_DATE

REPO_ROOT = Path(__file__).resolve().parents[2]
SOURCE_TGZ = REPO_ROOT / "sources" / "jmdict-simplified" / "jmdict-examples-eng.json.tgz"
OUT_COMMON = REPO_ROOT / "data" / "core" / "words.json"
OUT_FULL = REPO_ROOT / "data" / "core" / "words-full.json"
JLPT_ENRICHMENT = REPO_ROOT / "data" / "enrichment" / "jlpt-classifications.json"


def _load_source() -> dict:
    with tarfile.open(SOURCE_TGZ, "r:gz") as tf:
        for member in tf.getmembers():
            if member.name.endswith(".json"):
                f = tf.extractfile(member)
                if f is None:
                    raise RuntimeError(f"Cannot extract {member.name}")
                return json.loads(f.read().decode("utf-8"))
    raise RuntimeError(f"No JSON file found in {SOURCE_TGZ}")


def _load_vocab_jlpt_map() -> dict[str, str]:
    """Build a jmdict_seq → level map from the vocab portion of jlpt enrichment.

    D4 fix: for jmdict_seq values that appear at multiple JLPT levels (due to
    homographic variants — e.g., 会う at N5 and 遭う at N2 sharing seq 1198180),
    the easier level (higher N-number, closer to beginner) wins. This makes the
    mapping deterministic and pedagogically sensible: a learner encountering the
    common form of the word first sees it at the easiest level it's taught.
    """
    # Lower value = easier level; N5 wins over N1
    LEVEL_ORDER = {"N5": 0, "N4": 1, "N3": 2, "N2": 3, "N1": 4}
    if not JLPT_ENRICHMENT.exists():
        return {}
    data = json.loads(JLPT_ENRICHMENT.read_text(encoding="utf-8"))
    result: dict[str, str] = {}
    for entry in data.get("classifications", []):
        if entry.get("kind") == "vocab":
            seq = entry.get("jmdict_seq", "")
            level = entry.get("level")
            if not seq or not level:
                continue
            if seq in result:
                if LEVEL_ORDER.get(level, 99) < LEVEL_ORDER.get(result[seq], 99):
                    result[seq] = level
            else:
                result[seq] = level
    return result


def _transform_example(ex: dict) -> dict:
    """Transform an upstream example to our schema form."""
    source_obj = ex.get("source", {}) or {}
    source_name = source_obj.get("type", "")
    sentence_id = str(source_obj.get("value", ""))

    japanese = ""
    english = ""
    for sent in ex.get("sentences", []) or []:
        lang = sent.get("lang", "")
        text = sent.get("text", "")
        if lang == "jpn":
            japanese = text
        elif lang == "eng":
            english = text

    return {
        "source": source_name,
        "sentence_id": sentence_id,
        "word_form": ex.get("text", ""),
        "japanese": japanese,
        "english": english,
    }


def _transform_word(w: dict, jlpt_map: dict[str, str] | None = None) -> dict:
    """Transform an upstream JMdict word entry into our schema.

    The upstream structure is already close to our target — we preserve it
    mostly unchanged, adding our augmentation fields and transforming the
    examples sub-structure.
    """
    jlpt_map = jlpt_map or {}
    senses = []
    for s in w.get("sense", []) or []:
        sense = dict(s)  # shallow copy so we don't mutate upstream data
        if "examples" in sense:
            sense["examples"] = [_transform_example(ex) for ex in sense.get("examples", []) or []]
        senses.append(sense)

    wid = str(w.get("id", ""))
    return {
        "id": wid,
        "kanji": list(w.get("kanji", []) or []),
        "kana": list(w.get("kana", []) or []),
        "sense": senses,
        "jlpt_waller": jlpt_map.get(wid),  # None if not classified
        "frequency_media": None,  # Deferred to Phase 4 pending JPDB license clarification
    }


def _is_common(word: dict) -> bool:
    """An entry is 'common' if any of its writings has common=True."""
    for k in word.get("kanji", []) or []:
        if k.get("common"):
            return True
    for k in word.get("kana", []) or []:
        if k.get("common"):
            return True
    return False


def _metadata(source: dict, count: int, filter_note: str, tags: dict) -> dict:
    return {
        "source": "JMdict (examples variant) via scriptin/jmdict-simplified",
        "source_url": "https://github.com/scriptin/jmdict-simplified",
        "license": "CC-BY-SA 4.0 (EDRDG License)",
        "source_version": source.get("version", ""),
        "upstream_dict_date": source.get("dictDate", ""),
        "upstream_languages": source.get("languages", []),
        "upstream_common_only_variant": source.get("commonOnly", False),
        "dictRevisions": source.get("dictRevisions", []),
        "generated": BUILD_DATE,
        "count": count,
        "filter": filter_note,
        "tags": tags,
        "attribution": (
            "This work uses JMdict from the Electronic Dictionary Research "
            "and Development Group (EDRDG), used in conformance with the "
            "Group's license (https://www.edrdg.org/edrdg/licence.html). "
            "Example sentences sourced from the Tatoeba Project "
            "(https://tatoeba.org/) under CC-BY 2.0 FR, selected and linked "
            "by JMdict editors. Ingested via scriptin/jmdict-simplified "
            "(https://github.com/scriptin/jmdict-simplified)."
        ),
        "field_notes": {
            "id": "Unique JMdict entry ID, stable across upstream revisions.",
            "kanji": "Kanji and other non-kana writings. May be empty for kana-only words.",
            "kana": "Kana-only writings with applies-to relations to specific kanji writings.",
            "sense": "Senses = translations plus metadata (parts of speech, fields, dialects, misc).",
            "sense.gloss.lang": "Translation language code (eng=English etc.) per jmdict-simplified convention.",
            "sense.examples": "Editor-curated example sentences from Tatoeba, linked by sentence_id. The sentence_id can be used to look up the original at https://tatoeba.org/en/sentences/show/<id>.",
            "jlpt_waller": "Current N1-N5 level from Jonathan Waller's JLPT lists (tanos.co.uk). For words whose JMdict entry covers multiple homographic variants assigned to different JLPT levels, the easier level (higher N-number, closer to beginner) wins. See the classifications file for all per-variant assignments.",
            "frequency_media": "Rank in modern media corpus (JPDB light novels/anime/drama). Filled in Phase 2. Null in Phase 1 output.",
            "kanji.common and kana.common": "Derived from JMdict priority markers (news1, ichi1, spec1, spec2, gai1). True = common usage.",
        },
    }


def build() -> None:
    """Build words.json (common only) and words-full.json (gitignored)."""
    print(f"[words]    loading {SOURCE_TGZ.name}")
    source = _load_source()
    upstream_words = source.get("words", [])
    upstream_tags = source.get("tags", {}) or {}

    jlpt_map = _load_vocab_jlpt_map()
    if jlpt_map:
        print(f"[words]    found JLPT enrichment: {len(jlpt_map):,} words classified")
    else:
        print("[words]    no JLPT enrichment file; jlpt_waller will be null")

    print(f"[words]    transforming {len(upstream_words):,} entries")
    all_entries = [_transform_word(w, jlpt_map) for w in upstream_words]
    common_entries = [w for w in all_entries if _is_common(w)]
    print(f"[words]    common: {len(common_entries):,}  full: {len(all_entries):,}")

    enriched_jlpt_common = sum(1 for w in common_entries if w.get("jlpt_waller"))
    enriched_jlpt_full = sum(1 for w in all_entries if w.get("jlpt_waller"))
    print(f"[words]    enriched jlpt_waller: common={enriched_jlpt_common:,} full={enriched_jlpt_full:,}")

    OUT_COMMON.parent.mkdir(parents=True, exist_ok=True)

    # Common subset — primary committed file
    output_common = {
        "metadata": _metadata(
            source,
            len(common_entries),
            "Common entries only: any word with at least one kanji or kana writing "
            "flagged common=true in the upstream JMdict priority markers "
            "(news1/ichi1/spec1/spec2/gai1).",
            upstream_tags,
        ),
        "words": common_entries,
    }
    with OUT_COMMON.open("w", encoding="utf-8") as f:
        json.dump(output_common, f, ensure_ascii=False, indent=2)
        f.write("\n")
    size = OUT_COMMON.stat().st_size
    print(f"[words]    wrote {OUT_COMMON.relative_to(REPO_ROOT)} ({size:,} bytes)")

    # Full dataset — gitignored, built on demand
    output_full = {
        "metadata": _metadata(
            source,
            len(all_entries),
            "All JMdict entries (no common filter). Includes archaic, rare, "
            "specialized, and dialectal vocabulary. Built as a separate artifact "
            "due to size (~150 MB); gitignored by default. See docs/build.md.",
            upstream_tags,
        ),
        "words": all_entries,
    }
    with OUT_FULL.open("w", encoding="utf-8") as f:
        json.dump(output_full, f, ensure_ascii=False, indent=2)
        f.write("\n")
    size_full = OUT_FULL.stat().st_size
    print(f"[words]    wrote {OUT_FULL.relative_to(REPO_ROOT)} ({size_full:,} bytes, gitignored)")
