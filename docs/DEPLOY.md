# Vercelデプロイガイド

## 前提条件

- GitHubリポジトリにコードがプッシュされていること
- Vercelアカウントを作成済みであること
- FastAPIサーバーを別途デプロイ済みであること（Cloud Run、Heroku、Railway等）

## デプロイ手順

### 1. Vercelプロジェクトの作成

1. [Vercelダッシュボード](https://vercel.com/dashboard)にログイン
2. 「Add New...」→「Project」をクリック
3. GitHubリポジトリを選択
4. プロジェクト設定を確認

### 2. 環境変数の設定

Vercelダッシュボードで以下の環境変数を設定：

- `FASTAPI_URL`: FastAPIサーバーのURL（例: `https://your-fastapi-server.com`）

**設定方法:**
1. プロジェクト設定 → 「Environment Variables」
2. 「Add New」をクリック
3. Name: `FASTAPI_URL`
4. Value: FastAPIサーバーのURL
5. Environment: Production, Preview, Development すべてにチェック
6. 「Save」をクリック

### 3. ビルド設定

Vercelは自動的にNext.jsを検出しますが、カスタム設定が必要な場合は `vercel.json` を作成：

```json
{
  "buildCommand": "pnpm build",
  "devCommand": "pnpm dev",
  "installCommand": "pnpm install",
  "framework": "nextjs",
  "regions": ["nrt1"]
}
```

### 4. デプロイの実行

- **初回デプロイ**: GitHubにプッシュすると自動的にデプロイが開始されます
- **再デプロイ**: `main`ブランチにプッシュすると自動的に再デプロイされます

### 5. 動作確認

1. デプロイ完了後、Vercelから提供されるURLにアクセス
2. 予測機能が正常に動作するか確認
3. ブラウザの開発者ツールでエラーがないか確認

## 注意事項

### FastAPIサーバーのデプロイ

FastAPIサーバーは別途デプロイする必要があります。推奨プラットフォーム：

- **Google Cloud Run**: サーバーレス、自動スケーリング
- **Railway**: 簡単なデプロイ、自動SSL
- **Heroku**: 無料プランあり（制限あり）
- **Render**: 無料プランあり

### データファイルの配置

MVP版では、以下のファイルをVercelに含める必要があります：

- `data/past_results.csv`: 過去データ
- `data/keisen_master.json`: 罫線マスターデータ
- `data/models/*.pkl`: 学習済みモデル（サイズが大きい場合は外部ストレージ推奨）

**注意**: モデルファイルが大きい場合（100MB以上）、Vercelの制限に引っかかる可能性があります。その場合は：

- 外部ストレージ（AWS S3、Google Cloud Storage等）を使用
- CDN経由でモデルファイルを配信

### CORS設定

FastAPIサーバーでCORSを適切に設定してください：

```python
# api/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://your-vercel-app.vercel.app",
        "http://localhost:3000",  # 開発環境用
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## トラブルシューティング

### ビルドエラー

- `pnpm install` が失敗する場合: `package.json`の依存関係を確認
- TypeScriptエラー: `tsconfig.json`の設定を確認
- メモリ不足: Vercelのプランをアップグレード

### 環境変数が読み込まれない

- 環境変数が正しく設定されているか確認
- デプロイ後に環境変数を追加した場合は、再デプロイが必要

### API接続エラー

- FastAPIサーバーが起動しているか確認
- `FASTAPI_URL`が正しく設定されているか確認
- CORS設定を確認

## 次のステップ

デプロイ完了後：

1. パフォーマンステストを実施
2. エラーログを監視
3. ユーザーフィードバックを収集
4. 必要に応じて最適化を実施

