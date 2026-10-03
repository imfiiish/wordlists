#!/usr/bin/env python3
"""生成 data/zh/archive/粤拼.json —— 汉字级「普通话拼音 -> 粤拼(Jyutping)」对照。

来源：
    CC-CEDICT       sources/zh/cedict_ts.u8   (CC BY-SA 4.0)  普通话读音 + 简->繁
    rime-cantonese  sources/zh/rime-cantonese (CC BY 4.0 / ODbL 1.0) 字/词 -> 粤拼
    Unihan          sources/zh/Unihan.zip     (Unicode License V3)  kCantonese 兜底

做法：
    1. 用 CC-CEDICT 的**词**（含普通话音节）与 rime 的词（粤拼音节）逐音节对齐，给字级投票；
    2. 每个拼音读音取票数最高的粤拼；
    3. 仍缺的读音，依次取 rime 字表里「还没被用到」的读音（比单用 Unihan 更准）；
    4. 再缺才用 Unihan kCantonese。

输出：data/zh/archive/粤拼.json
    {汉字: {拼音: 粤拼}}，拼音为带调普通话，粤拼为 Jyutping
"""
from __future__ import annotations

import argparse
import json
import re
import unicodedata
import zipfile
from collections import Counter, OrderedDict, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "zh"
ARCHIVE = DATA / "archive"
CEDICT = ROOT / "sources" / "zh" / "cedict_ts.u8"
UNIHAN = ROOT / "sources" / "zh" / "Unihan.zip"
RIME = ROOT / "sources" / "zh" / "rime-cantonese"
OUT = ARCHIVE / "粤拼.json"

CEDICT_LINE = re.compile(r"^(\S+)\s+(\S+)\s+\[([^\]]*)\]\s+/(.*)/$")
UNIHAN_CT = re.compile(r"^U\+([0-9A-F]+)\tkCantonese\t(.*)$")

TONE = {"a": "āáǎà", "e": "ēéěè", "i": "īíǐì", "o": "ōóǒò", "u": "ūúǔù", "ü": "ǖǘǚǜ"}


def num_to_marks(syllables: str) -> str:
    out: list[str] = []
    for syl in syllables.split():
        m = re.match(r"^([A-Za-zü:]+?)([1-5])?$", syl)
        if not m:
            out.append(syl)
            continue
        b = m.group(1).replace("u:", "ü").replace("v", "ü")
        tone = m.group(2)
        if not tone or tone == "5":
            out.append(b)
            continue
        low = b.lower()
        for key in ("a", "o", "e"):
            if key in low:
                i = low.index(key)
                break
        else:
            if "iu" in low:
                i = low.index("u")
            elif "ui" in low:
                i = low.index("i")
            else:
                vowels = [j for j, c in enumerate(low) if c in TONE]
                if not vowels:
                    out.append(b)
                    continue
                i = vowels[-1]
        marks = TONE.get(b[i].lower())
        if marks is None:
            out.append(b)
            continue
        new = marks[int(tone) - 1]
        out.append(b[:i] + (new.upper() if b[i].isupper() else new) + b[i + 1 :])
    return " ".join(out)


def base_pinyin(s: str) -> str:
    s = s.replace(" ", "")
    return "".join(c for c in unicodedata.normalize("NFD", s) if not unicodedata.combining(c)).lower()


def load_cedict(path: Path):
    """(simp -> [(带调拼音(空格), [释义…]), …], simp -> {trad…})。"""
    index: dict[str, list[tuple[str, list[str]]]] = defaultdict(list)
    s2t: dict[str, set[str]] = defaultdict(set)
    with path.open(encoding="utf-8") as f:
        for line in f:
            if line.startswith("#"):
                continue
            m = CEDICT_LINE.match(line.rstrip("\n"))
            if m:
                trad, simp, pinyin, defs = m.groups()
                index[simp].append((num_to_marks(pinyin), [d for d in defs.split("/") if d]))
                s2t[simp].add(trad)
    return index, s2t


def load_unihan(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    with zipfile.ZipFile(path) as z:
        for raw in z.open("Unihan_Readings.txt"):
            m = UNIHAN_CT.match(raw.decode("utf-8").rstrip("\n"))
            if m:
                out[chr(int(m.group(1), 16))] = m.group(2).strip()
    return out


def load_rime(path: Path) -> dict[str, list[str]]:
    out: dict[str, list[str]] = defaultdict(list)
    with path.open(encoding="utf-8") as f:
        for line in f:
            if line.startswith("#") or line.startswith("---") or line.startswith("..."):
                continue
            parts = line.rstrip("\n").split("\t")
            if len(parts) >= 2 and parts[1].strip():
                out[parts[0]].append(" ".join(parts[1].split()))
    return out


def load_hsk() -> tuple[list[str], dict[str, list[str]]]:
    """HSK 汉字（有序）与 HSK 词汇里单字的拼音。"""
    hanzi = json.loads((ARCHIVE / "HSK汉字.json").read_text(encoding="utf-8"))
    seen: OrderedDict[str, None] = OrderedDict()
    for section, items in hanzi.items():
        if section.startswith("_"):
            continue
        for ch in items:
            seen.setdefault(ch, None)
    vocab = json.loads((ARCHIVE / "HSK词汇.json").read_text(encoding="utf-8"))
    hsk_py: dict[str, list[str]] = defaultdict(list)
    for word, records in vocab.items():
        if len(word) != 1:
            continue
        for rec in records:
            py = rec[0] if isinstance(rec, list) else ""
            if py and py not in hsk_py[word]:
                hsk_py[word].append(py)
    return list(seen), hsk_py


def main():
    ap = argparse.ArgumentParser(description="生成 data/zh/archive/粤拼.json")
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()

    cedict, s2t = load_cedict(CEDICT)
    unihan = load_unihan(UNIHAN)
    rime_c = load_rime(RIME / "jyut6ping3.chars.dict.yaml")
    rime_w = load_rime(RIME / "jyut6ping3.words.dict.yaml")
    chars, hsk_py = load_hsk()

    def rime_word(word: str) -> list[str]:
        for form in (word,) + tuple(s2t.get(word, ())):
            if form in rime_w:
                return rime_w[form]
        return []

    def rime_char(ch: str) -> list[str]:
        for form in (ch,) + tuple(s2t.get(ch, ())):
            if form in rime_c:
                return rime_c[form]
        return []

    # 1) 全量词对齐投票
    votes: dict[str, Counter] = defaultdict(Counter)
    aligned_words = 0
    for word, readings in cedict.items():
        if len(word) < 2:
            continue
        jyuts = rime_word(word)
        if not jyuts:
            continue
        for spaced, _ in readings:
            syls = spaced.split()
            if len(syls) != len(word):
                continue
            for jyut in jyuts:
                js = jyut.split()
                if len(js) != len(word):
                    continue
                for ch, py, jp in zip(word, syls, js):
                    votes[ch][(py, jp)] += 1
                break
        aligned_words += 1

    # 2) 每个拼音取票数最高的粤拼
    best: dict[str, dict[str, str]] = {}
    for ch, counter in votes.items():
        top: dict[str, tuple[str, int]] = {}
        for (py, jp), c in counter.items():
            if py not in top or c > top[py][1]:
                top[py] = (jp, c)
        best[ch] = {py: jp for py, (jp, _) in top.items()}

    # 3) 逐字补全：对齐 -> rime 字表未用读音 -> Unihan
    out: OrderedDict[str, OrderedDict] = OrderedDict()
    n_align = n_rime = n_unihan = 0
    for ch in chars:
        readings: list[str] = []
        for py in [spaced for spaced, _ in cedict.get(ch, [])] + hsk_py.get(ch, []):
            if py not in readings:
                readings.append(py)
        if not readings:
            readings = [""]
        per: OrderedDict[str, str] = OrderedDict()
        used = set(best.get(ch, {}).values())
        pool = [r for r in rime_char(ch) if r not in used]
        for py in readings:
            if py in best.get(ch, {}):
                per[py] = best[ch][py]
                n_align += 1
            elif pool:
                per[py] = pool.pop(0)
                n_rime += 1
            elif unihan.get(ch):
                per[py] = unihan[ch]
                n_unihan += 1
            else:
                per[py] = ""
        out[ch] = per

    print(f"汉字 {len(out)}；对齐词 {aligned_words}")
    print(f"  拼音->粤拼：对齐 {n_align}，rime 字表补 {n_rime}，Unihan 兜底 {n_unihan}")
    for k in ("弟", "行", "长", "重", "乐"):
        if k in out:
            print(f"    {k}: {json.dumps(out[k], ensure_ascii=False)}")

    if args.check:
        return

    meta = {
        "source": "CC-CEDICT（对齐）+ rime-cantonese chars（补全） + Unihan kCantonese（兜底）",
        "license": {"CC-CEDICT": "CC BY-SA 4.0", "rime-cantonese": "CC BY 4.0 / ODbL 1.0", "Unihan": "Unicode License V3"},
        "format": {"汉字": "{拼音: 粤拼}；拼音为带调普通话，粤拼为 Jyutping"},
        "note": "以 CC-CEDICT 的词逐音节对齐 rime 得到字级映射；缺的读音按序取 rime 字表未用读音，最后 Unihan 兜底。",
    }
    meta_text = '  "_meta": ' + json.dumps(meta, ensure_ascii=False, indent=2).replace("\n", "\n  ")
    body = ",\n".join(
        f"  {json.dumps(k, ensure_ascii=False)}: {json.dumps(v, ensure_ascii=False)}" for k, v in out.items()
    )
    OUT.write_text("{\n" + meta_text + ",\n" + body + "\n}\n", encoding="utf-8")
    print(f"已写入 {OUT.relative_to(ROOT)}（{OUT.stat().st_size / 1024:.0f} KB）")


if __name__ == "__main__":
    main()
