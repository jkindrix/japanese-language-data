# Upstream sources

This document catalogs every upstream source that this dataset builds on, with the information needed to reproduce the build: pinned URLs, version, license, format, size, update cadence, and what we extract from each. When a source is updated, the changes made to the pinned version are recorded here and in `CHANGELOG.md`.

For the full license text of each source, see `LICENSE`. For the required attribution wording, see `ATTRIBUTION.md`.

---

## jmdict-simplified

**Project**: https://github.com/scriptin/jmdict-simplified
**Maintainer**: scriptin (one-person project; see "Single-maintainer risk" below)
**License**: CC-BY-SA 4.0 (source code and distribution format) + EDRDG License (underlying data)
**Update cadence**: Automated weekly releases, every Monday
**Our pin**: version 3.6.2+20260406125001 (released 2026-04-06)

This is the primary upstream for JMdict, JMnedict, KANJIDIC2, KRADFILE, and RADKFILE. It converts the original EDRDG XML files into a clean, self-contained JSON format with stable schemas, human-readable field names, empty arrays over nulls, and no implicit field inheritance. We ingest its pre-built JSON releases directly rather than parsing XML ourselves.

### Assets we use from this project

| Asset | Source file | Size (compressed) | Target in our dataset |
|---|---|---|---|
| `jmdict-examples-eng-<ver>.json.tgz` | JMdict English + Tatoeba example links | 13.9 MB | `data/core/words.json` + link data for `data/cross-refs/word-to-sentences.json` |
| `jmnedict-all-<ver>.json.tgz` | JMnedict (all languages) | 13.4 MB | `data/optional/names.json` (opt-in, gitignored) |
| `kanjidic2-all-<ver>.json.tgz` | KANJIDIC2 all languages (13,108 characters, full coverage) | 1.55 MB | `data/core/kanji.json` |
| `kradfile-<ver>.json.tgz` | KRADFILE (kanji → radical decomposition) | 106 KB | part of `data/core/radicals.json` |
| `radkfile-<ver>.json.tgz` | RADKFILE (radical → kanji lookup) | 134 KB | part of `data/core/radicals.json` |

### What we extract and transform

- **Words (JMdict-examples-eng)**: Every entry preserved with its ID, kanji writings, kana writings (with `appliesToKanji` cross-references), senses (parts of speech, domains, dialects, misc tags, translations, example links), language-source notes for loanwords, and cross-references. We augment each entry with a `jlpt_level` field filled from the Waller list (see below), a `frequency_media` field from JPDB (see below), and a `source_refs` field listing the origin of every datum in the entry.
- **Kanji (KANJIDIC2-en)**: Every entry preserved with readings (on/kun/nanori), meanings, stroke count, grade, JLPT (old system — see `field_notes`), frequency rank, radical info, dictionary references, query codes, and variants. We augment each entry with a `jlpt_waller` field from the Waller list (current community-standard classification, distinct from the old JLPT in KANJIDIC2).
- **Names (JMnedict)**: Preserved largely as-is for the optional `data/optional/names.json` build. No augmentation — names are reference data, not learning data.
- **Radicals (KRADFILE+RADKFILE)**: Combined into a single `data/core/radicals.json` with bidirectional lookup: radical → kanji list and kanji → radical list.

### Single-maintainer risk

`jmdict-simplified` is maintained by one person (scriptin). If they stop, we lose our ingestion shortcut and would fall back to parsing raw JMdict XML ourselves, which is meaningfully harder but doable. We acknowledge this dependency and keep the transform logic simple enough to be reimplemented from the raw EDRDG XML if necessary. The raw XML is already downloadable from the EDRDG site as a fallback.

---

## KanjiVG

**Project**: https://github.com/KanjiVG/kanjivg
**Homepage**: https://kanjivg.tagaini.net/
**Maintainer**: Ulrich Apel and contributors
**License**: CC-BY-SA 3.0 (compatible with CC-BY-SA 4.0 output under CC's upgrade rule)
**Update cadence**: Irregular, semiannual-ish releases
**Our pin**: release `r20250816` (2025-08-16)

KanjiVG provides stroke order vector graphics for every character in the JIS X 0208 and JIS X 0213 standards, with metadata about component parts and stroke types. We use the non-variant "main" distribution.

### Asset we use

| Asset | Size (compressed) | Target |
|---|---|---|
| `kanjivg-20250816-main.zip` | 12.6 MB | `data/enrichment/stroke-order/*.svg` + `data/enrichment/stroke-order-index.json` |

### What we extract

- Each SVG file is named `<zero-padded hex codepoint>.svg`. We filter to CJK Unified Ideograph code points (0x4E00–0x9FFF, Extensions A/B in a later phase) and store each per-character SVG as-is in `data/enrichment/stroke-order/`.
- We generate `data/enrichment/stroke-order-index.json` mapping each character to its SVG filename for O(1) lookup, and noting its total stroke count.
- Component/radical metadata embedded in the SVG is preserved but not currently extracted into separate fields; future phases may lift it into a structured form.

### Known gap

Not all kanji characters in KANJIDIC2 are in KanjiVG. Characters without SVGs are recorded in `data/enrichment/stroke-order-index.json` with `"svg": null`. The percentage of covered characters is reported in `just stats`.

---

## Tatoeba

**Project**: https://tatoeba.org/
**Downloads**: https://downloads.tatoeba.org/exports/
**License**: CC-BY 2.0 FR (default), CC0 1.0 (subset)
**Update cadence**: Daily snapshots
**Our pin**: Sentences are ingested indirectly via the `jmdict-examples-eng` release from scriptin/jmdict-simplified (version 3.6.2+20260406125001), which bundles Tatoeba links selected by JMdict editors. The Tatoeba content is therefore pinned to whatever snapshot the jmdict-simplified release used at build time.

Tatoeba is a community-contributed multilingual sentence corpus. Quality varies by contributor and language pair. We use two distinct ingestion paths:

### Path 1: Via jmdict-examples-eng (editor-curated)

The `jmdict-examples-eng` variant of JMdict embeds a curated subset of Tatoeba sentences linked to specific senses. These sentences have been reviewed by the JMdict editors for quality and relevance. This is our primary source of example sentences for `data/corpus/sentences.json` and `data/cross-refs/word-to-sentences.json`.

### Path 2: Full unfiltered Japanese sentences (optional, Phase 2+)

For more comprehensive coverage (at the cost of quality), we may in Phase 2 ingest the full set of Japanese sentences from Tatoeba via the per-language export:

- `https://downloads.tatoeba.org/exports/per_language/jpn/` — Japanese-anchored per-language link files, e.g. `jpn-eng_links.tsv.bz2` for Japanese-English pairs.
- Plus `sentences.tar.bz2` (~204 MB compressed) for the actual sentence text.

If ingested, these go to `data/corpus/sentences-unfiltered.json` with a `curated: false` flag on each entry, so consumers can distinguish editor-reviewed sentences from the full firehose.

### What we extract

- Sentence ID (preserved from Tatoeba)
- Japanese text
- English translation text (matched via the link files)
- Contributor IDs (where available, for attribution)
- License flag (CC-BY 2.0 FR vs. CC0)
- Curation flag (true if from jmdict-examples, false if from the full corpus)
- Audio availability flag (where applicable; audio itself is not bundled)

---

## Kanjium (pitch accent)

**Project**: https://github.com/mifunetoshiro/kanjium
**Maintainer**: mifunetoshiro; last major update ~2022
**License**: CC-BY-SA 4.0
**Update cadence**: Irregular, currently ~stale as of 2022
**Our pin**: master branch at build time, with commit hash recorded

Kanjium aggregates pitch accent data for 124,137 Japanese words, along with a richer SQLite database of supplementary kanji information. We ingest the simpler `accents.txt` file for pitch data in Phase 2; the SQLite database is a Phase 4 candidate for additional kanji metadata.

### Asset we use

| Asset | Size | Target |
|---|---|---|
| `data/source_files/raw/accents.txt` | ~5 MB (plain TSV) | `data/enrichment/pitch-accent.json` |

### Format

Tab-separated: `<word>\t<kana_reading>\t<mora_position_list>` where the mora position list is a comma-separated list of pitch accent positions (0 = heiban/flat, N = accent falls after the Nth mora).

Example:
```
学校	がっこう	0
日本	にほん	2
今日	きょう	1
雨	あめ	1
```

### Known gap

Kanjium's pitch data is roughly frozen at 2022 levels. Words added to Japanese after 2022, loanwords from recent media, and specialized terminology added in the last few years will not have pitch accent in our dataset. See `docs/gaps.md` for details. A Phase 4 candidate is scraping Wiktionary or OJAD for newer words.

---

## Jonathan Waller's JLPT Resources (tanos.co.uk)

**Original project**: http://www.tanos.co.uk/jlpt/
**Sharing page**: http://www.tanos.co.uk/jlpt/sharing/
**Original author**: Jonathan Waller
**License**: CC-BY (explicit: "use anything here however you like (commercial or non-commercial), but credit my site. (A link would be nice.)")

JLPT stopped publishing official vocabulary lists in 2010. Jonathan Waller's lists are the de-facto community standard for JLPT level classification and are the upstream for virtually every other JLPT classification project (Jisho.org, Yomitan JLPT tags, many Anki decks).

### Why we don't scrape tanos.co.uk directly

The tanos.co.uk server returns HTTP 500 to user agents it does not recognize (confirmed via curl during Phase 2 investigation — `Vary: User-Agent` header is set). Programmatic scraping is fragile and would require maintaining a user-agent spoof that could break at any time.

Instead, we ingest Waller's data via two redistribution channels that have already done the scraping work and published it in structured form with compatible licenses:

### Redistribution channel 1: `stephenmk/yomitan-jlpt-vocab` (vocabulary)

**Project**: https://github.com/stephenmk/yomitan-jlpt-vocab
**License**: CC-BY-SA 4.0 (compatible with our CC-BY-SA 4.0 output)
**Our pin**: `main` branch (SHA256 per-file, in `manifest.json`)
**Assets we use**: `original_data/n{5,4,3,2,1}.csv` — 5 CSV files, roughly 24–199 KB each.

### Redistribution channel 2: `davidluzgouveia/kanji-data` (kanji)

**Project**: https://github.com/davidluzgouveia/kanji-data
**License**: MIT (code); underlying data combines KANJIDIC (CC-BY-SA) and Waller (CC-BY). We use only the Waller-derived `jlpt_new` field.
**Our pin**: `master` branch `kanji.json` (SHA256 in `manifest.json`)

**Important**: This project's `kanji.json` also contains WaniKani-derived fields (`wk_level`, `wk_meanings`, `wk_readings`, `wk_radicals`). **We deliberately do not use these fields** because the WaniKani license is not compatible with our CC-BY-SA 4.0 output. Only the `jlpt_new` field is extracted per kanji.

### What we extract

- **Vocabulary** (from stephenmk CSVs): 8,293 entries total across N5-N1. Each CSV row contains `jmdict_seq, kana, kanji, waller_definition`. The `jmdict_seq` field allows clean joins with our `words.json` by the same ID.
- **Kanji** (from davidluzgouveia): 2,211 entries with N5-N1 classifications. Only the `jlpt_new` field is extracted per character.
- **Grammar**: deferred to Phase 3. Waller's grammar lists are HTML only and would require either tanos.co.uk scraping or a separate redistribution source. Phase 3 will curate grammar from scratch.

### Transformation output

Produced at `data/enrichment/jlpt-classifications.json` with entries of the form:

```json
{
  "text": "猫",
  "reading": "ねこ",
  "kind": "vocab",
  "level": "N5",
  "meaning_en": "cat",
  "jmdict_seq": "1467640",
  "source_retrieved": "YYYY-MM-DD"
}
```

### Known caveats

- Not JLPT-official. The lists are reverse-engineered from past test questions and community consensus. Some entries are disputed; edge cases between levels are unclear.
- We report them as `jlpt_waller` (not `jlpt`) on kanji/word entries to avoid suggesting official provenance.
- **~6.6% of stephenmk's JLPT vocab entries (~546 of ~8,279) cannot be joined to `data/core/words.json` by ID** — not because of JMdict ID drift (all 8,279 seq IDs DO exist in the full JMdict), but because those specific entries are NOT in our common-subset `words.json`. The common filter drops them because JMdict does not flag them as common. They can still be joined against the full `words-full.json` (gitignored build artifact) or their Waller entries stand alone in `jlpt-classifications.json` without a word join.
- Waller's own grammar lists are also fuzzy; Phase 3 grammar classification will rely on multiple sources for cross-validation.

---

## JPDB frequency list (MarvNC)

**Project**: https://github.com/MarvNC/jpdb-freq-list
**Underlying data**: jpdb.io corpus analysis
**License**: Verified per release
**Update cadence**: Irregular releases
**Our pin**: To be set at Phase 2 build time.

Modern media frequency data derived from analysis of light novels, visual novels, anime, and drama. This is a better frequency signal for media-consumption learners than the newspaper corpus that underlies KANJIDIC2's frequency field.

### Asset we use

- Yomitan-compatible frequency dictionary ZIP from the latest release
- Converted into a flat mapping in `data/enrichment/frequency-modern.json`

### Known gaps

- Covers words, not kanji directly (though kanji frequency can be derived by aggregating across word usages)
- Corpus selection reflects one community's consumption patterns; not a balanced national corpus

---

## Wikipedia: Kangxi radicals article (added v0.4.0)

**Project**: https://en.wikipedia.org/wiki/Kangxi_radicals
**License**: CC-BY-SA 4.0 (compatible with our CC-BY-SA 4.0 output).
**Pinned revision**: `1346511063` (2024). Permanent URL: `https://en.wikipedia.org/w/index.php?title=Kangxi_radicals&oldid=1346511063`
**Fetch method**: `action=raw` endpoint on `index.php`, which returns the raw wikitext of the pinned revision as plain text. Avoids the `action=parse` JSON wrapping and MediaWiki API parameter constraints. SHA256-verified like every other source.

### Why Wikipedia for this specific dataset

RADKFILE (from EDRDG) provides 253 radicals with their stroke counts and the kanji that contain them, but does NOT provide English meanings or Kangxi radical numbers (1–214). Those fields are widely known facts but are not available in any CC-BY-SA-compatible structured source we've found. Wikipedia's "Kangxi radicals" article has a single well-structured wikitable with all 214 classical radicals plus their documented alternate forms, English meanings, and explicit Kangxi numbers, and is licensed CC-BY-SA 4.0 — a direct license match.

### What we extract

For each row of the Wikipedia wikitable:
- Kangxi radical number (1–214) → populates `classical_number` on the matching RADKFILE entry
- English meaning (from the "Meaning" column, split on commas when multiple equivalent words are listed, e.g., radical 10 儿 → `["son", "legs"]`) → populates `meanings`
- Alternate radical forms (e.g., 亻 listed as alternate for 人) → meanings and numbers propagate to all alternate forms

### What we do NOT use

- **Stroke count column**: we rely on RADKFILE, which is the authoritative upstream for stroke counts in this dataset. Using two sources for the same field risks divergence.
- **Pinyin, Vietnamese, Korean, Japanese readings**: the radicals dataset is scoped to Japanese dictionary lookup, not multilingual phonology. Cross-linguistic radical readings are a separate Phase 4 candidate.
- **Frequency and example kanji columns**: these are interesting but out of scope for this release.

### Coverage and known limitations

- **242 of 253 radicals (95.7%)** are populated by this source, as of v0.7.1. Wikipedia alone supplied 197/253 (77.9%) in v0.4.0 via the primary-and-alternate parser; v0.7.1 added a curated variant-to-Kangxi alias table in `build/transform/radicals.py` (`KANGXI_ALIASES`, 45 entries) that bridges Japanese-dictionary-specific variants — shinjitai simplifications, radical-in-compound variants, and positional markers — to their Kangxi parents. The 11 remaining unmatched radicals (マ, ユ, 尚, 杰, 井, 五, 巴, 禹, 世, 奄, 無) are Nelson-style variants whose Kangxi attribution is ambiguous; they are deliberately left unmatched rather than assigned arbitrary parents.
- **Stroke count mismatches are not expected** (Wikipedia's stroke column is read for reference only but not emitted).
- **Revision drift**: Wikipedia articles change over time. Our pin to revision 1346511063 locks the data to a specific snapshot. Updating requires a deliberate pin bump in `build/fetch.py` and `build/transform/radicals.py`.

### Attribution requirement

Per Wikipedia's CC-BY-SA 4.0 terms, downstream uses of the radicals data must include attribution equivalent to:

> Kangxi radical English meanings and Kangxi numbers derived from the Wikipedia article "Kangxi radicals" (https://en.wikipedia.org/wiki/Kangxi_radicals, revision 1346511063), authored by Wikipedia contributors under CC-BY-SA 4.0.

This attribution is also baked into `data/core/radicals.json` metadata.

---

## KANJIDIC2 frequency (from jmdict-simplified ingest)

The `freq` field in KANJIDIC2 entries (ingested via jmdict-simplified) provides newspaper frequency rank for the top ~2,500 most common kanji. This is extracted into `data/enrichment/frequency-newspaper.json` during the kanji transform and cross-linked with the modern frequency for consumers who want both.

---

## Pinning strategy

Every upstream source has two pinning components:

1. **URL pin**: The exact URL from which the source was downloaded. Hardcoded in `build/fetch.py` as a constant.
2. **Hash pin**: SHA256 of the downloaded file. Recorded in `manifest.json` after the first successful fetch. Subsequent fetches verify the hash; a mismatch fails the build.

Upgrading a source is a deliberate three-step process:

1. Update the URL in `build/fetch.py` (or leave it if only the file contents changed at the same URL).
2. Delete or clear the hash in `manifest.json` to force re-download and re-hashing.
3. Run `just fetch && just build && just validate` to confirm the upgrade produces valid output.
4. Commit with a message like `chore: bump <source> from <old_version> to <new_version>` and update `CHANGELOG.md`.

A build can never upgrade sources silently. This is the reproducibility guarantee.
