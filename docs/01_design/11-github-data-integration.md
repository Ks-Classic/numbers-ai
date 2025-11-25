# GitHubデータ統合設計

## 概要

`numbers-ai`プロジェクトにおいて、GitHubリポジトリの`past_results.csv`を参照して最新データで予測を実行する機能を実装しました。

## 背景

- Vercel環境ではファイルシステムが読み取り専用のため、ローカルファイルの更新ができない
- 最新の当選データやリハーサル数字を使用するには、GitHubから直接取得する必要がある
- `numbers-ai-cube`で実装済みのデータ更新ロジックを`numbers-ai`にも適用

## 実装内容

### 1. データ取得フロー

```
ユーザー入力（回号）
    ↓
GitHubデータ取得・確認（自動・1秒デバウンス）
    ↓
データあり？ → Yes → 「最新データあり」表示（緑） + useGitHubData=true
    ↓ No
データ更新開始（GitHub Actions）
    ↓
「更新中」表示（紫） → 「更新開始完了」表示（緑） + 再確認ボタン
```

**特徴:**
- 回号入力後、1秒のデバウンスで自動的にGitHubデータをチェック
- データがない場合は自動的にGitHub Actionsワークフローをトリガーして更新
- 「データ確認・更新」ボタンで手動チェック・更新も可能
- 時刻による制限なし（常にチェック・更新可能）

### 2. 新規API

#### `/api/check-latest-data`
- **目的**: GitHubから最新の`past_results.csv`を取得して必要なデータを確認
- **メソッド**: GET
- **パラメータ**: `round` (回号、クエリパラメータ)
- **レスポンス**:
  ```json
  {
    "success": true,
    "latestRound": 6701,
    "hasRequiredData": true,
    "targetRoundData": {
      "round": 6701,
      "n3Rehearsal": "123",
      "n4Rehearsal": "4567"
    },
    "previousRoundData": {
      "round": 6700,
      "n3Winning": "456",
      "n4Winning": "7890"
    },
    "previousPreviousRoundData": {
      "round": 6699,
      "n3Winning": "789",
      "n4Winning": "0123"
    }
  }
  ```
- **hasRequiredDataの判定**: 前回(N-1)と前々回(N-2)の当選データが両方存在する場合に`true`

#### `/api/update-data`
- **目的**: GitHub Actionsワークフローをトリガーしてデータを更新
- **メソッド**: POST
- **パラメータ**: なし
- **レスポンス**:
  ```json
  {
    "success": true,
    "message": "データ更新を開始しました。数分後に完了します。",
    "workflowUrl": "https://github.com/Ks-Classic/numbers-ai/actions/workflows/auto-update-data.yml",
    "workflowId": "auto-update-data.yml",
    "currentLatestRound": 6700
  }
  ```
- **動作**: GitHub Actions APIを使用して`auto-update-data.yml`ワークフローを手動実行
- **必要な環境変数**: `PAT_TOKEN`（workflow権限が必要）

### 3. 予測API拡張

`/api/predict`に`useGitHubData`パラメータを追加：

```typescript
{
  roundNumber: 6701,
  n3Rehearsal: "123",
  n4Rehearsal: "4567",
  useGitHubData: true  // 追加
}
```

**処理フロー:**
1. `useGitHubData=true`の場合、APIルート内でGitHubから`past_results.csv`を取得
2. 取得したCSV内容を`csvContent`パラメータとしてPython予測関数に渡す
3. Python側でCSVをパースして予測に使用

**実装場所:**
- `/src/app/api/predict/route.ts` (L75-97): GitHubデータ取得処理
- `/src/lib/predictor/vercel-python.ts`: Python関数呼び出し時に`csvContent`を渡す

### 4. フロントエンド実装

#### 回号選択画面 (`/src/app/predict/page.tsx`)
- **自動チェック**: 回号入力後1秒のデバウンスで自動的にGitHubデータをチェック
- **自動更新**: データがない場合は自動的にGitHub Actionsワークフローをトリガー
- **手動ボタン**: 「データ確認・更新」ボタンで即座にチェック・更新可能
- **ステータス表示**:
  - 🔄 青背景: データ確認中
  - ⏳ 紫背景: データ更新中（GitHub Actions実行中）
  - ✅ 緑背景: 最新データあり（リハーサル数字も取得済み）
  - ✅ 緑背景: 更新開始成功（再確認ボタン付き）
  - ⚠️ 黄背景: データなし（手動入力が必要）
  - ❌ 赤背景: エラー発生

**実装詳細:**
- `checkData(roundNum, forceUpdate)`: GitHubデータ確認・更新関数
  - データあり → 緑表示
  - データなし → 自動的に`/api/update-data`を呼び出し
- `useEffect`: 回号変更時の自動チェック（1秒デバウンス）
- リハーサル数字の自動保存: `dataStatus.githubData?.targetRoundData`から取得
- 更新成功後の「再確認」ボタン: 更新完了を待ってから再度データチェック

#### リハーサル入力画面 (`/src/app/predict/rehearsal/page.tsx`)
- `currentSession.rehearsalN3/N4`に値があれば自動的にフォームに反映
- GitHubから取得したリハーサル数字がそのまま表示される
- ユーザーは必要に応じて手動で修正可能

#### 予測実行画面 (`/src/app/predict/loading/page.tsx`)
- `useGitHubData`フラグを予測APIに送信
- GitHubデータが利用可能な場合は自動的に使用される

### 5. ストア拡張

`src/lib/store.ts`と`src/types/prediction.ts`に`useGitHubData`フィールドを追加：

```typescript
currentSession: {
  sessionId: string | null;
  roundNumber: number;
  numbersType: 'N3' | 'N4';
  patternType: Pattern;
  rehearsalN3: string;
  rehearsalN4: string;
  selectedAxes: number[];
  useGitHubData: boolean;  // 追加（デフォルト: false）
}
```

**実装場所:**
- `/src/lib/store.ts` (L15, L76): デフォルト値を`false`に設定

## 動作フロー

### ケース1: GitHubにデータがある場合（通常ケース）
1. ユーザーが回号を入力（例: 6701）
2. 1秒後に自動的にGitHubデータをチェック
3. 前回(6700)・前々回(6699)の当選データあり → ✅「最新データあり」表示（緑）
4. 対象回号(6701)のリハーサル数字も取得され、自動保存
5. 次画面でリハーサル数字が自動入力される
6. 予測実行時に`useGitHubData=true`で送信
7. GitHubのCSVデータを使って予測実行

### ケース2: GitHubにデータがない場合（自動更新）
1. ユーザーが回号を入力（例: 6702）
2. 1秒後に自動的にGitHubデータをチェック
3. 前回・前々回のデータが不足 → 自動的にデータ更新開始
4. ⏳「更新中」表示（紫）→ GitHub Actionsワークフローをトリガー
5. ✅「更新開始完了」表示（緑）+ 「再確認」ボタン
6. 数分後、ユーザーが「再確認」ボタンをクリック
7. 更新されたデータを取得 → リハーサル数字が自動入力される

### ケース3: 手動でデータ確認・更新
1. ユーザーが「データ確認・更新」ボタンをクリック
2. 即座にGitHubデータをチェック（デバウンスなし）
3. データあり → 最新状態を表示
4. データなし → 自動的に更新開始（ケース2と同じ）

## 環境変数

GitHubデータ取得・更新に使用される環境変数（`/src/lib/data-loader/github-data.ts`、`/src/app/api/update-data/route.ts`）：

```env
# GitHubリポジトリ設定
GITHUB_REPO=Ks-Classic/numbers-ai
GITHUB_BRANCH=main

# アクセストークン（必須）
PAT_TOKEN=ghp_xxxxx
```

**注意:**
- `PAT_TOKEN`は必須（データ更新機能で使用）
- トークンには以下の権限が必要:
  - `repo`: リポジトリへの読み取り・書き込みアクセス
  - `workflow`: GitHub Actionsワークフローの実行権限
- 環境変数は`.env.local`に設定（Vercelでも同様に設定）
- プライベートリポジトリの場合は読み取り権限も必要

## 今後の拡張案

1. **キャッシュ機能**: 取得したGitHubデータを一定時間キャッシュして、API呼び出しを削減
2. **更新状態の自動監視**: GitHub Actionsの実行状態をポーリングして自動的に完了を検知
3. **エラーハンドリング強化**: GitHubアクセス失敗時のリトライ機能やフォールバック
4. **進捗表示の改善**: データ取得・更新中のプログレスバーやアニメーション
5. **データ更新通知**: 新しいデータが利用可能になったときのプッシュ通知
6. **オフラインサポート**: ローカルキャッシュを使った完全オフライン動作

## 参考

### 実装ファイル
- `/src/lib/data-loader/github-data.ts`: GitHubからCSVを取得する関数
- `/src/app/api/check-latest-data/route.ts`: データ確認API
- `/src/app/api/update-data/route.ts`: データ更新API（GitHub Actions連携）
- `/src/app/api/predict/route.ts`: 予測実行API（GitHubデータ統合）
- `/src/app/predict/page.tsx`: 回号選択画面（データチェック・更新機能）
- `/src/app/predict/rehearsal/page.tsx`: リハーサル入力画面（自動入力）
- `/src/lib/store.ts`: グローバルストア（useGitHubDataフラグ）

### 関連ドキュメント
- `numbers-ai-cube`プロジェクトの実装を参考にしています
- データ形式: `data/past_results.csv`（GitHubリポジトリ）
- GitHub Actions: `.github/workflows/auto-update-data.yml`
