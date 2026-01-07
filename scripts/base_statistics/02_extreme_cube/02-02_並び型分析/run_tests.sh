#!/bin/bash
# 単体テストの実行スクリプト

# プロジェクトルートに移動
cd "$(dirname "$0")/../../../../" || exit 1

# venvの有効化（存在する場合）
if [ -d "venv" ]; then
    echo "venvを有効化しています..."
    source venv/bin/activate
fi

# Pythonのパスを確認
echo "Python: $(which python)"
echo "Python version: $(python --version)"
echo ""

# テストの実行
echo "単体テストを実行しています..."
echo "=========================================="
# PYTHONPATHを設定してテストを実行
export PYTHONPATH="${PROJECT_ROOT}/core:${PROJECT_ROOT}/scripts/production:${PYTHONPATH}"
python scripts/base_statistics/02_extreme_cube/02-02_並び型分析/test_pattern_classifier.py

# 終了コードを保存
EXIT_CODE=$?

# venvを無効化（有効化した場合）
if [ -d "venv" ] && [ -n "$VIRTUAL_ENV" ]; then
    deactivate
fi

exit $EXIT_CODE

