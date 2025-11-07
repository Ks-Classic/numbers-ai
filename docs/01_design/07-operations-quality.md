# 運用・品質管理書 v1.0

**Document Management Information**
- Document ID: DOC-07
- Version: 1.0
- Created: 2025-11-02
- Last Updated: 2025-11-02
- Status: Confirmed
- Approver: Technical Lead

---

## 📋 目次

1. [ドキュメント目的と適用範囲](#1-ドキュメント目的と適用範囲)
2. [CI/CD](#2-cicd)
3. [セキュリティ設計](#3-セキュリティ設計)
4. [品質基準](#4-品質基準)
5. [Definition of Done](#5-definition-of-done)
6. [本番デプロイ手順](#6-本番デプロイ手順)

---

## 1. ドキュメント目的と適用範囲

### 1.1 目的
本ドキュメントは、ナンバーズAI予測システムの**運用・品質管理**に関する方針を定義する。CI/CD、セキュリティ、品質基準を明確にすることで、安定したサービス運用を実現する。

### 1.2 対象読者
- DevOpsエンジニア
- QAエンジニア
- 開発リード
- 運用担当者

### 1.3 関連ドキュメント
- [02-system-architecture.md](./02-system-architecture.md): システム設計
- [06-implementation-plan.md](./06-implementation-plan.md): 実装計画

---

## 2. CI/CD

### 2.1 GitHub Actions設定

**MVP版ワークフロー:**

```yaml
# .github/workflows/ci.yml

name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: pnpm/action-setup@v2
      - name: Install dependencies
        run: pnpm install
      - name: Run ESLint
        run: pnpm lint
      - name: Run TypeScript check
        run: pnpm type-check

  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: pnpm/action-setup@v2
      - name: Install dependencies
        run: pnpm install
      - name: Run unit tests
        run: pnpm test

  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: pnpm/action-setup@v2
      - name: Install dependencies
        run: pnpm install
      - name: Build
        run: pnpm build
```

### 2.2 デプロイフロー

```
[開発者がコミット]
    │
    ▼
[GitHub Push]
    │
    ▼
[GitHub Actions CI実行]
    │ - Lint
    │ - Type Check
    │ - Unit Test
    │ - Build
    ▼
[CI成功 → Vercel自動デプロイ]
    │
    ▼
[プレビュー環境公開]（PR時）
    or
[本番環境デプロイ]（main push時）
```

---

## 3. セキュリティ設計

### 3.1 通信セキュリティ

- **HTTPS必須**: TLS 1.2以上
- **セキュアCookie**: HttpOnly, Secure, SameSite=Strict
- **CORS設定**: 許可されたオリジンのみ

### 3.2 データ保護

- **個人情報**: 収集しない（MVP版）
- **セッションデータ**: LocalStorage（機密情報なし）
- **APIキー**: 環境変数で管理、絶対にコミットしない

**環境変数管理:**

```bash
# .env.local.example

# API Keys
OPENAI_API_KEY=DUMMY_sk-xxx
DATABASE_URL=DUMMY_postgresql://xxx

# Supabase (Phase 2+)
NEXT_PUBLIC_SUPABASE_URL=DUMMY_https://xxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=DUMMY_xxx
```

### 3.3 脆弱性対策

- **XSS対策**: React自動エスケープ、DOMPurify使用
- **CSRF対策**: トークン使用（Phase 4）
- **SQLインジェクション**: Supabase SDKのプリペアドステートメント

---

## 4. 品質基準

### 4.1 コード品質基準

**禁止事項:**
- TODOコメントをcommit（issueで管理）
- 未確定ワード（「多分」「おそらく」等）の使用
- ハードコーディング（マジックナンバー、URL等）
- console.logの本番環境への混入

**推奨事項:**
- 能動態で記述（「〜される」ではなく「〜する」）
- 明確な命名（略語を避ける）
- 単一責任の原則（1関数1機能）
- DRY原則（Don't Repeat Yourself）

### 4.2 テスト品質基準

**テストカバレッジ目標:**
- ユニットテスト: 80%以上（Phase 2以降）
- 統合テスト: 主要機能100%
- E2Eテスト: クリティカルパス100%

**テスト実行タイミング:**
- ユニットテスト: commit前に実行
- 統合テスト: PR作成時に実行
- E2Eテスト: デプロイ前に実行

### 4.3 パフォーマンス基準

| 項目 | 目標値 | 測定条件 |
|------|--------|----------|
| 初期ローディング時間 | 3秒以内 | 初回アクセス時 |
| 画面遷移時間 | 500ms以内 | ページ間遷移 |
| AI予測応答時間 | 5秒以内 | 予測実行 |
| Lighthouse Score | 90+ | Performance |

---

## 5. Definition of Done

### 5.1 機能開発のDoD

以下の全条件を満たした時、機能は「完了」とみなす：

**コード品質:**
- [ ] ESLint、Prettierのチェック通過
- [ ] TypeScript型エラーなし
- [ ] コードレビュー完了（1人以上）
- [ ] 命名規則に従っている
- [ ] コメントが適切に記載されている

**テスト:**
- [ ] ユニットテスト実装（Phase 2以降）
- [ ] 統合テスト実装（主要機能）
- [ ] 手動テスト実施（全フロー）
- [ ] エッジケースの確認

**ドキュメント:**
- [ ] README更新（必要に応じて）
- [ ] API仕様書更新（API変更時）
- [ ] 変更履歴記録

**デプロイ:**
- [ ] CI/CD通過
- [ ] プレビュー環境で動作確認
- [ ] 本番環境デプロイ成功

### 5.2 リリースのDoD

以下の全条件を満たした時、リリースは「完了」とみなす：

**品質:**
- [ ] 全自動テスト通過
- [ ] パフォーマンス基準クリア
- [ ] セキュリティ脆弱性スキャン実施
- [ ] アクセシビリティチェック完了

**ドキュメント:**
- [ ] リリースノート作成
- [ ] ユーザー向けドキュメント更新
- [ ] バージョン番号更新

**運用:**
- [ ] バックアップ取得
- [ ] ロールバック手順確認
- [ ] モニタリング設定完了

---

## 6. 本番デプロイ手順

### 6.1 概要

本番環境へのデプロイは、以下の2つのコンポーネントで構成されます：

1. **Next.jsフロントエンド**: Vercelにデプロイ
2. **FastAPIバックエンド**: 別プラットフォーム（Railway/Cloud Run/Render）にデプロイ

### 6.2 FastAPIサーバーのデプロイ

FastAPIサーバーは先にデプロイし、URLを取得する必要があります。

#### オプションA: Railway（推奨・簡単）

1. Railwayアカウント作成: https://railway.app
2. 新しいプロジェクト作成
3. GitHubリポジトリを接続
4. `api`ディレクトリをルートとして設定
5. 環境変数設定（必要な場合）
6. デプロイ実行
7. デプロイURLを取得（例: `https://numbers-ai-api.railway.app`）

#### オプションB: Google Cloud Run

1. Google Cloudプロジェクト作成
2. Cloud Run API有効化
3. `api/Dockerfile`を使用してコンテナビルド
4. Cloud Runにデプロイ
5. URLを取得

#### オプションC: Render

1. Renderアカウント作成: https://render.com
2. 新しいWebサービス作成
3. GitHubリポジトリを接続
4. ビルドコマンド: `pip install -r requirements.txt`
5. 起動コマンド: `uvicorn main:app --host 0.0.0.0 --port $PORT`
6. デプロイ実行

### 6.3 CORS設定の更新

FastAPIサーバーのCORS設定を本番環境用に更新します。

**ファイル**: `api/main.py`

現在の設定（35行目）:
```python
allow_origins=["*"],  # 本番環境では適切に設定する
```

本番環境用に更新:
- 環境変数から許可オリジンを読み込む
- 開発環境（localhost）と本番環境（Vercel URL）を許可
- セキュリティを強化

**実装例:**
```python
import os

# 環境変数から許可オリジンを取得
allowed_origins = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:3000,http://localhost:8000"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 6.4 Next.jsアプリのVercelデプロイ

1. **Vercelアカウント作成・ログイン**
   - https://vercel.com/dashboard

2. **GitHubリポジトリを接続**
   - 「Add New...」→「Project」
   - GitHubリポジトリ `numbers-ai` を選択

3. **ビルド設定の確認**
   - `vercel.json`が既に存在（設定済み）
   - Framework: Next.js
   - Build Command: `pnpm build`
   - Region: `hnd1` (東京)

4. **環境変数の設定**
   - プロジェクト設定 → 「Environment Variables」
   - `FASTAPI_URL`: FastAPIサーバーのURL（フェーズ1で取得）
   - Environment: Production, Preview, Development すべてにチェック

5. **初回デプロイ**
   - 「Deploy」ボタンをクリック
   - デプロイ完了を待機（数分）
   - デプロイURLを取得（例: `https://numbers-ai.vercel.app`）

6. **FastAPIサーバーのCORS設定を更新**
   - フェーズ3で更新したCORS設定にVercel URLを追加
   - FastAPIサーバーを再デプロイ

7. **Vercelを再デプロイ**
   - 環境変数更新後、再デプロイを実行

### 6.5 動作確認

1. デプロイされたVercel URLにアクセス
2. 予測機能が正常に動作するか確認
3. ブラウザの開発者ツール（F12）でエラーを確認
4. NetworkタブでAPIリクエストが成功しているか確認

### 6.6 注意事項

#### データファイルとモデルファイル

- `data/past_results.csv`: Vercelに含まれる（Gitリポジトリに含まれている）
- `data/keisen_master.json`: Vercelに含まれる
- `data/models/*.pkl`: Vercelに含まれる（サイズが大きい場合は外部ストレージを検討）

#### セキュリティ

- CORS設定を適切に設定（`allow_origins=["*"]`は本番環境では非推奨）
- 環境変数はVercelダッシュボードで管理
- APIキーなどの機密情報は環境変数で管理

#### パフォーマンス

- Vercelの無料プランには制限あり
- モデルファイルが大きい場合（100MB以上）は外部ストレージを検討
- FastAPIサーバーのレスポンス時間を監視

### 6.7 トラブルシューティング

#### ビルドエラー
- `pnpm install`が失敗: `package.json`の依存関係を確認
- Node.jsバージョンを20に設定（Vercelダッシュボード）

#### API接続エラー
- FastAPIサーバーが起動しているか確認
- `FASTAPI_URL`が正しく設定されているか確認
- CORS設定を確認

#### 環境変数が読み込まれない
- 環境変数を追加/変更した場合は再デプロイが必要
- Vercelダッシュボード → Deployments → 「Redeploy」をクリック

---

## 変更履歴

| バージョン | 日付 | 変更者 | 変更内容 |
|-----------|------|--------|----------|
| 1.1 | 2025-01-XX | 技術リード | 本番デプロイ手順を追加（セクション6） |
| 1.0 | 2025-11-02 | 技術リード | 初版作成（元specifications.mdから分割） |

---

**承認**
- 技術リード: ________________ 日付: ________________

---

**関連ドキュメント**
- [01-business-requirements.md](./01-business-requirements.md): ビジネス要件
- [02-system-architecture.md](./02-system-architecture.md): システム設計
- [03-data-api-design.md](./03-data-api-design.md): データ・API設計
- [04-algorithm-ai.md](./04-algorithm-ai.md): アルゴリズム・AI
- [05-frontend-design.md](./05-frontend-design.md): フロントエンド設計
- [06-implementation-plan.md](./06-implementation-plan.md): 実装計画

---

**ドキュメント終了**

