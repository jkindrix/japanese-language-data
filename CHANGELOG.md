# Changelog

All notable changes to the Japanese Language Data project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). This project uses semantic versioning as defined in `docs/architecture.md`:

- **Major** (X.0.0): Schema-breaking changes that will require downstream code updates.
- **Minor** (0.X.0): New data domains, new fields, new sources, or substantial new data.
- **Patch** (0.0.X): Upstream data refreshes, bug fixes, documentation corrections, minor additions.

Unreleased changes accumulate under `[Unreleased]` until a version is tagged.

Upstream source versions used for each release are recorded in `manifest.json` at the time of the build and referenced in the relevant changelog entry.

---

## [Unreleased]

## [0.6.0] — 2026-04-12

**N2 grammar coverage reaches community-standard completeness.** After Batches B5 + B6 + B7 + B8 the grammar dataset stands at **440 entries** (60 N5 + 91 N4 + 139 N3 + **150 N2**), **63–88%** of the 500–700 community-standard target. N2 is now at 150 entries — within the ~150–180 community-consensus "complete N2" range. All new entries `review_status: "draft"`; authorship statement unchanged.

### Added (Batch B8)

- **N2 batch 4** — 30 more hand-curated N2 entries appended to `grammar-curated/n2.json`: 〜ようなら, 〜ようでは, 〜ずくめ, 〜まみれ, 〜ぶる, 〜めく, 〜ものがある, 〜というか, 〜ともなく, 〜からいうと, 〜なくもない, 〜にかかっている, 〜というのは, 〜果てに, 〜そびれる, 〜てしかるべき, 〜やしない, 〜まくる, 〜ということは, 〜ごとく, 〜ごとき, 〜かというと, 〜ものとして, 〜てもいいくらい, 〜あとは, 〜といえども, 〜と思いきや, 〜なりとも, 〜だけなら, 〜ないのみならず.
- Grammar total: 410 → **440**. N2: 120 → 150 (community-complete).

### Milestone

N2 grammar coverage reaches community-standard completeness — 150 entries, within the typical ~150–180 "complete N2" range. Tagged as **v0.6.0**. N5 and N4 remain at pre-v0.6.0 levels (60 and 91); N3 at 139 (already community-complete from v0.5.0); N1 is the remaining large gap (0 entries) to be filled in Batches B9–B12.

Honest limitations (unchanged from v0.5.0):
- Zero native-speaker reviewers engaged; everything is `draft`.
- Level assignments are community-consensus judgments; N2 has more borderline patterns than N3 or lower levels.
- N1 patterns overlap with classical / literary Japanese and have higher nuance uncertainty — flagged in advance for review.

---

### Added (Batch B7)

- **N2 batch 3** — 38 more hand-curated N2 entries appended to `grammar-curated/n2.json`: 〜次第で, 〜に至る, 〜に至るまで, 〜際(に), 〜に先駆けて, 〜を経て, 〜を踏まえて, 〜をよそに, 〜通り/〜どおり, 〜いかん, 〜得る, 〜とあって, 〜てからでないと, 〜ないことには, 〜とみえる, 〜とすれば/〜とすると, 〜はおろか, 〜にすぎない, 〜たって(casual), 〜こととて, 〜なり(as soon as), 〜なりに, 〜あっての, 〜が早いか, 〜に照らして, 〜に鑑みて, 〜を顧みず, 〜限りだ, 〜極まりない, 〜ほどのことではない, 〜ずとも, 〜だの〜だの, 〜とみる, 〜ようで, 〜さえ〜ば, だって (casual because), これといって, 〜まじき.
- Grammar total: 372 → **410** (+38). N2: 82 → 120. Coverage 53–74 → **59–82%**.
- `data/enrichment/jlpt-classifications.json`: 10,876 → **10,914**.

### Added (Batch B6)

- **N2 batch 2** — 41 more hand-curated N2 entries appended to `grammar-curated/n2.json`: 〜末に, 〜だけのことはある, 〜までもない, 〜というものだ / 〜というものではない, 〜ものだから, 〜やら〜やら, 〜からして, 〜からすると/〜からすれば, 〜からには, 〜のみならず, 〜とはいえ, 〜とはいうものの, 〜にしてみれば, 〜からといって, 〜のことだから, 〜てからというもの, 〜つつある, 〜だけましだ, 〜や否や, 〜か〜ないかのうちに, 〜そばから, 〜じゃあるまいし, 〜とばかりに, 〜とあれば, 〜ないまでも, 〜のもとで, 〜に足る, 〜に堪える, 〜に堪えない, 〜てやまない, 〜そうにない, 〜ずじまい, 〜たところで, なにしろ, なにせ, 〜あげく, 〜反面, 〜から見ると, 〜ということだ, 〜結果.
- Grammar total: 331 → **372** (+41: second N2 batch). N2: 41 → 82. Coverage 47–66 → **53–74%** of the 500–700 target.
- `data/enrichment/jlpt-classifications.json`: 10,835 → **10,876**.

### Added (Batch B5)

- **N2 batch 1** — new `grammar-curated/n2.json` file with **41 hand-curated N2 entries**: 〜にあたって, 〜に先立って, 〜をきっかけに, 〜を契機に, 〜につき, 〜ゆえに, 〜ことから, 〜あまり, 〜ばこそ, 〜からこそ, 〜に伴って, 〜に応じて, 〜にこたえて, 〜にかかわらず, 〜にもかかわらず, 〜を問わず, 〜はともかく, 〜はさておき, 〜に限って, 〜に限らず, 〜ずにはいられない, 〜ないではいられない, 〜てはいられない, 〜にしろ/〜にせよ, 〜としても, 〜(よ)うと, 〜(よ)うと〜まいと, 〜まい, 〜抜く, 〜かねない, 〜かねる, 〜づらい, 〜がたい, 〜べく, 〜はもちろん, 〜を通じて/通して, 〜にわたって, 〜を中心に, 〜を込めて, 〜にしては, 〜にして.
- Grammar total: 290 → **331** (+41: first N2 content). By-level: N5 60, N4 91, N3 139, **N2 41**. Coverage 41–58 → **47–66%** of the 500–700 target.
- `data/enrichment/jlpt-classifications.json`: 10,794 → **10,835** (+41 grammar classifications auto-emitted).



**N3 grammar coverage reaches community-standard completeness.** After Batches B1 + B2 + B3 + B4 the grammar dataset stands at 290 entries (60 N5 + 91 N4 + 139 N3), 41–58% of the 500–700 community-standard target. N3 is now at 139 entries — within the ~140–160 community-consensus "complete N3" range. All new entries `review_status: "draft"`; authorship statement unchanged (written in our own words from general non-copyrightable grammar knowledge; no content from copyrighted grammar references).

### Added (Batch B4)

- **N3 expansion batch 4 (39 entries)** bringing N3 from 100 → 139: 〜っけ (casual wondering), 〜もの / 〜もん (emotional reason); 〜ないで (without doing, casual of 〜ずに); 〜にちがいない (certainty), 〜ことだ (firm advice), 〜(より)ほかない (no choice but), 〜ことに (emotional reaction), 〜くらいなら (rather than), 〜にかけて (through / excel at), 〜以上(は) (since / as long as), 〜以外 (other than), 〜おきに (intervals), 〜ごとに (each), 〜代わりに (instead), 〜んだから (emphatic since), 〜わけがない (no way), しょうがない / 〜てしょうがない / 〜てしかたがない (can't be helped family), 〜っこない (absolutely not casual), 〜なんて (how / dismissive) and 〜なんか (dismissive casual), 〜ぶりに (for the first time in), 〜上は (now that, formal), 〜ないわけにはいかない (can't not) and 〜わけにはいかない (can't afford to), 〜ついでに (while I'm at it), 〜をはじめ (starting with), 〜ものなら (if possible), 〜てこそ (only by), 〜ばかりでなく / 〜だけでなく (not only X but also Y, formal and neutral), 〜に決まっている (definitely), 〜ずに済む (manage without), 〜に比べて (compared to), 〜となれば / 〜となると (if / when it comes to), 〜て初めて (only after).

### Verification

- **62/62 tests pass** — existing invariants continue to cover all new entries.
- **19/19 data files validate** against their schemas (no schema changes across B1–B4).
- **`data/grammar/grammar.json`**: 81 (v0.4.1 baseline) → **290 entries** (+209: 10 N5 + 60 N4 + 139 N3, of which 40 N3 were already in v0.4.1 baseline's N3 slot after batch 0).
- **`data/enrichment/jlpt-classifications.json`**: 10,585 → **10,794** (+209 grammar classifications, auto-emitted by `build/transform/jlpt.py` reading the curated files).
- **`manifest.json.grammar_curation_status`** refreshed: total 81 → 290; by_level {N5 50→60, N4 31→91, N3 0→139}; coverage_pct 11–16 → 41–58; draft 81 → 290.
- All new `related` cross-references resolve (hard-enforced at build time and by `test_d2_grammar_related_references_resolve`).

### Milestone

This is the first batch where N3 reaches community-standard completeness (~140 entries). It is tagged as v0.5.0 to mark the N3 milestone within the larger grammar expansion effort. N4 is at 91 entries (community-standard is ~80–100, so also close to complete). N5 is at 60 entries (community-standard is ~80, so close but not quite). N2 and N1 remain to be curated in subsequent batches.

Honest limitations:
- Zero native-speaker reviewers engaged; everything is `draft`.
- Level assignments are community-consensus judgments; some patterns live on the N3/N2 and N3/N4 borders and may shift with future review.
- Example sentences are original (not from Tatoeba); a future batch could text-match with the sentences corpus.
- Rare / formal patterns (especially in B3 and B4) may need nuance correction by native speakers.

---

## [Unreleased-prior]

Continuing multi-batch grammar expansion push toward the ~500-700 community-standard target. After Batches B1 + B2 + B3: 251 entries total (60 N5 + 91 N4 + 100 N3), 36–50% of target. All new entries `review_status: "draft"`, authorship statement unchanged.

### Added (Batch B3)

- **N3 expansion batch 3 (40 entries)** bringing N3 from 60 → 100: relational markers 〜に対して, 〜に関して, 〜に沿って, 〜にかわって, 〜として, 〜において; targeted-for markers 〜向け and 〜向き; parallel-change 〜につれて and 〜とともに; exclusivity 〜きり and temporal 〜たきり; causal-proportional 〜だけに and 〜だけあって; trigger-consequence 〜ばかりに and additive 〜ばかりか; speech/topic markers 〜というより, 〜と言えば, 〜と言っても, 〜といった; appearance suffixes 〜っぽい and 〜げ; strong contrastive 〜どころか and 〜どころではない; balance 〜一方で and trend 〜一方だ; addition 〜上に and prerequisite 〜上で; relative-standard 〜わりに; overwhelming states 〜てたまらない and 〜てならない; temporal 〜中 and tendency 〜気味; verb-compound auxiliaries 〜続ける, 〜直す, 〜合う, 〜出す, 〜込む; and 〜をもとに (based on) and 〜最中 (in the middle of).

### Verification (Batch B3)

- **62/62 tests pass** — existing invariants cover the new entries.
- **19/19 data files validate** against their schemas.
- **`data/grammar/grammar.json`**: 211 → **251 entries** (+40 N3).
- **`data/enrichment/jlpt-classifications.json`**: 10,715 → **10,755**.
- **`manifest.json.grammar_curation_status`** refreshed: total 211 → 251; N3 60 → 100; coverage_pct 30–42 → 36–50.
- One self-caught broken `related` reference during the initial build (placeholder slug `nanishiro-iro` typo in `to-iu-yori-rather` — caught by the build-time check in `build/transform/grammar.py`, fixed before commit).



### Added (Batch B2)

- **N4 expansion batch 2 (25 entries)** bringing N4 from 66 → 91: やる (casual give), 〜ても (even if, concessive); the honorific verb family いらっしゃる / おっしゃる / ご覧になる / なさる and the humble verb family 参る / 申す / いただく / くださる; 〜しか〜ない (only, negative-polarity); the が-marking predicate family 〜が好き/嫌い / 〜がわかる / 〜ができる / 〜が聞こえる/見える; たとえ〜ても (emphatic even if); sentence-initial conjunctions だから / それで / それから / しかし / けれども / それでも; 〜とか (casual listing), 〜って (casual quotation), 〜ものだ (general truth / nostalgic).
- **N3 expansion batch 2 (20 entries)** bringing N3 from 40 → 60: 〜つつ (while/although formal), 〜さえ (even, emphatic), 〜こそ (precisely), 〜たとたん (the moment), 〜次第 (depending on / as soon as), 〜にしたがって (in accordance with), 〜限り (as long as / unless), 〜だらけ (full of), 〜ふりをする (pretend), 〜くせに (despite, critical), 〜わけだ (it means) and 〜わけではない (not necessarily), 〜ようがない (no way to), 〜っぱなし (left in state / nonstop), 〜ものの (although formal), 〜にしても (even if), 〜かのように (as if), 〜とは限らない (not necessarily), 〜ないことはない (it's not that I can't), 〜以来 (ever since).

### Verification (Batch B2)

- **62/62 tests pass** — existing invariants cover the new entries.
- **19/19 data files validate** against their schemas.
- **`data/grammar/grammar.json`**: 166 → **211 entries** (+45: 25 N4 + 20 N3).
- **`data/enrichment/jlpt-classifications.json`**: 10,670 → **10,715**.
- **`manifest.json.grammar_curation_status`** refreshed: total 166 → 211; N4 66 → 91, N3 40 → 60; coverage_pct 24–33 → 30–42; draft 166 → 211.

### Added (Batch B1)

Batch B1 of the multi-batch grammar expansion push toward the ~500-700 community-standard target. After this commit: 166 entries total (60 N5 + 66 N4 + 40 N3), 24–33% of target. All new entries `review_status: "draft"`, authorship statement unchanged.

### Added (Batch B1)

- **N5 fill (10 entries)** appended to `grammar-curated/n5.json`, bringing N5 from 50 → 60: 〜ませんか (invitation), もう + Vた (already), まだ + Vていない/Vている (not yet / still), 〜とき(に) (when basic), 〜と一緒に (together with), 〜だけ (only basic), i-adj 〜く adverbial, na-adj 〜に adverbial, i-adj 〜くて joining, na-adj/noun 〜で joining. Focuses on the essentials that were missing from the v0.3.0 N5 batch — most commonly taught in Genki I lessons but absent from our initial curation.
- **N4 expansion batch 1 (30 entries)** appended to `grammar-curated/n4.json`, bringing N4 from 36 → 66: 〜てから, 〜前に, 〜後で (temporal sequence trio); 〜ことができる (can), 〜ことにする / 〜ことになる (decide / be decided); 〜なさい (gentle command), 〜てほしい (want someone to); 〜し (reason listing), 〜ようと思う (intend to); the giving-verb system (〜てくれる, 〜てもらう, 〜てあげる, あげる, くれる, もらう); keigo basics (お〜ください, 尊敬語 〜れる/られる, 謙譲語 お〜する); 〜てごらん (warm try-suggestion), こういう/そういう/ああいう/どういう (kind-of series), 気がする (feel like), 〜たいと思う (polite desire), 〜場合 (in case), 〜ずつ (each), 〜つもりだった (had intended), 〜はずだった (was supposed to), でも (even/casual suggestion), 〜ていただく (polite request), 〜ばいい (just need to).

### Verification (Batch B1)

- **62/62 tests pass** — existing invariants cover the new entries; no test count change.
- **19/19 data files validate** against their schemas.
- **`data/grammar/grammar.json`**: 126 → **166 entries** (+40: 10 N5 + 30 N4).
- **`data/enrichment/jlpt-classifications.json`**: 10,630 → **10,670** (+40 grammar classifications).
- **`manifest.json.grammar_curation_status`** refreshed: total_entries 126 → 166; by_level {N5:60, N4:66, N3:40}; coverage_pct 18–25 → 24–33; draft 126 → 166.
- All new `related` cross-references resolve.

First substantive grammar-content push after the v0.3.0 foundation. Also reconciles a documentation contradiction between `docs/gaps.md` and CHANGELOG [0.3.0] on what "N5+N4 complete" actually means, and refreshes `manifest.json.next_actions` which had gone stale during the v0.3.1/v0.3.2/v0.4.x review-fix cycles.

### Added

- **Grammar N3 batch 1** (`grammar-curated/n3.json`, **40 new hand-curated entries**): First substantial N3 curation after v0.3.0's N5+N4 foundation. Entries span modal/evidential (〜そうだ appearance, 〜そうだ hearsay, 〜ようだ, 〜みたい, 〜らしい), te-form auxiliaries (〜ておく, 〜てしまう, 〜てある, 〜てみる, 〜ていく, 〜てくる), temporal/sequence (〜ながら, 〜うちに, 〜間/間に, 〜たばかり, 〜たところ), reason/purpose/contrast (〜ために, 〜ように purpose, 〜のに, 〜おかげで/〜せいで), quantity/degree (〜ばかり, 〜かける, 〜ほど, 〜くらい), nominalizers (〜こと, 〜の), temporal/relational (〜たびに, 〜かどうか, 〜について, 〜にとって, 〜によって), should/obligation (〜べきだ, 〜たほうがいい, 〜なくちゃ/〜なきゃ), advanced conditional/causative (〜ばよかった, 〜ば〜ほど, causative-passive 〜させられる), and manner/state (〜まま, 〜ずに, 〜たがる). All 40 entries follow the established authorship statement: written in our own words from general non-copyrightable grammar knowledge, `review_status: "draft"`, `sources: ["General Japanese grammar knowledge (non-copyrightable facts)."]`, every example `source: "original"`. Cross-references to existing N4/N5 entries via the `related` field enable learner-pathing lookups. Pattern selection drew on community-consensus N3 inventories (JLPTsensei, Bunpro) for coverage, but every explanation is original.
- **Grammar N4 supplement** (`grammar-curated/n4.json`, **5 new entries**): Fills the most glaring N4 holes identified during N3 curation and investigation — 〜たり〜たりする (non-exhaustive action lists), 自動詞/他動詞 (transitive/intransitive pair concept), 〜がる (third-person emotion), 〜方 (way of doing), and 〜ようにする (make it so / try to). Brings N4 count from 31 → 36 entries. These are all universally-N4 patterns (not borderline N3); more N4 fill is expected in subsequent batches.

### Fixed / clarified

- **`docs/gaps.md` grammar-coverage paragraph reconciled with CHANGELOG [0.3.0]**: The "Comprehensive grammar coverage" section in `docs/gaps.md` previously committed to "N5 and N4 being complete (~140 points)" at v0.3.0, which contradicted CHANGELOG [0.3.0] § "Deliberate scope choices", where v0.3.0 was explicitly framed as "N5 essentials + N4 selections, not complete N5+N4". Rewrote the paragraph to reflect the progressive, phase-spanning curation approach actually in use, reference CHANGELOG [0.3.0] for the original framing, and point readers to `manifest.json.grammar_curation_status` for up-to-date per-level counts. Section heading updated from "DEFERRED to Phase 3" to "IN PROGRESS — Phase 3".
- **`manifest.json` `next_actions` refreshed** for the post-v0.4.1 state: The previous list read "Target N3 grammar points in v0.3.1, N2 in v0.3.2, N1 in v0.3.3" — a stale v0.3.0-era plan that was superseded when v0.3.1/v0.3.2 were consumed by external-review fix cycles and v0.4.x by radicals/review work. Rewrote to reflect the current plan: N3 expansion continues toward a v0.5.0 tag when a stable N3 milestone is reached; N4 fill continues in parallel; Tatoeba linkage text-match remains a pending low-effort improvement; Phase 4 radical alias table and post-2022 pitch accent fill remain pending. Also added `grammar_curation_status.by_level` so per-level counts are directly readable without needing to parse the full grammar dataset.

### Verification

- **62/62 tests pass** — no test count change; new entries are covered by existing invariants (`test_d2_grammar_related_references_resolve`, `test_invariant_grammar_jlpt_ids_resolve`).
- **19/19 data files validate** against their schemas (no schema changes).
- **`data/grammar/grammar.json`**: 81 → **126 entries** (50 N5 + 36 N4 + 40 N3).
- **`data/enrichment/jlpt-classifications.json`**: 10,585 → **10,630** (+45 grammar classifications auto-emitted by `build/transform/jlpt.py` reading the new curated files).
- All new `related` cross-references resolve (hard-enforced at build-time by `build/transform/grammar.py` and at test-time by the D2 regression test).

---

## [0.4.1] — 2026-04-11

Third external-review response cycle. Addresses every finding (F1–F6) from the post-v0.4.0 review. No new data domains, no scope expansion; each change targets exactly one flagged concern.

### Fixed / clarified

- **F1 — Schema version drift clarification** (`docs/architecture.md`). The review observed that 11/14 schemas are at `schemaVersion: "0.3.0"`, 2 at `"0.3.2"`, 1 at `"0.4.0"`, and asked whether this is drift or deliberate. **It is deliberate.** Updated `docs/architecture.md` § "Versioning within the schema" with an explicit "schemas version independently from the repo and from each other" paragraph. Schemas that have not been meaningfully restructured stay at their last-meaningful-update version; bumping on every repo release would produce noise and diminish the signal value. No schema edits.
- **F2 — Upstream contribution principle vs reality** (`docs/upstream-issues.md`). The review flagged that Design Principle 6 promises filing upstream, but zero items have been filed through Phase 4. **Added an explicit "Phase 1–4 filing status" section at the top of `docs/upstream-issues.md`** honestly accounting for what was found (and not found) in each phase. Phases 1, 2, 4 found no substantive upstream defects; Phase 3 is hand-curated and had no upstream interactions. The two internal schema gaps in "Pending" are *our* schemas, not upstream defects. Design Principle 6 is documented as an ethical commitment maintained even when there is nothing concrete to file.
- **F3 — Grammar curation operational status** (`manifest.json`). The review flagged that the grammar review pipeline is documented in `docs/contributing.md` but nothing at the manifest level makes the operational status explicit. **Added `manifest.json.grammar_curation_status`** with exact counts (81 entries, all draft, zero reviewers engaged), target range, review-status distribution, and an honest note that "the grammar dataset is usable-but-not-authoritative until this changes."
- **F4 — Cross-refs metadata gap** (`schemas/cross-refs.schema.json` + `build/transform/cross_links.py`). The review noted that the 4 files in `data/cross-refs/` do not carry `license` or `source` metadata — a doctrinal inconsistency with Design Principle 2 ("every data file carries metadata identifying its source(s) and license"). **Added `license` and `source` as optional (non-required) properties** to the cross-refs schema, and populated them in `build/transform/cross_links.py`. All 4 cross-reference files now carry a provenance statement and an explicit license declaration. Backward-compatible: fields are optional, existing consumers unaffected.
- **F5 — Transformer unit tests added** (`tests/test_transform_units.py`, 5 tests). The review flagged that the test suite exercises transformer code indirectly through built-data invariants only — a subtle transformer bug must actually corrupt data to be caught. **Added function-level unit tests for `_conjugate_godan`** covering the v5k-s/v5u-s/v5aru/v5r-i edge cases that previously regressed (D1/B1):
  - `test_conjugate_godan_v5k_s_iku_te_ta_forms` — 行く te/ta use って/った
  - `test_conjugate_godan_v5u_s_tou_te_ta_forms` — 問う te/ta use うて/うた
  - `test_conjugate_godan_v5aru_i_stem_and_imperative` — いらっしゃる polite i-stem and imperative
  - `test_conjugate_godan_v5r_i_bare_aru_suppletive_negative` — bare ある suppletive ない, keeps あれ/あろう
  - `test_conjugate_godan_v5r_i_compound_koto_ga_aru_prefix` — compound v5r-i prefix preservation and slot blanking
  All 5 pass; total test count 57 → 62.
- **F6 — `display_forms` heuristic refactored for auditability** (`build/transform/conjugations.py`). The review flagged the `_compute_display_forms` function as "dense and hard to audit by sight." **Split into four named helpers**:
  - `_longest_common_suffix_length(a, b)` — the suffix-overlap computation
  - `_replace_prefix_in_forms(forms, old, new)` — the form-by-form rewrite primitive
  - `_display_forms_adj_na(...)` — the class-aware branch for na-adjectives
  - `_display_forms_common_suffix(...)` — the verb/adj-i heuristic
  - `_compute_display_forms(...)` — now just a 5-line dispatcher
  Strictly behavior-preserving: `data/grammar/conjugations.json` output is byte-identical before and after. The existing `test_m1_display_forms_preserves_kanji_prefix` regression test continues to pass without modification.

### Not changed (per the review's own finding F7 and out-of-scope items)

- **F7 (Radicals Wikipedia parser is brittle)** — the review explicitly says "15-minute middle-ground: None needed — the tripwire is the right control." The `test_radicals_wikipedia_coverage_above_threshold` test is the correct defense for this risk class. No change.
- **Schema version bumps on the 11 schemas at 0.3.0** — per the F1 clarification, these are deliberately stable. No change.
- **Filing actual upstream issues** — per F2, through Phase 4 nothing substantive has been found to file. The principle is maintained; filing will occur when defects are actually discovered. No change.
- **Recruiting native-speaker reviewers for grammar** — out of session scope (requires human outreach channels). The F3 fix makes the gap explicit in manifest.json so the operational status is no longer only in prose.

### Verification

- 62/62 tests pass (57 prior + 5 new transformer unit tests)
- 19/19 data files validate against their schemas
- `just ci` passes end-to-end with byte-stable output
- `_compute_display_forms` refactor produces byte-identical conjugations.json output (verified via existing regression test)

---

## [0.4.0] — 2026-04-11

**First Phase 4 candidate delivered**: Wikipedia ingestion for Kangxi radical meanings. Also integrates a global User-Agent header for polite HTTP fetches (required by Wikipedia, polite elsewhere) and a trailing-edge cleanup of the CHANGELOG double-count presentation in [0.1.0] and [0.2.0].

This release introduces Wikipedia as a new pinned upstream source — the first source outside the EDRDG / KanjiVG / Tatoeba / Kanjium / Waller set used through v0.3.2. The ingestion pattern (action=raw wikitext, regex-based wikitable parsing, schema-stable join) is reusable for future Wikipedia-sourced data.

### Added

- **Wikipedia Kangxi radicals source** pinned in `build/fetch.py` at revision `1346511063` of the Wikipedia article "Kangxi radicals". Uses the `action=raw` endpoint on `index.php` for stable wikitext without JSON wrapping; SHA256-verified like every other source. Cached at `sources/wikipedia/kangxi-radicals.wikitext`.
- **Wikipedia Kangxi wikitable parser** in `build/transform/radicals.py` that extracts the 214 classical radicals, their English meanings, Kangxi numbers, and alternate forms (e.g., `亻` and `𠆢` listed under radical 9 `人`). Uses regex-based wikitext parsing with MediaWiki `{{lang|...}}` template unpacking. Reusable pattern for future Wikipedia-sourced data.
- **Global User-Agent header** on every `build/fetch.py` download, compliant with [Wikipedia's User-Agent policy](https://meta.wikimedia.org/wiki/User-Agent_policy). UA string: `japanese-language-data/0.4.0 (https://github.com/jkindrix/japanese-language-data; reproducible-build fetcher)` — descriptive, includes a contact URL, polite to all hosts.
- **Regression test** `test_radicals_wikipedia_coverage_above_threshold` in `tests/test_data_integrity.py`: asserts ≥77% radical-meaning coverage, equal meaning/classical_number coverage, and canonical spot-checks (一 #1 "one", 人 #9 "man", 水 #85 "water").

### Changed

- **`data/core/radicals.json` enriched**: **197 of 253 radicals (77.9%)** now have non-empty `meanings` arrays and non-null `classical_number` fields, populated from Wikipedia. Previously 0 of 253. Each Wikipedia row with multiple equivalent English words (e.g., radical 10 `儿` "son, legs") becomes a multi-element meanings array.
- **Schema `schemas/radical.schema.json`** bumped from `0.3.2` to `0.4.0` to reflect the populated-by-default semantics of `meanings` and `classical_number`.
- **Metadata fields added to `data/core/radicals.json`**: `source_version_wikipedia` (article, revision, URL), `radicals_total`, `radicals_with_meaning`, `radicals_meaning_coverage_pct`, attribution extended with Wikipedia credit, and the `warning` field updated to reflect actual coverage and enumerate the specific variant forms still without meanings.
- **`ATTRIBUTION.md`** adds a Wikipedia Kangxi radicals entry with required attribution wording.
- **`docs/sources.md`** adds a full Wikipedia Kangxi radicals section describing fetch method, coverage, known limitations, and attribution.
- **`docs/phase4-candidates.md`** adds an "Addressed Phase 4 items" section marking "Radical meanings and Kangxi numbers" as DELIVERED in v0.4.0 and explains the remaining 22.1% gap.
- **`manifest.json`** version bump to `0.4.0`, phase from 3 to 4, phase description rewritten to reflect Phase 4 activity.
- **`README.md`** status line reflects Phase 4 activity.

### Changed (trailing-edge cleanup of v0.3.2 review)

- **CHANGELOG [0.1.0] and [0.2.0]** — extended the M3 double-count presentation fix to these two earlier version entries. The v0.3.2 plan only updated [0.3.0] per explicit scope; the v0.3.2 completion report flagged the rest as follow-up. [0.1.0] now shows 280,445 rows / 62,136 unique; [0.2.0] now shows 478,892 rows / 260,583 unique, consistent with [0.3.0]'s format.
- **`.github/workflows/build.yml`** — the summary message had hardcoded `"18 files"` and `"tests (48)"` which were stale after v0.3.1 and v0.3.2. Replaced with a counts-free message that points to the stats report step output, so it no longer drifts when counts change.

### Known limitations

- **56 radicals still have empty meanings (22.1% of 253)**. These are Japanese-dictionary-specific variants that do not appear in the Wikipedia Kangxi table: simplified forms (`亀` for `龜`, `歯` for `齒`, `麦` for `麥`, `黄` for `黃`, `黒` for `黑`, `竜` for `龍`), katakana-shaped markers (`ノ`, `ハ`, `マ`, `ユ`, `ヨ`), fullwidth pipe (`｜` vs Kangxi's `丨`), and Nelson-style dictionary variants (`个`, `乃`, `久`, `九`, ...). Closing this requires a curated variant-to-Kangxi alias table, deferred as a v0.4.x patch.
- **Wikipedia's stroke count column is ignored.** RADKFILE is the authoritative source for stroke counts in this dataset; pulling a second source for the same field risks divergence. Documented in radicals.json metadata field_notes.
- **Revision drift**: the Wikipedia article can change over time. We pin to a specific revision (1346511063). A future maintainer wanting fresher Wikipedia content must bump the pin in both `build/fetch.py` and `build/transform/radicals.py` deliberately.

### Verification

- 57/57 tests pass (56 prior + 1 new radicals regression test)
- 19/19 data files validate against their schemas
- Wikipedia source SHA256-verified at fetch time (sha256=62e0c85ebcc33976…, size=74,968 bytes)
- `just ci` passes end-to-end with byte-stable output

---

## [0.3.2] — 2026-04-11

Second post-review defect-fix cycle. Addresses findings B1–B3 and M1–M4 from the external review of v0.3.1, plus a byte-reproducibility defect (non-deterministic set iteration in stroke_order.py) discovered during v0.3.2 verification. Also includes the previously-unreleased jinmeiyō view, Tatoeba linkage, CI smoke test, and stroke-count mismatch metadata (originally slated for v0.3.1-continued; now shipped together with the B/M fixes).

### Fixed (post-review findings B1–B3, M1–M4)

- **B1**: `build/transform/conjugations.py` v5r-i override for compound verbs. The previous version set `forms["nai_form"] = "ない"` as a literal string, which was correct for the bare verb ある but wrong for the three compound v5r-i entries (である, 事がある, でもある) where the prefix before the final ある was dropped. Fix: when stem ends in `ある`, strip the final `ある` and prepend the remaining prefix to `ない` / `なかった`, producing でない / ことがない / でもない respectively. Bare ある still emits `"ない"` because its prefix is empty. Additionally, for compound v5r-i entries, the `potential` / `passive` / `causative` / `imperative` / `volitional` / `conditional_ba` forms are now blanked (empty string) — these are not well-formed for ある-compounds and previously emitted grammatically-nonsensical output like ことがあれ (imperative of 事がある) and ことがあろう. The bare verb ある still emits its regular forms (あれば, あろう, etc.), which are in active modern use.
- **M1**: `data/grammar/conjugations.json` entries now include a `display_forms` companion dict alongside `forms`. The previous version emitted forms as kana only, forcing consumers to manually reconstruct kanji-preserving display forms (e.g., given `dictionary_form: "行く"` and `te_form: "いって"`, a consumer wanting to display `行って` had to know which leading characters of the dictionary were kanji). Fix: `build/transform/conjugations.py` now computes `display_forms` via two strategies — (1) a common-suffix heuristic for verbs and adj-i: find the longest common suffix between dictionary_form and reading, then replace the reading prefix with the kanji prefix in each form; (2) a class-aware branch for adj-na: every na-adjective form is `reading + copula`, so the reading prefix is replaced with `dictionary_form` directly, handling compound readings like 大切 (たいせつ) → 大切です where the kanji and kana share no trailing character. Verified against 3,174 kanji-containing entries: 100% improvement across v1, v5*, adj-i, adj-na. Zero wrong outputs — pure-kana dictionaries and forms that don't start with the reading prefix preserve the original kana form. `schemas/conjugations.schema.json` bumped to `0.3.2` with the new property documented.
- **M2**: `schemas/stroke-order.schema.json` did not list the `metadata.warnings` and `metadata.stroke_count_mismatches` fields that the stroke-order transform emits (added in the unreleased 1b218ed commit). Validation passed only because the metadata `$def` did not set `additionalProperties: false`. Schema-only consumers had no way to discover these fields existed. Fix: adds explicit property definitions and descriptions. Schema version bumped to `0.3.2`.
- **B2**: `docs/gaps.md` Jinmeiyō entry was stale. The 9293c76 commit added `data/core/kanji-jinmeiyo.json` (863 entries) but the gaps doc still listed the Jinmeiyō view as DEFERRED with a stale path suggestion (`data/enrichment/jinmeiyo-view.json`). Updated to ADDRESSED with the current path and count.
- **B3**: `docs/sources.md` scriptin/jmdict-simplified asset table still listed `kanjidic2-en-<ver>.json.tgz | KANJIDIC2 English | 1.3 MB`. The upgrade to `kanjidic2-all` (13,108 characters, all languages, 1.55 MB) shipped in v0.1.0 and is documented in the CHANGELOG, but this table row was never updated. Corrected.
- **M3**: `build/stats.py` `TOTAL` line double-counted the kanji derivative views (`kanji-joyo`, `kanji-jinmeiyo`) and included the gitignored `words-full.json`. The `CHANGELOG.md` [0.3.0] section copied the same inflated number ("Total committed entries: 495,766"). Fix: preserves the existing sum as `TOTAL (all rows)` for continuity and adds a new `UNIQUE COMMITTED` line that excludes derivative views and gitignored artifacts. The [0.3.0] CHANGELOG line is split into `Total rows (with derivatives and gitignored): 495,766` and `Unique committed entries: 277,457`.

### Fixed (byte-reproducibility regression discovered during verification)

- **stroke_order.py determinism**: `build/transform/stroke_order.py` iterated a Python `set` (`kanji_set`) when appending missing-SVG entries to the characters index. Python set iteration order is non-deterministic, so consecutive rebuilds produced the same content but with different key ordering in `data/enrichment/stroke-order-index.json` — a 13,386-line "diff" with zero semantic changes. This directly violated design principle #1 in `docs/architecture.md` ("Every byte of built data must be reproducible by running the pipeline from a clean clone"), and it undermines `just ci`'s source caching (keyed on `manifest.json` hash) and cold-clone byte-matching verification. Two-line fix: (1) iterate `sorted(kanji_set)` so the insertion sequence is deterministic; (2) emit `dict(sorted(index_entries.items()))` at the final output step so the characters map is in sorted Unicode-codepoint order. This normalizes both the ZIP-iterated portion (formerly in archive order) and the missing-entries portion. Manual double-build byte check confirmed byte-identical output on consecutive runs. This defect was not part of the original review plan — it was discovered during v0.3.2 verification, flagged, and promoted into scope rather than ship with a known regression from the v0.3.1 quality bar.

### Added (test coverage — M4 and new regression guards)

- **M4**: four data integrity invariant tests in `tests/test_data_integrity.py`. These are pure invariants that should hold on every build, not tied to a specific past defect:
  - `test_invariant_jlpt_waller_values_valid`: every `jlpt_waller` value on kanji and word entries is in `{N1,N2,N3,N4,N5}` or null.
  - `test_invariant_word_to_sentences_ids_exist`: every sentence_id in `word-to-sentences.json` exists in `sentences.json`.
  - `test_invariant_grammar_jlpt_ids_resolve`: every `grammar_id` in the JLPT classifications (kind=grammar) resolves to a grammar point in `grammar.json`.
  - `test_invariant_word_to_kanji_inverse_of_kanji_to_words`: `word-to-kanji.json` is the exact inverse of `kanji-to-words.json` for every (kanji, word_id) pair.
- **B1 regression tests** in `tests/test_data_integrity.py`: `test_b1_v5r_i_nai_form_has_correct_prefix` and `test_b1_v5r_i_compound_has_no_malformed_imperatives`. Both fail on the pre-fix data and pass on the post-fix data.
- **M1 regression test** in `tests/test_data_integrity.py`: `test_m1_display_forms_preserves_kanji_prefix` covers 食べる (v1), 行く (v5k-s), 高い (adj-i), 綺麗 (adj-na), and 大切 (adj-na, zero-common-suffix case) at minimum.
- **Determinism regression test** in `tests/test_data_integrity.py`: `test_stroke_order_characters_keys_are_sorted` asserts the characters keys in `stroke-order-index.json` are in sorted Unicode-codepoint order.

### Added (feature additions originally slated for v0.3.1-continued)

- **Jinmeiyō kanji view** (`data/core/kanji-jinmeiyo.json`): derived filter of `kanji.json` to grades 9 and 10 only — the kanji approved for personal-name use in Japan but not included in the Jōyō list. **863 entries**, matching the official 2017 MEXT jinmeiyō list count. Built by the kanji transform from the same source as the main kanji.json, using the exact same schema. Included in `build/validate.py` and `build/stats.py`.
- **Tatoeba sentence linkage for grammar examples**: the grammar transform now reads `data/corpus/sentences.json` and attempts exact-text matching between curated grammar example sentences and Tatoeba sentences. When a match exists, the grammar example's `source` is updated from `"original"` to `"tatoeba"` and a `sentence_id` is populated. Initial match rate is **1.7%** (3 of 180 examples), which is expected because the N5/N4 examples were written for pedagogical clarity rather than to reproduce corpus entries. The infrastructure is in place: future patches can add Tatoeba-sourced examples directly to `grammar-curated/` (they will pass through unchanged), or a fuzzy-matching pass can be added. The grammar metadata now includes a `tatoeba_linkage` summary with `total_examples`, `linked_examples`, `link_rate_pct`, and `method`.
- **`.github/workflows/build.yml`** — reproducibility smoke test CI workflow. Addresses the review's Reproducibility-dimension gap ("Missing: reproducibility smoke test in CI"). On every push to `main` and every pull request, the workflow performs a cold checkout, installs pinned dependencies, fetches upstream sources (SHA256-verified), runs the full build pipeline, validates every output against its schema, runs the test suite, and prints stats. Uses GitHub Actions cache for the `sources/` directory keyed on `manifest.json` hash to avoid re-downloading the 43 MB of upstream files on every run.
- **`just ci`** — local equivalent of the CI workflow: `just fetch && just build && just validate && just test && just stats`. Runs the same smoke test against the local checkout. Exits non-zero on any step failure.
- **Stroke-count mismatch metadata** on `data/enrichment/stroke-order-index.json`:
  - `metadata.warnings`: list of human-readable warnings, currently two: (1) the 109 stroke-count mismatches, (2) the 48.9% KanjiVG coverage.
  - `metadata.stroke_count_mismatches`: structured list of all 109 affected characters, each with the KANJIDIC2 canonical count and the KanjiVG path-element-count. Consumers joining kanji.json with stroke-order-index.json can now detect and handle these cases explicitly.

### Changed

- `build/transform/stroke_order.py`: emits the new `warnings` and `stroke_count_mismatches` metadata fields. Reads `data/core/kanji.json` when it exists to compute mismatches; gracefully falls back to empty lists when kanji.json is not yet built.
- `data/grammar/conjugations.json` regenerated with the B1 fix. The four v5r-i entries (事がある, である, でもある, 有る) now emit correct nai_form/nakatta_form with stem prefix preserved for compound entries.

### Not changed (deliberately)

- **Green-section observations** from the review (48.9% KanjiVG coverage, 109 stroke-count mismatches, 14 empty Waller jmdict_seq, 0.7% expression JLPT coverage, kana stroke-count caveat, single-maintainer upstream risk, names.json gitignored, committed weight, character schema kanji-range enforcement) — none were flagged as defects; no changes applied.

---

## [0.3.1] — 2026-04-11

Post-review defect fixes. This patch addresses every defect and stale-metadata issue flagged in the external review of the v0.3.0 release (D1–D5 and M1–M6 from the review notes). No new data sources or schemas are added; existing data is corrected where the review identified a wrong output.

### Fixed

- **D1**: `build/transform/conjugations.py` now handles the special-ending godan verb classes `v5k-s`, `v5u-s`, `v5aru`, and `v5r-i`. The previous version silently dropped all verbs in these classes, including `行く` (the canonical `v5k-s` verb), because `GODAN_POS_TO_ENDING` had no entry for these POS tags. The fix adds them to the map and applies per-POS overrides in `_conjugate_godan`:
  - `v5k-s`: te/ta forms use って/った instead of いて/いた (for 行く, 逝く, 往く)
  - `v5u-s`: te/ta forms use うて/うた instead of って/った (for 問う, 請う)
  - `v5aru`: i-stem and imperative use い instead of り (for いらっしゃる, ござる, なさる, おっしゃる)
  - `v5r-i`: nai/nakatta forms use the suppletive ない/なかった (for ある)
  - The previous dead `if stem == "行く" ...` check in `_conjugate_godan` has been removed; it is replaced by the POS-based handling which covers all v5k-s verbs, not just `行く`.
- **D2**: Broken `related` cross-references in the curated grammar data. `counter-tsu` referenced `counter-objects-ko` (which doesn't exist); removed. `potential-form` referenced `dekiru-potential` (which doesn't exist); removed. `build/transform/grammar.py` now validates that every `related` id resolves to an existing grammar entry and fails the build with a clear error if not.
- **D3**: Corrected the stale "6.6% JMdict ID drift" explanation in both `CHANGELOG.md` [0.2.0] and `docs/sources.md`. The ~6.6% of Waller JLPT vocab entries that don't appear in `data/core/words.json` are NOT due to JMdict ID drift (all 8,279 Waller seq IDs exist in the full JMdict); they are entries outside the common subset our `words.json` ships. They can be joined against `words-full.json` or they stand alone in `jlpt-classifications.json`.
- **D4**: Non-deterministic `jlpt_waller` assignment for words whose JMdict ID covers multiple homographic variants. When a single `jmdict_seq` appeared in multiple Waller level CSVs (e.g., 会う at N5 and 遭う at N2 sharing seq 1198180), the previous `_load_vocab_jlpt_map` in both `build/transform/words.py` and `build/transform/expressions.py` used the last-iterated level, which was deterministic (stable across runs) but semantically wrong. The fix: for duplicate `jmdict_seq`, the easier level wins (N5 > N4 > N3 > N2 > N1). Pedagogically, this reflects the level at which a learner first encounters the common form of the word. Documented in the `jlpt_waller` field_note on `words.json`.
- **D5**: `build/transform/cross_links.py` now detects and records characters in `kanji-to-words.json` that have no corresponding entry in `kanji.json`. The fix loads `kanji.json`, computes the set of orphan characters (words-side kanji that KANJIDIC2 does not index), logs a warning with the first 20 orphans, and writes `metadata.orphan_count` and `metadata.orphan_chars` to `kanji-to-words.json`. Consumers joining these two files can detect the integrity gap at read time instead of silently missing lookups.
- **M1**: Bumped `schemaVersion` from `"0.0.0"` to `"0.3.0"` in every schema that was still stale: `kana`, `kanji`, `word`, `name`, `radical`, `sentence`, `pitch-accent`, `frequency`, `jlpt`, `stroke-order`, `grammar`, `cross-refs` (12 files). `expressions.schema.json` and `conjugations.schema.json` were already at `0.3.0` and are unchanged.
- **M2**: `schemas/grammar.schema.json` description no longer claims the grammar dataset is derived from Tae Kim. The stale description was a Phase 0 scaffolding artifact that contradicted the Phase 3 authorship statement and could be read as a license-risk inconsistency. The description now correctly states that the data is hand-curated from general, non-copyrightable facts and explicitly NOT derived from Tae Kim or other copyrighted sources.
- **M3**: `docs/gaps.md` "Native-speaker reviewed grammar" section no longer claims Tae Kim is a source. Same correction as M2 but in the gaps doc.
- **M4**: `docs/phase4-candidates.md` JPDB entry status changed from "PROMOTED to Phase 4" to "DEFERRED (license-blocked)". Phase 4 is not active; "PROMOTED" was misleading.
- **M6**: `build/transform/radicals.py` now emits a `warning` field in `data/core/radicals.json` metadata, explicitly stating that every radical's `meanings` array is empty and `classical_number` is null because RADKFILE does not provide those fields and no CC-BY-SA-compatible upstream joining source is currently integrated.

### Added

- **T1** (test-coverage gap from review): new `tests/test_data_integrity.py` with 5 targeted regression tests corresponding to D1, D2, D4, and D5. Each test reads a built data file and verifies an invariant that would have caught the original defect. Tests gracefully skip if the file has not been built, preserving the ability to run `pytest tests/` on a fresh checkout.
  - `test_d1_conjugations_covers_iku`: verifies 行く has a conjugation table and the te/ta forms are いって/いった
  - `test_d1_conjugations_covers_v5aru_and_v5r_i`: verifies at least one v5aru and one v5r-i verb is emitted
  - `test_d2_grammar_related_references_resolve`: verifies every grammar `related` id resolves
  - `test_d4_words_jlpt_easier_level_wins`: verifies word 1198180 has `jlpt_waller=N5`
  - `test_d5_kanji_to_words_orphan_count_matches`: verifies `orphan_count` metadata matches reality

### Changed

- `data/grammar/conjugations.json` regenerated: entries with `v5k-s`, `v5u-s`, `v5aru`, `v5r-i` classes are now emitted where previously silently dropped. New entries cover 行く and other verbs in these classes.
- `data/core/words.json`, `data/core/kanji.json`, `data/core/kanji-joyo.json`, `data/core/words-full.json` regenerated with deterministic D4 JLPT join. For words with multi-level JLPT entries, `jlpt_waller` now reflects the easier level.
- `data/cross-refs/kanji-to-words.json` regenerated with new `orphan_count` and `orphan_chars` metadata fields.
- `data/core/radicals.json` regenerated with new `warning` metadata field.
- `data/enrichment/stroke-order-index.json`, `data/enrichment/jlpt-classifications.json`, etc. regenerated; content is unchanged except for the `generated` date.
- `grammar-curated/n5.json` — removed broken reference to `counter-objects-ko`.
- `grammar-curated/n4.json` — removed broken reference to `dekiru-potential`.

### Not changed (deliberately)

- **M5**: The review's M5 recommendation was a 15-minute middle-ground for the case where D1 was NOT fixed. Since D1 is fully fixed in this patch, adding a "known exclusions" note for v5k-s/v5aru/v5r-i/v5u-s would be misleading — they are no longer excluded.
- **M7**: The review noted this as "minor, not a bug" (a forward reference to a planned `stroke-order-metadata.json` in `docs/gaps.md`). No fix applied.
- **Observations (the green section of the review)**: 48.9% KanjiVG coverage, 109 stroke-count mismatches, 14 empty Waller jmdict_seq, 0.7% expression JLPT coverage, draft review_status, kana stroke-count caveat, single-maintainer upstream risk, `frequency-modern.json` placeholder, `names.json` gitignored — none of these were flagged as defects; no changes applied.

---

## [0.3.0] — 2026-04-11

Phase 3 — Grammar foundation. First tranche of original grammar content plus derived grammar datasets (expressions and conjugations). **This is the largest amount of original content in the project.** Everything in the grammar dataset is written in our own words based on general, non-copyrightable facts about Japanese grammar; nothing is copied from Tae Kim's Guide (CC-BY-NC-SA, license incompatible with our CC-BY-SA 4.0 output) or any other copyrighted source.

### Added

- **Curated grammar dataset** (`data/grammar/grammar.json`): **81 grammar points** hand-written from the project author's general knowledge of Japanese, following the grammar schema. All entries are flagged `review_status: "draft"` — the aspiration is `native_speaker_reviewed`, but the project does not yet have a native-speaker review pipeline. See `docs/contributing.md` for the call to reviewers.
  - **N5**: 50 entries covering copula (です/だ/でした/ではありません), polite verb forms (ます/ました/ません/ませんでした), particles (は, が, を, に, で, と, の, へ, から, まで, も, か, ね, よ, や), demonstratives (これ/それ/あれ, この/その/あの, ここ/そこ/あそこ), existence (あります/います), te-form basics (-て, -てください, -ています), -ない form, -た form, i-adjective and na-adjective conjugations, volitional (ましょう/ましょうか), desire (-たい, がほしい), comparison (のほうが...より, 一番), counters (~つ, ~人), question words, and -ないでください.
  - **N4**: 31 entries covering potential form, passive form, causative form, -たことがある (experience), つもり (intention), と思う (opinion), と言う (quotation), だろう/でしょう (conjecture), かもしれない (possibility), はず (expectation), four conditionals (たら, ば, と, なら), volitional form, -てはいけない (prohibition), -てもいい (permission), -なければならない (obligation), -なくてもいい (lack of obligation), から/ので (because), が/けど (although), んです (explanation), なる/する (change/decision), verb-stem auxiliaries (-始める, -終わる, -すぎる, -やすい, -にくい), and noun-modifying clauses.
- **JMdict expressions dataset** (`data/grammar/expressions.json`): **13,220 entries** — every JMdict entry with at least one sense tagged `exp` (expression). 436 of these are marked common. Each entry preserves its JMdict ID for cross-reference with `words.json`, plus all kanji writings, kana readings, English meanings of exp-tagged senses, and any Waller JLPT classification that matches by JMdict ID.
- **Auto-generated conjugation tables** (`data/grammar/conjugations.json`): **3,492 entries** covering every supported word class in `words.json` (common subset). Generated using formal conjugation rules encoded in `build/transform/conjugations.py` — no native-speaker review needed for the rules themselves (any incorrectness indicates a bug in the rule implementation). Breakdown:
  - v1 (ichidan): 555
  - v5k, v5s, v5u, v5r, v5m, v5t, v5g, v5b, v5n: 1,143 total across godan classes
  - vs-i (suru-verb compounds): 12
  - vk (くる): 1
  - adj-i: 312
  - adj-na: 1,469
  - Generates up to 16 forms per entry (dictionary, polite non-past/past/negative/past-negative, te-form, ta-form, nai-form, nakatta-form, potential, passive, causative, imperative, volitional, conditional_ba, conditional_tara).
- **Grammar JLPT classifications** integrated into `data/enrichment/jlpt-classifications.json`: 81 new entries with `kind: grammar`, bringing the total classification count from 10,504 → **10,585**. Each grammar classification includes a `grammar_id` field that joins with `data/grammar/grammar.json`.
- New schemas: `schemas/expressions.schema.json` and `schemas/conjugations.schema.json` (Draft 2020-12). Expected count: 14 → **14** (confirmed by tests).
- New transforms: `build/transform/grammar.py`, `build/transform/expressions.py`, `build/transform/conjugations.py`. The grammar transform reads from the committed `grammar-curated/` directory and validates every entry.
- New committed directory: **`grammar-curated/`** — our original hand-written grammar entries in JSON format, one file per JLPT level (`n5.json`, `n4.json`). These are the authoritative inputs to the grammar transform and are edited directly when adding/correcting grammar points.

### Changed

- `build/transform/jlpt.py` now also reads `grammar-curated/*.json` and emits `kind: grammar` classifications in addition to `kind: vocab` (from stephenmk) and `kind: kanji` (from davidluzgouveia). The JLPT metadata `counts_by_kind_and_level` now tracks grammar counts per level.
- `build/pipeline.py` adds three new stages (grammar, expressions, conjugations) as Phase 3 transforms, running after the cross-reference stage.
- `build/validate.py` SCHEMA_MAP extended with grammar.json, expressions.json, and conjugations.json.
- `build/stats.py` TARGET_FILES extended with the three new grammar files.
- `tests/test_schemas.py` guardrail test updated to expect 14 schema files (added expressions and conjugations).
- README status and manifest version/phase updated to Phase 3 / v0.3.0.

### Content provenance statement

**All grammar explanations in `grammar-curated/*.json` are written in our own words based on general, well-known, non-copyrightable facts about Japanese grammar.** We explicitly did NOT consult any of the following during writing, because their licenses are incompatible with our CC-BY-SA 4.0 output:

- **Tae Kim's Guide to Japanese** — CC-BY-NC-SA 3.0 (the NC clause is irreconcilable with our CC-BY-SA 4.0 output; incorporating any derivative would contaminate our license chain)
- **Dictionary of Basic/Intermediate/Advanced Japanese Grammar** (Seiichi Makino and Michio Tsutsui) — proprietary
- **Handbook of Japanese Grammar Patterns** — proprietary
- **Hanabira's grammar content** — license unclear

Sources referenced in grammar entries are cited as "General Japanese grammar knowledge" — this is honest: the factual content (which particles mark what, how verbs conjugate, what patterns mean) is well-known linguistic fact, not a derivative of any specific copyrighted work.

### Example sentence source

**All 200+ example sentences in grammar.json are marked `source: "original"`.** They are written by the project author to illustrate the pattern in its typical use. They are NOT linked to Tatoeba sentence IDs in this release. A future patch (v0.3.x) could add Tatoeba cross-references via text-match lookup against `data/corpus/sentences.json` for exact or near-exact matches.

### Data summary

| File | Phase 2 → Phase 3 |
|---|---|
| All Phase 1 and 2 files | unchanged |
| `data/enrichment/jlpt-classifications.json` | 10,504 → **10,585** (+81 grammar) |
| `data/grammar/grammar.json` | new — 81 entries |
| `data/grammar/expressions.json` | new — 13,220 entries |
| `data/grammar/conjugations.json` | new — 3,492 entries |

**Total rows (with derivatives and gitignored): 495,766** (up from 478,892 in v0.2.0).
**Unique committed entries: 277,457** (excludes `kanji-joyo.json` as a derived view of `kanji.json`, and `words-full.json` as a gitignored build artifact).

### Deliberate scope choices (with 15-minute middle-grounds applied)

- **Coverage limited to ~15% of total JLPT grammar** (N5 essentials + N4 selections, not complete N5+N4). **Middle-ground applied**: entries are tagged with explicit level metadata; `review_coverage` summary in metadata shows 81 draft entries; `docs/gaps.md` already documents the grammar coverage gap and the native-speaker review gap. Future patches can incrementally fill in N3, N2, N1.
- **All examples are original**, not linked to Tatoeba. **Middle-ground applied**: the schema allows `source: "tatoeba"` with a `sentence_id` field, and a future build step could text-match and populate it. For this release, we ship original examples with honest provenance.
- **No content from proprietary or NC-licensed sources**. **Middle-ground applied**: source field on each entry honestly says "General Japanese grammar knowledge" — it does not falsely cite sources we did not actually open.
- **Native-speaker review not available**. **Middle-ground applied**: every entry has `review_status: "draft"`; `docs/contributing.md` has a prominent call for native-speaker reviewers; the schema supports a progressive workflow (draft → community_reviewed → native_speaker_reviewed).

### Known limitations

- **Grammar correctness is the weakest verification point.** The project author (Claude) has broad knowledge of Japanese grammar but is not a native speaker or professional linguist. Subtle errors in nuance, formality, or rare usage are possible. This is why every entry starts as draft.
- **Conjugation generation covers ~3,500 entries**, which is the conjugable subset of the common-subset words.json (22,580 entries). Entries that are nouns, adverbs, or verbs with unusual conjugation patterns are skipped. The skipped count (34,396) includes multi-POS iterations, not 34k distinct skipped words.
- **ら-abbreviated ichidan potential forms** (食べれる for 食べられる, widely used in modern colloquial Japanese but grammatically nonstandard) are NOT generated; only the traditional form with ら is emitted. Documented in conjugations.json field notes.
- **Grammar JLPT classifications are community-consensus level assignments.** The level field on each grammar point was chosen by the project author based on which JLPT level typically tests the pattern, not from a definitive JLPT-official source (which doesn't exist — see the jlpt.schema.json disclaimer).
- **Expressions dataset includes 13,220 entries, ~30x the grammar point count**, because JMdict's `exp` tag covers everything from functional grammar (e.g., 〜てください) to set phrases (いらっしゃいませ) to idioms. The expressions and grammar datasets overlap in coverage but serve different purposes: grammar is compositional pedagogy; expressions is lexical lookup.

---

## [0.2.0] — 2026-04-11

Phase 2 — Enrichment and cross-references. All Phase 1 files are re-emitted with enrichment fields populated; six new enrichment and cross-reference files are added. Total committed data entries: 478,892 (up from 280,445 in v0.1.0).

### Added

- **Stroke order SVGs** (`data/enrichment/stroke-order/*.svg`): 6,416 individual SVG files from the KanjiVG `main` (non-variant) distribution r20250816. Files are named with the kanji character itself (e.g., `日.svg`). License: CC-BY-SA 3.0 Unported, upgraded to CC-BY-SA 4.0 in our CC-BY-SA 4.0 aggregate output per CC compatibility rules.
- **Stroke order index** (`data/enrichment/stroke-order-index.json`): 13,108 entries — one per kanji in our `kanji.json`. Each entry maps a character to its SVG filename (or null if no stroke order data exists upstream) and a stroke count derived from counting `<path>` elements in the SVG.
- **Pitch accent data** (`data/enrichment/pitch-accent.json`): 124,011 entries from Kanjium `accents.txt` (126 malformed upstream lines skipped). Each entry has the word, kana reading, pitch accent mora positions, and a derived mora count. Coverage date documented as approximately 2022 (Kanjium upstream is currently stale).
- **JLPT classifications** (`data/enrichment/jlpt-classifications.json`): 10,504 total classifications combining:
  - Vocabulary: 8,293 entries (N5=684, N4=640, N3=1,730, N2=1,812, N1=3,427) sourced from Jonathan Waller's JLPT Resources via `stephenmk/yomitan-jlpt-vocab` (CC-BY-SA 4.0). Each entry carries the JMdict sequence ID for clean join with `words.json`.
  - Kanji: 2,211 entries (N5=79, N4=166, N3=367, N2=367, N1=1,232) extracted from `davidluzgouveia/kanji-data` `jlpt_new` field only. WaniKani-derived fields deliberately ignored due to incompatible license.
  - Grammar: deferred to Phase 3 (schema supports `kind: grammar`).
- **Newspaper frequency rankings** (`data/enrichment/frequency-newspaper.json`): 2,501 ranked kanji extracted from KANJIDIC2 `misc.frequency` field. Represents a newspaper corpus from roughly the early 2000s. Modern media frequency (JPDB) is deferred to Phase 4.
- **Cross-reference indices** in `data/cross-refs/`:
  - `kanji-to-words.json` — 3,533 kanji characters mapped to the common-subset word IDs that contain them
  - `word-to-kanji.json` — 18,084 word IDs mapped to their component kanji characters
  - `word-to-sentences.json` — 14,550 word IDs mapped to their editor-curated Tatoeba sentence IDs
  - `kanji-to-radicals.json` — 12,156 kanji mapped to their component radicals from KRADFILE
- Six new upstream sources pinned in `build/fetch.py` with SHA256 verification:
  - `waller-jlpt-vocab-{n5,n4,n3,n2,n1}` — stephenmk CSV files for each level
  - `waller-jlpt-kanji` — davidluzgouveia kanji.json for kanji classifications
- Phase 2 transform implementations in `build/transform/`: `stroke_order.py`, `pitch.py`, `jlpt.py`, `frequency.py`, and `cross_links.py` replacing their Phase 0 stubs.

### Changed

- **Pipeline order reorganized** in `build/pipeline.py` so that independent transforms (kana, radicals, stroke_order, pitch, jlpt, frequency) run before main transforms (kanji, words, sentences) that consume their output. This enables kanji and words to read enrichment data during their build.
- `build/transform/kanji.py` now reads `data/enrichment/jlpt-classifications.json` and `data/core/radicals.json` if they exist, and populates `jlpt_waller` and `radical_components` fields per entry. Backward-compatible: if enrichment files are absent, those fields remain null/empty as in Phase 1. 2,211 kanji now have `jlpt_waller` populated (N5-N1 classifications), and 12,156 kanji have `radical_components` populated.
- `build/transform/words.py` now reads `data/enrichment/jlpt-classifications.json` and populates `jlpt_waller` via the JMdict sequence ID join. 7,208 common-subset words (out of 22,580) and 7,747 full-dataset words are now classified to an N5-N1 level. The remaining ~6.6% of Waller entries don't appear in `words.json` because they are not in the common subset (they reference valid JMdict IDs that the common filter excludes); all 8,279 Waller seq IDs exist in the full JMdict.
- `data/core/kanji.json`, `data/core/kanji-joyo.json`, `data/core/words.json` are updated in place with the newly-populated enrichment fields. `data/core/words-full.json` (gitignored) is similarly updated.
- README status updated to reflect Phase 2 completion.

### Data summary

| File | Entries | Notes |
|---|---:|---|
| `data/core/kana.json` | 215 | unchanged |
| `data/core/kanji.json` | 13,108 | enriched: 2,211 jlpt_waller, 12,156 radical_components |
| `data/core/kanji-joyo.json` | 2,136 | derived view, enriched |
| `data/core/words.json` | 22,580 | enriched: 7,208 jlpt_waller |
| `data/core/words-full.json` | 216,173 | gitignored; enriched: 7,747 jlpt_waller |
| `data/core/radicals.json` | 253 radicals + 12,156 mappings | unchanged |
| `data/corpus/sentences.json` | 25,980 | unchanged |
| `data/enrichment/stroke-order/*.svg` | 6,416 SVG files | new |
| `data/enrichment/stroke-order-index.json` | 13,108 | new |
| `data/enrichment/pitch-accent.json` | 124,011 | new |
| `data/enrichment/frequency-newspaper.json` | 2,501 | new |
| `data/enrichment/jlpt-classifications.json` | 10,504 | new |
| `data/cross-refs/kanji-to-words.json` | 3,533 | new |
| `data/cross-refs/word-to-kanji.json` | 18,084 | new |
| `data/cross-refs/word-to-sentences.json` | 14,550 | new |
| `data/cross-refs/kanji-to-radicals.json` | 12,156 | new |

**Total rows (with derivatives and gitignored): 478,892** (up from 280,445 in v0.1.0).
**Unique committed entries: 260,583** (excludes `kanji-joyo.json` as a derived view of `kanji.json`, and `words-full.json` as a gitignored build artifact). Plus 6,416 stroke-order SVG files.

### Deliberate deferrals (with 15-minute middle-grounds applied)

- **Modern media frequency (JPDB/Kuuuube)**: deferred to Phase 4. Both `MarvNC/jpdb-freq-list` and `Kuuuube/yomitan-dictionaries` lack explicit license files; the underlying JPDB.io corpus derives from copyrighted media. Documented as a Phase 4 candidate with license clarification required. Phase 2 ships only newspaper frequency, which is CC-BY-SA via EDRDG.
- **Grammar JLPT classifications**: the `jlpt-classifications.json` schema already supports `kind: grammar`; Phase 2 only populates `vocab` and `kanji` kinds. Grammar entries will be added in Phase 3 alongside the grammar dataset itself.
- **Radical meanings and Kangxi numbers**: RADKFILE does not provide these. The `radicals.json` file has empty `meanings` arrays and null `classical_number` fields. Joining from external sources (Wikipedia radical table, Unicode CJK Radical Supplement block) is a Phase 4 candidate.

### Known limitations

- **JLPT vocab coverage gap**: ~6.6% of Waller's JLPT vocab entries cannot be joined to `data/core/words.json` by ID — not because of JMdict ID drift (all Waller seq IDs DO exist in the full JMdict) but because those entries are outside the common subset that `words.json` ships. They can be joined against `words-full.json` (gitignored build artifact) or stand alone in `jlpt-classifications.json`.
- **Cross-references are scoped to the common-subset words**: `kanji-to-words.json` and `word-to-kanji.json` reference the common-subset word IDs in `words.json`. Consumers wanting full 216k cross-references should re-run the pipeline against `words-full.json`.
- **Stroke order count may differ from KANJIDIC2**: we derive stroke counts by counting SVG path elements in KanjiVG, which can differ by ±1 from KANJIDIC2 in edge cases (e.g., how a cross-stroke is counted). Consumers should prefer KANJIDIC2's `stroke_count` in `kanji.json` as the canonical count.
- **Pitch accent data is ~2022 vintage** (upstream Kanjium is currently stale). Vocabulary added to Japanese after 2022 lacks pitch accent entries. Documented in `docs/gaps.md` and `pitch-accent.json` metadata.

---

## [0.1.0] — 2026-04-11

Phase 1 — Core data foundation. First release that produces actual data files.

### Added

- **Kana dataset** (`data/core/kana.json`): 215 hand-curated entries covering basic hiragana/katakana, dakuten, handakuten, yōon combinations, sokuon, archaic kana, and the long-vowel mark. Includes stroke counts for base forms, Unicode codepoints, Hepburn and Kunrei-shiki romanizations, type classifications, and usage notes for non-obvious entries.
- **Kanji dataset** (`data/core/kanji.json`): 13,108 kanji characters from KANJIDIC2 (full character set, ingested via `scriptin/jmdict-simplified` 3.6.2). Each entry includes readings (on/kun in Japanese; pinyin/Korean/Vietnamese for cross-linguistic reference), multilingual meanings (en/fr/es/pt), stroke count, grade, JLPT (old system), frequency, radicals, nanori, variants, dictionary references (Heisig, Nelson, Halpern, Morohashi, etc.), and query codes (SKIP, Four Corner, Spahn/Hadamitzky, De Roo).
- **Jōyō kanji view** (`data/core/kanji-joyo.json`): Derived filter of `kanji.json` containing exactly 2,136 characters — the official 2010 MEXT Jōyō list (kyōiku grades 1-6 + secondary grade 8).
- **Words dataset — common subset** (`data/core/words.json`): 22,580 common JMdict entries (from jmdict-examples-eng 3.6.2). Includes every entry with at least one kanji or kana writing flagged as common in JMdict's news1/ichi1/spec1/gai1 priority markers. Each entry carries full JMdict sense structure plus editor-curated example sentence links to Tatoeba.
- **Words dataset — full** (`data/core/words-full.json`, gitignored): 216,173 entries. Built on demand via `just build`; gitignored because it exceeds typical git file size thresholds. Intended for release-artifact distribution.
- **Radicals dataset** (`data/core/radicals.json`): Bidirectional view combining KRADFILE (12,156 kanji → component radicals) and RADKFILE (253 radicals → kanji containing them).
- **Sentences dataset** (`data/corpus/sentences.json`): 25,980 unique example sentences (Japanese + English pairs) extracted from the editor-curated Tatoeba sentences embedded in jmdict-examples-eng. Deduplicated by Tatoeba sentence ID.
- `build/fetch.py`: Pinned fetcher with SHA256 verification for all 7 upstream source files.
- Phase 1 implementations of `build/transform/{kanji,words,sentences,radicals,kana}.py`.
- Schema fix: `kana.schema.json` now allows null `stroke_count` for yōon compound forms, which do not have a single canonical stroke count.
- Schema fix: `word.schema.json` `examples` items now have explicit required fields (`source`, `sentence_id`) and clearer field names (`word_form`, `japanese`, `english`).
- `data/core/kanji-joyo.json` and `data/core/words-full.json` added to `build/validate.py` SCHEMA_MAP and `build/stats.py` TARGET_FILES.
- `.gitignore`: `data/core/words-full.json` excluded (gitignored build artifact).
- Logged schema gaps (pitch accent `skipMisclassification` field, Morohashi volume/page) in `docs/upstream-issues.md`.
- Upstream source addition: `kanjidic2-all.json.tgz` (13,108 characters, all-language meanings) replacing `kanjidic2-en.json.tgz` (10,383 characters, English only). Net gain: 2,725 additional characters covered.

### Changed

- Bumped `manifest.json` version from `0.0.0` to `0.1.0` and phase from 0 to 1.
- README status line updated to reflect Phase 1 completion.
- `manifest.json` `sources` now contains verified SHA256 hashes for all 7 upstream pinned files.

### Data summary

Total rows across all Phase 1 files: **280,445**.
Unique committed entries: **62,136** (excludes `kanji-joyo.json` as a derived view of `kanji.json`, and `words-full.json` as a gitignored build artifact).

- kana.json: 215 entries
- kanji.json: 13,108 entries (15.6 MB)
- kanji-joyo.json: 2,136 entries (3.5 MB)
- words.json: 22,580 common entries (44.4 MB)
- radicals.json: 253 radical entries + 12,156 kanji-component mappings (1.8 MB)
- sentences.json: 25,980 unique sentences (8.9 MB)

Total committed data: ~74 MB.
Total uncommitted build artifact (words-full.json): ~285 MB.

### Known gaps (deliberate, to be addressed in later phases)

- Phase 2 (enrichment: stroke order, pitch accent, frequency, JLPT, cross-linking) is not yet implemented. The `jlpt_waller` and `frequency_media` fields on word entries are null; `radical_components` on kanji entries is an empty array.
- Phase 3 (grammar curation) is not yet implemented.
- Phase 4 candidates (classical handwriting, modern handwriting, Aozora Bunko texts, speech corpora, Wiktionary extraction, jinmeiyō-specific view) are deferred; see `docs/phase4-candidates.md`.

---

## [0.0.0] — 2026-04-11

Phase 0 foundation: scaffolding, documentation, schemas, and build pipeline skeleton. No data files built.

### Added

- Repository scaffolding, documentation, schemas, and build pipeline skeleton.
- Project README, LICENSE with full EDRDG and upstream license obligations, ATTRIBUTION.md with per-source credits.
- Architecture documentation (`docs/architecture.md`) describing data layout, pipeline, versioning, and design principles.
- Source documentation (`docs/sources.md`) cataloging every upstream source with pinned URL, version, format, license, and expected transformations.
- Gap documentation (`docs/gaps.md`) explicitly naming what this dataset does not cover and why.
- Phase 4 candidate documentation (`docs/phase4-candidates.md`) cataloging future extension candidates.
- Contributing guide (`docs/contributing.md`) including the call-out for native-speaker grammar reviewers.
- Build guide (`docs/build.md`) describing the fetch → transform → validate → stats pipeline.
- Schema overview (`docs/schema.md`) explaining the schema design philosophy.
- Initial JSON Schema skeletons for every planned data file under `schemas/`.
- Build pipeline skeleton (`build/`) with `fetch.py`, `pipeline.py`, `validate.py`, `stats.py`, and transform module stubs for every data type.
- `justfile` with recipes for `fetch`, `build`, `validate`, `stats`, `clean`, and `test`.
- `manifest.json` tracking repo and upstream source versions.
- `.gitignore` and `.gitattributes` configured for the expected file types.
- Tests directory skeleton with 37 schema validation tests (all passing).

---

## Versioning policy

- **Every upstream rebuild** produces at minimum a patch release, with updated `manifest.json` source pins and a corresponding changelog entry.
- **Monthly rebuilds** are committed to, in accordance with EDRDG License §4 obligations. A release is tagged even if no substantive schema or content changes occurred, to demonstrate currency.
- **Schema-breaking changes** trigger a major version bump. Downstream consumers can pin to a specific major version for stability.
- **New data domains or new fields** trigger a minor version bump and are called out in this changelog.

Pre-1.0.0 versions (0.x.x) indicate that the dataset is still in active scaffolding and may undergo schema changes without a major version bump. Once the Phase 1–3 core is stable and schema-validated, v1.0.0 will be tagged.
