# Sentry エラー監視セットアップガイド

## 概要

Numbers AI では Sentry を使用してアプリケーション全体のエラーを監視しています。

## セットアップ手順

### 1. Sentry プロジェクト作成

1. [Sentry](https://sentry.io/) にログイン
2. 新規プロジェクト作成 → **Next.js** を選択
3. プロジェクト名: `numbers-ai`

### 2. 環境変数設定

`.env.local` に以下を追加:

```env
# Sentry DSN (プロジェクトの Settings > Client Keys から取得)
NEXT_PUBLIC_SENTRY_DSN=https://xxxxx@xxxxx.ingest.sentry.io/xxxxx

# Sentry 組織・プロジェクト名 (ソースマップアップロード用)
SENTRY_ORG=your-org-name
SENTRY_PROJECT=numbers-ai

# Sentry Auth Token (Settings > Auth Tokens で "project:releases" スコープ付きで生成)
SENTRY_AUTH_TOKEN=sntrys_xxxxx
```

### 3. Vercel 環境変数設定

Vercel ダッシュボード → Settings → Environment Variables:

| 変数名 | 値 | 環境 |
|--------|-----|------|
| `NEXT_PUBLIC_SENTRY_DSN` | Sentry DSN | Production, Preview |
| `SENTRY_ORG` | 組織名 | Production, Preview |
| `SENTRY_PROJECT` | プロジェクト名 | Production, Preview |
| `SENTRY_AUTH_TOKEN` | Auth Token | Production, Preview |

### 4. Discord 通知設定 (Sentry側)

1. Sentry → Settings → Integrations → Discord
2. Discord サーバーを接続
3. プロジェクトの Alert Rules を設定:
   - **条件**: 新しいエラー発生時
   - **アクション**: Discord に通知

### 5. メール通知設定 (Sentry側)

1. Sentry → Settings → Notifications
2. Issue Alerts のメール通知を有効化
3. チームメンバーのメールアドレスを追加

## 監視対象

| 対象 | 説明 |
|------|------|
| **クライアントエラー** | ブラウザでのJSエラー、Reactエラー |
| **サーバーエラー** | API Routes、Server Components |
| **Edge Functions** | Middleware、Edge API Routes |
| **パフォーマンス** | 遅いAPI、遅いページロード |
| **セッションリプレイ** | エラー発生時のユーザー操作を記録 |

## カスタムエラー送信

```typescript
import * as Sentry from "@sentry/nextjs";

// エラーをSentryに送信
Sentry.captureException(error);

// メッセージを送信
Sentry.captureMessage("Something went wrong", "warning");

// コンテキスト付きでエラーを送信
Sentry.withScope((scope) => {
  scope.setTag("feature", "prediction");
  scope.setContext("data", { roundNumber: 6880 });
  Sentry.captureException(error);
});
```

## ファイル構成

```
numbers-ai/
├── sentry.client.config.ts   # クライアント設定
├── sentry.server.config.ts   # サーバー設定
├── sentry.edge.config.ts     # Edge設定
├── next.config.ts            # Sentry統合
└── src/app/
    ├── global-error.tsx      # グローバルエラーハンドラー
    └── error.tsx             # ページエラーハンドラー
```

## アラートルール推奨設定

### 重大エラー (即時通知)
- **条件**: エラーレベル = Error または Fatal
- **頻度**: 毎回
- **通知先**: Discord + メール

### 警告 (まとめて通知)
- **条件**: エラーレベル = Warning
- **頻度**: 1時間ごとにまとめて
- **通知先**: メールのみ

### パフォーマンス問題
- **条件**: API応答時間 > 3秒
- **頻度**: 10分間に3回以上
- **通知先**: Discord
