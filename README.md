# 词库 Wordlists

[English](README.en.md) | **中文**

```
wordlists/
├── data/       # 词库 JSON（输入词表在 archive/，输出在各自目录下）
│   ├── en/     # 英文
│   │   ├── archive/
│   │   │   ├── CET.json
│   │   │   ├── Oxford.json               # Oxford（美式 & 英式）
│   │   │   └── 义务教育-普通高中.json
│   │   ├── definitions.json          # 英文释义 + 音标（ECDICT）
│   │   └── categories.json           # 英文词 -> [类别]
│   └── zh/     # 中文
│       ├── archive/
│       │   ├── HSK词汇.json              # HSK 词汇大纲
│       │   ├── HSK汉字.json              # HSK 汉字大纲
│       │   ├── 字义.json                 # 字级释义（Unihan，中间产物）
│       │   └── 粤拼.json                 # 汉字粤拼（rime + Unihan，中间产物）
│       ├── definitions.json          # 拼音 + 粤拼 + 英文释义
│       └── categories.json           # 字/词 -> [HSK 等级 R/W]
├── sources/    # 原始来源
│   ├── en/
│   │   ├── ECDICT/                               # ECDICT 原始数据（ecdict.csv, LICENSE）
│   │   ├── The_Oxford_3000.pdf                   # 英式
│   │   ├── The_Oxford_5000.pdf
│   │   ├── American_Oxford_3000.pdf              # 美式
│   │   ├── American_Oxford_5000.pdf
│   │   ├── 《全国大学英语四、六级考试大纲（2016年修订版）》.pdf
│   │   ├── 普通高中英语课程标准日常修订版（2017年版2025年修订）.pdf
│   │   └── 义务教育英语课程标准日常修订版（2022年版2025年修订）.pdf
│   └── zh/
│       ├── 新版HSK考试大纲1219.pdf
│       ├── cedict_ts.u8                          # CC-CEDICT 原始数据
│       ├── Unihan.zip                            # Unihan 原始数据
│       └── UNICODE_LICENSE.txt                   # Unicode License V3
├── assets/     # 生成的图表
│   ├── counts-en-light.png
│   ├── counts-en-dark.png
│   ├── counts-zh-light.png
│   └── counts-zh-dark.png
├── tools/      # 脚本
│   ├── counts.py     # 统计 / 出图
│   ├── oxford.py     # 解析 Oxford PDF，生成两版词库
│   ├── defs.py       # 生成 definitions.json
│   ├── categories.py # 生成 categories.json（en）
│   ├── hsk.py        # 解析 HSK PDF，生成词汇/汉字
│   ├── zh_defs.py    # 生成中文英文释义 / 字义
│   ├── zh_jyutping.py # 生成汉字粤拼
│   └── zh_categories.py # 生成 categories.json（zh）
└── README.md
```

## 词表规模

### 英文

<!-- counts-en:start -->
| 词表 | 词条数 | 来源 |
| --- | --: | --- |
| CET 四 / 六级 | 5,346 | 《全国大学英语四、六级考试大纲（2016年修订版）》 |
| Oxford 3000 / 5000 | 5,062 | The Oxford 3000™ & 5000™（美式 & 英式） |
| 义务教育 · 普通高中 | 3,099 | 《普通高中英语课程标准（2017年版2025年修订）》 |

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/counts-en-dark.png">
  <img alt="英文词表词条数" src="assets/counts-en-light.png" width="540">
</picture>
<!-- counts-en:end -->

### 中文

<!-- counts-zh:start -->
| 词表 | 词条数 | 来源 |
| --- | --: | --- |
| HSK 词汇 | 10,896 | 《HSK 考试大纲》词汇大纲 |
| HSK 汉字 | 3,088 | 《HSK 考试大纲》汉字大纲 |

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/counts-zh-dark.png">
  <img alt="中文词表词条数" src="assets/counts-zh-light.png" width="540">
</picture>
<!-- counts-zh:end -->

## 词库格式

词表文件都在 `data/{en,zh}/archive/` 下，按「段」分节：顶层是段名，段内是 `单词 -> 数据`。

| 文件 | 段 | 每词的值 |
| --- | --- | --- |
| `CET.json` | `CET4` / `CET6` | `[派生词, 拼写变体]` |
| `Oxford.json` | `Oxford3000` / `Oxford5000` | `{CEFR: [[词性, 同形区分?, 版本?], …]}` |
| `义务教育-普通高中.json` | `义务教育` / `必修` / `选择性必修` | `[其他形式]` |
| `HSK词汇.json` | `一级`…`七—九级` | `[[拼音, 词性], …]` |
| `HSK汉字.json` | `一级认读字`…`七—九级书写字` | `[汉字, …]` |

- 同时在多段的词会在各段各出现一次（如 CET 的 4 个四级六级共有词）。
- Oxford 记录第 3 位为版本（`US`/`UK`），缺省表示美英相同；美式与英式已合并为一个文件。
- 「普通高中 = 必修 + 选择性必修」的分组写在 `_meta.groups`。
- 每个文件的 `_meta.format` 也都有说明。

## 类别索引

`data/{en,zh}/categories.json` 汇总各语言词库的类别，结构为 `词/字 -> [类别, …]`。

英语（`data/en/categories.json`）：

```json
"bank":    ["CET4", "Oxford3000", "义务教育", "A1", "B1"],
"analyse": ["Oxford3000", "选择性必修", "B1"],
"analyze": ["CET4", "Oxford3000", "A2"]
```

- 类别：`CET4` `CET6` `Oxford3000` `Oxford5000` `义务教育` `必修` `选择性必修` `A1`–`C1`
- Oxford 区分美式 `-US` / 英式 `-UK`；CEFR 也计入类别。

中文（`data/zh/categories.json`）：

```json
"爱":   ["HSK1", "HSK1R", "HSK1W", "HSK2W"],
"行":   ["HSK3", "HSK3R", "HSK3W", "HSK5"],
"银行": ["HSK3"]
```

- 类别：词 `HSK1`–`HSK7-9`；认读字 `HSK{n}R`；书写字 `HSK{n}W`（「一级~二级书写字」展开为 `HSK1W`+`HSK2W`）。

## 释义

### 英文 · `data/en/definitions.json`

`data/en/definitions.json` 收录上面四个英文词表的**去重词条**（7,008 个），给出**音标**和**中文释义**。
释义取自 [ECDICT](https://github.com/skywind3000/ECDICT)（MIT License），原始数据在 `sources/ECDICT/ecdict.csv`。
（ECDICT 为英汉词典，**不含 HSK 中文词/字**。）

每个词的格式为 `[音标, [[头, [释义…]], …]]`：

```json
"abandon": ["ә'bændәn", [["vt.", ["放弃, 抛弃, 遗弃, 使屈从, 沉溺, 放纵"]], ["n.", ["放任, 无拘束, 狂热"]]]],
"bank":    ["bæŋk", [["n.", ["银行, 堤, 岸"]], ["[医]", ["库"]]]],
"run":     ["rʌn", [["n.", ["跑, …"]], ["vi.", ["跑, …"]], ["vt.", ["使跑, …"]], ["a.", ["熔化的, …"]], ["其它", ["run的过去式和过去分词"]], ["[计]", ["运行"]]]]
```

- **头**按 ECDICT 释义行的行首判断：
  - 词性（`vt.` `vi.` `n.` `a.` `adv.` …）原样保留；
  - `vt.vi.` / `vi.vt.`（及物、不及物均可）归为 `v.`；
  - 领域标签（`[计]` `[医]` `[法]` `[经]` `[化]` …）原样保留；
  - 两者都没有的归入 `其它`。
- 行内出现的方括号（如 `交感[作用]`、`[疾]病`）保留在释义正文里，不拆。
- 未做清洗，专业领域义项、`run的过去式和过去分词` 之类的说明行都原样保留。
- `_meta.pos_map` 给出与 Oxford 词性口径的对照（`vt.`/`vi.`→`v.`、`a.`→`adj.`、`num.`→`number` …），方便和 `Oxford.json` 对表。

### 中文 · `data/zh/definitions.json`

`data/zh/definitions.json` 收录 HSK 词汇与汉字的**并集**（12,481 条），给出**拼音、粤拼**和**英文释义**。
每个字/词的格式为 `[[拼音, 粤拼, [英文释义…]], …]`：

```json
"爱":   [["ài", "oi3", ["love, be fond of, like"]]],
"行":   [["xíng", "hang4", ["go; walk; move, travel; circulate; Kangxi radical 144"]], ["háng", "hong4", ["go; walk; move, travel; circulate; Kangxi radical 144"]]],
"弟":   [["dì", "dai6", ["young brother; junior; I, me"]], ["tì", "tai5", ["young brother; junior; I, me"]]],
"银行": [["yínháng", "ngan4 hong4", ["bank", "CL:家[jia1],個|个[ge4]"]]]
```

- **拼音**优先 HSK 大纲（多字词全部、及部分字），只在 HSK 汉字、不在词汇里的字回退 CC-CEDICT；
- **粤拼**（Jyutping）：字取 `archive/粤拼.json`，词优先 rime-cantonese 整词、否则逐字拼；
- **释义**：都用 CC-CEDICT（每个读音各自一组），仅当某读音没有 CC-CEDICT 释义时才用 Unihan `kDefinition` 兜底；`(bound form)`、`CL:個|个[ge4]`、`variant of …` 等原样保留。

`data/zh/archive/字义.json` 另收 HSK 汉字的**字级**英文释义（3,088 字），取自
[Unihan](https://www.unicode.org/Public/UCD/latest/ucd/Unihan.zip)（Unicode License V3，MIT 兼容）的 `kDefinition`，
格式为 `字 -> 英文 gloss`：

```json
"爱": "love, be fond of, like",
"专": "monopolize, take sole possession"
```

- kDefinition 简略、偏字源，字级参考用；`definitions.json` 里单字的释义直接取它。

`data/zh/archive/粤拼.json` 收 HSK 汉字的**普通话拼音 -> 粤拼(Jyutping)** 对照（3,088 字），
用 [rime-cantonese](https://github.com/rime/rime-cantonese)（CC BY 4.0 / ODbL 1.0）的词条做逐音节对齐，
缺证据的读音按序取 rime 字表未用读音，再用 Unihan `kCantonese` 兜底，格式为 `字 -> {拼音: 粤拼}`：

```json
"行": {"háng": "hong4", "héng": "hang6", "xíng": "hang4"},
"弟": {"dì": "dai6", "tì": "tai5"}
```

- 用 CC-CEDICT 的**词**与 rime 的**词**逐音节对齐得到字级映射（共 53,841 个词参与）；
- 共 4,106 条 `拼音->粤拼`（3,088 字），绝大多数来自对齐，少量用 rime 字表/Unihan 补。

重新生成：

```bash
uv run tools/oxford.py         # 从 sources/ 的 Oxford PDF 重新生成两版词库
uv run tools/defs.py           # 读取 sources/ECDICT/ecdict.csv，刷新 data/definitions.json
uv run tools/defs.py --check   # 只报告覆盖情况，不写文件
uv run tools/categories.py     # 刷新 data/categories.json
uv run tools/hsk.py            # 从 sources/ 的 HSK PDF 生成 data/zh/archive/HSK词汇.json、HSK汉字.json
uv run tools/zh_jyutping.py    # 先跑：生成 data/zh/archive/粤拼.json
uv run tools/zh_defs.py        # 再跑：生成 data/zh/definitions.json、data/zh/archive/字义.json
uv run tools/zh_defs.py --check
uv run tools/zh_categories.py   # 刷新 data/zh/categories.json
```

## 许可 License

本项目自行整理的部分（JSON 数据结构、数据处理、文档）采用 [MIT](LICENSE) 许可证。

- `data/definitions.json` 的释义与音标来自 [ECDICT](https://github.com/skywind3000/ECDICT)，采用 MIT 许可证。
- `data/zh/definitions.json` 的英文释义来自 [CC-CEDICT](https://www.mdbg.net/chinese/dictionary?page=cc-cedict)，
  采用 **CC BY-SA 4.0**（署名—相同方式共享）；该文件的释义部分按 CC BY-SA 4.0 发布。
- `data/zh/archive/字义.json` 的字义来自 [Unihan](https://www.unicode.org/Public/UCD/latest/ucd/Unihan.zip)（Unicode, Inc.），
  采用 Unicode License V3（宽松许可，与 MIT 兼容）。
- `data/zh/archive/粤拼.json` 的粤拼来自 [rime-cantonese](https://github.com/rime/rime-cantonese)
  （CC BY 4.0 / ODbL 1.0），Unihan 兜底部分采用 Unicode License V3。
- `sources/` 中的 PDF 及其中词表内容的版权归原作者 / 出版机构所有
  （如 The Oxford 3000/5000 归 Oxford University Press，课程标准和考试大纲归相应教育机构），
  本项目仅出于学习研究目的收录，不主张任何权利。如需商用，请自行向权利人获取授权。
