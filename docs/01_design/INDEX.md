# ドキュメントインデックス v2.5

このディレクトリには、ナンバーズAI予測システムの包括的なドキュメントが含まれています。

**バージョン**: 2.5  
**更新日**: 2025-11-07  
**変更**: CUBE保存方法の戦略追加、HTML出力スクリプト実装完了を反映

---

## 📚 開発の3本柱ドキュメント

プロジェクト開発に必須の3つの核心ドキュメントです。

### 01. ビジネス要件定義書（What）

**ファイル**: `01-business-requirements.md`  
**対象読者**: プロジェクトマネージャー、全開発メンバー

**主な内容**:
- ゴール定義（誰が、何を、どれくらいの時間で）
- ペルソナ定義
- ユーザーフロー
- 機能要件（優先度付き）
- 非機能要件
- 制約条件
- 用語集

**いつ読むか**: プロジェクト開始時、スコープ確認時

---

### 02. システムアーキテクチャ設計書（How - Architecture）

**ファイル**: `02-system-architecture.md`  
**対象読者**: システムアーキテクト、フルスタックエンジニア

**主な内容**:
- システムアーキテクチャ（MVP版・完全版）
- 技術スタック
- ディレクトリ構成
- コンポーネント責務

**いつ読むか**: 技術選定時、設計レビュー時

---

### 03. データ・API設計書（How - Data Layer）

**ファイル**: `03-data-api-design.md`  
**対象読者**: バックエンド・フロントエンドエンジニア

**主な内容**:
- CSVデータ構造（MVP版）
- PostgreSQLスキーマ（Phase 2以降）
- TypeScript型定義
- API仕様（OpenAPI形式）
- エラーハンドリング

**いつ読むか**: API実装時、データベース設計時

---

### 04. アルゴリズム・AI設計書（How - Core Logic）

**ファイル**: `04-algorithm-ai.md`  
**対象読者**: アルゴリズム実装者、データサイエンティスト

**主な内容**:
- 予測表生成アルゴリズム
- AI特徴量設計（4カテゴリ）
- AIモデルアーキテクチャ（6モデル構成）
- XGBoostハイパーパラメータ
- 推論フロー
- **推論実装の詳細**（CLIツール、モデル読み込みユーティリティ）
- **モデル学習手順**（4ステップの学習パイプライン）

**いつ読むか**: アルゴリズム実装時、AIモデル開発時

---

### 05. フロントエンド設計書（How - UI/UX）

**ファイル**: `05-frontend-design.md`  
**対象読者**: フロントエンドエンジニア、UI/UXデザイナー

**主な内容**:
- コンポーネント階層
- 状態管理
- UI/UXガイドライン
- カラーパレット
- タイポグラフィ

**いつ読むか**: UI実装時、デザインシステム構築時

---

### 06. 実装計画書（When & Why）⭐️ **開発前必読**

**ファイル**: `06-implementation-plan.md`（または `元ネタ/implementation-plan.md`）  
**対象読者**: 全開発メンバー、技術リード

**主な内容**:
- 実装戦略の全体像（MVP → Phase 4）
- MVP: なぜSupabase、W&B、GCP Cloud Runを使わないのか
- Phase 2: Supabase導入理由（データ量増加）
- Phase 3: W&B導入理由（実験管理の科学化）
- Phase 4: GCP Cloud Run導入理由（Vercel制限の克服）
- 技術選定の判断基準フレームワーク
- 技術的負債の管理方針（3段階分類）

**いつ読むか**: 開発開始前（必読）、技術選定の判断時、各フェーズ移行時

---

### 07. 運用・品質管理書（DevOps & QA）

**ファイル**: `07-operations-quality.md`  
**対象読者**: DevOps、QAエンジニア、運用担当者

**主な内容**:
- CI/CD設定（GitHub Actions）
- セキュリティ設計
- 品質基準
- Definition of Done

**いつ読むか**: CI/CD構築時、デプロイ前

---

### 08. keisen_master.json作成方法ドキュメント（Core Data Creation）

**ファイル**: `08-keisen-master-creation.md`  
**対象読者**: データエンジニア、アルゴリズム実装者、品質管理者

**主な内容**:
- keisen_master.jsonの重要性とプロジェクトへの影響
- JSON構造の詳細説明
- 作成手順の枠組み
- 検証方法
- 注意事項

**いつ読むか**: keisen_master.json作成時、データ基盤構築時

**注意**: 具体的な作成方法と予測出目ルールは、紙媒体の罫線ルール確定後に追加予定

---

### 09. データ分析・基礎集計設計書（Data Analysis Design）

**ファイル**: 
- `09-data-pipeline-design.md` (全体フロー)
- `09-01_cube-analysis-design.md` (通常CUBE)
- `09-02_extreme-cube-analysis-design.md` (極CUBE)
- `09-03_common-analysis-design.md` (共通分析)

**対象読者**: データサイエンティスト、データ分析担当者、アルゴリズム実装者

**主な内容**:
- 予測モデル構築の5ステップ
- 通常CUBE分析（keisen基礎集計、新旧比較）
- 極CUBE分析（並び型分析、全期間集計）
- 共通分析（数字出現パターン、時系列分析）

**いつ読むか**: 予測モデル作成前、基礎集計実施時、データ分析設計時

---

### 10. 極CUBE生成アルゴリズム仕様（CUBE Tools）

**ファイル**: `10-extreme-cube-generation-rules.md`  
**対象読者**: アルゴリズム実装者、データ分析担当者、CUBE生成ツール実装者

**主な内容**:
- 極CUBE生成アルゴリズム仕様
- 既存CUBEとの違い（5行目の余りマス処理）
- 極CUBE生成スクリプト設計
- CUBE HTML出力設計（既存CUBE + 極CUBE）
- CUBE保存方法の戦略（実運用/分析用途/長期保存）

**いつ読むか**: 極CUBE生成スクリプト実装時、CUBE HTML出力実装時

---

## 📖 推奨読書順序

### 新規メンバー向け

1. **README.md** - プロジェクト全体の概要
2. **01-business-requirements.md** - システム要件を理解
3. **06-implementation-plan.md** - 開発の進め方を理解 ⭐️
4. **02-system-architecture.md** - 技術的な全体像を把握

### フロントエンド開発者向け

1. **06-implementation-plan.md** - 現在のフェーズで使う技術を確認 ⭐️
2. **05-frontend-design.md** - UI/UX設計を理解
3. **03-data-api-design.md** - API仕様を確認
4. **01-business-requirements.md** - 機能要件を確認

### バックエンド/AI開発者向け

1. **06-implementation-plan.md** - 現在のフェーズで使う技術を確認 ⭐️
2. **08-keisen-master-creation.md** - keisen_master.jsonの作成方法を理解
3. **09-data-analysis-design.md** - データ分析・基礎集計設計を理解
4. **04-algorithm-ai.md** - アルゴリズムとAIを理解
5. **03-data-api-design.md** - データ・API設計を確認
6. **02-system-architecture.md** - システム全体像を把握

### プロジェクトマネージャー向け

1. **01-business-requirements.md** - 要件と制約を把握
2. **06-implementation-plan.md** - 開発ロードマップを確認 ⭐️
3. **07-operations-quality.md** - 品質基準とDoD を確認

---

## 🔄 ドキュメント更新履歴

| バージョン | 日付 | 主な変更内容 |
|-----------|------|-------------|
| 2.5 | 2025-11-07 | 技術リード | 10-extreme-cube-generation-rules.md更新（CUBE保存方法の戦略を追加）、09-data-analysis-design.md更新（極CUBE保存方法を明確化）、CUBE HTML出力スクリプト実装完了を反映 |
| 2.4 | 2025-11-06 | 技術リード | 10-extreme-cube-generation-rules.md追加（極CUBE生成アルゴリズム仕様、スクリプト設計、HTML出力設計を統合） |
| 2.3 | 2025-11-06 | 技術リード | 09-data-analysis-design.md追加（データ分析・基礎集計設計書） |
| 2.2 | 2025-11-06 | 技術リード | 推論実装と学習手順のドキュメント化（04-algorithm-ai.md） |
| 2.1 | 2025-11-02 | 技術リード | 08-keisen-master-creation.md追加（keisen_master.json作成方法） |
| 2.0 | 2025-11-02 | ドキュメントを7カテゴリに分割、開発フェーズごとに最適化 |
| 1.1 | 2025-11-02 | implementation-plan.md追加（実装計画書） |
| 1.0 | 2025-11-02 | 初版作成（requirements.md, specifications.md, INDEX.md追加） |

---

## 📌 ドキュメント構成の哲学

### なぜ7つに分割したのか？

**従来の問題:**
- `requirements.md`: 30,000文字（読むのに時間がかかる）
- `specifications.md`: 35,000文字（非常に長大）
- `implementation-plan.md`: 15,000文字

**分割後の利点:**
- 各ドキュメントが10,000文字以下で読みやすい
- 開発フェーズごとに必要なドキュメントだけを読める
- 役割別に適切なドキュメントを参照できる

### 3層構造

```
レイヤー1: ビジネス層（What）
  └─ 01-business-requirements.md

レイヤー2: 設計層（How）
  ├─ 02-system-architecture.md（全体設計）
  ├─ 03-data-api-design.md（データ層）
  ├─ 04-algorithm-ai.md（コアロジック）
  ├─ 05-frontend-design.md（UI/UX）
  ├─ 08-keisen-master-creation.md（コアデータ作成）
  ├─ 09-data-analysis-design.md（データ分析設計）
  └─ 10-extreme-cube-generation-rules.md（CUBE生成ツール）

レイヤー3: 実装・運用層（When & Action）
  ├─ 06-implementation-plan.md（実装戦略）⭐️
  └─ 07-operations-quality.md（運用・品質）
```

---

## 🔗 関連リンク

- **GitHubリポジトリ**: [numbers-ai](https://github.com/YOUR_USERNAME/numbers-ai)
- **参考リポジトリ**: [genesis-numbers](https://github.com/Ks-Classic/genesis-numbers)
- **Next.js ドキュメント**: https://nextjs.org/docs
- **XGBoost ドキュメント**: https://xgboost.readthedocs.io/

---

**Last Updated**: 2025-11-07 v2.5
