"""Shared path constants for the build pipeline.

All build modules that need to resolve repository paths should import
from here rather than computing ``Path(__file__).resolve().parent.parent``
independently. This eliminates redundant path traversal and provides a
single place to update if the directory layout ever changes.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "data"
SOURCES_DIR = REPO_ROOT / "sources"
SCHEMAS_DIR = REPO_ROOT / "schemas"
MANIFEST_PATH = REPO_ROOT / "manifest.json"
GRAMMAR_CURATED_DIR = REPO_ROOT / "grammar-curated"
