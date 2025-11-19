#!/usr/bin/env python3
"""すべてのdraw_dateをみずほ銀行から取得して更新（バッチ処理で進捗保存）"""

import csv
import sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import requests

sys.path.insert(0, str(Path(__file__).parent))
from fetch_past_results import fetch_mizuhobank_csv, parse_mizuhobank_csv, calculate_weekday, find_mizuhobank_pages, fetch_page, parse_mizuhobank_table
from bs4 import BeautifulSoup

csv_file = Path(__file__).parent.parent / 'data' / 'past_results.csv'
progress_file = Path(__file__).parent.parent / 'data' / '.date_update_progress.txt'

# CSVファイルを読み込む
print("📥 CSVファイルを読み込み中...")
data = []
with open(csv_file, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        data.append(row)

print(f"✓ {len(data)}件のデータを読み込みました")

# 進捗ファイルから処理済みの回号を読み込む
processed_rounds = set()
if progress_file.exists():
    with open(progress_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line.isdigit():
                processed_rounds.add(int(line))
    print(f"✓ 進捗ファイルから{len(processed_rounds)}件の処理済み回号を読み込みました")

# セッションを作成（接続の再利用）
session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
})

def fetch_date_for_round(round_num: int) -> tuple[int, str | None]:
    """1回分の日付をみずほ銀行から取得（並列処理用）"""
    # まずCSVファイルから取得を試行
    csv_content = fetch_mizuhobank_csv(round_num, session=session)
    if csv_content:
        _, _, draw_date = parse_mizuhobank_csv(csv_content, round_num)
        if draw_date:
            return round_num, draw_date
    
    # CSVファイルが取得できない場合、HTMLページから取得を試行（4800回以前のみ）
    if round_num <= 4800:
        # HTMLページのURLを生成
        html_pages = find_mizuhobank_pages(round_num, round_num)
        if html_pages:
            html_content = fetch_page(html_pages[0])
            if html_content:
                soup = BeautifulSoup(html_content, 'html.parser')
                page_n4_data, page_n3_data = parse_mizuhobank_table(soup, max_round=round_num)
                if round_num in page_n4_data:
                    draw_date = page_n4_data[round_num].get('draw_date')
                    if draw_date:
                        return round_num, draw_date
                if round_num in page_n3_data:
                    draw_date = page_n3_data[round_num].get('draw_date')
                    if draw_date:
                        return round_num, draw_date
    
    return round_num, None

# 処理対象の回号を決定（未処理のもののみ）
round_numbers = [int(row['round_number']) for row in data]
round_numbers_to_process = [r for r in round_numbers if r not in processed_rounds]

if not round_numbers_to_process:
    print("✓ すべての回号の処理が完了しています")
    sys.exit(0)

print(f"\n📅 {len(round_numbers_to_process)}件の回号について、みずほ銀行から日付を取得します...")
print(f"   ⚡ 並列処理で高速化します（最大8並列）")

total_rounds = len(round_numbers_to_process)
updated_count = 0
failed_count = 0
completed_count = 0

max_workers = 8
save_interval = 100  # 100件ごとにCSVと進捗を保存

with ThreadPoolExecutor(max_workers=max_workers) as executor:
    future_to_round = {
        executor.submit(fetch_date_for_round, round_num): round_num
        for round_num in round_numbers_to_process
    }
    
    for future in as_completed(future_to_round):
        round_num = future_to_round[future]
        completed_count += 1
        
        try:
            round_num_result, draw_date = future.result()
            
            # データを更新
            for row in data:
                if int(row['round_number']) == round_num_result:
                    if draw_date:
                        old_date = row.get('draw_date', '')
                        if old_date != draw_date:
                            row['draw_date'] = draw_date
                            weekday = calculate_weekday(draw_date)
                            if weekday is not None:
                                row['weekday'] = str(weekday)
                            else:
                                row['weekday'] = 'NULL'
                            updated_count += 1
                            if updated_count <= 10 or updated_count % 100 == 0:
                                print(f"   ✓ 第{round_num_result}回: {old_date} → {draw_date} ({completed_count}/{total_rounds})")
                        # 処理済みとして記録
                        processed_rounds.add(round_num_result)
                        break
                    else:
                        failed_count += 1
                        if failed_count <= 10:
                            print(f"   ⚠ 第{round_num_result}回: 日付が取得できませんでした")
                        # 失敗しても処理済みとして記録（再試行を避ける）
                        processed_rounds.add(round_num_result)
                    break
            
            # 進捗表示と保存（100件ごと）
            if completed_count % save_interval == 0:
                print(f"\n   進捗: {completed_count}/{total_rounds}件完了（更新: {updated_count}件、失敗: {failed_count}件）")
                print(f"   💾 中間保存中...")
                
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
                
                # 進捗ファイルに保存
                with open(progress_file, 'w', encoding='utf-8') as f:
                    for r in sorted(processed_rounds):
                        f.write(f"{r}\n")
                
                print(f"   ✓ 中間保存完了（{completed_count}件処理済み）\n")
            
            # サーバー負荷軽減のため、少し待機
            if completed_count % 10 == 0:
                time.sleep(0.1)
                
        except Exception as e:
            failed_count += 1
            if failed_count <= 10:
                print(f"   ⚠ 第{round_num}回の処理でエラー: {e}")
            # エラーでも処理済みとして記録
            processed_rounds.add(round_num)

session.close()

print(f"\n✓ 取得完了: 更新={updated_count}件、失敗={failed_count}件")

# 最終保存
print("\n💾 CSVファイルに最終保存中...")
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

# 進捗ファイルに保存
with open(progress_file, 'w', encoding='utf-8') as f:
    for r in sorted(processed_rounds):
        f.write(f"{r}\n")

print(f"✓ CSVファイルを更新しました（{len(data)}件）")
print(f"✓ 進捗ファイルを更新しました（{len(processed_rounds)}件処理済み）")

# 進捗ファイルを削除（処理完了時）
if len(processed_rounds) == len(round_numbers):
    progress_file.unlink()
    print("✓ すべての処理が完了しました。進捗ファイルを削除しました。")


