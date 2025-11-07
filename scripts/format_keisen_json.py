#!/usr/bin/env python3
"""
keisen_master_new.jsonの配列を1行に整形
"""

import json
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"

# JSONファイルを読み込む
with open(DATA_DIR / "keisen_master_new.json", 'r', encoding='utf-8') as f:
    data = json.load(f)

# カスタムJSONエンコーダーで配列を1行に整形
def format_json(obj, indent=0):
    """配列を1行に整形するカスタムフォーマッター"""
    if isinstance(obj, dict):
        if len(obj) == 0:
            return '{}'
        items = []
        for key, value in obj.items():
            formatted_value = format_json(value, indent + 2)
            items.append(f'{" " * indent}"{key}": {formatted_value}')
        closing_indent = max(0, indent - 2) if indent >= 2 else 0
        return '{\n' + ',\n'.join(items) + '\n' + ' ' * closing_indent + '}'
    elif isinstance(obj, list):
        if len(obj) == 0:
            return '[]'
        # 配列は1行にまとめる
        items = ', '.join(str(item) for item in obj)
        return f'[{items}]'
    elif isinstance(obj, str):
        return json.dumps(obj, ensure_ascii=False)
    else:
        return json.dumps(obj)

# 整形して保存
print('JSONを整形中...')
formatted_json = format_json(data, indent=2)

print('ファイルに書き込み中...')
with open(DATA_DIR / "keisen_master_new.json", 'w', encoding='utf-8') as f:
    f.write(formatted_json)

print('keisen_master_new.jsonを整形しました（配列を1行にまとめました）')

# 確認のため最初の数行を表示
with open(DATA_DIR / "keisen_master_new.json", 'r', encoding='utf-8') as f:
    lines = f.readlines()[:15]
    print('\n整形後の最初の15行:')
    for i, line in enumerate(lines, 1):
        print(f'{i:2}: {line.rstrip()}')
