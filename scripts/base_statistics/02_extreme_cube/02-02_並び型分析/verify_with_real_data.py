"""
実際のデータでの並び型判定の検証スクリプト

過去のデータを使用して、並び型判定スクリプトが正しく動作することを確認する。
"""

import sys
import argparse
import json
from pathlib import Path
from typing import Dict, Any

import pandas as pd

# プロジェクトルートをパスに追加
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.append(str(PROJECT_ROOT / 'core'))
sys.path.append(str(PROJECT_ROOT / 'scripts' / 'production'))

from chart_generator import load_keisen_master
from generate_extreme_cube import load_past_results, validate_round_number, generate_extreme_cube
from pattern_classifier import (
    analyze_patterns,
    get_winning_digits_positions,
    are_all_connected,
    classify_pattern
)


def verify_recent_rounds(
    df: pd.DataFrame,
    keisen_master: dict,
    num_rounds: int = 150,
    start_round: int = None
) -> Dict[str, Any]:
    """最近の回号での検証
    
    Args:
        df: 過去当選番号データ
        keisen_master: 罫線マスターデータ
        num_rounds: 検証する回数
        start_round: 開始回号（Noneの場合は最新回から遡る）
    
    Returns:
        検証結果の辞書
    """
    if start_round is None:
        end_round = int(df['round_number'].max())
        start_round = max(3, end_round - num_rounds + 1)
    else:
        end_round = start_round + num_rounds - 1
    
    print(f"検証範囲: 回号 {start_round} - {end_round} ({num_rounds}回)")
    print("=" * 60)
    
    # 分析実行
    results = analyze_patterns(df, keisen_master, start_round, end_round, enable_detailed_stats=True)
    
    # 検証結果の表示
    print("\n検証結果サマリー")
    print("=" * 60)
    print(f"総回数: {results['total_rounds']}")
    print(f"分析成功回数: {results['total_analyzed']}")
    print(f"分析失敗回数: {results['total_failed']}")
    print(f"成功率: {results['total_analyzed'] / results['total_rounds'] * 100:.2f}%")
    
    if results['total_failed'] > 0:
        print("\n失敗理由別の内訳:")
        for reason, count in results['failure_reasons'].items():
            if count > 0:
                print(f"  {reason}: {count}回")
    
    if results['pattern_counts']:
        print("\n並び型の出現回数:")
        for pattern, count in sorted(results['pattern_counts'].items(), key=lambda x: -x[1]):
            percentage = (count / results['total_analyzed'] * 100) if results['total_analyzed'] > 0 else 0
            print(f"  {pattern}: {count}回 ({percentage:.2f}%)")
    
    # 未分類パターンの確認
    unclassified_count = results.get('unclassified_count', 0)
    if unclassified_count > 0:
        print(f"\n⚠️  未分類パターン: {unclassified_count}件")
        if 'detailed_stats' in results and results['detailed_stats'].get('unclassified_patterns'):
            print("未分類パターンの詳細（上位10件）:")
            for i, pattern_info in enumerate(results['detailed_stats']['unclassified_patterns'][:10], 1):
                print(f"  {i}. 回号 {pattern_info['round_number']}: {pattern_info['n3_winning']} - {pattern_info.get('position_str', pattern_info['positions'])}")
    else:
        print("\n✅ すべてのパターンが分類されました")
    
    # 詳細統計情報の表示
    if 'detailed_stats' in results and results['detailed_stats'].get('pattern_avg_times'):
        print("\n各型の平均判定時間:")
        for pattern, time_info in sorted(results['detailed_stats']['pattern_avg_times'].items(), 
                                         key=lambda x: x[1]['avg_time_ms']):
            print(f"  {pattern}: 平均 {time_info['avg_time_ms']:.3f}ms (件数: {time_info['count']})")
    
    return results


def verify_specific_rounds(
    df: pd.DataFrame,
    keisen_master: dict,
    round_numbers: list
) -> Dict[str, Any]:
    """特定の回号での検証
    
    Args:
        df: 過去当選番号データ
        keisen_master: 罫線マスターデータ
        round_numbers: 検証する回号のリスト
    
    Returns:
        検証結果の辞書
    """
    print(f"検証対象: {len(round_numbers)}回")
    print("=" * 60)
    
    results = []
    failed_rounds = []
    
    for round_number in round_numbers:
        try:
            if not validate_round_number(df, round_number):
                print(f"回号 {round_number}: データ不足のためスキップ")
                failed_rounds.append(round_number)
                continue
            
            # 極CUBEを生成
            grid, rows, cols = generate_extreme_cube(df, keisen_master, round_number)
            
            # 当選数字を取得
            round_data = df[df['round_number'] == round_number].iloc[0]
            n3_winning = str(round_data['n3_winning']).zfill(3)
            winning_digits = [int(d) for d in n3_winning]
            
            # 位置を取得
            positions = get_winning_digits_positions(grid, winning_digits)
            
            if len(positions) != 3:
                print(f"回号 {round_number}: 位置が3つ見つからない（見つかった数: {len(positions)}）")
                failed_rounds.append(round_number)
                continue
            
            # つながりの確認
            if not are_all_connected(positions):
                print(f"回号 {round_number}: 当選数字がつながっていない")
                failed_rounds.append(round_number)
                continue
            
            # 並び型を判定
            pattern = classify_pattern(positions)
            
            if pattern is None:
                print(f"回号 {round_number}: 並び型を判定できませんでした（位置: {positions}）")
                failed_rounds.append(round_number)
                continue
            
            results.append({
                'round_number': round_number,
                'n3_winning': n3_winning,
                'positions': positions,
                'pattern': pattern
            })
            
            print(f"回号 {round_number}: {n3_winning} → {pattern}")
        
        except Exception as e:
            print(f"回号 {round_number}: エラー - {e}")
            failed_rounds.append(round_number)
    
    print("\n" + "=" * 60)
    print(f"成功: {len(results)}回")
    print(f"失敗: {len(failed_rounds)}回")
    
    return {
        'results': results,
        'failed_rounds': failed_rounds
    }


def main():
    """メイン処理"""
    parser = argparse.ArgumentParser(description='実際のデータでの並び型判定の検証')
    parser.add_argument('--num-rounds', type=int, default=150, help='検証する回数（デフォルト: 150）')
    parser.add_argument('--start-round', type=int, default=None, help='開始回号（デフォルト: 最新回から遡る）')
    parser.add_argument('--rounds', type=str, default=None, help='検証する回号のリスト（カンマ区切り、例: 6840,6841,6842）')
    parser.add_argument('--csv-path', type=str, default=None, help='過去当選番号CSVファイルのパス（デフォルト: data/past_results.csv）')
    parser.add_argument('--output', type=str, default=None, help='結果を保存するJSONファイルのパス')
    
    args = parser.parse_args()
    
    # パスの設定
    if args.csv_path is None:
        csv_path = PROJECT_ROOT / 'data' / 'past_results.csv'
    else:
        csv_path = Path(args.csv_path)
    
    if not csv_path.exists():
        print(f"エラー: {csv_path} が見つかりません")
        return 1
    
    # データの読み込み
    print("データを読み込んでいます...")
    df = load_past_results(csv_path)
    keisen_master = load_keisen_master()
    print("✓ データの読み込み完了\n")
    
    # 検証実行
    if args.rounds:
        # 特定の回号での検証
        round_numbers = [int(r.strip()) for r in args.rounds.split(',')]
        results = verify_specific_rounds(df, keisen_master, round_numbers)
    else:
        # 最近の回号での検証
        results = verify_recent_rounds(df, keisen_master, args.num_rounds, args.start_round)
    
    # 結果を保存
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"\n結果を保存しました: {output_path}")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())

