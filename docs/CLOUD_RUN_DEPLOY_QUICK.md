# GCP認証とCloud Runデプロイ手順

## ステップ1: GCP認証

WSL環境で以下のコマンドを実行してください：

```bash
cd /home/ykoha/numbers-ai
gcloud auth login
```

ブラウザが開くので、GCPアカウントでログインしてください。

## ステップ2: GCPプロジェクトの作成

```bash
# プロジェクトを作成（既に存在する場合はスキップ）
gcloud projects create numbers-ai --name="Numbers AI"

# プロジェクトを設定
gcloud config set project numbers-ai

# 必要なAPIを有効化
gcloud services enable run.googleapis.com cloudbuild.googleapis.com
```

## ステップ3: Cloud Runへのデプロイ

```bash
# Cloud Runにデプロイ
gcloud run deploy numbers-ai-api \
  --source . \
  --region asia-northeast1 \
  --allow-unauthenticated \
  --port 8080 \
  --memory 2Gi \
  --timeout 300 \
  --platform managed
```

デプロイが完了すると、URLが表示されます。

## ステップ4: Vercelに環境変数を設定

```bash
vercel env add FASTAPI_URL production
```

プロンプトでCloud RunのURLを入力してください。

