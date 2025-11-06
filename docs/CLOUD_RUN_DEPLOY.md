# Cloud RunでFastAPIサーバーをデプロイする手順

## 前提条件
- Google Cloud Platform（GCP）アカウント
- gcloud CLIがインストールされていること
- Dockerがインストールされていること（ローカルビルドの場合）

## アーキテクチャ

```
Vercel（Next.js） → Cloud Run（FastAPI + AIモデル） → 予測結果
```

## デプロイ手順

### 1. Google Cloudプロジェクトの作成

```bash
# GCPプロジェクトを作成（既にあればスキップ）
gcloud projects create numbers-ai-backend --name="Numbers AI Backend"

# プロジェクトを設定
gcloud config set project numbers-ai-backend

# Cloud Run APIを有効化
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
```

### 2. Dockerfileの確認

`api/Dockerfile`が作成済みです。内容を確認してください。

### 3. Cloud Runへのデプロイ

**方法1: gcloud CLIでデプロイ（推奨）**

```bash
# プロジェクトルートで実行
gcloud run deploy numbers-ai-api \
  --source . \
  --region asia-northeast1 \
  --allow-unauthenticated \
  --port 8080 \
  --memory 2Gi \
  --timeout 300 \
  --platform managed
```

**重要な設定:**
- `--port 8080`: Cloud Runのデフォルトポート
- `--memory 2Gi`: モデルファイルを読み込むため、メモリを多めに設定
- `--timeout 300`: 予測処理に時間がかかる場合があるため、タイムアウトを長めに設定

### 4. デプロイURLの取得

デプロイ後にURLが表示されます：
```
Service URL: https://numbers-ai-api-xxxxx-xx.a.run.app
```

### 5. CORS設定の更新

`api/main.py`のCORS設定を更新してください：

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://numbers-ai.vercel.app",  # VercelのURL
        "http://localhost:3000",  # 開発環境用
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 6. Vercelに環境変数を設定

```bash
vercel env add FASTAPI_URL production
# プロンプトでCloud RunのURLを入力
```

## 予測モデルを更新した場合の対応

### ⚠️ 重要: モデル更新時は再デプロイが必要

現在のコードは、**コンテナイメージに含まれるファイルからモデルを読み込みます**。

**更新手順:**

```bash
# 1. モデルファイルを更新
# data/models/*.pkl を更新

# 2. GitHubにコミット・プッシュ
git add data/models/*.pkl
git commit -m "feat: 予測モデルを更新"
git push origin main

# 3. Cloud Runを再デプロイ（必須）
gcloud run deploy numbers-ai-api --source .
```

**理由:**
- Cloud Runのコンテナ内のファイルは不変（再デプロイしない限り更新されない）
- 現在のコード（`load_data_and_models()`）はファイルシステム上のファイル更新を検知するが、Cloud Runでは動作しない
- 自動リロード機能（`_file_mtimes`チェック）は、ローカルファイルシステム前提

### 将来の改善案: GCSから読み込む

モデル更新頻度が高い場合や、ダウンタイムを避けたい場合は、Google Cloud Storage（GCS）から読み込むように修正できます：

```python
# api/main.pyを修正
from google.cloud import storage

def load_model_from_gcs(bucket_name, blob_name):
    """GCSからモデルを読み込む"""
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    # モデルをダウンロードして読み込む
    ...
```

**メリット:**
- モデル更新時に再デプロイ不要
- ダウンタイムなし
- モデルファイルのサイズ制限なし

**デメリット:**
- コード修正が必要
- GCSの設定が必要

## 現在の推奨アプローチ

**MVP段階:**
- コンテナイメージに含める方法で問題なし
- モデル更新頻度が低い場合（週1回程度）は再デプロイで対応可能

**手順:**
1. モデルファイルを更新
2. GitHubにプッシュ
3. Cloud Runを再デプロイ（1コマンドで完了）

## トラブルシューティング

### ビルドエラー

- `venv/`ディレクトリが含まれている場合は、`.gitignore`で除外されているか確認
- モデルファイルが大きい場合（100MB以上）、Git LFSを使用するか、GCSから読み込む方法に変更

### メモリ不足エラー

- `--memory`を増やす（例: `--memory 4Gi`）

### タイムアウトエラー

- `--timeout`を増やす（例: `--timeout 600`）

## 次のステップ

1. GCPプロジェクトを作成
2. Cloud Runにデプロイ
3. URLを取得
4. Vercelに環境変数を設定
5. 動作確認
