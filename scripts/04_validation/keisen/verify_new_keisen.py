#!/usr/bin/env python3
"""
新しく生成されたkeisen_master_new.jsonを確認
既存のルールに従っているか検証
"""

import json
from pathlib import Path
from collections import Counter

DATA_DIR = Path(__file__).parent.parent / "data"

# 新しく生成されたkeisen_master_new.jsonを確認
with open(DATA_DIR / "keisen_master_new.json", 'r', encoding='utf-8') as f:
    keisen_new = json.load(f)

# 予測出目の桁数分布を確認
digit_count_distribution = Counter()
total_patterns = 0
non_empty_patterns = 0

for n_type in ['n3', 'n4']:
    for column in keisen_new[n_type].keys():
        for prev2 in keisen_new[n_type][column].keys():
            for prev in keisen_new[n_type][column][prev2].keys():
                predictions = keisen_new[n_type][column][prev2][prev]
                total_patterns += 1
                if len(predictions) > 0:
                    non_empty_patterns += 1
                    digit_count_distribution[len(predictions)] += 1

print('=' * 60)
print('新しく生成されたkeisen_master_new.jsonの確認')
print('=' * 60)
print()
print(f'総パターン数: {total_patterns}')
print(f'空でないパターン数: {non_empty_patterns}')
print()
print('予測出目の桁数分布:')
for digit_count in sorted(digit_count_distribution.keys()):
    count = digit_count_distribution[digit_count]
    percentage = count / non_empty_patterns * 100 if non_empty_patterns > 0 else 0
    print(f'  {digit_count}桁: {count}パターン ({percentage:.1f}%)')
print()

# 予測出目が4桁以上のパターンを確認
long_predictions = []
for n_type in ['n3', 'n4']:
    for column in keisen_new[n_type].keys():
        for prev2 in keisen_new[n_type][column].keys():
            for prev in keisen_new[n_type][column][prev2].keys():
                predictions = keisen_new[n_type][column][prev2][prev]
                if len(predictions) >= 4:
                    long_predictions.append({
                        'n_type': n_type,
                        'column': column,
                        'prev2': prev2,
                        'prev': prev,
                        'predictions': predictions,
                        'count': len(predictions)
                    })

print(f'予測出目が4桁以上のパターン数: {len(long_predictions)}')
print()
print('上位10件（桁数が多い順）:')
for i, item in enumerate(sorted(long_predictions, key=lambda x: x['count'], reverse=True)[:10], 1):
    print(f'{i}. {item["n_type"].upper()} {item["column"]} - 前々回={item["prev2"]}, 前回={item["prev"]}: {item["count"]}桁')
    print(f'   予測出目: {item["predictions"]}')
print()

# 既存のkeisen_master.jsonと比較
with open(DATA_DIR / "keisen_master.json", 'r', encoding='utf-8') as f:
    keisen_old = json.load(f)

old_digit_count_distribution = Counter()
old_total_patterns = 0
old_non_empty_patterns = 0

for n_type in ['n3', 'n4']:
    for column in keisen_old[n_type].keys():
        for prev2 in keisen_old[n_type][column].keys():
            for prev in keisen_old[n_type][column][prev2].keys():
                predictions = keisen_old[n_type][column][prev2][prev]
                old_total_patterns += 1
                if len(predictions) > 0:
                    old_non_empty_patterns += 1
                    old_digit_count_distribution[len(predictions)] += 1

print('=' * 60)
print('既存のkeisen_master.jsonとの比較')
print('=' * 60)
print()
print(f'既存: 総パターン数={old_total_patterns}, 空でないパターン数={old_non_empty_patterns}')
print(f'新規: 総パターン数={total_patterns}, 空でないパターン数={non_empty_patterns}')
print()
print('既存のkeisen_master.jsonの予測出目の桁数分布:')
for digit_count in sorted(old_digit_count_distribution.keys()):
    count = old_digit_count_distribution[digit_count]
    percentage = count / old_non_empty_patterns * 100 if old_non_empty_patterns > 0 else 0
    print(f'  {digit_count}桁: {count}パターン ({percentage:.1f}%)')
print()

