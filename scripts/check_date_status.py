#!/usr/bin/env python3
"""データの状態を確認"""

import csv
from pathlib import Path

csv_file = Path(__file__).parent.parent / 'data' / 'past_results.csv'
with open(csv_file, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    data = list(reader)

print(f'総件数: {len(data)}件')
print(f'\ndraw_dateの状態:')
null_dates = [r for r in data if not r.get('draw_date') or r.get('draw_date') == 'NULL']
print(f'  NULL: {len(null_dates)}件')

# 2025年以降の日付を確認
future_dates = []
for r in data:
    date = r.get('draw_date', '')
    if date and date != 'NULL' and date.startswith('2025'):
        future_dates.append((int(r['round_number']), date))

if future_dates:
    print(f'\n2025年以降の日付: {len(future_dates)}件')
    print('  最初の5件:')
    for r, d in future_dates[:5]:
        print(f'    第{r}回: {d}')
else:
    print('\n2025年以降の日付: 0件')

# 進捗ファイルの確認
progress_file = Path(__file__).parent.parent / 'data' / '.date_update_progress.txt'
if progress_file.exists():
    with open(progress_file, 'r', encoding='utf-8') as f:
        processed = [int(line.strip()) for line in f if line.strip().isdigit()]
    print(f'\n進捗ファイル: {len(processed)}件処理済み')
    remaining = [int(r['round_number']) for r in data if int(r['round_number']) not in processed]
    print(f'残り: {len(remaining)}件')
    if remaining:
        print(f'  最初の10件: {remaining[:10]}')

