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
- **TypeScript**: ビジネスロジック

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
- pnpm 8.12.0以上
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
cp .env.local.example .env.local
```

`.env.local` を編集して必要な環境変数を設定してください。

4. **開発サーバーの起動**

```bash
pnpm dev
```

ブラウザで `http://localhost:3000` を開いてください。

### データの準備

MVP版では、以下のデータファイルが必要です：

- `data/past_results.csv`: 過去の当選・リハーサル数字
- `data/keisen_master.json`: 罫線マスターデータ
- `data/models/`: 学習済みモデルファイル（.pkl）

詳細は `docs/specifications.md` を参照してください。

---

## 使い方

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
- [ ] 罫線データのデジタル化
- [ ] 予測表生成アルゴリズム実装
- [ ] AIモデル構築（100回分データ）
- [ ] フロントエンド実装
- [ ] Vercelデプロイ

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

# 型チェック
pnpm typecheck

# Lint
pnpm lint

# Lint修正
pnpm lint:fix

# ユニットテスト
pnpm test:unit

# E2Eテスト
pnpm test:e2e

# 全テスト
pnpm test
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

**Last Updated**: 2025-11-02

