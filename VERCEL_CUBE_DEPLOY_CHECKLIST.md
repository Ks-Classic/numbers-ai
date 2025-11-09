# CUBE生成機能 Vercelデプロイチェックリスト

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

### 3. 動作確認

1. デプロイされたURLにアクセス（例: `https://numbers-ai.vercel.app`）
2. `/cube`ページにアクセス
3. 回号を入力してCUBEを生成
4. 以下を確認：
   - [ ] 通常CUBE（8個）が表示される
   - [ ] 極CUBE（2個）が表示される
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

## 参考リンク

- [Vercelデプロイガイド](./VERCEL_DEPLOY.md)
- [CUBE生成システム設計書](./docs/01_design/10-cube-automation-design.md)
- [CUBE生成ルール](./docs/01_design/CUBE生成ルール.md)

