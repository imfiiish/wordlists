#!/usr/bin/env python3
"""从 Oxford 3000/5000 PDF 生成美式 / 英式两个词库 JSON。

输入（sources/）：
    American_Oxford_3000.pdf + American_Oxford_5000.pdf  → data/Oxford3000-5000-US.json
    The_Oxford_3000.pdf      + The_Oxford_5000.pdf       → data/Oxford3000-5000-UK.json

结构：单词 -> {来源: {CEFR: [[词性, 同形区分?], …]}}
    - 来源 = Oxford3000 / Oxford5000
    - 词性均已拆成单一值（det./pron. 拆成 det.、pron.）
    - 同形区分为空时省略（如 bank 的 money/river）
PDF 里词性与 CEFR 可能粘连（adj.B1）或缺点（n, / n B2），解析时已归一。

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
SRC = ROOT / "sources"
DATA = ROOT / "data"

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
    words: OrderedDict = OrderedDict()
    for pdf, source in ((pdf3, "Oxford3000"), (pdf5, "Oxford5000")):
        parsed, warns = parse_pdf(pdf, source)
        print(f"  {source}: {len(parsed)} 词" + (f"，残留 {len(warns)}: {warns}" if warns else ""))
        for word, groups in parsed.items():
            words.setdefault(word, OrderedDict())[source] = groups
    return words


def write_json(path: Path, words: OrderedDict, edition: str):
    meta = {
        "source": f"The Oxford 3000™ & The Oxford 5000™ ({edition})",
        "format": {"单词": "{来源: {CEFR: [[词性, 同形区分?], …]}}；同形区分为空时省略；词性均为单一值"},
        "categories": ["Oxford3000", "Oxford5000", "A1", "A2", "B1", "B2", "C1"],
        "note": f"{edition} 版；Oxford3000 = A1–B2，Oxford5000 = B2–C1 扩展。共 {len(words)} 个词。",
    }
    meta_text = '  "_meta": ' + json.dumps(meta, ensure_ascii=False, indent=2).replace("\n", "\n  ")
    body = ",\n".join(
        f"  {json.dumps(w, ensure_ascii=False)}: {json.dumps(v, ensure_ascii=False)}" for w, v in words.items()
    )
    path.write_text("{\n" + meta_text + ",\n" + body + "\n}\n", encoding="utf-8")
    print(f"已写入 {path.relative_to(ROOT)}（{len(words)} 词）")


def main():
    print("美式：")
    us = build(SRC / "American_Oxford_3000.pdf", SRC / "American_Oxford_5000.pdf")
    print("英式：")
    uk = build(SRC / "The_Oxford_3000.pdf", SRC / "The_Oxford_5000.pdf")
    write_json(DATA / "Oxford3000-5000-US.json", us, "American English")
    write_json(DATA / "Oxford3000-5000-UK.json", uk, "British English")


if __name__ == "__main__":
    main()
