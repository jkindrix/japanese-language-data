---
name: Data correction
about: Report an error, typo, or inaccuracy in the dataset
title: "[data] "
labels: data-correction
assignees: ''
---

## Which file?

Path of the affected file (e.g., `data/grammar/grammar.json`, `data/core/kanji.json`, `grammar-curated/n3.json`):

## Which entry?

Identifier or coordinate:
- For grammar: the `id` field (e.g., `te-shimau`, `sou-da-hearsay`)
- For kanji: the character
- For words: the JMdict `seq` id
- For radicals: the radical character
- For sentences: the Tatoeba sentence id

## What is wrong?

Be specific. Quote the exact field and value if possible.

```
(paste the incorrect entry or field here)
```

## What should it be?

Your proposed correction:

```
(paste the corrected entry or field here)
```

## Why?

Reference, native-speaker knowledge, or reasoning. For upstream-sourced data (KANJIDIC2, JMdict, KanjiVG, Wikipedia Kangxi), also note whether the error exists upstream — we prefer to file upstream rather than patch locally.

## Related

Any related entries, cross-references, or prior issues:
