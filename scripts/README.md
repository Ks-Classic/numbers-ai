# scriptsディレクトリ

プロジェクトの各種スクリプトをまとめたディレクトリです。

## ディレクトリ構造

```
scripts/
├── 01_model_generation/      # モデル生成関連
│   ├── data_generation/       # データ生成
│   └── monitoring/           # モニタリング
├── 02_data_preparation/      # データ準備関連
│   ├── fetch/                # データ取得
│   ├── fix/                  # データ修正
│   └── validation/           # データ検証
├── 03_analysis/              # 分析関連
│   ├── digit_patterns/       # 数値パターン分析
│   ├── predictions/          # 予測分析
│   ├── rules/                # ルール分析
│   └── past_results/         # 過去結果分析
├── 04_validation/            # 検証関連
│   ├── keisen/               # keisen検証
│   └── data/                 # データ検証
├── base_statistics/           # 基礎集計（カテゴリ別に整理）
├── tools/                     # 開発ツール（analysis, training, validation, visualization）
├── production/                # 本番スクリプト
└── test/                      # テストファイル
```

## カテゴリ別の説明

### 01_model_generation: モデル生成関連

モデル生成に関連するスクリプトをまとめています。

- **data_generation/**: データ生成スクリプト
- **monitoring/**: モニタリングスクリプト

詳細は [01_model_generation/README.md](01_model_generation/README.md) を参照してください。

### 02_data_preparation: データ準備関連

データ準備に関連するスクリプトをまとめています。

- **fetch/**: データ取得スクリプト
- **fix/**: データ修正スクリプト
- **validation/**: データ検証スクリプト

詳細は [02_data_preparation/README.md](02_data_preparation/README.md) を参照してください。

### 03_analysis: 分析関連

分析に関連するスクリプトをまとめています。

- **digit_patterns/**: 数値パターン分析
- **predictions/**: 予測分析
- **rules/**: ルール分析
- **past_results/**: 過去結果分析

詳細は [03_analysis/README.md](03_analysis/README.md) を参照してください。

### 04_validation: 検証関連

検証に関連するスクリプトをまとめています。

- **keisen/**: keisen検証
- **data/**: データ検証

詳細は [04_validation/README.md](04_validation/README.md) を参照してください。

### base_statistics: 基礎集計

基礎集計に関するスクリプトをカテゴリごとに整理したディレクトリです。

詳細は [base_statistics/README.md](base_statistics/README.md) を参照してください。

### tools: 開発ツール

開発時に使用するツールをまとめています。

- **analysis/**: 分析ツール
- **training/**: 学習ツール
- **validation/**: 検証ツール
- **visualization/**: 可視化ツール

### production: 本番スクリプト

本番環境で使用するスクリプトをまとめています。

### test: テストファイル

テスト用のファイルをまとめています。

## scripts直下のファイル

以下のファイルは、特定のディレクトリに属さないユーティリティスクリプトや設定ファイルです。

### ユーティリティスクリプト

- **`format_keisen_json.py`**: keisen_master_new.jsonの配列を1行に整形するスクリプト
- **`cleanup_old_models.sh`**: 古いXGBoostモデルファイルと評価結果ファイルを削除するスクリプト

### 開発・運用スクリプト

- **`start-nextjs.sh`**: Next.js開発サーバーを起動するスクリプト
- **`setup_cron.sh`**: cronジョブを設定するスクリプト（WSL環境対応）
- **`test-api.sh`**: API統合テストスクリプト（FastAPIサーバーとNext.js API Routeの動作確認）

### 設定ファイル

- **`requirements.txt`**: Python依存関係（OCR、画像処理、Webスクレイピングなど）
- **`tsconfig.json`**: TypeScript設定ファイル（scripts内のTypeScriptファイル用）

### ドキュメント

- **`README.md`**: このファイル（scriptsディレクトリの全体説明）
- **`STRUCTURE_ANALYSIS.md`**: ディレクトリ構造の分析ドキュメント（構造設計の参考資料）

## 整理履歴

- 2025-11-18: `base_statistics`を参考に、カテゴリごとにディレクトリを分けて整理
- 2025-11-18: 重複ファイルと古い仕様のスクリプトを削除
- 2025-11-18: 一時的な整理用スクリプトとドキュメントを削除

