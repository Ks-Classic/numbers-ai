#!/bin/bash

# FastAPIサーバー起動スクリプト

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 仮想環境のパス
VENV_DIR="$SCRIPT_DIR/venv"

# 仮想環境が存在しない場合は作成
if [ ! -d "$VENV_DIR" ]; then
    echo "仮想環境を作成中..."
    python3 -m venv venv
fi

# 仮想環境を有効化
echo "仮想環境を有効化中..."
source venv/bin/activate

# 依存関係をインストール（requirements.txtが更新されている場合）
echo "依存関係を確認中..."
pip install -q -r requirements.txt

# サーバーを起動
echo "FastAPIサーバーを起動中..."
echo "サーバーURL: http://localhost:8000"
echo "APIドキュメント: http://localhost:8000/docs"
echo ""
echo "停止するには Ctrl+C を押してください"
echo ""

python run.py

