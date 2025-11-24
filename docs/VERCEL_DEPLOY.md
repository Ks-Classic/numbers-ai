# Vercel本番デプロイ手順（ARM64環境対応版）

**最終更新**: 2025-11-24  
**対象環境**: Windows ARM64 + WSL (Ubuntu ARM64) → Vercel (Linux x86_64)

## 前提条件

- GitHubリポジトリにコードがプッシュされていること
- Vercelアカウントを作成済みであること
- **重要**: ARM64環境（Snapdragon X搭載PC）からのデプロイであることを理解していること

## アーキテクチャ不一致の理解

### 問題
- **ローカル環境**: Windows ARM64 + WSL (Ubuntu ARM64)
- **Vercel環境**: Linux x86_64
- **影響**: バイナリライブラリ（`.so`ファイル）の互換性がない

### 解決策: 「クリーンクラウドビルド + libgomp手動注入」

| 方法 | サイズ | 成功率 | 採用 |
|------|--------|--------|------|
| 完全クリーンビルド | - | ❌ 0% | ❌ |
| scikit-learn追加 | 250MB超過 | ❌ 0% | ❌ |
| **libgomp手動注入** | **164KB** | **✅ 100%** | **✅** |

## デプロイ手順

### 1. Vercelプロジェクトの作成

1. [Vercelダッシュボード](https://vercel.com/dashboard)にログイン
2. 「Add New...」→「Project」をクリック
3. GitHubリポジトリ `numbers-ai` を選択
4. プロジェクト設定を確認

### 2. 環境変数の設定（オプション）

Vercelダッシュボードで以下の環境変数を設定（AI推論機能を使用する場合のみ）：

- `FASTAPI_URL`: FastAPIサーバーのURL（使用しない場合は不要）
- `USE_VERCEL_PYTHON`: `true`（Vercel Python Serverless Functionsを使用）

**設定方法:**
1. プロジェクト設定 → 「Environment Variables」
2. 「Add New」をクリック
3. Name: `USE_VERCEL_PYTHON`, Value: `true`
4. Environment: Production, Preview, Development すべてにチェック
5. 「Save」をクリック

### 3. ビルド設定の確認

`vercel.json` が正しく設定されていることを確認：

```json
{
  "functions": {
    "api/**/*.py": {
      "runtime": "python3.12",
      "memory": 1024,
      "maxDuration": 60
    }
  }
}
```

### 4. ARM64対応の確認

以下のファイルが正しく配置されていることを確認：

- ✅ `api/lib/libgomp.so.1` (x86_64版、164KB)
- ✅ `api/predict/requirements.txt` (scikit-learn除外)
- ✅ `api/predict/axis.py` (libgomp手動ロード処理あり)
- ✅ `api/predict/combination.py` (libgomp手動ロード処理あり)
- ❌ `venv/` (`.gitignore`で除外されていること)

### 5. デプロイの実行

#### 初回デプロイ
```bash
vercel deploy --force
```

#### 本番環境デプロイ
```bash
vercel --prod --force
```

`--force` オプションは、ビルドキャッシュをクリアして完全に再ビルドします。

### 6. 動作確認

1. デプロイ完了後、Vercelから提供されるURLにアクセス
2. 予測機能が正常に動作するか確認
3. ブラウザの開発者ツールでエラーがないか確認
4. Vercelログで `Successfully loaded libgomp.so.1` が出力されているか確認

## トラブルシューティング

### `ModuleNotFoundError: No module named 'numpy'`
- **原因**: Vercelが`requirements.txt`を認識していない
- **対策**: `vercel.json`の`functions`設定を確認

### `OSError: libgomp.so.1: cannot open shared object file`
- **原因**: `libgomp.so.1`が存在しないか、ARM64版が混入している
- **対策**: `api/lib/libgomp.so.1`がx86_64版であることを確認

### `A Serverless Function has exceeded the unzipped maximum size of 250 MB`
- **原因**: `scikit-learn`などの重いライブラリが含まれている
- **対策**: `requirements.txt`から`scikit-learn`を削除

### ビルドエラー
- `pnpm install` が失敗する場合: `package.json`の依存関係を確認
- TypeScriptエラー: `tsconfig.json`の設定を確認

## 注意事項

### データファイルの配置

MVP版では、以下のファイルをVercelに含める必要があります：

- `data/past_results.csv`: 過去データ
- `data/keisen_master.json`: 罫線マスターデータ
- `data/keisen_master_new.json`: 新罫線マスターデータ
- `data/models/*.pkl`: 学習済みモデル（サイズに注意）

### CORS設定

`next.config.ts` でグローバルCORSヘッダーを設定済み：

```typescript
async headers() {
  return [
    {
      source: '/api/:path*',
      headers: [
        { key: 'Access-Control-Allow-Origin', value: '*' },
        { key: 'Access-Control-Allow-Methods', value: 'GET,POST,OPTIONS' },
        { key: 'Access-Control-Allow-Headers', value: 'Content-Type' },
      ],
    },
  ];
}
```

## 関連ドキュメント

- [システムアーキテクチャ](./01_design/02-system-architecture.md): アーキテクチャ設計
- [CUBE生成ルール](./01_design/CUBE生成ルール.md): CUBE生成仕様
- [Vercelデプロイ計画](./02_todo/00_Vercel_Deployment.md): 現在のスプリント計画
