# Japanese Language Data

**A unified, cross-linked, reproducible, openly-licensed dataset for learning Japanese.**

Status: **Phase 4 — Active, two candidates delivered.** All files from Phases 1–3 plus: (1) Wikipedia-sourced Kangxi radical meanings and numbers (v0.4.0), expanded in v0.7.1 by a curated variant-to-Kangxi alias table that bridges Japanese-dictionary-specific variants (shinjitai, radical-in-compound forms, katakana-shaped markers) to their Kangxi parents — radical coverage is now **242 of 253 (95.7%)**. (2) A hand-curated grammar dataset that grew from 81 entries to **595 entries** across all five JLPT levels (v0.5.0–v0.7.0), with community-standard completeness on N3/N2/N1/N4 and near-complete N5. Every grammar entry remains `review_status: draft` — native-speaker review is the most important remaining work. Other Phase 4 candidates (JPDB modern frequency, classical handwriting, audio corpora) remain pending — see `docs/phase4-candidates.md`.

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

## Data inventory

As of v0.7.1 (see `manifest.json` for live counts), the `data/` directory contains:

### Core

| File | Source(s) | Count | Committed? | Description |
|---|---|---:|---|---|
| `data/core/kana.json` | Hand-written | 215 | ✓ | Hiragana, katakana, variants, combinations |
| `data/core/kanji.json` | KANJIDIC2 (via jmdict-simplified) | 13,108 | ✓ | Full KANJIDIC2 set: readings, meanings, stroke count, grade, JLPT, frequency, radicals |
| `data/core/kanji-joyo.json` | Derived view of `kanji.json` | 2,136 | ✓ | Jōyō subset (grades 1–6 + 8, 2010 MEXT revision) |
| `data/core/kanji-jinmeiyo.json` | Derived view of `kanji.json` | 863 | ✓ | Jinmeiyō kanji (grades 9–10, personal-name use) |
| `data/core/words.json` | JMdict-examples (via jmdict-simplified) | 22,580 | ✓ | **Common-only subset** — entries whose kanji or kana writings carry JMdict priority markers (`news1`/`ichi1`/`spec1`/`spec2`/`gai1`). This is the primary committed file. |
| `data/core/words-full.json` | JMdict-examples (via jmdict-simplified) | 216,173 | gitignored | Full JMdict (no `common` filter) including archaic, rare, specialized, and dialectal vocabulary. ~150 MB uncompressed; rebuilt on demand by `just build`. |
| `data/core/radicals.json` | KRADFILE + RADKFILE + Wikipedia (Kangxi) | 253 | ✓ | Radical → kanji and kanji → radicals. 242/253 (95.7%) have English meanings and Kangxi numbers from Wikipedia + curated alias table. |
| `data/optional/names.json` | JMnedict (via jmdict-simplified) | ~720,000 | gitignored | Proper nouns. Built on demand with `just build-names`; not committed due to size. |

### Enrichment

| File | Source(s) | Count | Committed? | Description |
|---|---|---:|---|---|
| `data/enrichment/stroke-order/*.svg` | KanjiVG | 6,416 | ✓ | One SVG per kanji with stroke order metadata |
| `data/enrichment/stroke-order-index.json` | Generated from KanjiVG | 13,108 | ✓ | Character → SVG filename lookup (null for characters without a KanjiVG SVG) |
| `data/enrichment/pitch-accent.json` | Kanjium `accents.txt` | 124,011 | ✓ | Word → pitch accent mora positions |
| `data/enrichment/frequency-newspaper.json` | KANJIDIC2 | 2,501 | ✓ | Newspaper frequency rank (kanji) |
| `data/enrichment/frequency-modern.json` | JPDB (license-blocked) | — | not built | Modern media frequency. Blocked on license clarification — see `docs/phase4-candidates.md`. |
| `data/enrichment/jlpt-classifications.json` | Waller JLPT lists (tanos.co.uk) | 11,099 | ✓ | Community-consensus JLPT N5–N1 level for vocabulary, kanji, and grammar |

### Corpus

| File | Source(s) | Count | Committed? | Description |
|---|---|---:|---|---|
| `data/corpus/sentences.json` | Tatoeba (via jmdict-examples) | 25,980 | ✓ | Editor-curated JA–EN example sentence pairs (dedup'd by Tatoeba ID) |

### Grammar

| File | Source(s) | Count | Committed? | Description |
|---|---|---:|---|---|
| `data/grammar/grammar.json` | **Original curation** (Phase 3) | 595 | ✓ | Structured grammar points with patterns, examples, related refs, formality, JLPT level. All entries `review_status: draft` — native-speaker review pending. Target: 500–700. |
| `data/grammar/conjugations.json` | Derived from `words.json` | 3,507 | ✓ | Verb and adjective conjugation tables (ichidan, godan including v5k-s/v5u-s/v5aru/v5r-i edge cases, suru-verbs, i- and na-adjectives) |
| `data/grammar/expressions.json` | Extracted from JMdict `exp` entries | 13,220 | ✓ | Lexical grammar patterns tagged as expressions in JMdict |

### Cross-references

| File | Source(s) | Count | Committed? | Description |
|---|---|---:|---|---|
| `data/cross-refs/kanji-to-words.json` | Generated from `words.json` + `kanji.json` | 3,533 | ✓ | Every kanji → list of word IDs using it (common subset) |
| `data/cross-refs/word-to-kanji.json` | Generated from `words.json` | 18,084 | ✓ | Every word → list of kanji characters it contains |
| `data/cross-refs/word-to-sentences.json` | Generated from `words.json` + `sentences.json` | 14,550 | ✓ | Every word → list of Tatoeba sentence IDs |
| `data/cross-refs/kanji-to-radicals.json` | Generated from `radicals.json` | 12,156 | ✓ | Every kanji → component radicals (from KRADFILE) |

All files are schema-validated JSON with metadata headers crediting upstream sources. **Live counts are maintained in `manifest.json.counts` and refreshed by `just stats` on every build**; this table is a snapshot for discoverability.

## Quick start

```bash
# Install just (task runner) — see https://github.com/casey/just#installation
# e.g.: cargo install just  /  brew install just  /  apt install just

git clone https://github.com/jkindrix/japanese-language-data.git
cd japanese-language-data
python3 -m venv .venv && . .venv/bin/activate
pip install -r build/requirements.txt
just fetch    # download pinned upstream sources
just build    # transform and cross-link
just validate # schema-check every output
just stats    # print counts and coverage
```

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

- **Native-speaker review** for the grammar dataset (Phase 3). All 595 grammar entries currently carry `review_status: draft`. There is a complete reviewer workflow at `docs/grammar-review.md` with a per-entry checklist at `docs/grammar-review-checklist.md`. This is the single most impactful contribution you can make.
- **Error reports** for existing entries (these get filed upstream where applicable)
- **Additional enrichment sources** to integrate
- **Schema improvements** for edge cases we haven't modeled

## Grammar reviewers

Every grammar entry in this dataset that has been upgraded from `draft` was reviewed by one of the people below. Reviewers are listed by their preferred credit (real name, GitHub handle, or pseudonym); some reviewers have chosen to stay uncredited and are thanked anonymously.

_No reviewers yet. If you are the first, see `docs/grammar-review.md`._

If your review is merged and you would like to be listed here, say so in your PR description (see `.github/PULL_REQUEST_TEMPLATE.md`, "For grammar review PRs").

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
