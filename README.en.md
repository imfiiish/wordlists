# Wordlists

**English** | [中文](README.md)

A small collection of vocabulary lists for learners of **Chinese (HSK)** and **English (Oxford)**,
extracted from official exam syllabi. Each wordlist is a plain JSON file, grouped by section.

Focused here on the internationally useful lists: **HSK** (Chinese) and **Oxford 3000 / 5000** (English).
China-specific exam lists (CET, the compulsory/high-school English curriculum) live in the same repo and are
described in the [Chinese README](README.md).

```
wordlists/
├── data/
│   ├── en/                           # English
│   │   ├── archive/                  #   wordlists (input)
│   │   │   └── Oxford.json           #   Oxford 3000 / 5000 (American & British)
│   │   ├── definitions.json          # Chinese glosses + IPA (from ECDICT)
│   │   └── categories.json           # word -> [categories]
│   └── zh/                           # Chinese
│       ├── archive/                  #   intermediate / input
│       │   ├── HSK词汇.json          #   HSK vocabulary (pinyin + part of speech)
│       │   ├── HSK汉字.json          #   HSK characters (recognition / writing)
│       │   ├── 字义.json             #   Character glosses (Unihan)
│       │   └── 粤拼.json             #   Character Jyutping (rime + Unihan)
│       ├── definitions.json          # pinyin + jyutping + English glosses
│       └── categories.json           # character/word -> [HSK level]
├── sources/{en,zh}/                  # source PDFs and raw data
├── assets/                           # generated charts
└── tools/                            # generator scripts
```

## Wordlist sizes

### English

<!-- counts-en:start -->
| List | Entries | Source |
| --- | --: | --- |
| Oxford 3000 / 5000 | 5,062 | The Oxford 3000™ & 5000™ (American & British English) |

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/counts-en-intl-dark.png">
  <img alt="Oxford wordlist sizes" src="assets/counts-en-intl-light.png" width="540">
</picture>
<!-- counts-en:end -->

### Chinese

<!-- counts-zh:start -->
| List | Entries | Source |
| --- | --: | --- |
| HSK Vocabulary | 10,896 | HSK Exam Syllabus — Vocabulary |
| HSK Characters | 3,088 | HSK Exam Syllabus — Characters |

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/counts-zh-dark.png">
  <img alt="HSK wordlist sizes" src="assets/counts-zh-light.png" width="540">
</picture>
<!-- counts-zh:end -->

## Format

Wordlist files live in `data/{en,zh}/archive/`. Each file has a `_meta` block, then sections; inside a section a word maps to its data.

**Oxford 3000 / 5000** — `data/en/archive/Oxford.json`

```json
{ "Oxford3000": { "bank": {"A1": [["n.", "money"]], "B1": [["n.", "river"]]},
                 "analyse": {"B1": [["v.", "", "UK"]]} },
  "Oxford5000": { "exit": {"B2": [["n.", "", "UK"]], "C1": [["v.", "", "UK"]]} } }
```

- section = `Oxford3000` / `Oxford5000`
- value = `{CEFR: [[part of speech, sense?, edition?], …]}`; a 3rd element `US` / `UK` marks
  records that are edition-specific (American and British merged; 2-element records = both)

**HSK vocabulary** — `data/zh/archive/HSK词汇.json`

```json
{ "一级": { "爱": [["ài", "动"]], "半": [["bàn", "数"]] },
  "四级": { "半": [["bàn", "副"]] } }
```

- section = `一级` … `七—九级`
- value = `[[pinyin, part of speech], …]`; a word listed at several levels appears in each

**HSK characters** — `data/zh/archive/HSK汉字.json`

```json
{ "一级认读字": ["爱", "八", "爸", "..."],
  "一级~二级书写字": ["爱", "八", "爸", "..."] }
```

- sections are `<level>认读字` (recognition) and `<level>书写字` (writing)

**HSK definitions** — `data/zh/definitions.json`

```json
"爱":   [["ài", "oi3", ["love, be fond of, like"]]],
"行":   [["xíng", "hang4", ["go; walk; move, travel; circulate; Kangxi radical 144"]], ["háng", "hong4", ["go; walk; move, travel; circulate; Kangxi radical 144"]]],
"银行": [["yínháng", "ngan4 hong4", ["bank", "CL:家[jia1],個|个[ge4]"]]]
```

- value = `[[pinyin, jyutping, [English senses…]], …]` — one tuple per reading
- pinyin prefers the HSK syllabus; jyutping from `archive/粤拼.json` (chars) or the rime whole-word reading (words)
- senses: CC-CEDICT, one group per reading; a reading falls back to Unihan `kDefinition` only when it has none

**Unihan character glosses** — `data/zh/archive/字义.json`

```json
"爱": "love, be fond of, like",
"专": "monopolize, take sole possession"
```

- value = the Unihan `kDefinition` string; terse and etymological, for character-level reference only

**Character Jyutping** — `data/zh/archive/粤拼.json`

```json
"行": {"xíng": "hang4", "háng": "hong4"},
"长": {"cháng": "coeng4", "zhǎng": "zoeng2"}
```

- value = `{Mandarin pinyin: Jyutping}`; Mandarin tones shown, Jyutping from rime-cantonese (word-aligned) with Unihan fallback

**HSK categories** — `data/zh/categories.json`

```json
"爱": ["HSK1", "HSK1R", "HSK1W", "HSK2W"],
"行": ["HSK3", "HSK3R", "HSK3W", "HSK5"]
```

- value = `[HSK tag, …]`: words `HSK1`–`HSK7-9`, recognition chars `HSK{n}R`, writing chars `HSK{n}W`

## License

This project's own work (JSON structure, processing, docs) is under the [MIT](LICENSE) license.

- Glosses and IPA in `data/en/definitions.json` come from [ECDICT](https://github.com/skywind3000/ECDICT) (MIT).
- English glosses in `data/zh/definitions.json` come from [CC-CEDICT](https://www.mdbg.net/chinese/dictionary?page=cc-cedict),
  licensed **CC BY-SA 4.0**; that file's glosses are distributed under CC BY-SA 4.0.
- Character glosses in `data/zh/archive/字义.json` come from [Unihan](https://www.unicode.org/Public/UCD/latest/ucd/Unihan.zip)
  (Unicode, Inc.), licensed under the Unicode License V3 (permissive, MIT-compatible).
- Jyutping in `data/zh/archive/粤拼.json` comes from [rime-cantonese](https://github.com/rime/rime-cantonese)
  (CC BY 4.0 / ODbL 1.0), with [Unihan](https://www.unicode.org/Public/UCD/latest/ucd/Unihan.zip) (Unicode License V3) fallback.
- Source PDFs under `sources/` remain the copyright of their respective publishers and are included for study
  and research only; see the [Chinese README](README.md) for details.
