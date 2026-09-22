#!/usr/bin/env python3
"""从 Oxford 3000/5000 PDF 生成合并后的词库 JSON（data/en/Oxford.json）。

输入（sources/en/）：
    American_Oxford_3000.pdf + American_Oxford_5000.pdf  （美式）
    The_Oxford_3000.pdf      + The_Oxford_5000.pdf       （英式）

结构：{Oxford3000: {单词: {CEFR: [[词性, 同形区分?, 版本?], …]}}, Oxford5000: {...}}
    - 美式与英式相同 → 记录为 2 元素 [词性, 同形区分?]
    - 仅在一版或两版不同 → 记录为 3 元素 [词性, 同形区分, US/UK]
    - 词性均已拆成单一值；同形区分为空时省略

用法：
    uv run tools/oxford.py
"""
from __future__ import annotations

import json
import re
import subprocess
from collections import OrderedDict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "sources" / "en"
DATA = ROOT / "data" / "en"

_P = (
    r"(?:indefinite article|definite article|infinitive marker|auxiliary v\.?|modal v\.?"
    r"|noun\.?|exclam\.?|number|prep\.?|pron\.?|conj\.?|det\.?|adj\.?|adv\.?|n\.?|v\.?)"
)
_LB = r"(?<![A-Za-z])"
_LA = r"(?!(?-i:[a-z]))"  # 后面不是小写字母（放过粘着的大写 CEFR，如 adj.B1）
POS_RE = re.compile(rf"{_LB}{_P}{_LA}", re.I)
CEFR_RE = re.compile(r"^[ABC][12]$")
DOTTED = {"n", "v", "adj", "adv", "prep", "pron", "conj", "det", "exclam", "noun", "auxiliary v", "modal v"}

WORD_RE = re.compile(r"<word [^>]*>(.*?)</word>")
LINE_RE = re.compile(r"<line .*?</line>", re.S)
BLOCK_RE = re.compile(r"<block .*?</block>", re.S)
PAGE_RE = re.compile(r"<page .*?</page>", re.S)
HEADER_RE = re.compile(
    r"Oxford University Press|The Oxford 3000|The Oxford 5000|most important words to learn"
    r"|it includes an additional|which are listed here|^©|^\s*\d+\s*/\s*\d+\s*$"
)


def block_line_texts(pdf: Path) -> list[tuple[int, list[str]]]:
    """返回每个 block 的逐行文本（block 通常就是一列）。"""
    xml = subprocess.check_output(["pdftotext", "-bbox-layout", str(pdf), "-"]).decode("utf-8", "replace")
    out = []
    for page_i, pm in enumerate(PAGE_RE.finditer(xml)):
        for bm in BLOCK_RE.finditer(pm.group(0)):
            lines = []
            for lm in LINE_RE.finditer(bm.group(0)):
                words = [w.replace("\x08", "").strip() for w in WORD_RE.findall(lm.group(0))]
                words = [w for w in words if w]
                if words:
                    lines.append(" ".join(words))
            if lines:
                out.append((page_i, lines))
    return out


def norm_pos(tok: str) -> str:
    p = tok.lower().rstrip(".")
    if p == "noun":
        p = "n"
    return p + "." if p in DOTTED else p


def parse_rest(rest: str):
    leftover = re.sub(rf"{_LB}{_P}{_LA}|[ABC][12]|[/,]|\s", "", rest, flags=re.I)
    if leftover:
        return None
    tokens = re.findall(rf"{_LB}{_P}{_LA}|[ABC][12]|[/,]", rest, re.I)
    cur, recs = [], []
    for t in tokens:
        if CEFR_RE.match(t):
            recs.extend((pos, t) for pos in cur)
            cur = []
        elif t in "/,":
            continue
        else:
            cur.append(norm_pos(t))
    if cur or not recs:
        return None
    return recs


def parse_entry(text: str):
    """WORD [POS… CEFR]… → (word, [(pos, cefr), …])"""
    text = text.strip()
    for m in POS_RE.finditer(text):
        if m.start() == 0:
            continue
        word = text[: m.start()].strip()
        if not word:
            continue
        recs = parse_rest(text[m.start():])
        if recs:
            return word, recs
    return None


def split_word(w: str):
    """"lie 2 (tell a lie)"→("lie","tell a lie")；"close1"→("close","")"""
    w = re.sub(r"\s*\d+(?=\s*\(|$)", "", w).strip()
    m = re.match(r"^(.*?)\s*\((.*)\)$", w)
    return (m.group(1).strip(), m.group(2).strip()) if m else (w, "")


def parse_pdf(pdf: Path, source: str):
    words: dict[str, dict] = OrderedDict()
    warns: list[str] = []

    def emit(text: str) -> bool:
        text = text.strip()
        if not text or text.endswith(","):  # 行尾逗号 = 还没完，等下一行续
            return False
        parsed = parse_entry(text)
        if not parsed:
            return False
        word, recs = parsed
        word, sense = split_word(word)
        if not word or len(word) > 40:
            return False
        groups = words.setdefault(word, OrderedDict())
        for pos, cefr in recs:
            item = [pos, sense] if sense else [pos]
            bucket = groups.setdefault(cefr, [])
            if item not in bucket:
                bucket.append(item)
        return True

    for _, lines in block_line_texts(pdf):
        pending = None
        for text in lines:
            if HEADER_RE.search(text):
                if pending:
                    warns.append(pending)
                    pending = None
                continue
            if pending is not None:
                cand = pending + " " + text
                if emit(cand):
                    pending = None
                else:
                    pending = cand
                continue
            if emit(text):
                continue
            # 不能独立成条：残缺条目或“只有词、词性在下一行”
            if len(text) < 160 and re.search(r"[A-Za-z]", text):
                pending = text
        if pending:
            warns.append(pending)
    return words, warns


def build(pdf3: Path, pdf5: Path) -> OrderedDict:
    sections: OrderedDict = OrderedDict()
    for pdf, source in ((pdf3, "Oxford3000"), (pdf5, "Oxford5000")):
        parsed, warns = parse_pdf(pdf, source)
        print(f"  {source}: {len(parsed)} 词" + (f"，残留 {len(warns)}: {warns}" if warns else ""))
        sections[source] = parsed
    return sections


def merge(us: OrderedDict, uk: OrderedDict) -> OrderedDict:
    """合并美式/英式：两版相同则原样，否则记录带第 3 元素 US/UK。"""
    out: OrderedDict = OrderedDict()
    for section in ("Oxford3000", "Oxford5000"):
        sec: OrderedDict = OrderedDict()
        uws, kws = us.get(section, {}), uk.get(section, {})
        for word in sorted(set(uws) | set(kws)):
            if word in uws and word in kws and uws[word] == kws[word]:
                sec[word] = uws[word]  # 两版相同，保持 2 元素记录
                continue
            merged: OrderedDict = OrderedDict()
            for ed, src in (("US", uws), ("UK", kws)):
                if word not in src:
                    continue
                for cefr, items in src[word].items():
                    for it in items:
                        pos = it[0]
                        sense = it[1] if len(it) > 1 else ""
                        bucket = merged.setdefault(cefr, [])
                        rec = [pos, sense, ed]
                        if rec not in bucket:
                            bucket.append(rec)
            sec[word] = merged
        out[section] = sec
    return out


def write_json(path: Path, sections: OrderedDict):
    all_words = set()
    for words in sections.values():
        all_words |= set(words)
    meta = {
        "source": "The Oxford 3000™ & The Oxford 5000™ (American & British English)",
        "format": {
            "Oxford3000": "{单词: {CEFR: [[词性, 同形区分?, 版本?], …]}}；"
            "2 元素记录 = 美英相同，3 元素第 3 位 US/UK = 仅该版或两版不同",
            "Oxford5000": "同上",
        },
        "categories": ["A1", "A2", "B1", "B2", "C1"],
        "note": "Oxford3000 = A1–B2，Oxford5000 = B2–C1 扩展；美式与英式已合并。"
        f"共 {len(all_words)} 个词。",
    }
    parts = ['  "_meta": ' + json.dumps(meta, ensure_ascii=False, indent=2).replace("\n", "\n  ")]
    for section, words in sections.items():
        body = ",\n".join(
            f"    {json.dumps(w, ensure_ascii=False)}: {json.dumps(v, ensure_ascii=False)}" for w, v in words.items()
        )
        parts.append(f"  {json.dumps(section)}: {{\n{body}\n  }}")
    path.write_text("{\n" + ",\n".join(parts) + "\n}\n", encoding="utf-8")
    print(f"已写入 {path.relative_to(ROOT)}（{len(all_words)} 个词）")


def main():
    print("美式：")
    us = build(SRC / "American_Oxford_3000.pdf", SRC / "American_Oxford_5000.pdf")
    print("英式：")
    uk = build(SRC / "The_Oxford_3000.pdf", SRC / "The_Oxford_5000.pdf")
    write_json(DATA / "Oxford.json", merge(us, uk))


if __name__ == "__main__":
    main()
