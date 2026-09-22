#!/usr/bin/env python3
"""从 ECDICT 抽取 data/ 词库的中文释义与音标，生成 data/definitions.json。

数据来源：ECDICT  https://github.com/skywind3000/ECDICT  (MIT License)
原始文件：sources/ECDICT/ecdict.csv

结构：每个词 = [音标, [[头, [释义…]], …]]
头的取法（只按行首判断）：
    - 行首词性（vt./vi./n./a./adv./…）   → 头 = "vt." 等原文（带点）
    - 行首连写 vt.vi./vi.vt.              → 头 = "v."（表示及物、不及物均可）
    - 行首领域标签（[计]/[医]/[法]/…）   → 头 = "[医]" 等原文（带方括号）
    - 两者都没有                          → 头 = "其它"
行内出现的方括号一律保留在正文里（如 交感[作用]、[疾]病），不拆。

用法：
    uv run tools/defs.py           # 生成 / 刷新 data/definitions.json
    uv run tools/defs.py --check   # 只报告覆盖情况，不写文件
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import unicodedata
from collections import Counter
from pathlib import Path

csv.field_size_limit(1 << 30)

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
ECDICT = ROOT / "sources" / "ECDICT" / "ecdict.csv"
OUT = DATA / "definitions.json"
SKIP_FILES = {"definitions.json"}

# 行首连写的两个动词词性（vt.vi. / vi.vt.），含义是"及物、不及物均可"，归到 v.
GLUED_V = re.compile(r"^(?:vt|vi|v)\.(?:vt|vi|v)\.\s*(.*)$", re.I)
# 行首词性；头保留原文（带点）
POS = re.compile(
    r"^(vt|vi|v|aux|n|a|adj|adv|ad|prep|conj|pron|num|art|det|int|interj|abbr|pl|pref)\.\s*(.*)$",
    re.I,
)
# 行首领域标签，如 [医] [计]
BRACKET = re.compile(r"^\[([^\]]{1,10})\]\s*(.*)$")
OTHER = "其它"

# 与 Oxford 词性口径的映射（供消费方对表；文件本身保留原始细分）
POS_MAP = {
    "vt.": "v.",
    "vi.": "v.",
    "v.": "v.",
    "aux.": "auxiliary v.",
    "n.": "n.",
    "a.": "adj.",
    "adv.": "adv.",
    "prep.": "prep.",
    "pron.": "pron.",
    "conj.": "conj.",
    "num.": "number",
    "interj.": "exclam.",
    "art.": "article",
}


def load_ecdict(path: Path) -> dict[str, dict]:
    """按小写词形建索引；同形取信息最全的一条。"""
    index: dict[str, dict] = {}

    def score(r: dict) -> tuple:
        return (
            bool(r["translation"].strip()),
            bool(r["definition"].strip()),
            bool(r["tag"].strip()),
            bool(r["collins"].strip()),
            -int(r["bnc"] or 0),
        )

    with path.open(encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            key = row["word"].strip().lower()
            cur = index.get(key)
            if cur is None or score(row) > score(cur):
                index[key] = row
    return index


def candidates(word: str) -> list[str]:
    """把一个词条 key 展开为若干可用于查 ECDICT 的写法。"""
    w = unicodedata.normalize("NFC", word).strip().replace("\u2019", "'").replace("\u2018", "'")
    out: list[str] = []
    for cand in (w, w.lower()):
        if cand and cand not in out:
            out.append(cand)
    for part in re.split(r",", w):  # "a, an" → "a" / "an"
        part = part.strip()
        if part and part.lower() not in out:
            out.append(part.lower())
    for cand in list(out):  # 去音符兜底（café → cafe）
        plain = "".join(c for c in unicodedata.normalize("NFKD", cand) if not unicodedata.combining(c))
        if plain.lower() not in out:
            out.append(plain.lower())
    return out


def find(index: dict[str, dict], word: str) -> dict | None:
    for cand in candidates(word):
        rec = index.get(cand)
        if rec is not None:
            return rec
    return None


def raw_lines(text: str) -> list[str]:
    text = text.replace("\\r\\n", "\n").replace("\\n", "\n").replace("\r\n", "\n").replace("\r", "\n")
    return [line.strip() for line in text.split("\n") if line.strip()]


def group(lines: list[str]) -> list[list]:
    """按行首把头（词性 / 领域标签 / 其它）分组，返回 [[头, [释义…]], …]。"""
    out: dict[str, list[str]] = {}
    for line in lines:
        m = GLUED_V.match(line)
        if m:
            head, body = "v.", m.group(1).strip()
        else:
            m = POS.match(line)
            if m:
                head, body = m.group(1).lower() + ".", m.group(2).strip()
            else:
                m = BRACKET.match(line)
                head, body = (f"[{m.group(1)}]", m.group(2).strip()) if m else (OTHER, line)
        out.setdefault(head, []).append(body)
    return [[head, texts] for head, texts in out.items()]


def load_words() -> list[str]:
    words: list[str] = []
    seen: set[str] = set()
    for path in sorted(DATA.glob("*.json")):
        if path.name in SKIP_FILES:
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        for word in file_word_keys(data):
            if word in seen:
                continue
            seen.add(word)
            words.append(word)
    return words


def file_word_keys(data: dict) -> list[str]:
    """Oxford 词库按来源分节（Oxford3000/Oxford5000），其它词库直接是词名。"""
    if "Oxford3000" in data or "Oxford5000" in data:
        out: list[str] = []
        for section in ("Oxford3000", "Oxford5000"):
            if section in data:
                out.extend(data[section])
        return out
    return [k for k in data if k != "_meta"]


def main():
    ap = argparse.ArgumentParser(description="生成 data/definitions.json")
    ap.add_argument("--check", action="store_true", help="只报告覆盖情况，不写文件")
    args = ap.parse_args()

    if not ECDICT.exists():
        raise SystemExit(f"找不到 {ECDICT}，请先准备 ECDICT 原始文件。")

    index = load_ecdict(ECDICT)
    words = load_words()

    defs: dict[str, list] = {}
    missing: list[str] = []
    heads: Counter = Counter()
    for word in words:
        rec = find(index, word)
        if rec is None:
            missing.append(word)
            defs[word] = ["", []]
            continue
        grouped = group(raw_lines(rec["translation"]))
        heads.update(head for head, _ in grouped)
        defs[word] = [rec["phonetic"].strip(), grouped]

    no_phonetic = sum(1 for v in defs.values() if not v[0])
    print(f"词条 {len(words)} 个；匹配 {len(words) - len(missing)}，未匹配 {len(missing)}")
    print(f"音标为空 {no_phonetic}")
    print(f"使用到的头 {len(heads)} 种：{', '.join(h for h, _ in heads.most_common())}")
    if missing:
        print("未匹配：" + "、".join(missing))

    if args.check:
        return

    meta = {
        "source": "ECDICT  https://github.com/skywind3000/ECDICT",
        "license": "MIT",
        "format": {
            "单词": f"[音标, [[头, [释义…]], …]]；头为行首词性(如 vt.)或行首领域标签(如 [医])，无头归入 {OTHER}；未清洗"
        },
        "pos_map": POS_MAP,
        "note": f"收录 data/ 下词库去重后的词条，共 {len(words)} 个；数据来自 sources/ECDICT/ecdict.csv。",
    }
    # _meta 展开成多行，其余词条一行一条（与 data/ 下其它词库一致）
    meta_text = '  "_meta": ' + json.dumps(meta, ensure_ascii=False, indent=2).replace("\n", "\n  ")
    body = ",\n".join(
        f'  {json.dumps(word, ensure_ascii=False)}: {json.dumps(entry, ensure_ascii=False)}'
        for word, entry in defs.items()
    )
    OUT.write_text("{\n" + meta_text + ",\n" + body + "\n}\n", encoding="utf-8")
    print(f"已写入 {OUT.relative_to(ROOT)}（{OUT.stat().st_size / 1024:.0f} KB）")


if __name__ == "__main__":
    main()
