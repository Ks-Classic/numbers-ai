# CUBE生成機能のGit追加手順

## 必要なファイル

以下のファイルをGitに追加する必要があります：

### TypeScriptファイル（CUBE生成ロジック）
- `src/lib/cube-generator/chart-generator.ts`
- `src/lib/cube-generator/extreme-cube.ts`
- `src/lib/cube-generator/index.ts`
- `src/lib/cube-generator/keisen-master-loader.ts`
- `src/lib/cube-generator/types.ts`

### API Route
- `src/app/api/cube/[roundNumber]/route.ts`

### ページコンポーネント
- `src/app/cube/page.tsx`

### データファイル
- `data/keisen_master_new.json`

### ドキュメント
- `VERCEL_CUBE_DEPLOY_CHECKLIST.md`

## Git追加コマンド

WSL環境で以下のコマンドを実行してください：

```bash
cd /home/ykoha/numbers-ai

# CUBE生成ロジック
git add src/lib/cube-generator/chart-generator.ts
git add src/lib/cube-generator/extreme-cube.ts
git add src/lib/cube-generator/index.ts
git add src/lib/cube-generator/keisen-master-loader.ts
git add src/lib/cube-generator/types.ts

# API Route（角括弧はエスケープが必要）
git add 'src/app/api/cube/[roundNumber]/route.ts'

# ページコンポーネント
git add src/app/cube/page.tsx

# データファイル
git add data/keisen_master_new.json

# ドキュメント
git add VERCEL_CUBE_DEPLOY_CHECKLIST.md

# 状態確認
git status

# コミット
git commit -m "CUBE生成機能を追加（TypeScript実装、Vercelデプロイ対応）"

# プッシュ
git push origin main
```

## ワイルドカードを使用する場合

```bash
cd /home/ykoha/numbers-ai

# CUBE生成ロジック（ワイルドカード）
git add src/lib/cube-generator/*.ts

# API Route（角括弧はエスケープ）
git add 'src/app/api/cube/[roundNumber]/route.ts'

# ページコンポーネント
git add src/app/cube/page.tsx

# データファイルとドキュメント
git add data/keisen_master_new.json VERCEL_CUBE_DEPLOY_CHECKLIST.md

# 状態確認
git status
```

## 確認コマンド

追加されたファイルを確認：

```bash
git ls-files | grep -E "(cube-generator|cube/|VERCEL_CUBE|keisen_master_new)"
```

## 注意事項

- 角括弧を含むパス（`[roundNumber]`）は、シングルクォートで囲む必要があります
- ファイルが存在しない場合は、パスを確認してください
- `.gitignore`で除外されていないことを確認してください

