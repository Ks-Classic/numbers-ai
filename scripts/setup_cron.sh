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
# 毎日 08:00 と 20:00 に実行 (半日に1回)
# ナンバーズの抽選は平日のみだが、祝日判定などが複雑なため毎日実行し、
# スクリプト側で抽選日かどうかを判定する運用とする
CRON_CMD="0 8,20 * * * cd $PROJECT_ROOT && $PYTHON_PATH scripts/production/auto_update_past_results.py >> logs/cron.log 2>&1"

echo "設定するcronジョブ:"
echo "$CRON_CMD"
echo ""

# 既存のcronジョブを確認
if crontab -l 2>/dev/null | grep -q "scripts/production/auto_update_past_results.py"; then
    echo "既存のcronジョブが見つかりました。"
    # 自動的に更新する（ユーザーの手間を省くため）
    # 既存のジョブを削除
    crontab -l 2>/dev/null | grep -v "scripts/production/auto_update_past_results.py" | crontab -
    echo "既存のジョブを更新しました。"
fi

# 新しいcronジョブを追加
(crontab -l 2>/dev/null; echo "$CRON_CMD") | crontab -

echo "✓ cronジョブを設定しました。"
echo ""
echo "設定内容:"
crontab -l | grep "scripts/production/auto_update_past_results.py"
echo ""
echo "注意: WSL環境では、cronサービスが起動していない場合があります。"
echo "以下のコマンドでcronサービスを起動してください:"
echo "  sudo service cron start"
echo ""
echo "cronサービスが自動起動するように設定するには:"
echo "  sudo systemctl enable cron"
echo ""
