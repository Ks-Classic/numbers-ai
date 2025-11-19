#!/bin/bash
# 一時的な整理用スクリプトとドキュメントを削除するスクリプト

cd /home/ykoha/numbers-ai/scripts

echo "=== 一時的なファイルの削除 ==="
echo ""

# 整理用スクリプト（今回作成、一時的）
echo "【整理用スクリプトの削除】"
[ -f cleanup_old_files.sh ] && rm -f cleanup_old_files.sh && echo "  削除: cleanup_old_files.sh"
[ -f fix_import_paths.sh ] && rm -f fix_import_paths.sh && echo "  削除: fix_import_paths.sh"
[ -f reorganize_files.sh ] && rm -f reorganize_files.sh && echo "  削除: reorganize_files.sh"

# 整理計画・サマリー（整理完了したので不要）
echo ""
echo "【整理計画・サマリーの削除】"
[ -f REORGANIZATION_PLAN.md ] && rm -f REORGANIZATION_PLAN.md && echo "  削除: REORGANIZATION_PLAN.md"
[ -f REORGANIZATION_SUMMARY.md ] && rm -f REORGANIZATION_SUMMARY.md && echo "  削除: REORGANIZATION_SUMMARY.md"

# 重複ファイル（production/に移動済み）
echo ""
echo "【重複ファイルの削除】"
[ -f auto_update_past_results.py ] && rm -f auto_update_past_results.py && echo "  削除: auto_update_past_results.py (production/に移動済み)"

echo ""
echo "✅ 一時的なファイルの削除が完了しました"

