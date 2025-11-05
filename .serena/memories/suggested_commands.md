# 推奨コマンドリスト

## 開発サーバー
```bash
# Next.js開発サーバー起動
pnpm dev

# ビルド
pnpm build

# 本番環境起動
pnpm start
```

## テスト
```bash
# データローダーテスト
pnpm test:data-loader

# チャート生成テスト
pnpm test:chart-generator

# 4パターンテスト
pnpm test:patterns

# API統合テスト
pnpm test:api
# または
bash scripts/test-api.sh
```

## リント・フォーマット
```bash
# Lint実行
pnpm lint

# Lint修正（自動修正なしの場合は手動で修正）
# package.jsonにlint:fixスクリプトがないため、必要に応じて追加
```

## FastAPIサーバー
```bash
# apiディレクトリに移動
cd api

# 仮想環境をアクティベート（初回のみ）
python -m venv venv
source venv/bin/activate  # WSL/Linuxの場合

# 依存関係をインストール（初回のみ）
pip install -r requirements.txt

# サーバー起動
python run.py
# または
bash start.sh
```

## データ処理（Jupyter Notebook）
```bash
# notebooksディレクトリに移動
cd notebooks

# Jupyter Notebook起動
jupyter notebook

# または JupyterLab起動
jupyter lab
```

## CLI予測ツール
```bash
cd notebooks

# コマンドライン引数で実行
python predict_cli.py --round 6758 --n3-rehearsal 149 --n4-rehearsal 3782

# 対話的に実行
python predict_cli.py
```

## システムユーティリティ（WSL/Linux環境）
```bash
# ファイル検索
find . -name "*.ts" -type f

# パターン検索
grep -r "pattern" src/

# ディレクトリ一覧
ls -la

# Git操作
git status
git add .
git commit -m "message"
git push
```

## 環境変数設定
```bash
# .env.localファイルを作成（存在しない場合）
echo "FASTAPI_URL=http://localhost:8000" > .env.local

# 環境変数確認
cat .env.local
```

## データ確認
```bash
# CSVデータ確認
head -n 20 data/past_results.csv

# JSONデータ確認
cat data/keisen_master.json | jq .

# モデルファイル確認
ls -lh data/models/
```