# 02_data_preparation: データ準備関連スクリプト

データ準備に関連するスクリプトをまとめたディレクトリです。

## ディレクトリ構造

```
02_data_preparation/
├── fetch/                    # データ取得
│   └── fetch_past_results.py        # 過去結果データの取得
├── fix/                      # データ修正
│   ├── fix_date_weekday.py          # 日付と曜日の修正
│   ├── fix_null_weekdays.py         # NULL曜日の修正
│   ├── fix_future_dates.py          # 未来日付の修正
│   ├── fix_6841_date.py             # 6841回号の日付修正
│   ├── add_weekday_column.py        # 曜日カラムの追加
│   └── update_all_dates_from_mizuhobank.py  # みずほ銀行から日付を更新
└── validation/               # データ検証
    ├── validate_date_weekday.py     # 日付と曜日の検証
    ├── check_date_status.py         # 日付ステータスの確認
    └── investigate_null_weekdays.py # NULL曜日の調査
```

## 使用方法

### データ取得

```bash
# 過去結果データの取得
python3 scripts/02_data_preparation/fetch/fetch_past_results.py
```

### データ修正

```bash
# 日付と曜日の修正
python3 scripts/02_data_preparation/fix/fix_date_weekday.py

# NULL曜日の修正
python3 scripts/02_data_preparation/fix/fix_null_weekdays.py

# 未来日付の修正
python3 scripts/02_data_preparation/fix/fix_future_dates.py

# 6841回号の日付修正
python3 scripts/02_data_preparation/fix/fix_6841_date.py

# 曜日カラムの追加
python3 scripts/02_data_preparation/fix/add_weekday_column.py

# みずほ銀行から日付を更新
python3 scripts/02_data_preparation/fix/update_all_dates_from_mizuhobank.py
```

### データ検証

```bash
# 日付と曜日の検証
python3 scripts/02_data_preparation/validation/validate_date_weekday.py

# 日付ステータスの確認
python3 scripts/02_data_preparation/validation/check_date_status.py

# NULL曜日の調査
python3 scripts/02_data_preparation/validation/investigate_null_weekdays.py
```

## 関連ファイル

- `notebooks/run_01_data_preparation.py` - データ準備スクリプト
- `data/past_results.csv` - 過去結果データファイル

