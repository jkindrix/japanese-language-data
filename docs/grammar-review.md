# Grammar review

**You are reading this because you want to review grammar entries.** Thank you. Native-speaker review is the single most important remaining work in the Phase 3 grammar dataset — every one of the 595 entries currently carries `review_status: draft`, written by the project author from general grammar knowledge and awaiting expert eyes.

This document is a start-to-finish walkthrough of how to get from "I want to help" to "my review is merged." If any step is unclear, open an issue with the `grammar-review` label and say what wasn't obvious — the friction you hit is a bug in this document.

For the per-entry checklist (what a reviewer actually checks on each grammar point), see [`grammar-review-checklist.md`](grammar-review-checklist.md).

---

## Who can review

You are eligible to review if **any** of the following is true:

- You are a native speaker of Japanese.
- You have a university-level background in Japanese linguistics (undergrad minor or above), and you are comfortable judging whether an example sentence sounds natural.
- You have taught Japanese at any level to non-native learners and you are comfortable judging whether a formation rule is correctly stated.
- You are a JLPT N1 holder with demonstrable reading fluency and you are confident distinguishing what is "grammatically correct" from what "sounds natural."

If you are a confident N2 or strong N3 learner: we genuinely appreciate the interest, but please consider contributing in other ways first (error reports, sentence additions, code contributions). Grammar review needs eyes that can catch "this is technically valid but no Japanese speaker would say it that way" — a judgment that is very hard to make at N2 or below.

---

## The two review tracks

The schema allows three `review_status` values:

| Status | Meaning | Who can set it |
|---|---|---|
| `draft` | Written from general grammar knowledge by the project author. Not reviewed. | Default for every new entry. |
| `community_reviewed` | A reviewer who is not the original author has checked the entry against the checklist. | Any eligible reviewer (see above). |
| `native_speaker_reviewed` | A native Japanese speaker has checked the entry against the checklist. | Native speakers only. |

The two tracks are **parallel, not sequential**. A native speaker's review does not require a community review to have come first — a native speaker's judgment is strictly stronger. If a native speaker is reviewing, mark entries as `native_speaker_reviewed` directly. The community-review step is for eligible reviewers who are not native speakers and whose pass provides confidence that is real but not decisive.

An entry cannot be "downgraded." Once marked `community_reviewed` or `native_speaker_reviewed`, it stays at that level unless a later reviewer files a specific objection (see "Disagreement" below).

---

## The review workflow

### 1. Signal availability

Open a GitHub issue using the [`grammar-review-availability`](/.github/ISSUE_TEMPLATE/grammar-review-availability.md) template. It asks for:

- Your background (native speaker, linguistics training, teaching experience, JLPT N1)
- Which review track you can contribute to (`community_reviewed` or `native_speaker_reviewed`)
- Roughly how many entries per month you are willing to review
- Which JLPT levels you want to review

The project author will respond with a welcome, pointers, and — if applicable — a first recommended slice. You do not need to wait for an answer before starting, but announcing availability lets the project coordinate and prevents two reviewers from duplicating work on the same slice.

### 2. Claim a slice

Open a second GitHub issue using the [`grammar-review-batch`](/.github/ISSUE_TEMPLATE/grammar-review-batch.md) template to claim a specific slice of entries. A slice is a contiguous range or a filter, e.g.:

- "N5 entries 1–20 in `grammar-curated/n5.json`" (by file position)
- "All entries in `grammar-curated/n3.json` that have fewer than 3 examples" (the sparse_examples outliers — see `data/grammar/grammar.json` → `metadata.curation_outliers`)
- "All N1 entries flagged as classical/literary"

The claim is not exclusive by policy — two reviewers can cover the same slice if they want to — but it is informative, and the project will try to avoid assigning the same slice to multiple reviewers simultaneously.

Default slice size: **10–20 entries per PR**. Smaller PRs are easier to review; larger ones are easier for the reviewer to batch efficiently. Use your judgment.

### 3. Fork and branch

```bash
git clone https://github.com/<you>/japanese-language-data.git
cd japanese-language-data
git checkout -b grammar-review/n5-batch-1
```

Branch name convention: `grammar-review/<level>-<slice>` or `grammar-review/<reviewer>-<slice>`. The branch name is cosmetic but it makes parallel reviewer PRs easier to tell apart in the GitHub UI.

### 4. Review each entry in the slice

For each entry in your slice, work through `docs/grammar-review-checklist.md` in order. The checklist is ordered from fastest ("is the pattern string well-formed?") to most judgment-heavy ("does the example sound natural?"). A typical review is 3–5 minutes per entry if nothing is wrong, longer when there is a real issue.

When you find an issue:

- **For small fixes**, edit the entry in place in `grammar-curated/<level>.json`. Trivial typos, wrong `formality` labels, broken `related` refs — just fix them. These do NOT block you marking the entry as reviewed; they're part of the review.
- **For substantive issues** (formation is wrong, meaning is wrong, example is unnatural, level is miscategorized), write your comment in the `reviewer_notes` array on the entry (see format below), change what you are confident in directly, and leave the rest for the author to respond to. Do NOT mark an entry as reviewed until its substantive issues have been resolved or discussed.

### 5. Record your review

When you finish an entry, add a `reviewer_notes` entry and change `review_status` on the grammar point. The format is:

```json
{
  "id": "desu-polite-copula",
  "pattern": "Noun + です",
  ...
  "review_status": "native_speaker_reviewed",
  "reviewer_notes": [
    {
      "reviewer": "<your name or GitHub handle>",
      "date": "2026-04-15",
      "note": "Confirmed formation, examples, and usage notes. Small edit: changed formality from 'neutral' to 'formal' because です is explicitly polite. No other changes."
    }
  ],
  ...
}
```

Rules for `reviewer_notes`:

- Every non-draft entry must have at least one reviewer note (enforced by `test_grammar_review_status_state_machine` in `tests/test_data_integrity.py` — your PR CI will fail if you miss this).
- Each note has `reviewer`, `date` (YYYY-MM-DD), `note` (freeform text; short is fine if the review was "no changes needed").
- `reviewer` can be a real name, a GitHub handle, or a pseudonym — whatever you're comfortable with. The project does not require you to use your real name.
- Multiple notes accumulate over the entry's lifetime. Do not delete prior notes when adding yours; append.

### 6. Run the pipeline locally

```bash
python -m venv .venv && . .venv/bin/activate
pip install -r build/requirements.txt
just fetch
just build
just test
```

`just test` will catch a few things for you automatically:

- `test_d2_grammar_related_references_resolve` — broken `related` refs
- `test_grammar_review_status_state_machine` — non-draft entries must have reviewer notes
- `test_grammar_curated_sources_are_canonical` — the `sources` field uses the canonical string
- All the schema validations — every entry must match `schemas/grammar.schema.json`

Fix anything that fails before opening the PR.

### 7. Open the PR

```bash
git add grammar-curated/<level>.json
git commit -m "grammar-review: <level> batch <N> (<count> entries)"
git push -u origin grammar-review/<level>-batch-<N>
```

Use the [pull request template](/.github/PULL_REQUEST_TEMPLATE.md) — it has a Grammar review section that will be pre-filled. Fill in:

- Which slice you reviewed
- How many entries you touched in each review_status bucket (e.g., "20 entries: 17 → native_speaker_reviewed, 2 → community_reviewed with notes for author follow-up, 1 stays draft pending a native speaker")
- Any cross-cutting observations (patterns of errors, systemic issues, stylistic suggestions for the dataset as a whole)

### 8. Respond to PR feedback

The project author will review your PR, ask clarifying questions where needed, and merge. Reviews on reviews are normal — the project author is not a native speaker and may ask questions like "can you give a specific example of an unnatural sentence?" or "could we phrase the formation note in a way that matches the existing style?"

If your PR reveals a systemic issue (e.g., a common error across many entries in the same JLPT level), the project author may open a follow-up issue to address the pattern across the dataset rather than fixing it one entry at a time in your PR. That is a feature, not a delay — the goal is a correct dataset, not "every PR lands unchanged."

---

## Disagreement and escalation

If you disagree with a prior reviewer's judgment on an entry:

1. Do **not** delete the prior `reviewer_notes` entry.
2. Add a new `reviewer_notes` entry describing your disagreement and your proposed change.
3. Leave the `review_status` at its prior value (do not downgrade).
4. Open a GitHub issue tagged `grammar-review-disagreement` linking the entry and summarizing the disagreement.

The project author will mediate. If two native speakers disagree about a usage call, the default resolution is to state both positions in `formation_notes` and leave the call unresolved rather than picking one — Japanese usage has real regional and generational variation and the dataset should reflect that rather than imposing a false consensus.

---

## What about reviewing your own entries as the project author?

The project author is currently the author of every entry. Self-review does **not** count as `community_reviewed` — by definition, a self-review is not a community review. Entries should stay at `draft` until an external reviewer (community or native) has seen them.

The project author may re-read entries and correct typos, formation errors, or broken cross-references at any time; this does not require changing `review_status`. If the project author substantially rewrites an entry that had a prior `reviewer_notes` entry, they should add a new note acknowledging the rewrite so the review chain stays honest.

---

## What about AI / LLM review?

Do not use LLMs to mechanically generate `reviewer_notes` or to flip `review_status` to `community_reviewed` based on LLM output. An LLM reviewing its own output (or similar LLM output) does not add the epistemic signal the review pipeline is meant to capture. If you use an LLM to *help you* scan for obvious issues before your own human review, that is fine — but the review signature on the entry must be your own human judgment, and the note should reflect what *you* checked, not what the LLM said.

The project will not accept `review_status: community_reviewed` PRs whose reviewer_notes are obviously LLM-generated (vague, boilerplate, or identical across entries). This is a judgment call by the merge reviewer.

---

## Attribution and credit

Reviewers are credited in two places:

1. Every `reviewer_notes` entry on the specific grammar points they touched (permanent, in the data).
2. The "Reviewers" section in `README.md` (aggregate credit, opt-in — you tell the project author how you want to be listed).

You are under no obligation to be publicly credited. If you prefer to stay anonymous, use a pseudonym in `reviewer_notes.reviewer` and skip the README credit.

---

## See also

- `docs/grammar-review-checklist.md` — the per-entry checklist
- `docs/contributing.md` — general contribution workflow
- `docs/architecture.md` — design principles and schema philosophy
- `schemas/grammar.schema.json` — authoritative grammar entry schema
- `data/grammar/grammar.json` → `metadata.curation_outliers` — structural outliers worth prioritizing
- `tests/test_data_integrity.py::test_grammar_review_status_state_machine` — the state-machine guard
