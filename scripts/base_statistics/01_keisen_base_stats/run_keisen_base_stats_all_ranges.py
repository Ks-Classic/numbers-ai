#!/usr/bin/env python3
"""
keisen基礎集計を3パターンの範囲で実行するスクリプト

全範囲、週5以降、リハーサル導入以降の3パターンで集計を実行し、
それぞれのJSONファイルを生成する。
"""

import subprocess
import sys
from pathlib import Path

# スクリプトのディレクトリ
SCRIPT_DIR = Path(__file__).parent
ANALYZE_SCRIPT = SCRIPT_DIR / "analyze_keisen_base_stats.py"

# 集計範囲の定義
RANGES = [
    {
        "name": "全範囲",
        "start": 1,
        "end": 6850,
        "suffix": "all"
    },
    {
        "name": "週5実施開始以降",
        "start": 1340,
        "end": 6850,
        "suffix": "1340"
    },
    {
        "name": "リハーサル数字導入以降",
        "start": 4801,
        "end": 6850,
        "suffix": "4801"
    }
]

def run_analysis(range_config):
    """指定された範囲で集計を実行"""
    name = range_config["name"]
    start = range_config["start"]
    end = range_config["end"]
    suffix = range_config["suffix"]
    
    print("\n" + "=" * 80)
    print(f"集計実行: {name} ({start}回 ～ {end}回)")
    print("=" * 80)
    
    # Python実行可能ファイルのパスを取得（仮想環境を考慮）
    python_exe = sys.executable
    
    cmd = [
        python_exe,
        str(ANALYZE_SCRIPT),
        "--start-round", str(start),
        "--end-round", str(end),
        "--output-suffix", suffix
    ]
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=False)
        print(f"\n✓ {name}の集計が完了しました")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n✗ {name}の集計でエラーが発生しました: {e}")
        return False

def main():
    """メイン処理"""
    print("=" * 80)
    print("keisen基礎集計 - 全範囲パターン実行")
    print("=" * 80)
    print(f"\n実行する集計パターン数: {len(RANGES)}")
    for i, r in enumerate(RANGES, 1):
        print(f"  {i}. {r['name']}: {r['start']}回 ～ {r['end']}回 (suffix: {r['suffix']})")
    
    # 各範囲で集計を実行
    results = []
    for range_config in RANGES:
        success = run_analysis(range_config)
        results.append({
            "name": range_config["name"],
            "success": success
        })
    
    # 結果サマリー
    print("\n" + "=" * 80)
    print("実行結果サマリー")
    print("=" * 80)
    for result in results:
        status = "✓ 成功" if result["success"] else "✗ 失敗"
        print(f"{status}: {result['name']}")
    
    # 成功/失敗のカウント
    success_count = sum(1 for r in results if r["success"])
    total_count = len(results)
    
    print(f"\n成功: {success_count}/{total_count}")
    
    if success_count == total_count:
        print("\n✓ 全ての集計が正常に完了しました")
        return 0
    else:
        print(f"\n✗ {total_count - success_count}件の集計でエラーが発生しました")
        return 1

if __name__ == "__main__":
    sys.exit(main())

