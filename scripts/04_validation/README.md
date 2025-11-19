# 04_validation: 検証関連スクリプト

検証に関連するスクリプトをまとめたディレクトリです。

## ディレクトリ構造

```
04_validation/
├── keisen/                   # keisen検証
│   ├── verify_keisen_master.py        # keisenマスターの検証
│   ├── verify_new_keisen.py          # 新keisenの検証
│   ├── check_new_keisen.py           # 新keisenのチェック
│   ├── check_keisen_structure.py     # keisen構造のチェック
│   ├── check_pattern_key.py          # パターンキーのチェック
│   └── check_verification_logic.py   # 検証ロジックのチェック
└── data/                     # データ検証
    ├── check_missing_rounds.py       # 欠損回号のチェック
    ├── check_n3_table.py             # N3テーブルのチェック
    ├── check_table_structure.py      # テーブル構造のチェック
    ├── check_feature_data.py         # 特徴量データのチェック
    └── check_combination_data.py     # 組み合わせ予測データの確認
```

## 使用方法

### keisen検証

```bash
# keisenマスターの検証
python3 scripts/04_validation/keisen/verify_keisen_master.py

# 新keisenの検証
python3 scripts/04_validation/keisen/verify_new_keisen.py

# 新keisenのチェック
python3 scripts/04_validation/keisen/check_new_keisen.py

# keisen構造のチェック
python3 scripts/04_validation/keisen/check_keisen_structure.py

# パターンキーのチェック
python3 scripts/04_validation/keisen/check_pattern_key.py

# 検証ロジックのチェック
python3 scripts/04_validation/keisen/check_verification_logic.py
```

### データ検証

```bash
# 欠損回号のチェック
python3 scripts/04_validation/data/check_missing_rounds.py

# N3テーブルのチェック
python3 scripts/04_validation/data/check_n3_table.py

# テーブル構造のチェック
python3 scripts/04_validation/data/check_table_structure.py

# 特徴量データのチェック
python3 scripts/04_validation/data/check_feature_data.py

# 組み合わせ予測データの確認
python3 scripts/04_validation/data/check_combination_data.py
```

## 関連ファイル

- `scripts/tools/validation/` - 開発ツール（検証）
- `data/keisen_master.json` - keisenマスターデータ

