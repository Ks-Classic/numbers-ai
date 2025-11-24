# 開発ツール詳細

**場所**: `scripts/tools/`

開発・分析・検証に使用するツールの詳細ドキュメントです。

## 📋 前提条件

### 環境
- **OS**: WSL（Windows Subsystem for Linux）
- **Python**: Python 3.x（`python3`コマンドを使用）
- **仮想環境**: venv（仮想環境）が必要

### セットアップ手順

1. **仮想環境の作成と有効化**
   ```bash
   # プロジェクトルートで実行
   python3 -m venv venv
   source venv/bin/activate
   ```

2. **依存関係のインストール**
   ```bash
   pip install -r scripts/requirements.txt
   ```

3. **実行前の確認**
   ```bash
   # 仮想環境が有効化されていることを確認（プロンプトに (venv) が表示される）
   which python3  # venv/bin/python3 を指していることを確認
   ```

### 実行時の注意

- すべてのスクリプトは**仮想環境を有効化した状態**で実行してください
- `python3`ではなく`python3`を使用してください
- 例: `python3 scripts/tools/visualization/visualize_normal_cube_steps.py --round 6849`

---

## 📋 使用シーン別

### 🔍 デバッグ・可視化

#### CUBE生成プロセスを可視化したい時

**シーン**: CUBE生成ロジックのデバッグ、生成プロセスの理解

**ツール**:
- `visualize_normal_cube_steps.py` - 通常CUBE生成の各ステップを可視化
- `visualize_extreme_cube_steps.py` - 極CUBE生成の各ステップを可視化

**使い方**:
```bash
# 通常CUBEの生成ステップを確認
python3 scripts/tools/visualization/visualize_normal_cube_steps.py --round 6849 --pattern B1 --target n3

# 極CUBEの生成ステップを確認
python3 scripts/tools/visualization/visualize_extreme_cube_steps.py --round 6849
```

---

#### CUBEをExcelに貼り付けたい時

**シーン**: CUBEをExcelに貼り付けて使用したい、通常CUBEと極CUBEを比較したい

**ツール**: `export_cube_to_html.py` - CUBEをHTML形式で出力（Excel貼り付け可能）

**使い方**:
```bash
# 通常CUBEをHTML出力
python3 scripts/tools/visualization/export_cube_to_html.py --round 6849 --pattern B1 --target n3

# 極CUBEをHTML出力
python3 scripts/tools/visualization/export_cube_to_html.py --round 6849 --cube-type extreme
```

---

#### 特徴量の動作を確認したい時

**シーン**: 特徴量の動作確認、リハーサル数字の影響を分析

**ツール**:
- `visualize_rehearsal_features.py` - リハーサル数字と当選番号の関係性特徴量を可視化
- `generate_batch_visualization_data.py` - 複数回号・パターンの可視化データを一括生成
- `visualization_server.py` - HTTPサーバーで可視化データを提供

**使い方**:
```bash
# リハーサル特徴量を可視化
python3 scripts/tools/visualization/visualize_rehearsal_features.py 6849

# 可視化サーバーを起動
python3 scripts/tools/visualization/visualization_server.py --port 8000
# ブラウザで http://localhost:8000/?round=6849&pattern=B1&target=n3 にアクセス
```

---

### 📊 モデル分析

#### 重要な特徴量を特定したい時

**シーン**: モデル改善時に重要な特徴量を特定、特徴量の効果を確認

**ツール**: `analyze_model_features.py` - 学習済みモデルから特徴量重要度を抽出・分析

**使い方**:
```bash
python3 scripts/tools/analysis/analyze_model_features.py
```

**出力**: `docs/report/feature_importance_*.json`

---

#### 特徴量の関係性を分析したい時

**シーン**: 軸数字やリハーサル数字の効果を分析、特徴量の改善

**ツール**:
- `analyze_axis_relationship.py` - 軸数字と当選番号の関係性を分析
- `analyze_rehearsal_relationship.py` - リハーサル数字と当選番号の関係性を分析

**使い方**:
```bash
python3 scripts/tools/analysis/analyze_axis_relationship.py
python3 scripts/tools/analysis/analyze_rehearsal_relationship.py
```

---

#### 特徴量を最適化したい時

**シーン**: 不要な特徴量を削除してモデルを軽量化、特徴量の最適化

**ツール**:
- `select_features.py` - 特徴量重要度に基づいて特徴量を選択
- `feature_patterns.py` - 異なる特徴量セットを比較・実験

**使い方**:
```bash
# 特徴量を選択（重要度の低いものを削除）
python3 scripts/tools/analysis/select_features.py

# 特徴量パターンを実験
python3 scripts/tools/analysis/feature_patterns.py
```

---

### ✅ 検証・確認

#### データを確認したい時

**シーン**: データの内容や範囲を確認、データの不整合を確認

**ツール**:
- `check_data.py` - 学習データファイルの簡易確認
- `check_data_range.py` - 学習データ範囲の選定・比較
- `check_data_cleaning.py` - データクリーニング結果の確認
- `check_round_data.py` - 特定回号のデータを詳細確認

**使い方**:
```bash
# データ範囲を確認
python3 scripts/tools/validation/check_data_range.py

# 特定回号のデータを確認
python3 scripts/tools/validation/check_round_data.py --round 6847 --detailed
```

---

#### 予測精度を検証したい時

**シーン**: モデルの予測精度を検証、特定回号での予測結果を確認

**ツール**:
- `check_prediction_for_round.py` - 過去回号での予測結果を確認
- `predict_with_winning.py` - 予測結果を出力して検証

**使い方**:
```bash
# 単一回号で検証
python3 scripts/tools/validation/check_prediction_for_round.py --round 6847

# 範囲指定で検証
python3 scripts/tools/validation/check_prediction_for_round.py --range 6840 6849

# リハーサル数字を指定
python3 scripts/tools/validation/check_prediction_for_round.py --round 6847 --n3-rehearsal 149
```

---

#### 評価結果を確認したい時

**シーン**: モデル学習後の評価結果確認、過去の評価結果と比較

**ツール**: `check_evaluation_results.py` - 保存された評価結果を表示

**使い方**:
```bash
# 最新の評価結果を表示
python3 scripts/tools/validation/check_evaluation_results.py

# すべての評価結果を表示
python3 scripts/tools/validation/check_evaluation_results.py --all

# 特定ファイルを表示
python3 scripts/tools/validation/check_evaluation_results.py --file path/to/file.pkl
```

---

### 🎓 モデル学習

#### ハイパーパラメータを調整したい時

**シーン**: モデル改善時にハイパーパラメータを調整、AUC-ROCを0.55-0.60に改善したい

**ツール**: `tune_hyperparameters_v2.py` - XGBoostモデルのハイパーパラメータを最適化

**使い方**:
```bash
python3 scripts/tools/training/tune_hyperparameters_v2.py
```

**出力**: 
- 最適化されたパラメータ
- 評価結果（`docs/report/`）

---

#### 新しい特徴量を検証したい時

**シーン**: 新しい特徴量を追加した際の検証、特徴量の回帰テスト

**ツール**: `test_new_features.py` - 新規特徴量が正しく計算されることを確認

**使い方**:
```bash
python3 scripts/tools/training/test_new_features.py
```

---

## よくあるワークフロー

### 📈 モデル改善のワークフロー

1. **データ確認**
   ```bash
   python3 scripts/tools/validation/check_data_range.py
   ```

2. **特徴量分析**
   ```bash
   python3 scripts/tools/analysis/analyze_model_features.py
   ```

3. **ハイパーパラメータ調整**
   ```bash
   python3 scripts/tools/training/tune_hyperparameters_v2.py
   ```

4. **評価結果確認**
   ```bash
   python3 scripts/tools/validation/check_evaluation_results.py
   ```

5. **予測検証**
   ```bash
   python3 scripts/tools/validation/check_prediction_for_round.py --range 6840 6849
   ```

### 🐛 デバッグのワークフロー

1. **データ確認**
   ```bash
   python3 scripts/tools/validation/check_round_data.py --round 6849 --detailed
   ```

2. **CUBE生成の可視化**
   ```bash
   python3 scripts/tools/visualization/visualize_normal_cube_steps.py --round 6849 --pattern B1
   ```

3. **特徴量可視化**
   ```bash
   python3 scripts/tools/visualization/visualize_rehearsal_features.py 6849
   ```

### 📊 分析のワークフロー

1. **特徴量重要度分析**
   ```bash
   python3 scripts/tools/analysis/analyze_model_features.py
   ```

2. **関係性分析**
   ```bash
   python3 scripts/tools/analysis/analyze_axis_relationship.py
   python3 scripts/tools/analysis/analyze_rehearsal_relationship.py
   ```

3. **特徴量選択**
   ```bash
   python3 scripts/tools/analysis/select_features.py
   ```

---

## カテゴリ別一覧

### 可視化ツール (`scripts/tools/visualization/`)
- `export_cube_to_html.py` - HTML出力
- `visualize_normal_cube_steps.py` - 通常CUBE生成の各ステップを可視化
- `visualize_extreme_cube_steps.py` - 極CUBE生成の各ステップを可視化
- `visualize_rehearsal_features.py` - リハーサル特徴量可視化
- `generate_batch_visualization_data.py` - バッチ可視化データ生成
- `visualization_server.py` - HTTP可視化サーバー

### 分析ツール (`scripts/tools/analysis/`)
- `analyze_model_features.py` - 特徴量重要度分析
- `analyze_axis_relationship.py` - 軸数字関係性分析
- `analyze_rehearsal_relationship.py` - リハーサル関係性分析
- `select_features.py` - 特徴量選択
- `feature_patterns.py` - 特徴量パターン実験

### 検証ツール (`scripts/tools/validation/`)
- `check_evaluation_results.py` - 評価結果確認
- `check_prediction_for_round.py` - 予測検証
- `check_round_data.py` - 回号データ確認
- `check_data_range.py` - データ範囲確認
- `check_data_cleaning.py` - データクリーニング確認
- `check_data.py` - データ簡易確認
- `predict_with_winning.py` - 予測検証（出力）

### 学習ツール (`scripts/tools/training/`)
- `tune_hyperparameters_v2.py` - ハイパーパラメータ調整
- `test_new_features.py` - 新規特徴量検証
