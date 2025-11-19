#!/bin/bash
# 古いXGBoostモデルファイルと評価結果ファイルを削除するスクリプト

cd /home/ykoha/numbers-ai

echo "=== 削除対象ファイルの確認 ==="
echo ""
echo "【古いXGBoostモデルファイル（8ファイル）】"
ls -lh data/models/n3_axis.pkl data/models/n4_axis.pkl \
     data/models/n3_axis_tuned.pkl data/models/n4_axis_tuned.pkl \
     data/models/n3_box_comb.pkl data/models/n3_straight_comb.pkl \
     data/models/n4_box_comb.pkl data/models/n4_straight_comb.pkl 2>/dev/null | awk '{print "  " $9 " (" $5 ")"}'

echo ""
echo "【古い評価結果ファイル（3ファイル）】"
ls -lh data/models/evaluation_results.pkl \
     data/models/evaluation_results_axis.pkl \
     data/models/evaluation_results_combination.pkl 2>/dev/null | awk '{print "  " $9 " (" $5 ")"}'

echo ""
echo "【保持するファイル】"
echo "  - n3_axis_data.pkl (新しい軸数字予測データ)"
echo "  - n4_axis_data.pkl (新しい軸数字予測データ)"
echo "  - n3_box_comb_data.pkl (組み合わせ予測データ、再生成予定)"
echo "  - n3_straight_comb_data.pkl (組み合わせ予測データ、再生成予定)"
echo "  - n4_box_comb_data.pkl (組み合わせ予測データ、再生成予定)"
echo "  - n4_straight_comb_data.pkl (組み合わせ予測データ、再生成予定)"

echo ""
read -p "これらのファイルを削除しますか？ (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "削除中..."
    rm -f data/models/n3_axis.pkl
    rm -f data/models/n4_axis.pkl
    rm -f data/models/n3_axis_tuned.pkl
    rm -f data/models/n4_axis_tuned.pkl
    rm -f data/models/n3_box_comb.pkl
    rm -f data/models/n3_straight_comb.pkl
    rm -f data/models/n4_box_comb.pkl
    rm -f data/models/n4_straight_comb.pkl
    rm -f data/models/evaluation_results.pkl
    rm -f data/models/evaluation_results_axis.pkl
    rm -f data/models/evaluation_results_combination.pkl
    echo "✅ 削除完了"
else
    echo "削除をキャンセルしました"
fi

