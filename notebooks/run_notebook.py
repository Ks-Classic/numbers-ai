#!/usr/bin/env python3
"""
Notebookを実行するスクリプト
"""
import json
import sys
from pathlib import Path

# Notebookファイルを読み込む
notebook_name = sys.argv[1] if len(sys.argv) > 1 else '01_data_preparation.ipynb'
notebook_path = Path(__file__).parent / notebook_name
with open(notebook_path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

# コードセルを抽出して実行
code_cells = [c for c in nb['cells'] if c['cell_type'] == 'code']
code_source = []

for i, cell in enumerate(code_cells):
    source = ''.join(cell['source'])
    if source.strip():
        code_source.append(f"# Cell {i}\n{source}")

# 全てのコードを実行
full_code = '\n'.join(code_source)
exec(full_code, {'__file__': str(notebook_path)})

