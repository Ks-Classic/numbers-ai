# システムアーキテクチャ設計書 v1.0

**Document Management Information**
- Document ID: DOC-02
- Version: 1.0
- Created: 2025-11-02
- Last Updated: 2025-11-02
- Status: Confirmed
- Approver: Technical Lead

---

## 📋 目次

1. [ドキュメント目的と適用範囲](#1-ドキュメント目的と適用範囲)
2. [システムアーキテクチャ](#2-システムアーキテクチャ)
3. [技術スタック](#3-技術スタック)
4. [ディレクトリ構成](#4-ディレクトリ構成)

---

## 1. ドキュメント目的と適用範囲

### 1.1 目的
本ドキュメントは、ナンバーズAI予測システムの**システムアーキテクチャ**と**技術選定**を定義する。開発者が本書に従うことで、拡張性・保守性の高いシステム設計を実現する。

### 1.2 対象読者
- システムアーキテクト
- フルスタックエンジニア
- DevOpsエンジニア
- 技術リード

### 1.3 関連ドキュメント
- [01-business-requirements.md](./01-business-requirements.md): ビジネス要件
- [03-data-api-design.md](./03-data-api-design.md): データ・API設計
- [06-implementation-plan.md](./06-implementation-plan.md): 実装計画（技術導入タイミング）

---

## 2. システムアーキテクチャ

### 2.1 全体構成（MVP版）

```
┌─────────────────────────────────────────────────┐
│                   ユーザー                        │
│              (スマートフォン/PC)                  │
└─────────────────┬───────────────────────────────┘
                  │ HTTPS
                  ▼
┌─────────────────────────────────────────────────┐
│           Vercel (Hosting + CDN)                │
│  ┌─────────────────────────────────────────┐   │
│  │       Next.js 14 Application            │   │
│  │  ┌─────────────┐  ┌─────────────────┐  │   │
│  │  │  Frontend   │  │  API Routes     │  │   │
│  │  │  (React)    │  │  (/api/*)       │  │   │
│  │  └─────────────┘  └─────────────────┘  │   │
│  │                          │              │   │
│  │                          ▼              │   │
│  │                   ┌─────────────────┐  │   │
│  │                   │ Chart Generator │  │   │
│  │                   │ (TypeScript)    │  │   │
│  │                   └─────────────────┘  │   │
│  │                          │              │   │
│  │                          ▼              │   │
│  │                   ┌─────────────────┐  │   │
│  │                   │  AI Predictor   │  │   │
│  │                   │  (Python/TS)    │  │   │
│  │                   └─────────────────┘  │   │
│  └─────────────────────────────────────────┘   │
└─────────────────┬───────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────┐
│          Data Layer (MVP: CSV Files)            │
│  - past_results.csv                             │
│  - keisen_master.json                           │
│  - trained_models.pkl                           │
└─────────────────────────────────────────────────┘
```

**MVP版の特徴:**
- モノリシックアーキテクチャ（Next.js単体）
- CSVベースのデータ管理（シンプルかつ高速）
- Vercelのサーバーレス関数で完結
- セットアップコストを最小化

### 2.2 全体構成（Phase 4: 完全版）

```
┌─────────────────────────────────────────────────┐
│                   ユーザー                        │
└─────────────────┬───────────────────────────────┘
                  │ HTTPS
                  ▼
┌─────────────────────────────────────────────────┐
│           Vercel (Frontend Hosting)             │
│              Next.js 14 (SSG/SSR)               │
└─────────────────┬───────────────────────────────┘
                  │ REST API
                  ▼
┌─────────────────────────────────────────────────┐
│       GCP Cloud Run (AI Engine API)             │
│              FastAPI (Python)                   │
│  ┌─────────────────────────────────────────┐   │
│  │  Chart Generator │ Feature Extractor   │   │
│  │  AI Predictor    │ Model Manager       │   │
│  └─────────────────────────────────────────┘   │
└─────────────────┬───────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────┐
│        Supabase (Database + Storage)            │
│  - PostgreSQL (過去データ、予測表)               │
│  - Storage (学習済みモデル)                      │
└─────────────────────────────────────────────────┘
```

**Phase 4の特徴:**
- マイクロサービスアーキテクチャ
- フロントエンドとAIエンジンを物理的に分離
- それぞれを独立してスケール・更新可能
- リソース制限からの解放

**なぜPhase 4でマイクロサービス化するのか:**
詳細は [06-implementation-plan.md](./06-implementation-plan.md) の「Phase 4実装計画」を参照

### 2.3 データフロー

**予測実行時のデータフロー:**

```
[ユーザー入力]
  │ 回号: 6701
  │ N4リハーサル: 3782
  │ N3リハーサル: 149
  ▼
[Frontend: 入力バリデーション]
  ▼
[API Route: /api/predict]
  │
  ├─→ [Chart Generator]
  │     │ - 過去データ取得
  │     │ - 罫線マスター参照
  │     │ - 予測表A/B生成
  │     ▼
  │   [生成された予測表]
  │
  ├─→ [Feature Extractor]
  │     │ - 形状特徴計算
  │     │ - 位置特徴計算
  │     │ - 関係性特徴計算
  │     ▼
  │   [特徴量ベクトル]
  │
  └─→ [AI Predictor]
        │ - 軸数字予測モデル実行
        │ - 組み合わせ予測モデル実行
        │ - スコア算出・ランキング
        ▼
      [予測結果JSON]
        ▼
[Frontend: 結果表示]
```

### 2.4 コンポーネント責務

**Frontend (Next.js/React)**
- ユーザーインターフェース提供
- 入力バリデーション
- 状態管理（Redux Toolkit）
- APIコール
- 結果のビジュアライゼーション

**API Routes (Next.js)**
- リクエストハンドリング
- 認証・認可（Phase 4）
- ビジネスロジック呼び出し
- レスポンス生成

**Chart Generator (TypeScript)**
- 予測表生成ロジック
- アルゴリズム実装（docs/元ネタ/表作成ルール.,md準拠）
- パターンA/B処理

**Feature Extractor (TypeScript/Python)**
- 特徴量計算
- 数値変換
- 正規化処理

**AI Predictor (Python/TypeScript)**
- 学習済みモデル読み込み
- 推論実行
- スコアリング

---

## 3. 技術スタック

### 3.1 フロントエンド

**コア技術**
- **Next.js**: 14.2.0+
  - App Router使用
  - Server Components活用
  - ISR/SSG/SSRの使い分け
- **React**: 18.3.0+
- **TypeScript**: 5.3.0+

**状態管理**
- **Redux Toolkit**: 2.0.0+
- **React Query (TanStack Query)**: 5.0.0+

**スタイリング**
- **Tailwind CSS**: 3.4.0+
- **shadcn/ui**: コンポーネントライブラリ
- **Framer Motion**: アニメーション

**ユーティリティ**
- **Zod**: スキーマバリデーション
- **React Hook Form**: フォーム管理
- **date-fns**: 日付操作

### 3.2 バックエンド

**MVP版（Next.js API Routes）**
- **Next.js API Routes**: サーバーレス関数
- **TypeScript**: ビジネスロジック実装

**Phase 4（FastAPI）**
- **FastAPI**: 0.104.0+
- **Python**: 3.10+
- **Pydantic**: データバリデーション
- **Uvicorn**: ASGIサーバー

**なぜMVPではNext.js API Routesを使うのか:**
詳細は [06-implementation-plan.md](./06-implementation-plan.md) の「MVP実装計画」を参照

### 3.3 AI/ML

**機械学習**
- **XGBoost**: 2.0.0+（メインアルゴリズム）
- **scikit-learn**: 1.3.0+（前処理、評価）
- **Pandas**: 2.1.0+（データ操作）
- **NumPy**: 1.26.0+（数値計算）

**実験管理**
- **Jupyter Notebook**: 開発・実験
- **Weights & Biases (wandb)**: Phase 3以降

**なぜMVPではW&Bを使わないのか:**
詳細は [06-implementation-plan.md](./06-implementation-plan.md) の「Phase 3実装計画」を参照

### 3.4 データストア

**MVP版**
- **CSV**: ローカルファイルストレージ
- **JSON**: 罫線マスターデータ

**Phase 2以降**
- **Supabase PostgreSQL**: 15.0+
  - 過去実績データ
  - 予測表データ
  - ユーザーデータ
- **Supabase Storage**: 学習済みモデル

**なぜMVPではSupabaseを使わないのか:**
詳細は [06-implementation-plan.md](./06-implementation-plan.md) の「Phase 2実装計画」を参照

### 3.5 インフラ・デプロイ

**MVP版**
- **Vercel**: ホスティング + CI/CD
- **GitHub**: ソースコード管理

**Phase 4**
- **Vercel**: フロントエンド
- **GCP Cloud Run**: AI Engine API
- **GCP Cloud Storage**: モデルストレージ
- **Supabase**: データベース

**なぜPhase 4でGCP Cloud Runを使うのか:**
詳細は [06-implementation-plan.md](./06-implementation-plan.md) の「Phase 4実装計画」を参照

### 3.6 開発ツール

**コード品質**
- **ESLint**: 8.55.0+
- **Prettier**: 3.1.0+
- **TypeScript ESLint**: 6.15.0+

**テスト**
- **Vitest**: 1.0.0+（ユニット）
- **Playwright**: 1.40.0+（E2E）
- **Testing Library**: React/Node

**ビルド・パッケージ管理**
- **pnpm**: 8.12.0+
- **Turbo**: Monorepo管理（Phase 4）

---

## 4. ディレクトリ構成

### 4.1 MVP版構成

```
numbers-ai/
├── docs/                          # ドキュメント
│   ├── 01-business-requirements.md
│   ├── 02-system-architecture.md（本書）
│   ├── 03-data-api-design.md
│   ├── 04-algorithm-ai.md
│   ├── 05-frontend-design.md
│   ├── 06-implementation-plan.md
│   ├── 07-operations-quality.md
│   ├── INDEX.md
│   └── 元ネタ/
│
├── src/
│   ├── app/                       # Next.js App Router
│   │   ├── layout.tsx             # ルートレイアウト
│   │   ├── page.tsx               # ホーム画面
│   │   ├── predict/
│   │   │   ├── page.tsx           # 予測開始画面
│   │   │   ├── input/
│   │   │   │   └── page.tsx       # 回号入力
│   │   │   ├── rehearsal/
│   │   │   │   └── page.tsx       # リハーサル入力
│   │   │   └── result/
│   │   │       └── page.tsx       # 結果表示
│   │   │
│   │   └── api/                   # API Routes
│   │       └── predict/
│   │           └── route.ts       # 予測実行API
│   │
│   ├── components/                # Reactコンポーネント
│   │   ├── ui/                    # 共通UIコンポーネント
│   │   │   ├── button.tsx
│   │   │   ├── input.tsx
│   │   │   ├── tabs.tsx
│   │   │   ├── accordion.tsx
│   │   │   ├── modal.tsx
│   │   │   └── progress-bar.tsx
│   │   │
│   │   ├── features/              # 機能別コンポーネント
│   │   │   ├── RoundInput.tsx
│   │   │   ├── RehearsalInput.tsx
│   │   │   ├── ResultView.tsx
│   │   │   ├── AxisCandidates.tsx
│   │   │   └── ManualAxis.tsx
│   │   │
│   │   └── layouts/               # レイアウトコンポーネント
│   │       ├── Header.tsx
│   │       └── Navigation.tsx
│   │
│   ├── lib/                       # ビジネスロジック
│   │   ├── chart-generator/       # 予測表生成
│   │   │   ├── index.ts
│   │   │   ├── pattern-a.ts       # パターンA
│   │   │   ├── pattern-b.ts       # パターンB（Phase 4）
│   │   │   └── types.ts
│   │   │
│   │   ├── feature-extraction/    # 特徴量計算
│   │   │   ├── index.ts
│   │   │   ├── shape-features.ts
│   │   │   ├── position-features.ts
│   │   │   ├── relation-features.ts
│   │   │   └── aggregate-features.ts
│   │   │
│   │   ├── ai-predictor/          # AI予測
│   │   │   ├── index.ts
│   │   │   ├── axis-predictor.ts
│   │   │   ├── combination-predictor.ts
│   │   │   └── model-loader.ts
│   │   │
│   │   ├── data-loader/           # データ読み込み
│   │   │   ├── index.ts
│   │   │   ├── past-results.ts
│   │   │   └── keisen-master.ts
│   │   │
│   │   └── utils/                 # ユーティリティ
│   │       ├── validators.ts
│   │       ├── formatters.ts
│   │       └── constants.ts
│   │
│   ├── store/                     # Redux状態管理
│   │   ├── index.ts
│   │   ├── slices/
│   │   │   ├── prediction-slice.ts
│   │   │   └── ui-slice.ts
│   │   └── hooks.ts
│   │
│   ├── types/                     # TypeScript型定義
│   │   ├── prediction.ts
│   │   ├── chart.ts
│   │   └── api.ts
│   │
│   └── styles/                    # グローバルスタイル
│       └── globals.css
│
├── data/                          # データファイル（MVP）
│   ├── past_results.csv           # 過去実績
│   ├── keisen_master.json         # 罫線マスター
│   └── models/                    # 学習済みモデル
│       ├── n3_box_axis.pkl
│       ├── n3_box_comb.pkl
│       ├── n3_straight_axis.pkl
│       ├── n3_straight_comb.pkl
│       ├── n4_box_axis.pkl
│       ├── n4_box_comb.pkl
│       ├── n4_straight_axis.pkl
│       └── n4_straight_comb.pkl
│
├── notebooks/                     # Jupyter Notebooks
│   ├── 01_data_preparation.ipynb
│   ├── 02_chart_generation.ipynb
│   ├── 03_feature_engineering.ipynb
│   ├── 04_model_training.ipynb
│   └── 05_evaluation.ipynb
│
├── tests/                         # テストコード
│   ├── unit/
│   ├── integration/
│   └── e2e/
│
├── public/                        # 静的ファイル
│   ├── images/
│   └── favicon.ico
│
├── .github/                       # GitHub設定
│   └── workflows/
│       └── ci.yml
│
├── package.json
├── pnpm-lock.yaml
├── tsconfig.json
├── next.config.js
├── tailwind.config.ts
├── .eslintrc.json
├── .prettierrc
├── .env.local.example
└── README.md
```

### 4.2 ディレクトリ設計原則

**レイヤー分離**
- `app/`: ルーティング層（Next.js App Router）
- `components/`: プレゼンテーション層（UIコンポーネント）
- `lib/`: ビジネスロジック層（ドメインロジック）
- `store/`: 状態管理層（グローバル状態）

**責務の明確化**
- `components/ui/`: 汎用的なUIコンポーネント（再利用可能）
- `components/features/`: 機能特化コンポーネント（ビジネスロジック含む）
- `lib/*/`: モジュール単位でディレクトリ分割

**命名規則**
- コンポーネント: PascalCase（例: `RoundInput.tsx`）
- ユーティリティ: kebab-case（例: `data-loader.ts`）
- 型定義: kebab-case（例: `prediction.ts`）

---

## 変更履歴

| バージョン | 日付 | 変更者 | 変更内容 |
|-----------|------|--------|----------|
| 1.0 | 2025-11-02 | 技術リード | 初版作成（元specifications.mdから分割） |

---

**承認**
- 技術リード: ________________ 日付: ________________

---

**関連ドキュメント**
- [01-business-requirements.md](./01-business-requirements.md): ビジネス要件
- [03-data-api-design.md](./03-data-api-design.md): データ・API設計
- [04-algorithm-ai.md](./04-algorithm-ai.md): アルゴリズム・AI
- [05-frontend-design.md](./05-frontend-design.md): フロントエンド設計
- [06-implementation-plan.md](./06-implementation-plan.md): 実装計画
- [07-operations-quality.md](./07-operations-quality.md): 運用・品質

---

**ドキュメント終了**

