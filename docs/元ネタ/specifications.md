# ナンバーズAI予測システム - 技術仕様書 v1.0

**ドキュメント管理情報**
- バージョン: 1.0
- 作成日: 2025-11-02
- 最終更新日: 2025-11-02
- ステータス: 確定版
- 承認者: 技術リード

---

## 📋 目次

1. [ドキュメント目的と適用範囲](#1-ドキュメント目的と適用範囲)
2. [システムアーキテクチャ](#2-システムアーキテクチャ)
3. [技術スタック](#3-技術スタック)
4. [ディレクトリ構成](#4-ディレクトリ構成)
5. [データモデル](#5-データモデル)
6. [予測表生成アルゴリズム](#6-予測表生成アルゴリズム)
7. [AI特徴量設計](#7-ai特徴量設計)
8. [AIモデルアーキテクチャ](#8-aiモデルアーキテクチャ)
9. [API仕様](#9-api仕様)
10. [フロントエンド設計](#10-フロントエンド設計)
11. [CI/CD](#11-cicd)
12. [セキュリティ設計](#12-セキュリティ設計)
13. [Definition of Done](#13-definition-of-done)

---

## 1. ドキュメント目的と適用範囲

### 1.1 目的
本ドキュメントは、ナンバーズAI予測システムの技術的な実装仕様を定義する。開発者が本書に従うことで、一貫性のある高品質なコードを実装し、システム全体の保守性・拡張性を担保する。

### 1.2 対象読者
- フルスタックエンジニア
- フロントエンド開発者
- バックエンド開発者
- データサイエンティスト
- DevOpsエンジニア

### 1.3 参照ドキュメント
- docs/requirements.md: 要件定義書
- docs/UIイメージ.md: UI/UX設計書
- docs/表作成ルール.,md: アルゴリズム仕様書
- docs/企画内容.md: プロジェクト概要

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
- アルゴリズム実装（docs/表作成ルール.,md準拠）
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

### 3.3 AI/ML

**機械学習**
- **XGBoost**: 2.0.0+（メインアルゴリズム）
- **scikit-learn**: 1.3.0+（前処理、評価）
- **Pandas**: 2.1.0+（データ操作）
- **NumPy**: 1.26.0+（数値計算）

**実験管理**
- **Jupyter Notebook**: 開発・実験
- **Weights & Biases (wandb)**: Phase 3以降

### 3.4 データストア

**MVP版**
- **CSV**: ローカルファイルストレージ
- **JSON**: 罫線マスターデータ

**Phase 4**
- **Supabase PostgreSQL**: 15.0+
  - 過去実績データ
  - 予測表データ
  - ユーザーデータ
- **Supabase Storage**: 学習済みモデル

### 3.5 インフラ・デプロイ

**MVP版**
- **Vercel**: ホスティング + CI/CD
- **GitHub**: ソースコード管理

**Phase 4**
- **Vercel**: フロントエンド
- **GCP Cloud Run**: AI Engine API
- **GCP Cloud Storage**: モデルストレージ
- **Supabase**: データベース

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
│   ├── requirements.md            # 要件定義書
│   ├── specifications.md          # 技術仕様書（本書）
│   ├── UIイメージ.md              # UI設計
│   ├── 企画内容.md                # プロジェクト概要
│   ├── 表作成ルール.,md           # アルゴリズム仕様
│   └── 要望-元設計.md             # 元設計
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
│   ├── favicon.ico
│   └── images/
│
├── .github/
│   └── workflows/
│       └── ci.yml                 # GitHub Actions
│
├── package.json
├── tsconfig.json
├── next.config.js
├── tailwind.config.ts
├── .eslintrc.json
├── .prettierrc
├── .env.local.example
└── README.md
```

### 4.2 Phase 4完全版構成（モノレポ）

```
numbers-ai/
├── apps/
│   ├── web/                       # Next.js フロントエンド
│   └── api/                       # FastAPI バックエンド
│
├── packages/
│   ├── types/                     # 共通型定義
│   ├── utils/                     # 共通ユーティリティ
│   └── config/                    # 共通設定
│
└── (その他MVP版と同様)
```

---

## 5. データモデル

### 5.1 CSVデータ構造（MVP版）

#### past_results.csv

過去の当選番号とリハーサル数字を格納。

**カラム定義:**

```
round_number    : 回号（4桁整数）
draw_date       : 抽選日（YYYY-MM-DD）
n3_winning      : N3当選番号（3桁文字列、例: "123"）
n4_winning      : N4当選番号（4桁文字列、例: "1234"）
n3_rehearsal    : N3リハーサル（3桁文字列、NULL可）
n4_rehearsal    : N4リハーサル（4桁文字列、NULL可）
```

**サンプルデータ:**

```csv
round_number,draw_date,n3_winning,n4_winning,n3_rehearsal,n4_rehearsal
6701,2025-01-10,147,3782,149,3782
6700,2025-01-09,523,1056,NULL,NULL
6699,2025-01-08,891,7324,894,7329
```

**制約:**
- round_number: ユニークキー
- draw_date: 日付形式
- winning/rehearsal: 数字文字列（0埋めあり）

---

#### keisen_master.json

中国罫線の予測出目ルールを格納。

**JSON構造:**

```json
{
  "n3": {
    "columns": {
      "百の位": {
        "0": { "0": [0, 5], "1": [1, 6], ... },
        "1": { "0": [2, 7], ... },
        ...
      },
      "十の位": { ... },
      "一の位": { ... }
    }
  },
  "n4": {
    "columns": {
      "千の位": { ... },
      "百の位": { ... },
      "十の位": { ... },
      "一の位": { ... }
    }
  }
}
```

**詳細説明:**
- トップレベル: `n3` / `n4`
- `columns`: 各桁の定義
- 桁 → 前回の数字 → 前々回の数字 → 予測出目配列

**例:**
```json
{
  "n3": {
    "columns": {
      "百の位": {
        "0": {
          "0": [0, 5],
          "1": [1, 6],
          "2": [2, 7, 0]
        }
      }
    }
  }
}
```

意味: N3の百の位で、前回が0、前々回が0の場合、予測出目は `[0, 5]`

---

### 5.2 データベーススキーマ（Phase 4: Supabase PostgreSQL）

#### テーブル: past_results

```sql
CREATE TABLE past_results (
  id                 SERIAL PRIMARY KEY,
  round_number       INTEGER NOT NULL UNIQUE,
  draw_date          DATE NOT NULL,
  n3_winning         CHAR(3) NOT NULL,
  n4_winning         CHAR(4) NOT NULL,
  n3_rehearsal       CHAR(3),
  n4_rehearsal       CHAR(4),
  created_at         TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at         TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_round_number ON past_results(round_number);
CREATE INDEX idx_draw_date ON past_results(draw_date);
```

---

#### テーブル: generated_charts

```sql
CREATE TABLE generated_charts (
  id                 SERIAL PRIMARY KEY,
  round_number       INTEGER NOT NULL,
  target             VARCHAR(2) NOT NULL,  -- 'n3' or 'n4'
  pattern            CHAR(1) NOT NULL,     -- 'A' or 'B'
  chart_data         JSONB NOT NULL,       -- 2次元配列
  source_digits      INTEGER[] NOT NULL,   -- 元数字リスト
  generated_at       TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  
  UNIQUE(round_number, target, pattern)
);

CREATE INDEX idx_charts_round ON generated_charts(round_number);
```

**chart_data JSONサンプル:**

```json
{
  "grid": [
    [0, 5, 1, 6, 2, 7, 3, 8],
    [5, 0, 6, 1, 7, 2, 8, 3],
    ...
  ],
  "rows": 8,
  "cols": 8
}
```

---

#### テーブル: prediction_history（Phase 4）

```sql
CREATE TABLE prediction_history (
  id                 SERIAL PRIMARY KEY,
  user_id            UUID REFERENCES auth.users(id),
  round_number       INTEGER NOT NULL,
  n3_rehearsal       CHAR(3),
  n4_rehearsal       CHAR(4),
  prediction_result  JSONB NOT NULL,       -- 予測結果全体
  created_at         TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_history_user ON prediction_history(user_id);
CREATE INDEX idx_history_round ON prediction_history(round_number);
```

---

#### テーブル: users（Phase 4）

Supabase Authのデフォルトテーブルを使用。カスタムフィールドは追加しない。

---

### 5.3 TypeScript型定義

#### 予測結果型

```typescript
// src/types/prediction.ts

export type Target = 'n3' | 'n4';
export type Pattern = 'A' | 'B';
export type PredictionType = 'box' | 'straight';

export interface AxisCandidate {
  digit: number;              // 0-9
  score: number;              // 0-1000
  confidence: number;         // 0-100
  source: Pattern;            // 'A' | 'B'
}

export interface NumberCandidate {
  numbers: string;            // 例: "147"
  score: number;
  confidence: number;
  source: Pattern;
  rank: number;
  axis?: number;              // 含まれる軸数字（軸モード時）
}

export interface PredictionResult {
  roundNumber: number;
  n3: {
    box: {
      axisCandidates: AxisCandidate[];
      numberCandidates: NumberCandidate[];
    };
    straight: {
      axisCandidates: AxisCandidate[];
      numberCandidates: NumberCandidate[];
    };
  };
  n4: {
    box: {
      axisCandidates: AxisCandidate[];
      numberCandidates: NumberCandidate[];
    };
    straight: {
      axisCandidates: AxisCandidate[];
      numberCandidates: NumberCandidate[];
    };
  };
  generatedAt: string;        // ISO 8601
}
```

#### 予測表型

```typescript
// src/types/chart.ts

export type ChartGrid = (number | null)[][];

export interface ChartData {
  grid: ChartGrid;
  rows: number;
  cols: number;
  pattern: Pattern;
  target: Target;
  sourceDigits: number[];
}

export interface MainRow {
  elements: [number, number, number, number];
  rowIndex: number;
}
```

---

## 6. 予測表生成アルゴリズム

本セクションは `docs/表作成ルール.,md` の内容を実装可能な形で再整理する。

### 6.1 アルゴリズムフロー

```
入力: round_number, pattern ('A' | 'B'), target ('n3' | 'n4')

ステップ1: 予測出目の抽出
  - round_number-1 (前回) と round_number-2 (前々回) の当選番号を取得
  - keisen_master.json から各桁の予測出目を取得
  - 全桁の予測出目を結合 → source_list

ステップ2: パターン別の元数字リスト作成
  - pattern = 'A' (0なし):
    - source_list に 0-9 の欠番をすべて追加
  - pattern = 'B' (0あり):
    - source_list に 0 が含まれていなければ 0 を1つ追加
  - 昇順ソート → nums

ステップ3: メイン行の組み立て
  - mainRows = []
  - while nums が空でない:
    - uniqueDigits = nums のユニーク値（昇順）
    - if uniqueDigits.length >= 4:
      - members = uniqueDigits[0..3]
      - newRow = nums から members の各値を1個ずつ取り出して配列化
      - mainRows.push(newRow)
      - nums から newRow で使った数字を削除
    - else:
      - newRow = uniqueDigits の全要素
      - while newRow.length < 4:
        - newRow.push(max(uniqueDigits))
      - mainRows.push(newRow)
      - nums から newRow で使った数字を削除

ステップ4: グリッド初期配置
  - rows = mainRows.length * 2
  - cols = 8
  - grid = rows × cols の2次元配列（初期値 null）
  - for i in 0..mainRows.length-1:
    - row = i * 2
    - for j in 0..3:
      - grid[row][j*2] = mainRows[i][j]

ステップ5: パターンB中心0配置
  - if pattern = 'B':
    - centerRows = [floor((rows-1)/2), ceil((rows-1)/2)]
    - centerCols = [floor((cols-1)/2), ceil((cols-1)/2)]
    - for r in centerRows:
      - for c in centerCols:
        - if grid[r][c] = null:
          - grid[r][c] = 0
          - break outer loop

ステップ6: 裏数字ルール（縦パス）
  - inverse(n) = (n + 5) % 10
  - repeat:
    - updated = false
    - for y in 0..rows-1:
      - for x in 0..cols-1:
        - if grid[y][x] = null and y > 0 and grid[y-1][x] != null:
          - grid[y][x] = inverse(grid[y-1][x])
          - updated = true
  - until not updated

ステップ7: 裏数字ルール（横パス）
  - repeat:
    - updated = false
    - for y in 0..rows-1:
      - for x in 0..cols-1:
        - if grid[y][x] = null and x > 0 and grid[y][x-1] != null:
          - grid[y][x] = inverse(grid[y][x-1])
          - updated = true
  - until not updated

ステップ8: 余りマスルール
  - repeat:
    - updated = false
    - for y in 0..rows-1:
      - for x in 0..cols-1:
        - if grid[y][x] = null and y > 0 and grid[y-1][x] != null:
          - grid[y][x] = grid[y-1][x]
          - updated = true
  - until not updated

出力: grid (完成した予測表)
```

### 6.2 TypeScript実装例

```typescript
// src/lib/chart-generator/index.ts

export function generateChart(
  roundNumber: number,
  pattern: Pattern,
  target: Target
): ChartData {
  // Step 1: 予測出目の抽出
  const sourceList = extractPredictedDigits(roundNumber, target);
  
  // Step 2: 元数字リスト作成
  const nums = applyPatternExpansion(sourceList, pattern);
  
  // Step 3: メイン行の組み立て
  const mainRows = buildMainRows(nums);
  
  // Step 4: グリッド初期配置
  const rows = mainRows.length * 2;
  const cols = 8;
  const grid = initializeGrid(rows, cols, mainRows);
  
  // Step 5: パターンB中心0配置
  if (pattern === 'B') {
    placeCenterZero(grid, rows, cols);
  }
  
  // Step 6-8: 裏数字・余りマスルール
  applyVerticalInverse(grid, rows, cols);
  applyHorizontalInverse(grid, rows, cols);
  applyRemainingCopy(grid, rows, cols);
  
  return {
    grid,
    rows,
    cols,
    pattern,
    target,
    sourceDigits: sourceList
  };
}

function inverse(n: number): number {
  return (n + 5) % 10;
}

function buildMainRows(nums: number[]): MainRow[] {
  const mainRows: MainRow[] = [];
  let tempList = [...nums];
  let rowIndex = 0;
  
  while (tempList.length > 0) {
    const uniqueDigits = [...new Set(tempList)].sort((a, b) => a - b);
    
    if (uniqueDigits.length >= 4) {
      const members = uniqueDigits.slice(0, 4);
      const newRow: [number, number, number, number] = [0, 0, 0, 0];
      
      for (let i = 0; i < 4; i++) {
        const idx = tempList.indexOf(members[i]);
        newRow[i] = tempList[idx];
        tempList.splice(idx, 1);
      }
      
      mainRows.push({ elements: newRow, rowIndex: rowIndex++ });
    } else {
      const maxValue = Math.max(...uniqueDigits);
      const newRow: [number, number, number, number] = [...uniqueDigits, 0, 0, 0].slice(0, 4) as [number, number, number, number];
      
      for (let i = uniqueDigits.length; i < 4; i++) {
        newRow[i] = maxValue;
      }
      
      // tempListから使用した数字を削除
      for (const digit of newRow) {
        const idx = tempList.indexOf(digit);
        if (idx !== -1) tempList.splice(idx, 1);
      }
      
      mainRows.push({ elements: newRow, rowIndex: rowIndex++ });
    }
  }
  
  return mainRows;
}

function applyVerticalInverse(grid: ChartGrid, rows: number, cols: number): void {
  let updated = true;
  while (updated) {
    updated = false;
    for (let y = 0; y < rows; y++) {
      for (let x = 0; x < cols; x++) {
        if (grid[y][x] === null && y > 0 && grid[y-1][x] !== null) {
          grid[y][x] = inverse(grid[y-1][x]!);
          updated = true;
        }
      }
    }
  }
}

// 他の関数も同様に実装...
```

---

## 7. AI特徴量設計

### 7.1 特徴量カテゴリ

AIモデルが学習する特徴量は、以下の4カテゴリに分類される。

#### カテゴリ1: 形状特徴（Shape Features）

予測表上の数字の配置パターンから抽出される幾何学的特徴。

**具体的な特徴量（例）:**
- **線の長さ**: 同じ数字が連続する最大長
- **曲がりの回数**: 数字の配置方向が変わる回数
- **直線度**: 配置が直線的かどうかの度合い
- **密集度**: 特定エリアへの集中度合い

**計算例（TypeScript）:**

```typescript
function calculateLineLength(grid: ChartGrid, number: number): number {
  let maxLength = 0;
  // 横方向の連続チェック
  for (let y = 0; y < grid.length; y++) {
    let currentLength = 0;
    for (let x = 0; x < grid[y].length; x++) {
      if (grid[y][x] === number) {
        currentLength++;
        maxLength = Math.max(maxLength, currentLength);
      } else {
        currentLength = 0;
      }
    }
  }
  // 縦方向も同様にチェック...
  return maxLength;
}
```

---

#### カテゴリ2: 位置特徴（Position Features）

数字が表のどこに配置されているかに関する特徴。

**具体的な特徴量:**
- **重心X座標**: 数字の平均X位置
- **重心Y座標**: 数字の平均Y位置
- **左端からの距離**: 最左位置
- **右端からの距離**: 最右位置
- **上端からの距離**: 最上位置
- **下端からの距離**: 最下位置
- **中心からの距離**: 表の中心からの平均距離

**計算例:**

```typescript
function calculateCentroid(grid: ChartGrid, number: number): { x: number; y: number } {
  let sumX = 0, sumY = 0, count = 0;
  
  for (let y = 0; y < grid.length; y++) {
    for (let x = 0; x < grid[y].length; x++) {
      if (grid[y][x] === number) {
        sumX += x;
        sumY += y;
        count++;
      }
    }
  }
  
  return count > 0 
    ? { x: sumX / count, y: sumY / count }
    : { x: 0, y: 0 };
}
```

---

#### カテゴリ3: 関係性特徴（Relation Features）

候補数字とリハーサル数字の関係性に関する特徴。

**具体的な特徴量:**
- **リハーサルとの距離**: 候補ラインとリハーサルラインの平均距離
- **重なり度**: 候補とリハーサルが同じ位置にある回数
- **角度**: 候補ラインとリハーサルラインの角度差
- **裏数字関係**: 候補がリハーサルの裏数字である割合

**計算例:**

```typescript
function calculateRehearsalDistance(
  candidatePositions: {x: number, y: number}[],
  rehearsalPositions: {x: number, y: number}[]
): number {
  if (candidatePositions.length === 0 || rehearsalPositions.length === 0) {
    return Infinity;
  }
  
  let totalDistance = 0;
  for (const cPos of candidatePositions) {
    let minDist = Infinity;
    for (const rPos of rehearsalPositions) {
      const dist = Math.sqrt(
        Math.pow(cPos.x - rPos.x, 2) + Math.pow(cPos.y - rPos.y, 2)
      );
      minDist = Math.min(minDist, dist);
    }
    totalDistance += minDist;
  }
  
  return totalDistance / candidatePositions.length;
}
```

---

#### カテゴリ4: 集約特徴（Aggregate Features）

組み合わせ全体に関する統計的特徴。

**具体的な特徴量:**
- **出現頻度**: 表内での組み合わせの出現回数
- **パターン密集度**: 組み合わせを構成する数字の密集度
- **分散度**: 数字の配置の分散
- **偏り度**: 表の特定エリアへの偏り

---

### 7.2 特徴量エンジニアリングパイプライン

```
[予測表] + [リハーサル数字]
    │
    ▼
[数字位置の抽出]
    │ - 各数字(0-9)の座標リストを生成
    │ - リハーサル数字の座標リストを生成
    ▼
[カテゴリ1: 形状特徴計算]
    │ - 各数字の線の長さ、曲がり、直線度など
    ▼
[カテゴリ2: 位置特徴計算]
    │ - 各数字の重心、端からの距離など
    ▼
[カテゴリ3: 関係性特徴計算]
    │ - 候補とリハーサルの距離、重なりなど
    ▼
[カテゴリ4: 集約特徴計算]
    │ - 組み合わせ全体の統計量
    ▼
[特徴量ベクトル] (数百次元)
    │
    ▼
[正規化・スケーリング]
    │ - StandardScaler または MinMaxScaler
    ▼
[AIモデルへ入力]
```

### 7.3 特徴量の実装構造

```typescript
// src/lib/feature-extraction/index.ts

export interface FeatureVector {
  // 形状特徴 (40次元)
  shapeFeatures: number[];
  
  // 位置特徴 (30次元)
  positionFeatures: number[];
  
  // 関係性特徴 (20次元)
  relationFeatures: number[];
  
  // 集約特徴 (10次元)
  aggregateFeatures: number[];
  
  // メタデータ
  metadata: {
    pattern: Pattern;
    target: Target;
    predictionType: PredictionType;
  };
}

export function extractFeatures(
  chart: ChartData,
  rehearsal: string,
  candidate: string,
  predictionType: PredictionType
): FeatureVector {
  const shapeFeatures = calculateShapeFeatures(chart, candidate);
  const positionFeatures = calculatePositionFeatures(chart, candidate);
  const relationFeatures = calculateRelationFeatures(chart, rehearsal, candidate);
  const aggregateFeatures = calculateAggregateFeatures(chart, candidate);
  
  return {
    shapeFeatures,
    positionFeatures,
    relationFeatures,
    aggregateFeatures,
    metadata: {
      pattern: chart.pattern,
      target: chart.target,
      predictionType
    }
  };
}
```

---

## 8. AIモデルアーキテクチャ

### 8.1 モデル構成

本システムは **8つの独立したXGBoostモデル** で構成される。

| モデルID | 対象 | 予測タイプ | 予測内容 | ファイル名 |
|---------|------|-----------|---------|-----------|
| M-N3-B-A | N3 | ボックス | 軸数字 | n3_box_axis.pkl |
| M-N3-B-C | N3 | ボックス | 組み合わせ | n3_box_comb.pkl |
| M-N3-S-A | N3 | ストレート | 軸数字 | n3_straight_axis.pkl |
| M-N3-S-C | N3 | ストレート | 組み合わせ | n3_straight_comb.pkl |
| M-N4-B-A | N4 | ボックス | 軸数字 | n4_box_axis.pkl |
| M-N4-B-C | N4 | ボックス | 組み合わせ | n4_box_comb.pkl |
| M-N4-S-A | N4 | ストレート | 軸数字 | n4_straight_axis.pkl |
| M-N4-S-C | N4 | ストレート | 組み合わせ | n4_straight_comb.pkl |

### 8.2 学習データ構造

#### 軸数字予測モデルの学習データ

**特徴量（X）:**
- 予測表の特徴量（100次元）
- パターン情報（A=0, B=1）
- 対象数字（0-9）の個別特徴（40次元）

**ラベル（y）:**
- 0 または 1（その数字が当選番号に含まれたか）

**データ生成:**
```
過去1回につき、10サンプル生成（数字0-9それぞれ）
100回分のデータ → 1,000サンプル
```

---

#### 組み合わせ予測モデルの学習データ

**特徴量（X）:**
- 予測表の特徴量（100次元）
- 組み合わせの集約特徴（30次元）
- 指定された軸数字の情報（10次元）

**ラベル（y）:**
- 0 または 1（その組み合わせが当選したか）

**データ生成:**
```
過去1回につき、数百〜数千サンプル生成
（全組み合わせまたはサンプリング）
100回分のデータ → 数万〜数十万サンプル
```

### 8.3 XGBoostハイパーパラメータ

```python
# notebooks/04_model_training.ipynb

xgb_params = {
    'objective': 'binary:logistic',
    'eval_metric': 'logloss',
    'max_depth': 6,
    'learning_rate': 0.05,
    'n_estimators': 500,
    'subsample': 0.8,
    'colsample_bytree': 0.8,
    'min_child_weight': 3,
    'gamma': 0.1,
    'reg_alpha': 0.1,
    'reg_lambda': 1.0,
    'random_state': 42,
    'n_jobs': -1
}

model = xgb.XGBClassifier(**xgb_params)
model.fit(X_train, y_train, eval_set=[(X_val, y_val)], early_stopping_rounds=50)
```

### 8.4 モデル評価指標

- **AUC-ROC**: 主要評価指標（目標: 0.65以上）
- **Precision**: 適合率
- **Recall**: 再現率
- **F1-Score**: 調和平均
- **Top-K Accuracy**: 上位K件中に正解が含まれる確率

### 8.5 推論フロー

```
[ユーザー入力]
    │
    ▼
[予測表生成] (パターンA/B)
    │
    ▼
[特徴量計算]
    │
    ├─→ [軸数字予測モデル]
    │     │ 入力: 10サンプル (数字0-9)
    │     │ 出力: 各数字の確率 [p0, p1, ..., p9]
    │     │
    │     ▼
    │   [スコア算出] score = probability * 1000
    │     │
    │     ▼
    │   [ランキング] (降順ソート)
    │
    └─→ [組み合わせ予測モデル]
          │ 入力: 軸を含む全組み合わせの特徴量
          │ 出力: 各組み合わせの確率
          │
          ▼
        [スコア算出・ランキング]
          │
          ▼
        [結果返却]
```

---

## 9. API仕様

### 9.1 エンドポイント一覧

| エンドポイント | メソッド | 説明 | 認証 |
|---------------|---------|------|------|
| /api/predict | POST | 予測実行 | 不要（MVP） |
| /api/charts | POST | 予測表生成のみ | 不要 |
| /api/health | GET | ヘルスチェック | 不要 |

### 9.2 POST /api/predict

**概要:** 回号とリハーサル数字を受け取り、AI予測結果を返す。

**リクエスト:**

```typescript
POST /api/predict
Content-Type: application/json

{
  "roundNumber": 6701,
  "n3Rehearsal": "149",
  "n4Rehearsal": "3782"
}
```

**リクエストスキーマ（Zod）:**

```typescript
import { z } from 'zod';

export const PredictRequestSchema = z.object({
  roundNumber: z.number().int().min(1).max(9999),
  n3Rehearsal: z.string().regex(/^[0-9]{3}$/),
  n4Rehearsal: z.string().regex(/^[0-9]{4}$/)
});

export type PredictRequest = z.infer<typeof PredictRequestSchema>;
```

**レスポンス（成功）:**

```typescript
HTTP/1.1 200 OK
Content-Type: application/json

{
  "success": true,
  "data": {
    "roundNumber": 6701,
    "n3": {
      "box": {
        "axisCandidates": [
          { "digit": 7, "score": 985, "confidence": 98, "source": "A" },
          { "digit": 2, "score": 952, "confidence": 95, "source": "A" },
          { "digit": 4, "score": 847, "confidence": 85, "source": "B" }
        ],
        "numberCandidates": [
          { "numbers": "147", "score": 978, "confidence": 98, "source": "A", "rank": 1, "axis": 7 },
          { "numbers": "079", "score": 942, "confidence": 94, "source": "A", "rank": 2, "axis": 7 }
        ]
      },
      "straight": {
        "axisCandidates": [ ... ],
        "numberCandidates": [ ... ]
      }
    },
    "n4": {
      "box": { ... },
      "straight": { ... }
    },
    "generatedAt": "2025-11-02T12:34:56.789Z"
  }
}
```

**レスポンス（エラー）:**

```typescript
HTTP/1.1 400 Bad Request
Content-Type: application/json

{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input data",
    "details": [
      { "field": "n3Rehearsal", "message": "Must be a 3-digit string" }
    ]
  }
}
```

**エラーコード:**

| コード | HTTPステータス | 説明 |
|--------|---------------|------|
| VALIDATION_ERROR | 400 | 入力データが不正 |
| DATA_NOT_FOUND | 404 | 過去データが見つからない |
| MODEL_ERROR | 500 | AIモデルの実行エラー |
| INTERNAL_ERROR | 500 | その他の内部エラー |

### 9.3 POST /api/charts

**概要:** 予測表の生成のみを行う（デバッグ用）。

**リクエスト:**

```json
{
  "roundNumber": 6701,
  "pattern": "A",
  "target": "n3"
}
```

**レスポンス:**

```json
{
  "success": true,
  "data": {
    "grid": [
      [0, 5, 1, 6, 2, 7, 3, 8],
      [5, 0, 6, 1, 7, 2, 8, 3],
      ...
    ],
    "rows": 8,
    "cols": 8,
    "sourceDigits": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
  }
}
```

### 9.4 GET /api/health

**概要:** APIの稼働状態を確認。

**レスポンス:**

```json
{
  "status": "ok",
  "timestamp": "2025-11-02T12:34:56.789Z",
  "version": "1.0.0",
  "models": {
    "n3_box_axis": "loaded",
    "n3_box_comb": "loaded",
    "n4_box_axis": "loaded",
    "n4_box_comb": "loaded"
  }
}
```

---

## 10. フロントエンド設計

### 10.1 コンポーネント階層

```
App
├── Layout
│   ├── Header
│   └── Navigation
│
├── HomePage (/)
│   └── StartPredictionButton
│
├── PredictPage (/predict)
│   ├── RoundInputPage (/predict/input)
│   │   ├── RoundInput
│   │   └── NextButton
│   │
│   ├── RehearsalInputPage (/predict/rehearsal)
│   │   ├── RehearsalInput (N3)
│   │   ├── RehearsalInput (N4)
│   │   └── ExecuteButton
│   │
│   └── ResultPage (/predict/result)
│       ├── TabGroup (N3/N4)
│       ├── SubTabGroup (Box/Straight)
│       ├── ModeToggle (Axis/Overall)
│       │
│       ├── AxisCandidatesView
│       │   ├── AxisCard (Accordion)
│       │   │   ├── AxisHeader
│       │   │   └── NumberCandidatesTable
│       │   └── ManualAxisInput
│       │
│       └── OverallRankingView
│           └── NumberCandidatesTable
│
└── LoadingOverlay
```

### 10.2 状態管理（Redux Toolkit）

**Store構造:**

```typescript
// src/store/index.ts

interface RootState {
  prediction: PredictionState;
  ui: UIState;
}

interface PredictionState {
  roundNumber: number | null;
  n3Rehearsal: string;
  n4Rehearsal: string;
  result: PredictionResult | null;
  loading: boolean;
  error: string | null;
}

interface UIState {
  currentTab: 'n3' | 'n4';
  currentSubTab: 'box' | 'straight';
  currentMode: 'axis' | 'overall';
  expandedAxis: number[];
}
```

**主要なAction:**

```typescript
// src/store/slices/prediction-slice.ts

export const predictionSlice = createSlice({
  name: 'prediction',
  initialState,
  reducers: {
    setRoundNumber: (state, action: PayloadAction<number>) => {
      state.roundNumber = action.payload;
    },
    setN3Rehearsal: (state, action: PayloadAction<string>) => {
      state.n3Rehearsal = action.payload;
    },
    setN4Rehearsal: (state, action: PayloadAction<string>) => {
      state.n4Rehearsal = action.payload;
    },
    setPredictionResult: (state, action: PayloadAction<PredictionResult>) => {
      state.result = action.payload;
      state.loading = false;
    },
    setLoading: (state, action: PayloadAction<boolean>) => {
      state.loading = action.payload;
    },
    setError: (state, action: PayloadAction<string>) => {
      state.error = action.payload;
      state.loading = false;
    }
  }
});
```

### 10.3 スタイリング規約

**Tailwind CSSクラス命名:**

- レイアウト: `flex`, `grid`, `container`
- スペーシング: `p-4`, `m-2`, `gap-4`
- カラー: `bg-primary`, `text-secondary`, `border-accent`
- タイポグラフィ: `text-lg`, `font-semibold`, `leading-relaxed`

**カスタムカラー定義:**

```typescript
// tailwind.config.ts

export default {
  theme: {
    extend: {
      colors: {
        primary: '#6366F1',    // インディゴ
        secondary: '#374151',  // ミディアムグレー
        accent: '#F59E0B',     // アンバー
        success: '#10B981',    // グリーン
        error: '#EF4444',      // レッド
        background: '#1F2937', // ダークグレー
        card: '#374151',       // カード背景
        text: '#F9FAFB'        // テキスト
      }
    }
  }
};
```

### 10.4 アクセシビリティ対応

- `<button>` にはaria-label
- `<input>` にはlabel関連付け
- フォーカス可能な要素に`focus:ring-2`
- キーボードナビゲーション対応（Tab, Enter, Escape）
- カラーコントラスト比 4.5:1以上

---

## 11. CI/CD

### 11.1 GitHub Actions ワークフロー

**ファイル:** `.github/workflows/ci.yml`

```yaml
name: CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: pnpm/action-setup@v2
        with:
          version: 8.12.0
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'pnpm'
      - run: pnpm install
      - run: pnpm lint

  typecheck:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: pnpm/action-setup@v2
        with:
          version: 8.12.0
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'pnpm'
      - run: pnpm install
      - run: pnpm typecheck

  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: pnpm/action-setup@v2
        with:
          version: 8.12.0
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'pnpm'
      - run: pnpm install
      - run: pnpm test:unit

  e2e:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: pnpm/action-setup@v2
        with:
          version: 8.12.0
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'pnpm'
      - run: pnpm install
      - run: npx playwright install --with-deps
      - run: pnpm test:e2e

  deploy:
    needs: [lint, typecheck, test]
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v4
      - uses: pnpm/action-setup@v2
        with:
          version: 8.12.0
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'pnpm'
      - run: pnpm install
      - run: pnpm build
      - uses: amondnet/vercel-action@v25
        with:
          vercel-token: ${{ secrets.VERCEL_TOKEN }}
          vercel-org-id: ${{ secrets.VERCEL_ORG_ID }}
          vercel-project-id: ${{ secrets.VERCEL_PROJECT_ID }}
          vercel-args: '--prod'
```

### 11.2 デプロイフロー

**ブランチ戦略:**

```
main (本番)
  ← develop (開発)
      ← feature/* (機能開発)
```

**デプロイルール:**
- `feature/*` → develop: PR作成 → レビュー → マージ
- `develop` → main: PR作成 → レビュー → マージ → 自動デプロイ

### 11.3 Vercel設定

**vercel.json:**

```json
{
  "buildCommand": "pnpm build",
  "devCommand": "pnpm dev",
  "installCommand": "pnpm install",
  "framework": "nextjs",
  "regions": ["hnd1"],
  "env": {
    "NODE_ENV": "production"
  }
}
```

---

## 12. セキュリティ設計

### 12.1 通信セキュリティ

- **HTTPS強制**: Vercelのデフォルト設定で有効
- **セキュアヘッダー**: next.config.jsで設定

```javascript
// next.config.js
module.exports = {
  async headers() {
    return [
      {
        source: '/(.*)',
        headers: [
          {
            key: 'X-Content-Type-Options',
            value: 'nosniff'
          },
          {
            key: 'X-Frame-Options',
            value: 'DENY'
          },
          {
            key: 'X-XSS-Protection',
            value: '1; mode=block'
          }
        ]
      }
    ];
  }
};
```

### 12.2 入力バリデーション

- **クライアント側**: Zodスキーマ
- **サーバー側**: Zodスキーマ（二重チェック）
- **サニタイゼーション**: DOMPurify（Phase 4）

### 12.3 環境変数管理

**ローカル開発:**
- `.env.local` （gitignoreに追加）

**本番環境:**
- Vercelダッシュボードで設定

**必要な環境変数:**

```bash
# データソースURL（Phase 4）
DATABASE_URL=DUMMY_postgresql://user:pass@host:5432/db
SUPABASE_URL=DUMMY_https://xxx.supabase.co
SUPABASE_ANON_KEY=DUMMY_eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9

# AI API（Phase 4）
AI_API_URL=DUMMY_https://api.example.com
AI_API_KEY=DUMMY_sk-xxxxxxxxxxxxxxxx

# その他
NEXT_PUBLIC_APP_URL=https://numbers-ai.vercel.app
```

---

## 13. Definition of Done

各タスクが完了したと見なされる基準を定義する。

### 13.1 機能実装のDoD

✅ **必須条件:**
1. 要件定義書の仕様を満たしている
2. TypeScriptのコンパイルエラーがない
3. ESLintエラーがない（警告は許容）
4. ユニットテストが作成され、全てパスしている
5. コードレビューが完了し、承認されている
6. 主要な関数・コンポーネントにJSDocコメントがある
7. 該当する型定義ファイルが更新されている

✅ **推奨条件:**
8. E2Eテストが作成されている（主要機能）
9. パフォーマンス要件を満たしている
10. アクセシビリティチェックをパスしている

### 13.2 バグ修正のDoD

✅ **必須条件:**
1. バグが再現しないことを確認
2. 回帰テストが追加されている
3. 関連する既存テストが全てパス
4. バグの原因と修正内容がPRに記載されている

### 13.3 リリースのDoD

✅ **必須条件:**
1. 全てのCI/CDパイプラインがパス
2. ステージング環境でQAテスト完了
3. パフォーマンステスト完了
4. セキュリティスキャン完了（Phase 4）
5. ドキュメントが最新版に更新されている
6. CHANGELOGが更新されている

---

## 変更履歴

| バージョン | 日付 | 変更者 | 変更内容 |
|-----------|------|--------|----------|
| 1.0 | 2025-11-02 | 技術リード | 初版作成 |

---

**承認**
- 技術リード: ________________ 日付: ________________
- プロジェクトオーナー: ________________ 日付: ________________

---

**ドキュメント終了**

