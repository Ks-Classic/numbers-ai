#!/usr/bin/env bash

# Next.js開発サーバー起動スクリプト

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "Next.js開発サーバーを起動中..."
echo "サーバーURL: http://localhost:3000"
echo ""
echo "停止するには Ctrl+C を押してください"
echo ""

npm run dev

