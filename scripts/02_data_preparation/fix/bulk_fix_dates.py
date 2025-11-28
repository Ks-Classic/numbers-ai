#!/usr/bin/env python3
"""
すべての日付を一括でみずほ銀行から取得して修正するスクリプト
並列処理で高速化
"""

import csv
import re
import sys
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

try:
    import requests
except ImportError:
    print("エラー: requestsがインストールされていません")
    sys.exit(1)

CSV_FILE = Path(__file__).parent.parent.parent.parent / 'data' / 'past_results.csv'


def parse_japanese_date(date_str: str) -> str:
    match = re.search(r'(平成|令和|昭和)(\d+|元)年(\d{1,2})月(\d{1,2})日', date_str)
    if not match:
        return None
    
    era, year_str, month, day = match.group(1), match.group(2), int(match.group(3)), int(match.group(4))
    
    if era == '平成':
        year = 1988 + (1 if year_str == '元' else int(year_str))
    elif era == '令和':
        year = 2018 + (1 if year_str == '元' else int(year_str))
    elif era == '昭和':
        year = 1925 + (1 if year_str == '元' else int(year_str))
    else:
        return None
    
    return f"{year}-{month:02d}-{day:02d}"


def calculate_weekday(draw_date: str) -> int:
    if not draw_date or draw_date == 'NULL':
        return None
    try:
        date_obj = datetime.strptime(draw_date, '%Y-%m-%d')
        weekday = date_obj.weekday()
        return weekday if weekday < 5 else None
    except:
        return None


def fetch_date(round_number: int, session: requests.Session) -> tuple:
    csv_url = f'https://www.mizuhobank.co.jp/retail/takarakuji/numbers/csv/A100{round_number:04d}.CSV'
    try:
        response = session.get(csv_url, timeout=30)
        if response.status_code != 200:
            return round_number, None
        response.encoding = 'shift_jis'
        lines = response.text.split('\n')
        if len(lines) >= 2:
            return round_number, parse_japanese_date(lines[1])
        return round_number, None
    except:
        return round_number, None


def main():
    print("=" * 60)
    print("全日付を一括修正するスクリプト")
    print("=" * 60)
    
    # データ読み込み
    data = []
    with open(CSV_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for row in reader:
            data.append(row)
    
    print(f"✓ {len(data)}件のデータを読み込みました")
    
    # 日付の重複をチェック
    date_counts = {}
    for row in data:
        d = row.get('draw_date', '')
        if d and d != 'NULL':
            date_counts[d] = date_counts.get(d, 0) + 1
    
    duplicates = {d for d, c in date_counts.items() if c > 1}
    if duplicates:
        print(f"⚠ 重複日付: {duplicates}")
    
    # 全回号を修正対象にする（連鎖的なズレを解消するため）
    rounds_to_fix = [int(row['round_number']) for row in data]
    
    if not rounds_to_fix:
        print("✓ 修正が必要なデータはありません")
        return
    
    print(f"🔧 修正対象: {len(rounds_to_fix)}件")
    
    # セッション作成
    session = requests.Session()
    session.headers.update({'User-Agent': 'Mozilla/5.0'})
    
    # 並列取得
    print("📅 みずほ銀行から日付を取得中...")
    results = {}
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(fetch_date, r, session): r for r in rounds_to_fix}
        done = 0
        for future in as_completed(futures):
            done += 1
            if done % 50 == 0:
                print(f"   {done}/{len(rounds_to_fix)}")
            round_num, date = future.result()
            if date:
                results[round_num] = date
    
    session.close()
    
    # データ更新
    updated = 0
    for row in data:
        round_num = int(row['round_number'])
        if round_num in results:
            new_date = results[round_num]
            old_date = row.get('draw_date', '')
            if old_date != new_date:
                row['draw_date'] = new_date
                updated += 1
            
            weekday = calculate_weekday(new_date)
            row['weekday'] = str(weekday) if weekday is not None else 'NULL'
    
    print(f"✓ 日付を更新: {updated}件")
    
    # 保存
    with open(CSV_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in data:
            csv_row = {k: row.get(k, '') or 'NULL' for k in fieldnames}
            writer.writerow(csv_row)
    
    print(f"✓ 保存完了: {CSV_FILE}")


if __name__ == "__main__":
    main()

