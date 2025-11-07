# Jupyter Notebooks - AI学習環境

このディレクトリには、AIモデルの学習と特徴量エンジニアリングに使用するJupyter Notebookが格納されます。

## 📋 ディレクトリ構成

このディレクトリには、**Jupyter Notebookファイルとその実行スクリプトのみ**が格納されています。

**注意**: CLIツールやコアモジュールは以下の場所に移動しました：
- **CLIツール**: `scripts/tools/`配下（analysis/, training/, validation/, visualization/）
- **コアモジュール**: `core/`配下（chart_generator.py, feature_extractor.py, model_loader.py, config.py）
- **本番スクリプト**: `scripts/production/`配下（predict_cli.py, fetch_past_results.py など）

詳細は `docs/01_design/tools/README.md` を参照してください。

---

## セットアップ

### 1. Python仮想環境の作成と有効化

**重要**: 仮想環境は**プロジェクトルート**で作成・管理します。

```bash
# プロジェクトルートで実行
cd /path/to/numbers-ai
python3 -m venv venv
source venv/bin/activate  # Linux/Mac/WSL
# または
venv\Scripts\activate  # Windows
```

### 2. ライブラリのインストール

```bash
# プロジェクトルートのvenvを有効化した状態で実行
pip install -r notebooks/requirements.txt
# または
pip install -r scripts/requirements.txt
```

### 3. Jupyter Notebookの起動

```bash
jupyter notebook
```

または

```bash
jupyter lab
```

## Notebook構成

### 01_data_preparation.ipynb
- CSVデータの読み込みとクリーニング
- データの基本統計情報の確認
- 学習用データセットの準備（直近100回分）

### 02_chart_generation.ipynb
- 各回号に対して4パターン（A1/A2/B1/B2）の予測表を生成
- 予測表の検証と可視化
- 特徴量エンジニアリングの準備

### 03_feature_engineering.ipynb
- 予測表から特徴量を抽出
- パターンIDを特徴量として追加
- 軸数字予測モデルの学習データ生成（4,000サンプル）
- 組み合わせ予測モデルの学習データ生成（数万〜数十万サンプル）
- データセットの分割（train/val）と保存

### 04_model_training.ipynb
- XGBoostハイパーパラメータの設定
- 6つの統合モデルの学習:
  - 軸数字予測モデル（2モデル）: N3/N4
  - 組み合わせ予測モデル（4モデル）: N3/N4 × ボックス/ストレート
- モデル評価（AUC-ROC、Precision、Recall、F1-Score、Top-K Accuracy）
- 学習済みモデルの保存（`data/models/`ディレクトリ）

## モジュール構成

**注意**: 以下のモジュールは`core/`ディレクトリに移動しました。

### core/chart_generator.py
予測表生成アルゴリズムの実装。4パターン（A1/A2/B1/B2）に対応。

### core/feature_extractor.py
特徴量エンジニアリングモジュール。形状特徴、位置特徴、関係性特徴、集約特徴を計算。

### core/model_loader.py
学習済みモデルを読み込み、推論を行うためのユーティリティクラス。

### core/config.py
設定ファイル。学習範囲、データパスなどの設定を管理。

**主な機能:**
- 6つのモデルファイルの自動読み込み
- モデルファイルの存在確認
- エラーハンドリング
- 軸数字予測API (`predict_axis()`)
- 組み合わせ予測API (`predict_combination()`)

## CLIツール・ユーティリティ

**注意**: CLIツールは`scripts/tools/`ディレクトリに移動しました。

詳細は以下のドキュメントを参照してください：
- [開発ツール一覧](../docs/01_design/tools/README.md)
- [開発ツール詳細](../docs/01_design/tools/development-tools.md)

### 主なツールの場所

- **データ確認ツール**: `scripts/tools/validation/`
  - `check_data_range.py` - 学習データ範囲の選定
  - `check_data_cleaning.py` - クリーニング結果の確認
  - `check_data.py` - 学習データファイルの簡易確認
  - `check_round_data.py` - 特定回号のデータを詳細確認

- **モデル評価ツール**: `scripts/tools/validation/`
  - `check_evaluation_results.py` - 評価結果確認
  - `check_prediction_for_round.py` - 過去回号での予測結果確認

- **予測実行ツール**: `scripts/production/`
  - `predict_cli.py` - CLIから予測を実行

詳細は `README_predict_cli.md` を参照してください。

### ⚙️ 実行スクリプト

NotebookをPythonスクリプトとして実行するためのツールです。

#### run_01_data_preparation.py

**役割**: データ準備処理を実行

**使いたいシーン:**
- Notebookを実行せずにデータ準備を実行したい時
- バッチ処理でデータ準備を実行したい時

**使用方法:**
```bash
python run_01_data_preparation.py
```

#### run_03_feature_engineering_*.py

**役割**: 特徴量エンジニアリング処理を実行

**種類:**
- `run_03_feature_engineering_axis_only.py` - 軸数字予測データのみ生成
- `run_03_feature_engineering_full.py` - 軸数字予測 + 組み合わせ予測データを生成
- `run_03_feature_engineering_test.py` - テスト用（小規模データ）

**使いたいシーン:**
- 特徴量エンジニアリング処理をバッチ実行したい時
- 軸数字予測データのみが必要な時（処理時間短縮）

#### run_04_model_training_axis.py

**役割**: 軸数字予測モデルの学習を実行

**使いたいシーン:**
- 軸数字予測モデルのみを学習したい時
- バッチ処理でモデル学習を実行したい時

**使用方法:**
```bash
python run_04_model_training_axis.py
```

詳細は `README_execution.md` を参照してください。

## ツール使用フロー

### データ準備からモデル学習まで

```bash
# 1. データ範囲の確認
python3 scripts/tools/validation/check_data_range.py

# 2. データ準備
python3 notebooks/run_01_data_preparation.py
python3 scripts/tools/validation/check_data.py  # 生成されたデータを確認

# 3. 特徴量エンジニアリング
python3 notebooks/run_03_feature_engineering_full.py

# 4. モデル学習
python3 notebooks/run_04_model_training_axis.py
# または
# Jupyter Notebookで 04_model_training.ipynb を実行

# 5. 評価結果の確認
python3 scripts/tools/validation/check_evaluation_results.py
```

### モデル検証フロー

```bash
# 1. 評価結果の確認
python3 scripts/tools/validation/check_evaluation_results.py

# 2. 過去回号での予測結果確認
python3 scripts/tools/validation/check_prediction_for_round.py --round 6847

# 3. 複数回号で一括検証
python3 scripts/tools/validation/check_prediction_for_round.py --range 6840 6849
```

### トラブルシューティングフロー

```bash
# 1. データクリーニング結果の確認
python3 scripts/tools/validation/check_data_cleaning.py

# 2. 学習データの確認
python3 scripts/tools/validation/check_data.py

# 3. 特定回号のデータ確認（問題がある場合）
python3 scripts/tools/validation/check_round_data.py --round 6847 --detailed
```

## データ構造

**重要**: データは**プロジェクトルートの`data/`ディレクトリ**を使用します。

- **入力データ**: `data/past_results.csv`（プロジェクトルート）
- **罫線マスタ**: `data/keisen_master.json`（プロジェクトルート）
- **学習済みモデル**: `data/models/`（プロジェクトルート）

notebooksフォルダ内の`data/`ディレクトリは削除済みです。

## 学習手順

モデルを学習する場合は、以下の順序でNotebookを実行してください：

1. **`01_data_preparation.ipynb`**: データ準備
2. **`02_chart_generation.ipynb`**: 予測表生成
3. **`03_feature_engineering.ipynb`**: 特徴量エンジニアリングと学習データ生成
4. **`04_model_training.ipynb`**: モデル学習

詳細な手順は `docs/design/04-algorithm-ai.md` の「4.5.2 モデル学習手順」を参照してください。

## 注意事項

- すべての学習データは**基準回号: 第6758回（2025年6月30日）**を基準に構築します
- 4パターン（A1/A2/B1/B2）すべてのデータで統合モデルを学習します
- 軸数字予測モデルはボックス/ストレートで分けません（順序は関係ないため）
- モデル学習後、CLIツール（`scripts/production/predict_cli.py`）で予測をテストできます

