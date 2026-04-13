# Phase 4 candidates

Phase 4 is the "and beyond" phase — the domains where we extend the dataset past its core learner-oriented scope into specialized or supplementary territory. Phase 4 is deliberately deferred until Phases 0–3 are stable, because those are the value-dense foundation and Phase 4 items are all optional add-ons.

This document catalogs every candidate that has been raised, with enough detail that a decision to promote (or not) any of them can be made without re-researching the landscape.

Status values:

- **NOT EVALUATED** — on the list, needs research.
- **EVALUATED** — researched; decision pending.
- **PROMOTED** — scheduled for a specific phase.
- **REJECTED** — evaluated and declined; reason recorded.

---

## Handwriting and OCR data

### Kuzushiji-Kanji (KKanji) dataset

- **Source**: ROIS-DS Center for Open Data in the Humanities (CODH), via the "Deep Learning for Classical Japanese Literature" project.
- **URL**: https://github.com/rois-codh/kmnist (Kuzushiji-MNIST), https://datasets.activeloop.ai/docs/ml/datasets/kuzushiji-kanji-kkanji-dataset/ (Kuzushiji-Kanji)
- **Scale**: 140,426 images of 3,832 classical kanji classes, 64×64 pixel grayscale.
- **License**: CC-BY-SA 4.0 (compatible).
- **Format**: Image arrays in NumPy format or raw PNG.
- **Effort to integrate**: Small. Download, extract, organize by class, index in JSON.
- **Value**: Useful for classical text recognition, historical text processing, ML applications that need training data. Not useful for modern learners.
- **Status**: NOT EVALUATED. Straightforward to add if we commit to scope expansion. Would need a `data/phase4/kuzushiji/` subdirectory with the images, which would significantly increase repo size (~200+ MB).
- **Recommendation**: Add as a linked supplement only — do not bundle the images. Provide a `data/phase4/kuzushiji-manifest.json` with download URLs and metadata.

### Kuzushiji-MNIST

- **Source**: Same as above.
- **Scale**: 70,000 28×28 grayscale images of 10 hiragana classes.
- **License**: CC-BY-SA 4.0.
- **Value**: Demonstration dataset; drop-in replacement for MNIST in ML experiments. Limited learner utility.
- **Status**: NOT EVALUATED. Same linking strategy as KKanji if we include it.

### ETL Character Database

- **Source**: AIST (National Institute of Advanced Industrial Science and Technology), Japan.
- **URL**: http://etlcdb.db.aist.go.jp/the-etl-character-database/
- **Scale**: ~1.2 million handwritten and printed character images (alphanumeric, hiragana, katakana, kanji from JIS levels 1 and 2).
- **License**: AIST Terms of Use — not CC-BY-SA. Use is generally permitted for research; commercial use and redistribution have specific constraints.
- **Format**: Custom binary format (per the original 1973–1984 collection). Extraction utilities exist (e.g., `etlcdb-image-extractor`).
- **Effort to integrate**: Medium. License review + extraction pipeline + storage strategy.
- **Value**: Comprehensive handwriting dataset; useful for OCR, handwriting recognition ML, writing pedagogy. The ground truth for modern handwritten Japanese character recognition.
- **Status**: NOT EVALUATED. License incompatibility with CC-BY-SA 4.0 means we cannot bundle it — only link.
- **Recommendation**: Link-only manifest in `data/phase4/etl-manifest.json`. Include metadata (character set, collection date, sample counts per class) but do not redistribute images.

### manga-ocr training data

- **Source**: kha-white/manga-ocr, various contributors.
- **URL**: https://github.com/kha-white/manga-ocr
- **License**: Various (the tool is Apache 2.0; training data has its own situation).
- **Effort**: Medium-high.
- **Value**: Very specialized. Useful for manga-specific OCR but not general learners.
- **Status**: REJECTED for Phase 4 core scope. Out of scope for a general-purpose learner dataset.

---

## Speech and audio

### JSUT corpus

- **Source**: Shinnosuke Takamichi, University of Tokyo.
- **URL**: https://sites.google.com/site/shinnosuketakamichi/publication/jsut
- **Scale**: 10 hours of single-speaker reading speech, with full transcripts covering most daily-use kana combinations and kanji compounds.
- **License**: Research-use friendly; commercial use requires contacting the maintainer.
- **Format**: WAV audio files + transcript CSV.
- **Effort to integrate**: Low for transcripts, medium for audio redistribution.
- **Value**: Good for TTS development and phonetic training data.
- **Status**: NOT EVALUATED. The license restriction likely means we cannot bundle the audio, only the transcripts (which we could use as a supplementary pronunciation corpus).

### JVS corpus

- **Source**: Same group as JSUT.
- **URL**: https://sites.google.com/site/shinnosuketakamichi/research-topics/jvs_corpus
- **Scale**: 100 speakers, 30 hours of voice data in three styles (normal/whisper/falsetto).
- **License**: Tags CC-BY-SA 4.0; audio has per-use restrictions.
- **Value**: Multi-speaker voice conversion and TTS research. Specialized.
- **Status**: NOT EVALUATED. Tags are compatible and could be included; audio would require linking.

### Mozilla Common Voice Japanese

- **Source**: Mozilla Foundation.
- **URL**: https://commonvoice.mozilla.org/datasets
- **Scale**: Varies by release; historically 30–100+ hours of crowd-sourced Japanese voice data.
- **License**: CC0 (fully open, no restrictions).
- **Format**: MP3 audio + transcript TSV.
- **Effort to integrate**: Low for transcripts, medium for bundled audio.
- **Value**: Open speech dataset usable for any purpose; good for STT/speech modeling. Limited learner value directly but useful for building apps with voice features.
- **Status**: **PIPELINE READY**. Transform code delivered (`build/transform/common_voice.py`). Requires manual download (Mozilla account authentication) of `validated.tsv` to `sources/common-voice/`. Output: `data/phase4/common-voice-transcripts.json` (gitignored, built on demand). Deduplicates by NFKC text, aggregates vote counts. CC-0.

---

## Text corpora

### Aozora Bunko

- **Source**: Aozora Bunko project.
- **URL**: https://www.aozora.gr.jp/
- **Scale**: 17,000+ public-domain Japanese literary works (classical, Meiji, Taishō, early Shōwa, some modern).
- **License**: Japanese public domain, per-work. Some works are still under copyright. Strict per-work audit required.
- **Format**: Plain text, XHTML, or annotated XHTML. Ruby (furigana) preserved in some works.
- **Effort to integrate**: High. Per-work license audit, text normalization, metadata extraction (author, era, genre), splitting for manageable units.
- **Value**: Enormous for reading practice, classical Japanese exposure, literary vocabulary, historical context.
- **Status**: **DELIVERED (v0.8.0+)**. Initial curated corpus of 14 public-domain works by 7 authors (Soseki, Akutagawa, Dazai, Miyazawa, Nakajima, Mori, Higuchi — all died before 1955). Transform: `build/transform/aozora.py`. Output: `data/phase4/aozora-corpus.json` (gitignored, built on demand). ~620K chars with ruby extraction. Catalog auto-downloaded from aozora.gr.jp.
- **Recommendation**: Expand the curated selection beyond the initial 14 works. All authors with 著作権なし in the catalog and death year ≤1967 are safe.

### Wikipedia Japanese

- **Source**: Wikimedia dumps.
- **URL**: https://dumps.wikimedia.org/jawiki/
- **Scale**: ~1.4 million articles.
- **License**: CC-BY-SA 4.0 (compatible).
- **Format**: MediaWiki XML dumps; parsed via libraries like mwparserfromhell.
- **Effort to integrate**: High. Parsing MediaWiki markup is non-trivial; extracting clean text and structured metadata requires real work.
- **Value**: Enormous text corpus, modern Japanese, topic-diverse. Also a source of named-entity data and cross-linguistic links.
- **Status**: NOT EVALUATED. Large effort. Value depends on intended use cases.
- **Recommendation**: Defer until there is a concrete use case (e.g., a reading-difficulty rating system or an NLP training pipeline) that would benefit.

### Wiktionary Japanese

- **Source**: Wikimedia dumps.
- **URL**: https://dumps.wikimedia.org/enwiktionary/ and /jawiktionary/
- **Scale**: Tens of thousands of Japanese entries with variable depth.
- **License**: CC-BY-SA 4.0 (compatible).
- **Effort to integrate**: Medium-high. Wiktionary entries are free-form and inconsistent; extracting structured data (readings, pitch, meanings, examples) requires per-template parsing.
- **Value**: Secondary coverage of vocabulary that JMdict may lack; per-entry etymology notes; pitch accent for some modern terms. Filling the post-2022 Kanjium gap is one concrete use case.
- **Status**: **DELIVERED (v0.8.0+)**. Pitch accent extracted from Japanese Wiktionary via kaikki.org/wiktextract pre-processed JSONL. 7,378 entries not in Kanjium, covering post-2022 vocabulary gap. Accent type tags (Heiban, Atamadaka, Nakadaka, Odaka) converted to numeric mora positions. Output: `data/enrichment/pitch-accent-wiktionary.json`. Did NOT require mwparserfromhell — used kaikki.org structured data instead.
- **Recommendation**: Re-extract periodically from kaikki.org as Wiktionary coverage grows. The committed JSON is the version pin (kaikki.org URLs are not stable).

### KFTT (Kyoto Free Translation Task)

- **URL**: http://www.phontron.com/kftt/
- **Scale**: ~440k Japanese-English parallel sentences from Wikipedia articles.
- **License**: CC-BY-SA 3.0.
- **Effort**: Low. Already in TSV.
- **Value**: Supplementary parallel corpus; larger than Tatoeba's subset for Japanese.
- **Status**: **DELIVERED (v0.8.0)**. Integrated as `data/corpus/sentences-kftt.json` (443,849 JP-EN pairs). Upstream pinned in `manifest.json` with SHA256 verification. Gitignored due to size (~220 MB); built on demand.

### JParaCrawl

- **URL**: https://www.kecl.ntt.co.jp/icl/lirg/jparacrawl/
- **Scale**: ~25 million parallel sentences.
- **License**: Commercial use permitted but requires agreement; varies by version.
- **Effort**: High. License review + massive scale handling.
- **Status**: NOT EVALUATED. Likely deferred due to scale and license complexity.

---

## Addressed Phase 4 items

### Radical meanings and Kangxi numbers — **ADDRESSED (v0.4.0 + v0.7.1)**

- **Status**: DELIVERED in two increments. First Phase 4 candidate to reach stable completion.
- **Source**: Wikipedia "Kangxi radicals" article, pinned to revision 1346511063, licensed CC-BY-SA 4.0 (compatible with our output). Fetched via `index.php?action=raw` for stable wikitext without JSON wrapping.
- **v0.4.0 initial coverage**: 197 of 253 radicals (77.9%) populated from the Wikipedia Kangxi radical table directly. The 214 primary Kangxi radicals plus their documented alternate forms (e.g., 亻 listed as alternate for 人) were all mapped via the primary/alternate parser.
- **v0.7.1 expansion**: A curated variant-to-Kangxi alias table (`KANGXI_ALIASES` in `build/transform/radicals.py`, 45 entries) bridges 45 Japanese-dictionary-specific variants to their Kangxi parents — shinjitai simplifications (亀→龜, 麦→麥, 歯→齒), radical-in-compound variants (汁→水 via 氵, 忙→心 via 忄, 邦→邑 via right-side 阝), positional markers (｜→丨, ノ→丿, ハ→八, ヨ→彐), and unambiguous kanji-as-component indicators. **Coverage is now 242 of 253 (95.7%).**
- **Remaining gap**: 11 radicals (マ, ユ, 尚, 杰, 井, 五, 巴, 禹, 世, 奄, 無) are Nelson-style variants whose Kangxi attribution is ambiguous. They are deliberately left unmatched rather than assigned arbitrary parents, preserving honest provenance. Closing this residual gap would require a Nelson-radical-specific source or native-speaker judgment.
- **Parser**: lives in `build/transform/radicals.py`. Reusable pattern for future Wikipedia ingestion (wikitable extraction, template unpacking, cell parsing).

## Frequency data (discovered during Phase 2)

### Modern media frequency (JPDB-based) — **BLOCKED on license clarification**

- **Status**: DEFERRED (license-blocked). Deferred from Phase 2 during investigation (2026-04-11); Phase 4 is not yet active.
- **Candidate sources** and their license situations:
  - `MarvNC/jpdb-freq-list` — last release 2022-05 (stale). No `LICENSE` file. The maintainer explicitly recommends Kuuuube's newer version as superior.
  - `Kuuuube/yomitan-dictionaries` — `JPDB_v2.2_Frequency_2024-10-13` is current with excellent coverage (99.99% up to 25k words, 98.6% up to 100k), but **no `LICENSE` file** in the repo. The data inside carries `"author": "jpdb, Kuuube, Gecko"` metadata but no declared license.
- **Underlying concern**: The JPDB.io corpus derives from copyrighted media (light novels, visual novels, anime, drama). Frequency counts themselves are facts (not copyrightable), but the specific corpus selection and rank ordering is arguably a creative act with unclear redistribution rights for a CC-BY-SA output.
- **Why we care**: Modern media frequency is significantly more useful for contemporary learners than the early-2000s newspaper corpus we currently ship. The coverage (particularly up to 25k words) matches exactly what learners need to prioritize their studies.
- **Paths to resolution**:
  1. **Contact the Kuuuube maintainer** and request an explicit license declaration. If they respond with CC-BY, CC-BY-SA, or CC0, we can promote to the next patch release.
  2. **Use an alternative modern-corpus source** with clear licensing — NINJAL public frequency tools, BCCWJ short-form CSVs if distributable, or a community-maintained Anki deck with a clear license.
  3. **Derive our own modern frequency list** from openly-licensed corpora: Aozora Bunko (public domain, but literary/classical slant) and Japanese Wikipedia (CC-BY-SA, modern but encyclopedic). Could be complementary to a media-specific source.
  4. **Accept newspaper frequency as our only source** and document the gap explicitly. This is the Phase 2 fallback we shipped.
- **Recommendation**: Pursue option 1 first (low effort — a GitHub issue or email). If no response in 30 days, pursue option 3 as a fallback (derive from Wikipedia JA).

## Lexical supplements

### Jinmeiyō-specific view

- **Source**: Already in our KANJIDIC2 data (grades 9 and 10).
- **Effort**: Trivial. A filtered derivative file.
- **Value**: Useful for reading names, writing name characters, understanding the jinmeiyō vs. jōyō distinction.
- **Status**: PROMOTED to Phase 2 or as a standalone enrichment task. Trivial effort; trivial value-add; include.

### Kanji compound frequency (jukugo)

- **Source**: Derived from `words.json` by identifying multi-kanji noun entries.
- **Effort**: Medium. Requires iterating over JMdict entries, identifying pure-kanji compounds, and aggregating frequency.
- **Value**: Useful for kanji pedagogy — which compounds are the most useful for learning a given kanji.
- **Status**: **DELIVERED (v0.8.0+)**. Jukugo compound index (`data/enrichment/jukugo-compounds.json`) extracts 14,350 multi-kanji compounds with per-character meaning decomposition from KANJIDIC2.

### Irregular readings (ateji, jukujikun)

- **Source**: Partially in JMdict and KANJIDIC2 already; Kanjium has a dedicated file for this.
- **Effort**: Low.
- **Value**: Important for reading fluency; these readings cannot be derived from the standard kanji reading rules.
- **Status**: **DELIVERED (v0.8.0+)**. Ateji index (`data/enrichment/ateji.json`) extracts 239 entries from JMdict `ateji` kanji writing tags. Jukujikun remains unaddressed (no explicit JMdict tag; would require heuristic matching or Kanjium data).

### Counter-word data

- **Source**: JMdict has some (counters are tagged); U-biq and other sources have more detailed data.
- **Effort**: Medium. Requires selecting which counters, how to structure the counter-to-noun-type mappings.
- **Value**: High for learners — counter use is a real friction point.
- **Status**: **DELIVERED (v0.8.0+)**. Counter-word index (`data/enrichment/counter-words.json`) extracts 125 entries from JMdict `ctr` POS tag. Additional counter-to-noun-type mappings could be added from U-biq or curated data in a future release.

---

## Tooling and auxiliary data

### Morphological analyzer dictionary outputs (Sudachi/UniDic)

- **Source**: Sudachi or UniDic dictionaries.
- **Scale**: Millions of entries.
- **License**: Apache 2.0 (Sudachi) or research terms (UniDic).
- **Effort**: High. These are for morphological analysis, not direct redistribution; integrating them would mean bundling a parser or using them to annotate our own data.
- **Value**: Could enable us to annotate every word entry and sentence with part-of-speech and inflection info at build time.
- **Status**: NOT EVALUATED. Potentially high value but significant scope expansion.

### Yomitan dictionary format outputs

- **Source**: Derived from our own data.
- **Effort**: Low-medium. Write a converter from our JSON schema to Yomitan's format.
- **Value**: Makes this dataset directly usable by Yomitan users (the dominant Japanese reading extension). Natural adoption path.
- **Status**: **DELIVERED (v0.8.0)**. `just export-yomitan` produces a ~1.3 MB ZIP in Yomitan v3 format with 30,765 terms and 13,108 kanji entries. See `build/export_yomitan.py`.

### Anki deck packages

- **Effort**: Medium. Writing Anki deck generators from our data.
- **Value**: Makes the dataset directly usable as flashcard content.
- **Status**: **DELIVERED (v0.8.0+)**. `just export-anki` produces a ~9.2 MB .apkg with 23,119 vocabulary cards, 13,108 kanji cards, and 595 grammar cards. Vocabulary cards include pitch accent and JLPT tags. See `build/export_anki.py`.

---

## Decision framework

When Phase 3 completes and we evaluate Phase 4 promotions, each candidate should be assessed on:

1. **License compatibility**: Can we bundle it, or only link? CC-BY-SA 4.0-compatible items are strongly preferred.
2. **Effort vs. value**: Size of the integration work relative to the user-visible benefit.
3. **Maintenance burden**: Does adding this source create ongoing update obligations we can sustain?
4. **Scope creep**: Does this take the project toward its stated goal (definitive Japanese learning data) or away from it?
5. **Synergy with existing data**: Does it cross-link cleanly with what we already have?

Candidates scoring well on all five should be promoted. Candidates scoring poorly on any should either be rejected or shelved indefinitely.

---

## Suggesting a Phase 4 addition

Open an issue titled `phase4: <candidate name>` with:

- Source URL and maintainer
- License (with link to the license text)
- Scale (entries / hours / bytes)
- Format description
- Integration effort estimate (low/medium/high + what's involved)
- Why it belongs in this dataset rather than a separate one
- How it would cross-link with existing data

The project owner will evaluate and either promote, defer, or reject.
