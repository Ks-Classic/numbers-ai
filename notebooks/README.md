# Jupyter Notebooks - AI学習環境

このディレクトリには、AIモデルの学習と特徴量エンジニアリングに使用するJupyter Notebookが格納されます。

## 📋 CLIツール一覧（サマリ）

このディレクトリには、データ確認、モデル評価、予測実行のためのCLIツールが含まれています。

### 📊 データ確認ツール（4つ） - MECEで整理

| ツール | 目的 | 使用シーン |
|--------|------|------------|
| `check_data_range.py` | 学習データ範囲の選定 | 学習範囲選定時 |
| `check_data_cleaning.py` | クリーニング結果の確認 | データ準備後 |
| `check_data.py` | 学習データファイルの簡易確認 | クイックチェック |
| `check_round_data.py` | 特定回号の詳細確認 | 問題発生時・デバッグ |

### 📈 モデル評価ツール（2つ）

| ツール | 目的 | 使用シーン |
|--------|------|------------|
| `check_evaluation_results.py` | 評価結果確認 | モデル学習完了後 |
| `check_prediction_for_round.py` | 過去回号での予測結果確認 | モデル検証時 |

### 🎯 予測実行ツール（1つ）

| ツール | 目的 | 使用シーン |
|--------|------|------------|
| `predict_cli.py` | 予測実行 | 新しい回号の予測実行時 |

詳細は「[CLIツール・ユーティリティ](#cliツールユーティリティ)」セクションを参照してください。

---

## セットアップ

### 1. Python仮想環境の作成（推奨）

```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# または
venv\Scripts\activate  # Windows
```

### 2. ライブラリのインストール

```bash
pip install -r requirements.txt
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

### chart_generator.py
予測表生成アルゴリズムの実装。4パターン（A1/A2/B1/B2）に対応。

### feature_extractor.py
特徴量エンジニアリングモジュール。形状特徴、位置特徴、関係性特徴、集約特徴を計算。

### model_loader.py
学習済みモデルを読み込み、推論を行うためのユーティリティクラス。

**主な機能:**
- 6つのモデルファイルの自動読み込み
- モデルファイルの存在確認
- エラーハンドリング
- 軸数字予測API (`predict_axis()`)
- 組み合わせ予測API (`predict_combination()`)

## CLIツール・ユーティリティ

このディレクトリには、データ確認、モデル評価、予測実行のためのCLIツールが含まれています。

### 📊 データ確認ツール

データの状態や範囲を確認するためのツールです。

#### check_data_range.py

**役割**: 学習データ範囲の選択肢を比較・確認

**使いたいシーン**:
- 学習データ範囲を選定する前
- 1000回分と4801回分のデータ量を比較したい時
- リハーサル数字の有無を確認したい時

**使用方法:**
```bash
python check_data_range.py
```

**出力内容:**
- 最新回号と全データ件数
- 選択肢1（1000回分）のデータ範囲と件数、リハーサル数字の有無
- 選択肢2（4801回から最新回まで）のデータ範囲と件数、リハーサル数字の有無
- 両選択肢の比較

#### check_data_cleaning.py

**役割**: データクリーニング処理の結果を確認

**使いたいシーン**:
- データクリーニング処理を実行した後
- クリーニング前後のデータ件数を確認したい時
- 特定回号（6847回）がクリーニング後にも存在するか確認したい時

**使用方法:**
```bash
python check_data_cleaning.py
```

**出力内容:**
- クリーニング前後のデータ件数
- 除外された行数
- 6847回のデータ確認（クリーニング後）

#### check_data.py

**役割**: 学習データファイルの簡易確認

**使いたいシーン:**
- 学習データファイル（train_data_1000.csv）が正しく生成されているか確認したい時
- 特定回号が学習データに含まれているか確認したい時

**使用方法:**
```bash
python check_data.py
```

**出力内容:**
- 全データと学習データの回号範囲
- 特定回号（6847回）の存在確認

#### check_round_data.py

**役割**: 特定回号のデータを確認（汎用版）

**使いたいシーン:**
- 特定回号のデータを確認したい時
- データ形式に問題がある回号を調査したい時
- デバッグが必要な時

**使用方法:**
```bash
# 基本的な確認
python check_round_data.py --round 6847

# 詳細なデバッグ情報を表示
python check_round_data.py --round 6847 --detailed
```

**出力内容:**
- 指定回号の生データ
- データ変換後の値（--detailedオプション時）
- 正規表現マッチの結果（--detailedオプション時）
- 学習データに含まれるかどうか

**注意**: `check_6847.py`は`check_round_data.py --round 6847 --detailed`で代替可能です。

### 📈 モデル評価ツール

学習済みモデルの精度や予測結果を確認するためのツールです。

#### check_evaluation_results.py

**役割**: 保存されたモデル評価結果を確認

**使いたいシーン:**
- モデル学習完了後、評価指標を確認したい時
- 複数の評価結果ファイルを比較したい時
- 目標値（AUC-ROC: 0.65以上）との比較をしたい時

**使用方法:**
```bash
# 現在の評価結果を表示
python check_evaluation_results.py

# すべての評価結果ファイルを表示
python check_evaluation_results.py --all

# 指定ファイルを表示
python check_evaluation_results.py --file path/to/file
```

**出力内容:**
- 各モデルの評価指標一覧（AUC-ROC、Precision、Recall、F1-Score、Top-5 Accuracy）
- 各評価指標の平均値
- 目標値（AUC-ROC: 0.65以上）との比較

#### check_prediction_for_round.py

**役割**: 過去回号での予測結果を確認し、実際の当選番号と比較

**使いたいシーン:**
- モデルの予測精度を過去データで確認したい時
- 特定回号での予測結果を検証したい時
- 複数回号で一括検証したい時

**使用方法:**
```bash
# 特定回号の予測結果を確認
python check_prediction_for_round.py --round 6847

# リハーサル数字を指定
python check_prediction_for_round.py --round 6847 --n3-rehearsal 149

# 複数回号を一度に確認
python check_prediction_for_round.py --range 6840 6849
```

**出力内容:**
- 実際の当選番号
- 予測された軸数字ランキング（上位10件、当選数字にマーク）
- 組み合わせ予測結果（上位10件、当選番号にマーク）
- 予測精度（上位5件中に当選数字が含まれる数）

### 🎯 予測実行ツール

実際の予測を実行するためのツールです。

#### predict_cli.py

**役割**: コマンドラインから予測を実行

**使いたいシーン:**
- 新しい回号の予測を実行したい時
- 予測結果を確認したい時
- APIを使わずに直接予測を実行したい時

**使用方法:**
```bash
# コマンドライン引数で実行
python predict_cli.py --round 6758 --n3-rehearsal 149 --n4-rehearsal 3782

# 対話的に実行
python predict_cli.py
```

**出力内容:**
- パターン別軸数字予測結果（A1/A2/B1/B2）
- 最良パターンの特定
- 軸数字ランキング（上位10件）
- 組み合わせランキング（ボックス/ストレート別、上位10件）

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
python check_data_range.py

# 2. データ準備
python run_01_data_preparation.py
python check_data.py  # 生成されたデータを確認

# 3. 特徴量エンジニアリング
python run_03_feature_engineering_full.py

# 4. モデル学習
python run_04_model_training_axis.py
# または
# Jupyter Notebookで 04_model_training.ipynb を実行

# 5. 評価結果の確認
python check_evaluation_results.py
```

### モデル検証フロー

```bash
# 1. 評価結果の確認
python check_evaluation_results.py

# 2. 過去回号での予測結果確認
python check_prediction_for_round.py --round 6847

# 3. 複数回号で一括検証
python check_prediction_for_round.py --range 6840 6849
```

### トラブルシューティングフロー

```bash
# 1. データクリーニング結果の確認
python check_data_cleaning.py

# 2. 学習データの確認
python check_data.py

# 3. 特定回号のデータ確認（問題がある場合）
python check_round_data.py --round 6847 --detailed
```

## データ構造

- **入力データ**: `../data/past_results.csv`
- **罫線マスタ**: `../data/keisen_master.json`
- **学習済みモデル**: `../data/models/`

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
- モデル学習後、CLIツール（`predict_cli.py`）で予測をテストできます

