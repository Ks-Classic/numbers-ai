#!/bin/bash
# 特徴量エンジニアリングの実行状況を監視するスクリプト

cd /home/ykoha/numbers-ai

echo "=== 特徴量エンジニアリング実行状況 ==="
PROCESS=$(ps aux | grep '[r]un_03_feature_engineering_full.py')
if [ -n "$PROCESS" ]; then
    echo "✅ 実行中"
    echo "$PROCESS"
else
    echo "❌ 実行されていません"
fi

echo ""
echo "=== データファイルの状況 ==="
if [ -f "data/models/n3_axis_data.pkl" ]; then
    echo "✅ n3_axis_data.pkl が存在します"
    ls -lh data/models/n3_axis_data.pkl | awk '{print "  更新時刻:", $6, $7, $8, "サイズ:", $5}'
    
    # ファイルの更新時刻を確認
    FILE_TIME=$(stat -c %Y data/models/n3_axis_data.pkl 2>/dev/null)
    CURRENT_TIME=$(date +%s)
    if [ -n "$FILE_TIME" ]; then
        AGE=$((CURRENT_TIME - FILE_TIME))
        if [ $AGE -lt 300 ]; then
            echo "  ⚠️  ファイルは5分以内に更新されました（実行中かもしれません）"
        else
            echo "  ℹ️  ファイルは $((AGE / 60)) 分前に更新されました"
        fi
    fi
else
    echo "❌ n3_axis_data.pkl が存在しません"
fi

if [ -f "data/models/n4_axis_data.pkl" ]; then
    echo "✅ n4_axis_data.pkl が存在します"
    ls -lh data/models/n4_axis_data.pkl | awk '{print "  更新時刻:", $6, $7, $8, "サイズ:", $5}'
else
    echo "❌ n4_axis_data.pkl が存在しません"
fi

echo ""
echo "=== 最新のログ（最後の20行） ==="
LATEST_LOG=$(ls -t notebooks/feature_engineering_log*.txt 2>/dev/null | head -1)
if [ -n "$LATEST_LOG" ] && [ -f "$LATEST_LOG" ]; then
    echo "ログファイル: $LATEST_LOG"
    tail -20 "$LATEST_LOG"
else
    echo "ログファイルが見つかりません"
fi

