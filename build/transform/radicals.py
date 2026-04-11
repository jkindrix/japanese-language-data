"""Radicals (KRADFILE + RADKFILE) transform.

Reads KRADFILE (kanji → component radicals) and RADKFILE (radical → kanji
containing it) from the jmdict-simplified JSON releases and combines them
into a single bidirectional radical dataset.

Inputs:
    * ``sources/jmdict-simplified/kradfile.json.tgz``
    * ``sources/jmdict-simplified/radkfile.json.tgz``

Output: ``data/core/radicals.json`` conforming to
``schemas/radical.schema.json``.

The combined structure has two top-level views:
    * ``radicals`` — list of radical entries (from RADKFILE), each with
      radical character, stroke count, code, and the kanji that contain it.
    * ``kanji_to_radicals`` — map from each kanji to its component radicals
      (from KRADFILE). Inverse of the above.
"""

from __future__ import annotations

import json
import tarfile
from pathlib import Path
from datetime import date

REPO_ROOT = Path(__file__).resolve().parents[2]
KRADFILE_TGZ = REPO_ROOT / "sources" / "jmdict-simplified" / "kradfile.json.tgz"
RADKFILE_TGZ = REPO_ROOT / "sources" / "jmdict-simplified" / "radkfile.json.tgz"
OUT = REPO_ROOT / "data" / "core" / "radicals.json"


def _load_source(tgz_path: Path) -> dict:
    with tarfile.open(tgz_path, "r:gz") as tf:
        for member in tf.getmembers():
            if member.name.endswith(".json"):
                f = tf.extractfile(member)
                if f is None:
                    raise RuntimeError(f"Cannot extract {member.name}")
                return json.loads(f.read().decode("utf-8"))
    raise RuntimeError(f"No JSON file found in {tgz_path}")


def build() -> None:
    print(f"[radicals] loading {KRADFILE_TGZ.name} and {RADKFILE_TGZ.name}")
    krad = _load_source(KRADFILE_TGZ)
    radk = _load_source(RADKFILE_TGZ)

    # kradfile.json.tgz has shape:  {"version": "...", "kanji": {"亜": ["｜","一","口"], ...}}
    # radkfile.json.tgz has shape:  {"version": "...", "radicals": {"一": {"strokeCount": 1, "code": ..., "kanji": [...]}, ...}}

    kanji_to_radicals_raw = krad.get("kanji", {})
    # Ensure each entry is a list (defensive)
    kanji_to_radicals: dict[str, list[str]] = {
        k: list(v) for k, v in kanji_to_radicals_raw.items()
    }

    radicals_dict = radk.get("radicals", {})
    radicals_list: list[dict] = []
    for rad_char, rad_info in radicals_dict.items():
        radicals_list.append(
            {
                "radical": rad_char,
                "stroke_count": rad_info.get("strokeCount"),
                "classical_number": None,  # not provided by RADKFILE; could be joined later
                "meanings": [],  # not provided by RADKFILE
                "kanji": list(rad_info.get("kanji", []) or []),
            }
        )

    print(
        f"[radicals] kanji_to_radicals: {len(kanji_to_radicals):,}  "
        f"radicals: {len(radicals_list):,}"
    )

    output = {
        "metadata": {
            "source": "KRADFILE and RADKFILE via scriptin/jmdict-simplified",
            "source_url": "https://github.com/scriptin/jmdict-simplified",
            "license": "CC-BY-SA 4.0 (EDRDG License)",
            "source_version_kradfile": krad.get("version", ""),
            "source_version_radkfile": radk.get("version", ""),
            "generated": date.today().isoformat(),
            "attribution": (
                "This work uses KRADFILE and RADKFILE from the Electronic "
                "Dictionary Research and Development Group (EDRDG), used in "
                "conformance with the Group's license "
                "(https://www.edrdg.org/edrdg/licence.html)."
            ),
            "field_notes": {
                "radicals": "List view: each radical with stroke count and the kanji that contain it. Derived from RADKFILE.",
                "kanji_to_radicals": "Inverse view: each kanji mapped to its component radicals. Derived from KRADFILE.",
                "classical_number": "Kangxi radical number. Not present in RADKFILE; a future phase can join this from an external Kangxi radical table.",
                "meanings": "Radical meanings. Not present in RADKFILE; a future phase can join these from Wikipedia or an external radical table.",
            },
            "warning": "Every radical entry in this file has an empty `meanings` array and `classical_number: null`. RADKFILE does not provide these fields, and no CC-BY-SA-compatible upstream joining source is currently integrated. See docs/phase4-candidates.md for planned resolution.",
        },
        "radicals": radicals_list,
        "kanji_to_radicals": kanji_to_radicals,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"[radicals] wrote {OUT.relative_to(REPO_ROOT)}")
