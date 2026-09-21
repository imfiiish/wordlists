# 词库 Wordlists

```
wordlists/
├── data/       # 词库 JSON
│   ├── CET.json
│   ├── Oxford3000-5000.json
│   └── 义务教育-普通高中.json
├── sources/    # 原始大纲 / 课程标准 PDF
│   ├── The_Oxford_3000.pdf
│   ├── The_Oxford_3000_by_CEFR.pdf
│   ├── The_Oxford_5000.pdf
│   ├── The_Oxford_5000_by_CEFR_level.pdf
│   ├── 《全国大学英语四、六级考试大纲（2016年修订版）》.pdf
│   ├── 普通高中英语课程标准日常修订版（2017年版2025年修订）.pdf
│   ├── 义务教育英语课程标准日常修订版（2022年版2025年修订）.pdf
│   └── 新版HSK考试大纲1219.pdf
├── assets/     # 生成的图表
│   ├── counts-light.png
│   └── counts-dark.png
├── tools/      # 统计 / 出图脚本
│   └── counts.py
└── README.md
```

<!-- counts:start -->
| 词表 | 词条数 | 来源 |
| --- | --: | --- |
| CET 四 / 六级 | 5,346 | 《全国大学英语四、六级考试大纲（2016年修订版）》 |
| Oxford 3000 / 5000 | 4,935 | The Oxford 3000™ & 5000™ |
| 义务教育 · 普通高中 | 3,099 | 《普通高中英语课程标准（2017年版2025年修订）》 |

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/counts-dark.png">
  <img alt="各词表词条数" src="assets/counts-light.png">
</picture>
<!-- counts:end -->

## 许可 License

本项目自行整理的部分（JSON 数据结构、数据处理、文档）采用 [MIT](LICENSE) 许可证。

`sources/` 中的 PDF 及其中词表内容的版权归原作者 / 出版机构所有
（如 The Oxford 3000/5000 归 Oxford University Press，课程标准和考试大纲归相应教育机构），
本项目仅出于学习研究目的收录，不主张任何权利。如需商用，请自行向权利人获取授权。
