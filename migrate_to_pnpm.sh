#!/bin/bash
# numbers-ai を npm から pnpm に移行するスクリプト

cd ~/numbers-ai

echo "🔄 npm から pnpm への移行を開始..."

# 1. 既存の node_modules と package-lock.json を削除
echo "  ✓ 既存の node_modules と package-lock.json を削除中..."
rm -rf node_modules package-lock.json

# 2. pnpm で依存関係をインストール
echo "  ✓ pnpm で依存関係をインストール中..."
pnpm install

# 3. package.json の packageManager フィールドを更新
echo "  ✓ package.json の packageManager を更新中..."
# macOS/Linux 互換の sed コマンド
if [[ "$OSTYPE" == "darwin"* ]]; then
  # macOS
  sed -i '' 's/"packageManager": "npm@10.0.0"/"packageManager": "pnpm@9.0.0"/g' package.json
else
  # Linux
  sed -i 's/"packageManager": "npm@10.0.0"/"packageManager": "pnpm@9.0.0"/g' package.json
fi

echo ""
echo "✅ 移行完了！"
echo ""
echo "次のステップ:"
echo "1. package.json のスクリプトを確認（npx → pnpm exec に変更）"
echo "2. pnpm dev でアプリケーションが正常に起動することを確認"
echo "3. 問題がなければ、変更をコミット"
