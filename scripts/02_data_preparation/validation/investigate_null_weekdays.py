#!/usr/bin/env python3
"""weekdayがNULLの原因を調査"""

import csv
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))
from fetch_past_results import calculate_weekday

csv_file = Path(__file__).parent.parent / 'data' / 'past_results.csv'

null_weekdays = []
with open(csv_file, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        weekday_val = row.get('weekday', '').strip()
        draw_date_val = row.get('draw_date', '').strip()
        
        if (weekday_val == 'NULL' or not weekday_val) and draw_date_val and draw_date_val != 'NULL':
            round_num = int(row['round_number'])
            calculated_weekday = calculate_weekday(draw_date_val)
            
            null_weekdays.append({
                'round_number': round_num,
                'draw_date': draw_date_val,
                'weekday_raw': repr(weekday_val),
                'calculated_weekday': calculated_weekday,
                'n3_winning': row.get('n3_winning', ''),
            })
            
            if len(null_weekdays) <= 10:
                print(f"第{round_num}回:")
                print(f"  draw_date: {repr(draw_date_val)}")
                print(f"  weekday (raw): {repr(weekday_val)}")
                print(f"  calculated_weekday: {calculated_weekday}")
                print(f"  n3_winning: {row.get('n3_winning', '')}")
                print()

print(f"\n合計: {len(null_weekdays)}件")
print(f"\n原因分析:")
print(f"  - calculated_weekdayがNoneの件数: {sum(1 for x in null_weekdays if x['calculated_weekday'] is None)}件")
print(f"  - calculated_weekdayが設定可能な件数: {sum(1 for x in null_weekdays if x['calculated_weekday'] is not None)}件")

if null_weekdays:
    # calculated_weekdayがNoneのものを確認
    none_cases = [x for x in null_weekdays if x['calculated_weekday'] is None]
    if none_cases:
        print(f"\ncalculated_weekdayがNoneのケース（最初の5件）:")
        for case in none_cases[:5]:
            print(f"  第{case['round_number']}回: draw_date={repr(case['draw_date'])}")

