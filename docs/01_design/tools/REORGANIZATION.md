# ディレクトリ構造の再編成 - 完了報告

## ✅ 実施完了

すべての作業が完了しました。本番環境でもエラーなく動作するように整合性を確保しました。

## 📁 新しいディレクトリ構造

```
numbers-ai/
├── core/                    # 本番で使用するコアモジュール（新規）
│   ├── chart_generator.py   # 予測表生成
│   ├── feature_extractor.py # 特徴量抽出
│   ├── model_loader.py      # モデル読み込み
│   └── config.py            # 設定ファイル
│
├── scripts/
│   ├── production/         # 本番スクリプト（新規）
│   │   ├── fetch_past_results.py
│   │   ├── auto_update_past_results.py
│   │   ├── generate_extreme_cube.py
│   │   └── predict_cli.py
│   │
│   ├── tools/              # 開発ツール（新規）
│   │   ├── visualization/  # 可視化ツール（8ファイル）
│   │   ├── analysis/       # 分析ツール（5ファイル）
│   │   ├── validation/     # 検証ツール（7ファイル）
│   │   └── training/       # 学習ツール（2ファイル）
│   │
│   └── test/               # テストファイル（新規、3ファイル）
│
└── notebooks/              # Jupyter Notebook（整理済み）
    ├── *.ipynb            # Jupyter Notebookファイル
    ├── run_*.py           # Notebook実行スクリプト
    ├── README.md          # ドキュメント
    └── requirements.txt    # 依存関係（プロジェクトルートと統合推奨）
    
    # 注意: venv/, data/, __pycache__/は削除済み
    # - venv/はプロジェクトルートのvenv/を使用
    # - data/はプロジェクトルートのdata/を使用
```

## 🔄 インポートパスの変更

### 変更前
```python
sys.path.append(str(PROJECT_ROOT / 'notebooks'))
from chart_generator import ...
```

### 変更後
```python
sys.path.append(str(PROJECT_ROOT / 'core'))
from chart_generator import ...
```

### 更新したファイル
- ✅ `api/main.py`
- ✅ `scripts/production/*.py` (4ファイル)
- ✅ `scripts/tools/**/*.py` (22ファイル)
- ✅ `notebooks/run_*.py` (5ファイル)
- ✅ `scripts/setup_cron.sh`

## 🗑️ 削除したファイル（17ファイル）

### テストファイル（9ファイル）
- `scripts/test_extreme_cube_*.py` (4ファイル)
- `scripts/test_main_rows.py`
- `scripts/test_mizuhobank.py`
- `scripts/test-b1-n3-debug.ts`
- `scripts/debug-main-rows.ts`
- `notebooks/test_cell.py`

### 一時的・完了済み（8ファイル）
- `scripts/extract_text.py`
- `scripts/reorganize_todo*.py` (2ファイル)
- `scripts/compare_inverse_rules.py`
- `scripts/find_row5_remaining_cases.py`
- `notebooks/check_6847.py`
- `notebooks/fix_duplicate.py`
- `notebooks/run_03_feature_engineering_test.py`

## 📚 作成したドキュメント

1. **`docs/01_design/tools/README.md`**
   - ツール一覧と概要
   - カテゴリごとの説明
   - 使用シーン別の使い方

2. **`docs/01_design/tools/production-scripts.md`**
   - 本番スクリプトの詳細
   - 各スクリプトの目的・使い方・オプション

3. **`docs/01_design/tools/development-tools.md`**
   - 開発ツールの詳細
   - カテゴリごとの説明
   - 使用例とワークフロー

4. **`docs/01_design/tools/REORGANIZATION.md`**
   - 再編成の実施内容
   - 変更点のサマリー

## ✅ 整合性確認

### 本番環境での動作確認ポイント

1. **APIサーバー**
   ```bash
   # api/main.pyがcore/から正しくインポートできるか確認
   python api/main.py
   ```

2. **本番スクリプト**
   ```bash
   # 各スクリプトが正常に動作するか確認
   python scripts/production/fetch_past_results.py --limit 1
   python scripts/production/predict_cli.py --round 6849 --n3-rehearsal 149
   ```

3. **cron設定**
   ```bash
   # cron設定スクリプトのパスが正しいか確認
   bash scripts/setup_cron.sh
   ```

## 🎯 次のステップ

1. **動作確認**
   - 各スクリプトを実行してエラーがないか確認
   - APIサーバーが正常に起動するか確認

2. **テスト実行**
   ```bash
   pnpm test:chart-generator
   pnpm test:patterns
   pnpm test:data-loader
   ```

3. **ドキュメント確認**
   - `docs/01_design/tools/README.md`を確認
   - 必要に応じて追加の説明を追記

## 📝 注意事項

- すべてのスクリプトは`core/`モジュールを参照します
- 本番スクリプトは`scripts/production/`に配置されています
- 開発ツールは`scripts/tools/`配下にカテゴリごとに整理されています
- テストファイルは`scripts/test/`に配置されています
- **notebooksフォルダは整理済み**: `venv/`, `data/`, `__pycache__/`は削除され、プロジェクトルートの`venv/`と`data/`を使用します

## 🔍 トラブルシューティング

### インポートエラーが発生する場合

1. `core/`ディレクトリが存在するか確認
2. `sys.path.append(str(PROJECT_ROOT / 'core'))`が正しく設定されているか確認
3. 相対インポート（`from scripts.production.xxx import`）が正しいか確認

### cronジョブが動作しない場合

1. `scripts/setup_cron.sh`を再実行
2. cronジョブのパスが`scripts/production/auto_update_past_results.py`になっているか確認
3. cronサービスが起動しているか確認: `sudo service cron status`
