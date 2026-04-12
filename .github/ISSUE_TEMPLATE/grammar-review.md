---
name: Grammar review feedback (native speaker)
about: Native-speaker review of a grammar entry — corrections, nuance, register
title: "[grammar review] "
labels: grammar-review
assignees: ''
---

## About you

Native speaker / fluent bilingual / advanced learner / linguist / other:

(Background helps us weight the feedback — anonymous is fine, but please indicate the category.)

## Grammar entry

File: `grammar-curated/<level>.json` or `data/grammar/grammar.json`

Entry id: (e.g., `te-shimau`, `sou-da-hearsay`)

Pattern: (paste the `pattern` field, e.g., `Verb-て form + しまう`)

## Which field?

- [ ] `meaning_en`
- [ ] `meaning_detailed`
- [ ] `formation` or `formation_notes`
- [ ] `formality` (enum value)
- [ ] `examples` (which ones and why)
- [ ] `related` cross-references
- [ ] JLPT `level` classification
- [ ] `review_status` upgrade (`draft` → `community_reviewed` or `native_speaker_reviewed`)
- [ ] Other:

## What is incorrect or misleading?

Quote the exact text and explain the issue:

```
(paste the current text here)
```

(explanation — the specific nuance, register, or fact that's off)

## What would be more accurate?

Your proposed replacement:

```
(paste the corrected text here)
```

## Additional notes

- Alternative interpretations, dialectal variation, register nuances, classical vs modern distinctions — anything that context you'd like considered.
- If you're comfortable having your name / handle credited in the entry's `reviewer_notes` field, please say so and whether to use a real name, GitHub handle, or anonymous.

## Project context

All grammar entries currently carry `review_status: "draft"`. Native-speaker review is the most important remaining work before entries can be promoted. See `docs/contributing.md` for the project's review rubric and workflow.
