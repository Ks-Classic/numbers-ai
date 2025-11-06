#!/usr/bin/env python3
import json

with open('notebooks/03_feature_engineering.ipynb', 'r', encoding='utf-8') as f:
    nb = json.load(f)

# Cell 8の内容を確認
cell8_source = nb['cells'][8]['source']
print(f'Cell 8の元の行数: {len(cell8_source)}')

# 重複部分を特定（最初のprint文の後の行を確認）
new_source = []
found_first_print = False
found_duplicate = False

for i, line in enumerate(cell8_source):
    if 'print("組み合わせ予測モデルの学習データを生成中...")' in line:
        if not found_first_print:
            found_first_print = True
            new_source.append(line)
        else:
            # 2回目の出現 = 重複の開始
            found_duplicate = True
            print(f'重複開始位置: 行 {i+1}')
            break
    elif not found_duplicate:
        new_source.append(line)

print(f'重複削除後の行数: {len(new_source)}')
print(f'削除された行数: {len(cell8_source) - len(new_source)}')

# ファイルを更新
nb['cells'][8]['source'] = new_source

with open('notebooks/03_feature_engineering.ipynb', 'w', encoding='utf-8') as f:
    json.dump(nb, f, ensure_ascii=False, indent=1)

print('✅ 重複コードを削除しました')

