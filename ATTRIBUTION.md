# Attribution

This dataset aggregates, transforms, and cross-links data from several upstream sources. Every source is acknowledged here in the wording its license requires or prefers. Downstream users of this dataset must carry these attributions forward in accordance with CC-BY-SA 4.0 and the upstream licenses.

For the full legal text of each license, see `LICENSE`.

---

## Primary data sources

### JMdict, JMnedict, KANJIDIC2, KRADFILE, RADKFILE

**Copyright holder**: James William Breen and The Electronic Dictionary Research and Development Group (EDRDG).

**License**: Creative Commons Attribution-ShareAlike 4.0 International, with additional obligations specified in the EDRDG General Dictionary Licence Statement.

**Project pages (required to link)**:
- https://www.edrdg.org/wiki/index.php/JMdict-EDICT_Dictionary_Project
- https://www.edrdg.org/wiki/index.php/KANJIDIC_Project
- https://www.edrdg.org/edrdg/licence.html

**Required attribution wording** (adapt as appropriate for the medium):

> This work uses the JMdict, JMnedict, KANJIDIC2, KRADFILE, and RADKFILE files. These files are the property of the Electronic Dictionary Research and Development Group, and are used in conformance with the Group's license. See https://www.edrdg.org/edrdg/licence.html for license details.

**Ingestion**: We ingest the EDRDG files via `scriptin/jmdict-simplified`, which provides a JSON transformation of the original XML. Direct credit to scriptin is listed below.

**Update obligation**: Per EDRDG License §4, web-facing dictionary applications using this data must update at least once per month. This repository itself commits to monthly upstream rebuilds.

### KANJIDIC2 per-field contributors (EDRDG License §8)

Certain fields within KANJIDIC2 are held under individual copyright by named contributors. Where this dataset includes any of these fields, the individual contributor must be credited:

| Field | Contributor(s) | Notes |
|---|---|---|
| SKIP codes | Jack Halpern | Under Halpern's own similar Creative Commons license. See his conditions of use. |
| Pinyin readings | Christian Wittern and Koichi Yasuoka | |
| Four Corner codes | Urs App | |
| Morohashi index | Urs App | |
| Spahn/Hadamitzky descriptors | Mark Spahn and Wolfgang Hadamitzky | |
| Korean readings | Charles Muller | |
| De Roo codes | Joseph De Roo | |

These contributors have granted permission for inclusion under the broader EDRDG license while retaining copyright over their specific contributions.

### KanjiVG

**Copyright holder**: Ulrich Apel and KanjiVG contributors.

**License**: Creative Commons Attribution-ShareAlike 3.0 Unported. Compatible with CC-BY-SA 4.0 for use in ShareAlike derivatives under the CC upgrade compatibility rule.

**Project page**: https://kanjivg.tagaini.net/

**Required attribution wording**:

> Stroke order data (kanji vector graphics) from the KanjiVG project, by Ulrich Apel and contributors, released under CC-BY-SA 3.0. See https://kanjivg.tagaini.net/

### Tatoeba

**Copyright holder**: Tatoeba and individual sentence contributors.

**License**: Creative Commons Attribution 2.0 France (CC-BY 2.0 FR); a subset is additionally released under CC0 1.0.

**Project page**: https://tatoeba.org/

**Required attribution wording**:

> Example sentences from the Tatoeba Project (https://tatoeba.org/) under CC-BY 2.0 FR. Individual sentences may have different contributors; sentence IDs are preserved in this dataset to enable upstream lookup.

### Kanjium

**Copyright holder**: mifunetoshiro and Kanjium contributors.

**License**: Creative Commons Attribution-ShareAlike 4.0 International.

**Project page**: https://github.com/mifunetoshiro/kanjium

**Specific file used**: `data/source_files/raw/accents.txt`

**Required attribution wording**:

> Pitch accent data from the Kanjium project by mifunetoshiro and contributors, released under CC-BY-SA 4.0. See https://github.com/mifunetoshiro/kanjium

### Jonathan Waller's JLPT Resources

**Copyright holder**: Jonathan Waller.

**License**: Creative Commons Attribution (CC-BY). Commercial use and redistribution explicitly permitted.

**Project page**: http://www.tanos.co.uk/jlpt/

**Sharing page**: http://www.tanos.co.uk/jlpt/sharing/

**Required attribution wording**:

> JLPT classifications adapted from Jonathan Waller's JLPT Resources at http://www.tanos.co.uk/jlpt/, used under CC-BY.

### Wikipedia: "Kangxi radicals" article

**Copyright holder**: Wikipedia contributors.

**License**: Creative Commons Attribution-ShareAlike 4.0 International (CC-BY-SA 4.0).

**Project page**: https://en.wikipedia.org/wiki/Kangxi_radicals

**Pinned revision**: 1346511063 — permanent URL https://en.wikipedia.org/w/index.php?title=Kangxi_radicals&oldid=1346511063

**What we extract**: The English meaning (from the "Meaning" column) and the Kangxi radical number (1–214) for each of the 214 classical radicals, plus the alternate form characters listed for each radical (e.g., 亻 and 𠆢 listed under 人, radical 9). We deliberately do NOT use the Wikipedia stroke count column — RADKFILE is the authoritative source for stroke counts in our dataset and using two sources risks divergence.

**Target**: `data/core/radicals.json` `meanings` and `classical_number` fields. 197 of 253 radicals (77.9%) are populated via this source. The remaining 56 are Japanese-dictionary-specific variants that have no direct Kangxi table match.

**Required attribution wording**:

> Kangxi radical English meanings and Kangxi numbers in this dataset are derived from the Wikipedia article "Kangxi radicals" (https://en.wikipedia.org/wiki/Kangxi_radicals, revision 1346511063), authored by Wikipedia contributors and licensed under CC-BY-SA 4.0. See the article's revision history for per-contribution attribution.

### JPDB frequency list

**Copyright holder**: MarvNC and contributors; underlying corpus analysis by jpdb.io.

**License**: See per-release metadata in `docs/sources.md` for current pinning.

**Project page**: https://github.com/MarvNC/jpdb-freq-list

**Required attribution wording**:

> Modern media frequency rankings from the JPDB frequency list (https://github.com/MarvNC/jpdb-freq-list), derived from jpdb.io's corpus analysis of light novels, visual novels, anime, and drama.

---

## Tooling and intermediate transformations

### scriptin/jmdict-simplified

We ingest JMdict, JMnedict, KANJIDIC2, KRADFILE, and RADKFILE via the pre-parsed JSON distributions produced by `scriptin/jmdict-simplified`. The source code is CC-BY-SA 4.0; the underlying data carries EDRDG licensing (see above).

**Project page**: https://github.com/scriptin/jmdict-simplified

**Required attribution wording** (in addition to EDRDG above):

> JMdict, JMnedict, KANJIDIC2, KRADFILE, and RADKFILE data ingested via scriptin/jmdict-simplified (https://github.com/scriptin/jmdict-simplified), which provides a JSON transformation of the EDRDG source files.

---

## This dataset itself

**Copyright holder**: Justin Kindrix and contributors.

**License**: Creative Commons Attribution-ShareAlike 4.0 International.

**Required attribution wording**:

> Data from the Japanese Language Data project (https://github.com/jkindrix/japanese-language-data), released under CC-BY-SA 4.0.

**Recommended composite attribution** (for applications using this dataset): Include all of the following in your About/Credits screen or equivalent:

> This application uses data from the Japanese Language Data project
> (https://github.com/jkindrix/japanese-language-data), CC-BY-SA 4.0, which
> aggregates content from:
>
> - JMdict, JMnedict, KANJIDIC2, KRADFILE, and RADKFILE from the Electronic
>   Dictionary Research and Development Group (EDRDG), used under the EDRDG
>   license; see https://www.edrdg.org/edrdg/licence.html and
>   https://www.edrdg.org/wiki/index.php/JMdict-EDICT_Dictionary_Project
> - KanjiVG stroke order data by Ulrich Apel and contributors, CC-BY-SA 3.0;
>   see https://kanjivg.tagaini.net/
> - Example sentences from the Tatoeba Project, CC-BY 2.0 FR;
>   see https://tatoeba.org/
> - Kanjium pitch accent data by mifunetoshiro and contributors, CC-BY-SA 4.0;
>   see https://github.com/mifunetoshiro/kanjium
> - JLPT classifications adapted from Jonathan Waller's JLPT Resources, CC-BY;
>   see http://www.tanos.co.uk/jlpt/
> - Modern media frequency from the JPDB frequency list, see
>   https://github.com/MarvNC/jpdb-freq-list
> - JSON distribution tooling from scriptin/jmdict-simplified;
>   see https://github.com/scriptin/jmdict-simplified
>
> Per the EDRDG license, web-facing applications using this data must update
> the underlying data at least once per month.
