# データ・API設計書 v1.1

**Document Management Information**
- Document ID: DOC-03
- Version: 1.1
- Created: 2025-11-02
- Last Updated: 2025-01-XX
- Status: Confirmed
- Approver: Technical Lead

---

## 📋 目次

1. [ドキュメント目的と適用範囲](#1-ドキュメント目的と適用範囲)
2. [データモデル](#2-データモデル)
3. [API仕様](#3-api仕様)

---

## 1. ドキュメント目的と適用範囲

### 1.1 目的
本ドキュメントは、ナンバーズAI予測システムの**データモデル**と**API仕様**を定義する。データの構造とインターフェースを明確にすることで、フロントエンドとバックエンドの統合を円滑に進める。

### 1.2 対象読者
- バックエンドエンジニア
- フロントエンドエンジニア
- データベース設計者
- API実装者

### 1.3 関連ドキュメント
- [01-business-requirements.md](./01-business-requirements.md): ビジネス要件
- [02-system-architecture.md](./02-system-architecture.md): システム設計
- [04-algorithm-ai.md](./04-algorithm-ai.md): アルゴリズム・AI

---

## 2. データモデル

### 2.1 CSVデータ構造（MVP版）

**⚠️ 重要: データ基準点**

**すべてのデータモデルとAIモデルの基準点は以下の通りです：**
- **基準回号**: 第6758回
- **基準日**: 2025年6月30日
- **データ収集方法**: 第6758回を基準にさかのぼってデータを収集・管理する
- **適用範囲**: すべてのAIモデル（N3/N4、ボックス/ストレート、軸数字/組み合わせ）の学習データは上記基準点に準じる

この基準点は、データの一貫性と再現性を保証するために必須です。新しいデータを追加する際や、モデルを再学習する際は、必ずこの基準点を確認してください。

---

#### past_results.csv

過去の当選番号とリハーサル数字を格納。

**カラム定義:**

```
round_number    : 回号（4桁整数）
draw_date       : 抽選日（YYYY-MM-DD、NULL可）
weekday         : 曜日（0-4の整数、NULL可）
                 0: 月曜日、1: 火曜日、2: 水曜日、3: 木曜日、4: 金曜日
n3_winning      : N3当選番号（3桁文字列、例: "123"）
n4_winning      : N4当選番号（4桁文字列、例: "1234"）
n3_rehearsal    : N3リハーサル（3桁文字列、NULL可）
n4_rehearsal    : N4リハーサル（4桁文字列、NULL可）
```

**サンプルデータ:**

```csv
round_number,draw_date,weekday,n3_winning,n4_winning,n3_rehearsal,n4_rehearsal
6701,2025-01-10,4,147,3782,149,3782
6700,2025-01-09,3,523,1056,NULL,NULL
6699,2025-01-08,2,891,7324,894,7329
```

**制約:**
- round_number: ユニークキー
- draw_date: 日付形式（NULL可）
- weekday: 0-4の整数（NULL可、draw_dateがNULLの場合はNULL）
- winning/rehearsal: 数字文字列（0埋めあり）

**日付取得方法:**
- **1-4800回**: みずほ銀行のCSVファイルから日付を取得（元号表記から西暦に変換）
- **4801回以降**: 
  - **日付**: みずほ銀行のCSVファイルから取得（日付情報が正確に含まれているため）
  - **当選番号・リハーサル数字**: hpfree.comから取得（リハーサル数字が含まれているため）
  - **フォールバック**: みずほ銀行から日付が取得できない場合のみ、回号差から平日のみをカウントして計算
- **定期更新時**: まずみずほ銀行のCSVファイルから日付を取得を試行し、取得できない場合のみ既存データの最新回号と日付を基準に計算

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

**作成方法について:**
`keisen_master.json`の具体的な作成方法と予測出目ルールについては、[08-keisen-master-creation.md](./08-keisen-master-creation.md)を参照してください。

---

### 2.2 データベーススキーマ（Phase 2以降: Supabase PostgreSQL）

**なぜPhase 2でデータベースを導入するのか:**
詳細は [06-implementation-plan.md](./06-implementation-plan.md) の「Phase 2実装計画」を参照

#### テーブル: past_results

```sql
CREATE TABLE past_results (
  id                 SERIAL PRIMARY KEY,
  round_number       INTEGER NOT NULL UNIQUE,
  draw_date          DATE NOT NULL,
  weekday            INTEGER CHECK (weekday BETWEEN 0 AND 4),  -- 0:月, 1:火, 2:水, 3:木, 4:金
  n3_winning         CHAR(3) NOT NULL,
  n4_winning         CHAR(4) NOT NULL,
  n3_rehearsal       CHAR(3),
  n4_rehearsal       CHAR(4),
  created_at         TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at         TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_round_number ON past_results(round_number);
CREATE INDEX idx_draw_date ON past_results(draw_date);
CREATE INDEX idx_weekday ON past_results(weekday);
```

### 3.5.1 FastAPI と Next.js API の連携

```
[フロント predictor.ts]
        │
        ▼
  POST /api/predict ←─ UI 側は `/api/predict/axis` を直接呼ばず統一
        │
        ▼
[Next.js API Route] ← バリデーション・ログ・エラーを集中
        │
        ▼
[fastapi-bridge.ts] ← `/api/predict/axis` と `/api/predict/combination` を FastAPI へ転送
        │
        ▼
[FastAPI Predict API] ← LightGBM モデル＋`libgomp.so.1` を使って推論 → JSON を返す
```

- `rg /api/predict/axis` の結果どおり、 `/api/predict/axis` を直接叩いているのは `fastapi-bridge.ts` のみで、フロント/Next.js はすべて `/api/predict` に統一されている。
- Next.js 側が FastAPI のエラーを 500 でラップするため、405 やタイムアウトが発生しづらい。
- `pnpm dev` + 必要に応じて `uvicorn api.main:app` を併用すれば、本番と同じログ/レスポンスの順序を追跡できる。

### 3.5.2 Next.js API vs FastAPI direct の比較

| 観点 | Next.js API Route（`/api/predict`） | FastAPI direct（`/api/predict/axis` 等） |
|------|--------------------------------------|-------------------------------------------|
| デプロイサイズ | Node.js のみなのでVercel 関数サイズ制限に収まりやすい | LightGBM + `libgomp.so.1` + Pickle でサイズが膨張、Vercel で拒否の可能性あり |
| モデル改修 | `fastapi-bridge.ts` で Python 資産を併用しつつ Node 実装へ段階的移行可能 | Python 実装をそのまま使えるが Vercel デプロイの安定性が下がる |
| ローカルデバッグ | `pnpm dev` だけで UI→API→FastAPI の流れを追え、ログも統合できる | `uvicorn api.main:app` と Next.js を併走させる必要がありログ分散しやすい |
| フロント連携 | `predictor.ts` が `/api/predict` のみを呼び、405 を回避 | `/axis` を直接叩くためメソッド不一致の監視が必要 |
| 運用安定性 | Next.js ルートだけ完結で運用負荷が低い | Python 関数にデプロイすると依存・Cold Start・ログ管理が増える |

→ 現行は、Next.js API Route を正規ルートとして FastAPI に必要な部分だけ委譲するハイブリッド構成が最適。

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

### 2.3 TypeScript型定義

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

## 3. API仕様

### 3.1 エンドポイント一覧

| エンドポイント | メソッド | 説明 | 認証 |
|---------------|---------|------|------|
| /api/predict | POST | 予測実行 | 不要（MVP） |
| /api/charts | POST | 予測表生成のみ | 不要 |
| /api/health | GET | ヘルスチェック | 不要 |

### 3.2 POST /api/predict

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

**パフォーマンス要件:**
- レスポンスタイム: 5秒以内（95パーセンタイル）
- タイムアウト: 10秒

---

### 3.3 POST /api/charts

**概要:** 予測表の生成のみを行う（デバッグ用）。

**リクエスト:**

```json
{
  "roundNumber": 6701,
  "pattern": "A",
  "target": "n3"
}
```

**リクエストスキーマ（Zod):**

```typescript
export const ChartRequestSchema = z.object({
  roundNumber: z.number().int().min(1).max(9999),
  pattern: z.enum(['A', 'B']),
  target: z.enum(['n3', 'n4'])
});
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

**パフォーマンス要件:**
- レスポンスタイム: 100ms以内

---

### 3.4 GET /api/health

**概要:** APIの稼働状態を確認。

**リクエスト:**

```
GET /api/health
```

**レスポンス:**

```json
{
  "status": "ok",
  "timestamp": "2025-11-02T12:34:56.789Z",
  "version": "1.0.0",
  "models": {
    "n3_box_axis": "loaded",
    "n3_box_comb": "loaded",
    "n3_straight_axis": "loaded",
    "n3_straight_comb": "loaded",
    "n4_box_axis": "loaded",
    "n4_box_comb": "loaded",
    "n4_straight_axis": "loaded",
    "n4_straight_comb": "loaded"
  },
  "database": "connected"  // Phase 2以降
}
```

**ステータス:**
- `ok`: 正常稼働
- `degraded`: 一部機能が利用不可
- `down`: サービス停止中

---

### 3.5 API実装例（Next.js API Routes）

#### /api/predict/route.ts

```typescript
// src/app/api/predict/route.ts

import { NextRequest, NextResponse } from 'next/server';
import { PredictRequestSchema } from '@/types/api';
import { generateChart } from '@/lib/chart-generator';
import { extractFeatures } from '@/lib/feature-extraction';
import { predictAxis, predictCombinations } from '@/lib/ai-predictor';

export async function POST(request: NextRequest) {
  try {
    // リクエストボディの取得とバリデーション
    const body = await request.json();
    const validatedData = PredictRequestSchema.parse(body);
    
    const { roundNumber, n3Rehearsal, n4Rehearsal } = validatedData;
    
    // 予測表生成（N3/N4、パターンA/B）
    const charts = {
      n3A: generateChart(roundNumber, 'A', 'n3'),
      n3B: generateChart(roundNumber, 'B', 'n3'),
      n4A: generateChart(roundNumber, 'A', 'n4'),
      n4B: generateChart(roundNumber, 'B', 'n4')
    };
    
    // 特徴量計算 + AI予測
    const n3BoxAxis = await predictAxis(charts.n3A, n3Rehearsal, 'box');
    const n3BoxComb = await predictCombinations(charts.n3A, n3Rehearsal, n3BoxAxis[0].digit, 'box');
    // ... 他の組み合わせも同様に計算
    
    // レスポンス構築
    const result: PredictionResult = {
      roundNumber,
      n3: {
        box: {
          axisCandidates: n3BoxAxis,
          numberCandidates: n3BoxComb
        },
        straight: {
          axisCandidates: n3StraightAxis,
          numberCandidates: n3StraightComb
        }
      },
      n4: { /* ... */ },
      generatedAt: new Date().toISOString()
    };
    
    return NextResponse.json({ success: true, data: result });
    
  } catch (error) {
    if (error instanceof z.ZodError) {
      return NextResponse.json(
        {
          success: false,
          error: {
            code: 'VALIDATION_ERROR',
            message: 'Invalid input data',
            details: error.errors
          }
        },
        { status: 400 }
      );
    }
    
    console.error('Prediction error:', error);
    return NextResponse.json(
      {
        success: false,
        error: {
          code: 'INTERNAL_ERROR',
          message: 'An unexpected error occurred'
        }
      },
      { status: 500 }
    );
  }
}
```

---

### 3.5.3 Next.js API 単独運用の裏付け

- Vercel 2025-11-25 08:39:07 のログでは `fastapi-bridge.ts` が `http://localhost:8000/api/predict/axis` を呼び出そうとして `ECONNREFUSED` になったため、本番環境で FastAPI に依存する構成は実際に動作せずビルドも失敗した。このため、`/api/predict` のみを実装した Next.js API が本番で動いている唯一の構成であることが確認できた。
- したがって、FastAPI は資料・実験用途として `api/` に残しつつ、本番・顧客向けデプロイでは Next.js API に一本化する方が「実際にデプロイして動く」ことが証明されている選択肢である。
- この節のロードマップ（Docs 01_design/02-system-architecture.md 3.2.4）を参照しながら、Step2 以降で Node 側実装へ移行することを優先する。

### 3.6 CORS設定

**MVP版（Vercel）:**
デフォルトでCORSは有効。特別な設定は不要。

**Phase 4（GCP Cloud Run）:**
FastAPIでCORS設定を明示的に行う。

```python
# ai-engine/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://numbers-ai.vercel.app",  # 本番環境
        "http://localhost:3000"            # 開発環境
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

### 3.7 レート制限

**MVP版:**
- レート制限なし（単一ユーザー想定）

**Phase 4:**
- 匿名ユーザー: 10リクエスト/分
- 認証ユーザー: 60リクエスト/分

**実装方法:**
Vercel Edge Middlewareまたはupstash/ratelimitを使用。

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
- [02-system-architecture.md](./02-system-architecture.md): システム設計
- [04-algorithm-ai.md](./04-algorithm-ai.md): アルゴリズム・AI
- [05-frontend-design.md](./05-frontend-design.md): フロントエンド設計
- [06-implementation-plan.md](./06-implementation-plan.md): 実装計画
- [07-operations-quality.md](./07-operations-quality.md): 運用・品質

---

**ドキュメント終了**

