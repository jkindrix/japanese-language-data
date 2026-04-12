# Cookbook

This project produces static JSON files, not an API. The examples below show common patterns for loading and querying the data in Python, JavaScript/Node.js, and from the command line with `jq`.

All paths are relative to the repository root.

---

## Python

### Load kanji and look up an entry

```python
import json

with open("data/core/kanji.json") as f:
    kanji_data = json.load(f)

kanji_by_char = {k["character"]: k for k in kanji_data["kanji"]}

entry = kanji_by_char["食"]
print(entry["stroke_count"])        # 9
print(entry["jlpt_waller"])         # "N4"
print(entry["meanings"]["en"])      # ["eat", "food"]
print(entry["readings"]["kun"])     # ["く.う", "く.らう", "た.べる", "は.む"]
```

### Cross-reference: given a kanji, find all words containing it with their JLPT level

```python
import json

with open("data/cross-refs/kanji-to-words.json") as f:
    k2w = json.load(f)

with open("data/core/words.json") as f:
    words_data = json.load(f)

words_by_id = {w["id"]: w for w in words_data["words"]}

word_ids = k2w["mapping"].get("食", [])
for wid in word_ids:
    word = words_by_id[wid]
    text = word["kanji"][0]["text"] if word["kanji"] else word["kana"][0]["text"]
    level = word["jlpt_waller"]
    gloss = word["sense"][0]["gloss"][0]["text"]
    print(f"{text} ({level}): {gloss}")
```

### Find all N3 grammar patterns

```python
import json

with open("data/grammar/grammar.json") as f:
    grammar_data = json.load(f)

n3 = [g for g in grammar_data["grammar_points"] if g["level"] == "N3"]
for g in n3:
    print(f"{g['pattern']}  —  {g['meaning_en']}")

print(f"\n{len(n3)} N3 grammar points")
```

### Filter: all N5 kanji with stroke counts

```python
import json

with open("data/core/kanji.json") as f:
    kanji_data = json.load(f)

n5 = [k for k in kanji_data["kanji"] if k["jlpt_waller"] == "N5"]
n5.sort(key=lambda k: k["stroke_count"])

for k in n5:
    print(f"{k['character']}  {k['stroke_count']} strokes")

print(f"\n{len(n5)} N5 kanji")
```

---

## JavaScript / Node.js

### Load kanji and look up an entry

```javascript
import { readFileSync } from "fs";

const kanjiData = JSON.parse(readFileSync("data/core/kanji.json", "utf-8"));
const kanjiByChar = Object.fromEntries(
  kanjiData.kanji.map((k) => [k.character, k])
);

const entry = kanjiByChar["食"];
console.log(entry.stroke_count);       // 9
console.log(entry.jlpt_waller);        // "N4"
console.log(entry.meanings.en);        // ["eat", "food"]
```

### Cross-reference: given a kanji, find all words containing it with their JLPT level

```javascript
import { readFileSync } from "fs";

const k2w = JSON.parse(readFileSync("data/cross-refs/kanji-to-words.json", "utf-8"));
const wordsData = JSON.parse(readFileSync("data/core/words.json", "utf-8"));
const wordsById = Object.fromEntries(
  wordsData.words.map((w) => [w.id, w])
);

const wordIds = k2w.mapping["食"] || [];
for (const wid of wordIds) {
  const word = wordsById[wid];
  const text = word.kanji.length ? word.kanji[0].text : word.kana[0].text;
  const level = word.jlpt_waller;
  const gloss = word.sense[0].gloss[0].text;
  console.log(`${text} (${level}): ${gloss}`);
}
```

### Find all N3 grammar patterns

```javascript
import { readFileSync } from "fs";

const grammarData = JSON.parse(
  readFileSync("data/grammar/grammar.json", "utf-8")
);
const n3 = grammarData.grammar_points.filter((g) => g.level === "N3");

for (const g of n3) {
  console.log(`${g.pattern}  —  ${g.meaning_en}`);
}
console.log(`\n${n3.length} N3 grammar points`);
```

---

## jq (command line)

### All N5 kanji with stroke counts

```bash
jq -r '.kanji[] | select(.jlpt_waller == "N5") | "\(.character)  \(.stroke_count) strokes"' \
  data/core/kanji.json
```

### All N3 grammar patterns

```bash
jq -r '.grammar_points[] | select(.level == "N3") | "\(.pattern)  —  \(.meaning_en)"' \
  data/grammar/grammar.json
```

### Words containing a specific kanji, with JLPT level

This requires two files. First extract the word IDs from the cross-ref, then look them up:

```bash
# Get word IDs for 食
jq -r '.mapping["食"][]' data/cross-refs/kanji-to-words.json > /tmp/word_ids.txt

# Look up each word
jq -r --slurpfile ids <(jq -R . /tmp/word_ids.txt) \
  '[.words[] | select(.id as $id | $ids | index($id))] |
   .[] | "\(.kanji[0].text // .kana[0].text)  \(.jlpt_waller // "—")  \(.sense[0].gloss[0].text)"' \
  data/core/words.json
```

### Count entries per JLPT level in the grammar dataset

```bash
jq -r '[.grammar_points[].level] | group_by(.) | map({level: .[0], count: length}) | .[]' \
  data/grammar/grammar.json
```

---

## Working with large files

The committed `data/core/words.json` (22,580 common entries, ~45 MB) loads comfortably in any language. The full `data/core/words-full.json` (216,173 entries, ~285 MB) requires more care.

### Prefer the common subset

Unless you specifically need rare, archaic, or specialized vocabulary, use `words.json` (the common subset). It contains every entry whose kanji or kana writings carry JMdict priority markers (`news1`, `ichi1`, `spec1`, `spec2`, `gai1`) — this covers the vocabulary a learner or general-purpose app needs.

### Memory estimates

| File | Entries | Disk | In-memory (Python dict) |
|---|---:|---:|---:|
| `words.json` | 22,580 | ~45 MB | ~120 MB |
| `words-full.json` | 216,173 | ~285 MB | ~800 MB |
| `kanji.json` | 13,108 | ~17 MB | ~60 MB |
| `pitch-accent.json` | 124,011 | ~17 MB | ~80 MB |

### Lazy loading with cross-references

Load cross-reference files first (they're small), then load entries on demand:

```python
import json

# Cross-refs are small — load fully
with open("data/cross-refs/kanji-to-words.json") as f:
    k2w = json.load(f)["mapping"]

# Load words index once
with open("data/core/words.json") as f:
    words_by_id = {w["id"]: w for w in json.load(f)["words"]}

# Look up on demand
def words_for_kanji(kanji_char: str) -> list[dict]:
    return [words_by_id[wid] for wid in k2w.get(kanji_char, [])
            if wid in words_by_id]
```

### Faster JSON parsing

Python's built-in `json` module is adequate for most files. For `words-full.json` or batch processing, consider:

- **`orjson`** (pip install orjson): 3–5x faster parsing, returns `bytes` instead of `str`.
- **`ijson`** (pip install ijson): Streaming parser — process entries one at a time without loading the full file.

```python
# Streaming with ijson (words-full.json without loading 800 MB)
import ijson

with open("data/core/words-full.json", "rb") as f:
    for word in ijson.items(f, "words.item"):
        if word.get("jlpt_waller") == "N5":
            print(word["kana"][0]["text"])
```

### jq streaming for large files

```bash
# Stream words-full.json without loading it fully
jq --stream 'select(.[0][0] == "words" and .[0][2] == "id") | .[1]' \
  data/core/words-full.json | head -20
```

For most `jq` queries on files under 50 MB, standard (non-streaming) mode is fine.

---

## SQLite database

The SQLite export (`dist/japanese-language-data.sqlite`, built via `just export-sqlite`) puts all data into a single queryable file. No JSON parsing needed.

### Word lookup with JLPT level and pitch accent

```sql
SELECT w.kanji_primary, w.kana_primary, w.jlpt,
       pa.positions AS pitch, fs.rank AS media_freq
FROM words w
LEFT JOIN pitch_accent pa ON pa.text = w.kanji_primary AND pa.reading = w.kana_primary
LEFT JOIN frequency_subtitles fs ON fs.text = w.kanji_primary
WHERE w.kanji_primary = '食べる';
```

### N3 grammar points sorted by pattern

```sql
SELECT id, pattern, meaning_en FROM grammar WHERE level = 'N3' ORDER BY pattern;
```

### Counter words with JLPT level

```sql
SELECT text, reading, meanings_json, jlpt FROM counter_words ORDER BY text;
```

### Most common words in spoken media (top 20)

```sql
SELECT fs.text, fs.reading, fs.rank, w.jlpt
FROM frequency_subtitles fs
LEFT JOIN words w ON w.kanji_primary = fs.text OR w.kana_primary = fs.text
ORDER BY fs.rank
LIMIT 20;
```

---

## Subtitle frequency

### Python: load and rank

```python
import json

with open("data/enrichment/frequency-subtitles.json") as f:
    freq = json.load(f)

# Top 10 most frequent words in spoken media
for entry in freq["entries"][:10]:
    print(f"{entry['rank']:>5}  {entry['text']}  ({entry['reading']})  count={entry['count']}")
```

### jq: top N words

```bash
jq '.entries[:10][] | "\(.rank) \(.text) (\(.reading))"' data/enrichment/frequency-subtitles.json
```

---

## Furigana (ruby text)

### Python: render ruby annotations

```python
import json

with open("data/enrichment/furigana.json") as f:
    furigana = json.load(f)

# Build lookup by (text, reading)
furi_lookup = {(e["text"], e["reading"]): e["segments"] for e in furigana["entries"]}

# Render HTML ruby for a word
segments = furi_lookup.get(("食べる", "たべる"), [])
html = ""
for seg in segments:
    base = seg.get("ruby", "")
    rt = seg.get("rt", "")
    if rt:
        html += f"<ruby>{base}<rt>{rt}</rt></ruby>"
    else:
        html += base
print(html)  # <ruby>食<rt>た</rt></ruby>べる
```

### jq: list all furigana entries for a word

```bash
jq '.entries[] | select(.text == "食べる")' data/enrichment/furigana.json
```

---

## Multi-source frequency comparison

### SQLite: compare word rank across 4 frequency sources

```sql
-- Compare ranks for a word across all frequency sources
SELECT 'newspaper' AS source, rank, count FROM frequency_corpus WHERE text = '食べる'
UNION ALL
SELECT 'subtitles', rank, count FROM frequency_subtitles WHERE text = '食べる'
UNION ALL
SELECT 'web', rank, count FROM frequency_web WHERE text = '食べる'
UNION ALL
SELECT 'wikipedia', rank, count FROM frequency_wikipedia WHERE text = '食べる';
```

### SQLite: words in all 4 frequency sources

```sql
-- Words that appear in all four frequency rankings (high-confidence common words)
SELECT fw.text, fw.reading,
       fw.rank AS web_rank,
       fs.rank AS sub_rank,
       fc.rank AS corpus_rank,
       fp.rank AS wiki_rank
FROM frequency_web fw
JOIN frequency_subtitles fs ON fw.text = fs.text
JOIN frequency_corpus fc ON fw.text = fc.text
JOIN frequency_wikipedia fp ON fw.text = fp.text
ORDER BY fw.rank
LIMIT 20;
```

---

## Wiktionary pitch accent supplement

### Python: combined pitch accent lookup

```python
import json

# Load both pitch sources
with open("data/enrichment/pitch-accent.json") as f:
    kanjium = {e["word"]: e for e in json.load(f)["entries"]}

with open("data/enrichment/pitch-accent-wiktionary.json") as f:
    wiktionary = {e["word"]: e for e in json.load(f)["entries"]}

def get_pitch(word):
    """Look up pitch accent, checking Kanjium first, then Wiktionary."""
    entry = kanjium.get(word) or wiktionary.get(word)
    if entry:
        return entry["pitch_positions"]
    return None

print(get_pitch("食べる"))  # [2] — from Kanjium
print(get_pitch("AIDS"))   # [1] — from Wiktionary (not in Kanjium)
```
