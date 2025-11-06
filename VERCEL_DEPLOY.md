# Vercelデプロイクイックスタート

## 前提条件

- GitHubリポジトリにコードがプッシュされていること
- Vercelアカウントを作成済みであること（https://vercel.com/ks-classic/numbers-ai）

## デプロイ手順

### 1. GitHubリポジトリをVercelに接続

1. [Vercelダッシュボード](https://vercel.com/dashboard)にログイン
2. 「Add New...」→「Project」をクリック
3. GitHubリポジトリ `numbers-ai` を選択
4. プロジェクト名: `numbers-ai` を確認

### 2. ビルド設定の確認

Vercelは自動的にNext.jsを検出します。`vercel.json`が作成されているので、その設定が使用されます：

- Framework: Next.js
- Build Command: `pnpm build`
- Install Command: `pnpm install`
- Output Directory: `.next`
- Region: `nrt1` (東京)

### 3. 環境変数の設定

**重要**: Vercelダッシュボードで以下の環境変数を設定してください：

1. プロジェクト設定 → 「Environment Variables」を開く
2. 以下の環境変数を追加：

| 名前 | 値 | 環境 |
|------|-----|------|
| `FASTAPI_URL` | FastAPIサーバーのURL（後述） | Production, Preview, Development |

**FastAPIサーバーのURLについて:**
- FastAPIサーバーは別途デプロイが必要です（Railway、Cloud Run等）
- デプロイ完了後、そのURLを`FASTAPI_URL`に設定してください
- 開発環境では `http://localhost:8000` を使用

### 4. 初回デプロイの実行

1. 「Deploy」ボタンをクリック
2. デプロイが完了するまで待機（数分かかります）
3. デプロイ完了後、提供されるURL（例: `https://numbers-ai.vercel.app`）にアクセス

### 5. 動作確認

1. ブラウザでデプロイされたURLにアクセス
2. 予測機能が正常に動作するか確認
3. ブラウザの開発者ツール（F12）でエラーがないか確認

## FastAPIサーバーのデプロイについて

FastAPIサーバー（`api/main.py`）はVercelでは動作しません。別途以下のいずれかのプラットフォームにデプロイしてください：

### 推奨プラットフォーム

1. **Railway** (推奨)
   - 簡単なデプロイ、自動SSL
   - 無料プランあり
   - URL: https://railway.app

2. **Google Cloud Run**
   - サーバーレス、自動スケーリング
   - 従量課金
   - URL: https://cloud.google.com/run

3. **Render**
   - 無料プランあり
   - 自動SSL
   - URL: https://render.com

### FastAPIサーバーデプロイ後の設定

FastAPIサーバーをデプロイしたら：

1. FastAPIサーバーのURLを取得（例: `https://numbers-ai-api.railway.app`）
2. Vercelダッシュボードで`FASTAPI_URL`環境変数を更新
3. FastAPIサーバーのCORS設定を更新（`api/main.py`）：
   ```python
   allow_origins=[
       "https://numbers-ai.vercel.app",  # VercelのURL
       "http://localhost:3000",  # 開発環境用
   ]
   ```
4. Vercelを再デプロイ（環境変数更新後）

## トラブルシューティング

### ビルドエラー

- `pnpm install`が失敗する場合：
  - `package.json`の依存関係を確認
  - Node.jsバージョンを20に設定（Vercelダッシュボード → Settings → Node.js Version）

### 環境変数が読み込まれない

- 環境変数を追加/変更した場合は、再デプロイが必要です
- Vercelダッシュボード → Deployments → 「Redeploy」をクリック

### API接続エラー

- FastAPIサーバーが起動しているか確認
- `FASTAPI_URL`が正しく設定されているか確認
- CORS設定を確認（FastAPIサーバー側）
- ブラウザの開発者ツール → Networkタブでエラーを確認

### モデルファイルのサイズ制限

- Vercelの無料プランでは、ファイルサイズに制限があります
- モデルファイル（`data/models/*.pkl`）が大きい場合（100MB以上）は、外部ストレージ（AWS S3、Google Cloud Storage等）を使用することを検討してください

## 次のステップ

デプロイ完了後：

1. ✅ パフォーマンステストを実施
2. ✅ エラーログを監視（Vercelダッシュボード → Logs）
3. ✅ ユーザーフィードバックを収集
4. ✅ 必要に応じて最適化を実施

## 参考リンク

- [Vercelドキュメント](https://vercel.com/docs)
- [Next.jsデプロイメントガイド](https://nextjs.org/docs/deployment)
- [FastAPIデプロイメントガイド](https://fastapi.tiangolo.com/deployment/)

