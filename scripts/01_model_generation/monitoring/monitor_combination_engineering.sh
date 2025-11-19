#!/bin/bash
# 組み合わせ予測データ生成の実行状況を監視するスクリプト

cd /home/ykoha/numbers-ai

echo "=== 組み合わせ予測データ生成実行状況 ==="
PROCESS=$(ps aux | grep '[r]un_03_feature_engineering_combination_only.py')
if [ -n "$PROCESS" ]; then
    echo "✅ 実行中"
    echo "$PROCESS"
else
    echo "❌ 実行されていません"
fi

echo ""
echo "=== データファイルの状況 ==="
for file in n3_box_comb_data.pkl n3_straight_comb_data.pkl n4_box_comb_data.pkl n4_straight_comb_data.pkl; do
    if [ -f "data/models/$file" ]; then
        echo "✅ $file が存在します"
        ls -lh "data/models/$file" | awk '{print "  更新時刻:", $6, $7, $8, "サイズ:", $5}'
        
        # ファイルの更新時刻を確認
        FILE_TIME=$(stat -c %Y "data/models/$file" 2>/dev/null)
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
        echo "❌ $file が存在しません"
    fi
done

echo ""
echo "=== 最新のログ（最後の20行） ==="
LATEST_LOG="notebooks/combination_engineering_log.txt"
if [ -f "$LATEST_LOG" ]; then
    echo "ログファイル: $LATEST_LOG"
    tail -20 "$LATEST_LOG"
else
    echo "ログファイルが見つかりません"
fi

