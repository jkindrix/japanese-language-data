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

**Target**: `data/core/radicals.json` `meanings` and `classical_number` fields. Wikipedia directly supplies 197 of 253 radicals (77.9%); from v0.7.1, a curated variant-to-Kangxi alias table in `build/transform/radicals.py` (`KANGXI_ALIASES`) bridges an additional 45 Japanese-dictionary-specific variants (shinjitai, radical-in-compound forms, positional markers) to their Wikipedia-sourced Kangxi parents, bringing total coverage to 242 of 253 (95.7%). The 11 remaining unmatched radicals are ambiguous Nelson-style variants deliberately left unmatched rather than assigned arbitrary Kangxi parents.

**Required attribution wording**:

> Kangxi radical English meanings and Kangxi numbers in this dataset are derived from the Wikipedia article "Kangxi radicals" (https://en.wikipedia.org/wiki/Kangxi_radicals, revision 1346511063), authored by Wikipedia contributors and licensed under CC-BY-SA 4.0. See the article's revision history for per-contribution attribution.

### JPDB frequency list (license-blocked — not currently distributed)

**Copyright holder**: MarvNC and contributors; underlying corpus analysis by jpdb.io.

**License**: No explicit license declared. Integration deferred pending license clarification. See `docs/phase4-candidates.md`.

**Project page**: https://github.com/MarvNC/jpdb-freq-list

### OpenSubtitles word frequency via FrequencyWords

**Copyright holder**: Hermit Dave (FrequencyWords tool); OpenSubtitles (underlying corpus).

**License**: CC-BY-SA 4.0 (FrequencyWords content); MIT (FrequencyWords code). The upstream README specifies "MIT License for code. CC-by-sa-4.0 for content."

**Project page**: https://github.com/hermitdave/FrequencyWords

**What we extract**: Japanese word frequency counts from the OpenSubtitles 2018 corpus, matched against JMdict vocabulary. 8,598 vocabulary-matched entries covering spoken/media Japanese (movies, TV, anime subtitles).

**Target**: `data/enrichment/frequency-subtitles.json`

**Required attribution wording**:

> Word frequency data from FrequencyWords by Hermit Dave (https://github.com/hermitdave/FrequencyWords, CC-BY-SA 4.0), derived from the OpenSubtitles parallel corpus (https://www.opensubtitles.org/).

### JmdictFurigana

**Copyright holder**: Doublevil and contributors.

**License**: CC-BY-SA 4.0 (derived from JMdict, EDRDG License).

**Project page**: https://github.com/Doublevil/JmdictFurigana

**What we extract**: Per-character reading alignment (furigana) for 28,920 JMdict entries. Maps kanji within compound words to their individual readings, enabling ruby text rendering.

**Target**: `data/enrichment/furigana.json`

**Required attribution wording**:

> Furigana alignment data from JmdictFurigana by Doublevil (https://github.com/Doublevil/JmdictFurigana), distributed under CC-BY-SA 4.0 (derived from JMdict).

### KFTT (Kyoto Free Translation Task)

**Copyright holder**: Graham Neubig and the NAIST/NICT bilingual corpus team.

**License**: CC-BY-SA 3.0.

**Project page**: https://www.phontron.com/kftt/

**What we extract**: 443,849 Japanese-English parallel sentence pairs from Wikipedia Kyoto articles. Machine-aligned, not editor-curated.

**Target**: `data/corpus/sentences-kftt.json` (gitignored due to size)

**Required attribution wording**:

> Parallel sentences from the Kyoto Free Translation Task (KFTT) (https://www.phontron.com/kftt/), derived from NICT's Japanese-English Bilingual Corpus of Wikipedia's Kyoto Articles, licensed under CC-BY-SA 3.0.

### Leeds University Internet Japanese Word Frequency List

Web-corpus word frequency data from the Leeds University Centre for Translation Studies.

**Author**: Serge Sharoff.

**License**: Creative Commons Attribution (CC-BY).

**Citation**: Sharoff, S. (2006) "Creating general-purpose corpora using automated search engine queries." In M. Baroni and S. Bernardini (eds.) *WaCky! Working papers on the Web as Corpus*, Gedit, Bologna.

**Original URL**: http://corpus.leeds.ac.uk/frqc/internet-jp.num (server offline; pinned via Wayback Machine).

**Required attribution wording**:

> Web-corpus word frequency data from the Leeds University Internet Japanese Word Frequency List, compiled by Serge Sharoff, CC-BY. See http://corpus.leeds.ac.uk/

### Japanese Wiktionary pitch accent data

Pitch accent data extracted from the Japanese-edition Wiktionary (ja.wiktionary.org) via the kaikki.org/wiktextract pre-processed JSONL.

**Source**: Wikimedia Foundation contributors to ja.wiktionary.org, extracted by wiktextract (Tatu Ylonen).

**License**: Creative Commons Attribution-ShareAlike 4.0 International (CC-BY-SA 4.0).

**URLs**: https://kaikki.org/dictionary/downloads/ja/ (extraction), https://ja.wiktionary.org/ (source)

**Required attribution wording**:

> Pitch accent data from Japanese Wiktionary (ja.wiktionary.org), extracted via wiktextract (https://github.com/tatuylonen/wiktextract). Content is CC-BY-SA 4.0 per Wikimedia Foundation terms.

### Aozora Bunko

**Copyright holder**: Individual authors (works in public domain); Aozora Bunko (digitization).

**License**: Public domain (著作権なし — copyright expired). Aozora Bunko's digitization work requests attribution per their usage guidelines.

**Project page**: https://www.aozora.gr.jp/

**What we extract**: Curated literary corpus from public-domain Japanese literary works for frequency analysis and reading practice.

**Required attribution wording**:

> Literary corpus data from Aozora Bunko (https://www.aozora.gr.jp/), a digital library of Japanese public-domain works.

### Wikipedia Kangxi radicals

**Copyright holder**: Wikimedia Foundation contributors.

**License**: CC-BY-SA 4.0.

**Project page**: https://en.wikipedia.org/wiki/Kangxi_radical

**What we extract**: English meanings and Kangxi radical numbers used to annotate RADKFILE radical entries. 242 of 253 RADKFILE radicals mapped to Kangxi equivalents via this source.

**Required attribution wording**:

> Kangxi radical English meanings from Wikipedia (https://en.wikipedia.org/wiki/Kangxi_radical), CC-BY-SA 4.0.

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
> - Spoken-media word frequency from FrequencyWords/OpenSubtitles, CC-BY-SA 4.0;
>   see https://github.com/hermitdave/FrequencyWords
> - Furigana alignment from JmdictFurigana by Doublevil, CC-BY-SA 4.0;
>   see https://github.com/Doublevil/JmdictFurigana
> - KFTT parallel corpus by Neubig et al., CC-BY-SA 3.0;
>   see https://www.phontron.com/kftt/
> - Web-corpus word frequency from Leeds University, CC-BY;
>   see http://corpus.leeds.ac.uk/
> - Pitch accent supplement from Japanese Wiktionary via wiktextract, CC-BY-SA 4.0;
>   see https://ja.wiktionary.org/
> - JESC (Japanese-English Subtitle Corpus) by Pryzant et al., CC-BY-SA 4.0;
>   see https://nlp.stanford.edu/projects/jesc/
> - WikiMatrix parallel sentences from OPUS, CC-BY-SA 4.0;
>   see https://opus.nlpl.eu/WikiMatrix.php
> - Japanese WordNet (wn-ja) v1.1 by NICT, permissive license;
>   see https://bond-lab.github.io/wnja/
> - Kangxi radical data from Wikipedia, CC-BY-SA 4.0;
>   see https://en.wikipedia.org/wiki/Kangxi_radical
> - Aozora Bunko literary works (public domain);
>   see https://www.aozora.gr.jp/
> - JSON distribution tooling from scriptin/jmdict-simplified;
>   see https://github.com/scriptin/jmdict-simplified
>
> Per the EDRDG license, web-facing applications using this data must update
> the underlying data at least once per month.
