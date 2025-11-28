#!/usr/bin/env python3
"""
NULLの日付を持つ回号についてみずほ銀行から日付を取得して更新するスクリプト

みずほ銀行のCSVファイル形式:
https://www.mizuhobank.co.jp/retail/takarakuji/numbers/csv/A100{回号:04d}.CSV

CSVファイルの内容例:
A50
第6864回ナンバーズ,数字選択式全国自治宝くじ,令和7年11月25日,東京 宝くじドリーム館
...
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
    
    Args:
        date_str: 和暦の日付（例: "令和7年11月25日"）
    
    Returns:
        西暦の日付（例: "2025-11-25"）
    """
    match = re.search(r'(平成|令和|昭和)(\d+|元)年(\d{1,2})月(\d{1,2})日', date_str)
    if not match:
        return None
    
    era = match.group(1)
    year_str = match.group(2)
    month = int(match.group(3))
    day = int(match.group(4))
    
    # 元号を西暦に変換
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
    
    Args:
        draw_date: 日付文字列（YYYY-MM-DD形式）
    
    Returns:
        曜日（0:月, 1:火, 2:水, 3:木, 4:金）
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
    
    Args:
        round_number: 回号
        session: requests.Sessionオブジェクト
    
    Returns:
        日付（YYYY-MM-DD形式）、取得失敗時はNone
    """
    csv_url = f'https://www.mizuhobank.co.jp/retail/takarakuji/numbers/csv/A100{round_number:04d}.CSV'
    
    try:
        response = session.get(csv_url, timeout=30)
        
        if response.status_code == 404:
            return None
        
        response.raise_for_status()
        
        # Shift_JISでデコード
        response.encoding = 'shift_jis'
        content = response.text
        
        # 日付を抽出（2行目のヘッダー行から）
        lines = content.split('\n')
        if len(lines) >= 2:
            header_line = lines[1]
            date = parse_japanese_date(header_line)
            return date
        
        return None
        
    except Exception as e:
        print(f"   ⚠ 第{round_number}回の取得エラー: {e}")
        return None


def main():
    print("=" * 60)
    print("NULLの日付を更新するスクリプト")
    print("=" * 60)
    
    # CSVファイルを読み込む
    print(f"\n📥 CSVファイルを読み込み中: {CSV_FILE}")
    
    data = []
    with open(CSV_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for row in reader:
            data.append(row)
    
    print(f"✓ {len(data)}件のデータを読み込みました")
    
    # NULLの日付を持つ回号を特定
    null_date_rounds = []
    for row in data:
        if row.get('draw_date') == 'NULL' or not row.get('draw_date'):
            try:
                round_number = int(row['round_number'])
                null_date_rounds.append(round_number)
            except (ValueError, KeyError):
                continue
    
    if not null_date_rounds:
        print("✓ NULLの日付はありません")
        return
    
    print(f"\n🔍 NULLの日付を持つ回号: {len(null_date_rounds)}件")
    print(f"   回号: {null_date_rounds}")
    
    # セッションを作成
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    })
    
    # みずほ銀行から日付を取得
    print(f"\n📅 みずほ銀行から日付を取得中...")
    
    updated_count = 0
    failed_rounds = []
    
    for round_number in null_date_rounds:
        date = fetch_date_from_mizuhobank(round_number, session)
        
        if date:
            # データを更新
            for row in data:
                if int(row['round_number']) == round_number:
                    row['draw_date'] = date
                    weekday = calculate_weekday(date)
                    row['weekday'] = str(weekday) if weekday is not None else 'NULL'
                    updated_count += 1
                    print(f"   ✓ 第{round_number}回: {date} (曜日: {row['weekday']})")
                    break
        else:
            failed_rounds.append(round_number)
            print(f"   ⚠ 第{round_number}回: 日付を取得できませんでした")
        
        # サーバー負荷軽減
        time.sleep(0.2)
    
    session.close()
    
    print(f"\n✓ 取得完了: 更新={updated_count}件、失敗={len(failed_rounds)}件")
    
    if failed_rounds:
        print(f"   失敗した回号: {failed_rounds}")
    
    # CSVファイルに保存
    print(f"\n💾 CSVファイルに保存中...")
    
    with open(CSV_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in data:
            # NULL値の処理
            csv_row = {}
            for key in fieldnames:
                value = row.get(key, '')
                csv_row[key] = value if value else 'NULL'
            writer.writerow(csv_row)
    
    print(f"✓ CSVファイルを更新しました: {CSV_FILE}")
    print("\n" + "=" * 60)
    print("✓ 処理完了")
    print("=" * 60)


if __name__ == "__main__":
    main()

