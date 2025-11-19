#!/usr/bin/env python3
"""
新しく生成されたkeisen_master_new.jsonを確認
"""

import json
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"

# 新しく生成されたkeisen_master_new.jsonを確認
with open(DATA_DIR / "keisen_master_new.json", 'r', encoding='utf-8') as f:
    keisen_new = json.load(f)

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

print(f'新しく生成されたkeisen_master_new.jsonで、予測出目が4桁以上のパターン数: {len(long_predictions)}')
print()
print('上位10件:')
for i, item in enumerate(sorted(long_predictions, key=lambda x: x['count'], reverse=True)[:10], 1):
    print(f'{i}. {item["n_type"].upper()} {item["column"]} - 前々回={item["prev2"]}, 前回={item["prev"]}: {item["count"]}桁 - {item["predictions"]}')

