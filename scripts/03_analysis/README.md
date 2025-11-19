# 03_analysis: 分析関連スクリプト

分析に関連するスクリプトをまとめたディレクトリです。

## ディレクトリ構造

```
03_analysis/
├── digit_patterns/           # 数値パターン分析
│   ├── analyze_4digit_patterns.py      # 4桁パターン分析
│   ├── analyze_4digit_detailed.py       # 4桁詳細分析
│   ├── analyze_3digit_vs_4digit_rule.py # 3桁 vs 4桁ルール分析
│   └── analyze_digit_count.py           # 数字カウント分析
├── predictions/              # 予測分析
│   ├── analyze_3digit_predictions.py    # 3桁予測分析
│   ├── analyze_4digit_predictions.py   # 4桁予測分析
│   └── analyze_long_predictions.py      # 長期予測分析
├── rules/                    # ルール分析
│   ├── analyze_complete_rule.py        # 完全ルール分析
│   └── analyze_final_rule.py           # 最終ルール分析
└── past_results/             # 過去結果分析
    └── analyze_past_results.py         # 過去結果分析
```

## 使用方法

### 数値パターン分析

```bash
# 4桁パターン分析
python3 scripts/03_analysis/digit_patterns/analyze_4digit_patterns.py

# 4桁詳細分析
python3 scripts/03_analysis/digit_patterns/analyze_4digit_detailed.py

# 3桁 vs 4桁ルール分析
python3 scripts/03_analysis/digit_patterns/analyze_3digit_vs_4digit_rule.py

# 数字カウント分析
python3 scripts/03_analysis/digit_patterns/analyze_digit_count.py
```

### 予測分析

```bash
# 3桁予測分析
python3 scripts/03_analysis/predictions/analyze_3digit_predictions.py

# 4桁予測分析
python3 scripts/03_analysis/predictions/analyze_4digit_predictions.py

# 長期予測分析
python3 scripts/03_analysis/predictions/analyze_long_predictions.py
```

### ルール分析

```bash
# 完全ルール分析
python3 scripts/03_analysis/rules/analyze_complete_rule.py

# 最終ルール分析
python3 scripts/03_analysis/rules/analyze_final_rule.py
```

### 過去結果分析

```bash
# 過去結果分析
python3 scripts/03_analysis/past_results/analyze_past_results.py
```

## 関連ファイル

- `scripts/base_statistics/` - 基礎集計スクリプト
- `scripts/tools/analysis/` - 開発ツール（分析）

