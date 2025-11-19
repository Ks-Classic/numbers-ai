#!/usr/bin/env python3
"""
過去データの日付・曜日を再計算するスクリプト

既存のpast_results.csvの日付とweekdayを、最新回から逆算して再計算します。
"""
import sys
import csv
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional

# プロジェクトルートを取得
PROJECT_ROOT = Path(__file__).parent.parent
CSV_FILE = PROJECT_ROOT / 'data' / 'past_results.csv'


def calculate_weekday(draw_date: Optional[str]) -> Optional[int]:
    """
    日付から曜日を計算（0-4の整数）
    
    Args:
        draw_date: 日付文字列（YYYY-MM-DD形式、NULL可）
    
    Returns:
        曜日（0:月, 1:火, 2:水, 3:木, 4:金）、NULLの場合はNone
    """
    if not draw_date or draw_date == 'NULL' or not draw_date.strip():
        return None
    
    try:
        date_obj = datetime.strptime(draw_date, '%Y-%m-%d')
        weekday = date_obj.weekday()
        # ナンバーズは平日のみ抽選のため、0-4の値のみ
        if weekday < 5:
            return weekday
        return None
    except (ValueError, TypeError):
        return None


def recalculate_dates(data: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """
    日付とweekdayを再計算
    
    Args:
        data: CSVデータのリスト
    
    Returns:
        再計算後のデータリスト
    """
    if not data:
        return data
    
    # 最新回号を取得
    max_round = max(int(row['round_number']) for row in data if row.get('round_number'))
    
    # 最新回の日付を基準にする（既存の日付があれば使用、なければ今日）
    latest_row = next((row for row in data if int(row.get('round_number', 0)) == max_round), None)
    if latest_row and latest_row.get('draw_date') and latest_row['draw_date'] != 'NULL':
        try:
            base_date = datetime.strptime(latest_row['draw_date'], '%Y-%m-%d')
        except ValueError:
            base_date = datetime.now()
    else:
        base_date = datetime.now()
    
    print(f"基準日: {base_date.strftime('%Y-%m-%d')} (第{max_round}回)")
    
    # 各回号の日付を再計算
    updated_count = 0
    for row in data:
        round_num = int(row.get('round_number', 0))
        if round_num == 0:
            continue
        
        # 最新回から逆算して日付を計算（平日のみを考慮）
        round_diff = max_round - round_num
        draw_date_obj = base_date
        weekday_count = 0
        
        # 最新回から逆算して、平日のみをカウント
        while weekday_count < round_diff:
            draw_date_obj = draw_date_obj - timedelta(days=1)
            # 平日かどうかを確認（月曜=0, 金曜=4）
            if draw_date_obj.weekday() < 5:
                # 年末年始を除外
                month = draw_date_obj.month
                day = draw_date_obj.day
                if not ((month == 12 and day >= 29) or (month == 1 and day <= 3)):
                    weekday_count += 1
        
        new_date = draw_date_obj.strftime('%Y-%m-%d')
        new_weekday = calculate_weekday(new_date)
        
        old_date = row.get('draw_date', '')
        old_weekday = row.get('weekday', '')
        
        # 日付またはweekdayが変更される場合のみ更新
        if old_date != new_date or str(old_weekday) != str(new_weekday):
            row['draw_date'] = new_date
            row['weekday'] = str(new_weekday) if new_weekday is not None else 'NULL'
            updated_count += 1
            
            if round_num >= max_round - 10:  # 最新10件のみ表示
                print(f"  第{round_num}回: {old_date} ({old_weekday}) → {new_date} ({new_weekday})")
    
    print(f"\n✓ {updated_count}件のデータを更新しました")
    return data


def main():
    """メイン処理"""
    print("=" * 80)
    print("過去データの日付・曜日再計算スクリプト")
    print("=" * 80)
    
    if not CSV_FILE.exists():
        print(f"⚠ CSVファイルが見つかりません: {CSV_FILE}")
        sys.exit(1)
    
    # CSVファイルを読み込む
    print(f"\n📥 CSVファイルを読み込み中: {CSV_FILE}")
    data = []
    try:
        with open(CSV_FILE, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # NULL値を空文字列に変換
                cleaned_row = {}
                for key, value in row.items():
                    cleaned_row[key] = '' if value == 'NULL' else value
                data.append(cleaned_row)
    except Exception as e:
        print(f"⚠ CSVファイルの読み込みエラー: {e}")
        sys.exit(1)
    
    print(f"✓ {len(data)}件のデータを読み込みました")
    
    # 日付とweekdayを再計算
    print("\n🔄 日付・曜日を再計算中...")
    data = recalculate_dates(data)
    
    # バックアップを作成
    backup_file = CSV_FILE.with_suffix('.csv.backup')
    print(f"\n💾 バックアップを作成中: {backup_file}")
    try:
        import shutil
        shutil.copy2(CSV_FILE, backup_file)
        print("✓ バックアップを作成しました")
    except Exception as e:
        print(f"⚠ バックアップ作成エラー: {e}")
    
    # CSVファイルに保存
    print(f"\n💾 CSVファイルに保存中: {CSV_FILE}")
    fieldnames = [
        'round_number',
        'draw_date',
        'weekday',
        'n3_winning',
        'n4_winning',
        'n3_rehearsal',
        'n4_rehearsal'
    ]
    
    try:
        with open(CSV_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for row in data:
                csv_row = {}
                for key in fieldnames:
                    value = row.get(key, '')
                    csv_row[key] = value if value else 'NULL'
                
                writer.writerow(csv_row)
        
        print("✓ CSVファイルを保存しました")
    except Exception as e:
        print(f"⚠ CSVファイルの保存エラー: {e}")
        sys.exit(1)
    
    print("\n" + "=" * 80)
    print("✓ 処理完了")
    print("=" * 80)


if __name__ == "__main__":
    main()

