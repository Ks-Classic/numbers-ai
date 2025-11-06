# 環境変数設定ガイド

## 開発環境のセットアップ

### 1. 環境変数ファイルの作成

プロジェクトルートに `.env.local` ファイルを作成してください：

```bash
# FastAPIサーバーのURL
FASTAPI_URL=http://localhost:8000

# データ更新用APIキー（オプション）
# Webスクレイピングに失敗した場合のフォールバック機能で使用
# Gemini API: https://makersuite.google.com/app/apikey
GEMINI_API_KEY=your_gemini_api_key_here

# SerpAPI (Google Search API): https://serpapi.com/
SERP_API_KEY=your_serp_api_key_here
```

**注意**: APIキーは必須ではありません。Webスクレイピングが正常に動作する場合は設定不要です。

### 2. FastAPIサーバーの起動

```bash
# apiディレクトリに移動
cd api

# 仮想環境を有効化（初回のみ）
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 依存関係をインストール（初回のみ）
pip install -r requirements.txt

# サーバーを起動
python3 run.py
```

FastAPIサーバーは `http://localhost:8000` で起動します。

### 3. Next.js開発サーバーの起動

別のターミナルで：

```bash
# プロジェクトルートに戻る
cd ..

# 依存関係をインストール（初回のみ）
pnpm install

# 開発サーバーを起動
pnpm dev
```

Next.jsアプリは `http://localhost:3000` で起動します。

## 本番環境（Vercel）の設定

Vercelダッシュボードで以下の環境変数を設定してください：

- `FASTAPI_URL`: FastAPIサーバーのURL（例: `https://your-fastapi-server.com`）

## 動作確認

1. FastAPIサーバーが起動していることを確認：
   ```bash
   curl http://localhost:8000/health
   ```

2. Next.jsアプリからAPIを呼び出して予測を実行

3. ブラウザの開発者ツールでネットワークエラーがないか確認

## トラブルシューティング

### FastAPIサーバーに接続できない

- FastAPIサーバーが起動しているか確認
- `FASTAPI_URL` が正しく設定されているか確認
- ファイアウォールでポート8000がブロックされていないか確認

### 予測APIがタイムアウトする

- FastAPIサーバーのログを確認
- モデルファイルが正しく配置されているか確認（`data/models/*.pkl`）
- データファイルが正しく配置されているか確認（`data/past_results.csv`）

