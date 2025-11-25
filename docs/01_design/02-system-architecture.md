# システムアーキテクチャ設計書 v1.2

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

### 3.2.1 予測APIルーティング選定

**現状（MVP）**
- `src/app/api/predict/route.ts` が `POST /api/predict` を唯一のエンドポイントで、Next.js API Routes 内で特徴量計算・モデル呼び出しを完結させる。
- `src/lib/predictor/predictor.ts` は `fetch('/api/predict/axis')` を連携先として持っているが、Next.js API 側では `/axis` を受け付けていないため、リクエスト先は `POST /api/predict` に統一する必要がある。
- デプロイサイズ・ライブラリ制限を考えると、Vercel上で Python + `libgomp.so.1` を組みこむ FastAPI よりも、Next.js API Routes 単体での完結が安定する。

**FastAPIの位置付け**
- `api/main.py` には FastAPI による `/api/predict/axis` や `/api/predict/combination` の実装が存在するが、Vercel で Python 関数にモデルファイルとネイティブライブラリを含めると関数サイズ制限で失敗する恐れがあるため、本番環境での運用は控えている。
- FastAPI を活用するためには `USE_VERCEL_PYTHON` を `true` に切り替え、Next.js API ルートからプロキシして FastAPI を呼び出すパターンが必要になるが、現在は `/api/predict` を直接 Next.js で処理する方針。
- FastAPI を維持しつつ Vercel にデプロイするには `api/lib/libgomp.so.1` を手動配置する実績があるため、モデル検証や資料用としては残す価値がある。

**推奨方針**
- デプロイ済みの要求は `POST /api/predict` を正規ルートとし、Next.js API Routes で処理すること。
- FastAPI は文書化・実験用途、あるいは将来専用サービスとして分離する。ローカル開発では `uvicorn api.main:app` で容易にテストできるので、実験資産として維持。
- フロントエンドから FastAPI を使う場合は、ドキュメント上で `/api/predict/axis` への呼び出しが 405 になる点と、Next.js ルートへの統一が必要であることを明示する。

### 3.2.2 予測エンドポイントの実装構成

```
[フロントエンド predictor.ts]
         │
         ▼
   POST /api/predict       ←─ フロントは `/api/predict/axis` を直接呼ばず、Next.js ルートに集約
         │
         ▼
[Next.js API Route]       ← バリデーション / レスポンス整形 / ログ制御
         │
         ▼
[fastapi-bridge.ts]      ← 軽量な内部 fetch で `/api/predict/axis` と `/api/predict/combination` を呼ぶ
         │
         ▼
[FastAPI Predict API]    ← Python/LightGBM モデルで推論 → JSON を返却
```

- Next.js 側でバリデーション・エラー処理を行うため、FastAPI の失敗（モデル読み込みタイムアウトなど）も Next.js で 500 へ統一できる。
- `/api/predict/axis` へのアクセスは `src/lib/predictor/fastapi-bridge.ts` のみで、他に直接叩いている箇所は存在しない（`rg /api/predict/axis` で確認）。
- ローカルでは `pnpm dev` + `uvicorn api.main:app` でも同じフローを再現でき、以降のログがプロダクションと同じ順序になる。

### 3.2.3 FastAPI vs Next.js API 完結の比較

| 評価軸 | Next.js API Route（現行：`/api/predict`） | FastAPI（`/api/predict/axis` 等） |
|--------|---------------------------------------------|----------------------------------|
| デプロイサイズ / 依存 | Node.js + TypeScript の軽量構成。Vercel の関数サイズ制限に収まりやすい | LightGBM + `libgomp.so.1` + Pickle を含むため、Vercel の ZIP 圧縮でサイズ超過リスクが高い |
| モデル検証・改修 | `fastapi-bridge.ts` で Python 資産へアクセスしつつ、必要部分を Next.js だけで置き換え可能 | 既存 Python 実装をそのまま使えるため、実験サイクルが速い |
| ローカル開発・デバッグ | `pnpm dev` の Next.js だけで UI→API→FastAPI の流れを追え、ログも統一できる | `uvicorn api.main:app` + Next.js の併走が必要でログが分散しやすい |
| 特徴量処理と再利用 | `predictor.ts` を通じて UI/Next.js のロジックを共有できる | 再利用想定なら Node 側で再実装が必要 |
| 本番の安定性 | Next.js ルートだけで完結するため運用負荷が低い | FastAPI を Vercel Python 関数としてデプロイすると 405 や依存サイズの問題が出やすい |

→ 現状は Next.js API Route を正規ルートとし、FastAPI へは `fastapi-bridge.ts` 経由で必要な処理だけを委譲するハイブリッド構成が最適。

### 3.2.4 Next.js API 完全移行ロードマップ

1. **依存の切り出し** – `fastapi-bridge.ts` の `predictAxis` / `predictCombination` を、Node 版モジュール（例: `src/lib/predictor/node-models.ts`）と同じインターフェースで置き換える実験をローカルで行い、`fastapi-bridge.ts` が FastAPI 呼び出しに依存しないことを確認する。
2. **モデルの軽量化** – Pickle/LightGBM/`libgomp.so.1` を代替できる ONNX・JSON スコア・簡易統計を検討し、Next.js 環境で読み込める軽量モデルを用意する。プロトタイプを API ルートに組み込んで `pnpm dev`・`npm run build` 通過を確認する。
3. **Next.js API への統合** – `src/app/api/predict/route.ts` が直接 Node 版ロード・スコア計算を呼び出すように変更し、`FASTAPI_URL` 環境変数や `fastapi-bridge.ts` を本番コードから除外する。ログ/エラーは既存通り Next.js で出力できるため、FastAPI の 405/ECONNREFUSED 問題が消失。
4. **CI/本番での検証** – Vercel 上で `npm run build` / `next build` を回して `ECONNREFUSED` などのログが出ないこと、`fastapi-bridge.ts` へのアクセスログがなくなることを確認し、デプロイ済みの `predictor.ts` に `/api/predict` のみが含まれることを記録。
5. **ドキュメント同期** – 本ロードマップと「Next.js API 完全構成で Vercel が唯一の依存」としてこの節を 01_design/02-system-architecture.md に載せ、`docs/01_design/03-data-api-design.md` でも FastAPI direct を補足資料に位置づけることで運用判断を明文化する。

### 3.2.5 Node ベースの予測モジュール設計

- **目標**: 現在の LightGBM モデル（`data/models/*.pkl`）と `libgomp.so.1` を捨てずに、Next.js 側から直接利用できる Node モジュール（`src/lib/predictor/node-models.ts`）を用意する。
- **アプローチ**:
  1. Python スクリプト（例: `scripts/node_model_server.py`）を用意し、LightGBM モデルと `libgomp` を `joblib`/`pickle` からロードした上で gRPC または stdin/stdout で特徴量ベクトルを受け取り確率を返す。Next.js とは軽量な IPC（`child_process.spawn` + JSON）で通信する。
  2. Node モデルロード層では、特徴量キーを `core/feature_extractor.py` 相当の計算結果に変換し、Python 側リクエストを自動化。`fastapi-bridge.ts` と同じ `predictAxis`/`predictCombination` シグネチャを維持することで、API Route の差し替えは容易。
  3. 必要であれば ONNX や JSON キャッシュに変換し、Python スクリプトの依存を減らす方向に進める。それまでは既存のモデル資産を Python 側で使いつつ、Next.js からは Node モジュール経由で呼び出す。
- **メリット**: LightGBM そのままを継承しながら、Vercel には Node.js 側のみデプロイ。FastAPI や別サーバーを立てず本番で `localhost:8000` へ接続しない構成を確立でき、ロードマップ Step2~3 に合致。

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

