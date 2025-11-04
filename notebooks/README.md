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
- 特徴量計算関数の実装
- 形状特徴、位置特徴、関係性特徴、集約特徴の計算
- 特徴量ベクトルの生成

### 04_model_training.ipynb
- XGBoostモデルの学習
- 6つの統合モデルの学習（N3/N4 × 軸数字/組み合わせ）
- モデル評価と保存

## データ構造

- **入力データ**: `../data/past_results.csv`
- **罫線マスタ**: `../data/keisen_master.json`
- **学習済みモデル**: `../data/models/`

## 注意事項

- すべての学習データは**基準回号: 第6758回（2025年6月30日）**を基準に構築します
- 4パターン（A1/A2/B1/B2）すべてのデータで統合モデルを学習します
- 軸数字予測モデルはボックス/ストレートで分けません（順序は関係ないため）

