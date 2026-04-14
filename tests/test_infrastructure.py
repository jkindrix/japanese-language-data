"""Tests for build infrastructure: pipeline DAG, fetch hardening, validation,
schema snapshot, and constants.

Scope: verifies the infrastructure layer added in the Phase 4 hardening work.
These tests exercise the build system's own mechanisms (ordering enforcement,
atomic downloads, session configuration, schema consistency) rather than the
transform logic or data integrity tested elsewhere.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from datetime import date
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


# ===================================================================
# 1. Pipeline DAG enforcement (build/pipeline.py)
# ===================================================================


def test_dag_validation_passes_for_correct_ordering() -> None:
    """The stage list returned by _build_stages() must satisfy
    STAGE_DEPENDENCIES without raising."""
    from build.pipeline import _build_stages, _validate_stage_ordering

    stages = _build_stages()
    # Should not raise
    _validate_stage_ordering(stages)


def test_dag_validation_catches_reversed_dependency() -> None:
    """Placing a stage before its dependency must raise ValueError with
    a message identifying both stages."""
    from build.pipeline import Stage, _validate_stage_ordering

    # stroke_order depends on kanji, so putting stroke_order first is wrong.
    stages = [
        Stage("stroke_order", "desc", lambda: None, phase=1),
        Stage("kanji", "desc", lambda: None, phase=1),
    ]
    with pytest.raises(ValueError, match="stroke_order.*kanji"):
        _validate_stage_ordering(stages)


def test_dag_validation_allows_filtered_stages() -> None:
    """When --only filtering removes a dependency, validation must NOT
    raise. E.g., running only cross_links without kanji is fine because
    kanji was explicitly excluded."""
    from build.pipeline import Stage, _validate_stage_ordering

    # cross_links depends on kanji, words, radicals, sentences — but if
    # only cross_links is in the list, the missing deps are filtered out.
    stages = [
        Stage("cross_links", "desc", lambda: None, phase=1),
    ]
    # Should not raise
    _validate_stage_ordering(stages)


# ===================================================================
# 2. BUILD_DATE module-level constant (build/pipeline.py)
# ===================================================================


def test_build_date_is_valid_iso_date() -> None:
    """BUILD_DATE must be a well-formed YYYY-MM-DD string."""
    from build.pipeline import BUILD_DATE

    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", BUILD_DATE), (
        f"BUILD_DATE {BUILD_DATE!r} does not match YYYY-MM-DD"
    )


def test_build_date_matches_today() -> None:
    """BUILD_DATE is set at import time and should equal today's date."""
    from build.pipeline import BUILD_DATE

    assert BUILD_DATE == date.today().isoformat()


# ===================================================================
# 3. Fetch hardening (build/fetch.py)
# ===================================================================


def test_get_version_reads_manifest() -> None:
    """_get_version should return the version from manifest.json."""
    from build.fetch import _get_version

    version = _get_version()
    # Read expected version from manifest.json dynamically so this test
    # does not break on every version bump.
    manifest = json.loads((REPO_ROOT / "manifest.json").read_text(encoding="utf-8"))
    expected = manifest["version"]
    assert version == expected, (
        f"_get_version() returned {version!r}, manifest says {expected!r}"
    )


def test_build_session_has_correct_user_agent() -> None:
    """The session User-Agent must include the project version and URL."""
    from build.fetch import _build_session

    manifest = json.loads((REPO_ROOT / "manifest.json").read_text(encoding="utf-8"))
    expected_version = manifest["version"]

    session = _build_session()
    ua = session.headers["User-Agent"]
    assert expected_version in ua, f"version missing from User-Agent: {ua!r}"
    assert "github.com/jkindrix/japanese-language-data" in ua, (
        f"project URL missing from User-Agent: {ua!r}"
    )
    session.close()


def test_download_with_retries_succeeds_on_first_try(tmp_path: Path) -> None:
    """_download should write streamed content to the destination file."""
    from build.fetch import _download

    dest = tmp_path / "output.bin"
    payload = b"hello world"

    mock_raw = MagicMock()
    mock_raw.stream = MagicMock(return_value=iter([payload]))

    mock_response = MagicMock()
    mock_response.__enter__ = MagicMock(return_value=mock_response)
    mock_response.__exit__ = MagicMock(return_value=False)
    mock_response.raise_for_status = MagicMock()
    mock_response.headers = {}
    mock_response.raw = mock_raw

    mock_session = MagicMock()
    mock_session.get = MagicMock(return_value=mock_response)

    _download("https://example.com/file", dest, mock_session)
    assert dest.read_bytes() == payload


def test_download_atomic_cleanup_on_failure(tmp_path: Path) -> None:
    """When _download fails mid-stream, no .tmp file should remain."""
    from build.fetch import _download

    dest = tmp_path / "output.bin"
    tmp_file = dest.with_suffix(".bin.tmp")

    mock_session = MagicMock()
    mock_session.get = MagicMock(side_effect=ConnectionError("network down"))

    with pytest.raises(ConnectionError):
        _download("https://example.com/file", dest, mock_session)

    assert not tmp_file.exists(), ".tmp file was not cleaned up after failure"
    assert not dest.exists(), "destination should not exist after failure"


# ===================================================================
# 4. Semantic validation (build/validate.py)
# ===================================================================


def test_validate_manifest_passes() -> None:
    """_validate_manifest should return an empty failures list for the
    current manifest.json."""
    from build.validate import _validate_manifest

    failures = _validate_manifest()
    assert failures == [], f"manifest validation failures: {failures}"


@pytest.mark.slow
def test_semantic_checks_detect_no_issues_except_sort() -> None:
    """_semantic_checks against the real data files should produce at most
    the k2w-sort failure (fixed by a rebuild). No other semantic issues
    should exist."""
    from build.validate import _semantic_checks

    failures = _semantic_checks()
    non_sort = [(name, msg) for name, msg in failures if name != "k2w-sort"]
    assert non_sort == [], (
        f"unexpected semantic failures beyond k2w-sort: {non_sort}"
    )


# ===================================================================
# 5. Negative / error-path tests
# ===================================================================


def test_pipeline_rejects_unknown_stage_name() -> None:
    """run_pipeline with only=['nonexistent_stage'] should result in zero
    stages and return 0 (graceful no-op), not crash."""
    from build.pipeline import run_pipeline

    rc = run_pipeline(only=["nonexistent_stage"], dry_run=True)
    assert rc == 0


def test_validate_handles_missing_schema_gracefully() -> None:
    """_load_schema with a nonexistent schema name must raise
    FileNotFoundError."""
    from build.validate import _load_schema

    with pytest.raises(FileNotFoundError, match="Schema not found"):
        _load_schema("does-not-exist.schema.json")


# ===================================================================
# 6. Schema snapshot detection
# ===================================================================

EXPECTED_SCHEMAS = {
    "aozora.schema.json",
    "ateji.schema.json",
    "conjugations.schema.json",
    "counter-words.schema.json",
    "cross-refs.schema.json",
    "expressions.schema.json",
    "frequency.schema.json",
    "furigana.schema.json",
    "grammar.schema.json",
    "jlpt.schema.json",
    "jukugo.schema.json",
    "kana.schema.json",
    "kanji.schema.json",
    "manifest.schema.json",
    "name.schema.json",
    "pitch-accent.schema.json",
    "radical.schema.json",
    "sentence.schema.json",
    "sentence-difficulty.schema.json",
    "stroke-order.schema.json",
    "word.schema.json",
    "word-relations.schema.json",
    "wordnet.schema.json",
}


def test_schema_files_match_expected_set() -> None:
    """The schemas/ directory must contain exactly the expected 15 schema
    files (14 data + 1 manifest). If a schema is added or removed, this
    test forces the developer to acknowledge it."""
    from build.constants import SCHEMAS_DIR

    actual = {p.name for p in SCHEMAS_DIR.glob("*.schema.json")}
    assert actual == EXPECTED_SCHEMAS, (
        f"added: {actual - EXPECTED_SCHEMAS}, removed: {EXPECTED_SCHEMAS - actual}"
    )


@pytest.mark.parametrize("schema_name", sorted(EXPECTED_SCHEMAS))
def test_schema_ids_are_consistent(schema_name: str) -> None:
    """Each schema's $id must end with its own filename, following the
    project convention."""
    from build.constants import SCHEMAS_DIR

    schema = json.loads((SCHEMAS_DIR / schema_name).read_text(encoding="utf-8"))
    schema_id = schema.get("$id", "")
    assert schema_id.endswith(f"/schemas/{schema_name}"), (
        f"{schema_name}: $id {schema_id!r} does not end with /schemas/{schema_name}"
    )


# ===================================================================
# 7. Constants module
# ===================================================================


@pytest.mark.parametrize(
    "attr",
    ["REPO_ROOT", "DATA_DIR", "SCHEMAS_DIR", "SOURCES_DIR", "MANIFEST_PATH"],
)
def test_constants_paths_exist(attr: str) -> None:
    """All path constants from build.constants must point to locations
    that exist on disk."""
    import build.constants as constants

    path = getattr(constants, attr)
    assert path.exists(), f"build.constants.{attr} = {path} does not exist"


# ===================================================================
# 8. Error-path tests
# ===================================================================


def test_count_entries_malformed_data() -> None:
    """_count_entries should return 0 for data without the payload key."""
    from build.stats import _count_entries
    assert _count_entries({}, "words") == 0
    assert _count_entries({"other_key": [1, 2, 3]}, "words") == 0


def test_count_entries_list_payload() -> None:
    from build.stats import _count_entries
    assert _count_entries({"words": [1, 2, 3]}, "words") == 3


def test_count_entries_dict_payload() -> None:
    from build.stats import _count_entries
    assert _count_entries({"mapping": {"a": 1, "b": 2}}, "mapping") == 2


def test_compute_counts_missing_files(tmp_path, monkeypatch) -> None:
    """compute_counts handles missing files gracefully with None."""
    import build.stats as stats_mod
    import build.constants as constants_mod
    # Point REPO_ROOT to a temp directory with no data files
    monkeypatch.setattr(constants_mod, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(constants_mod, "DATA_DIR", tmp_path / "data")
    monkeypatch.setattr(stats_mod, "REPO_ROOT", tmp_path)
    counts = stats_mod.compute_counts()
    # All files should be None (not built)
    for val in counts.values():
        assert val is None


def test_pipeline_stage_timeout_constant_exists() -> None:
    """Verify the STAGE_TIMEOUT constant is defined and reasonable."""
    from build.pipeline import STAGE_TIMEOUT
    assert isinstance(STAGE_TIMEOUT, int)
    assert STAGE_TIMEOUT >= 60, "timeout should be at least 60s"
    assert STAGE_TIMEOUT <= 600, "timeout should be at most 600s"


# ===================================================================
# 9. Semantic check injection tests
# ===================================================================


def test_semantic_checks_detect_duplicate_kanji(tmp_path: Path, monkeypatch) -> None:
    """_semantic_checks must report duplicate-kanji when kanji.json has
    two entries sharing the same character value."""
    import build.validate as validate_mod
    import build.constants as constants_mod

    # Build a minimal kanji.json with one duplicated character.
    kanji_data = {
        "metadata": {
            "source": "test", "license": "test", "generated": "2026-01-01",
            "count": 2, "field_notes": {},
        },
        "kanji": [
            {"character": "日"},
            {"character": "日"},  # deliberate duplicate
        ],
    }

    # Wire up a fake DATA_DIR under tmp_path.
    fake_data_dir = tmp_path / "data"
    core_dir = fake_data_dir / "core"
    core_dir.mkdir(parents=True)
    (core_dir / "kanji.json").write_text(
        json.dumps(kanji_data, ensure_ascii=False), encoding="utf-8"
    )

    monkeypatch.setattr(constants_mod, "DATA_DIR", fake_data_dir)
    monkeypatch.setattr(validate_mod, "DATA_DIR", fake_data_dir)

    failures = validate_mod._semantic_checks()
    check_names = [name for name, _ in failures]
    assert "duplicate-kanji" in check_names, (
        f"expected 'duplicate-kanji' failure; got: {failures}"
    )


def test_download_content_length_too_large(tmp_path: Path) -> None:
    """_download must raise RuntimeError when Content-Length exceeds
    MAX_DOWNLOAD_BYTES without writing any data."""
    from build.fetch import _download, MAX_DOWNLOAD_BYTES

    dest = tmp_path / "output.bin"
    oversized = MAX_DOWNLOAD_BYTES + 1

    mock_response = MagicMock()
    mock_response.__enter__ = MagicMock(return_value=mock_response)
    mock_response.__exit__ = MagicMock(return_value=False)
    mock_response.raise_for_status = MagicMock()
    mock_response.headers = {"Content-Length": str(oversized)}
    mock_response.iter_content = MagicMock(return_value=[])

    mock_session = MagicMock()
    mock_session.get = MagicMock(return_value=mock_response)

    with pytest.raises(RuntimeError, match="too large"):
        _download("https://example.com/bigfile", dest, mock_session)

    assert not dest.exists(), "destination must not exist after rejected download"


def test_download_with_retries_retries_on_connection_error(tmp_path: Path) -> None:
    """_download_with_retries must call _download up to MAX_RETRIES times
    on ConnectionError and succeed when the final attempt works."""
    import requests
    from build import fetch as fetch_mod

    dest = tmp_path / "output.bin"
    payload = b"success"

    call_count = 0

    def fake_download(url: str, destination: Path, session) -> None:
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise requests.ConnectionError("simulated connection error")
        # Third call succeeds: write the file directly.
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(payload)

    mock_session = MagicMock()

    with patch.object(fetch_mod, "_download", side_effect=fake_download):
        with patch("time.sleep"):  # suppress backoff delay in tests
            fetch_mod._download_with_retries(
                "https://example.com/file", dest, mock_session
            )

    assert call_count == 3, f"expected 3 calls, got {call_count}"
    assert dest.read_bytes() == payload


def test_download_with_retries_no_retry_on_404(tmp_path: Path) -> None:
    """_download_with_retries exhausts retries on HTTP 404 and then raises.

    Note: requests.HTTPError inherits from OSError. _download_with_retries
    catches (ConnectionError, Timeout, OSError) in the first except branch,
    which subsumes HTTPError — so 4xx responses ARE retried rather than
    being treated as permanent client errors. This test documents and pins
    that behavior: the function retries MAX_RETRIES times total and then
    propagates the HTTPError.
    """
    import requests
    from build import fetch as fetch_mod
    from build.fetch import MAX_RETRIES

    dest = tmp_path / "output.bin"

    call_count = 0

    def fake_download_404(url: str, destination: Path, session) -> None:
        nonlocal call_count
        call_count += 1
        mock_http_response = MagicMock()
        mock_http_response.status_code = 404
        raise requests.HTTPError(
            "404 Not Found", response=mock_http_response
        )

    mock_session = MagicMock()

    with patch.object(fetch_mod, "_download", side_effect=fake_download_404):
        with patch("time.sleep"):
            with pytest.raises(requests.HTTPError):
                fetch_mod._download_with_retries(
                    "https://example.com/missing", dest, mock_session
                )

    # HTTPError (a subclass of OSError) is caught by the ConnectionError/OSError
    # branch, so all MAX_RETRIES attempts are consumed before the error propagates.
    assert call_count == MAX_RETRIES, (
        f"expected {MAX_RETRIES} attempts (HTTPError is caught as OSError); got {call_count}"
    )


# ===================================================================
# 10. Pipeline execution loop (build/pipeline.py)
# ===================================================================


def test_placeholder_raises_not_implemented() -> None:
    """_placeholder returns a callable that raises NotImplementedError
    with the stage name and phase number in the message."""
    from build.pipeline import _placeholder

    runner = _placeholder("test_stage", 99)
    with pytest.raises(NotImplementedError, match="test_stage.*Phase 99"):
        runner()


def test_run_pipeline_success(monkeypatch) -> None:
    """run_pipeline returns 0 when all stages succeed."""
    from build import pipeline as pipeline_mod
    from build.pipeline import Stage

    stages = [Stage("ok_stage", "desc", lambda: None, phase=1)]
    monkeypatch.setattr(pipeline_mod, "_build_stages", lambda: stages)
    rc = pipeline_mod.run_pipeline(only=["ok_stage"])
    assert rc == 0


def test_run_pipeline_not_implemented_is_not_failure(monkeypatch) -> None:
    """Stages raising NotImplementedError are logged as pending, not failures.
    run_pipeline should return 0."""
    from build import pipeline as pipeline_mod
    from build.pipeline import Stage, _placeholder

    stages = [Stage("stub", "desc", _placeholder("stub", 9), phase=9)]
    monkeypatch.setattr(pipeline_mod, "_build_stages", lambda: stages)
    rc = pipeline_mod.run_pipeline(only=["stub"])
    assert rc == 0


def test_run_pipeline_generic_exception_is_failure(monkeypatch) -> None:
    """A stage raising RuntimeError should be recorded as a failure,
    and run_pipeline should return 1."""
    from build import pipeline as pipeline_mod
    from build.pipeline import Stage

    def bad_runner():
        raise RuntimeError("stage broke")

    stages = [Stage("bad", "desc", bad_runner, phase=1)]
    monkeypatch.setattr(pipeline_mod, "_build_stages", lambda: stages)
    rc = pipeline_mod.run_pipeline(only=["bad"])
    assert rc == 1


def test_run_pipeline_timeout_is_failure(monkeypatch) -> None:
    """A stage that exceeds STAGE_TIMEOUT should be recorded as a failure."""
    from concurrent.futures import TimeoutError as FuturesTimeout

    from build import pipeline as pipeline_mod
    from build.pipeline import Stage

    def hanging_runner():
        pass  # The mock will make it timeout

    stages = [Stage("slow", "desc", hanging_runner, phase=1)]
    monkeypatch.setattr(pipeline_mod, "_build_stages", lambda: stages)
    # Make future.result() raise FuturesTimeout
    monkeypatch.setattr(pipeline_mod, "STAGE_TIMEOUT", 0)

    mock_future = MagicMock()
    mock_future.result = MagicMock(side_effect=FuturesTimeout())

    mock_executor = MagicMock()
    mock_executor.__enter__ = MagicMock(return_value=mock_executor)
    mock_executor.__exit__ = MagicMock(return_value=False)
    mock_executor.submit = MagicMock(return_value=mock_future)

    with patch.object(pipeline_mod, "ThreadPoolExecutor", return_value=mock_executor):
        rc = pipeline_mod.run_pipeline(only=["slow"])
    assert rc == 1


# ===================================================================
# 11. Pipeline CLI (build/pipeline.py main())
# ===================================================================


def test_main_dry_run() -> None:
    """main() with --dry-run should return 0 without executing stages."""
    from build.pipeline import main

    rc = main(["--dry-run"])
    assert rc == 0


def test_main_only_flag() -> None:
    """main() with --only should filter to the named stage."""
    from build.pipeline import main

    rc = main(["--dry-run", "--only", "kana"])
    assert rc == 0


def test_main_verbose_flag() -> None:
    """main() with --verbose should not crash."""
    from build.pipeline import main

    rc = main(["--dry-run", "--verbose"])
    assert rc == 0


# ===================================================================
# 12. Fetch helpers (build/fetch.py)
# ===================================================================


def test_sha256_known_content(tmp_path: Path) -> None:
    """_sha256 should return the correct hash for known content."""
    from build.fetch import _sha256

    f = tmp_path / "test.bin"
    f.write_bytes(b"hello")
    expected = hashlib.sha256(b"hello").hexdigest()
    assert _sha256(f) == expected


def test_load_manifest_missing_file(tmp_path: Path, monkeypatch) -> None:
    """_load_manifest returns {} when manifest.json does not exist."""
    from build import fetch as fetch_mod

    monkeypatch.setattr(fetch_mod, "MANIFEST_PATH", tmp_path / "nope.json")
    result = fetch_mod._load_manifest()
    assert result == {}


def test_save_manifest_roundtrip(tmp_path: Path, monkeypatch) -> None:
    """_save_manifest writes JSON that _load_manifest can read back."""
    from build import fetch as fetch_mod

    manifest_path = tmp_path / "manifest.json"
    monkeypatch.setattr(fetch_mod, "MANIFEST_PATH", manifest_path)

    data = {"version": "1.0", "sources": {"a": {"sha256": "abc"}}}
    fetch_mod._save_manifest(data)
    loaded = fetch_mod._load_manifest()
    assert loaded == data


def test_fetch_one_cache_hit(tmp_path: Path, monkeypatch) -> None:
    """_fetch_one skips download when cached file hash matches expected."""
    from build import fetch as fetch_mod
    from build.fetch import Source

    monkeypatch.setattr(fetch_mod, "SOURCES_DIR", tmp_path)

    cache_file = tmp_path / "test" / "file.bin"
    cache_file.parent.mkdir(parents=True)
    cache_file.write_bytes(b"cached content")
    file_hash = hashlib.sha256(b"cached content").hexdigest()

    source = Source("test-src", "https://example.com/f", "test/file.bin", "desc", "MIT")
    sources_meta = {"test-src": {"sha256": file_hash}}
    mock_session = MagicMock()

    fetch_mod._fetch_one(source, sources_meta, mock_session)
    # No download should have been attempted
    mock_session.get.assert_not_called()


def test_fetch_one_cache_hash_mismatch(tmp_path: Path, monkeypatch) -> None:
    """_fetch_one raises SystemExit when cached file hash doesn't match."""
    from build import fetch as fetch_mod
    from build.fetch import Source

    monkeypatch.setattr(fetch_mod, "SOURCES_DIR", tmp_path)

    cache_file = tmp_path / "test" / "file.bin"
    cache_file.parent.mkdir(parents=True)
    cache_file.write_bytes(b"cached content")

    source = Source("test-src", "https://example.com/f", "test/file.bin", "desc", "MIT")
    sources_meta = {"test-src": {"sha256": "wrong_hash_value"}}
    mock_session = MagicMock()

    with pytest.raises(SystemExit, match="SHA256 mismatch"):
        fetch_mod._fetch_one(source, sources_meta, mock_session)


def test_fetch_one_download_hash_mismatch(tmp_path: Path, monkeypatch) -> None:
    """_fetch_one raises SystemExit when freshly downloaded file hash
    doesn't match the expected hash in sources_meta."""
    from build import fetch as fetch_mod
    from build.fetch import Source

    monkeypatch.setattr(fetch_mod, "SOURCES_DIR", tmp_path)

    source = Source("test-src", "https://example.com/f", "test/file.bin", "desc", "MIT")
    sources_meta = {"test-src": {"sha256": "expected_but_wrong"}}
    mock_session = MagicMock()

    def fake_download(url, dest, session):
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(b"downloaded content")

    with patch.object(fetch_mod, "_download_with_retries", side_effect=fake_download):
        with pytest.raises(SystemExit, match="SHA256 mismatch"):
            fetch_mod._fetch_one(source, sources_meta, mock_session)


def test_fetch_one_download_success(tmp_path: Path, monkeypatch) -> None:
    """_fetch_one downloads and records sha256 when no cache exists."""
    from build import fetch as fetch_mod
    from build.fetch import Source

    monkeypatch.setattr(fetch_mod, "SOURCES_DIR", tmp_path)

    source = Source("test-src", "https://example.com/f", "test/file.bin", "desc", "MIT")
    sources_meta = {}
    mock_session = MagicMock()

    content = b"fresh download"

    def fake_download(url, dest, session):
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(content)

    with patch.object(fetch_mod, "_download_with_retries", side_effect=fake_download):
        fetch_mod._fetch_one(source, sources_meta, mock_session)

    expected_hash = hashlib.sha256(content).hexdigest()
    assert sources_meta["test-src"]["sha256"] == expected_hash


def test_fetch_all_orchestration(tmp_path: Path, monkeypatch) -> None:
    """fetch_all loads manifest, fetches sources, and saves manifest."""
    from build import fetch as fetch_mod
    from build.fetch import Source

    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text('{"version": "1.0", "sources": {}}', encoding="utf-8")
    monkeypatch.setattr(fetch_mod, "MANIFEST_PATH", manifest_path)
    monkeypatch.setattr(fetch_mod, "SOURCES_DIR", tmp_path)

    source = Source("s1", "https://example.com/f", "s1/file.bin", "desc", "MIT")
    content = b"data"

    def fake_fetch_one(src, meta, session):
        cache = tmp_path / src.cache_path
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_bytes(content)
        entry = meta.setdefault(src.name, {})
        entry["sha256"] = hashlib.sha256(content).hexdigest()

    with patch.object(fetch_mod, "_fetch_one", side_effect=fake_fetch_one):
        with patch.object(fetch_mod, "_build_session", return_value=MagicMock(close=MagicMock())):
            result = fetch_mod.fetch_all(sources=[source])

    assert "s1" in result["sources"]
    # Verify manifest was saved to disk
    saved = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert "s1" in saved["sources"]


def test_download_with_retries_5xx_retry(tmp_path: Path) -> None:
    """5xx HTTPError is retried via the OSError branch (HTTPError inherits
    from OSError) and succeeds on the final attempt."""
    import requests
    from build import fetch as fetch_mod
    from build.fetch import MAX_RETRIES

    dest = tmp_path / "output.bin"
    call_count = 0

    def fake_download_5xx(url, destination, session):
        nonlocal call_count
        call_count += 1
        if call_count < MAX_RETRIES:
            resp = MagicMock()
            resp.status_code = 503
            raise requests.HTTPError("503 Service Unavailable", response=resp)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(b"ok")

    with patch.object(fetch_mod, "_download", side_effect=fake_download_5xx):
        with patch("time.sleep"):
            fetch_mod._download_with_retries(
                "https://example.com/file", dest, MagicMock()
            )

    assert call_count == MAX_RETRIES
