---
name: Grammar reviewer — claim a batch
about: Claim a slice of grammar entries to review (before opening a PR)
title: "[grammar-review: claim] "
labels: grammar-review, reviewer-claim
assignees: ''
---

**Before filing**: read `docs/grammar-review.md` for the full workflow and `docs/grammar-review-checklist.md` for the per-entry checks.

---

## Reviewer

**Name or handle**: _____

**Review track**:
- [ ] `community_reviewed`
- [ ] `native_speaker_reviewed`

If you already filed a `grammar-review: available` issue, link it here so the project can connect the two.

Link to prior availability issue (if any): #___

## Slice

**Which file / entries are you claiming?**

Examples:

- "N5 entries 1–20 in `grammar-curated/n5.json`" (by file position)
- "All 65 sparse-example entries" (see `data/grammar/grammar.json` → `metadata.curation_outliers.sparse_examples`)
- "N3 entries 60–100 in `grammar-curated/n3.json`"
- "All N1 entries tagged as classical/literary"

Your claim: _____

**Approximate entry count**: _____

**Expected completion timeframe**: _____ (e.g., "within the week", "over the next month", "one session")

## Coordination

- [ ] I have checked open PRs and issues for overlap with my claim and found none.
- [ ] I understand claims are informative, not exclusive — multiple reviewers may independently review the same slice, and both reviews are valuable.
- [ ] I have read `docs/grammar-review.md` and understand the review_status state machine.
- [ ] I will add `reviewer_notes` to every entry I touch, not just entries where I made changes.

## Questions for the project author

Any questions about the slice, the workflow, or specific entries you want clarified before you start? The author will respond here before you open the PR.
