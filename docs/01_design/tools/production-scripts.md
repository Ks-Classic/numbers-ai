# 本番スクリプト詳細

**場所**: `scripts/production/`

本番環境で実行されるスクリプトの詳細ドキュメントです。

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
- 例: `python3 scripts/production/fetch_past_results.py`

---

## 📋 使用シーン別

### 🔄 データ管理

#### データ取得・更新が必要な時

**`fetch_past_results.py`** - 過去データ取得

**目的**: ナンバーズの過去当選番号・リハーサル番号をWebページから取得してCSVに保存

**使用シーン**:
- 手動でデータを更新したい場合
- 初回データ取得時
- データが古いと感じた時

**使い方**:
```bash
# 基本（デフォルト: data/past_results.csv）
python3 scripts/production/fetch_past_results.py

# 出力ファイルを指定
python3 scripts/production/fetch_past_results.py data/past_results.csv

# 取得件数を制限
python3 scripts/production/fetch_past_results.py --limit 100

# 最新の1回分のみ取得してマージ（cron用）
python3 scripts/production/fetch_past_results.py --merge
```

**オプション**:
- `output_file`: 出力ファイルパス（デフォルト: `data/past_results.csv`）
- `--limit N`: 取得する最大件数（デフォルト: 300）
- `--use-fallback`: Webスクレイピング失敗時に検索APIを使用
- `--merge`: 最新の1回分のみ取得して既存CSVとマージ

**データソース**:
- https://www.hpfree.com/numbers/rehearsal.html
- https://www.mizuhobank.co.jp/takarakuji/check/numbers/backnumber/ (4800回以前)

---

**`auto_update_past_results.py`** - 自動データ更新

**目的**: 抽選日を判定し、必要に応じて`fetch_past_results.py`を実行してデータを自動更新

**使用シーン**:
- cronジョブで定期実行したい場合（推奨）
- 手動でテスト実行したい場合

**使い方**:
```bash
# 基本実行
python3 scripts/production/auto_update_past_results.py
```

**cron設定**:
```bash
# cron設定スクリプトを実行（推奨）
bash scripts/setup_cron.sh

# 手動でcron設定
crontab -e
# 以下を追加:
# 0 15 * * 1-5 cd /path/to/numbers-ai && python3 scripts/production/auto_update_past_results.py >> logs/cron.log 2>&1
```

**動作**:
1. 今日が抽選日（月〜金）か判定
2. 抽選日でない場合はスキップ
3. 抽選日の場合は`fetch_past_results.py --merge`を実行
4. ログを`logs/data_update_YYYY-MM-DD.log`に出力

---

### 🎯 予測実行

#### 予測を実行したい時

**`predict_cli.py`** - CLI予測実行

**目的**: コマンドラインから予測を実行

**使用シーン**:
- コマンドラインから予測を実行したい場合
- デバッグや検証時
- スクリプトから予測を呼び出したい場合

**使い方**:
```bash
# 対話的に実行
python3 scripts/production/predict_cli.py

# 引数で指定
python3 scripts/production/predict_cli.py --round 6758 --n3-rehearsal 149 --n4-rehearsal 3782

# N3のみ
python3 scripts/production/predict_cli.py --round 6758 --n3-rehearsal 149

# N4のみ
python3 scripts/production/predict_cli.py --round 6758 --n4-rehearsal 3782
```

**オプション**:
- `--round N`: 回号（必須）
- `--n3-rehearsal NNN`: N3リハーサル数字（3桁）
- `--n4-rehearsal NNNN`: N4リハーサル数字（4桁）

**出力**:
- 軸数字予測結果（各パターン×各数字のスコア）
- 組み合わせ予測結果（ボックス/ストレート）

---

### 📊 CUBE生成

#### 極CUBEを生成したい時

**`generate_extreme_cube.py`** - 極CUBE生成

**目的**: 極CUBEを生成（5行目の余りマスを0で埋める）

**使用シーン**:
- 極CUBEが必要な場合
- 本番で極CUBEを生成する場合

**使い方**:
```bash
# 基本（回号指定）
python3 scripts/production/generate_extreme_cube.py --round 6849

# 出力ディレクトリを指定
python3 scripts/production/generate_extreme_cube.py --round 6849 --output-dir data/extreme_cubes

# 複数回号を一括生成
python3 scripts/production/generate_extreme_cube.py --round 6849 --round 6850 --round 6851
```

**オプション**:
- `--round N`: 回号（必須、複数指定可能）
- `--output-dir DIR`: 出力ディレクトリ（デフォルト: `data/extreme_cubes`）
- `--verbose`: 詳細ログを出力

**出力**:
- `data/extreme_cubes/n3/round_NNNN.json`: 極CUBEデータ（JSON形式）

**特徴**:
- N3のみ対応（N4は対象外）
- B1パターンと同じ（欠番補足なし、中心0配置なし）
- 最大5行まで（メイン行1,3,5行目）
- 5行目の余りマスを0で埋める

---

## 依存関係

すべてのスクリプトは`core/`モジュールを参照します：

- `core/chart_generator.py` - 予測表生成
- `core/feature_extractor.py` - 特徴量抽出
- `core/model_loader.py` - モデル読み込み
- `core/config.py` - 設定

---

## エラーハンドリング

- すべてのスクリプトは適切なエラーメッセージを出力します
- `auto_update_past_results.py`はログファイルに記録します
- エラー時は適切な終了コードを返します

---

## ログ

- `auto_update_past_results.py`: `logs/data_update_YYYY-MM-DD.log`
- cron実行: `logs/cron.log`
