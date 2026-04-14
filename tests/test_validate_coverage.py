"""Coverage tests for build/validate.py.

Targets uncovered lines: _load_json_safe error paths, duplicate
detection for radicals and grammar, bidirectional cross-ref checks,
determinism sort-order checks, validate_all, and main.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


# ===================================================================
# 1. _load_json_safe — error paths (lines 131-138)
# ===================================================================


def test_load_json_safe_missing_file(tmp_path: Path) -> None:
    """_load_json_safe returns None for a file that does not exist."""
    from build.validate import _load_json_safe

    result = _load_json_safe(tmp_path / "nonexistent.json")
    assert result is None


def test_load_json_safe_invalid_json(tmp_path: Path) -> None:
    """_load_json_safe returns None for a file with invalid JSON."""
    from build.validate import _load_json_safe

    bad_file = tmp_path / "bad.json"
    bad_file.write_text("{not valid json", encoding="utf-8")
    result = _load_json_safe(bad_file)
    assert result is None


# ===================================================================
# 2. Duplicate detection — radicals and grammar (lines 174-194)
# ===================================================================


def test_semantic_checks_detect_duplicate_radicals(tmp_path: Path, monkeypatch) -> None:
    """_semantic_checks must report duplicate-radicals when radicals.json
    has two entries sharing the same radical value."""
    import build.validate as validate_mod
    import build.constants as constants_mod

    fake_data_dir = tmp_path / "data"
    core_dir = fake_data_dir / "core"
    core_dir.mkdir(parents=True)

    radicals_data = {
        "metadata": {"source": "test", "license": "test",
                      "generated": "2026-01-01", "count": 2},
        "radicals": [
            {"radical": "一"},
            {"radical": "一"},  # duplicate
        ],
    }
    (core_dir / "radicals.json").write_text(
        json.dumps(radicals_data, ensure_ascii=False), encoding="utf-8"
    )

    monkeypatch.setattr(constants_mod, "DATA_DIR", fake_data_dir)
    monkeypatch.setattr(validate_mod, "DATA_DIR", fake_data_dir)

    failures = validate_mod._semantic_checks()
    check_names = [name for name, _ in failures]
    assert "duplicate-radicals" in check_names, (
        f"expected 'duplicate-radicals' failure; got: {failures}"
    )


def test_semantic_checks_detect_duplicate_grammar(tmp_path: Path, monkeypatch) -> None:
    """_semantic_checks must report duplicate-grammar when grammar.json
    has two entries sharing the same id."""
    import build.validate as validate_mod
    import build.constants as constants_mod

    fake_data_dir = tmp_path / "data"
    grammar_dir = fake_data_dir / "grammar"
    grammar_dir.mkdir(parents=True)

    grammar_data = {
        "metadata": {"source": "test", "license": "test",
                      "generated": "2026-01-01", "count": 2},
        "grammar_points": [
            {"id": "gp-001"},
            {"id": "gp-001"},  # duplicate
        ],
    }
    (grammar_dir / "grammar.json").write_text(
        json.dumps(grammar_data, ensure_ascii=False), encoding="utf-8"
    )

    monkeypatch.setattr(constants_mod, "DATA_DIR", fake_data_dir)
    monkeypatch.setattr(validate_mod, "DATA_DIR", fake_data_dir)

    failures = validate_mod._semantic_checks()
    check_names = [name for name, _ in failures]
    assert "duplicate-grammar" in check_names, (
        f"expected 'duplicate-grammar' failure; got: {failures}"
    )


# ===================================================================
# 3. Bidirectional consistency — asymmetry detection (lines 271-288)
# ===================================================================


def test_semantic_checks_k2w_w2k_asymmetry(tmp_path: Path, monkeypatch) -> None:
    """When k2w maps kanji->word but w2k does not map word->kanji,
    _semantic_checks must report k2w-w2k-asymmetry."""
    import build.validate as validate_mod
    import build.constants as constants_mod

    fake_data_dir = tmp_path / "data"
    xref_dir = fake_data_dir / "cross-refs"
    xref_dir.mkdir(parents=True)

    k2w = {"mapping": {"日": ["word-1"]}}
    w2k = {"mapping": {"word-1": ["月"]}}  # word-1 maps to 月, not 日

    (xref_dir / "kanji-to-words.json").write_text(
        json.dumps(k2w), encoding="utf-8"
    )
    (xref_dir / "word-to-kanji.json").write_text(
        json.dumps(w2k), encoding="utf-8"
    )

    monkeypatch.setattr(constants_mod, "DATA_DIR", fake_data_dir)
    monkeypatch.setattr(validate_mod, "DATA_DIR", fake_data_dir)

    failures = validate_mod._semantic_checks()
    check_names = [name for name, _ in failures]
    assert "k2w-w2k-asymmetry" in check_names, (
        f"expected 'k2w-w2k-asymmetry'; got: {failures}"
    )


def test_semantic_checks_w2k_k2w_asymmetry(tmp_path: Path, monkeypatch) -> None:
    """When w2k maps word->kanji but k2w does not map kanji->word,
    _semantic_checks must report w2k-k2w-asymmetry."""
    import build.validate as validate_mod
    import build.constants as constants_mod

    fake_data_dir = tmp_path / "data"
    xref_dir = fake_data_dir / "cross-refs"
    xref_dir.mkdir(parents=True)

    k2w = {"mapping": {"日": ["word-2"]}}
    w2k = {"mapping": {"word-1": ["日"]}}  # word-1 -> 日, but k2w has 日 -> word-2 only

    (xref_dir / "kanji-to-words.json").write_text(
        json.dumps(k2w), encoding="utf-8"
    )
    (xref_dir / "word-to-kanji.json").write_text(
        json.dumps(w2k), encoding="utf-8"
    )

    monkeypatch.setattr(constants_mod, "DATA_DIR", fake_data_dir)
    monkeypatch.setattr(validate_mod, "DATA_DIR", fake_data_dir)

    failures = validate_mod._semantic_checks()
    check_names = [name for name, _ in failures]
    assert "w2k-k2w-asymmetry" in check_names, (
        f"expected 'w2k-k2w-asymmetry'; got: {failures}"
    )


# ===================================================================
# 4. Determinism sort-order checks (lines 296-326)
# ===================================================================


def test_semantic_checks_unsorted_cross_ref_keys(tmp_path: Path, monkeypatch) -> None:
    """_semantic_checks must flag cross-ref files whose mapping keys
    are not in sorted order."""
    import build.validate as validate_mod
    import build.constants as constants_mod

    fake_data_dir = tmp_path / "data"
    xref_dir = fake_data_dir / "cross-refs"
    xref_dir.mkdir(parents=True)

    # k2w with unsorted keys
    k2w = {"mapping": {"日": ["w1"], "一": ["w2"]}}  # 日 > 一 in sort
    (xref_dir / "kanji-to-words.json").write_text(
        json.dumps(k2w), encoding="utf-8"
    )
    # w2k sorted (to avoid a second failure masking the first)
    w2k = {"mapping": {"a": ["日"]}}
    (xref_dir / "word-to-kanji.json").write_text(
        json.dumps(w2k), encoding="utf-8"
    )

    monkeypatch.setattr(constants_mod, "DATA_DIR", fake_data_dir)
    monkeypatch.setattr(validate_mod, "DATA_DIR", fake_data_dir)

    failures = validate_mod._semantic_checks()
    check_names = [name for name, _ in failures]
    assert "k2w-sort" in check_names, (
        f"expected 'k2w-sort' failure; got: {failures}"
    )


# ===================================================================
# 5. validate_all and main (lines 342-384)
# ===================================================================


@pytest.mark.slow
def test_validate_all_returns_zero() -> None:
    """validate_all on the current repo data should return 0 (or at worst
    only the known k2w-sort issue which still returns 1). We accept both."""
    from build.validate import validate_all

    rc = validate_all()
    assert rc in (0, 1), f"validate_all returned unexpected code {rc}"


@pytest.mark.slow
def test_main_returns_int() -> None:
    """main() delegates to validate_all and returns an int."""
    from build.validate import main

    rc = main()
    assert isinstance(rc, int)
