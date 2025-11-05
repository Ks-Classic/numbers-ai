"""
FastAPIサーバーの起動スクリプト
"""

import uvicorn
import sys
from pathlib import Path

# プロジェクトルートのパスを設定（reload時のサブプロセスでも動作するように）
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / 'notebooks'))

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # 開発時のみ有効化
        log_level="info",
        reload_dirs=[str(Path(__file__).resolve().parent)]  # apiディレクトリのみ監視
    )

