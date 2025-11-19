#!/usr/bin/env python3
import json
import re
import sys

# package.jsonを読み込む
try:
    with open('package.json', 'r', encoding='utf-8') as f:
        content = f.read()
    
    print(f"ファイルサイズ: {len(content)} bytes")
    print(f"最初の100文字: {content[:100]}")
    
    # マージコンフリクトマーカーを検出
    if '<<<<<<< HEAD' in content:
        print("マージコンフリクトマーカーを検出しました")
        # マージコンフリクトマーカーを削除
        lines = content.split('\n')
        new_lines = []
        skip = False
        for line in lines:
            if '<<<<<<< HEAD' in line:
                skip = True
                continue
            if '=======' in line:
                skip = False
                continue
            if '>>>>>>>' in line:
                skip = False
                continue
            if not skip:
                new_lines.append(line)
        content = '\n'.join(new_lines)
    
    # JSONとして検証
    try:
        data = json.loads(content)
        # 正しいJSONとして保存
        with open('package.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print("package.jsonを修正しました")
        sys.exit(0)
    except json.JSONDecodeError as e:
        print(f"JSONエラー: {e}")
        print(f"エラー位置: 行 {e.lineno}, 列 {e.colno}")
        sys.exit(1)
        
except Exception as e:
    print(f"エラー: {e}")
    sys.exit(1)
