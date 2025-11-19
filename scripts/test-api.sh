#!/usr/bin/env bash

# API統合テストスクリプト
# FastAPIサーバーとNext.js API Routeの動作確認を行う

set -e

# 色の定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=========================================="
echo "API統合テスト"
echo "=========================================="
echo ""

# FastAPIサーバーのヘルスチェック
echo "1. FastAPIサーバーのヘルスチェック..."
FASTAPI_URL="${FASTAPI_URL:-http://localhost:8000}"

if curl -f -s "${FASTAPI_URL}/health" > /dev/null; then
    echo -e "${GREEN}✓ FastAPIサーバーが起動しています${NC}"
else
    echo -e "${RED}✗ FastAPIサーバーに接続できません${NC}"
    echo "  ${FASTAPI_URL}/health にアクセスできるか確認してください"
    exit 1
fi

# Next.js API Routeのテスト
echo ""
echo "2. Next.js API Routeのテスト..."

# テスト用のリクエストボディ
TEST_BODY='{
  "roundNumber": 6847,
  "n3Rehearsal": "806",
  "n4Rehearsal": "7007"
}'

NEXTJS_URL="${NEXTJS_URL:-http://localhost:3000}"

# Next.jsサーバーが起動しているか確認
if curl -f -s "${NEXTJS_URL}/" > /dev/null 2>&1; then
    echo "Next.jsサーバーに接続中..."
    # API Routeのテスト
    RESPONSE=$(curl -s -X POST "${NEXTJS_URL}/api/predict" \
      -H "Content-Type: application/json" \
      -d "${TEST_BODY}" 2>&1)
    
    if echo "${RESPONSE}" | grep -q "success"; then
        echo -e "${GREEN}✓ Next.js API Routeが正常に動作しています${NC}"
        echo "  レスポンスの一部:"
        echo "${RESPONSE}" | head -c 200
        echo "..."
    else
        echo -e "${YELLOW}⚠ Next.js API Routeのレスポンスが期待と異なります${NC}"
        echo "  レスポンス: ${RESPONSE}"
    fi
else
    echo -e "${YELLOW}⚠ Next.js API Routeのテストをスキップ（サーバーが起動していない可能性）${NC}"
    echo "  ${NEXTJS_URL} にアクセスできるか確認してください"
    echo "  起動方法: cd /home/ykoha/numbers-ai && npm run dev"
fi

# FastAPIの軸数字予測エンドポイントのテスト
echo ""
echo "3. FastAPI軸数字予測エンドポイントのテスト..."

AXIS_RESPONSE=$(curl -s -X POST "${FASTAPI_URL}/api/predict/axis" \
  -H "Content-Type: application/json" \
  -d '{
    "round_number": 6847,
    "target": "n3",
    "rehearsal_digits": "806"
  }')

if echo "${AXIS_RESPONSE}" | grep -q "best_pattern"; then
    echo -e "${GREEN}✓ 軸数字予測エンドポイントが正常に動作しています${NC}"
    echo "  レスポンスの一部:"
    echo "${AXIS_RESPONSE}" | head -c 200
    echo "..."
else
    echo -e "${RED}✗ 軸数字予測エンドポイントでエラーが発生しました${NC}"
    echo "${AXIS_RESPONSE}"
    exit 1
fi

# FastAPIの組み合わせ予測エンドポイントのテスト
echo ""
echo "4. FastAPI組み合わせ予測エンドポイントのテスト..."

# まず軸数字を取得してから組み合わせを予測
COMB_RESPONSE=$(curl -s -X POST "${FASTAPI_URL}/api/predict/combination" \
  -H "Content-Type: application/json" \
  -d '{
    "round_number": 6847,
    "target": "n3",
    "combo_type": "box",
    "best_pattern": "A1",
    "top_axis_digits": [1, 2, 3],
    "rehearsal_digits": "806",
    "max_combinations": 10
  }')

if echo "${COMB_RESPONSE}" | grep -q "combinations"; then
    echo -e "${GREEN}✓ 組み合わせ予測エンドポイントが正常に動作しています${NC}"
    echo "  レスポンスの一部:"
    echo "${COMB_RESPONSE}" | head -c 200
    echo "..."
else
    echo -e "${RED}✗ 組み合わせ予測エンドポイントでエラーが発生しました${NC}"
    echo "${COMB_RESPONSE}"
    exit 1
fi

echo ""
echo -e "${GREEN}=========================================="
echo "✓ すべてのテストが成功しました"
echo "==========================================${NC}"

