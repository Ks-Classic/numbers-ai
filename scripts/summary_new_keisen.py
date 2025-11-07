#!/usr/bin/env python3
"""
新しく生成されたkeisen_master_new.jsonのサマリーを作成
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
n3_patterns = 0
n4_patterns = 0
n3_non_empty = 0
n4_non_empty = 0

for n_type in ['n3', 'n4']:
    for column in keisen_new[n_type].keys():
        for prev2 in keisen_new[n_type][column].keys():
            for prev in keisen_new[n_type][column][prev2].keys():
                predictions = keisen_new[n_type][column][prev2][prev]
                total_patterns += 1
                if n_type == 'n3':
                    n3_patterns += 1
                else:
                    n4_patterns += 1
                    
                if len(predictions) > 0:
                    non_empty_patterns += 1
                    if n_type == 'n3':
                        n3_non_empty += 1
                    else:
                        n4_non_empty += 1
                    digit_count_distribution[len(predictions)] += 1

print('=' * 60)
print('新しく生成されたkeisen_master_new.jsonのサマリー')
print('=' * 60)
print()
print(f'データ範囲: 4801-6850回（2,025行）')
print()
print(f'総パターン数: {total_patterns}')
print(f'  - N3: {n3_patterns}パターン')
print(f'  - N4: {n4_patterns}パターン')
print()
print(f'空でないパターン数: {non_empty_patterns}')
print(f'  - N3: {n3_non_empty}パターン')
print(f'  - N4: {n4_non_empty}パターン')
print()
print('予測出目の桁数分布:')
for digit_count in sorted(digit_count_distribution.keys()):
    count = digit_count_distribution[digit_count]
    percentage = count / non_empty_patterns * 100 if non_empty_patterns > 0 else 0
    print(f'  {digit_count}桁: {count}パターン ({percentage:.1f}%)')
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
print(f'既存: データ範囲=1340-6391回, 総パターン数={old_total_patterns}, 空でないパターン数={old_non_empty_patterns}')
print(f'新規: データ範囲=4801-6850回, 総パターン数={total_patterns}, 空でないパターン数={non_empty_patterns}')
print()
print('既存のkeisen_master.jsonの予測出目の桁数分布:')
for digit_count in sorted(old_digit_count_distribution.keys()):
    count = old_digit_count_distribution[digit_count]
    percentage = count / old_non_empty_patterns * 100 if old_non_empty_patterns > 0 else 0
    print(f'  {digit_count}桁: {count}パターン ({percentage:.1f}%)')
print()

print('=' * 60)
print('生成完了')
print('=' * 60)
print()
print('新しく生成されたkeisen_master_new.jsonは、既存のkeisen_master.jsonと同じルール')
print('「予測出目の最小出現回数 >= 除外された数字の最大出現回数」を適用して生成されました。')
print()
print('データ範囲が異なるため（既存: 1340-6391回、新規: 4801-6850回）、')
print('出現回数の分布が異なり、予測出目の桁数も異なります。')
print()
print('ファイル: data/keisen_master_new.json')

