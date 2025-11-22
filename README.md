# ナンバーズAI予測システム (Numbers-AI)

独自の「中国罫線」理論とAI技術を融合した、ナンバーズ3/4の当選番号予測Webアプリケーション

[![TypeScript](https://img.shields.io/badge/TypeScript-5.3-blue)](https://www.typescriptlang.org/)
[![Next.js](https://img.shields.io/badge/Next.js-14.2-black)](https://nextjs.org/)
[![License](https://img.shields.io/badge/license-MIT-green)](./LICENSE)

---

## 📋 目次

- [概要](#概要)
- [主な機能](#主な機能)
- [技術スタック](#技術スタック)
- [環境構築](#環境構築)
- [使い方](#使い方)
- [プロジェクト構造](#プロジェクト構造)
- [ドキュメント](#ドキュメント)
- [開発ロードマップ](#開発ロードマップ)
- [貢献](#貢献)
- [ライセンス](#ライセンス)

---

## 概要

ナンバーズAI予測システムは、紙媒体で管理されていた「中国罫線」という独自の予測理論をデジタル化し、過去約6,700回分のデータから学習したAIモデルを用いて、ナンバーズ3/4の当選番号候補をスコア順にランキング表示するWebアプリケーションです。

### 🎯 プロジェクトの特徴

- **独自理論のデジタル化**: 紙媒体の罫線理論を完全にデジタル化
- **AI多角分析**: XGBoostを用いた8つの専門モデルで多角的に予測
- **3ステップで完結**: 回号入力 → リハーサル入力 → 予測結果表示
- **モバイルファースト**: スマートフォンでの使用を前提としたUI/UX
- **高速レスポンス**: 5秒以内にAI予測結果を表示

### 🚀 開発アプローチ

本プロジェクトは、MVP（Minimum Viable Product）から段階的に機能を拡張するアジャイル開発を採用しています。

**現在のフェーズ: MVP（Phase 1）**
- 開発期間: 7日間
- 対象: N3/N4の基本予測機能
- データ: 直近100回分

---

## 主な機能

### ✅ MVP版（Phase 1）

- **予測表自動生成**: 中国罫線理論に基づく予測表を自動生成
- **AI軸数字予測**: 当選確率が高い軸数字（0〜9）をスコア順に提示
- **AI組み合わせ予測**: 軸数字を含む当選番号候補をランキング表示
- **N3/N4対応**: ナンバーズ3と4の両方に対応
- **ボックス/ストレート対応**: 2つの予測タイプに対応
- **手動指定軸機能**: ユーザーが任意の軸数字を指定して予測

### ✅ CUBE生成機能（Phase 1+）

- **CUBE自動生成**: 回号を入力すると、通常CUBE（8個）と極CUBE（2個）を自動生成
- **現罫線/新罫線対応**: 両方の罫線マスターデータに対応（合計10個のCUBE）
- **Excel貼り付け対応**: 生成されたCUBEをクリップボードにコピーしてExcelに直接貼り付け可能
- **TypeScript実装**: Next.js内包型で、FastAPIサーバーへの依存なし

### 🔜 今後の予定

- **Phase 2**: 学習データを1,800回分に拡大（MVP+2週間）
- **Phase 3**: アンサンブル学習の実装（MVP+1ヶ月）
- **Phase 4**: 0あり/0なし統一モデル、Supabase移行（MVP+3ヶ月）

---

## 技術スタック

### フロントエンド

- **Next.js** 14.2+ (App Router)
- **React** 18.3+
- **TypeScript** 5.3+
- **Tailwind CSS** 3.4+
- **Redux Toolkit** 2.0+
- **Framer Motion**: アニメーション

### バックエンド（MVP版）

- **Next.js API Routes**: サーバーレス関数
- **TypeScript**: ビジネスロジック（CUBE生成を含む）
- **FastAPI** (Python): AI推論エンジン（XGBoostモデル実行）

### AI/ML

- **XGBoost** 2.0+: 機械学習アルゴリズム
- **scikit-learn** 1.3+: 前処理・評価
- **Python** 3.10+: AIモデル開発

### インフラ

- **Vercel**: ホスティング + CI/CD
- **GitHub**: ソースコード管理
- **CSV**: データストレージ（MVP版）

---

## 環境構築

### 前提条件

- Node.js 20.x以上
- pnpm 9.0.0以上（高速・省スペースなパッケージマネージャー）
  ```bash
  npm install -g pnpm
  ```
- Python 3.10以上（AI開発時）

### セットアップ手順

1. **リポジトリのクローン**

```bash
git clone https://github.com/YOUR_USERNAME/numbers-ai.git
cd numbers-ai
```

2. **依存関係のインストール**

```bash
pnpm install
```

3. **環境変数の設定**

```bash
# .env.localファイルを作成
echo "FASTAPI_URL=http://localhost:8000" > .env.local
```

`.env.local` を編集して `FASTAPI_URL` を設定してください。

4. **FastAPIサーバーの起動**

```bash
# apiディレクトリに移動
cd api

# 仮想環境を作成（初回のみ）
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 依存関係をインストール（初回のみ）
pip install -r requirements.txt

# サーバーを起動
python run.py
```

FastAPIサーバーは `http://localhost:8000` で起動します。

5. **Next.js開発サーバーの起動**

別のターミナルで：

```bash
# プロジェクトルートに戻る
cd ..

# 開発サーバーを起動
pnpm dev
```

ブラウザで `http://localhost:3000` を開いてください。

### API統合テストの実行

両方のサーバーが起動している状態で、以下のコマンドでAPI統合テストを実行できます：

```bash
# テストスクリプトを実行
pnpm test:api

# または直接実行
bash scripts/test-api.sh
```

テストスクリプトは以下を確認します：
- FastAPIサーバーのヘルスチェック
- Next.js API Routeの動作確認
- FastAPI軸数字予測エンドポイントのテスト
- FastAPI組み合わせ予測エンドポイントのテスト

詳細は `docs/SETUP.md` を参照してください。

### Vercelへのデプロイ

プロジェクトをVercelにデプロイする手順：

1. **GitHubリポジトリにプッシュ**
   ```bash
   git add .
   git commit -m "Deploy to Vercel"
   git push origin main
   ```

2. **Vercelプロジェクトの作成**
   - [Vercelダッシュボード](https://vercel.com/dashboard)にログイン
   - 「Add New...」→「Project」をクリック
   - GitHubリポジトリ `Ks-Classic/numbers-ai` を選択
   - プロジェクト名: `numbers-ai` を確認

3. **環境変数の設定**
   - Vercelダッシュボード → Settings → Environment Variables
   - **必須**: `GITHUB_TOKEN` を設定（GitHub Personal Access Token、データ更新機能用）
     - スコープ: `repo`, `workflow`
   - **オプション**: `GITHUB_REPO` を設定（デフォルト: `Ks-Classic/numbers-ai`）
   - Environment: Production, Preview, Development すべてにチェック

4. **デプロイの実行**
   - 「Deploy」ボタンをクリック
   - デプロイが完了するまで待機

**注意**: 
- **CUBE生成機能はVercelでそのまま動作します**（FastAPIサーバー不要）
- データ更新機能を使用する場合は、`GITHUB_TOKEN`の設定が必要です
- 詳細は `docs/VERCEL_CUBE_DEPLOY.md` を参照してください

### データの準備

MVP版では、以下のデータファイルが必要です：

**予測機能に必要なデータ:**
- `data/past_results.csv`: 過去当選番号データ
- `data/models/*.pkl`: 学習済みモデル（AI推論用）

**CUBE生成機能に必要なデータ:**
- `data/past_results.csv`: 過去当選番号データ（予測機能と共通）
- `data/keisen_master.json`: 現罫線マスターデータ
- `data/keisen_master_new.json`: 新罫線マスターデータ

**注意**: これらのファイルはGitリポジトリに含まれている必要があります（Vercelデプロイ時に必要）。

詳細は `docs/design/04-algorithm-ai.md` を参照してください。

### AIモデルの学習

モデルを学習する場合は、以下の手順でNotebookを実行してください：

1. **データ準備** (`notebooks/01_data_preparation.ipynb`)
   - 過去当選番号データの読み込みとクリーニング
   - 学習用データセットの準備（直近100回分）

2. **予測表生成** (`notebooks/02_chart_generation.ipynb`)
   - 各回号に対して4パターン（A1/A2/B1/B2）の予測表を生成

3. **特徴量エンジニアリング** (`notebooks/03_feature_engineering.ipynb`)
   - 予測表から特徴量を抽出
   - 学習データの生成と保存

4. **モデル学習** (`notebooks/04_model_training.ipynb`)
   - 6つの統合モデルの学習
   - モデル評価と保存

詳細な手順は `docs/design/04-algorithm-ai.md` の「4.5.2 モデル学習手順」を参照してください。

---

## 使い方

### Webアプリケーション

#### 予測機能（Phase 2以降）

### 1. ホーム画面

アプリを開くと、「新規予測を開始」ボタンが表示されます。

### 2. 回号入力

4桁の回号（例: 6701）を入力します。

### 3. リハーサル数字入力

- **N4**: 4桁のリハーサル数字を入力
- **N3**: 3桁のリハーサル数字を入力

各桁は自動的に次のフィールドにフォーカスが移動します。

### 4. AI予測実行

「AI予測を実行」ボタンをタップすると、AIが分析を開始します（3〜5秒）。

### 5. 結果表示

- **タブ切替**: N3/N4、ボックス/ストレート
- **表示モード**: 軸数字モード / 総合ランキングモード
- **軸数字候補**: スコア順にランキング表示、タップで展開
- **手動指定軸**: 任意の数字（0〜9）を指定して予測

#### CUBE生成機能

### 1. CUBE表示ページにアクセス

ナビゲーションから「CUBE」を選択するか、`/cube`にアクセスします。

### 2. 回号を入力

4桁の回号（例: 6851）を入力します。

### 3. CUBE生成

「生成」ボタンをクリックすると、以下の10個のCUBEが自動生成されます：

- **通常CUBE（8個）**:
  - 現罫線: N3/N4 × A1/A2/B1/B2 = 4個
  - 新罫線: N3/N4 × A1/A2/B1/B2 = 4個
- **極CUBE（2個）**:
  - 現罫線: N3のみ = 1個
  - 新罫線: N3のみ = 1個

### 4. Excelにコピー

各CUBEの「コピー」ボタンをクリックすると、TSV形式でクリップボードにコピーされます。Excelに貼り付けると、そのままCUBEとして表示されます。

詳細は [CUBE生成ルール.md](./docs/01_design/CUBE生成ルール.md) を参照してください。

### CLIツール（MVP版）

コマンドラインから予測を実行するためのCLIツールが利用可能です。

**使用方法:**

```bash
cd notebooks

# コマンドライン引数で実行
python predict_cli.py --round 6758 --n3-rehearsal 149 --n4-rehearsal 3782

# 対話的に実行
python predict_cli.py
```

**出力内容:**
- パターン別軸数字予測結果（A1/A2/B1/B2）
- 最良パターンの特定
- 軸数字ランキング（上位10件）
- 組み合わせランキング（ボックス/ストレート別、上位10件）

詳細は `notebooks/README_predict_cli.md` を参照してください。

---

## プロジェクト構造

```
numbers-ai/
├── docs/                      # ドキュメント
│   ├── requirements.md        # 要件定義書
│   ├── specifications.md      # 技術仕様書
│   ├── UIイメージ.md          # UI設計
│   └── ...
├── src/
│   ├── app/                   # Next.js App Router
│   ├── components/            # Reactコンポーネント
│   ├── lib/                   # ビジネスロジック
│   ├── store/                 # Redux状態管理
│   └── types/                 # TypeScript型定義
├── data/                      # データファイル（MVP）
├── notebooks/                 # Jupyter Notebooks
├── tests/                     # テストコード
└── public/                    # 静的ファイル
```

詳細は `docs/specifications.md` の「ディレクトリ構成」セクションを参照してください。

---

## ドキュメント

プロジェクトの詳細な情報は、以下のドキュメントを参照してください：

### 📚 主要ドキュメント（v2.0: 7カテゴリ分割版）

#### 開発の3本柱ドキュメント
- **[01-ビジネス要件定義書](./docs/01-business-requirements.md)**: システムの要件・機能・非機能要件（**What**を定義）
- **[02-システムアーキテクチャ設計書](./docs/02-system-architecture.md)**: 技術スタック・システム構成（**How - Architecture**を定義）
- **[06-実装計画書](./docs/06-implementation-plan.md)** または [元ネタ版](./docs/元ネタ/implementation-plan.md): 段階的な開発計画・技術選定理由（**When & Why**を定義）⭐️ **開発前必読**

#### 設計ドキュメント
- **[03-データ・API設計書](./docs/03-data-api-design.md)**: データモデル・API仕様（**How - Data Layer**）
- **[04-アルゴリズム・AI設計書](./docs/04-algorithm-ai.md)**: 予測表生成・AIモデル（**How - Core Logic**）
- **[05-フロントエンド設計書](./docs/05-frontend-design.md)**: UI/UXガイドライン・コンポーネント（**How - UI/UX**）

#### 運用ドキュメント
- **[07-運用・品質管理書](./docs/07-operations-quality.md)**: CI/CD・セキュリティ・品質基準（**DevOps & QA**）

#### 補助ドキュメント
- **[INDEX.md](./docs/INDEX.md)**: ドキュメントインデックス（推奨読書順序付き）
- **[SUMMARY.md](./docs/SUMMARY.md)**: ドキュメント作成サマリー
- **[UIイメージ.md](./docs/UIイメージ.md)**: 詳細なUI設計

### 📖 ドキュメントの読み方

1. **初めての方**: `INDEX.md` → `01-business-requirements.md` → `06-implementation-plan.md`⭐️ の順に読むことを推奨
2. **開発者**: `06-implementation-plan.md`で現在のフェーズを確認⭐️ → 必要なドキュメント（02〜05）を参照
3. **アルゴリズム理解**: `04-algorithm-ai.md`で予測表生成ロジックを理解

**重要**: `06-implementation-plan.md`は、「なぜ今この技術を使うのか」「なぜ今は使わないのか」を明確にしているため、開発開始前に必ず読んでください。⭐️

**v2.0の改善点:**
- 巨大ドキュメントを7つのカテゴリに分割
- 各ドキュメントが10,000文字以下で読みやすい
- 役割別・開発フェーズ別に最適化された構成

---

## 開発ロードマップ

### ✅ Phase 1: MVP（7日間） - 現在

- [x] 環境構築
- [x] ドキュメント作成
- [x] 罫線データのデジタル化
- [x] 予測表生成アルゴリズム実装
- [x] AIモデル構築（100回分データ）
- [x] フロントエンド実装
- [x] Vercelデプロイ設定（vercel.json作成完了）

### 🔜 Phase 2: 信頼性向上（MVP+2週間）

- [ ] 学習データを1,800回分に拡大
- [ ] モデル再学習・精度向上
- [ ] パフォーマンス最適化

### 🔜 Phase 3: アンサンブル導入（MVP+1ヶ月）

- [ ] 全6,700回分データで学習
- [ ] チャート・マスターモデル構築
- [ ] アンサンブル学習実装

### 🔜 Phase 4: プロフェッショナル化（MVP+3ヶ月）

- [ ] 0あり/0なし統一モデル
- [ ] Supabase移行
- [ ] GCP Cloud Run移行
- [ ] ユーザー認証機能
- [ ] 履歴管理機能

---

## 開発コマンド

```bash
# 開発サーバー起動
pnpm dev

# ビルド
pnpm build

# 本番環境起動
pnpm start

# Lint
pnpm lint

# テスト実行
pnpm test:data-loader
pnpm test:chart-generator
pnpm test:patterns
pnpm test:api
```

---

## 貢献

現在このプロジェクトは個人開発中のため、外部からの貢献は受け付けていません。

将来的にオープンソース化する予定です。

---

## ライセンス

MIT License

Copyright (c) 2025 Numbers-AI Project

---

## 参考リソース

- **元リポジトリ**: [genesis-numbers](https://github.com/Ks-Classic/genesis-numbers)
- **Next.js ドキュメント**: https://nextjs.org/docs
- **XGBoost ドキュメント**: https://xgboost.readthedocs.io/
- **Vercel ドキュメント**: https://vercel.com/docs

---

## お問い合わせ

プロジェクトに関する質問・要望は、GitHub Issuesまでお願いします。

---

**Last Updated**: 2025-11-22

