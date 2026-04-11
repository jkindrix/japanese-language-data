# Japanese Language Data

**A unified, cross-linked, reproducible, openly-licensed dataset for learning Japanese.**

Status: **Phase 2 — Core + enrichment built.** All files from Phase 1 plus stroke order SVGs (6,416 characters), pitch accent data (124k entries), JLPT classifications (kanji + vocab, ~10.5k entries), newspaper frequency rankings, and 4 cross-reference indices. Kanji entries are now enriched with component radicals and JLPT levels; word entries with JLPT levels. Phase 3 (original grammar curation) is still pending. Modern media frequency (JPDB) is deferred to Phase 4 pending license clarification.

---

## What this is

A single coherent dataset that aggregates the best open Japanese-language resources, cross-links them at the entry level, validates everything against explicit schemas, and rebuilds reproducibly from pinned upstream versions. The goal is a dataset that underpins learning, reading, parsing, and studying Japanese — complete enough to be useful on its own, modern enough to be worth adopting, and open enough that anyone can use, inspect, modify, or contribute to it.

The project exists because every piece of Japanese-language data you'd want already exists openly, but nothing unifies them. JMdict gives you ~200,000 words. KANJIDIC2 gives you ~13,000 kanji. KanjiVG gives you stroke order SVGs. Tatoeba gives you example sentences. Kanjium gives you pitch accent. Waller gives you community-standard JLPT classifications. These projects represent decades of volunteer labor — but they live in separate repos with separate formats, separate licenses, and no cross-references. Building an app or a study system means assembling the puzzle yourself every time.

This repository assembles the puzzle once, commits the result, and provides a reproducible build so the dataset stays fresh as upstream sources update.

## What this is not

- **Not a learning application.** There's no UI, no SRS, no flashcard system. This is raw structured data. Applications build on top.
- **Not a replacement for the upstream projects.** JMdict, KANJIDIC2, KanjiVG, Tatoeba, Kanjium, and the others are *the foundation*. This project builds on them, contributes back to them, and provides the unification layer they don't individually offer. If upstream sources disappeared, this project could not exist. We are a grateful downstream neighbor, not a competitor.
- **Not a commercial product.** Licensed CC-BY-SA 4.0 end-to-end. You may use the data commercially; derivatives must carry the same license.
- **Not authoritative for grammar.** The grammar dataset (Phase 3) is original curation. It is our best effort, community-contributable, transparently sourced per entry — but it is explicitly not reviewed by native-speaker linguists at the time of v1 release. See `docs/gaps.md`.

## Planned data inventory

When Phases 1–3 are complete, the `data/` directory will contain:

| File | Source(s) | Scale | Description |
|---|---|---|---|
| `data/core/kana.json` | Hand-written | ~200 | Hiragana, katakana, variants, combinations |
| `data/core/kanji.json` | KANJIDIC2 (via jmdict-simplified) | ~13,108 | Readings, meanings, stroke count, grade, JLPT, frequency, radicals |
| `data/core/words.json` | JMdict-examples (via jmdict-simplified) | ~200,000 | Entries with kanji/kana writings, senses, translations, example links |
| `data/core/radicals.json` | KRADFILE/RADKFILE (via jmdict-simplified) | ~214 + mappings | Radical → kanji and kanji → radicals |
| `data/enrichment/stroke-order/*.svg` | KanjiVG | ~11,000 | One SVG per character with stroke order metadata |
| `data/enrichment/stroke-order-index.json` | Generated | ~11,000 | Character → SVG filename lookup |
| `data/enrichment/pitch-accent.json` | Kanjium `accents.txt` | ~124,137 | Word → pitch accent mora positions |
| `data/enrichment/frequency-newspaper.json` | KANJIDIC2 | ~2,500 | Newspaper frequency rank (kanji) |
| `data/enrichment/frequency-modern.json` | JPDB (via MarvNC) | ~500,000 | Media frequency rank (light novel / anime / VN / drama) |
| `data/enrichment/jlpt-classifications.json` | Waller JLPT lists (tanos.co.uk) | ~8,000+ | Community-consensus JLPT N5–N1 level assignment for vocabulary and kanji |
| `data/corpus/sentences.json` | Tatoeba (via jmdict-examples) | varies | Editor-curated JA–EN example sentence pairs |
| `data/grammar/grammar.json` | **Original curation** (Phase 3) | ~500–700 target | Structured grammar points with patterns, examples, references |
| `data/grammar/conjugations.json` | Derived from words.json | ~thousands | Verb and adjective conjugation tables |
| `data/grammar/expressions.json` | Extracted from JMdict `exp` entries | ~10,000 | Lexical grammar patterns from JMdict |
| `data/cross-refs/kanji-to-words.json` | Generated | — | Every kanji → list of word IDs using it |
| `data/cross-refs/word-to-kanji.json` | Generated | — | Every word → list of kanji characters it contains |
| `data/cross-refs/word-to-sentences.json` | Generated | — | Every word → list of Tatoeba sentence IDs |
| `data/cross-refs/kanji-to-radicals.json` | Generated | — | Every kanji → component radicals (from KRADFILE) |
| `data/optional/names.json` | JMnedict (via jmdict-simplified) | ~720,000 | Proper nouns — gitignored; build with `just build-names` |

All files are schema-validated JSON with metadata headers crediting upstream sources.

## Quick start (once Phase 1 is built)

```bash
git clone https://github.com/jkindrix/japanese-language-data.git
cd japanese-language-data
python3 -m venv .venv && . .venv/bin/activate
pip install -r build/requirements.txt
just fetch    # download pinned upstream sources
just build    # transform and cross-link
just validate # schema-check every output
just stats    # print counts and coverage
```

None of these will work until Phase 1 is implemented. Phase 0 (current) provides the scaffolding only.

## Licensing

The entire built dataset is released under **Creative Commons Attribution-ShareAlike 4.0 International** (CC-BY-SA 4.0). This is required by the license terms of several of our upstream sources and is the most permissive license we can use while respecting them.

- **For users**: You may use, redistribute, remix, and build upon this data, including commercially, provided you attribute the sources and license derivatives under the same or compatible terms.
- **For downstream projects**: If you build on this data and publish the result, your result must also be CC-BY-SA 4.0 (or a compatible copyleft license). Proprietary use is permitted but derivatives must remain open.
- **For authors of proprietary applications**: You can use the data within a commercial application. The CC-BY-SA requirement applies to distribution of the data itself and direct derivatives of it, not to separate software that merely reads it.

**Attribution**: Every downstream use must credit this project, the upstream sources this project builds on, and (in the case of KANJIDIC2-derived data) the individual rights holders of the specific fields involved. See `ATTRIBUTION.md` for exact wording, URLs, and per-source credits.

**License obligations inherited from EDRDG**: The EDRDG License (applicable to JMdict, JMnedict, KANJIDIC2, KRADFILE, RADKFILE) requires that *web-facing dictionary applications* update their data at least monthly. This repository commits to rebuilding against upstream at least monthly, and to tagging releases accordingly. Downstream servers using this data must themselves update at least monthly to remain in compliance. See `LICENSE` and `ATTRIBUTION.md` for the full text of EDRDG's requirements.

## Architecture

See `docs/architecture.md` for the full architectural overview, data flow, directory layout rationale, and schema philosophy.

## Contributing

Contributions welcome — see `docs/contributing.md`. We especially need:

- **Native-speaker review** for the grammar dataset (Phase 3)
- **Error reports** for existing entries (these get filed upstream where applicable)
- **Additional enrichment sources** to integrate
- **Schema improvements** for edge cases we haven't modeled

## Acknowledgments

This project would not exist without the work of:

- **Jim Breen and the EDRDG** for JMdict, JMnedict, KANJIDIC2, KRADFILE/RADKFILE — the foundation of open Japanese lexical data
- **Ulrich Apel and the KanjiVG contributors** for the open stroke order dataset
- **The Tatoeba community** for the world's largest open multilingual example sentence corpus
- **mifunetoshiro and contributors** for the Kanjium pitch accent data
- **Jonathan Waller** for the tanos.co.uk community-standard JLPT lists
- **scriptin** for `jmdict-simplified` — our primary ingestion format
- **MarvNC** for JPDB frequency list exports
- **Jack Halpern, Christian Wittern, Koichi Yasuoka, Urs App, Mark Spahn, Wolfgang Hadamitzky, Charles Muller, Joseph De Roo** for the per-field KANJIDIC2 contributions (SKIP codes, pinyin, Four Corner codes, Spahn/Hadamitzky descriptors, Korean readings, De Roo codes)
- **Every volunteer** who has contributed corrections, translations, and edits to any of the upstream projects across three decades of work

This project is a unification layer over 60+ collective years of volunteer labor. We owe them everything.
