#!/usr/bin/env python3
"""
draw_dateとweekdayの整合性を検証するスクリプト
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


def validate_data_integrity(csv_file: Path):
    """
    draw_dateとweekdayの整合性を検証
    
    Args:
        csv_file: CSVファイルのパス
    """
    if not csv_file.exists():
        print(f"エラー: ファイルが見つかりません: {csv_file}")
        sys.exit(1)
    
    errors = []
    warnings = []
    total_count = 0
    weekday_mismatch_count = 0
    null_weekday_count = 0
    null_date_count = 0
    
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        
        if 'weekday' not in fieldnames:
            print("⚠ weekdayカラムが存在しません。weekdayカラムを追加してください。")
            return
        
        for row_num, row in enumerate(reader, start=2):  # ヘッダー行を除く
            total_count += 1
            round_number = row.get('round_number', '')
            draw_date = row.get('draw_date', '')
            weekday_str = row.get('weekday', '')
            
            # NULLのdraw_dateをチェック
            if not draw_date or draw_date == 'NULL' or not draw_date.strip():
                null_date_count += 1
                if weekday_str and weekday_str != 'NULL':
                    warnings.append(f"行{row_num}: 回号{round_number} - draw_dateがNULLなのにweekdayが設定されています")
                continue
            
            # weekdayがNULLの場合
            if not weekday_str or weekday_str == 'NULL' or not weekday_str.strip():
                null_weekday_count += 1
                # draw_dateからweekdayを計算して警告
                calculated_weekday = calculate_weekday(draw_date)
                if calculated_weekday is not None:
                    warnings.append(f"行{row_num}: 回号{round_number} - weekdayがNULLですが、draw_dateから計算すると{calculated_weekday}です")
                continue
            
            # weekdayとdraw_dateの整合性をチェック
            try:
                weekday = int(weekday_str)
                if weekday < 0 or weekday > 4:
                    errors.append(f"行{row_num}: 回号{round_number} - weekdayが不正な値です: {weekday}")
                    continue
                
                # draw_dateからweekdayを計算
                calculated_weekday = calculate_weekday(draw_date)
                if calculated_weekday is not None and calculated_weekday != weekday:
                    weekday_mismatch_count += 1
                    weekday_names = ['月', '火', '水', '木', '金']
                    errors.append(
                        f"行{row_num}: 回号{round_number} - weekdayの不一致: "
                        f"設定値={weekday}({weekday_names[weekday]}), "
                        f"計算値={calculated_weekday}({weekday_names[calculated_weekday]}), "
                        f"draw_date={draw_date}"
                    )
            except ValueError:
                errors.append(f"行{row_num}: 回号{round_number} - weekdayが数値ではありません: {weekday_str}")
    
    # 結果を表示
    print("=" * 80)
    print("draw_dateとweekdayの整合性検証結果")
    print("=" * 80)
    print(f"\nデータ件数: {total_count:,}件")
    print(f"weekday不一致: {weekday_mismatch_count}件")
    print(f"weekdayがNULL: {null_weekday_count}件")
    print(f"draw_dateがNULL: {null_date_count}件")
    
    if errors:
        print(f"\n❌ エラー: {len(errors)}件")
        print("-" * 80)
        for error in errors[:20]:  # 最初の20件のみ表示
            print(error)
        if len(errors) > 20:
            print(f"... 他 {len(errors) - 20}件のエラー")
    else:
        print("\n✓ エラーはありませんでした")
    
    if warnings:
        print(f"\n⚠ 警告: {len(warnings)}件")
        print("-" * 80)
        for warning in warnings[:20]:  # 最初の20件のみ表示
            print(warning)
        if len(warnings) > 20:
            print(f"... 他 {len(warnings) - 20}件の警告")
    
    print("\n" + "=" * 80)
    
    if errors:
        sys.exit(1)
    else:
        print("✓ 検証完了")


def main():
    csv_file = Path(__file__).parent.parent / 'data' / 'past_results.csv'
    
    if len(sys.argv) > 1:
        csv_file = Path(sys.argv[1])
    
    validate_data_integrity(csv_file)


if __name__ == "__main__":
    main()

