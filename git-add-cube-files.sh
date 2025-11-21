#!/bin/bash
# CUBE生成機能のファイルをGitに追加するスクリプト

cd /home/ykoha/numbers-ai

echo "CUBE生成機能のファイルをGitに追加します..."

# CUBE生成ロジック
git add src/lib/cube-generator/chart-generator.ts
git add src/lib/cube-generator/extreme-cube.ts
git add src/lib/cube-generator/index.ts
git add src/lib/cube-generator/keisen-master-loader.ts
git add src/lib/cube-generator/types.ts

# API Route
git add 'src/app/api/cube/[roundNumber]/route.ts'

# ページコンポーネント
git add src/app/cube/page.tsx

# データファイル
git add data/keisen_master_new.json
git add data/past_results.csv

# ドキュメント
git add VERCEL_CUBE_DEPLOY_CHECKLIST.md

echo ""
echo "追加されたファイル:"
git status --short

echo ""
echo "コミットする場合は以下を実行してください:"
echo "git commit -m 'CUBE生成機能を追加（TypeScript実装、Vercelデプロイ対応）'"
echo "git push origin main"

