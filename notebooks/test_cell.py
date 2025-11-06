#!/usr/bin/env python3
"""特定のセルをテストするためのユーティリティ"""

import json
import sys
from pathlib import Path

def extract_cell_code(notebook_path: str, cell_index: int) -> str:
    """Notebookから特定のセルコードを抽出"""
    with open(notebook_path, 'r', encoding='utf-8') as f:
        nb = json.load(f)
    
    if cell_index >= len(nb['cells']):
        raise ValueError(f"セルインデックス {cell_index} は範囲外です（総セル数: {len(nb['cells'])}）")
    
    cell = nb['cells'][cell_index]
    if cell.get('cell_type') != 'code':
        raise ValueError(f"セル {cell_index} はコードセルではありません")
    
    return ''.join(cell.get('source', []))

def test_cell(notebook_path: str, cell_index: int, setup_code: str = ""):
    """特定のセルを実行してテスト"""
    code = extract_cell_code(notebook_path, cell_index)
    
    # セットアップコードとセルコードを結合
    full_code = setup_code + "\n\n" + code
    
    # グローバル名前空間を作成
    globals_dict = {
        '__file__': notebook_path,
        '__name__': '__main__'
    }
    
    try:
        exec(full_code, globals_dict)
        print(f"✅ セル {cell_index} の実行成功")
        return True
    except Exception as e:
        print(f"❌ セル {cell_index} の実行失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("使用方法: python test_cell.py <notebook_path> <cell_index>")
        print("例: python test_cell.py notebooks/03_feature_engineering.ipynb 8")
        sys.exit(1)
    
    notebook_path = sys.argv[1]
    cell_index = int(sys.argv[2])
    
    # 基本的なセットアップコード（必要に応じて拡張）
    setup_code = """
import pandas as pd
import numpy as np
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import warnings
from itertools import product
warnings.filterwarnings('ignore')

# プロジェクトルートのパスを設定
PROJECT_ROOT = Path.cwd()
DATA_DIR = PROJECT_ROOT / 'data'

# モジュールをインポート
import sys
sys.path.append(str(PROJECT_ROOT / 'notebooks'))
from chart_generator import (
    load_keisen_master,
    generate_chart,
    Pattern,
    Target
)
from feature_extractor import (
    extract_digit_features,
    extract_combination_features,
    add_pattern_id_features,
    features_to_vector,
    get_rehearsal_positions
)
"""
    
    test_cell(notebook_path, cell_index, setup_code)

