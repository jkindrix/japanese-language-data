"""Shared utilities for build transform modules.

Consolidates functions that were duplicated across multiple transform
modules — tarball extraction, JLPT enrichment loading, and the common-
entry filter. Each transform module should import from here instead of
maintaining its own copy.
"""

from __future__ import annotations

import json
import tarfile
from pathlib import Path

from build.constants import REPO_ROOT


# Default path for JLPT enrichment data (used by load_vocab_jlpt_map).
JLPT_ENRICHMENT = REPO_ROOT / "data" / "enrichment" / "jlpt-classifications.json"


def load_json_from_tgz(tgz_path: Path) -> dict:
    """Extract and parse the first JSON file from a .tgz archive.

    Used by every transform module that reads from the jmdict-simplified
    or kanjidic2 upstream tarballs. Raises RuntimeError if the archive
    contains no .json member or the member cannot be extracted.
    """
    with tarfile.open(tgz_path, "r:gz") as tf:
        for member in tf.getmembers():
            if member.name.endswith(".json"):
                f = tf.extractfile(member)
                if f is None:
                    raise RuntimeError(f"Cannot extract {member.name}")
                return json.loads(f.read().decode("utf-8"))
    raise RuntimeError(f"No JSON file found in {tgz_path}")


def load_vocab_jlpt_map(
    enrichment_path: Path = JLPT_ENRICHMENT,
) -> dict[str, str]:
    """Build a jmdict_seq → JLPT level map from the vocab portion of
    jlpt-classifications.json.

    D4 fix: for jmdict_seq values that appear at multiple JLPT levels
    (due to homographic variants — e.g., 会う at N5 and 遭う at N2
    sharing seq 1198180), the easier level (higher N-number, closer to
    beginner) wins.  This makes the mapping deterministic and
    pedagogically sensible.
    """
    LEVEL_ORDER = {"N5": 0, "N4": 1, "N3": 2, "N2": 3, "N1": 4}
    if not enrichment_path.exists():
        return {}
    data = json.loads(enrichment_path.read_text(encoding="utf-8"))
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


def is_common(word: dict) -> bool:
    """Return True if any kanji or kana writing is flagged common.

    Common = any writing has ``common: true`` in the upstream JMdict
    priority markers (news1/ichi1/spec1/spec2/gai1).
    """
    for k in word.get("kanji", []) or []:
        if k.get("common"):
            return True
    for k in word.get("kana", []) or []:
        if k.get("common"):
            return True
    return False
