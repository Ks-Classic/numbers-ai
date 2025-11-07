#!/usr/bin/env python3
"""
past_results.csvにweekdayカラムを追加するスクリプト

既存データのdraw_dateからweekdayを計算して追加します。
"""

import sys
import csv
from pathlib import Path
from datetime import datetime
from typing import Optional

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


def add_weekday_column(csv_file: Path, backup: bool = True):
    """
    past_results.csvにweekdayカラムを追加
    
    Args:
        csv_file: CSVファイルのパス
        backup: バックアップを作成するか
    """
    if not csv_file.exists():
        print(f"エラー: ファイルが見つかりません: {csv_file}")
        sys.exit(1)
    
    # バックアップを作成
    if backup:
        backup_file = csv_file.with_suffix('.csv.backup')
        print(f"📋 バックアップを作成中: {backup_file}")
        import shutil
        shutil.copy2(csv_file, backup_file)
        print(f"✓ バックアップを作成しました")
    
    # CSVファイルを読み込む
    data = []
    has_weekday = False
    
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        
        # weekdayカラムが既に存在するか確認
        if 'weekday' in fieldnames:
            has_weekday = True
            print("⚠ weekdayカラムは既に存在します。既存の値を更新します。")
        else:
            # weekdayカラムを追加
            fieldnames = list(fieldnames)
            # draw_dateの後にweekdayを挿入
            if 'draw_date' in fieldnames:
                draw_date_idx = fieldnames.index('draw_date')
                fieldnames.insert(draw_date_idx + 1, 'weekday')
            else:
                fieldnames.append('weekday')
            print(f"✓ weekdayカラムを追加します")
        
        for row in reader:
            # weekdayを計算
            draw_date = row.get('draw_date', '')
            weekday = calculate_weekday(draw_date)
            
            if has_weekday:
                # 既存のweekdayカラムがある場合、空またはNULLの場合は更新
                existing_weekday = row.get('weekday', '')
                if not existing_weekday or existing_weekday == 'NULL':
                    row['weekday'] = str(weekday) if weekday is not None else 'NULL'
            else:
                # 新しいweekdayカラムを追加
                row['weekday'] = str(weekday) if weekday is not None else 'NULL'
            
            data.append(row)
    
    # CSVファイルに書き込む
    print(f"\n💾 CSVファイルを更新中: {csv_file}")
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for row in data:
            # NULL値の処理
            csv_row = {}
            for key in fieldnames:
                value = row.get(key, '')
                csv_row[key] = value if value else 'NULL'
            
            writer.writerow(csv_row)
    
    # 統計情報を表示
    total_count = len(data)
    weekday_count = sum(1 for row in data if row.get('weekday') and row.get('weekday') != 'NULL')
    null_weekday_count = total_count - weekday_count
    
    print(f"✓ CSVファイルを更新しました")
    print(f"  データ件数: {total_count:,}件")
    print(f"  weekdayが設定された件数: {weekday_count:,}件")
    print(f"  weekdayがNULLの件数: {null_weekday_count:,}件")


def main():
    csv_file = Path(__file__).parent.parent / 'data' / 'past_results.csv'
    
    if len(sys.argv) > 1:
        csv_file = Path(sys.argv[1])
    
    print("=" * 80)
    print("past_results.csvにweekdayカラムを追加するスクリプト")
    print("=" * 80)
    print(f"\n対象ファイル: {csv_file}\n")
    
    add_weekday_column(csv_file)
    
    print("\n" + "=" * 80)
    print("✓ 処理完了")
    print("=" * 80)


if __name__ == "__main__":
    main()

