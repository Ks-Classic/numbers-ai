#!/usr/bin/env python3
"""
past_results.csvの欠番を調べるスクリプト
"""
import csv
import sys
from pathlib import Path

def find_missing_rounds(csv_file: str, min_round: int = 1, max_round: int = 6850):
    """
    CSVファイルから欠番を調べる
    
    Args:
        csv_file: CSVファイルのパス
        min_round: 最小回号（デフォルト: 1）
        max_round: 最大回号（デフォルト: 6850）
    """
    existing_rounds = set()
    
    # CSVファイルから回号を読み込む
    csv_path = Path(csv_file)
    if not csv_path.exists():
        print(f"エラー: ファイルが見つかりません: {csv_file}")
        sys.exit(1)
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                round_num = int(row['round_number'])
                existing_rounds.add(round_num)
            except (ValueError, KeyError):
                continue
    
    # 欠番を特定
    all_rounds = set(range(min_round, max_round + 1))
    missing_rounds = sorted(all_rounds - existing_rounds)
    
    print(f"=== 欠番の調査結果 ===")
    print(f"データ件数: {len(existing_rounds)}件")
    print(f"期待される回号範囲: {min_round}回 ～ {max_round}回")
    print(f"欠番の数: {len(missing_rounds)}件")
    print()
    
    if not missing_rounds:
        print("欠番はありません。")
        return
    
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
    
    print("=== 欠番の範囲 ===")
    for start, end in ranges:
        if start == end:
            print(f"  第{start}回 (単独)")
        else:
            count = end - start + 1
            print(f"  第{start}回 ～ 第{end}回 ({count}件連続)")
    
    print()
    print("=== 全欠番リスト ===")
    print(", ".join(map(str, missing_rounds)))

if __name__ == "__main__":
    csv_file = "data/past_results.csv"
    if len(sys.argv) > 1:
        csv_file = sys.argv[1]
    
    min_round = 1
    max_round = 6850
    
    if len(sys.argv) > 2:
        min_round = int(sys.argv[2])
    if len(sys.argv) > 3:
        max_round = int(sys.argv[3])
    
    find_missing_rounds(csv_file, min_round, max_round)

