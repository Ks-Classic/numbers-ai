# 01_model_generation: モデル生成関連スクリプト

モデル生成に関連するスクリプトをまとめたディレクトリです。

## ディレクトリ構造

```
01_model_generation/
├── data_generation/          # データ生成
│   ├── fix_n4_data_save.py              # n4のデータファイルを再保存
│   ├── check_n4_data.py                 # n4データの生成状況を確認
│   ├── check_metadata_n4.py             # メタデータからn4のインデックス抽出を確認
│   ├── check_combination_data.py        # 組み合わせ予測データファイルの内容を確認
│   └── check_checkpoint.py              # チェックポイントファイルの確認
└── monitoring/               # モニタリング
    ├── monitor_combination_engineering.sh    # 組み合わせ予測データ生成のモニタリング
    ├── monitor_feature_engineering.sh        # 特徴量エンジニアリングのモニタリング
    └── check_feature_engineering_status.sh   # 特徴量エンジニアリングのステータス確認
```

## 使用方法

### データ生成

```bash
# n4のデータファイルを再保存
python3 scripts/01_model_generation/data_generation/fix_n4_data_save.py

# n4データの生成状況を確認
python3 scripts/01_model_generation/data_generation/check_n4_data.py

# メタデータからn4のインデックス抽出を確認
python3 scripts/01_model_generation/data_generation/check_metadata_n4.py

# 組み合わせ予測データファイルの内容を確認
python3 scripts/01_model_generation/data_generation/check_combination_data.py
```

### モニタリング

```bash
# 組み合わせ予測データ生成のモニタリング
bash scripts/01_model_generation/monitoring/monitor_combination_engineering.sh

# 特徴量エンジニアリングのモニタリング
bash scripts/01_model_generation/monitoring/monitor_feature_engineering.sh

# 特徴量エンジニアリングのステータス確認
bash scripts/01_model_generation/monitoring/check_feature_engineering_status.sh
```

## 関連ファイル

- `notebooks/run_03_feature_engineering_combination_only.py` - 組み合わせ予測データ生成スクリプト
- `notebooks/run_05_model_training_combination.py` - 組み合わせ予測モデル学習スクリプト

