"""Check if pinned upstream sources have newer versions available.

Queries GitHub API for latest releases of upstream sources and compares
against the versions pinned in manifest.json. Reports any that have
newer releases available.

Run via ``just check-upstream`` or ``python -m build.check_upstream``.
"""

from __future__ import annotations

import json
import sys
import urllib.request
import urllib.error
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
MANIFEST_PATH = REPO_ROOT / "manifest.json"

# Map manifest source names to (GitHub owner/repo, version-extraction-hint)
GITHUB_SOURCES = {
    "jmdict-examples-eng": ("scriptin/jmdict-simplified", "3."),
    "kanjivg": ("KanjiVG/kanjivg", "r"),
    "jmdict-furigana": ("Doublevil/JmdictFurigana", "2."),
}


def _get_latest_release(owner_repo: str) -> str | None:
    """Get the tag name of the latest GitHub release."""
    url = f"https://api.github.com/repos/{owner_repo}/releases/latest"
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            return data.get("tag_name", "")
    except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError):
        return None


def _extract_version_from_url(url: str, hint: str) -> str:
    """Extract a version-like string from a download URL."""
    # Try to find the version in the URL path
    for segment in url.split("/"):
        if hint and hint in segment:
            return segment
    return "(unknown)"


def main() -> int:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    sources = manifest.get("sources", {})

    updates_found = 0
    for name, (owner_repo, hint) in GITHUB_SOURCES.items():
        if name not in sources:
            continue

        pinned_url = sources[name].get("url", "")
        pinned_version = _extract_version_from_url(pinned_url, hint)

        latest_tag = _get_latest_release(owner_repo)
        if latest_tag is None:
            print(f"[?]  {name}: could not check {owner_repo} (API error)")
            continue

        # URL-decode for comparison (GitHub uses + but URLs encode as %2B)
        from urllib.parse import unquote
        pinned_url_decoded = unquote(pinned_url)
        if latest_tag in pinned_url_decoded or pinned_version == latest_tag:
            print(f"[ok] {name}: up to date ({pinned_version})")
        else:
            print(f"[!!] {name}: pinned={pinned_version}, latest={latest_tag}")
            print(f"     → https://github.com/{owner_repo}/releases/latest")
            updates_found += 1

    if updates_found:
        print(f"\n{updates_found} source(s) have newer versions available.")
        print("Update manifest.json source URLs and SHA256 hashes to upgrade.")
    else:
        print("\nAll checked sources are up to date.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
