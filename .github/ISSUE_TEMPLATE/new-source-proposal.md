---
name: New source proposal
about: Propose a new upstream data source or Phase 4 candidate
title: "[source proposal] "
labels: phase4, source-proposal
assignees: ''
---

## Source overview

- **Name:**
- **Maintainer / org:**
- **URL:**
- **License:** (include a link to the license text)
- **Scale:** (rows, bytes, coverage)
- **Format:** (JSON, CSV, XML, SQLite, wikitext, …)

## License compatibility

The project's output is CC-BY-SA 4.0. A new source must be compatible — that means one of:
- [ ] CC-BY (any version)
- [ ] CC-BY-SA (any version)
- [ ] CC0 / public domain
- [ ] EDRDG License (via scriptin/jmdict-simplified)
- [ ] Other CC-BY-SA 4.0 compatible license: (specify)

**Incompatible** (please do not propose): CC-BY-NC, CC-BY-ND, anything with NC or ND, or license-unclear.

## Why this source?

What gap does it close? How does it advance the project's stated goals (definitive / comprehensive / modern / complete Japanese learning data)?

## Effort estimate

- [ ] Low (drop-in: existing parser handles the format, no pipeline changes)
- [ ] Medium (new transformer module, new schema, some testing)
- [ ] High (new storage model, license audit, multi-file processing)

Describe any specifics:

## Cross-linking

How would this source cross-link with existing data (kanji, words, radicals, sentences, grammar, pitch accent, frequency, JLPT)?

## Upstream contribution

If the source has gaps or errors, would we be able to file them back upstream? (Project Design Principle 6.)

## Maintenance

Is the upstream source actively maintained? How often do we expect to bump the pinned version?

## Related documents

See `docs/phase4-candidates.md` for the existing candidate list and evaluation framework. New candidates follow the same rubric.
