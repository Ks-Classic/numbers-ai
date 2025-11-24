# 開発ツール・スクリプト一覧

このディレクトリには、開発・分析・検証に使用するツールの解説ドキュメントが格納されています。

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
   # scripts/requirements.txtからインストール
   pip install -r scripts/requirements.txt
   ```

3. **仮想環境の有効化確認**
   ```bash
   # プロンプトに (venv) が表示されることを確認
   which python3  # venv/bin/python3 を指していることを確認
   ```

### 実行時の注意

- すべてのスクリプトは**仮想環境を有効化した状態**で実行してください
- `python3`ではなく`python3`を使用してください
- 仮想環境が有効化されていない場合は、`ModuleNotFoundError`が発生する可能性があります

---

## 📋 目次

- [目的・シーン別ツール一覧](#目的シーン別ツール一覧)
- [ディレクトリ構造](#ディレクトリ構造)
- [コアモジュール](#コアモジュール)

---

## 目的・シーン別ツール一覧

### 🔄 データ管理

#### データ取得・更新
**シーン**: 過去データを取得・更新したい

| ツール | 場所 | 用途 |
|--------|------|------|
| `fetch_past_results.py` | `scripts/production/` | Webから過去データを取得してCSVに保存 |
| `auto_update_past_results.py` | `scripts/production/` | 抽選日に自動でデータを更新（cron用） |

**使い方**:
```bash
# 仮想環境を有効化（必須）
source venv/bin/activate

# 手動でデータ取得
python3 scripts/production/fetch_past_results.py

# 自動更新（cron設定）
bash scripts/setup_cron.sh
python3 scripts/production/auto_update_past_results.py
```

#### データ確認
**シーン**: データの内容や範囲を確認したい

| ツール | 場所 | 用途 |
|--------|------|------|
| `check_data.py` | `scripts/tools/validation/` | 学習データファイルの簡易確認 |
| `check_data_range.py` | `scripts/tools/validation/` | 学習データ範囲の選定・比較 |
| `check_data_cleaning.py` | `scripts/tools/validation/` | データクリーニング結果の確認 |
| `check_round_data.py` | `scripts/tools/validation/` | 特定回号のデータを詳細確認 |

**使い方**:
```bash
# 仮想環境を有効化（必須）
source venv/bin/activate

# データ範囲を確認
python3 scripts/tools/validation/check_data_range.py

# 特定回号のデータを確認
python3 scripts/tools/validation/check_round_data.py --round 6847 --detailed
```

---

### 🎯 予測実行・検証

#### 予測実行
**シーン**: 新しい回号で予測を実行したい

| ツール | 場所 | 用途 |
|--------|------|------|
| `predict_cli.py` | `scripts/production/` | CLIから予測を実行 |

**使い方**:
```bash
python3 scripts/production/predict_cli.py --round 6849 --n3-rehearsal 149 --n4-rehearsal 3782
```

#### 予測検証
**シーン**: 過去回号で予測精度を検証したい

| ツール | 場所 | 用途 |
|--------|------|------|
| `check_prediction_for_round.py` | `scripts/tools/validation/` | 過去回号での予測結果を確認 |
| `predict_with_winning.py` | `scripts/tools/validation/` | 予測結果を出力して検証 |

**使い方**:
```bash
# 単一回号で検証
python3 scripts/tools/validation/check_prediction_for_round.py --round 6847

# 範囲指定で検証
python3 scripts/tools/validation/check_prediction_for_round.py --range 6840 6849
```

---

### 📊 CUBE生成・可視化

#### CUBE生成
**シーン**: 極CUBEを生成したい

| ツール | 場所 | 用途 |
|--------|------|------|
| `generate_extreme_cube.py` | `scripts/production/` | 極CUBEを生成（5行目0埋め） |

**使い方**:
```bash
python3 scripts/production/generate_extreme_cube.py --round 6849
```

#### CUBE可視化・デバッグ
**シーン**: CUBE生成プロセスを可視化してデバッグしたい

| ツール | 場所 | 用途 |
|--------|------|------|
| `visualize_normal_cube_steps.py` | `scripts/tools/visualization/` | 通常CUBE生成の各ステップを可視化 |
| `visualize_extreme_cube_steps.py` | `scripts/tools/visualization/` | 極CUBE生成の各ステップを可視化 |

**使い方**:
```bash
# 通常CUBEの生成ステップを確認
python3 scripts/tools/visualization/visualize_normal_cube_steps.py --round 6849 --pattern B1 --target n3

# 極CUBEの生成ステップを確認
python3 scripts/tools/visualization/visualize_extreme_cube_steps.py --round 6849
```

#### CUBE出力
**シーン**: CUBEをExcelに貼り付けたい、HTMLで確認したい

| ツール | 場所 | 用途 |
|--------|------|------|
| `export_cube_to_html.py` | `scripts/tools/visualization/` | CUBEをHTML形式で出力（Excel貼り付け可能） |

**使い方**:
```bash
# 通常CUBEをHTML出力
python3 scripts/tools/visualization/export_cube_to_html.py --round 6849 --pattern B1 --target n3

# 極CUBEをHTML出力
python3 scripts/tools/visualization/export_cube_to_html.py --round 6849 --cube-type extreme
```

#### 特徴量可視化
**シーン**: 特徴量の動作を確認したい、リハーサル数字の影響を分析したい

| ツール | 場所 | 用途 |
|--------|------|------|
| `visualize_rehearsal_features.py` | `scripts/tools/visualization/` | リハーサル数字と当選番号の関係性特徴量を可視化 |
| `generate_batch_visualization_data.py` | `scripts/tools/visualization/` | 複数回号・パターンの可視化データを一括生成 |
| `visualization_server.py` | `scripts/tools/visualization/` | HTTPサーバーで可視化データを提供 |

**使い方**:
```bash
# リハーサル特徴量を可視化
python3 scripts/tools/visualization/visualize_rehearsal_features.py 6849

# 可視化サーバーを起動
python3 scripts/tools/visualization/visualization_server.py --port 8000
# ブラウザで http://localhost:8000/?round=6849&pattern=B1&target=n3 にアクセス
```

---

### 🤖 モデル改善

#### 特徴量分析
**シーン**: モデル改善のために重要な特徴量を特定したい

| ツール | 場所 | 用途 |
|--------|------|------|
| `analyze_model_features.py` | `scripts/tools/analysis/` | 学習済みモデルから特徴量重要度を抽出・分析 |
| `analyze_axis_relationship.py` | `scripts/tools/analysis/` | 軸数字と当選番号の関係性を分析 |
| `analyze_rehearsal_relationship.py` | `scripts/tools/analysis/` | リハーサル数字と当選番号の関係性を分析 |
| `select_features.py` | `scripts/tools/analysis/` | 特徴量重要度に基づいて特徴量を選択 |
| `feature_patterns.py` | `scripts/tools/analysis/` | 異なる特徴量セットを比較・実験 |

**使い方**:
```bash
# 特徴量重要度を分析
python3 scripts/tools/analysis/analyze_model_features.py

# 特徴量を選択（重要度の低いものを削除）
python3 scripts/tools/analysis/select_features.py
```

#### ハイパーパラメータ調整
**シーン**: モデルの精度を向上させたい

| ツール | 場所 | 用途 |
|--------|------|------|
| `tune_hyperparameters_v2.py` | `scripts/tools/training/` | XGBoostモデルのハイパーパラメータを最適化 |

**使い方**:
```bash
python3 scripts/tools/training/tune_hyperparameters_v2.py
```

#### 特徴量検証
**シーン**: 新しい特徴量を追加した際に正しく動作するか確認したい

| ツール | 場所 | 用途 |
|--------|------|------|
| `test_new_features.py` | `scripts/tools/training/` | 新規特徴量が正しく計算されることを確認 |

**使い方**:
```bash
python3 scripts/tools/training/test_new_features.py
```

#### 評価結果確認
**シーン**: モデル学習後の評価結果を確認したい

| ツール | 場所 | 用途 |
|--------|------|------|
| `check_evaluation_results.py` | `scripts/tools/validation/` | 保存された評価結果を表示 |

**使い方**:
```bash
# 最新の評価結果を表示
python3 scripts/tools/validation/check_evaluation_results.py

# すべての評価結果を表示
python3 scripts/tools/validation/check_evaluation_results.py --all
```

---

### 🧪 テスト・動作確認

#### 基本テスト
**シーン**: 基本的な動作を確認したい

| ツール | 場所 | 用途 |
|--------|------|------|
| `test-chart-generator.ts` | `scripts/test/` | 予測表生成アルゴリズムの動作確認 |
| `test-4-patterns.ts` | `scripts/test/` | 4パターン（A1/A2/B1/B2）の総合テスト |
| `test-data-loader.ts` | `scripts/test/` | データ読み込みユーティリティの動作確認 |

**使い方**:
```bash
pnpm test:chart-generator
npx tsx scripts/test/test-4-patterns.ts 6758
pnpm test:data-loader
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

## ディレクトリ構造

```
scripts/
├── production/         # 本番スクリプト（4ファイル）
│   ├── fetch_past_results.py
│   ├── auto_update_past_results.py
│   ├── generate_extreme_cube.py
│   └── predict_cli.py
│
├── tools/              # 開発ツール
│   ├── visualization/  # 可視化ツール（8ファイル）
│   ├── analysis/       # 分析ツール（5ファイル）
│   ├── validation/     # 検証ツール（7ファイル）
│   └── training/       # 学習ツール（2ファイル）
│
└── test/               # テストファイル（3ファイル）
    ├── test-chart-generator.ts
    ├── test-4-patterns.ts
    └── test-data-loader.ts
```

---

## コアモジュール

**場所**: `core/`

本番で使用するコアモジュールです。すべてのスクリプトから参照されます。

- `chart_generator.py` - 予測表生成モジュール
- `feature_extractor.py` - 特徴量抽出モジュール
- `model_loader.py` - モデル読み込みユーティリティ
- `config.py` - 設定ファイル

---

## 詳細ドキュメント

各カテゴリの詳細は以下のドキュメントを参照してください：

- [本番スクリプト詳細](production-scripts.md)
- [開発ツール詳細](development-tools.md)
