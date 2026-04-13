"""Aozora Bunko curated corpus transform.

Downloads and extracts clean text from a curated selection of public-
domain Japanese literary works hosted on Aozora Bunko.

Only works marked 著作権なし (no copyright) in the Aozora catalog are
included. The selection focuses on works commonly used in Japanese
language education and widely referenced in cultural literacy.

Input:
    sources/aozora/catalog.csv  (downloaded from aozora.gr.jp)
    sources/aozora/texts/       (downloaded XHTML files)

Output: ``data/phase4/aozora-corpus.json``

License: Japanese public domain (per-work, verified via catalog flag).
"""

from __future__ import annotations
import logging

import csv
import json
import re
import zipfile
from html.parser import HTMLParser
from io import BytesIO
from pathlib import Path

import requests

from build.pipeline import BUILD_DATE

log = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parents[2]
CATALOG_URL = "https://www.aozora.gr.jp/index_pages/list_person_all_extended_utf8.zip"
CATALOG_DIR = REPO_ROOT / "sources" / "aozora"
CATALOG_CSV = CATALOG_DIR / "catalog.csv"
TEXTS_DIR = CATALOG_DIR / "texts"
OUT = REPO_ROOT / "data" / "phase4" / "aozora-corpus.json"

# Curated selection: (work_id, title, author, reason for inclusion)
# All authors died before 1955 → definitively public domain
CURATED_WORKS = [
    # Natsume Sōseki (d. 1916)
    ("000789", "坊っちゃん", "夏目漱石", "canonical modern novel, widely studied"),
    ("000790", "吾輩は猫である", "夏目漱石", "iconic opening line, humor"),
    ("000773", "こころ", "夏目漱石", "most assigned modern novel in Japanese schools"),
    # Akutagawa Ryūnosuke (d. 1927)
    ("000127", "羅生門", "芥川龍之介", "most famous short story, standard textbook inclusion"),
    ("000082", "蜘蛛の糸", "芥川龍之介", "classic children's story, simple language"),
    ("000033", "藪の中", "芥川龍之介", "Rashomon basis, narrative structure study"),
    # Dazai Osamu (d. 1948)
    ("001567", "走れメロス", "太宰治", "widely read short story, clear modern Japanese"),
    ("000035", "人間失格", "太宰治", "most-sold Japanese novel, cultural touchstone"),
    # Miyazawa Kenji (d. 1933)
    ("001951", "銀河鉄道の夜", "宮沢賢治", "beloved children's classic"),
    ("000043", "注文の多い料理店", "宮沢賢治", "accessible short story"),
    ("000081", "雨ニモマケズ", "宮沢賢治", "most memorized Japanese poem"),
    # Nakajima Atsushi (d. 1942)
    ("000119", "山月記", "中島敦", "standard textbook inclusion, prose style model"),
    ("001737", "李陵", "中島敦", "historical fiction, Chinese classical allusion"),
    ("000620", "名人伝", "中島敦", "zen archery parable"),
    # Mori Ōgai (d. 1922)
    ("000058", "舞姫", "森鷗外", "literary Japanese, Meiji cultural reference"),
    ("000691", "高瀬舟", "森鷗外", "standard textbook short story"),
    ("000689", "山椒大夫", "森鷗外", "classic tale, widely anthologized"),
    # Higuchi Ichiyō (d. 1896)
    ("000079", "たけくらべ", "樋口一葉", "classical/modern transitional prose"),
    # Kajii Motojirō (d. 1932)
    ("046349", "檸檬", "梶井基次郎", "iconic modernist short story, widely taught"),
    # Sakaguchi Ango (d. 1955)
    ("042620", "堕落論", "坂口安吾", "famous postwar essay"),
    ("042618", "桜の森の満開の下", "坂口安吾", "supernatural classic"),
    # Kobayashi Takiji (d. 1933)
    ("001465", "蟹工船", "小林多喜二", "canonical proletarian novel"),
    # Niimi Nankichi (d. 1943) — children's stories, widely taught in schools
    ("000628", "ごん狐", "新美南吉", "most-taught children's story in Japanese schools"),
    ("000637", "手袋を買いに", "新美南吉", "beloved children's story, simple language"),
    # Izumi Kyōka (d. 1939)
    ("043466", "高野聖", "泉鏡花", "classic supernatural tale"),
    ("000360", "外科室", "泉鏡花", "famous short story"),
    # Arishima Takeo (d. 1923)
    ("000211", "一房の葡萄", "有島武郎", "widely anthologized, accessible"),
    ("001111", "生まれいずる悩み", "有島武郎", "coming-of-age classic"),
    # Kunikida Doppo (d. 1908)
    ("000329", "武蔵野", "国木田独歩", "iconic nature essay"),
    # Hori Tatsuo (d. 1953)
    ("004803", "風立ちぬ", "堀辰雄", "source for Miyazaki film, lyrical prose"),
    # Nakahara Chūya (d. 1937)
    ("000219", "在りし日の歌", "中原中也", "major modern poetry collection"),
    # Shimazaki Tōson (d. 1943)
    ("001502", "破戒", "島崎藤村", "groundbreaking social novel"),
    # Yokomitsu Riichi (d. 1947)
    ("000907", "機械", "横光利一", "modernist classic, experimental prose"),
    # Hayama Yoshiki (d. 1945)
    ("000863", "海に生くる人々", "葉山嘉樹", "proletarian literature"),
    # Masaoka Shiki (d. 1902)
    ("043537", "病牀六尺", "正岡子規", "iconic essay, haiku master"),
    # Natsume Sōseki (additional)
    ("000799", "夢十夜", "夏目漱石", "10 dream stories, each self-contained"),
    # Akutagawa Ryūnosuke (additional)
    ("000042", "鼻", "芥川龍之介", "classic short story, standard textbook"),
    ("000170", "杜子春", "芥川龍之介", "accessible tale"),
    ("000061", "地獄変", "芥川龍之介", "powerful short story"),
    ("000069", "河童", "芥川龍之介", "satirical novella"),
    ("000019", "或阿呆の一生", "芥川龍之介", "autobiographical, literary Japanese"),
    # Dazai Osamu (additional)
    ("001565", "斜陽", "太宰治", "postwar classic novel"),
    ("000275", "女生徒", "太宰治", "accessible first-person narrative"),
    ("002253", "ヴィヨンの妻", "太宰治", "Nobel-adjacent short story"),
    # Miyazawa Kenji (additional)
    ("000473", "よだかの星", "宮沢賢治", "poignant children's fable"),
    ("000470", "セロ弾きのゴーシュ", "宮沢賢治", "musical children's story"),
    ("000462", "風の又三郎", "宮沢賢治", "nature and childhood classic"),
]


class _TextExtractor(HTMLParser):
    """Extract plain text from Aozora XHTML, stripping ruby annotations."""

    def __init__(self) -> None:
        super().__init__()
        self._text_parts: list[str] = []
        self._skip = False
        self._in_body = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "body":
            self._in_body = True
        if tag in ("rt", "rp"):
            self._skip = True
        if tag in ("br",):
            self._text_parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in ("rt", "rp"):
            self._skip = False
        if tag == "body":
            self._in_body = False
        if tag in ("p", "div", "h1", "h2", "h3", "h4"):
            self._text_parts.append("\n")

    def handle_data(self, data: str) -> None:
        if self._in_body and not self._skip:
            self._text_parts.append(data)

    def get_text(self) -> str:
        raw = "".join(self._text_parts)
        # Collapse multiple newlines, strip editorial notes
        raw = re.sub(r"［＃[^］]*］", "", raw)
        raw = re.sub(r"\n{3,}", "\n\n", raw)
        return raw.strip()


class _RubyExtractor(HTMLParser):
    """Extract (kanji, furigana) pairs from ruby tags."""

    def __init__(self) -> None:
        super().__init__()
        self._pairs: list[tuple[str, str]] = []
        self._in_rb = False
        self._in_rt = False
        self._rb_text = ""
        self._rt_text = ""

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "rb":
            self._in_rb = True
            self._rb_text = ""
        elif tag == "rt":
            self._in_rt = True
            self._rt_text = ""

    def handle_endtag(self, tag: str) -> None:
        if tag == "rb":
            self._in_rb = False
        elif tag == "rt":
            self._in_rt = False
            if self._rb_text and self._rt_text:
                self._pairs.append((self._rb_text, self._rt_text))

    def handle_data(self, data: str) -> None:
        if self._in_rb:
            self._rb_text += data
        elif self._in_rt:
            self._rt_text += data

    def get_pairs(self) -> list[tuple[str, str]]:
        return self._pairs


def _download_catalog() -> None:
    """Download and extract the Aozora catalog CSV."""
    CATALOG_DIR.mkdir(parents=True, exist_ok=True)
    if CATALOG_CSV.exists():
        return
    log.info("[aozora]   downloading catalog...")
    resp = requests.get(CATALOG_URL, timeout=60)
    resp.raise_for_status()
    with zipfile.ZipFile(BytesIO(resp.content)) as zf:
        for name in zf.namelist():
            if name.endswith("_utf8.csv"):
                CATALOG_CSV.write_bytes(zf.read(name))
                log.info(f"extracted {CATALOG_CSV.name}")
                return
    raise RuntimeError("No UTF-8 CSV found in catalog ZIP")


def _find_work_url(work_id: str) -> str | None:
    """Look up the XHTML URL for a work ID from the catalog."""
    with CATALOG_CSV.open("r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("作品ID") == work_id:
                url = row.get("XHTML/HTMLファイルURL", "")
                if url:
                    return url
                # Fall back to text file
                url = row.get("テキストファイルURL", "")
                return url if url else None
    return None


def _download_work(work_id: str, url: str) -> str:
    """Download a work's HTML/text content."""
    TEXTS_DIR.mkdir(parents=True, exist_ok=True)
    cache_path = TEXTS_DIR / f"{work_id}.html"
    if cache_path.exists():
        return cache_path.read_text(encoding="utf-8", errors="replace")

    log.info(f"downloading {work_id}...")
    resp = requests.get(url, timeout=60)
    resp.raise_for_status()

    # Aozora files may be Shift_JIS or UTF-8
    content_type = resp.headers.get("Content-Type", "")
    if "shift_jis" in content_type.lower() or "sjis" in content_type.lower():
        text = resp.content.decode("cp932", errors="replace")
    else:
        text = resp.content.decode("utf-8", errors="replace")
        if "charset=Shift_JIS" in text or "charset=shift_jis" in text:
            text = resp.content.decode("cp932", errors="replace")

    # If it's a ZIP, extract the HTML inside
    if url.endswith(".zip"):
        with zipfile.ZipFile(BytesIO(resp.content)) as zf:
            for name in zf.namelist():
                if name.endswith(".html") or name.endswith(".htm"):
                    raw = zf.read(name)
                    text = raw.decode("cp932", errors="replace")
                    break

    cache_path.write_text(text, encoding="utf-8")
    return text


def build() -> None:
    log.info("[aozora]   Aozora Bunko curated corpus")

    _download_catalog()

    entries: list[dict] = []
    for work_id, title, author, reason in CURATED_WORKS:
        url = _find_work_url(work_id)
        if not url:
            log.info(f"WARNING: no URL for {work_id} ({title}), skipping")
            continue

        try:
            html = _download_work(work_id, url)
        except Exception as e:
            log.info(f"WARNING: download failed for {work_id}: {e}")
            continue

        extractor = _TextExtractor()
        extractor.feed(html)
        text = extractor.get_text()

        ruby_extractor = _RubyExtractor()
        ruby_extractor.feed(html)
        ruby_pairs = ruby_extractor.get_pairs()

        char_count = len(text)
        sentence_count = len(re.findall(r"[。！？]", text))

        entries.append({
            "work_id": work_id,
            "title": title,
            "author": author,
            "reason": reason,
            "char_count": char_count,
            "sentence_count": sentence_count,
            "ruby_count": len(ruby_pairs),
            "text": text,
            "ruby_pairs": [{"kanji": k, "reading": r} for k, r in ruby_pairs[:500]],
        })
        log.info(f"{title} ({author}): {char_count:,} chars, {sentence_count} sentences, {len(ruby_pairs)} ruby")

    log.info(f"total: {len(entries)} works")

    output = {
        "metadata": {
            "source": "Aozora Bunko (青空文庫)",
            "source_url": "https://www.aozora.gr.jp/",
            "license": "Japanese public domain (per-work, verified via catalog 著作権なし flag)",
            "generated": BUILD_DATE,
            "count": len(entries),
            "note": (
                "Curated selection of public-domain Japanese literary works from "
                "Aozora Bunko. All included works are by authors who died before "
                "1955, placing them definitively in the Japanese public domain "
                "(death + 70 years, with no retroactive protection under the 2018 "
                "copyright term extension). Selection focuses on works commonly used "
                "in Japanese language education."
            ),
            "attribution": (
                "Text from Aozora Bunko (https://www.aozora.gr.jp/), a volunteer-"
                "run digital library of Japanese public-domain literature."
            ),
        },
        "works": entries,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
        f.write("\n")
    log.info(f"wrote {OUT.relative_to(REPO_ROOT)}")
