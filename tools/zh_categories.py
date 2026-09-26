#!/usr/bin/env python3
"""汇总 data/zh/archive 下 HSK 词表与汉字表的等级/类型，生成 data/zh/categories.json。

类别：
    词汇（HSK词汇.json 段：一级 … 七—九级）        -> HSK{n}          （n = 1..6 或 7-9）
    认读字（HSK汉字.json 段：…认读字）              -> HSK{n}R
    书写字（HSK汉字.json 段：…书写字）              -> HSK{n}W
        「一级~二级书写字」展开为 HSK1W 与 HSK2W

结构：字/词 -> [类别, …]

用法：
    uv run tools/zh_categories.py
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "zh"
ARCHIVE = DATA / "archive"
OUT = DATA / "categories.json"

LEVEL = {
    "一级": "HSK1",
    "二级": "HSK2",
    "三级": "HSK3",
    "四级": "HSK4",
    "五级": "HSK5",
    "六级": "HSK6",
    "七—九级": "HSK7-9",
}
LEVEL_ORDER = list(LEVEL.values())
CATEGORY_ORDER = [f"{tag}{suffix}" for tag in LEVEL_ORDER for suffix in ("", "R", "W")]


def sections(section: str) -> list[str]:
    """段名 -> [类别…]（一个段可能对应多个等级，如「一级~二级书写字」）。"""
    if section.endswith("认读字"):
        base, suffix = section[:-3], "R"
    elif section.endswith("书写字"):
        base, suffix = section[:-3], "W"
    else:
        base, suffix = section, ""
    parts = [p.strip() for p in base.split("~")] if "~" in base else [base]
    return [f"{LEVEL[p]}{suffix}" for p in parts if p in LEVEL]


def collect() -> dict[str, set[str]]:
    cats: dict[str, set[str]] = {}

    def add(item: str, categories: list[str]):
        bucket = cats.setdefault(item, set())
        bucket.update(categories)

    vocab = json.loads((ARCHIVE / "HSK词汇.json").read_text(encoding="utf-8"))
    for section, words in vocab.items():
        if section.startswith("_"):
            continue
        for word in words:
            add(word, sections(section))

    hanzi = json.loads((ARCHIVE / "HSK汉字.json").read_text(encoding="utf-8"))
    for section, chars in hanzi.items():
        if section.startswith("_"):
            continue
        for ch in chars:
            add(ch, sections(section))

    return cats


def main():
    cats = collect()
    ordered = {w: [c for c in CATEGORY_ORDER if c in cs] for w, cs in cats.items()}
    meta = {
        "source": "汇总 data/zh/archive 下 HSK 词汇表与汉字表的等级/类型",
        "format": {"字/词": ["类别", "…"]},
        "categories": CATEGORY_ORDER,
        "note": f"字/词为 HSK 词汇与汉字的并集，共 {len(ordered)} 个；"
        "词 -> HSK{n}，认读字 -> HSK{n}R，书写字 -> HSK{n}W。",
    }
    meta_text = '  "_meta": ' + json.dumps(meta, ensure_ascii=False, indent=2).replace("\n", "\n  ")
    body = ",\n".join(
        f"  {json.dumps(w, ensure_ascii=False)}: {json.dumps(v, ensure_ascii=False)}" for w, v in ordered.items()
    )
    OUT.write_text("{\n" + meta_text + ",\n" + body + "\n}\n", encoding="utf-8")
    print(f"已写入 {OUT.relative_to(ROOT)}（{len(ordered)} 字/词，{len(CATEGORY_ORDER)} 个类别）")


if __name__ == "__main__":
    main()
