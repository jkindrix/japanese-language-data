"""Fetch upstream sources with content-hash verification.

Every upstream source is pinned to a specific URL and (after the first
successful fetch) a specific SHA256 hash. Subsequent fetches verify the
hash against the pin. A hash mismatch is fatal — it means upstream has
been updated and we need a deliberate pin bump, not a silent update.

The sources to fetch are defined as Source dataclass instances in
SOURCES. To add a new upstream source:

    1. Add a Source to SOURCES with name, url, cache_path, and
       expected_sha256 (leave empty on first fetch).
    2. Run `just fetch` once to populate the hash.
    3. Commit the new hash in manifest.json (not in this file — the
       file encodes only the URL pin; the hash pin lives in manifest.json
       to keep this file stable across rebuilds).

Run as a module: ``python -m build.fetch`` or via ``just fetch``.
"""

from __future__ import annotations

import hashlib
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

import requests

# Paths relative to the repository root.
REPO_ROOT = Path(__file__).resolve().parent.parent
SOURCES_DIR = REPO_ROOT / "sources"
MANIFEST_PATH = REPO_ROOT / "manifest.json"


@dataclass(frozen=True)
class Source:
    """A pinned upstream source to fetch.

    Attributes:
        name: Short identifier used as the manifest key.
        url: The exact download URL. Changing this requires a deliberate
            pin bump.
        cache_path: Where the downloaded file is stored, relative to
            ``sources/``.
        description: Human-readable description for logs.
        license: SPDX identifier or canonical license name.
    """

    name: str
    url: str
    cache_path: str
    description: str
    license: str


# ---------------------------------------------------------------------------
# Pinned sources
# ---------------------------------------------------------------------------
#
# URLs here are the pinned versions. Upgrading requires editing the URL
# AND clearing the corresponding SHA256 in manifest.json.

JMDICT_SIMPLIFIED_VERSION = "3.6.2+20260406125001"
_JMDS = f"https://github.com/scriptin/jmdict-simplified/releases/download/{JMDICT_SIMPLIFIED_VERSION.replace('+', '%2B')}"

KANJIVG_VERSION = "r20250816"
KANJIVG_DATE = "20250816"

SOURCES: tuple[Source, ...] = (
    Source(
        name="jmdict-examples-eng",
        url=f"{_JMDS}/jmdict-examples-eng-{JMDICT_SIMPLIFIED_VERSION}.json.tgz",
        cache_path="jmdict-simplified/jmdict-examples-eng.json.tgz",
        description="JMdict English entries with Tatoeba example sentences pre-linked.",
        license="EDRDG License / CC-BY-SA 4.0",
    ),
    Source(
        name="jmnedict",
        url=f"{_JMDS}/jmnedict-all-{JMDICT_SIMPLIFIED_VERSION}.json.tgz",
        cache_path="jmdict-simplified/jmnedict-all.json.tgz",
        description="JMnedict proper nouns (all languages).",
        license="EDRDG License / CC-BY-SA 4.0",
    ),
    Source(
        name="kanjidic2",
        url=f"{_JMDS}/kanjidic2-all-{JMDICT_SIMPLIFIED_VERSION}.json.tgz",
        cache_path="jmdict-simplified/kanjidic2-all.json.tgz",
        description="KANJIDIC2 kanji data, all languages (13,108 characters, full coverage).",
        license="EDRDG License / CC-BY-SA 4.0",
    ),
    Source(
        name="kradfile",
        url=f"{_JMDS}/kradfile-{JMDICT_SIMPLIFIED_VERSION}.json.tgz",
        cache_path="jmdict-simplified/kradfile.json.tgz",
        description="KRADFILE kanji → radical components mapping.",
        license="EDRDG License / CC-BY-SA 4.0",
    ),
    Source(
        name="radkfile",
        url=f"{_JMDS}/radkfile-{JMDICT_SIMPLIFIED_VERSION}.json.tgz",
        cache_path="jmdict-simplified/radkfile.json.tgz",
        description="RADKFILE radical → kanji lookup.",
        license="EDRDG License / CC-BY-SA 4.0",
    ),
    Source(
        name="kanjivg",
        url=f"https://github.com/KanjiVG/kanjivg/releases/download/{KANJIVG_VERSION}/kanjivg-{KANJIVG_DATE}-main.zip",
        cache_path="kanjivg/kanjivg-main.zip",
        description="KanjiVG stroke order SVG files (non-variant forms).",
        license="CC-BY-SA 3.0 Unported",
    ),
    Source(
        name="kanjium-accents",
        url="https://raw.githubusercontent.com/mifunetoshiro/kanjium/master/data/source_files/raw/accents.txt",
        cache_path="kanjium/accents.txt",
        description="Kanjium pitch accent TSV (word, reading, mora positions).",
        license="CC-BY-SA 4.0",
    ),
)


def _download(url: str, destination: Path) -> None:
    """Stream a download to *destination*, creating parent directories."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    with requests.get(url, stream=True, timeout=60) as response:
        response.raise_for_status()
        with destination.open("wb") as handle:
            for chunk in response.iter_content(chunk_size=65536):
                if chunk:
                    handle.write(chunk)


def _sha256(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def _load_manifest() -> dict:
    if MANIFEST_PATH.exists():
        return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    return {}


def _save_manifest(manifest: dict) -> None:
    MANIFEST_PATH.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def fetch_all(sources: Iterable[Source] = SOURCES) -> dict:
    """Fetch every source, verifying or recording SHA256 hashes.

    Returns the updated manifest dict. Writes any newly-observed hashes
    to ``manifest.json``.

    Hash verification policy:
        - If the manifest already has a hash for the source and the
          cached file's hash matches, the source is not re-downloaded.
        - If the manifest has a hash and the cached file's hash does not
          match, the build aborts.
        - If the manifest has no hash yet, the source is downloaded and
          the observed hash is recorded.
    """
    manifest = _load_manifest()
    manifest.setdefault("sources", {})
    sources_meta = manifest["sources"]

    for source in sources:
        cache_full = SOURCES_DIR / source.cache_path
        entry = sources_meta.setdefault(source.name, {})
        entry["url"] = source.url
        entry["license"] = source.license
        entry["description"] = source.description

        expected = entry.get("sha256")
        need_download = True

        if cache_full.exists() and expected:
            observed = _sha256(cache_full)
            if observed == expected:
                print(f"[cache ok]   {source.name}")
                need_download = False
            else:
                raise SystemExit(
                    f"\nFATAL: SHA256 mismatch for cached source {source.name!r}.\n"
                    f"  Cached file: {cache_full}\n"
                    f"  Expected:    {expected}\n"
                    f"  Observed:    {observed}\n"
                    f"  Either the cached file is corrupt (delete it and re-run) or\n"
                    f"  the upstream pin has been updated and manifest.json needs to\n"
                    f"  be updated deliberately.\n"
                )

        if need_download:
            print(f"[fetching]   {source.name} <- {source.url}")
            _download(source.url, cache_full)
            observed = _sha256(cache_full)
            if expected and observed != expected:
                raise SystemExit(
                    f"\nFATAL: SHA256 mismatch after downloading {source.name!r}.\n"
                    f"  Downloaded: {cache_full}\n"
                    f"  Expected:   {expected}\n"
                    f"  Observed:   {observed}\n"
                    f"  Upstream source has changed. Update manifest.json if this\n"
                    f"  is intentional.\n"
                )
            entry["sha256"] = observed
            entry["size_bytes"] = cache_full.stat().st_size
            print(f"[fetched]    {source.name} sha256={observed[:16]}… size={entry['size_bytes']:,}B")

    _save_manifest(manifest)
    return manifest


def main() -> int:
    print(f"Fetching {len(SOURCES)} upstream sources to {SOURCES_DIR}")
    fetch_all()
    print("Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
