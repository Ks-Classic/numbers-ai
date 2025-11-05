# コーディング規約とスタイル

## TypeScript設定
- **strictモード**: 有効
- **target**: ES2017
- **module**: esnext
- **jsx**: preserve
- **paths**: `@/*` → `./src/*`

## 命名規則
- **関数**: camelCase（例: `predictAxis`, `generateChart`）
- **型/インターフェース**: PascalCase（例: `AxisPredictionResponse`, `ChartData`）
- **定数**: UPPER_SNAKE_CASE（例: `FASTAPI_URL`）
- **ファイル名**: kebab-case（例: `chart-generator.ts`, `predictor.ts`）

## コードスタイル
- **非同期処理**: async/awaitを使用
- **エラーハンドリング**: try-catchとカスタムエラークラスを使用
- **型定義**: 明示的な型注釈を推奨
- **コメント**: 日本語コメントを使用（ビジネスロジックの説明）

## ディレクトリ構造
- **src/app/**: Next.js App Router（ページとAPIルート）
- **src/components/**: Reactコンポーネント
  - `features/`: 機能コンポーネント
  - `layouts/`: レイアウトコンポーネント
  - `shared/`: 共有コンポーネント
  - `ui/`: UIコンポーネント（Radix UI）
- **src/lib/**: ビジネスロジック
  - `chart-generator/`: 予測表生成
  - `data-loader/`: データ読み込み
  - `predictor/`: 予測処理
- **src/types/**: TypeScript型定義

## 状態管理
- **Zustand**: グローバル状態管理
  - `usePredictionStore`: 予測状態
  - `useHistoryStore`: 履歴状態
  - `useStatisticsStore`: 統計状態

## エラーハンドリング
- **カスタムエラークラス**: `ChartGenerationError`, `DataLoadError`
- **エラーメッセージ**: 日本語でユーザーフレンドリーなメッセージ

## コメント規約
- ビジネスロジックの説明は日本語
- 複雑なアルゴリズムには詳細なコメントを追加
- ステップバイステップの説明を推奨