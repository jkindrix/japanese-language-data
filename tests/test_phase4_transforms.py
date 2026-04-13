"""Unit tests for Phase 4 transform modules.

Covers modules that had zero or near-zero test coverage:
    * sentence_difficulty: _build_word_jlpt_lookup, _build_kanji_jlpt_lookup,
      _score_sentence
    * sentences_full: _load_sentences, _load_links
    * word_relations: build() with synthetic data
    * wordnet: _extract() with in-memory SQLite
    * jesc: build() with synthetic tar.gz
    * wikimatrix: build() with synthetic zip
"""

from __future__ import annotations

import bz2
import io
import json
import sqlite3
import sys
import tarfile
import tempfile
import zipfile
from pathlib import Path
from unittest.mock import patch

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


# ---------------------------------------------------------------------------
# sentence_difficulty
# ---------------------------------------------------------------------------


class TestSentenceDifficultyHelpers:
    """Tests for sentence_difficulty private helper functions."""

    def test_build_word_jlpt_lookup_basic(self) -> None:
        from build.transform.sentence_difficulty import _build_word_jlpt_lookup

        words_data = {
            "words": [
                {
                    "id": "1000",
                    "kanji": [{"text": "食べる"}],
                    "kana": [{"text": "たべる"}],
                    "sense": [],
                },
            ]
        }
        jlpt_data = {
            "classifications": [
                {"kind": "vocab", "jmdict_seq": "1000", "level": "N5"},
            ]
        }
        lookup = _build_word_jlpt_lookup(words_data, jlpt_data)
        assert lookup["食べる"] == "N5"
        assert lookup["たべる"] == "N5"

    def test_build_word_jlpt_lookup_easier_level_wins(self) -> None:
        from build.transform.sentence_difficulty import _build_word_jlpt_lookup

        words_data = {
            "words": [
                {
                    "id": "1000",
                    "kanji": [{"text": "行く"}],
                    "kana": [{"text": "いく"}],
                    "sense": [],
                },
            ]
        }
        jlpt_data = {
            "classifications": [
                {"kind": "vocab", "jmdict_seq": "1000", "level": "N3"},
                {"kind": "vocab", "jmdict_seq": "1000", "level": "N5"},
            ]
        }
        lookup = _build_word_jlpt_lookup(words_data, jlpt_data)
        assert lookup["行く"] == "N5"  # easier level wins

    def test_build_word_jlpt_lookup_short_kana_excluded(self) -> None:
        from build.transform.sentence_difficulty import _build_word_jlpt_lookup

        words_data = {
            "words": [
                {
                    "id": "2000",
                    "kanji": [],
                    "kana": [{"text": "の"}],  # 1 char, too short
                    "sense": [],
                },
            ]
        }
        jlpt_data = {
            "classifications": [
                {"kind": "vocab", "jmdict_seq": "2000", "level": "N5"},
            ]
        }
        lookup = _build_word_jlpt_lookup(words_data, jlpt_data)
        assert "の" not in lookup  # single-char kana excluded

    def test_build_word_jlpt_lookup_short_kanji_excluded(self) -> None:
        from build.transform.sentence_difficulty import _build_word_jlpt_lookup

        words_data = {
            "words": [
                {
                    "id": "3000",
                    "kanji": [{"text": "木"}],  # 1 char kanji, too short
                    "kana": [{"text": "き"}],
                    "sense": [],
                },
            ]
        }
        jlpt_data = {
            "classifications": [
                {"kind": "vocab", "jmdict_seq": "3000", "level": "N4"},
            ]
        }
        lookup = _build_word_jlpt_lookup(words_data, jlpt_data)
        assert "木" not in lookup

    def test_build_word_jlpt_lookup_no_jlpt(self) -> None:
        from build.transform.sentence_difficulty import _build_word_jlpt_lookup

        words_data = {
            "words": [
                {
                    "id": "5000",
                    "kanji": [{"text": "珍妙"}],
                    "kana": [],
                    "sense": [],
                },
            ]
        }
        jlpt_data = {"classifications": []}
        lookup = _build_word_jlpt_lookup(words_data, jlpt_data)
        assert "珍妙" not in lookup

    def test_build_word_jlpt_lookup_skips_non_vocab(self) -> None:
        from build.transform.sentence_difficulty import _build_word_jlpt_lookup

        words_data = {"words": []}
        jlpt_data = {
            "classifications": [
                {"kind": "kanji", "text": "食", "level": "N5"},
            ]
        }
        lookup = _build_word_jlpt_lookup(words_data, jlpt_data)
        assert len(lookup) == 0

    def test_build_kanji_jlpt_lookup(self) -> None:
        from build.transform.sentence_difficulty import _build_kanji_jlpt_lookup

        jlpt_data = {
            "classifications": [
                {"kind": "kanji", "text": "食", "level": "N4"},
                {"kind": "kanji", "text": "日", "level": "N5"},
                {"kind": "vocab", "jmdict_seq": "1000", "level": "N5"},
            ]
        }
        lookup = _build_kanji_jlpt_lookup(jlpt_data)
        assert lookup["食"] == "N4"
        assert lookup["日"] == "N5"
        assert "1000" not in lookup  # vocab entries excluded

    def test_score_sentence_n5(self) -> None:
        from build.transform.sentence_difficulty import _score_sentence

        word_lookup = {"食べる": "N5"}
        kanji_lookup = {}
        level, level_int, matched = _score_sentence(
            "私は食べる", word_lookup, kanji_lookup
        )
        assert level == "N5"
        assert level_int == 1
        assert "食べる" in matched

    def test_score_sentence_max_level(self) -> None:
        from build.transform.sentence_difficulty import _score_sentence

        word_lookup = {"食べる": "N5", "難しい": "N3"}
        kanji_lookup = {}
        level, level_int, matched = _score_sentence(
            "食べるのは難しい", word_lookup, kanji_lookup
        )
        assert level == "N3"
        assert level_int == 3

    def test_score_sentence_kanji_upgrades_level(self) -> None:
        from build.transform.sentence_difficulty import _score_sentence

        word_lookup = {"食べる": "N5"}
        kanji_lookup = {"鬱": "N1"}
        level, level_int, _ = _score_sentence(
            "鬱な食べる", word_lookup, kanji_lookup
        )
        assert level == "N1"
        assert level_int == 5

    def test_score_sentence_unscored(self) -> None:
        from build.transform.sentence_difficulty import _score_sentence

        level, level_int, matched = _score_sentence("hello", {}, {})
        assert level is None
        assert level_int == 0
        assert matched == []

    def test_score_sentence_empty(self) -> None:
        from build.transform.sentence_difficulty import _score_sentence

        level, level_int, matched = _score_sentence("", {}, {})
        assert level is None
        assert level_int == 0

    def test_level_constants(self) -> None:
        from build.transform.sentence_difficulty import LEVEL_FROM_INT, LEVEL_ORDER

        assert LEVEL_ORDER["N5"] == 1
        assert LEVEL_ORDER["N1"] == 5
        assert LEVEL_FROM_INT[1] == "N5"
        assert LEVEL_FROM_INT[5] == "N1"


# ---------------------------------------------------------------------------
# sentences_full
# ---------------------------------------------------------------------------


class TestSentencesFullHelpers:
    """Tests for sentences_full private helper functions."""

    def test_load_sentences(self, tmp_path: Path) -> None:
        from build.transform.sentences_full import _load_sentences

        tsv = "100\tjpn\tこれはテストです。\n200\tjpn\t二番目の文。\n"
        bz2_path = tmp_path / "test.tsv.bz2"
        bz2_path.write_bytes(bz2.compress(tsv.encode("utf-8")))

        result = _load_sentences(bz2_path)
        assert result["100"] == "これはテストです。"
        assert result["200"] == "二番目の文。"

    def test_load_sentences_malformed_line(self, tmp_path: Path) -> None:
        from build.transform.sentences_full import _load_sentences

        tsv = "100\tjpn\t良い文\nbadline\n300\tjpn\tまた良い文\n"
        bz2_path = tmp_path / "test.tsv.bz2"
        bz2_path.write_bytes(bz2.compress(tsv.encode("utf-8")))

        result = _load_sentences(bz2_path)
        assert "100" in result
        assert "300" in result
        # badline has < 3 parts, should be skipped
        assert len(result) == 2

    def test_load_links(self, tmp_path: Path) -> None:
        from build.transform.sentences_full import _load_links

        links_content = "100\t500\n100\t501\n200\t600\n300\t700\n"
        links_path = tmp_path / "links.csv"
        links_path.write_text(links_content, encoding="utf-8")

        jpn_ids = {"100", "200"}
        eng_ids = {"500", "501", "600"}

        result = _load_links(links_path, jpn_ids, eng_ids)
        assert "100" in result
        assert len(result["100"]) == 2
        assert "200" in result
        # 300 not in jpn_ids, should be excluded
        assert "300" not in result

    def test_load_links_filters_unknown_ids(self, tmp_path: Path) -> None:
        from build.transform.sentences_full import _load_links

        links_content = "100\t999\n"
        links_path = tmp_path / "links.csv"
        links_path.write_text(links_content, encoding="utf-8")

        # 999 not in eng_ids
        result = _load_links(links_path, {"100"}, {"500"})
        assert "100" not in result


# ---------------------------------------------------------------------------
# word_relations — test through build() with synthetic words.json
# ---------------------------------------------------------------------------


class TestWordRelations:
    """Tests for word_relations module using synthetic word data."""

    def test_build_with_related_refs(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        import build.transform.word_relations as wr

        words_data = {
            "words": [
                {
                    "id": "100",
                    "kanji": [{"text": "大きい"}],
                    "kana": [{"text": "おおきい"}],
                    "sense": [
                        {"related": [["小さい"]], "antonym": [["小さい"]]},
                    ],
                },
                {
                    "id": "200",
                    "kanji": [{"text": "小さい"}],
                    "kana": [{"text": "ちいさい"}],
                    "sense": [],
                },
            ]
        }

        words_file = tmp_path / "words.json"
        words_file.write_text(json.dumps(words_data), encoding="utf-8")
        out_file = tmp_path / "word-relations.json"

        monkeypatch.setattr(wr, "WORDS_JSON", words_file)
        monkeypatch.setattr(wr, "OUT", out_file)
        monkeypatch.setattr(wr, "REPO_ROOT", tmp_path)

        wr.build()

        result = json.loads(out_file.read_text(encoding="utf-8"))
        rels = result["relations"]
        assert len(rels) == 2  # one related + one antonym
        rel_types = {r["relation"] for r in rels}
        assert rel_types == {"related", "antonym"}

    def test_build_deduplicates(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        import build.transform.word_relations as wr

        words_data = {
            "words": [
                {
                    "id": "100",
                    "kanji": [{"text": "見る"}],
                    "kana": [],
                    "sense": [
                        {"related": [["観る"]], "antonym": []},
                        {"related": [["観る"]], "antonym": []},  # dup
                    ],
                },
                {
                    "id": "200",
                    "kanji": [{"text": "観る"}],
                    "kana": [],
                    "sense": [],
                },
            ]
        }

        words_file = tmp_path / "words.json"
        words_file.write_text(json.dumps(words_data), encoding="utf-8")
        out_file = tmp_path / "word-relations.json"

        monkeypatch.setattr(wr, "WORDS_JSON", words_file)
        monkeypatch.setattr(wr, "OUT", out_file)
        monkeypatch.setattr(wr, "REPO_ROOT", tmp_path)

        wr.build()

        result = json.loads(out_file.read_text(encoding="utf-8"))
        assert len(result["relations"]) == 1  # deduped

    def test_build_unresolved_refs(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        import build.transform.word_relations as wr

        words_data = {
            "words": [
                {
                    "id": "100",
                    "kanji": [{"text": "食べる"}],
                    "kana": [],
                    "sense": [
                        {"related": [["存在しない語"]], "antonym": []},
                    ],
                },
            ]
        }

        words_file = tmp_path / "words.json"
        words_file.write_text(json.dumps(words_data), encoding="utf-8")
        out_file = tmp_path / "word-relations.json"

        monkeypatch.setattr(wr, "WORDS_JSON", words_file)
        monkeypatch.setattr(wr, "OUT", out_file)
        monkeypatch.setattr(wr, "REPO_ROOT", tmp_path)

        wr.build()

        result = json.loads(out_file.read_text(encoding="utf-8"))
        assert len(result["relations"]) == 0
        assert result["metadata"]["unresolved_count"] == 1

    def test_build_missing_source_raises(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        import build.transform.word_relations as wr

        monkeypatch.setattr(wr, "WORDS_JSON", tmp_path / "nonexistent.json")
        with pytest.raises(FileNotFoundError):
            wr.build()


# ---------------------------------------------------------------------------
# wordnet — test _extract() with in-memory SQLite
# ---------------------------------------------------------------------------


class TestWordNetExtract:
    """Tests for wordnet._extract() using an in-memory SQLite database."""

    @staticmethod
    def _create_test_db() -> sqlite3.Connection:
        """Create a minimal wn-ja compatible SQLite database."""
        conn = sqlite3.connect(":memory:")
        cur = conn.cursor()
        cur.execute("CREATE TABLE word (wordid TEXT, lang TEXT, lemma TEXT)")
        cur.execute("CREATE TABLE sense (synset TEXT, wordid TEXT, rank INTEGER)")
        cur.execute("CREATE TABLE synset_def (synset TEXT, lang TEXT, def TEXT)")
        cur.execute("CREATE TABLE synlink (synset1 TEXT, synset2 TEXT, link TEXT)")

        # Add Japanese words
        cur.execute("INSERT INTO word VALUES ('w1', 'jpn', '犬')")
        cur.execute("INSERT INTO word VALUES ('w2', 'jpn', 'いぬ')")
        cur.execute("INSERT INTO word VALUES ('w3', 'jpn', '猫')")
        cur.execute("INSERT INTO word VALUES ('w4', 'jpn', '動物')")

        # Link to synsets
        cur.execute("INSERT INTO sense VALUES ('syn-dog', 'w1', 1)")
        cur.execute("INSERT INTO sense VALUES ('syn-dog', 'w2', 2)")
        cur.execute("INSERT INTO sense VALUES ('syn-cat', 'w3', 1)")
        cur.execute("INSERT INTO sense VALUES ('syn-animal', 'w4', 1)")

        # Definitions
        cur.execute("INSERT INTO synset_def VALUES ('syn-dog', 'eng', 'a domesticated canine')")
        cur.execute("INSERT INTO synset_def VALUES ('syn-dog', 'jpn', '家畜化されたイヌ科の動物')")
        cur.execute("INSERT INTO synset_def VALUES ('syn-cat', 'eng', 'a small domesticated feline')")
        cur.execute("INSERT INTO synset_def VALUES ('syn-animal', 'eng', 'a living organism')")

        # Hypernym: dog IS-A animal
        cur.execute("INSERT INTO synlink VALUES ('syn-dog', 'syn-animal', 'hype')")
        cur.execute("INSERT INTO synlink VALUES ('syn-cat', 'syn-animal', 'hype')")

        conn.commit()
        return conn

    def test_extract_synonym_pairs(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        import build.transform.wordnet as wn

        conn = self._create_test_db()
        out_file = tmp_path / "wordnet-synonyms.json"
        monkeypatch.setattr(wn, "OUT", out_file)
        monkeypatch.setattr(wn, "REPO_ROOT", tmp_path)

        wn._extract(conn)
        conn.close()

        result = json.loads(out_file.read_text(encoding="utf-8"))
        synonyms = [r for r in result["relations"] if r["relation"] == "synonym"]
        # 犬 and いぬ share syn-dog
        assert len(synonyms) == 1
        assert {synonyms[0]["word_a"], synonyms[0]["word_b"]} == {"犬", "いぬ"}

    def test_extract_hypernym_pairs(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        import build.transform.wordnet as wn

        conn = self._create_test_db()
        out_file = tmp_path / "wordnet-synonyms.json"
        monkeypatch.setattr(wn, "OUT", out_file)
        monkeypatch.setattr(wn, "REPO_ROOT", tmp_path)

        wn._extract(conn)
        conn.close()

        result = json.loads(out_file.read_text(encoding="utf-8"))
        hypernyms = [r for r in result["relations"] if r["relation"] == "hypernym"]
        # dog→animal and cat→animal
        assert len(hypernyms) == 2
        targets = {h["word_b"] for h in hypernyms}
        assert "動物" in targets

    def test_extract_synset_groups(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        import build.transform.wordnet as wn

        conn = self._create_test_db()
        out_file = tmp_path / "wordnet-synonyms.json"
        monkeypatch.setattr(wn, "OUT", out_file)
        monkeypatch.setattr(wn, "REPO_ROOT", tmp_path)

        wn._extract(conn)
        conn.close()

        result = json.loads(out_file.read_text(encoding="utf-8"))
        groups = result["synset_groups"]
        # Only syn-dog has 2+ words
        assert len(groups) == 1
        assert groups[0]["synset_id"] == "syn-dog"
        assert set(groups[0]["words"]) == {"犬", "いぬ"}

    def test_extract_metadata(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        import build.transform.wordnet as wn

        conn = self._create_test_db()
        out_file = tmp_path / "wordnet-synonyms.json"
        monkeypatch.setattr(wn, "OUT", out_file)
        monkeypatch.setattr(wn, "REPO_ROOT", tmp_path)

        wn._extract(conn)
        conn.close()

        result = json.loads(out_file.read_text(encoding="utf-8"))
        meta = result["metadata"]
        assert meta["synonym_count"] == 1
        assert meta["hypernym_count"] == 2
        assert meta["synset_group_count"] == 1
        assert meta["unique_words"] == 4

    def test_extract_empty_db(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        import build.transform.wordnet as wn

        conn = sqlite3.connect(":memory:")
        cur = conn.cursor()
        cur.execute("CREATE TABLE word (wordid TEXT, lang TEXT, lemma TEXT)")
        cur.execute("CREATE TABLE sense (synset TEXT, wordid TEXT, rank INTEGER)")
        cur.execute("CREATE TABLE synset_def (synset TEXT, lang TEXT, def TEXT)")
        cur.execute("CREATE TABLE synlink (synset1 TEXT, synset2 TEXT, link TEXT)")
        conn.commit()

        out_file = tmp_path / "wordnet-synonyms.json"
        monkeypatch.setattr(wn, "OUT", out_file)
        monkeypatch.setattr(wn, "REPO_ROOT", tmp_path)

        wn._extract(conn)
        conn.close()

        result = json.loads(out_file.read_text(encoding="utf-8"))
        assert result["metadata"]["count"] == 0
        assert result["relations"] == []
        assert result["synset_groups"] == []


# ---------------------------------------------------------------------------
# jesc — test build() with a synthetic tar.gz
# ---------------------------------------------------------------------------


class TestJesc:
    """Tests for jesc.build() with synthetic data."""

    def test_build_basic(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        import build.transform.jesc as jesc_mod

        # Create a synthetic tar.gz with tab-separated EN\tJA lines
        content = "Hello world\tこんにちは世界\nGoodbye\tさようなら\n"
        buf = io.BytesIO()
        with tarfile.open(fileobj=buf, mode="w:gz") as tf:
            data = content.encode("utf-8")
            info = tarfile.TarInfo(name="raw")
            info.size = len(data)
            tf.addfile(info, io.BytesIO(data))

        tgz_path = tmp_path / "raw.tar.gz"
        tgz_path.write_bytes(buf.getvalue())
        out_path = tmp_path / "sentences-jesc.json"

        monkeypatch.setattr(jesc_mod, "SOURCE_TGZ", tgz_path)
        monkeypatch.setattr(jesc_mod, "OUT", out_path)
        monkeypatch.setattr(jesc_mod, "REPO_ROOT", tmp_path)

        jesc_mod.build()

        result = json.loads(out_path.read_text(encoding="utf-8"))
        assert result["metadata"]["count"] == 2
        assert len(result["sentences"]) == 2
        assert result["sentences"][0]["id"] == "jesc-1"
        assert result["sentences"][0]["japanese"] == "こんにちは世界"
        assert result["sentences"][0]["english"] == "Hello world"
        assert result["sentences"][0]["curated"] is False

    def test_build_skips_bad_lines(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        import build.transform.jesc as jesc_mod

        content = "Good\t良い\nbadline\n\t\nAlso good\tまた良い\n"
        buf = io.BytesIO()
        with tarfile.open(fileobj=buf, mode="w:gz") as tf:
            data = content.encode("utf-8")
            info = tarfile.TarInfo(name="raw")
            info.size = len(data)
            tf.addfile(info, io.BytesIO(data))

        tgz_path = tmp_path / "raw.tar.gz"
        tgz_path.write_bytes(buf.getvalue())
        out_path = tmp_path / "out.json"

        monkeypatch.setattr(jesc_mod, "SOURCE_TGZ", tgz_path)
        monkeypatch.setattr(jesc_mod, "OUT", out_path)
        monkeypatch.setattr(jesc_mod, "REPO_ROOT", tmp_path)

        jesc_mod.build()

        result = json.loads(out_path.read_text(encoding="utf-8"))
        assert result["metadata"]["count"] == 2

    def test_build_missing_source_raises(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        import build.transform.jesc as jesc_mod

        monkeypatch.setattr(jesc_mod, "SOURCE_TGZ", tmp_path / "nonexistent.tar.gz")
        with pytest.raises(FileNotFoundError):
            jesc_mod.build()

    def test_build_empty_archive_raises(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        import build.transform.jesc as jesc_mod

        buf = io.BytesIO()
        with tarfile.open(fileobj=buf, mode="w:gz"):
            pass  # empty archive

        tgz_path = tmp_path / "raw.tar.gz"
        tgz_path.write_bytes(buf.getvalue())

        monkeypatch.setattr(jesc_mod, "SOURCE_TGZ", tgz_path)
        monkeypatch.setattr(jesc_mod, "OUT", tmp_path / "out.json")

        with pytest.raises(RuntimeError, match="No file found"):
            jesc_mod.build()


# ---------------------------------------------------------------------------
# wikimatrix — test build() with a synthetic zip
# ---------------------------------------------------------------------------


class TestWikiMatrix:
    """Tests for wikimatrix.build() with synthetic data."""

    def test_build_basic(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        import build.transform.wikimatrix as wm

        zip_path = tmp_path / "en-ja.txt.zip"
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("WikiMatrix.en-ja.ja", "こんにちは\nさようなら\n")
            zf.writestr("WikiMatrix.en-ja.en", "Hello\nGoodbye\n")

        out_path = tmp_path / "out.json"
        monkeypatch.setattr(wm, "SOURCE_ZIP", zip_path)
        monkeypatch.setattr(wm, "OUT", out_path)
        monkeypatch.setattr(wm, "REPO_ROOT", tmp_path)

        wm.build()

        result = json.loads(out_path.read_text(encoding="utf-8"))
        assert result["metadata"]["count"] == 2
        sents = result["sentences"]
        assert sents[0]["id"] == "wikimatrix-1"
        assert sents[0]["japanese"] == "こんにちは"
        assert sents[0]["english"] == "Hello"
        assert sents[0]["curated"] is False

    def test_build_skips_empty_lines(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        import build.transform.wikimatrix as wm

        zip_path = tmp_path / "en-ja.txt.zip"
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("data.ja", "一\n\n三\n")
            zf.writestr("data.en", "one\n\nthree\n")

        out_path = tmp_path / "out.json"
        monkeypatch.setattr(wm, "SOURCE_ZIP", zip_path)
        monkeypatch.setattr(wm, "OUT", out_path)
        monkeypatch.setattr(wm, "REPO_ROOT", tmp_path)

        wm.build()

        result = json.loads(out_path.read_text(encoding="utf-8"))
        assert result["metadata"]["count"] == 2  # empty line skipped

    def test_build_missing_source_raises(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        import build.transform.wikimatrix as wm

        monkeypatch.setattr(wm, "SOURCE_ZIP", tmp_path / "nonexistent.zip")
        with pytest.raises(FileNotFoundError):
            wm.build()

    def test_build_line_count_mismatch_raises(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        import build.transform.wikimatrix as wm

        zip_path = tmp_path / "en-ja.txt.zip"
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("data.ja", "一\n二\n三\n")
            zf.writestr("data.en", "one\ntwo\n")

        monkeypatch.setattr(wm, "SOURCE_ZIP", zip_path)
        monkeypatch.setattr(wm, "OUT", tmp_path / "out.json")

        with pytest.raises(RuntimeError, match="Line count mismatch"):
            wm.build()

    def test_build_missing_language_files_raises(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        import build.transform.wikimatrix as wm

        zip_path = tmp_path / "en-ja.txt.zip"
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("readme.txt", "no language files here")

        monkeypatch.setattr(wm, "SOURCE_ZIP", zip_path)
        monkeypatch.setattr(wm, "OUT", tmp_path / "out.json")

        with pytest.raises(RuntimeError, match="Could not find"):
            wm.build()
