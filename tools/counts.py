#!/usr/bin/env python3
"""统计 data/ 下各词库的词条数，生成 Markdown 表格与柱状图。

用法：
    uv run --with matplotlib tools/counts.py

输出：
    - 更新 README.md 中 <!-- counts:start --> … <!-- counts:end --> 区块
    - 生成 assets/counts-light.png 与 assets/counts-dark.png（适配 GitHub 主题）
"""
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
ASSETS = ROOT / "assets"
README = ROOT / "README.md"

# data/ 下非词库的辅助 JSON（不参与词条统计）
SKIP = {"definitions.json"}

# 展示用名称与来源
LABELS = {
    "CET.json": ("CET 四 / 六级", "《全国大学英语四、六级考试大纲（2016年修订版）》"),
    "Oxford3000-5000-US.json": ("Oxford 3000 / 5000（美式）", "The Oxford 3000™ & 5000™ (American English)"),
    "Oxford3000-5000-UK.json": ("Oxford 3000 / 5000（英式）", "The Oxford 3000™ & 5000™ (British English)"),
    "义务教育-普通高中.json": ("义务教育 · 普通高中", "《普通高中英语课程标准（2017年版2025年修订）》"),
}

# 配色取自 GitHub Primer（浅色 / 深色主题）
THEMES = {
    "light": {"bg": "#FFFFFF", "accent": "#3B82F6", "ink": "#1F2937", "muted": "#57606A"},
    "dark": {"bg": "#0D1117", "accent": "#58A6FF", "ink": "#E6EDF3", "muted": "#8B949E"},
}

FONT = "Noto Sans CJK SC"

# 中文字体
for path in ("/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc",):
    if Path(path).exists():
        font_manager.fontManager.addfont(path)
plt.rcParams["font.sans-serif"] = [FONT, "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False


def count_entries(path: Path) -> int:
    data = json.loads(path.read_text(encoding="utf-8"))
    if "words" in data:  # 形如 {"words": {...}}
        return len(data["words"])
    return len(data) - (1 if "_meta" in data else 0)


def table_block(rows) -> str:
    lines = ["| 词表 | 词条数 | 来源 |", "| --- | --: | --- |"]
    for label, n, src in rows:
        lines.append(f"| {label} | {n:,} | {src} |")
    return "\n".join(lines)


def render_chart(rows, out: Path, theme):
    rows = list(reversed(rows))            # 最大值放顶部
    labels = [r[0] for r in rows]
    counts = [r[1] for r in rows]
    y = list(range(len(rows)))

    fig, ax = plt.subplots(figsize=(6.4, 0.5 * len(rows) + 0.5), dpi=180)
    fig.patch.set_facecolor(theme["bg"])
    ax.set_facecolor(theme["bg"])

    bars = ax.barh(y, counts, height=0.42, color=theme["accent"])
    ax.bar_label(bars, labels=[f"{c:,}" for c in counts],
                 padding=6, fontsize=10, fontweight="bold", color=theme["ink"])

    ax.set_yticks(y, labels)
    ax.set_xlim(0, max(counts) * 1.18)
    ax.set_xticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.tick_params(axis="y", length=0, labelsize=10, colors=theme["muted"])
    ax.set_ylim(-0.6, len(rows) - 0.4)

    ASSETS.mkdir(exist_ok=True)
    fig.tight_layout(pad=0.4)
    fig.savefig(out, format="png", facecolor=theme["bg"])
    plt.close(fig)


def update_readme(block: str):
    text = README.read_text(encoding="utf-8")
    start = "<!-- counts:start -->"
    end = "<!-- counts:end -->"
    picture = (
        '<picture>\n'
        '  <source media="(prefers-color-scheme: dark)" srcset="assets/counts-dark.png">\n'
        '  <img alt="各词表词条数" src="assets/counts-light.png" width="540">\n'
        '</picture>'
    )
    if start in text and end in text:
        head, rest = text.split(start, 1)
        _, tail = rest.split(end, 1)
        text = f"{head}{start}\n{block}\n\n{picture}\n{end}{tail}"
    README.write_text(text, encoding="utf-8")


def main():
    rows = []
    for path in sorted(DATA.glob("*.json")):
        if path.name in SKIP:
            continue
        label, src = LABELS.get(path.name, (path.stem, ""))
        rows.append((label, count_entries(path), src))
    rows.sort(key=lambda r: r[1], reverse=True)

    for name, theme in THEMES.items():
        render_chart(rows, ASSETS / f"counts-{name}.png", theme)
    update_readme(table_block(rows))
    print(table_block(rows))
    print(f"\n已生成 assets/counts-light.png、assets/counts-dark.png，并更新 README.md")


if __name__ == "__main__":
    main()
