"""Example sentences transform.

Extracts example sentences from the jmdict-examples variant (which embeds
editor-curated Tatoeba sentences pre-linked to specific JMdict senses)
and writes them as a standalone sentence corpus file.

Input: ``sources/jmdict-simplified/jmdict-examples-eng.json.tgz``

Output: ``data/corpus/sentences.json`` conforming to
``schemas/sentence.schema.json``.

Sentences are deduplicated by Tatoeba sentence ID and emitted with a
``tatoeba-{n}`` prefixed ID (matching the project-wide ``{source}-{n}``
convention). A single sentence referenced by multiple word senses
appears exactly once in the output. The word → sentence cross-reference
is generated separately by the cross_links transform.

All sentences in this file are marked ``curated: true`` because they are
editor-selected via JMdict's curation process. Phase 2 or later may add
an unfiltered sentences file from the full Tatoeba export.
"""

from __future__ import annotations
import logging

import json
import tarfile
from pathlib import Path
from build.pipeline import BUILD_DATE

log = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parents[2]
SOURCE_TGZ = REPO_ROOT / "sources" / "jmdict-simplified" / "jmdict-examples-eng.json.tgz"
OUT = REPO_ROOT / "data" / "corpus" / "sentences.json"


def _load_source() -> dict:
    with tarfile.open(SOURCE_TGZ, "r:gz") as tf:
        for member in tf.getmembers():
            if member.name.endswith(".json"):
                f = tf.extractfile(member)
                if f is None:
                    raise RuntimeError(f"Cannot extract {member.name}")
                return json.loads(f.read().decode("utf-8"))
    raise RuntimeError(f"No JSON file found in {SOURCE_TGZ}")


def build() -> None:
    log.info(f"loading {SOURCE_TGZ.name}")
    source = _load_source()
    upstream_words = source.get("words", [])

    # Deduplicate sentences by Tatoeba ID.
    seen: dict[str, dict] = {}
    total_refs = 0
    for w in upstream_words:
        for sense in w.get("sense", []) or []:
            for ex in sense.get("examples", []) or []:
                total_refs += 1
                src = ex.get("source", {}) or {}
                if src.get("type") != "tatoeba":
                    continue
                sid = str(src.get("value", ""))
                if not sid or sid in seen:
                    continue

                japanese = ""
                english = ""
                for sent in ex.get("sentences", []) or []:
                    lang = sent.get("lang", "")
                    text = sent.get("text", "")
                    if lang == "jpn":
                        japanese = text
                    elif lang == "eng":
                        english = text

                if not japanese:
                    # Skip malformed entries with no Japanese text
                    continue

                seen[sid] = {
                    "id": f"tatoeba-{sid}",
                    "japanese": japanese,
                    "english": english,
                    "translation_id": None,
                    "curated": True,
                    "license_flag": "CC-BY-2.0-FR",
                    "has_audio": False,
                    "japanese_contributor": None,
                    "english_contributor": None,
                }

    sentences = sorted(seen.values(), key=lambda s: int(s["id"].removeprefix("tatoeba-")) if s["id"].removeprefix("tatoeba-").isdigit() else 0)
    log.info(f"{total_refs:,} upstream references, {len(sentences):,} unique sentences")

    output = {
        "metadata": {
            "source": "Tatoeba via JMdict editor-curated examples (jmdict-examples-eng)",
            "source_url": "https://tatoeba.org/",
            "license": "CC-BY 2.0 FR (sentence text); subset under CC0 1.0",
            "source_version": source.get("version", ""),
            "upstream_dict_date": source.get("dictDate", ""),
            "generated": BUILD_DATE,
            "count": len(sentences),
            "attribution": (
                "Example sentences from the Tatoeba Project (https://tatoeba.org/) "
                "under CC-BY 2.0 FR. These sentences were selected and linked to "
                "JMdict senses by JMdict editors. Individual sentences may have "
                "different contributors; sentence IDs are preserved to allow "
                "upstream lookup at https://tatoeba.org/en/sentences/show/<id>."
            ),
            "field_notes": {
                "id": "Sentence ID in the format 'tatoeba-{n}' where n is the Tatoeba sentence ID. View the original at https://tatoeba.org/en/sentences/show/{n} (strip the 'tatoeba-' prefix). All sentence IDs across the project use a '{source}-{n}' convention for source identification.",
                "japanese": "The Japanese sentence text as provided by Tatoeba.",
                "english": "The English translation as linked by JMdict editors. May be empty if no English translation was associated.",
                "curated": "True for these entries because they are editor-selected from JMdict. A later phase may add unfiltered Tatoeba sentences with curated=false.",
                "license_flag": "Default CC-BY 2.0 FR. Individual Tatoeba sentences may be under CC0 1.0; we mark the default here and defer per-sentence license tracking to a later phase.",
                "has_audio": "Whether Tatoeba has an audio recording. We do not currently populate this; a later phase may cross-reference Tatoeba's audio export.",
                "japanese_contributor / english_contributor": "Not currently populated. Tatoeba provides this via the full corpus export, which is a Phase 2+ candidate.",
            },
        },
        "sentences": sentences,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
        f.write("\n")
    log.info(f"wrote {OUT.relative_to(REPO_ROOT)} ({len(sentences):,} entries)")
