# CUBE生成システム設計書

**Document Management Information**
- Document ID: DOC-10
- Version: 1.2
- Created: 2025-01-XX
- Last Updated: 2025-01-XX
- Status: Confirmed

---

## 📋 目次

1. [ドキュメント目的と適用範囲](#1-ドキュメント目的と適用範囲)
2. [システムアーキテクチャ](#2-システムアーキテクチャ)
   - [2.1 全体構成（ハイブリッド構成）](#21-全体構成ハイブリッド構成)
   - [2.2 特徴](#22-特徴)
   - [2.3 Python版とTypeScript版の使い分け](#23-python版とtypescript版の使い分け)
3. [CUBE生成フロー](#3-cube生成フロー)
4. [データ更新の自動化](#4-データ更新の自動化)
5. [ディレクトリ構造](#5-ディレクトリ構造)
6. [実装の詳細](#6-実装の詳細)
7. [実装状況](#7-実装状況)
8. [関連ドキュメント](#8-関連ドキュメント)

---

## 1. ドキュメント目的と適用範囲

### 1.1 目的
本ドキュメントは、CUBE生成システムの設計を定義する。CUBE生成はユーザーが回号を入力することで手動トリガーで実行され、Next.jsアプリケーション内に完全に内包される。

### 1.2 対象読者
- フロントエンドエンジニア
- フルスタックエンジニア
- システムアーキテクト

### 1.3 関連ドキュメント
- [CUBE生成ルール.md](./CUBE生成ルール.md): CUBE生成アルゴリズムの詳細仕様
- [02-system-architecture.md](./02-system-architecture.md): システムアーキテクチャ全体
- [07-operations-quality.md](./07-operations-quality.md): 運用・品質管理

---

## 2. システムアーキテクチャ

### 2.1 全体構成（ハイブリッド構成）

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
│  │  ┌─────────────────────────────────┐   │   │
│  │  │  CUBE表示ページ (/cube)           │   │   │
│  │  │  予測アプリ (/predict)            │   │   │
│  │  └───────────┬───────────────────────┘   │   │
│  │              │                             │   │
│  │              ▼                             │   │
│  │  ┌─────────────────────────────────┐   │   │
│  │  │  API Routes                      │   │   │
│  │  │  /api/cube/[roundNumber]         │   │   │
│  │  │  /api/predict                    │   │   │
│  │  └───────┬───────────────┬─────────┘   │   │
│  │          │               │               │   │
│  │          ▼               ▼               │   │
│  │  ┌──────────────┐  ┌──────────────┐     │   │
│  │  │ CUBE生成     │  │ AI推論       │     │   │
│  │  │ (TypeScript) │  │ (FastAPI)    │     │   │
│  │  │              │  │              │     │   │
│  │  │ cube-       │  │ → FastAPI    │     │   │
│  │  │ generator/  │  │   サーバー    │     │   │
│  │  └──────┬──────┘  └──────┬───────┘     │   │
│  │         │                 │             │   │
│  │         ▼                 │             │   │
│  │  ┌──────────────┐         │             │   │
│  │  │ data-loader/ │         │             │   │
│  │  └──────────────┘         │             │   │
│  └───────────────────────────┼─────────────┘   │
└──────────────────────────────┼─────────────────┘
                                │
                                ▼
                ┌───────────────────────────────┐
                │   FastAPI Server              │
                │   (GCP Cloud Run等)           │
                │  ┌─────────────────────────┐  │
                │  │ AI推論エンジン           │  │
                │  │ - XGBoostモデル         │  │
                │  │ - 特徴量抽出            │  │
                │  │ - 推論実行             │  │
                │  └─────────────────────────┘  │
                └───────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────┐
│          Data Layer (CSV Files)                 │
│  - past_results.csv                             │
│  - keisen_master.json                            │
│  - keisen_master_new.json                       │
│  - models/*.pkl (XGBoostモデル)                │
└─────────────────────────────────────────────────┘
```

### 2.2 特徴

- **Next.js内包型**: CUBE生成はFastAPIサーバーへの依存なし
- **手動トリガー**: ユーザーが回号を入力することでCUBEを生成
- **TypeScript実装**: PythonコードをTypeScriptに移植
- **Vercelで完結**: CUBE生成はデプロイ不要、Vercelのサーバーレス関数で動作
- **ハイブリッド構成**: CUBE生成はTypeScript、AI推論はFastAPI（Python機械学習ライブラリが必要なため）

### 2.3 Python版とTypeScript版の使い分け

本システムでは、CUBE生成ロジックが**Python版**と**TypeScript版**の2つで実装されている。それぞれ異なる用途で使用される。

#### TypeScript版（本番Webアプリ用途）

**実装場所**: `src/lib/cube-generator/`

**用途**:
- **本番Webアプリ**: `/cube`ページでのCUBE生成
- **予測アプリ**: `/predict`ページでの予測表生成
- **Next.js API Route**: `/api/cube/[roundNumber]`エンドポイント

**メリット**:
- Vercelでそのまま動作（デプロイ不要）
- FastAPIサーバーへの依存なし
- フロントエンドとバックエンドを統合
- コードの重複を排除（予測アプリとCUBE表示ページで共通使用）

#### Python版（開発・分析用途）

**実装場所**: `core/chart_generator.py`, `scripts/generate_extreme_cube.py`

**用途**:
- **可視化・デバッグツール**: CUBE生成プロセスの可視化
  - `scripts/tools/visualization/visualize_normal_cube_steps.py`
  - `scripts/tools/visualization/visualize_extreme_cube_steps.py`
  - `scripts/tools/visualization/export_cube_to_html.py`
- **バッチ処理**: 大量のCUBE生成
  - `scripts/production/generate_extreme_cube.py`
- **データ分析**: 特徴量エンジニアリング、モデル訓練
  - `notebooks/run_03_feature_engineering_*.py`
  - `scripts/tools/training/test_new_features.py`
  - `scripts/tools/validation/predict_with_winning.py`
- **ノートブック**: Jupyterでの対話的分析

**メリット**:
- ターミナルから直接実行可能
- データ分析ライブラリ（Pandas, NumPy）との統合が容易
- ステップごとの可視化が容易
- TypeScript版との相互検証が可能

#### FastAPIサーバーのCUBE生成エンドポイント（非推奨）

**実装場所**: `api/main.py` の `/api/cube/{round_number}` エンドポイント

**状態**: **非推奨**（TypeScript版に移行済み）

**理由**:
- TypeScript版（`src/app/api/cube/[roundNumber]/route.ts`）に完全移行済み
- FastAPIサーバーのデプロイが不要になった
- 将来的に削除予定

**注意**: FastAPIサーバー自体は**AI推論エンドポイント**（`/api/predict`）のために必要。CUBE生成エンドポイントのみ非推奨。

---

## 3. CUBE生成フロー

### 3.1 ユーザー操作フロー

```
1. ユーザーがCUBE表示ページ（/cube）にアクセス
   ↓
2. 回号を入力（例: 6851）
   ↓
3. 「生成」ボタンをクリック
   ↓
4. Next.js API Route (/api/cube/6851) が呼び出される
   ↓
5. CUBE生成ロジックが実行される
   - 前回・前々回の当選番号を取得
   - 罫線マスターデータを読み込み
   - 通常CUBE 8個 + 極CUBE 2個 = 10個を生成
   ↓
6. 生成されたCUBEがJSON形式で返される
   ↓
7. フロントエンドでCUBEを表示
   ↓
8. ユーザーが各CUBEの「コピー」ボタンをクリック
   ↓
9. TSV形式でクリップボードにコピー
   ↓
10. Excelに貼り付け可能
```

### 3.2 CUBE生成の種類

#### 通常CUBE（8個）
- **現罫線**: N3/N4 × A1/A2/B1/B2 = 4個
- **新罫線**: N3/N4 × A1/A2/B1/B2 = 4個

#### 極CUBE（2個）
- **現罫線**: N3のみ = 1個
- **新罫線**: N3のみ = 1個

**合計**: 10個のCUBE

---

## 4. データ更新の自動化

### 4.1 自動更新されるデータ

- **当選番号データ** (`past_results.csv`)
  - 既存の`scripts/production/auto_update_past_results.py`で自動更新
  - cronジョブ: 平日15:00に自動実行
  - 最新の1回分のみ取得・更新

- **リハーサル数字** (`past_results.csv`の`n3_rehearsal`, `n4_rehearsal`カラム)
  - 当選番号データと同時に取得・更新される
  - 既存の`fetch_past_results.py`で取得可能

### 4.2 データ更新フロー

```
1. cronジョブ実行（平日15:00）
   ↓
2. 抽選日判定（平日かつ年末年始でない）
   ↓
3. 最新回号を取得
   ↓
4. Webスクレイピング実行（fetch_past_results.py --merge）
   ↓
5. 失敗時 → 検索APIフォールバック
   ↓
6. CSV更新（最新の1回分を追加/更新）
   - 当選番号（n3_winning, n4_winning）
   - リハーサル数字（n3_rehearsal, n4_rehearsal）
   ↓
7. ログ記録
```

### 4.3 CUBE生成との関係

- **CUBE生成は手動トリガー**: ユーザーが回号を入力することで実行される
- **データは自動更新**: 毎日最新データが自動取得・更新されるため、ユーザーが当日の回号を入力した際に、前日分の当選番号とリハーサル数字が利用可能

---

## 5. ディレクトリ構造

### 5.1 ソースコード

```
src/lib/
├── cube-generator/                   # CUBE生成ロジック（統一）
│   ├── index.ts                      # エクスポート
│   ├── chart-generator.ts            # 通常CUBE生成
│   ├── extreme-cube-generator.ts     # 極CUBE生成
│   ├── keisen-master-loader.ts      # 罫線マスターデータ読み込み（現/新両対応）
│   └── types.ts                      # 型定義
│
├── predictor/                         # 予測アプリ用（cube-generatorを使用）
│   ├── predictor.ts                  # AI推論（FastAPIにリクエスト）
│   └── ...
│
└── data-loader/                      # データ読み込みユーティリティ（共通）
    ├── index.ts
    ├── past-results.ts
    ├── keisen-master.ts
    └── types.ts
```

### 5.2 APIルート

```
src/app/api/
├── cube/
│   └── [roundNumber]/
│       └── route.ts                  # CUBE生成API（cube-generatorを使用）
│
└── predict/
    └── route.ts                       # AI推論API（FastAPIにプロキシ）
```

### 5.3 ページ

```
src/app/
├── cube/
│   └── page.tsx                      # CUBE表示ページ
│
└── predict/
    └── ...                           # 予測アプリページ
```

### 5.4 アーキテクチャの分離

| 機能 | 実装 | 使用箇所 | デプロイ | 用途 |
|------|------|---------|---------|------|
| **CUBE生成（本番）** | TypeScript (`cube-generator/`) | `src/app/cube/`, `src/app/api/cube/`, `src/lib/predictor/` | Vercel（Next.js API Routes） | 本番Webアプリ |
| **CUBE生成（開発）** | Python (`core/chart_generator.py`) | 可視化ツール、バッチ処理、ノートブック | ローカル実行 | 開発・分析・デバッグ |
| **AI推論** | Python (FastAPI) | `src/app/api/predict/` → `api/main.py` | FastAPIサーバー（GCP Cloud Run等） | 本番Webアプリ |

**設計方針**: 
- **CUBE生成は統一**: 予測アプリとCUBE表示ページの両方で同じ`cube-generator/`を使用（コードの重複を排除）
- **Python版は開発用途**: 可視化、バッチ処理、データ分析に使用
- **AI推論はFastAPI**: Python機械学習ライブラリ（XGBoost, NumPy, Pandas）が必要なため、FastAPIのまま維持

---

## 6. 実装の詳細

### 6.1 CUBE生成ロジック

詳細は [CUBE生成ルール.md](./CUBE生成ルール.md) を参照。

### 6.2 データ読み込み

- `past_results.csv`: 過去当選番号データ（前回・前々回の当選番号を取得）
- `keisen_master.json`: 現罫線マスターデータ（1340-6391回のデータから生成）
- `keisen_master_new.json`: 新罫線マスターデータ（4801-6850回のデータから生成）

### 6.3 エラーハンドリング

- 回号が無効な場合: 400エラーを返す
- 前回・前々回の当選番号が見つからない場合: 404エラーを返す
- CUBE生成に失敗した場合: 500エラーを返す

---

## 7. 実装状況

### 7.1 Phase 1: TypeScript実装の完成 ✅

- **完了日**: 2025-01-XX
- **内容**:
  - `src/lib/cube-generator/`ディレクトリを作成し、統一されたCUBE生成機能を実装
  - `chart-generator.ts`: 通常CUBE生成ロジック（現罫線/新罫線対応）
  - `extreme-cube.ts`: 極CUBE生成ロジック（現罫線/新罫線対応）
  - `keisen-master-loader.ts`: 現罫線/新罫線の両方を読み込む関数を実装
  - `types.ts`: 型定義
  - `index.ts`: エクスポート
  - `src/app/api/cube/[roundNumber]/route.ts`: FastAPI依存を削除し、`cube-generator/`を使用するように更新
  - `src/lib/predictor/chart-generator.ts`: `cube-generator/`を使用するように更新
  - 予測アプリとCUBE表示ページの両方で同じ`cube-generator/`を使用することで、コードの重複を排除

### 7.2 Phase 2: データ自動更新の確認・拡張 ✅

- **完了日**: 2025-01-XX
- **内容**:
  - `scripts/production/auto_update_past_results.py`の動作確認完了
  - `scripts/production/fetch_past_results.py`でリハーサル数字の取得機能を確認
  - リハーサル数字（`n3_rehearsal`, `n4_rehearsal`）の取得・更新は既に実装済み
  - `parse_n3_table`関数: N3のリハーサル数字を取得（セル1-3から）
  - `parse_n4_table`関数: N4のリハーサル数字を取得（セル1-4から）
  - `combine_data`関数: リハーサル数字を含めてデータを結合
  - `save_to_csv`関数: CSVファイルにリハーサル数字を含めて保存
  - 4801回以降のデータ: hpfree.comからリハーサル数字も取得
  - 4800回以前のデータ: みずほ銀行から取得（リハーサル数字は空文字列）

### 7.3 Phase 3: ドキュメント整備 ✅

- **完了日**: 2025-01-XX
- **内容**:
  - 設計ドキュメントの更新（本ドキュメント）
  - TODOドキュメントの更新
  - READMEやセットアップガイドの更新

### 7.4 Phase 4: CUBE生成機能の改善 ✅

- **完了日**: 2025-01-XX
- **内容**:
  - 8行を超える場合の行数調整を実装（ステップ8: 9行目以降を削除して8行に）
  - 0配置パターン（A2/B2）で8列×8行の場合の最終調整を実装（ステップ9: 5列5行目→0、5列4行目→5）
  - 余りマスルール（裏数字適用後）を削除
  - 極CUBEのテーブルサイズ調整（スクロール不要に）
  - ビルドエラーの修正（`grid`と`rows`を`const`から`let`に変更、`tempList`のundefined対応）

---

## 8. 関連ドキュメント

- [CUBE生成ルール.md](./CUBE生成ルール.md): CUBE生成アルゴリズムの詳細仕様
- [02-system-architecture.md](./02-system-architecture.md): システムアーキテクチャ全体
- [07-operations-quality.md](./07-operations-quality.md): 運用・品質管理
- [AUTO_UPDATE_SETUP.md](../../AUTO_UPDATE_SETUP.md): データ自動更新システムのセットアップガイド
- [06-03_CUBE自動生成システム実装.md](../../02_todo/06_cube_tools/06-03_CUBE自動生成システム実装.md): CUBE生成システム実装の詳細

