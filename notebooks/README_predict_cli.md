# CLIツールの使用方法

## 予測実行ツール

### predict_cli.py

コマンドラインから予測を実行するためのCLIツール。

## 基本的な使い方

### 1. コマンドライン引数で実行

```bash
cd notebooks
python predict_cli.py --round 6758 --n3-rehearsal 149 --n4-rehearsal 3782
```

### 2. 対話的に実行

```bash
cd notebooks
python predict_cli.py
```

実行すると、回号とリハーサル数字の入力を求められます。

## 出力例

```
予測結果 - 回号: 6758
================================================================================
N3リハーサル: 149
N4リハーサル: 3782

--------------------------------------------------------------------------------
N3予測結果
--------------------------------------------------------------------------------

[BOX]

軸数字予測（パターン別）:
  A1: 7(985), 2(952), 4(847), ...
  A2: 7(982), 2(948), 4(842), ...
  ...

最良パターン: A1

軸数字ランキング:
   1. 数字7: スコア985
   2. 数字2: スコア952
   ...

組み合わせランキング（上位10件）:
   1. 147: スコア978
   2. 079: スコア942
   ...
```

## 評価結果確認ツール

### check_evaluation_results.py

保存された評価結果を確認するCLIツール。

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

### check_prediction_for_round.py

過去回号での予測結果を確認し、実際の当選番号と比較するCLIツール。

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

## 注意事項

- モデルファイル（`data/models/*.pkl`）が存在する必要があります
- 過去データファイル（`data/past_results.csv`）が存在する必要があります
- 罫線マスターファイル（`data/keisen_master.json`）が存在する必要があります

## トラブルシューティング

### モデルが見つからないエラー

モデルを学習していない場合は、まず以下のNotebookを実行してください：

1. `01_data_preparation.ipynb` - データ準備
2. `02_chart_generation.ipynb` - 予測表生成
3. `03_feature_engineering.ipynb` - 特徴量エンジニアリング
4. `04_model_training.ipynb` - モデル学習

