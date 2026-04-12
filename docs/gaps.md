# Gaps

What this dataset does not cover, and why. This document exists so nobody is surprised by what's missing, and so that decisions about what to add in the future are informed by a clear picture of the current scope.

When something is listed here, it is a *deliberate* gap — not an oversight. Oversights are bugs; gaps are scope decisions.

Gaps are organized by category. Within each category, items are marked:

- **INTENTIONAL** — we will not address this in any foreseeable phase.
- **DEFERRED** — planned for a later phase (see `docs/phase4-candidates.md` or a relevant phase).
- **LICENSE** — blocked by upstream licensing.
- **EFFORT** — technically possible but out of current resource scope.
- **UNCERTAIN** — we are not sure if this should be in scope at all.

---

## Grammar

### Comprehensive grammar coverage (ADDRESSED — community-standard coverage achieved)

As of v0.7.0, the grammar dataset has **595 hand-curated entries** spanning all five JLPT levels (76 N5 + 91 N4 + 139 N3 + 150 N2 + 139 N1), reaching **85–119% of the 500–700 community-standard target**. All five levels are at or near community-standard completeness. This gap is addressed at the content level.

The remaining open concern is **review quality**, not coverage volume: every entry carries `review_status: "draft"` and awaits native-speaker review. See the "Native-speaker reviewed grammar" entry below for that gap. The current per-level count is tracked in `manifest.json.grammar_curation_status`; the target remains 500–700 total entries with progressive review status upgrades as the review pipeline operates.

### Native-speaker reviewed grammar (EFFORT — pipeline exists, reviewers needed)

All 595 grammar entries carry `review_status: "draft"` — they were written from general, non-copyrightable facts about Japanese grammar in the project's own words. No content is drawn from Tae Kim's Guide (CC-BY-NC-SA, license incompatible), Dictionary of Basic Japanese Grammar (proprietary), Handbook of Japanese Grammar Patterns (proprietary), or Hanabira (license unclear). See `data/grammar/grammar.json.metadata.authorship_statement` for the full provenance details.

**The review pipeline now exists** (added in v0.7.2): `docs/grammar-review.md` documents the full workflow from "I want to help" to "my review is merged," `docs/grammar-review-checklist.md` provides a per-entry checklist, and issue templates for reviewer availability and slice-claiming are in `.github/ISSUE_TEMPLATE/`. The review status state machine (`draft` → `community_reviewed` / `native_speaker_reviewed`) is enforced by `test_grammar_review_status_state_machine`.

**Zero native-speaker reviewers are engaged as of v0.7.2.** This is the single weakest dimension of the project — the content exists, the infrastructure exists, but the humans are missing. See `docs/contributing.md § Urgent needs` for how to get involved.

The gap is *explicit* in the schema: no consumer can mistake a draft entry for a reviewed one. The `curation_outliers` metadata in `data/grammar/grammar.json` surfaces the entries most in need of review attention (sparse examples, missing related links, missing formation notes).

### Classical Japanese grammar (INTENTIONAL)

Classical Japanese (bungo, kobun) has its own grammar system significantly different from modern Japanese. Including it would roughly double the grammar corpus scope and requires different sources. This project focuses on modern (post-Meiji, post-war reform) Japanese; classical grammar is out of scope indefinitely.

Classical *texts* are a separate question — see "Classical texts" below.

### Dialect grammar (INTENTIONAL)

Japanese has substantial dialect variation (Kansai, Tohoku, Kyushu, Okinawan, etc.), and grammar differs meaningfully between them. This dataset covers standard (hyōjungo) grammar only. Some dialect *markers* are present as tags on individual entries from JMdict, but no dialect-specific grammar corpus is included. Adding dialect grammar would be a separate, scoped contribution under a future phase.

---

## Phonology and pronunciation

### Pitch accent for post-2022 vocabulary (PARTIALLY ADDRESSED)

Kanjium's pitch data was last substantially updated around 2022. A supplementary extraction from Japanese Wiktionary (`data/enrichment/pitch-accent-wiktionary.json`, 7,378 entries) fills part of the gap — these are words with pitch accent data on ja.wiktionary.org that are not in Kanjium. Combined coverage: 131,389 entries (124,011 Kanjium + 7,378 Wiktionary).

The remaining gap: vocabulary that has no pitch accent entry in either Kanjium or Wiktionary. This primarily affects very recent loanwords and niche technical terms. Consumers should still handle the "no pitch data" case gracefully.

### Pitch accent for conjugated verb forms (EFFORT)

Pitch accent shifts when verbs conjugate (e.g., the accent position in the dictionary form vs. the te-form vs. the masu form). Kanjium provides dictionary-form accents; we do not currently compute or look up accents for conjugated forms.

A well-understood algorithm for this exists (Haraguchi and others), but implementing it is a phase's worth of work and is not currently scheduled. Consumers needing conjugated-form pitch accents should use OJAD's Suzuki-kun or a similar tool directly.

### Audio recordings (DEFERRED / LICENSE)

This dataset contains no audio. Several free Japanese speech corpora exist (JSUT, JVS, Mozilla Common Voice Japanese) and are under consideration for Phase 4 as optional supplements. See `docs/phase4-candidates.md`.

Some of these corpora have restrictions on redistributing the audio files themselves (as opposed to the transcripts and metadata), so integration would likely be via linking rather than bundling.

### Regional pronunciation (INTENTIONAL)

All pronunciation data refers to Standard Japanese (hyōjungo / Tokyo dialect). Regional pronunciations, Kansai-ben accents, Hakata-ben accents, and so on are not included.

---

## Writing system

### Classical handwriting / kuzushiji (DEFERRED to Phase 4)

Kuzushiji is the cursive classical Japanese script used in historical documents. The Kuzushiji-Kanji and Kuzushiji-MNIST datasets (from the ROIS-DS Center for Open Data in the Humanities) are openly licensed and could be added as a distinct dataset in Phase 4.

### Modern handwriting samples (DEFERRED to Phase 4)

The ETL Character Database from AIST (~1.2 million images) is a Phase 4 candidate for modern handwriting samples. License is AIST terms-of-use, not CC-BY-SA, so it would be a linked supplement rather than a bundled one.

### Non-stroke-order kanji metadata (DEFERRED)

KanjiVG SVGs contain rich structural metadata (radical decomposition embedded in the SVG, stroke types, etc.) beyond just "draw this line here." We currently store the raw SVGs and do not lift this structural metadata into separate JSON fields. Phase 4 could add a `stroke-order-metadata.json` deriving structured fields from the SVG metadata for consumers that want them without parsing SVG.

### Historical kanji forms (kyūjitai) (PARTIAL)

Many modern kanji have historical forms (kyūjitai) that appear in older texts, place names, and personal names. JMdict and KANJIDIC2 include `variant` fields for these, which we preserve. There is no comprehensive kyūjitai → shinjitai mapping dataset, though — and that gap is inherited from upstream.

### Hentaigana (INTENTIONAL)

Hentaigana are obsolete variant forms of hiragana used in pre-modern Japanese. They have been assigned Unicode code points but are essentially never used in modern writing. Out of scope.

---

## Lexicon

### Jinmeiyō (name-use) kanji (ADDRESSED)

The Jinmeiyō Kanji List — kanji approved for personal-name use but not on the Jōyō list — is now shipped as `data/core/kanji-jinmeiyo.json` (863 entries, matching the official 2017 MEXT list count). This is a derived view of `data/core/kanji.json` filtered to grades 9 and 10 via `build/transform/kanji.py`. Consumers can use the Jinmeiyō view directly or join it back to the full kanji.json by the `character` field.

### Proper nouns — beyond JMnedict (LICENSE)

JMnedict covers ~720,000 names but is inherently incomplete for contemporary Japan (new people, new companies, new place names every day). More comprehensive proper-noun data would require Wikidata or similar, which has its own licensing and integration effort. Deferred indefinitely.

### Technical and domain-specific vocabulary (PARTIAL)

JMdict has tags for specialized domains (medicine, law, computing, biology, etc.), and we preserve these. However, JMdict's coverage of specialized vocabulary is uneven. Users needing deep technical coverage should consult domain-specific dictionaries separately.

### Slang and internet vocabulary (PARTIAL)

JMdict includes a meaningful amount of slang, but current internet usage (younger generations' neologisms, meme-derived expressions, social-media coinages) lags the actual language by months or years. This is a gap we cannot realistically close without a continuous collection pipeline.

### Collocations (EFFORT)

Dictionaries tell you word meanings; collocation databases tell you which words go together. There are published collocation dictionaries for Japanese, but they are proprietary. No open collocation dataset of sufficient quality exists that we could redistribute. Deferred.

### Formality / register markers beyond JMdict's tagging (EFFORT)

JMdict has tags for `hum` (humble), `pol` (polite), `hon` (honorific), `fam` (familiar), `vulg` (vulgar), etc. These are useful but not comprehensive; nuance about when to use what register is largely absent. Bridging this gap is arguably a grammar concern rather than a lexical one, and could be addressed partially in the grammar corpus (Phase 3) under formality-related patterns.

---

## Corpus data

### Parallel corpora beyond Tatoeba (PARTIALLY ADDRESSED)

As of v0.8.0, the dataset includes both Tatoeba (25,980 curated JP-EN pairs) and KFTT (443,849 Wikipedia-sourced JP-EN pairs, CC-BY-SA 3.0), totaling 469,829 sentences. KFTT sentences are machine-aligned from Wikipedia Kyoto articles — quality is variable compared to Tatoeba's editor-curated pairs.

Remaining options (JParaCrawl, WMT Japanese-English pairs) have varying licenses and would add scale but not necessarily quality. Deferred unless a concrete need for additional parallel text arises.

### Balanced written corpus (NINJAL BCCWJ) (LICENSE)

NINJAL's Balanced Corpus of Contemporary Written Japanese (BCCWJ) is the gold standard for Japanese written corpus analysis. The offline version requires a paid license application; the online version (Shonagon, Chunagon) is free for interactive query but not for bulk download. We cannot redistribute BCCWJ data. Consumers needing balanced-corpus analysis should apply to NINJAL directly.

### Spoken corpus (NINJAL CSJ) (LICENSE)

Same situation as BCCWJ. The Corpus of Spontaneous Japanese is license-gated.

### Learner corpora (EFFORT)

Corpora of L2 Japanese produced by learners at various levels (error-annotated, common mistakes, etc.) exist in academic contexts but are not openly redistributable in the form we would need. Deferred indefinitely.

### Historical and classical texts (DEFERRED)

Aozora Bunko (the Japanese Project Gutenberg) has thousands of public-domain Japanese literary texts. Phase 4 candidate for a `data/corpus/aozora/` addition. License is per-work (Japanese public domain rules), so any integration requires per-work audit.

---

## Reference materials

### Etymology (EFFORT)

JMdict has minimal etymology data. There are academic etymology sources for Japanese vocabulary, but no openly redistributable structured dataset. Deferred indefinitely.

### Comprehensive kanji etymology (EFFORT)

KANJIDIC2 contains some etymological hints (classical vs. modern forms), but no systematic etymological history. Heisig's "Remembering the Kanji" mnemonics are proprietary and cannot be bundled. Comprehensive open kanji etymology is not available in a form we can redistribute.

### Proper dictionary definitions (as opposed to gloss lists) (EFFORT)

JMdict provides English glosses — typically single words or short phrases that translate a Japanese word. It does not provide full dictionary-style definitions of Japanese words in Japanese. Monolingual Japanese dictionaries (Daijirin, Daijisen, Shinmeikai, Meikyou) are proprietary. There is no open monolingual Japanese dictionary of comparable quality.

This is arguably the single biggest gap in the open Japanese data ecosystem. It is not solvable by this project.

---

## Audio, visual, and multimedia

### Audio recordings (DEFERRED)

Covered under "Phonology" above.

### Video/subtitle data (LICENSE / INTENTIONAL)

Subtitle-extracted corpora (from anime, dorama, film) exist but are legally precarious — subtitles are copyrighted by their creators even when the underlying video is not. We do not include any subtitle data. Deferred indefinitely.

### Stroke order animations (EFFORT)

KanjiVG provides static SVGs. Animated stroke order (showing the strokes being drawn one at a time) can be generated from the SVGs programmatically, but is not included as pre-rendered animations. Consumers can generate their own from the SVG data.

---

## Implementation decisions

### Yomi-lookup (IME-style) tables (ADDRESSED)

As of v0.8.0, `data/cross-refs/reading-to-words.json` maps 24,927 kana readings to word IDs, enabling IME-style reverse lookup by pronunciation.

### Handwritten stroke-order recognition (INTENTIONAL)

This is a user interaction layer, not data. Out of scope.

### Machine-learning-ready formats (UNCERTAIN)

We emit JSON. Some ML-oriented consumers want Parquet, HDF5, Arrow, or other columnar formats. Converting is trivial but we do not currently emit these. If a Phase 4 priority emerges for ML use cases, we can add a conversion target.

### GraphQL/REST API (INTENTIONAL)

This project ships data, not services. A GraphQL or REST API over this data is a separate project that can be built by anyone using the released JSON files. We would welcome such projects but do not build them.

---

## How to challenge a gap

If you believe an item on this list should be addressed sooner, open an issue on GitHub explaining:

1. The specific gap (quote the heading)
2. Why it matters for your use case
3. What upstream source could close it (with license information)
4. An estimate of effort, if you have one

The project owner will evaluate and respond. Gaps are not frozen — they reflect current priorities, not permanent decisions (except where marked INTENTIONAL, which are deliberate scope choices).
