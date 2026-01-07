#!/bin/bash
# GitHubリポジトリから最新のCSVデータを同期するスクリプト
# 使用方法: bash scripts/sync-github-data.sh
#
# プライベートリポジトリ対応のため、git pullを使用

set -e

# カラー出力
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

CSV_FILE="data/past_results.csv"

echo -e "${BLUE}📡 GitHubから最新データを確認中...${NC}"

# 現在のブランチを取得
CURRENT_BRANCH=$(git branch --show-current 2>/dev/null || echo "main")

# リモートの変更をフェッチ
if git fetch origin "$CURRENT_BRANCH" --quiet 2>/dev/null; then
    
    # CSVファイルに変更があるか確認
    LOCAL_HASH=$(git rev-parse HEAD:$CSV_FILE 2>/dev/null || echo "")
    REMOTE_HASH=$(git rev-parse origin/$CURRENT_BRANCH:$CSV_FILE 2>/dev/null || echo "")
    
    if [ "$LOCAL_HASH" = "$REMOTE_HASH" ]; then
        if [ -f "$CSV_FILE" ]; then
            LINE_COUNT=$(wc -l < "$CSV_FILE")
            echo -e "${GREEN}✅ ローカルデータは最新です (${LINE_COUNT} 行)${NC}"
        else
            echo -e "${GREEN}✅ リモートと同期済みです${NC}"
        fi
    else
        # 変更がある場合、ローカルの変更を確認
        if git diff --quiet HEAD -- "$CSV_FILE" 2>/dev/null; then
            # ローカルに変更がない場合、CSVファイルのみをプル
            echo -e "${YELLOW}🔄 新しいデータが見つかりました。同期中...${NC}"
            
            # stashしてからプル
            STASH_NEEDED=false
            if ! git diff --quiet 2>/dev/null || ! git diff --cached --quiet 2>/dev/null; then
                STASH_NEEDED=true
                git stash push --quiet -m "sync-data-temp"
            fi
            
            # マージを実行
            if git merge origin/$CURRENT_BRANCH --quiet --no-edit 2>/dev/null; then
                if [ -f "$CSV_FILE" ]; then
                    LINE_COUNT=$(wc -l < "$CSV_FILE")
                    # 最新の回号を表示
                    LATEST_ROUND=$(head -2 "$CSV_FILE" | tail -1 | cut -d',' -f1)
                    echo -e "${GREEN}🔄 データを更新しました (${LINE_COUNT} 行, 最新: 第${LATEST_ROUND}回)${NC}"
                else
                    echo -e "${GREEN}✅ 同期完了${NC}"
                fi
            else
                echo -e "${RED}❌ マージに失敗しました。手動で 'git pull' を実行してください。${NC}"
                git merge --abort 2>/dev/null || true
            fi
            
            # stashを戻す
            if [ "$STASH_NEEDED" = true ]; then
                git stash pop --quiet 2>/dev/null || true
            fi
        else
            # ローカルにCSVの変更がある場合はスキップ
            echo -e "${YELLOW}⚠️  ローカルに未コミットの変更があります。'git pull' を手動で実行してください。${NC}"
        fi
    fi
else
    # フェッチに失敗した場合（オフラインなど）
    if [ -f "$CSV_FILE" ]; then
        LINE_COUNT=$(wc -l < "$CSV_FILE")
        echo -e "${YELLOW}⚠️  オフラインです。ローカルデータを使用します (${LINE_COUNT} 行)${NC}"
    else
        echo -e "${YELLOW}⚠️  オフラインです。${NC}"
    fi
    exit 0  # エラーにはしない
fi
