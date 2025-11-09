# 04-04-01 CUBE生成機能 Vercelデプロイチェックリスト

## 概要

CUBE生成機能はFastAPIサーバーに依存せず、TypeScriptで完全に実装されています。Next.js API Route（`/api/cube/[roundNumber]`）で実行されるため、Vercelにデプロイするだけで動作します。

## デプロイ前の確認事項

### 1. データファイルの確認

以下のファイルがGitリポジトリに含まれていることを確認：

- [ ] `data/past_results.csv` - 過去当選番号データ
- [ ] `data/keisen_master.json` - 現罫線マスターデータ
- [ ] `data/keisen_master_new.json` - 新罫線マスターデータ

**確認方法:**
```bash
git ls-files data/past_results.csv data/keisen_master.json data/keisen_master_new.json
```

### 2. ファイルサイズの確認

Vercelの無料プランでは、プロジェクト全体で100MBの制限があります。

- [ ] データファイルの合計サイズを確認
- [ ] 100MBを超える場合は、外部ストレージの使用を検討

**確認方法:**
```bash
du -sh data/past_results.csv data/keisen_master.json data/keisen_master_new.json
```

**現在のサイズ（参考）:**
- `data/past_results.csv`: 約252KB
- `data/keisen_master.json`: 約24KB
- `data/keisen_master_new.json`: 約24KB
- **合計**: 約300KB（問題なし）

### 3. `.gitignore`の確認

以下のディレクトリは除外されていることを確認（問題なし）：
- `data/extreme_cubes/` - 生成されたCUBEデータ（不要）
- `data/analysis/` - 分析結果（不要）

**必要なファイルが除外されていないことを確認:**
```bash
# 以下のファイルが表示されないことを確認
git check-ignore data/past_results.csv data/keisen_master.json data/keisen_master_new.json
```

### 4. ビルド設定の確認

- [ ] `vercel.json`が存在し、設定が正しいことを確認
- [ ] `package.json`の`build`スクリプトが正しいことを確認

**確認内容:**
- `vercel.json`の`buildCommand`: `pnpm build`
- `vercel.json`の`framework`: `nextjs`
- `vercel.json`の`regions`: `["hnd1"]`（東京リージョン）

### 5. コードの確認

- [ ] CUBE生成API Route（`src/app/api/cube/[roundNumber]/route.ts`）が存在することを確認
- [ ] CUBE生成ロジック（`src/lib/cube-generator/`）が存在することを確認
- [ ] CUBE表示ページ（`src/app/cube/page.tsx`）が存在することを確認

## デプロイ手順

### 1. GitHubにプッシュ

```bash
git add .
git commit -m "CUBE生成機能を追加"
git push origin main
```

### 2. Vercelダッシュボードで確認

1. [Vercelダッシュボード](https://vercel.com/dashboard)にログイン
2. プロジェクトを選択
3. 「Deployments」タブで最新のデプロイを確認
4. デプロイが成功していることを確認

**注意**: CUBE生成機能のみ使用する場合は、環境変数`FASTAPI_URL`の設定は不要です。

### 3. 動作確認

1. デプロイされたURLにアクセス（例: `https://numbers-ai.vercel.app`）
2. `/cube`ページにアクセス
3. 回号を入力してCUBEを生成
4. 以下を確認：
   - [ ] 通常CUBE（16個）が表示される
     - 現罫線 × 4パターン（A1, A2, B1, B2） × N3/N4 = 8個
     - 新罫線 × 4パターン（A1, A2, B1, B2） × N3/N4 = 8個
   - [ ] 極CUBE（2個）が表示される
     - 現罫線 × 1パターン（N3のみ）
     - 新罫線 × 1パターン（N3のみ）
   - [ ] 各CUBEのコピーボタンが動作する
   - [ ] 前回・前々回の当選番号が表示される（N3、N4）
   - [ ] 抽出数字が正しく表示される

### 4. エラーログの確認

Vercelダッシュボード → 「Logs」タブで以下を確認：

- [ ] ビルドエラーがないこと
- [ ] ランタイムエラーがないこと
- [ ] API Route（`/api/cube/[roundNumber]`）が正常に動作していること

## トラブルシューティング

### データファイルが見つからないエラー

**エラーメッセージ:**
```
データファイルが見つかりません: /vercel/path/to/data/past_results.csv
```

**対処法:**
1. データファイルがGitリポジトリに含まれているか確認
2. `.gitignore`で除外されていないか確認
3. ファイルパスが正しいか確認（`process.cwd()`を使用）

### 前回・前々回の当選番号が見つからないエラー

**エラーメッセージ:**
```
前回の当選番号が見つかりません（回号: XXXX）
```

**対処法:**
1. `past_results.csv`に最新のデータが含まれているか確認
2. 回号が3回以上存在することを確認（前回・前々回が必要なため）
3. CSVファイルのフォーマットが正しいか確認

### ビルドエラー

**エラーメッセージ:**
```
Error: Cannot find module '@/lib/cube-generator/...'
```

**対処法:**
1. TypeScriptのパスエイリアス（`@/`）が正しく設定されているか確認
2. `tsconfig.json`の`paths`設定を確認
3. ファイルが存在するか確認

### ファイルサイズ制限エラー

**エラーメッセージ:**
```
Error: File size exceeds limit
```

**対処法:**
1. データファイルのサイズを確認
2. 不要なファイルを削除
3. 外部ストレージ（AWS S3、Google Cloud Storage等）の使用を検討

## デプロイ後の確認事項

- [ ] CUBE生成機能が正常に動作する
- [ ] エラーログに問題がない
- [ ] パフォーマンスが許容範囲内（API Routeの実行時間が10秒以内）
- [ ] モバイルデバイスでも正常に動作する

## 重要なポイント

### ✅ FastAPIサーバー不要

CUBE生成機能は**完全にTypeScriptで実装**されており、FastAPIサーバーに依存しません：

- **API Route**: `src/app/api/cube/[roundNumber]/route.ts`
- **生成ロジック**: `src/lib/cube-generator/`
- **データローダー**: `src/lib/data-loader.ts`

### ✅ 環境変数不要

CUBE生成機能のみ使用する場合は、環境変数の設定は不要です。

### ⚠️ データ自動更新について

**現状**: ローカル環境では自動更新が設定されていますが、**Vercelデプロイ時は自動更新が動作しません**。

**ローカル環境での自動更新:**
- `scripts/production/auto_update_past_results.py`がcronジョブで平日15:00に実行される
- WSL環境でのcron設定が必要

**Vercelデプロイ時の対応（推奨: GitHub Actions）:**

✅ **GitHub Actions（無料・簡単）** - 推奨
- `.github/workflows/auto-update-data.yml`を作成済み
- 平日15:00（JST）に自動実行
- データ更新後、自動的にGitHubにコミット
- Vercelが自動的に再デプロイ（GitHub連携時）

**セットアップ手順:**
1. GitHubリポジトリの「Settings」→「Secrets and variables」→「Actions」を開く
2. 必要に応じてAPIキーを設定（オプション）:
   - `GEMINI_API_KEY`: Gemini APIキー（フォールバック用）
   - `SERP_API_KEY`: SerpAPIキー（フォールバック用）
3. `.github/workflows/auto-update-data.yml`が既に作成されているので、そのまま動作します
4. 初回実行は手動で「Actions」タブから実行可能

**その他の方法:**
- **Vercel Cron Jobs**: 無料プランでは1日1回まで（平日15:00の定期実行には不十分）
- **外部cronサービス**: EasyCron、Cron-job.orgなど（無料プランあり）
- **手動更新**: 必要に応じて手動でデータを更新

詳細は [04-05_データ自動更新とCUBE生成自動化.md](./04-05_データ自動更新とCUBE生成自動化.md) を参照。

### ✅ 生成されるCUBE

1. **通常CUBE（16個）**:
   - 現罫線 × 4パターン（A1, A2, B1, B2） × N3/N4 = 8個
   - 新罫線 × 4パターン（A1, A2, B1, B2） × N3/N4 = 8個

2. **極CUBE（2個）**:
   - 現罫線 × 1パターン（N3のみ）
   - 新罫線 × 1パターン（N3のみ）

**合計**: 18個のCUBEが生成されます

## 関連ドキュメント

- [07-operations-quality.md](../../01_design/07-operations-quality.md): 運用・品質管理書（本番デプロイ手順を含む）
- [10-cube-automation-design.md](../../01_design/10-cube-automation-design.md): CUBE生成システム設計書
- [CUBE生成ルール.md](../../01_design/CUBE生成ルール.md): CUBE生成アルゴリズムの詳細仕様

