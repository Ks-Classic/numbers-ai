# CUBE Webアプリ実装

## 概要
ReactベースのWebアプリで、回号を指定すると自動で全パターンのCUBE（通常CUBE 8個 + 極CUBE 2個 = 10個）を生成・表示し、Excelに貼り付け可能な形式で提供する。

## 要件

### CUBEの種類
- **通常CUBE**: A1, A2, B1, B2の4パターン × 現罫線/新罫線 = 8個
- **極CUBE**: 1パターン × 現罫線/新罫線 = 2個
- **合計**: 10個のCUBE

### 罫線マスター
- **現罫線**: `keisen_master.json`（1340-6391回のデータから生成）
- **新罫線**: `keisen_master_new.json`（4801-6850回のデータから生成）
- 両方を自動表示（選択不要）

### 機能
- 回号を入力すると、10個のCUBEを自動生成・表示
- 各CUBEにコピーボタンを配置
- クリックでクリップボードにコピー
- Excelに貼り付けたらそのままCUBEとして表示

## タスク

### Phase 1: バックエンドAPIの実装
- [x] Flask/FastAPIサーバーを実装
  - `/api/cube/<round_number>` エンドポイント
  - 指定回号で10個のCUBEを生成してJSONで返す
  - 現罫線と新罫線の両方に対応
- [x] CUBE生成関数の拡張
  - `load_keisen_master_by_type()`関数を追加して、keisen_masterの選択に対応
  - 現罫線と新罫線の両方でCUBEを生成

### Phase 2: フロントエンド（React）の実装
- [x] Reactプロジェクトのセットアップ
  - 既存のNext.jsプロジェクトに追加
- [x] 回号入力フォームの実装
  - 回号を入力するフォーム
  - バリデーション（最小回号）
- [x] CUBE表示コンポーネントの実装
  - 10個のCUBEを自動表示
  - 各CUBEにタイトル（罫線種類、パターン、CUBEタイプ）を表示
  - グリッドレイアウトで見やすく配置
- [x] コピーボタンの実装
  - 各CUBEにコピーボタンを配置
  - クリップボードAPI（`navigator.clipboard.writeText()`）を使用
  - 成功/失敗メッセージを表示（toast）
- [x] Excel貼り付け対応
  - TSV形式でクリップボードにコピー
  - Excelに貼り付けたらそのままCUBEとして表示される形式

### Phase 3: UI/UXの改善
- [x] ローディング状態の表示
  - CUBE生成中のローディングインジケーター（Loader2アイコン）
- [x] エラーハンドリング
  - 回号が無効な場合のエラーメッセージ（toast）
  - CUBE生成失敗時のエラーメッセージ（エラーカード表示）
- [x] レスポンシブデザイン
  - モバイル対応（グリッドレイアウト: 1列）
  - タブレット対応（グリッドレイアウト: 2列）
  - デスクトップ対応（グリッドレイアウト: 3列）

### Phase 4: テスト
- [ ] 単体テストを実施
  - APIエンドポイントのテスト
  - CUBE生成関数のテスト
  - Reactコンポーネントのテスト
- [ ] 統合テストを実施
  - エンドツーエンドのテスト
  - 10個のCUBEが正しく生成されることを確認
- [ ] ブラウザテストを実施
  - 実際にブラウザで開いて表示を確認
  - コピーボタンの動作確認
- [ ] Excel貼り付けテストを実施
  - 実際にExcelに貼り付けて動作を確認
  - セルが正しく分割されることを確認

## 実装ファイル

### バックエンド
- **APIサーバー**: `api/cube_api.py`（新規作成）
- **CUBE生成関数**: `scripts/export_cube_to_html.py`（拡張）

### フロントエンド
- **Reactコンポーネント**: `src/app/cube/page.tsx`（新規作成）
- **APIクライアント**: `src/lib/cube-api.ts`（新規作成）

## 完了した作業

- 2025-11-07: CUBE HTML出力スクリプトの実装を完了
  - `scripts/export_cube_to_html.py`を作成
  - 基本関数（`load_cube_data()`, `generate_html_table()`, `generate_html_page()`）を実装
  - コピーボタン機能を実装
  - コマンドライン引数処理とエラーハンドリングを実装

- 2025-01-XX: CUBE Webアプリの実装を完了
  - FastAPIサーバーに`/api/cube/<round_number>`エンドポイントを追加
  - `load_keisen_master_by_type()`関数を実装して、現罫線と新罫線の両方に対応
  - Reactコンポーネント（`src/app/cube/page.tsx`）を作成
  - APIクライアント関数（`src/lib/cube-api.ts`）を作成
  - 10個のCUBE（通常CUBE 8個 + 極CUBE 2個）を自動生成・表示
  - 各CUBEにコピーボタンを配置し、Excel貼り付け対応（TSV形式）

## 関連ドキュメント
- [CUBE生成ルール.md](../../01_design/CUBE生成ルール.md): CUBE生成ルール（通常CUBEと極CUBE）


