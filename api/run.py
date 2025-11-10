"""
FastAPIサーバーの起動スクリプト
"""

import uvicorn
import sys
import os
from pathlib import Path

# プロジェクトルートのパスを設定（reload時のサブプロセスでも動作するように）
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / 'notebooks'))
sys.path.insert(0, str(Path(__file__).resolve().parent))  # apiディレクトリをパスに追加

if __name__ == "__main__":
    # Cloud Runの$PORT環境変数を使用（デフォルト: 8000）
    port = int(os.environ.get('PORT', 8000))
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=True,  # 開発環境では有効化
        log_level="info",
    )

