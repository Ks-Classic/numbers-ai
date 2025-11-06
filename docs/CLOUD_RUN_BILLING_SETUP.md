# GCP請求アカウントの設定手順

## エラーについて

Cloud Runを使用するには、GCPプロジェクトに請求アカウントをリンクする必要があります。

**重要:**
- Cloud Runには**無料枠**があります（月間200万リクエストまで無料）
- 無料枠内であれば**課金されません**
- ただし、請求アカウントのリンクは必須です

## 解決方法

### 方法1: GCPコンソールで設定（推奨）

1. **GCPコンソールにアクセス**
   - https://console.cloud.google.com/billing/linkedaccount?project=numbers-ai

2. **請求アカウントをリンク**
   - 「請求アカウントをリンク」をクリック
   - 既存の請求アカウントを選択、または新規作成
   - 無料トライアル（$300クレジット）を開始できます

3. **APIを有効化**
   ```bash
   gcloud services enable run.googleapis.com cloudbuild.googleapis.com
   ```

### 方法2: gcloud CLIで設定

```bash
# 請求アカウントのリストを確認
gcloud billing accounts list

# 請求アカウントをプロジェクトにリンク
gcloud billing projects link numbers-ai --billing-account=BILLING_ACCOUNT_ID
```

`BILLING_ACCOUNT_ID`は、`gcloud billing accounts list`で確認できます。

## Cloud Runの無料枠

- **月間200万リクエストまで無料**
- **CPU時間**: 月間360,000 vCPU秒まで無料
- **メモリ**: 月間400,000 GB秒まで無料
- **ネットワーク**: 月間1GBの送信まで無料

**MVP段階では無料枠内で運用可能です。**

## 請求アカウント設定後のデプロイ

請求アカウントを設定したら、再度デプロイを実行：

```bash
gcloud run deploy numbers-ai-api \
  --source . \
  --region asia-northeast1 \
  --allow-unauthenticated \
  --port 8080 \
  --memory 2Gi \
  --timeout 300 \
  --platform managed
```

## 参考リンク

- [Cloud Run料金](https://cloud.google.com/run/pricing)
- [GCP無料トライアル](https://cloud.google.com/free)

