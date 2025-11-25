# GitHubデータ統合機能実装

**ステータス**: ✅ 完了  
**優先度**: 高  
**担当**: AI  
**完了日**: 2025-11-26

## 概要

`numbers-ai-cube`のGitHubデータ更新ロジックを`numbers-ai`に移植し、回号選択画面で自動的に最新データを確認・適用する機能を実装しました。

## 実装内容

### ✅ 完了項目

1. **Python予測APIの拡張**
   - `api/py/axis.py`に`csv_content`パラメータを追加
   - `api/py/combination.py`に`csv_content`パラメータを追加
   - GitHubから取得したCSVデータを直接使用可能に

2. **新規API作成**
   - `/api/check-local-data`: ローカルデータの有無確認
   - `/api/check-latest-data`: GitHubから最新データ取得・確認

3. **予測API拡張**
   - `/api/predict`に`useGitHubData`パラメータを追加
   - GitHubデータ取得処理を実装

4. **回号選択画面の機能追加**
   - 13時以降の自動データチェック機能
   - 手動「データ更新確認」ボタン
   - データステータスの視覚的表示（緑/黄）
   - GitHubデータがある場合の自動適用

5. **リハーサル数字自動入力**
   - GitHubにリハーサル数字がある場合、自動的に入力欄に反映

6. **ストア拡張**
   - `useGitHubData`フラグの追加
   - リハーサル数字の事前保存機能

7. **TypeScript型定義更新**
   - `PredictionState`に`useGitHubData`を追加

8. **設計ドキュメント作成**
   - `/docs/01_design/11-github-data-integration.md`

## 技術詳細

### データ取得フロー

```
回号入力
  ↓
13時以降？ → No → スキップ
  ↓ Yes
ローカルチェック（N-1, N-2）
  ↓
あり？ → Yes → OK
  ↓ No
GitHubチェック
  ↓
あり？ → Yes → useGitHubData=true
  ↓ No
警告表示
```

### 修正ファイル一覧

#### Python
- `api/py/axis.py` - csv_content対応
- `api/py/combination.py` - csv_content対応

#### TypeScript/React
- `src/app/api/check-local-data/route.ts` - 新規作成
- `src/app/api/check-latest-data/route.ts` - 新規作成
- `src/app/api/predict/route.ts` - useGitHubData対応
- `src/app/predict/page.tsx` - データチェック機能追加
- `src/app/predict/loading/page.tsx` - useGitHubData送信
- `src/lib/predictor/vercel-python.ts` - csvContent対応
- `src/lib/store.ts` - useGitHubData追加
- `src/types/prediction.ts` - 型定義更新

#### ドキュメント
- `docs/01_design/11-github-data-integration.md` - 新規作成

## 動作確認項目

### テストケース

1. **ローカルデータあり**
   - [ ] 13時前: チェックスキップ
   - [ ] 13時以降: 自動チェック → OK表示
   - [ ] 手動ボタン: いつでもチェック可能

2. **ローカルデータなし、GitHubあり**
   - [ ] GitHubから最新データ取得
   - [ ] 緑色の成功メッセージ表示
   - [ ] リハーサル数字が自動入力される
   - [ ] 予測実行時にGitHubデータを使用

3. **どこにもデータなし**
   - [ ] 黄色の警告メッセージ表示
   - [ ] 手動入力で続行可能

## 今後の改善案

1. **パフォーマンス最適化**
   - GitHubデータのキャッシュ機能
   - 取得済みデータの再利用

2. **エラーハンドリング強化**
   - GitHubアクセス失敗時のリトライ
   - タイムアウト処理

3. **UI/UX改善**
   - データ取得中のローディング表示
   - より詳細なステータス情報

4. **GitHub Actions連携**
   - 手動データ更新ボタン（ワークフロートリガー）
   - 更新完了通知

## 関連ドキュメント

- [GitHubデータ統合設計](/docs/01_design/11-github-data-integration.md)
- [numbers-ai-cube データ更新設計](/home/ykoha/numbers-ai-cube/docs/01_design/10-cube-automation-design.md)

## 備考

- Vercel環境では`past_results.csv`の更新ができないため、GitHubから直接取得する方式を採用
- ローカル開発環境では従来通りローカルファイルを優先使用
- 13時判定はJST（日本時間）で実施
