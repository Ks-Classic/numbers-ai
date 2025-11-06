# RailwayでFastAPIサーバーをデプロイする手順

## 前提条件
- GitHubアカウント（既にリポジトリにプッシュ済み）
- Railwayアカウント（無料で作成可能）

## デプロイ手順

### 1. Railwayアカウントの作成
1. https://railway.app にアクセス
2. 「Start a New Project」をクリック
3. 「Login with GitHub」をクリックしてGitHubアカウントでログイン

### 2. プロジェクトの作成とデプロイ
1. 「New Project」をクリック
2. 「Deploy from GitHub repo」を選択
3. `Ks-Classic/numbers-ai` リポジトリを選択
4. Railwayが自動的にFastAPIを検出してデプロイを開始します

### 3. Root Directoryの設定（重要）

**設定場所:**
1. Railwayダッシュボードで、作成したプロジェクトをクリック
2. デプロイされたサービス（Service）をクリック
3. 上部のタブから **「Settings」** をクリック
4. 「Settings」ページを下にスクロール
5. **「Source」** セクションまたは **「Build & Deploy」** セクションに **「Root Directory」** という項目があります
6. 「Root Directory」の値を変更：
   - デフォルト: `/`（空欄または`.`）
   - 変更後: `api`
7. 「Save」または「Update」をクリック
8. 自動的に再デプロイが開始されます

**スクリーンショットのイメージ:**
```
Railway Dashboard
├─ Your Project
   └─ Service (numbers-ai)
      ├─ Deployments（タブ）
      ├─ Metrics（タブ）
      ├─ Logs（タブ）
      ├─ Settings（タブ）← ここをクリック
      │   └─ Scroll down
      │       └─ Sourceセクション
      │           └─ Root Directory: [api] ← ここを変更
      └─ Variables（タブ）
```

### 4. 環境変数の設定（必要に応じて）
現在は不要ですが、今後必要になった場合は：
1. サービス画面で **「Variables」** タブをクリック
2. 「+ New Variable」をクリック
3. 必要な環境変数を追加（例: `PYTHON_VERSION=3.12`）

### 5. ポート設定の確認
Railwayは自動的に`$PORT`環境変数を設定しますが、現在のコードはポート8000固定です。
必要に応じて`api/run.py`を修正してください（現在はそのままで動作する可能性があります）。

### 6. デプロイURLの取得
1. デプロイ完了後、サービス画面で **「Settings」** タブを開く
2. **「Networking」** セクションまたは **「Domains」** セクションでURLを確認
3. 「Generate Domain」をクリックすると、URLが生成されます（例: `https://numbers-ai-api.railway.app`）
4. このURLをコピー

### 7. Vercelに環境変数を設定
```bash
# Vercel CLIを使用
vercel env add FASTAPI_URL production
# プロンプトでRailwayのURLを入力: https://numbers-ai-api.railway.app
```

または、Vercelダッシュボードで：
1. プロジェクト設定 → 「Environment Variables」
2. 「Add New」をクリック
3. Name: `FASTAPI_URL`
4. Value: RailwayのURL（例: `https://numbers-ai-api.railway.app`）
5. Environment: Production, Preview, Development すべてにチェック
6. 「Save」をクリック

### 8. Vercelを再デプロイ
環境変数を追加した後、Vercelを再デプロイしてください。

## トラブルシューティング

### Root Directoryが見つからない場合
- RailwayのUIが更新されている可能性があります
- 代わりに `railway.json` ファイルを作成して設定することもできます（後述）

### ビルドエラーが発生する場合
- **Root Directory**が`api`に設定されているか確認
- `requirements.txt`が`api/`ディレクトリにあるか確認
- Railwayのログを確認（「Deployments」→「View Logs」）

### ポートエラーが発生する場合
- Railwayは自動的に`$PORT`環境変数を設定します
- 必要に応じて`api/run.py`を修正してポートを環境変数から取得するように設定

### モデルファイルが見つからないエラー
- Railwayにファイルをアップロードする必要があります
- 方法1: GitHubリポジトリに含める（推奨）
- 方法2: RailwayのVolume機能を使用

## railway.jsonを使う方法（代替）

Root Directoryを設定ファイルで指定する場合：

**プロジェクトルートに `railway.json` を作成:**
```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS",
    "buildCommand": "pip install -r api/requirements.txt"
  },
  "deploy": {
    "startCommand": "cd api && uvicorn main:app --host 0.0.0.0 --port $PORT",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

ただし、通常はUIから設定する方が簡単です。

## 注意事項

### モデルファイルのサイズ
- `data/models/*.pkl`ファイルが大きい場合（100MB以上）、GitHubに直接プッシュできない可能性があります
- その場合は、Git LFSを使用するか、外部ストレージ（AWS S3、Google Cloud Storage）を使用

### コスト
- Railwayの無料プランには制限があります
- 本番環境で重要な場合は、有料プランへのアップグレードを検討してください

## 次のステップ

デプロイ完了後：
1. RailwayのURLでヘルスチェック: `https://your-app.railway.app/health`
2. Vercelに環境変数を設定
3. Vercelを再デプロイ
4. 動作確認
