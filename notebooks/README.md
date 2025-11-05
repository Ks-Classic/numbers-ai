# Jupyter Notebooks - AI学習環境

このディレクトリには、AIモデルの学習と特徴量エンジニアリングに使用するJupyter Notebookが格納されます。

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

## CLIツール

### predict_cli.py

コマンドラインから予測を実行するためのCLIツール。

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

