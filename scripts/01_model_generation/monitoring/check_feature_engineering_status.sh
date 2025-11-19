#!/bin/bash
# 特徴量エンジニアリングの実行状況を確認するスクリプト

cd /home/ykoha/numbers-ai

echo "=== 特徴量エンジニアリング実行状況 ==="
if ps aux | grep -q "[r]un_03_feature_engineering_full.py"; then
    echo "✅ 実行中"
    ps aux | grep "[r]un_03_feature_engineering_full.py"
else
    echo "❌ 実行されていません"
fi

echo ""
echo "=== データファイルの更新時刻 ==="
ls -lh data/models/*_axis_data.pkl 2>/dev/null | awk '{print $6, $7, $8, $9}'

echo ""
echo "=== 最新のログ（存在する場合） ==="
if [ -f "notebooks/feature_engineering_log.txt" ]; then
    tail -10 notebooks/feature_engineering_log.txt
else
    echo "ログファイルが見つかりません"
fi

