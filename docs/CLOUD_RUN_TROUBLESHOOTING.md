# Cloud Runデプロイのトラブルシューティング

## 現在の状況

ビルドが失敗しているため、以下の方法でエラー内容を確認してください。

## ビルドログの確認方法

### 方法1: GCPコンソール（推奨）

1. **以下にアクセス**:
   https://console.cloud.google.com/cloud-build/builds?project=numbers-ai

2. **最新のビルドをクリック**

3. **エラー詳細を確認**

### 方法2: gcloud CLI

```bash
# 最新のビルドIDを取得
BUILD_ID=$(gcloud builds list --limit=1 --format='value(id)')

# ビルドログを確認
gcloud builds log $BUILD_ID
```

## よくあるエラーの原因と対処法

### 1. インポートエラー

**症状:** `ModuleNotFoundError` が発生

**対処法:**
- `PYTHONPATH`が正しく設定されているか確認
- `notebooks/`ディレクトリが正しくコピーされているか確認

### 2. モデルファイルが見つからない

**症状:** `FileNotFoundError: data/models/*.pkl`

**対処法:**
- `data/models/`ディレクトリがDockerイメージに含まれているか確認
- `.gcloudignore`で除外されていないか確認

### 3. メモリ不足

**症状:** Out of memory エラー

**対処法:**
- `--memory`を増やす（例: `--memory 4Gi`）

### 4. 依存関係のインストールエラー

**症状:** `pip install`が失敗

**対処法:**
- `requirements.txt`の内容を確認
- 必要なシステムパッケージがインストールされているか確認

## 次のステップ

ビルドログを確認して、エラー内容を特定してください。
エラー内容が分かれば、対応方法を提案します。
