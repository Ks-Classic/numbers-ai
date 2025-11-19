# scriptsディレクトリ構造の分析

## 現在の構造

```
scripts/
├── 01_model_generation/      # モデル生成関連
├── 02_data_preparation/      # データ準備関連
├── 03_analysis/              # 分析関連
├── 04_validation/            # 検証関連
├── base_statistics/           # 基礎集計（カテゴリ別に整理）
├── tools/                     # 開発ツール
├── production/                # 本番スクリプト
└── test/                      # テストファイル
```

## 各ディレクトリの目的

### 01-04: AIモデル開発ワークフロー
- **01_model_generation**: モデル生成（データ生成、モニタリング）
- **02_data_preparation**: データ準備（取得、修正、検証）
- **03_analysis**: 分析（数値パターン、予測、ルール、過去結果）
- **04_validation**: 検証（keisen、データ）

これらは**AIモデル開発のワークフロー**の各ステップを表しています。

### base_statistics: 基礎集計
- **目的**: keisen作成のための基礎統計を実施
- **特徴**: データ分析・基礎集計に特化した独立したカテゴリ

### tools, production, test: その他
- **tools**: 開発時に使用するツール（analysis, training, validation, visualization）
- **production**: 本番環境で使用するスクリプト
- **test**: テストファイル

## 上位ディレクトリを作る場合の候補

### 候補1: `ml_workflow/` または `model_development/`
```
scripts/
├── ml_workflow/              # AIモデル開発ワークフロー
│   ├── 01_model_generation/
│   ├── 02_data_preparation/
│   ├── 03_analysis/
│   └── 04_validation/
├── base_statistics/           # 基礎集計（独立）
├── tools/                     # 開発ツール
├── production/                # 本番スクリプト
└── test/                      # テストファイル
```

**メリット**:
- AIモデル開発ワークフローが明確にグループ化される
- 01-04の関連性が明確になる

**デメリット**:
- `base_statistics`が独立して見えるが、実は「データ分析」の一部でもある
- 階層が深くなる（パスが長くなる）

### 候補2: `data_analysis/` または `analytics/`
```
scripts/
├── data_analysis/             # データ分析関連
│   ├── base_statistics/       # 基礎集計
│   ├── 03_analysis/           # 分析
│   └── 04_validation/         # 検証
├── ml_workflow/               # AIモデル開発ワークフロー
│   ├── 01_model_generation/
│   └── 02_data_preparation/
├── tools/                     # 開発ツール
├── production/                # 本番スクリプト
└── test/                      # テストファイル
```

**メリット**:
- データ分析関連がグループ化される
- `base_statistics`と`03_analysis`の関連性が明確になる

**デメリット**:
- `04_validation`は「検証」なので、データ分析とは少し異なる
- 構造が複雑になる

## 推奨: 上位ディレクトリは作らない

### 理由

1. **現在の構造が既に明確**
   - 01-04は番号で順序が明確
   - `base_statistics`は独立した目的が明確
   - `tools`, `production`, `test`も用途が明確

2. **base_statisticsとの関係**
   - `base_statistics`は「基礎集計」という特定の目的
   - `03_analysis`は「分析」というより広い目的
   - これらは異なる目的なので、同じ上位ディレクトリにまとめる必要はない

3. **階層の深さ**
   - 現在は2階層（scripts/01_model_generation/data_generation/）
   - 上位ディレクトリを作ると3階層になり、パスが長くなる

4. **base_statisticsの設計思想**
   - `base_statistics`は「基礎集計」という独立したカテゴリ
   - 01-04は「AIモデル開発ワークフロー」のステップ
   - これらは異なる分類軸なので、同じ上位ディレクトリにまとめる必要はない

### 現在の構造の利点

- **明確な分類**: 各ディレクトリの目的が明確
- **検索性**: 目的に応じて直接アクセス可能
- **拡張性**: 新しいカテゴリを追加しやすい
- **シンプル**: 階層が浅く、理解しやすい

## 結論

**上位ディレクトリは作らない方が自然です。**

現在の構造は：
- 01-04: AIモデル開発ワークフロー（番号で順序が明確）
- `base_statistics`: 基礎集計（独立した目的）
- `tools`, `production`, `test`: その他（用途が明確）

これらは異なる分類軸なので、同じ上位ディレクトリにまとめる必要はありません。

もし将来的に分類が必要になった場合は、README.mdで説明を追加する方が良いでしょう。

