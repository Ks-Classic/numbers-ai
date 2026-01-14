#!/usr/bin/env python3
"""
回号6847以前のデータで、リハーサル番号と本番番号が逆になっているデータを修正するスクリプト

問題: 6847以前のデータでは：
- n3_rehearsal列に本番番号が入っている
- n3_winning列にリハーサル番号が入っている
- 同様に n4_rehearsal と n4_winning も逆

解決: これらの列をスワップして正しい状態にする
"""

import sys
from pathlib import Path
from typing import Dict
from datetime import datetime

# ------------------------------------------------------------
# 定数
# ------------------------------------------------------------
SWAP_THRESHOLD_ROUND = 6847  # この回号以前のデータをスワップ

def log(msg: str):
    """標準エラー出力にログを出力"""
    sys.stderr.write(f"{msg}\n")

# ------------------------------------------------------------
# CSV 入出力
# ------------------------------------------------------------
def load_csv(csv_path: str) -> Dict[int, Dict]:
    """CSVを読み込む"""
    path = Path(csv_path)
    if not path.exists():
        log(f"❌ ファイルが見つかりません: {csv_path}")
        return {}
    
    data: Dict[int, Dict] = {}
    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    for line in lines[1:]:  # ヘッダーはスキップ
        if not line.strip():
            continue
        cols = line.strip().split(",")
        try:
            rnd = int(cols[0])
        except:
            continue
        
        data[rnd] = {
            "round_number": rnd,
            "draw_date": cols[1] if len(cols) > 1 else "NULL",
            "weekday": cols[2] if len(cols) > 2 else "NULL",
            "n3_rehearsal": cols[3] if len(cols) > 3 else "NULL",
            "n4_rehearsal": cols[4] if len(cols) > 4 else "NULL",
            "n3_winning": cols[5] if len(cols) > 5 else "NULL",
            "n4_winning": cols[6] if len(cols) > 6 else "NULL",
        }
    
    return data

def save_csv(data: Dict[int, Dict], csv_path: str):
    """CSVを保存"""
    path = Path(csv_path)
    rounds = sorted(data.keys(), reverse=True)
    
    with open(path, "w", encoding="utf-8") as f:
        f.write("round_number,draw_date,weekday,n3_rehearsal,n4_rehearsal,n3_winning,n4_winning\n")
        for r in rounds:
            row = data[r]
            f.write(
                f"{row['round_number']},{row['draw_date']},{row['weekday']},"
                f"{row['n3_rehearsal']},{row['n4_rehearsal']},"
                f"{row['n3_winning']},{row['n4_winning']}\n"
            )

# ------------------------------------------------------------
# メイン処理
# ------------------------------------------------------------
def main():
    csv_path = Path(__file__).parent.parent / "data" / "past_results.csv"
    
    log("=" * 80)
    log("リハーサル・本番データスワップスクリプト")
    log(f"対象: 回号 {SWAP_THRESHOLD_ROUND} 以前のデータ")
    log("=" * 80)
    
    # 1. 現在のCSVを読み込む
    log("\n📂 現在のCSVを読み込み中...")
    current_data = load_csv(str(csv_path))
    log(f"✓ {len(current_data)} 回号分のデータを読み込み")
    
    # 2. バックアップ作成
    backup_path = csv_path.parent / f"past_results_before_swap_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    log(f"\n💾 バックアップを作成: {backup_path.name}")
    save_csv(current_data.copy(), str(backup_path))
    
    # 3. データをスワップ
    log(f"\n🔄 回号 {SWAP_THRESHOLD_ROUND} 以前のデータをスワップ中...")
    swapped_count = 0
    
    for round_num in sorted(current_data.keys()):
        if round_num > SWAP_THRESHOLD_ROUND:
            # 6848以降はスキップ
            continue
        
        row = current_data[round_num]
        
        # リハーサルと本番をスワップ
        old_n3_rehearsal = row["n3_rehearsal"]
        old_n4_rehearsal = row["n4_rehearsal"]
        old_n3_winning = row["n3_winning"]
        old_n4_winning = row["n4_winning"]
        
        # スワップ実行
        row["n3_rehearsal"] = old_n3_winning
        row["n4_rehearsal"] = old_n4_winning
        row["n3_winning"] = old_n3_rehearsal
        row["n4_winning"] = old_n4_rehearsal
        
        # NULLでないデータのみログ出力
        if old_n3_rehearsal != "NULL" or old_n3_winning != "NULL":
            log(f"  Round {round_num}: ")
            log(f"    N3: rehearsal {old_n3_rehearsal} ⇄ {row['n3_rehearsal']} | winning {old_n3_winning} ⇄ {row['n3_winning']}")
            log(f"    N4: rehearsal {old_n4_rehearsal} ⇄ {row['n4_rehearsal']} | winning {old_n4_winning} ⇄ {row['n4_winning']}")
        
        swapped_count += 1
    
    log(f"\n✅ {swapped_count} 回号分のデータをスワップ")
    
    # 4. 更新されたデータを保存
    log(f"\n💾 更新されたデータを保存: {csv_path.name}")
    save_csv(current_data, str(csv_path))
    
    # 5. 結果を確認
    log("\n📊 スワップ結果の確認:")
    for r in [6845, 6846, 6847, 6848, 6849, 6850]:
        if r in current_data:
            row = current_data[r]
            log(f"  Round {r}: N3_rehearsal={row['n3_rehearsal']}, N3_winning={row['n3_winning']}, "
                f"N4_rehearsal={row['n4_rehearsal']}, N4_winning={row['n4_winning']}")
    
    log("\n" + "=" * 80)
    log("✅ 処理完了！")
    log("=" * 80)

if __name__ == "__main__":
    main()
