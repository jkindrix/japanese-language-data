# Grammar review checklist

This is the per-entry checklist a reviewer works through on each grammar point. It is intentionally ordered from fastest to slowest — mechanical structural checks first, judgment-heavy semantic checks last — so you can triage quickly and spend the most effort where it matters most.

Use this alongside [`grammar-review.md`](grammar-review.md), which describes the overall workflow.

---

## How to use this checklist

1. Open `grammar-curated/<level>.json` for the level you are reviewing.
2. For each entry in your slice:
   - Work through the checklist top to bottom.
   - At the first blocking issue, stop and fix it (if you are confident) or note it in `reviewer_notes` for the author to address (if you are unsure or the fix is non-trivial).
   - When all items pass, set `review_status` to `community_reviewed` or `native_speaker_reviewed` and append a `reviewer_notes` entry summarizing what you checked.
3. Move to the next entry.

If every entry in your slice passes unchanged, your reviewer_notes entries can be brief: `"Checked formation, meaning, examples, and related refs. No changes needed."` is plenty.

---

## Structural checks (fast; mechanical)

### 1. Schema conformance

Does the entry have every required field?

- [x] `id` (slug-form identifier, stable)
- [x] `pattern` (Japanese pattern notation, e.g., `~ください`)
- [x] `level` (N5 / N4 / N3 / N2 / N1)
- [x] `meaning_en` (concise English gloss)
- [x] `formation` (how to form the pattern)
- [x] `examples` (at least 2; ideally 3)
- [x] `review_status` (you'll be changing this)
- [x] `sources` (the canonical non-copyrightable-facts string, at minimum)

The pipeline validates against `schemas/grammar.schema.json` on every build, so schema violations fail the build. If `just build` passes, schema conformance is OK. If it fails, fix the schema violation first.

### 2. `id` is stable and meaningful

- [ ] Is the `id` a slug that conveys what the pattern is?
- [ ] Is the `id` stable (not changed in this PR)?

Changing an `id` breaks `related` references from other entries and breaks any downstream consumer's cross-references. Only rename an `id` if it is genuinely wrong (typo, misleading slug). If you rename, update every other entry that references it in `related`.

### 3. `pattern` notation is well-formed

- [ ] Does the pattern use `~` (tilde) to mark the placeholder slot?
- [ ] Is the Japanese text well-formed (no missing particles, no typos)?
- [ ] Does the notation match other entries in the same file stylistically?

### 4. `level` is valid and plausible

- [ ] Is the level one of N5, N4, N3, N2, N1?
- [ ] Does the level match the file you're in (N5 entries in `n5.json`, etc.)?
- [ ] Is the level roughly consistent with the pattern's community consensus? (If you think an entry is really N2 but it's filed under N3, flag it in reviewer_notes — this is a judgment call and the default is "leave it where it is and note the concern.")

### 5. `formality` is declared and plausible

- [ ] Is `formality` one of `very_formal`, `formal`, `neutral`, `casual`, `intimate`, `vulgar`?
- [ ] Does it match the pattern? (です is `formal`; だ is `casual`; honorific keigo is `very_formal`; slang patterns might be `intimate` or `vulgar`)

### 6. `related` references resolve

- [ ] Is every id in `related` present in this file or another curated file?

The build enforces this (`test_d2_grammar_related_references_resolve`), so broken refs fail the build. But sometimes the build enforces it *per commit*, not per entry, so your local build may catch a broken ref you introduced mid-review. Re-run `just build` after each batch to catch this early.

### 7. `sources` field uses the canonical string

- [ ] Does the entry use `"General Japanese grammar knowledge (non-copyrightable facts)."` as the `sources` value?

If the entry uses the short form, update it to the canonical long form. The test `test_grammar_curated_sources_are_canonical` enforces this.

---

## Content checks (slower; requires Japanese knowledge)

### 8. `meaning_en` is accurate

- [ ] Does the English gloss capture what the pattern does?
- [ ] Is it concise (not more than one or two sentences)?
- [ ] Does it avoid promising more than the pattern delivers? (E.g., a pattern that sometimes implies surprise should say "often implies surprise," not "always expresses surprise.")

### 9. `meaning_detailed` (if present) is nuanced and accurate

- [ ] Does the longer explanation capture nuance the short gloss misses?
- [ ] Does it contrast with related patterns where the distinction matters?
- [ ] Does it avoid copying from proprietary sources? (This project does NOT use Tae Kim's Guide, Dictionary of Basic Japanese Grammar, Handbook of Japanese Grammar Patterns, or any copyrighted grammar reference. If a `meaning_detailed` looks like a direct translation of a copyrighted reference, flag it.)

### 10. `formation` rule is correct

- [ ] Is the formation rule stated precisely?
- [ ] Does it handle edge cases (ichidan vs godan, い-adjective vs な-adjective, irregular verbs)?
- [ ] Does it acknowledge alternative forms where they exist?

If the formation rule is too compressed to be correct, move the detail into `formation_notes` and keep `formation` as a one-line summary.

### 11. `formation_notes` cover exceptions and edge cases

- [ ] Do the notes call out irregular verbs (行く, する, 来る) if the pattern interacts with them?
- [ ] Do the notes mention い-adjective vs な-adjective differences where applicable?
- [ ] Do the notes mention register (plain vs polite) interactions if relevant?

Missing formation notes are not a bug per se — not every pattern has exceptions worth calling out. But if you think a critical exception is missing, add it.

### 12. `examples` are natural Japanese

**This is the most important check and the one that most benefits from native-speaker judgment.**

For each example sentence:

- [ ] Is the sentence grammatically correct?
- [ ] Does it *sound* natural? (If a Japanese person would say "technically valid but I wouldn't say it that way," flag it.)
- [ ] Does it illustrate the grammar point being taught, not some peripheral feature?
- [ ] Is the English translation accurate and natural?
- [ ] Is the Japanese-English pairing well-matched in register? (A very formal Japanese sentence shouldn't have a colloquial English translation.)

If an example is unnatural, you have three options:
- **Replace it** with a better example (mark as a substantive edit in reviewer_notes)
- **Edit it** minimally to make it natural (note the edit in reviewer_notes)
- **Flag it** for the author to replace (do not set `review_status: native_speaker_reviewed` until the example is fixed)

### 13. `examples` illustrate meaningful variation

- [ ] If there are 3 examples, do they cover at least two different contexts/scenarios?
- [ ] Do they use different vocabulary so a learner sees the pattern in multiple situations?

Three examples that all describe the same scenario with slight vocabulary swaps are less pedagogically valuable than three examples in different contexts.

### 14. `related` links are pedagogically sensible

- [ ] Do the related patterns actually help someone understand this one?
- [ ] Are the related patterns at a similar or lower JLPT level? (Linking an N5 entry to an N1 pattern is rarely helpful.)
- [ ] Are there obvious related patterns missing?

### 15. Level assignment is defensible

- [ ] Is this pattern plausibly at this JLPT level?
- [ ] If you disagree strongly, flag it with your reasoning in `reviewer_notes`.

Level assignments in this dataset are community-consensus estimates; there is no JLPT-official list. A strong disagreement should be documented, but it should not block a review — note it and move on. The project will batch level-reassignments in a dedicated follow-up pass.

---

## Process checks (end of each entry)

### 16. `reviewer_notes` entry added

- [ ] Have you appended a `reviewer_notes` entry with your name, today's date, and a short summary?
- [ ] Does it say what you checked, what you changed (if anything), and any flags for the author?

### 17. `review_status` updated

- [ ] Have you set `review_status` to `community_reviewed` or `native_speaker_reviewed`?
- [ ] If you are a native speaker: did you use `native_speaker_reviewed` rather than `community_reviewed`?

### 18. `just build && just test` passes locally

- [ ] Does the pipeline build without errors?
- [ ] Do all tests pass?

If tests fail on your branch, fix the failure before pushing. The most common failures during review:

- Broken `related` ref: you edited an `id` and forgot to update a cross-reference.
- Missing `reviewer_notes`: you set `review_status` to non-draft but forgot the note.
- Source-string drift: you added an entry with the short source string.

---

## Common pitfalls

### Register mismatch between Japanese and English

A very common issue: a Japanese example in polite speech gets a colloquial English translation, or vice versa. "お茶をいかがですか。" translated as "Want some tea?" is register-mismatched. Good translations preserve register when possible and note it explicitly when not.

### Over-specification of meaning

A pattern that has three different uses should not have a `meaning_en` that only captures one. Either the `meaning_en` should be general enough to cover all three, or `meaning_detailed` should enumerate them.

### Implicit vs. explicit level judgments

"I think this is really N2, not N3" is a legitimate reviewer observation but it is not an entry-level problem. Note it and move on. A systematic level reassignment pass is a better way to fix these than doing it ad-hoc during review.

### Ambiguous formality

Patterns like 〜じゃん are labeled `casual`, but in practice they are closer to `intimate` (only used between friends, not casual strangers). Small formality mislabels are worth fixing; borderline ones are worth flagging.

### Classical / literary N1 patterns

The N1 tier contains patterns that are classical or literary (〜や否や, 〜んばかり, etc.). These are the hardest to review because many native speakers rarely use them in everyday speech. If you are not sure whether a classical pattern is correctly described, flag the uncertainty in `reviewer_notes` and leave it at `draft` — better to wait for a specialist than guess.

---

## What if the entry is so broken it needs to be rewritten?

If you open an entry and conclude it needs substantial rewriting, you have two options:

1. **Rewrite it yourself** in the same PR if you are confident. Add a long `reviewer_notes` entry explaining the change and why.
2. **Open a follow-up issue** with the label `grammar-rewrite` describing what's wrong and what you'd replace it with. Do not mark the entry as reviewed in this PR; leave it at `draft`.

Which option is better depends on your time budget and the nature of the issue. A wholly wrong formation rule is worth rewriting in place. A pattern whose entire framing is misleading is worth a separate discussion.

---

## See also

- `docs/grammar-review.md` — the review workflow (the "how do I get from here to a merged PR" document)
- `schemas/grammar.schema.json` — the authoritative entry schema
- `data/grammar/grammar.json` → `metadata.curation_outliers` — lists of structurally thin entries worth prioritizing
