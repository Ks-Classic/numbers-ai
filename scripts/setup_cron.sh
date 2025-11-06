#!/bin/bash
# cronジョブ設定スクリプト
# WSL環境対応

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PYTHON_PATH="$(which python3)"

echo "=================================="
echo "cronジョブ設定スクリプト"
echo "=================================="
echo ""
echo "プロジェクトルート: $PROJECT_ROOT"
echo "Pythonパス: $PYTHON_PATH"
echo ""

# cronジョブを設定
CRON_CMD="0 15 * * 1-5 cd $PROJECT_ROOT && $PYTHON_PATH scripts/auto_update_past_results.py >> logs/cron.log 2>&1"

echo "設定するcronジョブ:"
echo "$CRON_CMD"
echo ""

# 既存のcronジョブを確認
if crontab -l 2>/dev/null | grep -q "auto_update_past_results.py"; then
    echo "既存のcronジョブが見つかりました。"
    read -p "既存のジョブを削除して新しく設定しますか？ (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        # 既存のジョブを削除
        crontab -l 2>/dev/null | grep -v "auto_update_past_results.py" | crontab -
        echo "既存のジョブを削除しました。"
    else
        echo "設定をキャンセルしました。"
        exit 0
    fi
fi

# 新しいcronジョブを追加
(crontab -l 2>/dev/null; echo "$CRON_CMD") | crontab -

echo "✓ cronジョブを設定しました。"
echo ""
echo "設定内容:"
crontab -l | grep "auto_update_past_results.py"
echo ""
echo "注意: WSL環境では、cronサービスが起動していない場合があります。"
echo "以下のコマンドでcronサービスを起動してください:"
echo "  sudo service cron start"
echo ""
echo "cronサービスが自動起動するように設定するには:"
echo "  sudo systemctl enable cron"
echo ""
echo "設定を確認するには:"
echo "  crontab -l"
echo ""
echo "cronジョブを削除するには:"
echo "  crontab -e"
echo "  (該当行を削除して保存)"
echo ""
