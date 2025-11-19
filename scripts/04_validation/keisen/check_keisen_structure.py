#!/usr/bin/env python3
"""
検証ロジックの詳細確認
"""

import json

# keisen_master.jsonの構造を確認
with open('data/keisen_master.json', 'r', encoding='utf-8') as f:
    keisen = json.load(f)

print('=' * 60)
print('keisen_master.jsonの構造確認')
print('=' * 60)
print('keisen["n3"]["百の位"]["0"]["1"] =', keisen['n3']['百の位']['0']['1'])
print()
print('構造:')
print('  keisen["n3"]["百の位"][前回][前々回] = 予測出目')
print('  外側のキー("0"): 前回の数字')
print('  内側のキー("1"): 前々回の数字')
print()
print('つまり:')
print('  前回の百の位=0、前々回の百の位=1 のときの予測出目 = [3, 9, 5]')
print()

# 検証結果ファイルを確認
with open('data/keisen_master_verification.json', 'r', encoding='utf-8') as f:
    verification = json.load(f)

# N3百の位、前々回=0、前回=1のパターンを探す
print('=' * 60)
print('検証結果ファイルの確認')
print('=' * 60)
for item in verification:
    if item['n_type'] == 'n3' and item['column'] == '百の位' and item['prev'] == '0' and item['prev2'] == '1':
        print(f'prev (前回): {item["prev"]}')
        print(f'prev2 (前々回): {item["prev2"]}')
        print(f'keisen_predictions: {item["keisen_predictions"]}')
        print(f'actual_top_n: {item["actual_top_n"]}')
        print(f'actual_ranking: {item["actual_ranking"]}')
        print(f'total_samples: {item["total_samples"]}')
        print()
        print('検証ロジック:')
        print('  前回=0、前々回=1 のパターンで検証している')
        print('  → これは正しい')
        break

# 逆のパターンも確認
print('=' * 60)
print('逆パターンの確認（前回=1、前々回=0）')
print('=' * 60)
for item in verification:
    if item['n_type'] == 'n3' and item['column'] == '百の位' and item['prev'] == '1' and item['prev2'] == '0':
        print(f'prev (前回): {item["prev"]}')
        print(f'prev2 (前々回): {item["prev2"]}')
        print(f'keisen_predictions: {item["keisen_predictions"]}')
        print(f'actual_top_n: {item["actual_top_n"]}')
        print(f'actual_ranking: {item["actual_ranking"]}')
        print(f'total_samples: {item["total_samples"]}')
        print()
        print('keisen_master.json:')
        print(f'  keisen["n3"]["百の位"]["1"]["0"] = {keisen["n3"]["百の位"]["1"]["0"]}')
        break

