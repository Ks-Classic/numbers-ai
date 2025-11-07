#!/usr/bin/env python3
"""weekdayがNULLでdraw_dateがある行のweekdayを計算して更新"""

import csv
import sys
from pathlib import Path

# fetch_past_results.pyの関数をインポート
sys.path.insert(0, str(Path(__file__).parent))
from fetch_past_results import calculate_weekday

csv_file = Path(__file__).parent.parent / 'data' / 'past_results.csv'

# CSVファイルを読み込む
data = []
with open(csv_file, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        data.append(row)

# weekdayがNULLでdraw_dateがある行を修正
updated_count = 0
for row in data:
    if (row.get('weekday') == 'NULL' or not row.get('weekday')) and row.get('draw_date') and row.get('draw_date') != 'NULL':
        weekday = calculate_weekday(row['draw_date'])
        if weekday is not None:
            row['weekday'] = str(weekday)
            updated_count += 1

if updated_count > 0:
    # CSVファイルに保存
    fieldnames = ['round_number', 'draw_date', 'weekday', 'n3_winning', 'n4_winning', 'n3_rehearsal', 'n4_rehearsal']
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in data:
            csv_row = {}
            for key in fieldnames:
                value = row.get(key, '')
                csv_row[key] = value if value else 'NULL'
            writer.writerow(csv_row)
    print(f"✓ {updated_count}件のweekdayを更新しました")
else:
    print("更新する必要がありませんでした")

