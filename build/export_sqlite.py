"""Export the dataset as a single SQLite database.

Creates a queryable SQLite database with all core data tables and
cross-reference indices. This enables SQL queries across the entire
dataset without loading large JSON files into memory.

Output: ``dist/japanese-language-data.sqlite``

Run via ``just export-sqlite`` or ``python -m build.export_sqlite``.
"""

from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

from build.constants import DATA_DIR, MANIFEST_PATH, REPO_ROOT

DIST_DIR = REPO_ROOT / "dist"
OUT_DB = DIST_DIR / "japanese-language-data.sqlite"


def _load_json(path: Path) -> dict | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _create_schema(conn: sqlite3.Connection) -> None:
    """Create all tables."""
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS words (
            id TEXT PRIMARY KEY,
            kanji_primary TEXT,
            kana_primary TEXT,
            jlpt TEXT,
            common INTEGER,
            senses_json TEXT
        );

        CREATE TABLE IF NOT EXISTS kanji (
            character TEXT PRIMARY KEY,
            stroke_count INTEGER,
            grade INTEGER,
            jlpt TEXT,
            frequency INTEGER,
            readings_on TEXT,
            readings_kun TEXT,
            meanings_en TEXT
        );

        CREATE TABLE IF NOT EXISTS radicals (
            character TEXT PRIMARY KEY,
            kangxi_number INTEGER,
            stroke_count INTEGER,
            meaning_en TEXT
        );

        CREATE TABLE IF NOT EXISTS sentences (
            id TEXT PRIMARY KEY,
            japanese TEXT,
            english TEXT,
            source TEXT DEFAULT 'tatoeba'
        );

        CREATE TABLE IF NOT EXISTS grammar (
            id TEXT PRIMARY KEY,
            pattern TEXT,
            meaning_en TEXT,
            level TEXT,
            formality TEXT,
            formation TEXT,
            review_status TEXT
        );

        CREATE TABLE IF NOT EXISTS pitch_accent (
            text TEXT,
            reading TEXT,
            positions TEXT,
            mora_count INTEGER
        );

        CREATE TABLE IF NOT EXISTS frequency_corpus (
            text TEXT,
            reading TEXT,
            rank INTEGER,
            count INTEGER
        );

        CREATE TABLE IF NOT EXISTS frequency_subtitles (
            text TEXT,
            reading TEXT,
            rank INTEGER,
            count INTEGER
        );

        CREATE TABLE IF NOT EXISTS furigana (
            text TEXT,
            reading TEXT,
            segments_json TEXT
        );

        CREATE TABLE IF NOT EXISTS kanji_to_words (
            kanji TEXT,
            word_id TEXT
        );

        CREATE TABLE IF NOT EXISTS word_to_sentences (
            word_id TEXT,
            sentence_id TEXT
        );

        CREATE TABLE IF NOT EXISTS kanji_to_sentences (
            kanji TEXT,
            sentence_id TEXT
        );

        CREATE TABLE IF NOT EXISTS radical_to_kanji (
            radical TEXT,
            kanji TEXT
        );

        CREATE TABLE IF NOT EXISTS reading_to_words (
            reading TEXT,
            word_id TEXT
        );

        CREATE TABLE IF NOT EXISTS word_to_grammar (
            word_id TEXT,
            grammar_id TEXT
        );

        CREATE TABLE IF NOT EXISTS expressions (
            id TEXT PRIMARY KEY,
            text TEXT,
            reading TEXT,
            meanings_json TEXT,
            common INTEGER,
            jlpt TEXT
        );

        CREATE TABLE IF NOT EXISTS conjugations (
            dictionary_form TEXT,
            reading TEXT,
            class TEXT,
            forms_json TEXT,
            display_forms_json TEXT
        );

        CREATE TABLE IF NOT EXISTS counter_words (
            word_id TEXT,
            text TEXT,
            reading TEXT,
            meanings_json TEXT,
            jlpt TEXT
        );

        CREATE TABLE IF NOT EXISTS ateji (
            word_id TEXT,
            text TEXT,
            reading TEXT,
            meanings_json TEXT,
            jlpt TEXT
        );

        CREATE TABLE IF NOT EXISTS jlpt_classifications (
            kind TEXT,
            level TEXT,
            jmdict_seq TEXT,
            grammar_id TEXT,
            text TEXT,
            reading TEXT
        );

        -- Indexes for common queries
        CREATE INDEX IF NOT EXISTS idx_words_jlpt ON words(jlpt);
        CREATE INDEX IF NOT EXISTS idx_words_kanji ON words(kanji_primary);
        CREATE INDEX IF NOT EXISTS idx_kanji_grade ON kanji(grade);
        CREATE INDEX IF NOT EXISTS idx_kanji_jlpt ON kanji(jlpt);
        CREATE INDEX IF NOT EXISTS idx_sentences_source ON sentences(source);
        CREATE INDEX IF NOT EXISTS idx_grammar_level ON grammar(level);
        CREATE INDEX IF NOT EXISTS idx_pitch_text ON pitch_accent(text);
        CREATE INDEX IF NOT EXISTS idx_freq_rank ON frequency_corpus(rank);
        CREATE INDEX IF NOT EXISTS idx_freqsub_rank ON frequency_subtitles(rank);
        CREATE INDEX IF NOT EXISTS idx_freqsub_text ON frequency_subtitles(text);
        CREATE INDEX IF NOT EXISTS idx_furigana_text ON furigana(text);
        CREATE INDEX IF NOT EXISTS idx_k2w_kanji ON kanji_to_words(kanji);
        CREATE INDEX IF NOT EXISTS idx_w2s_word ON word_to_sentences(word_id);
        CREATE INDEX IF NOT EXISTS idx_k2s_kanji ON kanji_to_sentences(kanji);
        CREATE INDEX IF NOT EXISTS idx_r2k_radical ON radical_to_kanji(radical);
        CREATE INDEX IF NOT EXISTS idx_r2w_reading ON reading_to_words(reading);
        CREATE INDEX IF NOT EXISTS idx_w2g_word ON word_to_grammar(word_id);
        CREATE INDEX IF NOT EXISTS idx_exp_text ON expressions(text);
        CREATE INDEX IF NOT EXISTS idx_exp_jlpt ON expressions(jlpt);
        CREATE INDEX IF NOT EXISTS idx_conj_form ON conjugations(dictionary_form);
        CREATE INDEX IF NOT EXISTS idx_conj_class ON conjugations(class);
        CREATE INDEX IF NOT EXISTS idx_jlpt_level ON jlpt_classifications(level);
        CREATE INDEX IF NOT EXISTS idx_jlpt_kind ON jlpt_classifications(kind);
        CREATE INDEX IF NOT EXISTS idx_ctr_text ON counter_words(text);
        CREATE INDEX IF NOT EXISTS idx_ateji_text ON ateji(text);
    """)


def _insert_words(conn: sqlite3.Connection, data: dict) -> int:
    rows = []
    for w in data.get("words", []):
        kanji_list = w.get("kanji", []) or []
        kana_list = w.get("kana", []) or []
        rows.append((
            w.get("id", ""),
            kanji_list[0].get("text", "") if kanji_list else None,
            kana_list[0].get("text", "") if kana_list else None,
            w.get("jlpt_waller"),
            1 if any(
                tag in (k.get("tags", []) or [])
                for k in kanji_list + kana_list
                for tag in ("news1", "ichi1", "spec1", "spec2", "gai1")
            ) else 0,
            json.dumps(w.get("sense", []), ensure_ascii=False),
        ))
    conn.executemany("INSERT OR IGNORE INTO words VALUES (?,?,?,?,?,?)", rows)
    return len(rows)


def _insert_kanji(conn: sqlite3.Connection, data: dict) -> int:
    rows = []
    for k in data.get("kanji", []):
        readings = k.get("readings", {}) or {}
        meanings = k.get("meanings", {}) or {}
        rows.append((
            k.get("character", ""),
            k.get("stroke_count"),
            k.get("grade"),
            k.get("jlpt_waller"),
            k.get("frequency"),
            ", ".join(readings.get("on", []) or []),
            ", ".join(readings.get("kun", []) or []),
            ", ".join(meanings.get("en", []) or []),
        ))
    conn.executemany("INSERT OR IGNORE INTO kanji VALUES (?,?,?,?,?,?,?,?)", rows)
    return len(rows)


def _insert_sentences(conn: sqlite3.Connection, data: dict, source: str = "tatoeba") -> int:
    rows = [
        (str(s.get("id", "")), s.get("japanese", ""), s.get("english", ""), source)
        for s in data.get("sentences", [])
    ]
    conn.executemany("INSERT OR IGNORE INTO sentences VALUES (?,?,?,?)", rows)
    return len(rows)


def _insert_grammar(conn: sqlite3.Connection, data: dict) -> int:
    rows = [
        (g.get("id", ""), g.get("pattern", ""), g.get("meaning_en", ""),
         g.get("level", ""), g.get("formality", ""), g.get("formation", ""),
         g.get("review_status", "draft"))
        for g in data.get("grammar_points", [])
    ]
    conn.executemany("INSERT OR IGNORE INTO grammar VALUES (?,?,?,?,?,?,?)", rows)
    return len(rows)


def _insert_pitch(conn: sqlite3.Connection, data: dict) -> int:
    rows = [
        (e.get("text", ""), e.get("reading"), json.dumps(e.get("pitch_positions", [])),
         e.get("mora_count"))
        for e in data.get("entries", [])
    ]
    conn.executemany("INSERT OR IGNORE INTO pitch_accent VALUES (?,?,?,?)", rows)
    return len(rows)


def _insert_xref(conn: sqlite3.Connection, table: str, data: dict) -> int:
    mapping = data.get("mapping", {})
    rows = [(k, v) for k, vals in mapping.items() for v in vals]
    conn.executemany(f"INSERT INTO {table} VALUES (?,?)", rows)
    return len(rows)


def export() -> None:
    """Build the SQLite database."""
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    version = manifest.get("version", "dev")

    DIST_DIR.mkdir(parents=True, exist_ok=True)
    if OUT_DB.exists():
        OUT_DB.unlink()

    conn = sqlite3.connect(str(OUT_DB))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=OFF")

    print(f"[sqlite]   creating {OUT_DB.name} (v{version})")
    _create_schema(conn)

    # Core data
    words_data = _load_json(DATA_DIR / "core" / "words.json")
    if words_data:
        n = _insert_words(conn, words_data)
        print(f"[sqlite]   words: {n:,}")

    kanji_data = _load_json(DATA_DIR / "core" / "kanji.json")
    if kanji_data:
        n = _insert_kanji(conn, kanji_data)
        print(f"[sqlite]   kanji: {n:,}")

    radicals_data = _load_json(DATA_DIR / "core" / "radicals.json")
    if radicals_data:
        rows = [
            (r.get("character", ""), r.get("kangxi_number"),
             r.get("stroke_count"), r.get("meaning_en"))
            for r in radicals_data.get("radicals", [])
        ]
        conn.executemany("INSERT OR IGNORE INTO radicals VALUES (?,?,?,?)", rows)
        print(f"[sqlite]   radicals: {len(rows):,}")

    # Sentences
    sentences_data = _load_json(DATA_DIR / "corpus" / "sentences.json")
    if sentences_data:
        n = _insert_sentences(conn, sentences_data, "tatoeba")
        print(f"[sqlite]   sentences (tatoeba): {n:,}")

    kftt_data = _load_json(DATA_DIR / "corpus" / "sentences-kftt.json")
    if kftt_data:
        n = _insert_sentences(conn, kftt_data, "kftt")
        print(f"[sqlite]   sentences (kftt): {n:,}")

    # Grammar
    grammar_data = _load_json(DATA_DIR / "grammar" / "grammar.json")
    if grammar_data:
        n = _insert_grammar(conn, grammar_data)
        print(f"[sqlite]   grammar: {n:,}")

    # Enrichment
    pitch_data = _load_json(DATA_DIR / "enrichment" / "pitch-accent.json")
    if pitch_data:
        n = _insert_pitch(conn, pitch_data)
        print(f"[sqlite]   pitch accent: {n:,}")

    freq_data = _load_json(DATA_DIR / "enrichment" / "frequency-corpus.json")
    if freq_data:
        rows = [(e["text"], e.get("reading"), e["rank"], e.get("count"))
                for e in freq_data.get("entries", [])]
        conn.executemany("INSERT INTO frequency_corpus VALUES (?,?,?,?)", rows)
        print(f"[sqlite]   frequency: {len(rows):,}")

    freq_sub_data = _load_json(DATA_DIR / "enrichment" / "frequency-subtitles.json")
    if freq_sub_data:
        rows = [(e["text"], e.get("reading"), e["rank"], e.get("count"))
                for e in freq_sub_data.get("entries", [])]
        conn.executemany("INSERT INTO frequency_subtitles VALUES (?,?,?,?)", rows)
        print(f"[sqlite]   frequency (subtitles): {len(rows):,}")

    furigana_data = _load_json(DATA_DIR / "enrichment" / "furigana.json")
    if furigana_data:
        rows = [(e["text"], e["reading"], json.dumps(e["segments"], ensure_ascii=False))
                for e in furigana_data.get("entries", [])]
        conn.executemany("INSERT INTO furigana VALUES (?,?,?)", rows)
        print(f"[sqlite]   furigana: {len(rows):,}")

    # Expressions
    expr_data = _load_json(DATA_DIR / "grammar" / "expressions.json")
    if expr_data:
        rows = [
            (e.get("id", ""), e.get("text", ""), e.get("reading", ""),
             json.dumps(e.get("meanings", []), ensure_ascii=False),
             1 if e.get("common") else 0, e.get("jlpt_waller"))
            for e in expr_data.get("expressions", [])
        ]
        conn.executemany("INSERT OR IGNORE INTO expressions VALUES (?,?,?,?,?,?)", rows)
        print(f"[sqlite]   expressions: {len(rows):,}")

    # Conjugations
    conj_data = _load_json(DATA_DIR / "grammar" / "conjugations.json")
    if conj_data:
        rows = [
            (e.get("dictionary_form", ""), e.get("reading", ""), e.get("class", ""),
             json.dumps(e.get("forms", {}), ensure_ascii=False),
             json.dumps(e.get("display_forms", {}), ensure_ascii=False))
            for e in conj_data.get("entries", [])
        ]
        conn.executemany("INSERT INTO conjugations VALUES (?,?,?,?,?)", rows)
        print(f"[sqlite]   conjugations: {len(rows):,}")

    # JLPT classifications
    jlpt_data = _load_json(DATA_DIR / "enrichment" / "jlpt-classifications.json")
    if jlpt_data:
        rows = [
            (e.get("kind", ""), e.get("level", ""), e.get("jmdict_seq", ""),
             e.get("grammar_id", ""), e.get("text", ""), e.get("reading", ""))
            for e in jlpt_data.get("classifications", [])
        ]
        conn.executemany("INSERT INTO jlpt_classifications VALUES (?,?,?,?,?,?)", rows)
        print(f"[sqlite]   jlpt classifications: {len(rows):,}")

    # Counter words
    ctr_data = _load_json(DATA_DIR / "enrichment" / "counter-words.json")
    if ctr_data:
        rows = [
            (e.get("word_id", ""), e.get("text", ""), e.get("reading", ""),
             json.dumps(e.get("meanings", []), ensure_ascii=False), e.get("jlpt_waller"))
            for e in ctr_data.get("counter_words", [])
        ]
        conn.executemany("INSERT INTO counter_words VALUES (?,?,?,?,?)", rows)
        print(f"[sqlite]   counter words: {len(rows):,}")

    # Ateji
    ateji_data = _load_json(DATA_DIR / "enrichment" / "ateji.json")
    if ateji_data:
        rows = [
            (e.get("word_id", ""), e.get("text", ""), e.get("reading", ""),
             json.dumps(e.get("meanings", []), ensure_ascii=False), e.get("jlpt_waller"))
            for e in ateji_data.get("entries", [])
        ]
        conn.executemany("INSERT INTO ateji VALUES (?,?,?,?,?)", rows)
        print(f"[sqlite]   ateji: {len(rows):,}")

    # Cross-references
    for fname, table in [
        ("kanji-to-words.json", "kanji_to_words"),
        ("word-to-sentences.json", "word_to_sentences"),
        ("kanji-to-sentences.json", "kanji_to_sentences"),
        ("radical-to-kanji.json", "radical_to_kanji"),
        ("reading-to-words.json", "reading_to_words"),
        ("word-to-grammar.json", "word_to_grammar"),
    ]:
        xref_data = _load_json(DATA_DIR / "cross-refs" / fname)
        if xref_data:
            n = _insert_xref(conn, table, xref_data)
            print(f"[sqlite]   {table}: {n:,} rows")

    conn.commit()

    # Store version metadata
    conn.execute("CREATE TABLE IF NOT EXISTS _metadata (key TEXT PRIMARY KEY, value TEXT)")
    conn.execute("INSERT OR REPLACE INTO _metadata VALUES ('version', ?)", (version,))
    conn.execute("INSERT OR REPLACE INTO _metadata VALUES ('generated', ?)", (manifest.get("generated", ""),))
    conn.commit()
    conn.close()

    size = OUT_DB.stat().st_size
    print(f"[sqlite]   wrote {OUT_DB.relative_to(REPO_ROOT)} ({size:,} bytes, {size/1024/1024:.1f} MB)")


def main() -> int:
    export()
    return 0


if __name__ == "__main__":
    sys.exit(main())
