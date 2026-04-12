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
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

import requests

from build.constants import MANIFEST_PATH, REPO_ROOT, SOURCES_DIR


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
    # ---- Phase 2 additions ---------------------------------------------------
    # Waller JLPT vocabulary CSVs via stephenmk/yomitan-jlpt-vocab.
    # Each file is a raw export of Jonathan Waller's N<level> vocab list with
    # columns: jmdict_seq, kana, kanji, waller_definition.
    # Last maintained 2025-08; CC-BY-SA 4.0.
    Source(
        name="waller-jlpt-vocab-n5",
        url="https://raw.githubusercontent.com/stephenmk/yomitan-jlpt-vocab/main/original_data/n5.csv",
        cache_path="waller-jlpt/n5.csv",
        description="Jonathan Waller JLPT N5 vocabulary list (CSV) via stephenmk/yomitan-jlpt-vocab.",
        license="CC-BY 4.0 (Waller) distributed under CC-BY-SA 4.0 (stephenmk)",
    ),
    Source(
        name="waller-jlpt-vocab-n4",
        url="https://raw.githubusercontent.com/stephenmk/yomitan-jlpt-vocab/main/original_data/n4.csv",
        cache_path="waller-jlpt/n4.csv",
        description="Jonathan Waller JLPT N4 vocabulary list (CSV) via stephenmk/yomitan-jlpt-vocab.",
        license="CC-BY 4.0 (Waller) distributed under CC-BY-SA 4.0 (stephenmk)",
    ),
    Source(
        name="waller-jlpt-vocab-n3",
        url="https://raw.githubusercontent.com/stephenmk/yomitan-jlpt-vocab/main/original_data/n3.csv",
        cache_path="waller-jlpt/n3.csv",
        description="Jonathan Waller JLPT N3 vocabulary list (CSV) via stephenmk/yomitan-jlpt-vocab.",
        license="CC-BY 4.0 (Waller) distributed under CC-BY-SA 4.0 (stephenmk)",
    ),
    Source(
        name="waller-jlpt-vocab-n2",
        url="https://raw.githubusercontent.com/stephenmk/yomitan-jlpt-vocab/main/original_data/n2.csv",
        cache_path="waller-jlpt/n2.csv",
        description="Jonathan Waller JLPT N2 vocabulary list (CSV) via stephenmk/yomitan-jlpt-vocab.",
        license="CC-BY 4.0 (Waller) distributed under CC-BY-SA 4.0 (stephenmk)",
    ),
    Source(
        name="waller-jlpt-vocab-n1",
        url="https://raw.githubusercontent.com/stephenmk/yomitan-jlpt-vocab/main/original_data/n1.csv",
        cache_path="waller-jlpt/n1.csv",
        description="Jonathan Waller JLPT N1 vocabulary list (CSV) via stephenmk/yomitan-jlpt-vocab.",
        license="CC-BY 4.0 (Waller) distributed under CC-BY-SA 4.0 (stephenmk)",
    ),
    # davidluzgouveia/kanji-data provides the only reliably-downloadable form
    # of Waller's kanji JLPT classifications. We extract ONLY the jlpt_new
    # field per kanji; the WaniKani fields (wk_*) are deliberately ignored
    # because their license is not compatible with our CC-BY-SA output.
    Source(
        name="waller-jlpt-kanji",
        url="https://raw.githubusercontent.com/davidluzgouveia/kanji-data/master/kanji.json",
        cache_path="waller-jlpt/kanji-data.json",
        description="Jonathan Waller JLPT kanji classifications via davidluzgouveia/kanji-data (jlpt_new field only). Code is MIT; data fields derive from Waller CC-BY.",
        license="CC-BY 4.0 (Waller JLPT data)",
    ),
    # ---- KFTT parallel corpus -----------------------------------------------
    Source(
        name="kftt",
        url="https://www.phontron.com/kftt/download/kftt-data-1.0.tar.gz",
        cache_path="kftt/kftt-data-1.0.tar.gz",
        description="Kyoto Free Translation Task — ~440k JP-EN parallel sentence pairs from Wikipedia Kyoto articles.",
        license="CC-BY-SA 3.0",
    ),
    # ---- Phase 4 additions --------------------------------------------------
    # Wikipedia "Kangxi radicals" article, pinned to revision 1346511063 via
    # index.php's action=raw endpoint. This returns the raw wikitext for that
    # specific revision as a plain text file (no JSON wrapping), so the
    # SHA256 is stable across rebuilds. Source for authoritative English
    # meanings and Kangxi numbers for the 214 classical radicals.
    Source(
        name="wikipedia-kangxi-radicals",
        url="https://en.wikipedia.org/w/index.php?title=Kangxi_radicals&oldid=1346511063&action=raw",
        cache_path="wikipedia/kangxi-radicals.wikitext",
        description="Wikipedia 'Kangxi radicals' article raw wikitext, pinned to revision 1346511063 (2024). Source for radical English meanings and Kangxi numbers used to populate data/core/radicals.json.",
        license="CC-BY-SA 4.0",
    ),
)


# Maximum file size we'll accept (100 MB). Protects against corrupted
# upstream URLs pointing to unexpectedly large files.
MAX_DOWNLOAD_BYTES = 100 * 1024 * 1024

# Retry policy for transient network failures.
MAX_RETRIES = 3
RETRY_BACKOFF_BASE = 2  # seconds: 2, 4, 8


def _get_version() -> str:
    """Read the project version from manifest.json for the User-Agent header."""
    try:
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        return manifest.get("version", "dev")
    except (FileNotFoundError, json.JSONDecodeError):
        return "dev"


def _build_session() -> requests.Session:
    """Create a reusable requests.Session with a descriptive User-Agent.

    Connection pooling across multiple fetches is more efficient and
    reduces the chance of transient failures from opening fresh
    connections.

    User-Agent follows Wikipedia's UA policy (required for
    api.wikipedia.org) and polite practice on other hosts.
    See https://meta.wikimedia.org/wiki/User-Agent_policy
    """
    session = requests.Session()
    version = _get_version()
    session.headers["User-Agent"] = (
        f"japanese-language-data/{version} "
        f"(https://github.com/jkindrix/japanese-language-data; "
        f"reproducible-build fetcher)"
    )
    return session


def _download(url: str, destination: Path, session: requests.Session) -> None:
    """Stream a download to *destination* atomically.

    Downloads to a ``.tmp`` file first and renames on success so that a
    partial download (from a dropped connection) never leaves a corrupt
    file in the cache.
    """
    destination.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = destination.with_suffix(destination.suffix + ".tmp")

    try:
        with session.get(url, stream=True, timeout=60) as response:
            response.raise_for_status()

            # Check Content-Length if the server provides it.
            content_length = response.headers.get("Content-Length")
            if content_length and int(content_length) > MAX_DOWNLOAD_BYTES:
                raise RuntimeError(
                    f"Upstream file too large: {int(content_length):,} bytes "
                    f"(limit {MAX_DOWNLOAD_BYTES:,}). Check the URL."
                )

            written = 0
            with tmp_path.open("wb") as handle:
                for chunk in response.iter_content(chunk_size=65536):
                    if chunk:
                        written += len(chunk)
                        if written > MAX_DOWNLOAD_BYTES:
                            raise RuntimeError(
                                f"Download exceeded {MAX_DOWNLOAD_BYTES:,} byte "
                                f"limit during streaming. Aborting."
                            )
                        handle.write(chunk)

        # Atomic rename: only replaces the destination once the full
        # download succeeds. On POSIX this is atomic; on Windows it
        # replaces but is not atomic (acceptable for this use case).
        tmp_path.rename(destination)

    except BaseException:
        # Clean up the partial .tmp file on any failure.
        tmp_path.unlink(missing_ok=True)
        raise


def _download_with_retries(
    url: str,
    destination: Path,
    session: requests.Session,
) -> None:
    """Download with exponential backoff on transient failures.

    Retries on connection errors and server errors (5xx). Hash
    mismatches and client errors (4xx) are NOT retried — they indicate
    a real problem, not a transient one.
    """
    for attempt in range(MAX_RETRIES):
        try:
            _download(url, destination, session)
            return
        except (requests.ConnectionError, requests.Timeout, OSError) as exc:
            if attempt == MAX_RETRIES - 1:
                raise
            delay = RETRY_BACKOFF_BASE ** (attempt + 1)
            print(f"[retry]      attempt {attempt + 1}/{MAX_RETRIES} "
                  f"failed ({type(exc).__name__}), retrying in {delay}s")
            time.sleep(delay)
        except requests.HTTPError as exc:
            # Only retry on server errors (5xx); client errors (4xx) are permanent.
            if exc.response is not None and 500 <= exc.response.status_code < 600:
                if attempt == MAX_RETRIES - 1:
                    raise
                delay = RETRY_BACKOFF_BASE ** (attempt + 1)
                print(f"[retry]      attempt {attempt + 1}/{MAX_RETRIES} "
                      f"failed (HTTP {exc.response.status_code}), retrying in {delay}s")
                time.sleep(delay)
            else:
                raise


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


def _fetch_one(
    source: Source,
    sources_meta: dict,
    session: requests.Session,
) -> None:
    """Fetch a single source, verifying or recording its SHA256 hash.

    Called from fetch_all() — either serially or in parallel via a
    ThreadPoolExecutor.  On success, updates sources_meta[source.name]
    in place.
    """
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
        _download_with_retries(source.url, cache_full, session)
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


def fetch_all(sources: Iterable[Source] = SOURCES) -> dict:
    """Fetch every source in parallel, verifying or recording SHA256 hashes.

    Returns the updated manifest dict. Writes any newly-observed hashes
    to ``manifest.json``.

    Sources are fetched in parallel (up to 4 concurrent downloads) since
    they target different hosts and are entirely independent. The
    requests.Session is thread-safe for concurrent use.

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
    session = _build_session()
    sources_list = list(sources)

    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {
            executor.submit(_fetch_one, source, sources_meta, session): source
            for source in sources_list
        }
        for future in as_completed(futures):
            future.result()  # propagate any exception

    session.close()
    _save_manifest(manifest)
    return manifest


def main() -> int:
    print(f"Fetching {len(SOURCES)} upstream sources to {SOURCES_DIR}")
    fetch_all()
    print("Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
