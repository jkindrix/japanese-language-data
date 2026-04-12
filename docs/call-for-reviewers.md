# Call for native-speaker grammar reviewers

> **This document is a self-contained recruitment pitch.** You can copy-paste it to Reddit (r/LearnJapanese, r/linguistics, r/japanese), Discord servers, academic mailing lists, or language-learning communities. Edit the opening line to suit the platform.

---

**We built an open-source Japanese grammar dataset with 595 hand-curated entries across all five JLPT levels — and we need native speakers to review it.**

## What is this?

[japanese-language-data](https://github.com/jkindrix/japanese-language-data) is an open-source (CC-BY-SA 4.0) dataset for learning Japanese. It includes kanji, vocabulary, radicals, sentences, pitch accent, stroke order, and — most importantly — **a grammar dataset that is the project's only completely original contribution**.

The grammar covers N5 through N1 with pattern explanations, formation rules, nuance notes, formality ratings, cross-references to related patterns, and 2–3 example sentences per entry — all written in the project's own words from general, non-copyrightable grammar knowledge.

**The problem: every single entry is still `review_status: "draft"`.** Zero native speakers have reviewed any of it. We have the content; we need expert eyes.

## What would a reviewer do?

Each reviewer claims a "slice" (e.g., `n3.json entries 1–20`) and reviews each entry against a [per-entry checklist](https://github.com/jkindrix/japanese-language-data/blob/main/docs/grammar-review-checklist.md) that covers:

1. **Meaning** — is the English explanation accurate and complete?
2. **Formation** — are the conjugation/attachment rules correct?
3. **Nuance** — is the `meaning_detailed` field honest about register, region, and common misuse?
4. **Formality** — is the `formality` enum value right (formal / neutral / casual / etc.)?
5. **Examples** — are the example sentences natural, unambiguous, and level-appropriate?
6. **Related** — are the cross-references to other patterns useful and complete?

Reviewers record their findings as `reviewer_notes` entries on each grammar point and submit a pull request. The full workflow is documented at [docs/grammar-review.md](https://github.com/jkindrix/japanese-language-data/blob/main/docs/grammar-review.md).

## Two review tracks

- **Community review** (`community_reviewed`): open to anyone with strong Japanese knowledge — linguistics training, teaching experience, JLPT N1, or equivalent. Reviews grammar accuracy, formation rules, and example naturalness.
- **Native-speaker review** (`native_speaker_reviewed`): for native Japanese speakers or near-native equivalents. Covers everything in community review plus nuance, register, naturalness judgments, and edge cases that non-native speakers can't reliably assess.

A native-speaker review does not require a prior community review — you can go straight to `native_speaker_reviewed` if you're qualified.

## What's in it for you?

- **Attribution**: reviewers are credited by name (or handle, or pseudonym — your choice) in `README.md` and in the `reviewer_notes` of every entry they reviewed.
- **Impact**: this dataset is freely available to anyone building Japanese learning tools — apps, flashcard decks, study guides, NLP pipelines. Your review directly improves the quality of tools used by thousands of learners.
- **Open source**: CC-BY-SA 4.0. Your work stays free and open forever.

## How to start

1. **Signal availability**: open an issue using the [grammar-review-availability template](https://github.com/jkindrix/japanese-language-data/issues/new?template=grammar-review-availability.md) — tell us your background and which levels you're comfortable reviewing.
2. **Claim a slice**: once confirmed, open a [grammar-review-batch issue](https://github.com/jkindrix/japanese-language-data/issues/new?template=grammar-review-batch.md) to claim a specific set of entries.
3. **Review**: follow the [per-entry checklist](https://github.com/jkindrix/japanese-language-data/blob/main/docs/grammar-review-checklist.md), record your findings, and submit a PR.

The [full reviewer workflow](https://github.com/jkindrix/japanese-language-data/blob/main/docs/grammar-review.md) has all the details.

## Priority entries

Not sure where to start? The dataset's `curation_outliers` metadata highlights entries that are structurally thinnest:

- **65 entries with fewer than 3 examples** — these need more (or better) example sentences
- **8 entries with no `related` cross-references** — these need links to related patterns
- **1 entry with no `formation_notes`** — needs additional notes on irregular cases

These are triage signals, not quality judgments — but they're a good place to start if you want to review entries where your contribution will have the most visible impact.

## Questions?

Open an issue on the [GitHub repository](https://github.com/jkindrix/japanese-language-data/issues) or contact the maintainer directly.

---

*This project is maintained by Justin Kindrix ([@jkindrix](https://github.com/jkindrix)). Licensed CC-BY-SA 4.0.*
