#!/usr/bin/env python3
"""生成 data/zh/definitions.json —— 字/词 -> [[拼音, 粤拼, [英文释义…]], …]。

读音（拼音）：
    HSK 词汇里有拼音的（所有多字词 + 部分字）用 HSK 大纲拼音，不用 CC-CEDICT；
    只在 HSK 汉字、不在词汇里的字回退 CC-CEDICT 读音。
粤拼：
    字    取 data/zh/archive/粤拼.json（按该拼音查）；
    词    优先 rime-cantonese 整词，缺则按 粤拼.json 逐字拼。
释义：
    字    用 Unihan kDefinition（data/zh/archive/字义.json 同源，此处直接取 Unihan）；
    词    用 CC-CEDICT（按拼音对齐到对应读音的释义）。
另生成 data/zh/archive/字义.json（字 -> Unihan gloss，原样保留）。

来源：
    HSK 大纲        sources/zh/新版HSK考试大纲1219.pdf  -> data/zh/archive/HSK{词汇,汉字}.json
    CC-CEDICT       sources/zh/cedict_ts.u8                 (CC BY-SA 4.0)
    Unihan          sources/zh/Unihan.zip                   (Unicode License V3)
    rime-cantonese  sources/zh/rime-cantonese/…             (CC BY 4.0 / ODbL 1.0)

用法：
    uv run tools/zh_defs.py
    uv run tools/zh_defs.py --check
"""
from __future__ import annotations

import argparse
import json
import re
import unicodedata
import zipfile
from collections import OrderedDict, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "zh"
ARCHIVE = DATA / "archive"
CEDICT = ROOT / "sources" / "zh" / "cedict_ts.u8"
UNIHAN = ROOT / "sources" / "zh" / "Unihan.zip"
RIME = ROOT / "sources" / "zh" / "rime-cantonese"
JYUTPING = ARCHIVE / "粤拼.json"
DEFS_OUT = DATA / "definitions.json"
CHAR_OUT = ARCHIVE / "字义.json"

CEDICT_LINE = re.compile(r"^(\S+)\s+(\S+)\s+\[([^\]]*)\]\s+/(.*)/$")
UNIHAN_DEF = re.compile(r"^U\+([0-9A-F]+)\tkDefinition\t(.*)$")

TONE = {"a": "āáǎà", "e": "ēéěè", "i": "īíǐì", "o": "ōóǒò", "u": "ūúǔù", "ü": "ǖǘǚǜ"}


def num_to_marks(syllables: str) -> str:
    """CC-CEDICT 数字调拼音（ai4 si5）-> 带调拼音（ài si）。"""
    out: list[str] = []
    for syl in syllables.split():
        m = re.match(r"^([A-Za-zü:]+?)([1-5])?$", syl)
        if not m:
            out.append(syl)
            continue
        base = m.group(1).replace("u:", "ü").replace("v", "ü")
        tone = m.group(2)
        if not tone or tone == "5":
            out.append(base)
            continue
        low = base.lower()
        if "a" in low:
            i = low.index("a")
        elif "o" in low:
            i = low.index("o")
        elif "e" in low:
            i = low.index("e")
        elif "iu" in low:
            i = low.index("u")
        elif "ui" in low:
            i = low.index("i")
        else:
            vowels = [j for j, c in enumerate(low) if c in TONE]
            if not vowels:
                out.append(base)
                continue
            i = vowels[-1]
        marks = TONE.get(base[i].lower())
        if marks is None:
            out.append(base)
            continue
        new = marks[int(tone) - 1]
        out.append(base[:i] + (new.upper() if base[i].isupper() else new) + base[i + 1 :])
    return " ".join(out)


def base_pinyin(s: str) -> str:
    """去空格/连字符/撇号、去声调，用于跨源对齐（bú kèqi / bù kè qi / qīnpéng-hǎoyǒu -> bukeqi）。"""
    for ch in (" ", "-", "’", "'", "·"):
        s = s.replace(ch, "")
    return "".join(c for c in unicodedata.normalize("NFD", s) if not unicodedata.combining(c)).lower()


def norm_full(s: str) -> str:
    """去分隔符，但保留声调与大小写（用于精确对齐读音）。"""
    for ch in (" ", "-", "’", "'", "·"):
        s = s.replace(ch, "")
    return s


def is_surname(defs: list[str]) -> bool:
    return bool(defs) and defs[0].lower().startswith("surname")


def load_cedict(path: Path) -> dict[str, list[tuple[str, list[str]]]]:
    """简体 -> [(带调拼音(空格分隔), [释义…]), …]。"""
    index: dict[str, list[tuple[str, list[str]]]] = defaultdict(list)
    with path.open(encoding="utf-8") as f:
        for line in f:
            if line.startswith("#"):
                continue
            m = CEDICT_LINE.match(line.rstrip("\n"))
            if m:
                _trad, simp, pinyin, defs = m.groups()
                index[simp].append((num_to_marks(pinyin), [d for d in defs.split("/") if d]))
    return index


def load_simp2trad(path: Path) -> dict[str, set[str]]:
    m: dict[str, set[str]] = defaultdict(set)
    with path.open(encoding="utf-8") as f:
        for line in f:
            if line.startswith("#"):
                continue
            match = re.match(r"^(\S+)\s+(\S+)\s+\[", line)
            if match:
                m[match.group(2)].add(match.group(1))
    return m


def load_unihan(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    with zipfile.ZipFile(path) as z:
        for raw in z.open("Unihan_Readings.txt"):
            m = UNIHAN_DEF.match(raw.decode("utf-8").rstrip("\n"))
            if m:
                out[chr(int(m.group(1), 16))] = m.group(2)
    return out


def load_rime_words(path: Path) -> dict[str, list[str]]:
    out: dict[str, list[str]] = defaultdict(list)
    with path.open(encoding="utf-8") as f:
        for line in f:
            if line.startswith("#") or line.startswith("---") or line.startswith("..."):
                continue
            parts = line.rstrip("\n").split("\t")
            if len(parts) >= 2 and parts[1].strip():
                out[parts[0]].append(" ".join(parts[1].split()))
    return out


def load_hsk() -> tuple[OrderedDict[str, list[str]], set[str]]:
    """HSK 词汇拼音（词/字 -> [拼音…]）与 HSK 汉字集合。"""
    vocab = json.loads((ARCHIVE / "HSK词汇.json").read_text(encoding="utf-8"))
    pinyin: OrderedDict[str, list[str]] = OrderedDict()
    for section, words in vocab.items():
        if section.startswith("_"):
            continue
        for word, records in words.items():
            bucket = pinyin.setdefault(word, [])
            for rec in records:
                py = rec[0] if isinstance(rec, list) else ""
                if py and py not in bucket:
                    bucket.append(py)
    hanzi = json.loads((ARCHIVE / "HSK汉字.json").read_text(encoding="utf-8"))
    chars = {ch for s, items in hanzi.items() if not s.startswith("_") for ch in items}
    return pinyin, chars


def keys_order(pinyin: OrderedDict[str, list[str]], chars: set[str]) -> list[str]:
    order: OrderedDict[str, None] = OrderedDict.fromkeys(pinyin)
    for ch in chars:
        order.setdefault(ch, None)
    return list(order)


def main():
    ap = argparse.ArgumentParser(description="生成 data/zh/definitions.json、data/zh/archive/字义.json")
    ap.add_argument("--check", action="store_true", help="只报告覆盖，不写文件")
    args = ap.parse_args()

    for p in (CEDICT, UNIHAN, RIME / "jyut6ping3.words.dict.yaml", JYUTPING):
        if not p.exists():
            raise SystemExit(f"找不到 {p}")

    cedict = load_cedict(CEDICT)
    s2t = load_simp2trad(CEDICT)
    unihan = load_unihan(UNIHAN)
    rime = load_rime_words(RIME / "jyut6ping3.words.dict.yaml")
    jyutping = json.loads(JYUTPING.read_text(encoding="utf-8"))
    jyutping.pop("_meta", None)
    hsk_pinyin, chars = load_hsk()
    keys = keys_order(hsk_pinyin, chars)

    # 每个字的 粤拼：base(拼音) -> 粤拼，方便按音节查（容忍声调差异）
    jyut_by_base: dict[str, dict[str, str]] = {}
    for ch, mapping in jyutping.items():
        jyut_by_base[ch] = {base_pinyin(py): jp for py, jp in mapping.items() if jp}

    def jyut_of_char(ch: str, syllable: str) -> str:
        m = jyutping.get(ch, {})
        for s in syllable.split("/"):
            if s in m:
                return m[s]
        for s in syllable.split("/"):
            jp = jyut_by_base.get(ch, {}).get(base_pinyin(s))
            if jp:
                return jp
        return ""

    def rime_of_word(word: str) -> str:
        for form in (word,) + tuple(s2t.get(word, ())):
            if form in rime:
                return rime[form][0]
        return ""

    def match_cedict(word: str, reading: str):
        """把读音对到 CC-CEDICT 某条：先完整拼音(含调/大小写)精确，再忽略大小写，再按去调 base（排除 surname），返回 (空格音节, 释义)。"""
        target, low = norm_full(reading), norm_full(reading).lower()
        base = base_pinyin(reading)
        cands = cedict.get(word, [])
        for spaced, defs in cands:
            if norm_full(spaced) == target:
                return spaced, defs
        for spaced, defs in cands:
            if norm_full(spaced).lower() == low:
                return spaced, defs
        for spaced, defs in cands:
            if base_pinyin(spaced) == base and not is_surname(defs):
                return spaced, defs
        for spaced, defs in cands:
            if base_pinyin(spaced) == base:
                return spaced, defs
        return "", []

    def assemable(word: str, spaced: str) -> str:
        syls = spaced.split()
        if len(syls) != len(word):
            return ""
        parts = [jyut_of_char(ch, syl) for ch, syl in zip(word, syls)]
        return " ".join(p for p in parts) if all(parts) else ""

    out: OrderedDict[str, list] = OrderedDict()
    char_defs: OrderedDict[str, str] = OrderedDict()
    n_readings = n_word_jyut = n_assemble = n_jyut_missing = 0
    for key in keys:
        entries: list[list] = []
        if key in hsk_pinyin:
            readings = hsk_pinyin[key]
            for py in readings:
                spaced, defs = match_cedict(key, py)
                if len(key) == 1:
                    jp = jyut_of_char(key, py)
                elif len(readings) == 1 and (rw := rime_of_word(key)):
                    jp = rw
                else:
                    jp = assemable(key, spaced)
                entries.append([py, jp, defs])
        else:
            for spaced, defs in cedict.get(key, []):
                entries.append([spaced, jyut_of_char(key, spaced) if len(key) == 1 else "", defs])

        if key in chars and (gloss := unihan.get(key)):
            char_defs[key] = gloss
            for e in entries:  # 字：仅当某读音没有 CC-CEDICT 释义时才用 Unihan gloss 兜底
                if not e[2]:
                    e[2] = [gloss]

        n_readings += len(entries)
        for e in entries:
            if e[1]:
                if " " in e[1]:
                    n_assemble += 1
            else:
                n_jyut_missing += 1
        out[key] = entries

    print(f"字/词 {len(out)} 个；读音 {n_readings} 条")
    print(f"  粤拼缺失 {n_jyut_missing}；Unihan 字释义 {len(char_defs)}")
    print("  样例：")
    for k in ("弟", "行", "爱", "银行", "行走", "的"):
        if k in out:
            print(f"    {k}: {json.dumps(out[k], ensure_ascii=False)}")

    if args.check:
        return

    write_meta = {
        "source": "拼音:HSK 大纲 + CC-CEDICT；粤拼:rime-cantonese + Unihan；释义:CC-CEDICT(词) + Unihan(字)",
        "license": {
            "CC-CEDICT": "CC BY-SA 4.0",
            "Unihan": "Unicode License V3",
            "rime-cantonese": "CC BY 4.0 / ODbL 1.0",
        },
        "format": {"字/词": "[[拼音, 粤拼, [英文释义…]], …]"},
        "note": "拼音优先 HSK 大纲（多字词全部、及部分字），其余回退 CC-CEDICT；"
        "粤拼 字取 粤拼.json、词优先 rime 整词否则逐字；释义用 CC-CEDICT（字在某读音无释义时才回退 Unihan kDefinition）。",
    }
    meta_text = '  "_meta": ' + json.dumps(write_meta, ensure_ascii=False, indent=2).replace("\n", "\n  ")
    body = ",\n".join(
        f"  {json.dumps(k, ensure_ascii=False)}: {json.dumps(v, ensure_ascii=False)}" for k, v in out.items()
    )
    DEFS_OUT.write_text("{\n" + meta_text + ",\n" + body + "\n}\n", encoding="utf-8")
    print(f"已写入 {DEFS_OUT.relative_to(ROOT)}（{DEFS_OUT.stat().st_size / 1024:.0f} KB）")

    cmeta = {
        "source": "Unihan  https://www.unicode.org/Public/UCD/latest/ucd/Unihan.zip（kDefinition）",
        "license": "Unicode License V3",
        "format": {"汉字": "英文 gloss（Unihan kDefinition 原文，未清洗）"},
        "note": f"仅收 HSK 汉字，共 {len(char_defs)} 字；释义简略、偏字源，供字级参考。",
    }
    cmeta_text = '  "_meta": ' + json.dumps(cmeta, ensure_ascii=False, indent=2).replace("\n", "\n  ")
    cbody = ",\n".join(
        f"  {json.dumps(k, ensure_ascii=False)}: {json.dumps(v, ensure_ascii=False)}" for k, v in char_defs.items()
    )
    CHAR_OUT.write_text("{\n" + cmeta_text + ",\n" + cbody + "\n}\n", encoding="utf-8")
    print(f"已写入 {CHAR_OUT.relative_to(ROOT)}（{CHAR_OUT.stat().st_size / 1024:.0f} KB）")


if __name__ == "__main__":
    main()
