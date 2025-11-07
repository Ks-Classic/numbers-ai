#!/usr/bin/env python3
"""第6841回の日付をみずほ銀行から取得して修正"""

import csv
import sys
from pathlib import Path

# fetch_past_results.pyの関数をインポート
sys.path.insert(0, str(Path(__file__).parent))
from fetch_past_results import fetch_mizuhobank_csv, parse_mizuhobank_csv, calculate_weekday

csv_file = Path(__file__).parent.parent / 'data' / 'past_results.csv'

# CSVファイルを読み込む
data = []
with open(csv_file, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        data.append(row)

# 第6841回のデータを探す
found = False
for row in data:
    if int(row['round_number']) == 6841:
        if not row.get('draw_date') or row.get('draw_date') == 'NULL':
            print(f"第6841回の日付がNULLです。みずほ銀行から取得します...")
            
            # みずほ銀行から取得
            csv_content = fetch_mizuhobank_csv(6841)
            if csv_content:
                n3, n4, draw_date = parse_mizuhobank_csv(csv_content, 6841)
                if draw_date:
                    row['draw_date'] = draw_date
                    weekday = calculate_weekday(draw_date)
                    if weekday is not None:
                        row['weekday'] = str(weekday)
                    else:
                        row['weekday'] = 'NULL'
                    print(f"✓ 第6841回の日付を更新: {draw_date}, weekday={weekday}")
                    found = True
                else:
                    print(f"⚠ 第6841回の日付が取得できませんでした")
            else:
                print(f"⚠ 第6841回のCSVファイルが取得できませんでした")
        else:
            print(f"第6841回の日付は既に設定されています: {row.get('draw_date')}")
        break

if found:
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
    print(f"✓ CSVファイルを更新しました")
else:
    print("更新する必要がありませんでした")

