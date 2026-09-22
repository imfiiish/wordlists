#!/usr/bin/env python3
"""从《HSK 考试大纲》PDF 生成 data/HSK词汇.json 与 data/HSK汉字.json。

词汇大纲表格：序号 | 等级 | 词语 | 拼音 | 词性
    - 等级含括号表示跨级，如 1（4）；词性里对应的括号给出该级词性
    - 词尾数字是同形词编号（本1/本2），解析时去掉
    - 值 = [[拼音, 词性], …]（同一 (段, 词) 可能有同音异义的多条）

汉字大纲：各等级的「认读字」「书写字」（书写字一级二级合并）。
    - 值 = [汉字, …]

用法：
    uv run tools/hsk.py
"""
from __future__ import annotations

import json
import re
import subprocess
from collections import OrderedDict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PDF = ROOT / "sources" / "新版HSK考试大纲1219.pdf"
VOCAB_OUT = ROOT / "data" / "zh" / "HSK词汇.json"
HANZI_OUT = ROOT / "data" / "zh" / "HSK汉字.json"

VOCAB_PAGES = (79, 354)  # 0-based，含头不含尾
HANZI_PAGES = (354, 384)
LEVELS = {"1": "一级", "2": "二级", "3": "三级", "4": "四级", "5": "五级", "6": "六级", "7-9": "七—九级"}


def pdf_pages() -> list[str]:
    out = subprocess.check_output(
        ["pdftotext", "-layout", str(PDF), "-"], stderr=subprocess.DEVNULL
    ).decode("utf-8", "replace")
    return out.split("\f")


def split_cells(line: str) -> list[str]:
    return [x.strip() for x in re.split(r"\s{2,}", line.rstrip())]


def parse_vocab(pages: list[str]) -> OrderedDict:
    sections: OrderedDict = OrderedDict((lv, OrderedDict()) for lv in LEVELS.values())

    def add(level: str, word: str, pinyin: str, pos: str):
        if level not in LEVELS or not word:
            return
        bucket = sections[LEVELS[level]].setdefault(word, [])
        rec = [pinyin, pos]
        if rec not in bucket:
            bucket.append(rec)

    for page in pages:
        for line in page.split("\n"):
            f = split_cells(line)
            if len(f) < 4 or not re.fullmatch(r"\d+", f[0]) or not re.fullmatch(r"[\d（）()\-]+", f[1]):
                continue
            grade, word = f[1], f[2]
            pinyin = f[3] if len(f) > 3 else ""
            pos = f[4] if len(f) > 4 else ""
            word = re.sub(r"\d+$", "", word)  # 去掉同形词编号
            primary = re.split(r"[（(]", grade)[0].strip()
            extras = re.findall(r"[（(]([^（）()]+)[）)]", grade)
            unpar = [p for p in re.split(r"[、,]", re.sub(r"[（(][^（）()]*[）)]", "", pos)) if p]
            pars = re.findall(r"[（(]([^（）()]*)[）)]", pos)
            add(primary, word, pinyin, "、".join(unpar))
            for i, extra in enumerate(extras):
                add(extra.strip(), word, pinyin, pars[i] if i < len(pars) else "")
    return sections


def parse_hanzi(pages: list[str]) -> OrderedDict:
    sections: OrderedDict = OrderedDict()
    numbered: dict[str, dict[int, str]] = {}
    current = None
    header = re.compile(r"HSK（([^）]+)）(?:~（([^）]+)）)?(认读字|书写字)")
    for page in pages:
        for line in page.split("\n"):
            m = header.search(line)
            if m:
                name = m.group(1) + (f"~{m.group(2)}" if m.group(2) else "") + m.group(3)
                current = name
                numbered.setdefault(current, {})
                continue
            if current is None:
                continue
            for num, chars in re.findall(r"(\d+)\.\s*([\u4e00-\u9fff]+)", line):
                for i, ch in enumerate(chars):
                    numbered[current][int(num) + i] = ch
    for name, d in numbered.items():
        sections[name] = [d[n] for n in sorted(d)]
    return sections


def write_json(path: Path, meta: dict, sections: OrderedDict):
    parts = ['  "_meta": ' + json.dumps(meta, ensure_ascii=False, indent=2).replace("\n", "\n  ")]
    for section, body in sections.items():
        if isinstance(body, dict):  # 词汇：一条（词）一行
            lines = ",\n".join(
                f"    {json.dumps(w, ensure_ascii=False)}: {json.dumps(v, ensure_ascii=False)}" for w, v in body.items()
            )
            parts.append(f"  {json.dumps(section, ensure_ascii=False)}: {{\n{lines}\n  }}")
        else:  # 汉字：一条（字）一行
            lines = ",\n".join(f"    {json.dumps(x, ensure_ascii=False)}" for x in body)
            parts.append(f"  {json.dumps(section, ensure_ascii=False)}: [\n{lines}\n  ]")
    path.write_text("{\n" + ",\n".join(parts) + "\n}\n", encoding="utf-8")
    print(f"已写入 {path.relative_to(ROOT)}")


def main():
    pages = pdf_pages()
    vocab = parse_vocab(pages[VOCAB_PAGES[0]:VOCAB_PAGES[1]])
    words = {w for sec in vocab.values() for w in sec}
    vocab_meta = {
        "source": "《HSK 考试大纲》（2025-11 发布 / 2026-07 实施）词汇大纲",
        "format": {"一级": "{词语: [[拼音, 词性], …]}", "…": "同上"},
        "categories": list(LEVELS.values()),
        "note": f"跨级词在对应各级各出现一次；同形词（如 花1/花2）已去掉编号合并为多条记录。去重后 {len(words)} 个词。",
    }
    write_json(VOCAB_OUT, vocab_meta, vocab)

    hanzi = parse_hanzi(pages[HANZI_PAGES[0]:HANZI_PAGES[1]])
    hanzi_meta = {
        "source": "《HSK 考试大纲》汉字大纲",
        "format": {"一级认读字": "[汉字, …]", "…": "同上"},
        "categories": list(hanzi),
        "note": "认读字按等级；书写字一级、二级合并为「一级~二级书写字」。",
    }
    write_json(HANZI_OUT, hanzi_meta, hanzi)

    for lv, sec in vocab.items():
        print(f"  {lv}: {len(sec)} 词")
    for name, chars in hanzi.items():
        print(f"  {name}: {len(chars)} 字")


if __name__ == "__main__":
    main()
