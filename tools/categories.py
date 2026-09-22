#!/usr/bin/env python3
"""汇总 data/ 下各词库的段类别与 CEFR，生成 data/categories.json（词 -> [类别…]）。

- 段名即类别：CET4/CET6、义务教育/必修/选择性必修
- Oxford 区分美英，段名带后缀：Oxford3000-US、Oxford5000-UK 等
- Oxford 的 CEFR（A1–C1）也算类别
- 只保留词与类别，不含音标/词性/释义

用法：
    uv run tools/categories.py
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
OUT = DATA / "categories.json"

SKIP = {"definitions.json", "categories.json", "HSK词汇.json", "HSK汉字.json"}
# Oxford 文件 → 段后缀（区分美英）
OXFORD_SUFFIX = {"Oxford3000-5000-US.json": "-US", "Oxford3000-5000-UK.json": "-UK"}
CATEGORY_ORDER = [
    "CET4",
    "CET6",
    "Oxford3000-US",
    "Oxford5000-US",
    "Oxford3000-UK",
    "Oxford5000-UK",
    "义务教育",
    "必修",
    "选择性必修",
    "A1",
    "A2",
    "B1",
    "B2",
    "C1",
]


def collect() -> dict[str, set[str]]:
    cats: dict[str, set[str]] = {}
    for path in sorted(DATA.glob("*.json")):
        if path.name in SKIP:
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        data.pop("_meta", None)
        suffix = OXFORD_SUFFIX.get(path.name, "")
        for section, words in data.items():
            for word, value in words.items():
                bucket = cats.setdefault(word, set())
                if isinstance(value, dict):  # Oxford：段名加后缀，并把 CEFR 也算进去
                    bucket.add(section + suffix)
                    bucket.update(value)
                else:  # CET / 义务教育·普通高中
                    bucket.add(section)
    return cats


def main():
    cats = collect()
    ordered = {w: [c for c in CATEGORY_ORDER if c in cs] for w, cs in cats.items()}
    meta = {
        "source": "汇总 data/ 下各词库的段类别与 CEFR",
        "format": {"单词": ["类别", "…"]},
        "categories": CATEGORY_ORDER,
        "note": f"词为各词库并集，共 {len(ordered)} 个；Oxford 区分美式(-US)/英式(-UK)，CEFR（A1–C1）也计入类别。",
    }
    meta_text = '  "_meta": ' + json.dumps(meta, ensure_ascii=False, indent=2).replace("\n", "\n  ")
    body = ",\n".join(
        f"  {json.dumps(w, ensure_ascii=False)}: {json.dumps(v, ensure_ascii=False)}" for w, v in ordered.items()
    )
    OUT.write_text("{\n" + meta_text + ",\n" + body + "\n}\n", encoding="utf-8")
    print(f"已写入 {OUT.relative_to(ROOT)}（{len(ordered)} 词，{len(CATEGORY_ORDER)} 个类别）")


if __name__ == "__main__":
    main()
