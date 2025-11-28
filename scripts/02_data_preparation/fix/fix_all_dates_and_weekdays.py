#!/usr/bin/env python3
"""
すべての日付と曜日を検証・修正するスクリプト

みずほ銀行のCSVファイルから正しい日付を取得し、
既存の日付が間違っている場合も修正します。

また、日付から曜日を再計算します。
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
    print("pip install requests を実行してください")
    sys.exit(1)

# ファイルパス
CSV_FILE = Path(__file__).parent.parent.parent.parent / 'data' / 'past_results.csv'


def parse_japanese_date(date_str: str) -> str:
    """
    和暦の日付を西暦のYYYY-MM-DD形式に変換
    """
    match = re.search(r'(平成|令和|昭和)(\d+|元)年(\d{1,2})月(\d{1,2})日', date_str)
    if not match:
        return None
    
    era = match.group(1)
    year_str = match.group(2)
    month = int(match.group(3))
    day = int(match.group(4))
    
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
    """
    日付から曜日を計算（0-4の整数、月-金）
    """
    if not draw_date or draw_date == 'NULL':
        return None
    
    try:
        date_obj = datetime.strptime(draw_date, '%Y-%m-%d')
        weekday = date_obj.weekday()
        if weekday < 5:  # 平日のみ
            return weekday
        return None
    except (ValueError, TypeError):
        return None


def fetch_date_from_mizuhobank(round_number: int, session: requests.Session) -> str:
    """
    みずほ銀行のCSVファイルから日付を取得
    """
    csv_url = f'https://www.mizuhobank.co.jp/retail/takarakuji/numbers/csv/A100{round_number:04d}.CSV'
    
    try:
        response = session.get(csv_url, timeout=30)
        
        if response.status_code == 404:
            return None
        
        response.raise_for_status()
        
        response.encoding = 'shift_jis'
        content = response.text
        
        lines = content.split('\n')
        if len(lines) >= 2:
            header_line = lines[1]
            date = parse_japanese_date(header_line)
            return date
        
        return None
        
    except Exception as e:
        return None


def main():
    print("=" * 70)
    print("日付と曜日を検証・修正するスクリプト")
    print("=" * 70)
    
    # CSVファイルを読み込む
    print(f"\n📥 CSVファイルを読み込み中: {CSV_FILE}")
    
    data = []
    with open(CSV_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for row in reader:
            data.append(row)
    
    print(f"✓ {len(data)}件のデータを読み込みました")
    
    # 修正が必要な回号を特定
    # 1. NULLの日付
    # 2. 曜日がNULLまたは日付と不一致
    # 3. 日付が週末（土日）になっている
    # 4. 日付が重複している
    
    # 日付の出現回数をカウント
    date_counts = {}
    for row in data:
        draw_date = row.get('draw_date', '')
        if draw_date and draw_date != 'NULL':
            date_counts[draw_date] = date_counts.get(draw_date, 0) + 1
    
    # 重複している日付
    duplicate_dates = {date for date, count in date_counts.items() if count > 1}
    if duplicate_dates:
        print(f"\n⚠ 重複している日付を検出: {duplicate_dates}")
    
    rounds_to_check = []
    for row in data:
        round_number = int(row['round_number'])
        draw_date = row.get('draw_date', '')
        weekday = row.get('weekday', '')
        
        needs_check = False
        
        # NULLの日付
        if draw_date == 'NULL' or not draw_date:
            needs_check = True
        # 曜日がNULL
        elif weekday == 'NULL' or not weekday:
            needs_check = True
        # 日付が重複している
        elif draw_date in duplicate_dates:
            needs_check = True
        else:
            # 日付から曜日を計算して不一致をチェック
            calculated_weekday = calculate_weekday(draw_date)
            if calculated_weekday is None:
                # 週末の日付 - 間違っている可能性が高い
                needs_check = True
            elif str(calculated_weekday) != weekday:
                # 曜日が不一致
                needs_check = True
        
        if needs_check:
            rounds_to_check.append(round_number)
    
    if not rounds_to_check:
        print("✓ 修正が必要なデータはありません")
        return
    
    print(f"\n🔍 検証が必要な回号: {len(rounds_to_check)}件")
    if len(rounds_to_check) <= 20:
        print(f"   回号: {rounds_to_check}")
    else:
        print(f"   回号: {rounds_to_check[:10]}... (他{len(rounds_to_check)-10}件)")
    
    # セッションを作成
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    })
    
    # みずほ銀行から日付を取得して更新
    print(f"\n📅 みずほ銀行から日付を取得・検証中...")
    
    date_updated = 0
    weekday_updated = 0
    failed_rounds = []
    
    for i, round_number in enumerate(rounds_to_check):
        # 進捗表示
        if (i + 1) % 10 == 0 or i == 0:
            print(f"   処理中: {i + 1}/{len(rounds_to_check)}")
        
        correct_date = fetch_date_from_mizuhobank(round_number, session)
        
        if correct_date:
            # データを更新
            for row in data:
                if int(row['round_number']) == round_number:
                    old_date = row.get('draw_date', 'NULL')
                    old_weekday = row.get('weekday', 'NULL')
                    
                    # 日付を更新
                    if old_date != correct_date:
                        row['draw_date'] = correct_date
                        date_updated += 1
                        print(f"   ✓ 第{round_number}回: 日付 {old_date} → {correct_date}")
                    
                    # 曜日を計算して更新
                    correct_weekday = calculate_weekday(correct_date)
                    if correct_weekday is not None:
                        new_weekday = str(correct_weekday)
                        if old_weekday != new_weekday:
                            row['weekday'] = new_weekday
                            weekday_updated += 1
                            if old_date == correct_date:  # 日付は同じで曜日だけ更新
                                print(f"   ✓ 第{round_number}回: 曜日 {old_weekday} → {new_weekday}")
                    else:
                        row['weekday'] = 'NULL'
                    
                    break
        else:
            failed_rounds.append(round_number)
        
        # サーバー負荷軽減
        time.sleep(0.1)
    
    session.close()
    
    print(f"\n✓ 検証完了:")
    print(f"   日付を更新: {date_updated}件")
    print(f"   曜日を更新: {weekday_updated}件")
    print(f"   取得失敗: {len(failed_rounds)}件")
    
    if failed_rounds:
        print(f"   失敗した回号: {failed_rounds}")
    
    # CSVファイルに保存
    print(f"\n💾 CSVファイルに保存中...")
    
    with open(CSV_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in data:
            csv_row = {}
            for key in fieldnames:
                value = row.get(key, '')
                csv_row[key] = value if value else 'NULL'
            writer.writerow(csv_row)
    
    print(f"✓ CSVファイルを更新しました: {CSV_FILE}")
    print("\n" + "=" * 70)
    print("✓ 処理完了")
    print("=" * 70)


if __name__ == "__main__":
    main()

