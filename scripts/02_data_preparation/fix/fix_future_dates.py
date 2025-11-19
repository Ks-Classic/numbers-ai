#!/usr/bin/env python3
"""weekdayがNULLの行の日付を修正（未来の日付をみずほ銀行から取得）"""

import csv
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))
from fetch_past_results import fetch_mizuhobank_csv, parse_mizuhobank_csv, calculate_weekday

csv_file = Path(__file__).parent.parent / 'data' / 'past_results.csv'

# CSVファイルを読み込む
data = []
with open(csv_file, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        data.append(row)

# weekdayがNULLで、draw_dateが未来の日付（2025年以降）の行を修正
updated_count = 0
for row in data:
    weekday_val = row.get('weekday', '').strip()
    draw_date_val = row.get('draw_date', '').strip()
    
    if (weekday_val == 'NULL' or not weekday_val) and draw_date_val and draw_date_val != 'NULL':
        try:
            date_obj = datetime.strptime(draw_date_val, '%Y-%m-%d')
            # 2025年以降の日付は間違っている可能性が高い
            if date_obj.year >= 2025:
                round_num = int(row['round_number'])
                print(f"第{round_num}回の日付が未来の日付です: {draw_date_val}。みずほ銀行から取得します...")
                
                # みずほ銀行から取得
                csv_content = fetch_mizuhobank_csv(round_num)
                if csv_content:
                    n3, n4, correct_date = parse_mizuhobank_csv(csv_content, round_num)
                    if correct_date:
                        row['draw_date'] = correct_date
                        weekday = calculate_weekday(correct_date)
                        if weekday is not None:
                            row['weekday'] = str(weekday)
                        else:
                            row['weekday'] = 'NULL'
                        print(f"  ✓ 修正: {draw_date_val} → {correct_date}, weekday={weekday}")
                        updated_count += 1
                    else:
                        print(f"  ⚠ 日付が取得できませんでした")
                else:
                    print(f"  ⚠ CSVファイルが取得できませんでした")
        except (ValueError, TypeError):
            pass

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
    print(f"\n✓ {updated_count}件の日付を修正しました")
else:
    print("修正する必要がありませんでした")

