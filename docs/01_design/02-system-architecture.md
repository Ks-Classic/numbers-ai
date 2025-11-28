# システムアーキテクチャ設計書 v2.0

**Document Management Information**
- Document ID: DOC-02
- Version: 1.2
- Created: 2025-11-02
- Last Updated: 2025-01-XX
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
- 状態管理（Zustand）
- APIコール
- 結果のビジュアライゼーション

**API Routes (Next.js)**
- リクエストハンドリング
- 認証・認可（Phase 4）
- ビジネスロジック呼び出し
- レスポンス生成

**Chart Generator (TypeScript)**
- 予測表生成ロジック
- CUBE生成ロジック（通常CUBE・極CUBE）
- アルゴリズム実装（docs/元ネタ/表作成ルール.,md準拠）
- パターンA/B処理
- **実装場所**: `src/lib/cube-generator/`
- **用途**: 本番Webアプリ（`/cube`ページ、`/predict`ページ）

**Chart Generator (Python)**
- 予測表生成ロジック（開発・分析用途）
- CUBE生成ロジック（開発・分析用途）
- **実装場所**: `core/chart_generator.py`
- **用途**: 可視化ツール、バッチ処理、データ分析、ノートブック

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
- **Zustand**: 4.4.0+（軽量でシンプルな状態管理）
- **React Query (TanStack Query)**: 5.0.0+（Phase 2以降）

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

**Phase 4（FastAPI）**（実装済み、デプロイ準備中）
- **FastAPI**: 0.104.0+
- **Python**: 3.10+
- **Pydantic**: データバリデーション
- **Uvicorn**: ASGIサーバー

**実装状況:**
- FastAPI AI推論エンジンは実装済み（`api/`ディレクトリ）
- Dockerコンテナ化とGCP Cloud Runデプロイは準備中
- **注意**: FastAPIサーバーのCUBE生成エンドポイント（`/api/cube/{round_number}`）は**非推奨**。TypeScript版（`src/app/api/cube/[roundNumber]/route.ts`）に移行済み。

**なぜMVPではNext.js API Routesを使うのか:**
詳細は [06-implementation-plan.md](./06-implementation-plan.md) の「MVP実装計画」を参照

### 3.2.1 予測APIルーティング（現状の決定事項）

**現状（Production / Vercel）**
- **エントリポイント**: `POST /api/predict` (Next.js API Route)
- **内部処理**: `src/lib/predictor/vercel-python.ts` を経由して、Vercel Python Serverless Functions を呼び出す。
- **Python関数**:
  - `/api/py/axis` (`api/py/axis.py`): 軸数字予測
  - `/api/py/combination` (`api/py/combination.py`): 組み合わせ予測
- **特徴**: FastAPIは使用せず、標準の `http.server.BaseHTTPRequestHandler` を使用して軽量化を実現。

**開発用・レガシー資産（非推奨）**
- `api/main.py` (FastAPI): 開発初期のサーバー実装。現在は本番環境では使用されていない。
- `src/lib/predictor/fastapi-bridge.ts`: FastAPIサーバーと通信するためのクライアント。現在は `vercel-python.ts` に移行済み。

### 3.2.2 予測エンドポイントの実装構成

```
[フロントエンド predictor.ts]
         │
         ▼
   POST /api/predict       (Next.js API Route)
         │                 ・バリデーション
         │                 ・GitHubデータ取得
         │
         ▼
[vercel-python.ts]         (Internal Client)
         │                 ・/api/py/axis 呼び出し
         │                 ・/api/py/combination 呼び出し
         │
         ▼
[Vercel Python Functions]  (api/py/*.py)
         │                 ・LightGBMモデル読み込み
         │                 ・推論実行
         ▼
    [LightGBM Native Model]
```

### 3.2.3 FastAPI vs Vercel Python Functions

初期設計ではFastAPIサーバーを検討しましたが、Vercelへのデプロイ容易性とコールドスタート対策のため、**Vercel Python Serverless Functions** を採用しました。

| 項目 | FastAPI (Legacy) | Vercel Python Functions (Current) |
|------|------------------|-----------------------------------|
| 実装ファイル | `api/main.py` | `api/py/axis.py`, `api/py/combination.py` |
| フレームワーク | FastAPI | 標準 `http.server` |
| クライアント | `fastapi-bridge.ts` | `vercel-python.ts` |
| デプロイ | 別途サーバーが必要 | Vercelに同梱可能 |
| 現状 | **非推奨 (参考用)** | **稼働中** |

### 3.2.4 今後のロードマップ

1.  **レガシーコードの削除**: 混乱を避けるため、`api/main.py` および `fastapi-bridge.ts` を削除または `legacy/` ディレクトリへ移動する。
2.  **ONNX移行**: Python依存を完全に排除するため、将来的にONNX Runtime (Node.js) への移行を検討（v2.0構想）。

### 3.3 AI/ML

**機械学習**
- **LightGBM**: 4.5.0+（メインアルゴリズム）
  - 高速・軽量な勾配ブースティング
  - Vercel Python Serverless Functionsで実行
- **scikit-learn**: 1.3.0+（前処理、評価）
- **Pandas**: 2.1.0+（データ操作）
- **NumPy**: 1.26.0+（数値計算）

**デプロイ方式（MVP版）**
- **Vercel Python Serverless Functions**でLightGBMモデルを直接実行
- `api/predict/axis.py`、`api/predict/combination.py`で予測API提供
- モデルファイル（`data/models/*.pkl`）をVercelにデプロイ

**libgomp問題と解決策**
- LightGBMはOpenMP（libgomp.so.1）に依存
- Vercel環境では標準で利用不可
- 解決策：LightGBM 4.5.0（OpenMP依存軽減版）を使用
- フォールバック：scikit-learn GradientBoostingClassifierで代替

**検討済み・不採用の選択肢**
- ONNX + onnxruntime-node：Next.jsビルド時にメモリ不足
- ONNX + onnxruntime-web：同様のビルド問題
- FastAPI別サービス：Vercel単体完結の要件に反する

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
│   │   ├── globals.css            # グローバルスタイル
│   │   ├── favicon.ico            # ファビコン
│   │   │
│   │   ├── predict/               # 予測フロー
│   │   │   ├── page.tsx           # 回号入力画面（実装済み）
│   │   │   ├── rehearsal/
│   │   │   │   └── page.tsx       # リハーサル入力（実装済み）
│   │   │   ├── loading/
│   │   │   │   └── page.tsx       # ローディング画面（実装済み）
│   │   │   ├── axis/
│   │   │   │   └── page.tsx       # 軸数字選択画面（実装済み）
│   │   │   └── result/
│   │   │       └── page.tsx       # 結果表示（実装済み）
│   │   │
│   │   ├── history/               # 履歴画面（実装済み・非表示）
│   │   │   └── page.tsx
│   │   │
│   │   ├── statistics/            # 統計画面（実装済み・非表示）
│   │   │   └── page.tsx
│   │   │
│   │   ├── settings/              # 設定画面（実装済み・非表示）
│   │   │   └── page.tsx
│   │   │
│   │   └── api/                   # API Routes
│   │       └── predict/
│   │           └── route.ts       # 予測実行API（実装済み）
│   │
│   ├── components/                # Reactコンポーネント
│   │   ├── ui/                    # 共通UIコンポーネント（shadcn/ui）
│   │   │   ├── button.tsx         # 実装済み
│   │   │   ├── input.tsx          # 実装済み
│   │   │   ├── tabs.tsx           # 実装済み
│   │   │   ├── dialog.tsx         # 実装済み
│   │   │   ├── card.tsx           # 実装済み
│   │   │   ├── badge.tsx          # 実装済み
│   │   │   ├── label.tsx          # 実装済み
│   │   │   ├── progress.tsx       # 実装済み
│   │   │   ├── select.tsx         # 実装済み
│   │   │   ├── switch.tsx         # 実装済み
│   │   │   ├── radio-group.tsx    # 実装済み
│   │   │   ├── sonner.tsx         # 実装済み
│   │   │   ├── accordion.tsx      # Phase 2実装予定
│   │   │   └── modal.tsx          # Phase 2実装予定
│   │   │
│   │   ├── features/              # 機能別コンポーネント
│   │   │   ├── RoundInput.tsx     # Phase 2実装予定
│   │   │   ├── RehearsalInput.tsx # Phase 2実装予定
│   │   │   ├── ResultView.tsx     # Phase 2実装予定
│   │   │   ├── AxisCandidates.tsx # Phase 2実装予定
│   │   │   └── ManualAxis.tsx     # Phase 2実装予定
│   │   │
│   │   ├── layouts/               # レイアウトコンポーネント
│   │   │   ├── Header.tsx         # Phase 2実装予定
│   │   │   └── Navigation.tsx     # Phase 2実装予定（shared/から移動予定）
│   │   │
│   │   └── shared/                # 共有コンポーネント
│   │       └── Navigation.tsx     # ナビゲーション（実装済み）
│   │
│   ├── lib/                       # ビジネスロジック
│   │   ├── store.ts               # Zustand状態管理（実装済み）
│   │   ├── utils.ts               # ユーティリティ関数（実装済み）
│   │   ├── sample-data.ts         # サンプルデータ（実装済み）
│   │   │
│   │   ├── cube-generator/           # CUBE生成（実装済み）
│   │   │   ├── index.ts              # エクスポート
│   │   │   ├── chart-generator.ts    # 通常CUBE生成
│   │   │   ├── extreme-cube.ts      # 極CUBE生成
│   │   │   ├── keisen-master-loader.ts # 罫線マスターデータ読み込み
│   │   │   └── types.ts              # 型定義
│   │   │
│   │   ├── feature-extraction/    # 特徴量計算（Phase 2実装予定）
│   │   │   ├── index.ts
│   │   │   ├── shape-features.ts   # 形状特徴
│   │   │   ├── position-features.ts # 位置特徴
│   │   │   ├── relation-features.ts # 関係性特徴
│   │   │   └── aggregate-features.ts # 集約特徴
│   │   │
│   │   ├── ai-predictor/          # AI予測（Phase 2実装予定）
│   │   │   ├── index.ts
│   │   │   ├── axis-predictor.ts  # 軸数字予測
│   │   │   ├── combination-predictor.ts # 組み合わせ予測
│   │   │   └── model-loader.ts    # モデル読み込み
│   │   │
│   │   ├── data-loader/           # データ読み込み（Phase 2実装予定）
│   │   │   ├── index.ts
│   │   │   ├── past-results.ts    # 過去実績データ（CSV→Supabase）
│   │   │   └── keisen-master.ts    # 罫線マスターデータ
│   │   │
│   │   └── utils/                 # ユーティリティ（Phase 2実装予定）
│   │       ├── validators.ts      # バリデーション
│   │       ├── formatters.ts      # フォーマット
│   │       └── constants.ts      # 定数
│   │
│   └── types/                     # TypeScript型定義
│       ├── prediction.ts          # 予測関連の型（実装済み）
│       ├── statistics.ts           # 統計関連の型（実装済み）
│       ├── chart.ts                # チャート関連の型（Phase 2実装予定）
│       └── api.ts                  # API関連の型（Phase 2実装予定）
│
├── data/                          # データファイル（MVP）
│   ├── past_results.csv           # 過去実績（MVP: CSV、Phase 2: Supabaseへ移行）
│   ├── keisen_master.json         # 罫線マスター
│   └── models/                     # 学習済みモデル（MVP: ローカル、Phase 4: GCP Storageへ移行）
│       ├── n3_box_axis.pkl
│       ├── n3_box_comb.pkl
│       ├── n3_straight_axis.pkl
│       ├── n3_straight_comb.pkl
│       ├── n4_box_axis.pkl
│       ├── n4_box_comb.pkl
│       ├── n4_straight_axis.pkl
│       └── n4_straight_comb.pkl
│
├── api/                           # FastAPIバックエンド（実装済み、デプロイ準備中）
│   ├── main.py                    # FastAPIアプリケーション（実装済み）
│   ├── requirements.txt           # Python依存関係（実装済み）
│   ├── Dockerfile                 # Dockerイメージ（実装済み）
│   ├── routers/
│   │   └── predict.py             # 予測APIルーター（実装済み）
│   ├── services/
│   │   ├── chart_generator.py     # 予測表生成サービス（実装済み）
│   │   ├── feature_extractor.py   # 特徴量抽出サービス（実装済み）
│   │   └── ai_predictor.py        # AI予測サービス（実装済み）
│   └── models/
│       └── schemas.py             # Pydanticスキーマ（実装済み）
│
├── notebooks/                     # Jupyter Notebooks
│   ├── 01_data_preparation.ipynb  # Phase 2実装予定
│   ├── 02_chart_generation.ipynb  # Phase 2実装予定
│   ├── 03_feature_engineering.ipynb # Phase 3実装予定
│   ├── 04_model_training.ipynb    # Phase 3実装予定（W&B統合）
│   └── 05_evaluation.ipynb        # Phase 3実装予定
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
- `lib/`: ビジネスロジック層（ドメインロジック、状態管理）
- `types/`: 型定義層（TypeScript型）

**責務の明確化**
- `components/ui/`: 汎用的なUIコンポーネント（shadcn/ui、再利用可能）
- `components/shared/`: アプリ全体で共有されるコンポーネント
- `components/features/`: 機能特化コンポーネント（将来拡張用）
- `components/layouts/`: レイアウトコンポーネント（将来拡張用）
- `lib/store.ts`: Zustandによる状態管理（軽量でシンプル）

**MVP版の簡素化**
- ビジネスロジックは `lib/` に直接配置（Phase 2以降でディレクトリ分割予定）
- 状態管理はZustandを使用（Redux Toolkitより軽量）
- グローバルスタイルは `app/globals.css` に配置（Next.js App Routerの標準）

**将来実装予定の明確化**
- **Phase 1**: `lib/cube-generator/` を実装（完了）
- **Phase 2**: `lib/feature-extraction/`, `lib/ai-predictor/`, `lib/data-loader/` を実装
- **Phase 2**: `components/features/` に機能別コンポーネントを実装
- **Phase 2**: `components/layouts/` にレイアウトコンポーネントを実装（`shared/Navigation.tsx` を移動予定）
- **Phase 2**: Supabase統合により `lib/data-loader/` でCSV→Supabase移行
- **Phase 2**: `data/past_results.csv` → Supabase PostgreSQLへ移行
- **Phase 3**: W&B統合（実験管理機能、`notebooks/` にW&B統合）
- **Phase 3**: 特徴量エンジニアリングとハイパーパラメータチューニング
- **Phase 4**: パターンB実装（`lib/chart-generator/pattern-b.ts`）
- **Phase 4**: FastAPIバックエンド実装（`api/` ディレクトリ、実装済み、GCP Cloud Runデプロイ準備中）
- **Phase 4**: `data/models/` → GCP Cloud Storageへ移行

**命名規則**
- コンポーネント: PascalCase（例: `RoundInput.tsx`）
- ユーティリティ: kebab-case（例: `data-loader.ts`）
- 型定義: kebab-case（例: `prediction.ts`）

---

## 変更履歴

| バージョン | 日付 | 変更者 | 変更内容 |
|-----------|------|--------|----------|
| 1.0 | 2025-11-02 | 技術リード | 初版作成（元specifications.mdから分割） |
| 1.1 | 2025-01-XX | 技術リード | 現実装に合わせてディレクトリ構成を更新（Zustand採用、ルーティング構造反映） |
| 1.2 | 2025-01-XX | 技術リード | FastAPI実装状況を反映（実装済み、デプロイ準備中）、学習データ範囲を4801回分に更新 |
| 1.3 | 2025-11-24 | 技術リード | Vercel Python Serverless Functions採用、ARM64環境からのデプロイ戦略を追記 |

### 1.3の主な変更点

**Vercel Python Serverless Functions採用:**
- FastAPIサーバーの代わりに、Vercel Python Serverless Functionsを採用
- `api/predict/axis.py`, `api/predict/combination.py` を実装
- Next.js API Routes (`src/app/api/predict/route.ts`) がプロキシとして機能

**ARM64環境からのデプロイ対応:**
- ローカル環境: Windows ARM64 + WSL (Ubuntu ARM64)
- Vercel環境: Linux x86_64
- 対策: 「クリーンクラウドビルド + libgomp手動注入」戦略
  - `requirements.txt` のみをVercelに送信（venvは除外）
  - Vercel側でx86_64環境で `pip install` を実行
  - `libgomp.so.1` (164KB) のみx86_64版を手動配置
  - `scikit-learn` (100MB) を避けてサイズ制限（250MB）をクリア

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


---

### 3.6 ONNXベース推論アーキテクチャ（v2.0 - Future Plan）

**⚠️ 現状ステータス**: 設計段階 / 実験中
現在（2025-11-28時点）は `src/lib/predictor/fastapi-bridge.ts` を使用した **FastAPI/Python連携** が稼働しています。以下のONNX構成は、将来的な「Vercel単体完結」を目指すための設計案であり、まだ本番コードには統合されていません。

### 3.6.1 アーキテクチャ概要（計画）

**v2.0で採用予定のアーキテクチャ:**
- **ONNX Runtime (Node.js)** によるAI推論
- FastAPI/Python別サーバー不要
- Vercel単体で完結

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
│  │                   │ ONNX Runtime    │  │   │
│  │                   │ (onnxruntime-   │  │   │
│  │                   │  node)          │  │   │
│  │                   └─────────────────┘  │   │
│  │                          │              │   │
│  │                          ▼              │   │
│  │                   ┌─────────────────┐  │   │
│  │                   │  ONNXモデル     │  │   │
│  │                   │  (*.onnx)       │  │   │
│  │                   └─────────────────┘  │   │
│  └─────────────────────────────────────────┘   │
└─────────────────────────────────────────────────┘
```

### 3.6.2 旧アーキテクチャとの比較

| 項目 | v1.x (FastAPI) | v2.0 (ONNX) |
|------|---------------|-------------|
| 推論サーバー | FastAPI (Python) | Next.js API Routes |
| モデル形式 | LightGBM (.pkl) | ONNX (.onnx) |
| 追加サーバー | Railway/Cloud Run必要 | **不要** |
| デプロイ複雑度 | 高（2サーバー管理） | **低（Vercelのみ）** |
| 精度 | 基準 | ほぼ同等（誤差1e-6以下） |
| コールドスタート | Python起動が遅い | **Node.js高速** |

### 3.6.3 ONNXモデル構成

**モデルファイル（6モデル）:**
| モデル名 | 用途 | ファイル名 |
|---------|------|-----------|
| n3_axis | N3軸数字予測 | n3_axis.onnx |
| n4_axis | N4軸数字予測 | n4_axis.onnx |
| n3_box_comb | N3ボックス組合せ予測 | n3_box_comb.onnx |
| n3_straight_comb | N3ストレート組合せ予測 | n3_straight_comb.onnx |
| n4_box_comb | N4ボックス組合せ予測 | n4_box_comb.onnx |
| n4_straight_comb | N4ストレート組合せ予測 | n4_straight_comb.onnx |

**配置場所:** `data/models/*.onnx`

### 3.6.4 実装構成

```
src/lib/predictor/
├── onnx-loader.ts      # ONNXモデル読み込み・キャッシュ
├── predictor.ts        # 予測実行（ONNX呼び出し）
└── feature-extractor.ts # 特徴量計算

src/app/api/predict/
├── route.ts            # POST /api/predict エンドポイント
└── combination/
    └── route.ts        # POST /api/predict/combination エンドポイント
```

### 3.6.5 技術スタック（v2.0）

**AI/ML推論**
- **onnxruntime-node**: 1.16.0+ （Node.js用ONNXランタイム）
- **ONNX形式**: LightGBMからの変換モデル

**学習環境（開発用、本番では使用しない）**
- **LightGBM**: モデル学習
- **onnxmltools**: ONNX変換
- **skl2onnx**: sklearn互換変換

### 3.6.6 廃止されたコンポーネント

以下のコンポーネントはv2.0で**廃止**または**開発用のみ**に変更:

| コンポーネント | 状態 | 理由 |
|--------------|------|------|
| `api/main.py` (FastAPI) | 廃止 | ONNX Runtime移行 |
| `api/predict/axis.py` | 廃止 | Next.js API Routes移行 |
| `api/predict/combination.py` | 廃止 | Next.js API Routes移行 |
| `notebooks/model_loader.py` | 開発用 | XGBoost用（学習時のみ） |
| `core/model_loader.py` | 開発用 | LightGBM用（学習時のみ） |
| `FASTAPI_URL` 環境変数 | 廃止 | 別サーバー不要 |

---

