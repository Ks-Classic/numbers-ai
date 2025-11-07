#!/usr/bin/env python3
"""
past_results.csvの詳細な分析スクリプト
- 件数
- 欠番
- リハーサル有無の範囲
- 当選番号NULL範囲や対象回
"""
import csv
import sys
from pathlib import Path
from datetime import datetime

def analyze_past_results(csv_file: str):
    """
    past_results.csvを詳細に分析
    
    Args:
        csv_file: CSVファイルのパス
    """
    data = []
    
    csv_path = Path(csv_file)
    if not csv_path.exists():
        print(f"エラー: ファイルが見つかりません: {csv_file}")
        sys.exit(1)
    
    # CSVファイルを読み込む
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                round_num = int(row['round_number'])
                data.append({
                    'round': round_num,
                    'date': row['draw_date'],
                    'n3_winning': row['n3_winning'],
                    'n4_winning': row['n4_winning'],
                    'n3_rehearsal': row['n3_rehearsal'],
                    'n4_rehearsal': row['n4_rehearsal'],
                })
            except (ValueError, KeyError) as e:
                continue
    
    # 回号でソート
    data.sort(key=lambda x: x['round'])
    
    # 基本統計
    total_count = len(data)
    min_round = data[0]['round'] if data else 0
    max_round = data[-1]['round'] if data else 0
    
    # 欠番を特定
    all_rounds = set(range(min_round, max_round + 1))
    existing_rounds = {d['round'] for d in data}
    missing_rounds = sorted(all_rounds - existing_rounds)
    
    # リハーサル有無の範囲を特定
    rehearsal_available_from = None
    rehearsal_available_to = None
    rehearsal_rounds = []
    
    for d in data:
        if d['n3_rehearsal'] and d['n3_rehearsal'] != 'NULL' and d['n3_rehearsal'].strip():
            rehearsal_rounds.append(d['round'])
    
    if rehearsal_rounds:
        rehearsal_available_from = min(rehearsal_rounds)
        rehearsal_available_to = max(rehearsal_rounds)
    
    # NULL値の範囲を特定
    n3_null_rounds = []
    n4_null_rounds = []
    n3_rehearsal_null_rounds = []
    n4_rehearsal_null_rounds = []
    
    for d in data:
        if not d['n3_winning'] or d['n3_winning'] == 'NULL' or not d['n3_winning'].strip():
            n3_null_rounds.append(d['round'])
        if not d['n4_winning'] or d['n4_winning'] == 'NULL' or not d['n4_winning'].strip():
            n4_null_rounds.append(d['round'])
        if not d['n3_rehearsal'] or d['n3_rehearsal'] == 'NULL' or not d['n3_rehearsal'].strip():
            n3_rehearsal_null_rounds.append(d['round'])
        if not d['n4_rehearsal'] or d['n4_rehearsal'] == 'NULL' or not d['n4_rehearsal'].strip():
            n4_rehearsal_null_rounds.append(d['round'])
    
    # 日付範囲（NULLを除外）
    dates = [d['date'] for d in data if d['date'] and d['date'] != 'NULL' and d['date'].strip()]
    min_date = min(dates) if dates else None
    max_date = max(dates) if dates else None
    
    # 結果を出力
    print("# past_results.csv データ分析レポート")
    print()
    print(f"**作成日時**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    print("## 1. 基本統計")
    print()
    print(f"- **データ件数**: {total_count:,}件")
    print(f"- **回号範囲**: 第{min_round}回 ～ 第{max_round}回")
    print(f"- **日付範囲**: {min_date} ～ {max_date}")
    print()
    
    print("## 2. 欠番")
    print()
    if missing_rounds:
        print(f"- **欠番の数**: {len(missing_rounds)}件")
        print()
        
        # 連続した範囲をグループ化
        ranges = []
        start = missing_rounds[0]
        end = missing_rounds[0]
        
        for i in range(1, len(missing_rounds)):
            if missing_rounds[i] == end + 1:
                end = missing_rounds[i]
            else:
                ranges.append((start, end))
                start = missing_rounds[i]
                end = missing_rounds[i]
        ranges.append((start, end))
        
        print("### 欠番の範囲")
        print()
        for start, end in ranges:
            if start == end:
                print(f"- 第{start}回 (単独)")
            else:
                count = end - start + 1
                print(f"- 第{start}回 ～ 第{end}回 ({count}件連続)")
        print()
        print(f"### 全欠番リスト")
        print()
        print(", ".join(map(str, missing_rounds)))
    else:
        print("- 欠番なし")
    print()
    
    print("## 3. リハーサル番号の有無")
    print()
    if rehearsal_available_from:
        print(f"- **リハーサル番号が存在する範囲**: 第{rehearsal_available_from}回 ～ 第{rehearsal_available_to}回")
        print(f"- **リハーサル番号が存在する件数**: {len(rehearsal_rounds):,}件")
        print()
        print(f"- **リハーサル番号が存在しない範囲**: 第{min_round}回 ～ 第{rehearsal_available_from - 1}回")
        print(f"- **リハーサル番号が存在しない件数**: {rehearsal_available_from - min_round:,}件")
    else:
        print("- リハーサル番号のデータなし")
    print()
    
    print("## 4. NULL値の範囲")
    print()
    
    if n3_null_rounds:
        print(f"### N3当選番号がNULL")
        print(f"- **件数**: {len(n3_null_rounds)}件")
        print(f"- **対象回**: {', '.join(map(str, n3_null_rounds[:20]))}{' ...' if len(n3_null_rounds) > 20 else ''}")
    else:
        print("### N3当選番号がNULL")
        print("- NULL値なし")
    print()
    
    if n4_null_rounds:
        print(f"### N4当選番号がNULL")
        print(f"- **件数**: {len(n4_null_rounds)}件")
        print(f"- **対象回**: {', '.join(map(str, n4_null_rounds[:20]))}{' ...' if len(n4_null_rounds) > 20 else ''}")
    else:
        print("### N4当選番号がNULL")
        print("- NULL値なし")
    print()
    
    if n3_rehearsal_null_rounds:
        print(f"### N3リハーサル番号がNULL")
        print(f"- **件数**: {len(n3_rehearsal_null_rounds)}件")
        if rehearsal_available_from:
            null_before = [r for r in n3_rehearsal_null_rounds if r < rehearsal_available_from]
            null_after = [r for r in n3_rehearsal_null_rounds if r >= rehearsal_available_from]
            if null_before:
                print(f"- **リハーサル導入前**: {len(null_before)}件（第{min(null_before)}回 ～ 第{max(null_before)}回）")
            if null_after:
                print(f"- **リハーサル導入後**: {len(null_after)}件（第{min(null_after)}回 ～ 第{max(null_after)}回）")
        else:
            print(f"- **対象回**: {', '.join(map(str, n3_rehearsal_null_rounds[:20]))}{' ...' if len(n3_rehearsal_null_rounds) > 20 else ''}")
    else:
        print("### N3リハーサル番号がNULL")
        print("- NULL値なし")
    print()
    
    if n4_rehearsal_null_rounds:
        print(f"### N4リハーサル番号がNULL")
        print(f"- **件数**: {len(n4_rehearsal_null_rounds)}件")
        if rehearsal_available_from:
            null_before = [r for r in n4_rehearsal_null_rounds if r < rehearsal_available_from]
            null_after = [r for r in n4_rehearsal_null_rounds if r >= rehearsal_available_from]
            if null_before:
                print(f"- **リハーサル導入前**: {len(null_before)}件（第{min(null_before)}回 ～ 第{max(null_before)}回）")
            if null_after:
                print(f"- **リハーサル導入後**: {len(null_after)}件（第{min(null_after)}回 ～ 第{max(null_after)}回）")
        else:
            print(f"- **対象回**: {', '.join(map(str, n4_rehearsal_null_rounds[:20]))}{' ...' if len(n4_rehearsal_null_rounds) > 20 else ''}")
    else:
        print("### N4リハーサル番号がNULL")
        print("- NULL値なし")
    print()
    
    print("## 5. データソース")
    print()
    print("- **4800回以前**: みずほ銀行のCSVファイルから直接取得")
    print("- **4801回以降**: hpfree.comから取得")
    print()

if __name__ == "__main__":
    csv_file = "data/past_results.csv"
    if len(sys.argv) > 1:
        csv_file = sys.argv[1]
    
    analyze_past_results(csv_file)

