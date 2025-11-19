#!/usr/bin/env python3
"""
過去データ自動更新スクリプト

抽選日判定を行い、必要に応じてpast_results.csvを更新します。
cronジョブから実行されることを想定しています。

使い方:
    python3 auto_update_past_results.py

環境変数:
    GEMINI_API_KEY: Gemini APIキー（オプション）
    SERP_API_KEY: SerpAPIキー（オプション）
"""

import sys
import os
from pathlib import Path
from datetime import datetime

# プロジェクトルートのパスを設定
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.append(str(PROJECT_ROOT / 'core'))

# 環境変数からAPIキーを読み込み
try:
    from dotenv import load_dotenv
    load_dotenv(PROJECT_ROOT / '.env.local')
except ImportError:
    pass  # dotenvがなくても動作するようにする

from scripts.production.fetch_past_results import is_draw_day, main as fetch_main
import subprocess
import logging

# ログディレクトリを作成
LOG_DIR = PROJECT_ROOT / 'logs'
LOG_DIR.mkdir(exist_ok=True)

# ログ設定
log_file = LOG_DIR / f"data_update_{datetime.now().strftime('%Y-%m-%d')}.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


def main():
    """メイン処理"""
    logger.info("=" * 80)
    logger.info("過去データ自動更新スクリプト開始")
    logger.info("=" * 80)
    
    # 抽選日判定
    today = datetime.now()
    logger.info(f"実行日時: {today.strftime('%Y-%m-%d %H:%M:%S')}")
    
    if not is_draw_day(today):
        logger.info(f"今日は抽選日ではありません（{today.strftime('%Y年%m月%d日 %A')}）。スキップします。")
        return 0
    
    logger.info("✓ 抽選日を確認しました。データ更新を実行します。")
    
    # fetch_past_results.pyを実行
    try:
        script_path = PROJECT_ROOT / 'scripts' / 'production' / 'fetch_past_results.py'
        
        # Pythonインタープリターのパスを取得
        python = sys.executable
        
        # スクリプトを実行（最新の1回分のみ取得してマージ）
        logger.info(f"データ取得スクリプトを実行中: {script_path}")
        result = subprocess.run(
            [python, str(script_path), '--merge'],  # 最新の1回分のみ取得して既存CSVとマージ
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            encoding='utf-8'
        )
        
        # 標準出力とエラー出力をログに記録
        if result.stdout:
            logger.info("標準出力:")
            for line in result.stdout.split('\n'):
                if line.strip():
                    logger.info(f"  {line}")
        
        if result.stderr:
            logger.warning("エラー出力:")
            for line in result.stderr.split('\n'):
                if line.strip():
                    logger.warning(f"  {line}")
        
        if result.returncode == 0:
            logger.info("✓ データ更新が完了しました")
            return 0
        else:
            logger.error(f"✗ データ更新に失敗しました（終了コード: {result.returncode}）")
            return 1
            
    except Exception as e:
        logger.error(f"✗ データ更新中にエラーが発生しました: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
