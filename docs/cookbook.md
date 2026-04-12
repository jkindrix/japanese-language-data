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
