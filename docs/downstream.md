# Building on this dataset

This guide is for application developers who want to use the Japanese Language Data files in their own projects — SRS apps, dictionary lookup tools, text analysis pipelines, or anything else.

---

## Which files to use

| Use case | Recommended files |
|---|---|
| **SRS / flashcard app** | `words.json` + `kanji.json` + `jlpt-classifications.json` + `pitch-accent.json` + `sentences.json` + cross-refs |
| **Dictionary lookup** | `words.json` (or `words-full.json` for rare words) + `kanji.json` + `pitch-accent.json` + `furigana.json` |
| **Grammar study** | `grammar.json` + `jlpt-classifications.json` |
| **Kanji study** | `kanji.json` + `kanji-joyo.json` + `radicals.json` + `stroke-order/` SVGs + `radical-to-kanji.json` |
| **Text analysis / parsing** | `words-full.json` + `conjugations.json` + `expressions.json` |
| **Reading aid** | `words.json` + `pitch-accent.json` + `furigana.json` + `kanji-to-words.json` + `word-to-sentences.json` |
| **SQL queries** | `dist/japanese-language-data.sqlite` — single file with all tables, build via `just export-sqlite` |

All files are in `data/`. See the [data inventory in README.md](../README.md#data-inventory) for complete descriptions.

---

## Data loading patterns

### Index by ID, not scan

Every primary data file uses stable IDs. Build lookup tables at startup rather than scanning arrays on every query:

```python
words_by_id = {w["id"]: w for w in data["words"]}
kanji_by_char = {k["character"]: k for k in data["kanji"]}
grammar_by_id = {g["id"]: g for g in data["grammar_points"]}
```

Cross-reference files (`data/cross-refs/`) are already keyed by ID — load them directly as lookup tables.

### File sizes

| File | Entries | Disk | In-memory (approx) |
|---|---:|---:|---:|
| `words.json` | 23,119 | 46 MB | 120 MB |
| `words-full.json` | 216,173 | 285 MB | 800 MB |
| `kanji.json` | 13,108 | 17 MB | 60 MB |
| `pitch-accent.json` | 124,011 | 17 MB | 80 MB |
| `frequency-subtitles.json` | 8,598 | 1.6 MB | 5 MB |
| `frequency-web.json` | 11,038 | 1.2 MB | 5 MB |
| `frequency-wikipedia.json` | 14,553 | 1.6 MB | 6 MB |
| `pitch-accent-wiktionary.json` | 7,378 | 1.1 MB | 4 MB |
| `counter-words.json` | 125 | 24 KB | <1 MB |
| `ateji.json` | 239 | 52 KB | <1 MB |
| `jukugo-compounds.json` | 14,350 | 14 MB | 40 MB |
| `furigana.json` | 28,920 | 6.8 MB | 20 MB |
| `grammar.json` | 595 | 1.1 MB | 3 MB |
| `sentences.json` | 25,980 | 9.3 MB | 30 MB |
| All cross-refs | ~76K mappings | 5.5 MB | 25 MB |

For `words-full.json`, consider streaming (see `docs/cookbook.md` § Working with large files).

---

## Update cadence

The EDRDG License (applicable to all JMdict, KANJIDIC2, KRADFILE, and RADKFILE data) requires that **web-facing dictionary applications update their data at least monthly**. This applies to you if:

- Your application serves Japanese dictionary data to users via the web.
- Your application's data originates from this dataset (which itself originates from EDRDG sources).

This repository commits to rebuilding against upstream at least monthly and tagging releases accordingly. Your application should track releases and update within a month of each tagged release.

Mobile apps, offline tools, and internal tools are not subject to the monthly update requirement, but updating regularly is still good practice.

---

## Attribution

You must attribute this dataset and its upstream sources when distributing data or derivatives. The simplest approach:

> Japanese language data from the [Japanese Language Data](https://github.com/jkindrix/japanese-language-data) project (CC-BY-SA 4.0), incorporating data from JMdict/EDRDG, KANJIDIC2, KanjiVG, Tatoeba, and Kanjium. See ATTRIBUTION.md for full credits.

For the complete per-source attribution wording, see [`ATTRIBUTION.md`](../ATTRIBUTION.md).

If your application has an "About" or "Credits" screen, include the attribution there. If it is a web application, include it on a publicly accessible page.

---

## Schema stability

This project uses semantic versioning:

- **Major** (X.0.0): Schema-breaking changes that require downstream code updates.
- **Minor** (0.X.0): New data domains, new fields, new sources. Existing fields are not removed or renamed.
- **Patch** (0.0.X): Upstream data refreshes, bug fixes, documentation. No schema changes.

Schemas version independently from the repository version. If `word.schema.json` hasn't changed since v0.3.0 and the repo is now v0.7.2, the schema stays at v0.3.0. Check `schemaVersion` in each schema file.

**Safe assumptions for downstream code:**

- Fields present in a schema version will remain present in all future versions of that major version.
- New fields may be added in minor versions (handle unknown fields gracefully).
- The `metadata` block structure is stable across all files.
- Cross-reference files always use the `{"metadata": {...}, "mapping": {...}}` shape.

---

## Grammar dataset caveats

All 595 grammar entries carry `review_status: "draft"` — they have not been reviewed by native speakers. Your application should:

- Not present grammar data as authoritative without disclaimer.
- Check `review_status` and surface it to users if appropriate.
- Watch for future releases that upgrade entries to `community_reviewed` or `native_speaker_reviewed`.

---

## See also

- [`cookbook.md`](cookbook.md) — code examples in Python, JavaScript, and jq
- [`architecture.md`](architecture.md) — design principles and schema philosophy
- [`schema.md`](schema.md) — schema conventions and per-schema overview
- [`gaps.md`](gaps.md) — what this dataset does not cover
