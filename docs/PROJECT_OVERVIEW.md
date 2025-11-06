# ナンバーズAI予測システム - プロジェクト概要

**最終更新日**: 2025-01-XX  
**プロジェクト名**: numbers-ai  
**バージョン**: MVP (Phase 1)

---

## 📌 プロジェクトの目的

独自の「中国罫線」理論とAI技術を融合した、ナンバーズ3/4の当選番号予測Webアプリケーション。

### コアコンセプト
- **独自理論のデジタル化**: 紙媒体の罫線理論を完全にデジタル化
- **AI多角分析**: XGBoostを用いた6つの統合モデルで多角的に予測
- **3ステップで完結**: 回号入力 → リハーサル入力 → 予測結果表示
- **モバイルファースト**: スマートフォンでの使用を前提としたUI/UX
- **高速レスポンス**: 5秒以内にAI予測結果を表示

---

## 🏗️ 技術スタック

### フロントエンド
- **Next.js 15.5.4+** (App Router)
- **React 19.1.0+**
- **TypeScript 5.3+**
- **Tailwind CSS 4.0+**
- **Zustand 5.0.8+** (状態管理)
- **Framer Motion** (アニメーション)
- **Radix UI** (UIコンポーネント)

### バックエンド
- **Next.js API Routes**: サーバーレス関数（MVP版）
- **FastAPI**: AI推論エンジン（Python）
- **TypeScript**: ビジネスロジック

### AI/ML
- **XGBoost 2.0+**: 機械学習アルゴリズム
- **scikit-learn 1.3+**: 前処理・評価
- **Python 3.10+**: AIモデル開発
- **Jupyter Notebook**: データ分析・モデル開発

### インフラ・ツール
- **Vercel**: ホスティング + CI/CD
- **GitHub**: ソースコード管理
- **CSV**: データストレージ（MVP版）
- **pnpm**: パッケージマネージャー

---

## 📁 プロジェクト構造

```
numbers-ai/
├── src/                          # ソースコード
│   ├── app/                      # Next.js App Router
│   │   ├── api/                  # API Routes
│   │   │   ├── predict/          # 予測API
│   │   │   ├── test-chart/       # テストAPI
│   │   │   └── test-data-loader/ # データローダーテスト
│   │   ├── predict/              # 予測画面
│   │   │   ├── loading/          # ローディング画面
│   │   │   └── axis/             # 軸数字表示画面
│   │   ├── history/              # 履歴画面
│   │   ├── statistics/           # 統計画面
│   │   └── settings/             # 設定画面
│   ├── components/               # Reactコンポーネント
│   │   ├── features/             # 機能コンポーネント
│   │   ├── layouts/              # レイアウトコンポーネント
│   │   ├── shared/               # 共有コンポーネント
│   │   └── ui/                   # UIコンポーネント（Radix UI）
│   ├── lib/                      # ビジネスロジック
│   │   ├── chart-generator/      # 予測表生成
│   │   ├── data-loader/          # データ読み込み
│   │   ├── predictor/            # 予測処理
│   │   ├── store.ts              # Zustandストア
│   │   └── utils.ts              # ユーティリティ
│   └── types/                    # TypeScript型定義
│       ├── chart.ts              # 予測表型
│       ├── prediction.ts         # 予測結果型
│       └── statistics.ts        # 統計型
├── api/                          # FastAPIサーバー
│   ├── main.py                   # FastAPIアプリケーション
│   ├── run.py                    # サーバー起動スクリプト
│   └── requirements.txt          # Python依存関係
├── data/                         # データファイル
│   ├── past_results.csv          # 過去当選番号データ
│   ├── keisen_master.json        # 罫線マスターデータ
│   └── models/                   # 学習済みモデル（.pkl）
├── notebooks/                    # Jupyter Notebooks
│   ├── 01_data_preparation.ipynb # データ前処理
│   ├── 02_chart_generation.ipynb # 予測表生成
│   ├── 03_feature_engineering.ipynb # 特徴量エンジニアリング
│   ├── 04_model_training.ipynb   # モデル学習
│   ├── chart_generator.py        # 予測表生成モジュール
│   ├── feature_extractor.py      # 特徴量抽出モジュール
│   ├── model_loader.py           # モデル読み込みユーティリティ
│   └── predict_cli.py            # CLI予測ツール
├── docs/                         # ドキュメント
│   ├── design/                   # 設計ドキュメント
│   │   ├── 01-business-requirements.md
│   │   ├── 02-system-architecture.md
│   │   ├── 03-data-api-design.md
│   │   ├── 04-algorithm-ai.md
│   │   ├── 05-frontend-design.md
│   │   ├── 06-implementation-plan.md
│   │   └── 07-operations-quality.md
│   ├── todo/                     # タスク管理
│   │   ├── 01_mvp-foundation/
│   │   ├── 02_data-infrastructure/
│   │   └── 進捗状況サマリー.md
│   └── SETUP.md                  # セットアップガイド
├── scripts/                      # スクリプト
│   ├── test-api.sh               # API統合テスト
│   ├── test-4-patterns.ts        # 4パターンテスト
│   └── start-nextjs.sh           # Next.js起動スクリプト
└── .serena/                      # Serena設定
    └── project.yml               # プロジェクト設定
```

---

## 🎯 主要機能

### MVP版（Phase 1）機能

#### 1. 予測表自動生成
- **4パターン対応**: A1/A2/B1/B2の4パターンで予測表を生成
- **中国罫線理論**: 独自の罫線理論に基づく予測表生成
- **メイン行組み立て**: 予測出目からメイン行を組み立て
- **裏数字ルール**: 縦パス/横パスによる裏数字適用
- **余りマスルール**: メイン行配置後の余りマス処理

#### 2. AI軸数字予測
- **6つの統合モデル**: 軸数字予測（N3/N4）と組み合わせ予測（N3/N4、ボックス/ストレート）
- **スコア順ランキング**: 当選確率が高い軸数字をスコア順に提示
- **最良パターン特定**: 4パターンから最良パターンを自動選択

#### 3. AI組み合わせ予測
- **軸数字ベース予測**: 軸数字を含む当選番号候補を生成
- **ボックス/ストレート対応**: 2つの予測タイプに対応
- **N3/N4対応**: ナンバーズ3と4の両方に対応

#### 4. 手動指定軸機能
- **ユーザー指定軸**: 任意の軸数字（0〜9）を指定して予測
- **リアルタイム予測**: 軸数字選択時に即座に予測結果を表示

#### 5. UI/UX機能
- **モバイルファースト**: スマートフォンでの使用を前提としたUI
- **ローディング画面**: 予測実行中のプログレス表示
- **エラーハンドリング**: ユーザーフレンドリーなエラーメッセージ
- **タブ切り替え**: N3/N4、ボックス/ストレートの切り替え

---

## 🚀 開発フェーズ

### ✅ Phase 1: MVP（7日間） - **現在のフェーズ**

**完了項目:**
- ✅ 環境構築とプロジェクトセットアップ
- ✅ ドキュメント作成（7カテゴリ分割版）
- ✅ 予測表生成アルゴリズム実装（4パターン対応）
- ✅ AIモデル構築（6つの統合モデル）
- ✅ バックエンドAPI開発（FastAPI + Next.js API Routes）
- ✅ フロントエンド実装（予測フロー、ローディング、軸数字表示）
- ✅ データファイル準備（past_results.csv、keisen_master.json）
- ✅ モデル学習（直近100回分データ）

**特徴:**
- CSVベースのデータ管理
- Vercelサーバーレス関数で完結
- セットアップコスト最小化

### 🔜 Phase 2: 信頼性向上（MVP+2週間）

**予定項目:**
- [ ] 学習データを1,800回分に拡大
- [ ] Supabase環境構築とテーブル設計
- [ ] CSVデータのマイグレーション
- [ ] モデル再学習・精度向上
- [ ] パフォーマンス最適化

### 🔜 Phase 3: アンサンブル導入（MVP+1ヶ月）

**予定項目:**
- [ ] 全6,700回分データで学習
- [ ] Weights & Biases導入とセットアップ
- [ ] チャート・マスターモデル構築
- [ ] アンサンブル学習実装
- [ ] 特徴量エンジニアリング実験

### 🔜 Phase 4: プロフェッショナル化（MVP+3ヶ月）

**予定項目:**
- [ ] 0あり/0なし統一モデル
- [ ] Dockerコンテナ化とGCP Cloud Run移行
- [ ] ユーザー認証機能
- [ ] 履歴管理機能
- [ ] CI/CDパイプライン構築
- [ ] セキュリティ対策実装

---

## 📊 進捗状況

### 完了した作業

1. **予測表生成アルゴリズム実装** ✅
   - 4パターン（A1/A2/B1/B2）対応完了
   - メイン行組み立てロジック実装
   - 裏数字ルール実装
   - 余りマスルール実装
   - 中心0配置実装（A2/B2のみ）

2. **AIモデル構築と学習** ✅
   - Jupyter Notebook環境セットアップ
   - データ前処理スクリプト作成
   - 予測表生成処理実装（Python）
   - 特徴量エンジニアリング実装
   - 6つの統合モデルの学習完了
   - モデル読み込みユーティリティ作成

3. **バックエンドAPI開発** ✅
   - FastAPI AI推論エンジン実装
   - Next.js API Route実装
   - 4パターン対応の予測表生成処理統合
   - 軸数字予測処理実装
   - 組み合わせ予測処理実装
   - ファイル更新自動検知機能実装

4. **フロントエンド実装** ✅
   - 予測フロー実装（回号入力、リハーサル入力）
   - ローディング画面実装（API呼び出し、エラーハンドリング）
   - 軸数字表示画面実装（N3/N4切り替え、ボックス/ストレート切り替え）
   - 手動指定軸数字機能実装
   - Zustandストア実装

### 次のステップ

1. **テストとデプロイ**
   - [ ] FastAPIサーバー起動確認と動作テスト
   - [ ] デバッグAPIでの動作確認
   - [ ] パフォーマンス最適化
   - [ ] Vercelへのデプロイ

---

## 🔑 主要ファイルとディレクトリ

### フロントエンド
- `src/app/page.tsx`: ホーム画面
- `src/app/predict/page.tsx`: 予測入力画面
- `src/app/predict/loading/page.tsx`: ローディング画面
- `src/app/predict/axis/page.tsx`: 軸数字表示画面
- `src/lib/chart-generator/chart-generator.ts`: 予測表生成ロジック
- `src/lib/predictor/predictor.ts`: 予測処理実装
- `src/lib/store.ts`: Zustandストア

### バックエンド
- `api/main.py`: FastAPIアプリケーション
- `src/app/api/predict/route.ts`: Next.js API Route

### AI/ML
- `notebooks/01_data_preparation.ipynb`: データ前処理
- `notebooks/02_chart_generation.ipynb`: 予測表生成
- `notebooks/03_feature_engineering.ipynb`: 特徴量エンジニアリング
- `notebooks/04_model_training.ipynb`: モデル学習
- `notebooks/chart_generator.py`: 予測表生成モジュール
- `notebooks/feature_extractor.py`: 特徴量抽出モジュール
- `notebooks/model_loader.py`: モデル読み込みユーティリティ

### データ
- `data/past_results.csv`: 過去当選番号データ（約6,700回分）
- `data/keisen_master.json`: 罫線マスターデータ
- `data/models/`: 学習済みモデル（6つの.pklファイル）

### ドキュメント
- `docs/design/01-business-requirements.md`: ビジネス要件定義書
- `docs/design/02-system-architecture.md`: システムアーキテクチャ設計書
- `docs/design/04-algorithm-ai.md`: アルゴリズム・AI設計書
- `docs/todo/進捗状況サマリー.md`: 進捗状況サマリー
- `README.md`: プロジェクト概要とセットアップガイド

---

## 📚 ドキュメント構造

### 開発の3本柱ドキュメント
1. **ビジネス要件定義書** (`docs/design/01-business-requirements.md`)
   - What（何を）を定義
2. **システムアーキテクチャ設計書** (`docs/design/02-system-architecture.md`)
   - How - Architecture（どのように構築するか）を定義
3. **実装計画書** (`docs/design/06-implementation-plan.md`)
   - When & Why（いつ、なぜ導入するか）を定義

### 設計ドキュメント
- **データ・API設計書** (`docs/design/03-data-api-design.md`)
- **アルゴリズム・AI設計書** (`docs/design/04-algorithm-ai.md`)
- **フロントエンド設計書** (`docs/design/05-frontend-design.md`)
- **運用・品質管理書** (`docs/design/07-operations-quality.md`)

### タスク管理
- `docs/todo/01_mvp-foundation/`: MVP基盤タスク
- `docs/todo/02_data-infrastructure/`: データインフラタスク
- `docs/todo/進捗状況サマリー.md`: 進捗状況サマリー

---

## 🎓 重要な概念

### 中国罫線理論
- **4パターン**: A1/A2/B1/B2の4パターンで予測表を生成
- **メイン行**: 予測出目から組み立てる主要な行
- **裏数字**: 縦パス/横パスによる裏数字適用ルール
- **余りマス**: メイン行配置後の余りマス処理ルール

### AIモデル構成
- **6つの統合モデル**:
  1. N3軸数字予測モデル
  2. N4軸数字予測モデル
  3. N3ボックス組み合わせ予測モデル
  4. N3ストレート組み合わせ予測モデル
  5. N4ボックス組み合わせ予測モデル
  6. N4ストレート組み合わせ予測モデル

### データ構造
- **past_results.csv**: 過去当選番号データ（約6,700回分）
- **keisen_master.json**: 罫線マスターデータ（前々回×前回の構造）
- **学習データ**: 直近100回分（MVP版）

---

## 🔧 開発コマンド

```bash
# 開発サーバー起動
pnpm dev

# ビルド
pnpm build

# 本番環境起動
pnpm start

# 型チェック
pnpm typecheck

# Lint
pnpm lint

# Lint修正
pnpm lint:fix

# テスト
pnpm test:patterns    # 4パターンテスト
pnpm test:api         # API統合テスト
```

---

## 📝 注意事項

### 重要な設定
- **環境変数**: `.env.local`で`FASTAPI_URL`を設定
- **データ基準点**: 第6758回以降のデータを使用
- **モデルファイル**: `data/models/`に6つの.pklファイルが必要

### 技術的負債
- MVP版はCSVベースのデータ管理（Phase 2でSupabase移行予定）
- Vercelサーバーレス関数の制限（Phase 4でGCP Cloud Run移行予定）

---

**最終更新**: 2025-01-XX  
**プロジェクト状態**: MVP開発中（Phase 1）

