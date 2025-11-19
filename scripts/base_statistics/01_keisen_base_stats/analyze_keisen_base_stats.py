#!/usr/bin/env python3
"""
keisen基礎集計スクリプト
指定範囲のデータから、前々回・前回パターンごとの当選数字の出現頻度とランキングを集計し、
新keisenマスターデータを生成する。
"""

import pandas as pd
import json
import numpy as np
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Tuple
import sys
import argparse
import pickle
import gc
from tqdm import tqdm

# データディレクトリのパス
# scripts/base_statistics/01_keisen_base_stats/ から見て、プロジェクトルートは4階層上
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
# 出力先は data/base_statistics/01_keisen_base_stats/ に統一
OUTPUT_DIR = DATA_DIR / "base_statistics" / "01_keisen_base_stats"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# チェックポイントと中間ファイルのディレクトリ
CHECKPOINT_DIR = OUTPUT_DIR / "checkpoints"
CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
INTERMEDIATE_DIR = OUTPUT_DIR / "intermediate"
INTERMEDIATE_DIR.mkdir(parents=True, exist_ok=True)

# メモリ対策の設定
BATCH_SIZE = 500  # 500回号ごとにバッチ処理
CHECKPOINT_INTERVAL = 100  # 100回号ごとにチェックポイントを保存
INTERMEDIATE_SAVE_INTERVAL = 1000  # 1000回号ごとに中間ファイルに保存

# N3とN4の桁定義
N3_COLUMNS = ["百の位", "十の位", "一の位"]
N4_COLUMNS = ["千の位", "百の位", "十の位", "一の位"]

def load_past_results() -> pd.DataFrame:
    """past_results.csvを読み込む"""
    file_path = DATA_DIR / "past_results.csv"
    if not file_path.exists():
        raise FileNotFoundError(f"データファイルが見つかりません: {file_path}")
    
    # NULL文字列をNaNとして読み込む
    df = pd.read_csv(file_path, na_values=['NULL', 'null', ''])
    
    # 当選番号を文字列型に変換（数値型で読み込まれる可能性があるため）
    df['n3_winning'] = df['n3_winning'].astype(str).str.replace('.0', '', regex=False)
    df['n4_winning'] = df['n4_winning'].astype(str).str.replace('.0', '', regex=False)
    
    # NULL値やNaNを除外
    df['n3_winning'] = df['n3_winning'].replace('nan', pd.NA).replace('NULL', pd.NA)
    df['n4_winning'] = df['n4_winning'].replace('nan', pd.NA).replace('NULL', pd.NA)
    
    # 先頭0を補完（数値型として読み込まれた場合、先頭0が失われるため）
    df['n3_winning'] = df['n3_winning'].apply(
        lambda x: str(x).zfill(3) if pd.notna(x) and str(x) != 'nan' and str(x) != 'NULL' else x
    )
    df['n4_winning'] = df['n4_winning'].apply(
        lambda x: str(x).zfill(4) if pd.notna(x) and str(x) != 'nan' and str(x) != 'NULL' else x
    )
    
    print(f"データ読み込み完了: {len(df)}行")
    return df

def filter_data_range(df: pd.DataFrame, start_round: int = 4801, end_round: int = 6850) -> pd.DataFrame:
    """指定範囲のデータをフィルタリング"""
    filtered = df[(df['round_number'] >= start_round) & (df['round_number'] <= end_round)].copy()
    filtered = filtered.sort_values('round_number')
    print(f"フィルタリング完了: {len(filtered)}行 (回号 {start_round}-{end_round})")
    return filtered

def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """データクリーニング"""
    df = df.copy()
    
    # NULL値の除去
    original_len = len(df)
    df = df.dropna(subset=['n3_winning', 'n4_winning'])
    if len(df) < original_len:
        print(f"NULL値除去: {original_len - len(df)}行を削除")
    
    # 形式チェック（文字列型であることを確認）
    df = df[df['n3_winning'].astype(str).str.len() == 3]
    df = df[df['n4_winning'].astype(str).str.len() == 4]
    
    print(f"データクリーニング完了: {len(df)}行")
    return df

def extract_previous_numbers(df: pd.DataFrame) -> pd.DataFrame:
    """前回・前々回の当選番号を抽出"""
    df = df.copy()
    df['prev_n3'] = df['n3_winning'].shift(1)
    df['prev2_n3'] = df['n3_winning'].shift(2)
    df['prev_n4'] = df['n4_winning'].shift(1)
    df['prev2_n4'] = df['n4_winning'].shift(2)
    
    # 前回・前々回が存在しない行を除外
    df = df.dropna(subset=['prev_n3', 'prev2_n3', 'prev_n4', 'prev2_n4'])
    
    print(f"前回・前々回データ抽出完了: {len(df)}行")
    return df

def extract_digits(number_str, num_digits: int) -> List[int]:
    """数字文字列から各桁を抽出"""
    # 文字列型に変換
    if pd.isna(number_str):
        raise ValueError(f"数値がNULLです: {number_str}")
    str_value = str(number_str)
    if len(str_value) != num_digits:
        raise ValueError(f"数値の桁数が不正です: {str_value} (期待値: {num_digits})")
    return [int(str_value[i]) for i in range(num_digits)]

def count_pattern_frequency(df: pd.DataFrame, columns: List[str], prev_col: str, prev2_col: str, winning_col: str) -> Dict:
    """パターン出現頻度を集計（メモリ最適化版）"""
    pattern_counts = defaultdict(int)
    digit_counts = defaultdict(lambda: defaultdict(int))
    
    # iterrows()の代わりにitertuples()を使用（より高速でメモリ効率が良い）
    for row in df.itertuples(index=False):
        prev = getattr(row, prev_col)
        prev2 = getattr(row, prev2_col)
        winning = getattr(row, winning_col)
        
        # 各桁を抽出
        prev_digits = extract_digits(prev, len(columns))
        prev2_digits = extract_digits(prev2, len(columns))
        winning_digits = extract_digits(winning, len(columns))
        
        # 各桁ごとにパターンを集計
        for i, column in enumerate(columns):
            prev_digit = str(prev_digits[i])
            prev2_digit = str(prev2_digits[i])
            winning_digit = winning_digits[i]
            
            # パターン出現回数をカウント
            # keisen_master.jsonの構造は[前々回][前回]なので、pattern_keyも(column, 前々回, 前回)の順序にする
            pattern_key = (column, prev2_digit, prev_digit)
            pattern_counts[pattern_key] += 1
            
            # 当選数字の出現回数をカウント
            digit_counts[pattern_key][winning_digit] += 1
    
    return pattern_counts, digit_counts

def count_pattern_frequency_batch(batch_df: pd.DataFrame, columns: List[str], prev_col: str, prev2_col: str, winning_col: str,
                                   pattern_counts: Dict, digit_counts: Dict) -> Tuple[Dict, Dict]:
    """パターン出現頻度を集計（バッチ処理版、既存の辞書に追加）"""
    for row in batch_df.itertuples(index=False):
        prev = getattr(row, prev_col)
        prev2 = getattr(row, prev2_col)
        winning = getattr(row, winning_col)
        
        # 各桁を抽出
        prev_digits = extract_digits(prev, len(columns))
        prev2_digits = extract_digits(prev2, len(columns))
        winning_digits = extract_digits(winning, len(columns))
        
        # 各桁ごとにパターンを集計
        for i, column in enumerate(columns):
            prev_digit = str(prev_digits[i])
            prev2_digit = str(prev2_digits[i])
            winning_digit = winning_digits[i]
            
            # パターン出現回数をカウント
            pattern_key = (column, prev2_digit, prev_digit)
            pattern_counts[pattern_key] += 1
            
            # 当選数字の出現回数をカウント
            digit_counts[pattern_key][winning_digit] += 1
    
    return pattern_counts, digit_counts

def save_checkpoint(checkpoint_file: Path, processed_rounds: set, last_round: int, 
                   n3_pattern_counts: Dict, n3_digit_counts: Dict,
                   n4_pattern_counts: Dict, n4_digit_counts: Dict):
    """チェックポイントを保存（pickle形式、tupleキーをそのまま保存可能）"""
    checkpoint_data = {
        'processed_rounds': sorted(list(processed_rounds)),
        'last_round': last_round,
        'n3_pattern_counts': dict(n3_pattern_counts),  # tupleキーをそのまま保存（pickleなので可能）
        'n3_digit_counts': {k: dict(v) for k, v in n3_digit_counts.items()},  # tupleキーをそのまま保存
        'n4_pattern_counts': dict(n4_pattern_counts),
        'n4_digit_counts': {k: dict(v) for k, v in n4_digit_counts.items()}
    }
    
    with open(checkpoint_file, 'wb') as f:
        pickle.dump(checkpoint_data, f)
    
    print(f"✅ チェックポイント保存: {last_round}回号まで処理済み")

def load_checkpoint(checkpoint_file: Path) -> Tuple[set, int, Dict, Dict, Dict, Dict]:
    """チェックポイントから復元"""
    if not checkpoint_file.exists():
        return set(), 0, defaultdict(int), defaultdict(lambda: defaultdict(int)), defaultdict(int), defaultdict(lambda: defaultdict(int))
    
    with open(checkpoint_file, 'rb') as f:
        checkpoint_data = pickle.load(f)
    
    processed_rounds = set(checkpoint_data.get('processed_rounds', []))
    last_round = checkpoint_data.get('last_round', 0)
    
    # 辞書を復元（pickleなのでtupleキーをそのまま復元可能）
    n3_pattern_counts = defaultdict(int, checkpoint_data.get('n3_pattern_counts', {}))
    n3_digit_counts = defaultdict(lambda: defaultdict(int))
    for k, v in checkpoint_data.get('n3_digit_counts', {}).items():
        n3_digit_counts[k] = defaultdict(int, v)
    
    n4_pattern_counts = defaultdict(int, checkpoint_data.get('n4_pattern_counts', {}))
    n4_digit_counts = defaultdict(lambda: defaultdict(int))
    for k, v in checkpoint_data.get('n4_digit_counts', {}).items():
        n4_digit_counts[k] = defaultdict(int, v)
    
    print(f"✅ チェックポイントから復元: {len(processed_rounds)}回号処理済み、最終回号: {last_round}")
    return processed_rounds, last_round, n3_pattern_counts, n3_digit_counts, n4_pattern_counts, n4_digit_counts

def calculate_rankings_with_rule(digit_counts: Dict, pattern_counts: Dict) -> Dict:
    """ランキングを作成（既存のkeisen_master.jsonと同じルールを適用）
    
    ルールの適用順序:
    1. 上位3位の最小出現回数 > 4位以降の最大出現回数 の場合 → 上位3位のみ（3桁）
    2. 上位3位の最小出現回数 = 4位以降の最大出現回数 の場合（同率） → ルール2を適用（4桁以上）
    3. 上位3位の最小出現回数 < 4位以降の最大出現回数 の場合 → ルール2を適用（4桁以上）
    
    ルール2: 予測出目の最小出現回数 >= 除外された数字の最大出現回数
    """
    rankings = {}
    
    for pattern_key, digit_count_dict in digit_counts.items():
        # 出現回数の降順でソート、同率の場合は数字の昇順でソート
        sorted_digits = sorted(
            digit_count_dict.items(),
            key=lambda x: (-x[1], x[0])
        )
        
        if len(sorted_digits) == 0:
            rankings[pattern_key] = {
                'ranking': [],
                'counts': {},
                'total_samples': 0
            }
            continue
        
        # 上位3位の情報
        top3_digits = [digit for digit, count in sorted_digits[:3]]
        top3_counts = [count for _, count in sorted_digits[:3]]
        top3_min_count = min(top3_counts) if top3_counts else 0
        
        # 4位以降の情報
        if len(sorted_digits) > 3:
            remaining_counts = [count for _, count in sorted_digits[3:]]
            remaining_max_count = max(remaining_counts) if remaining_counts else 0
        else:
            remaining_max_count = 0
        
        # ルール1をチェック: 上位3位の最小出現回数 > 4位以降の最大出現回数
        if top3_min_count > remaining_max_count:
            # ルール1を満たす場合: 上位3位のみを予測出目とする（3桁）
            predictions = top3_digits
        else:
            # ルール1を満たさない場合（同率または小さい）: 上位3位 + 上位3位の最小出現回数と同じ（同率）の4位以降の数字
            predictions = top3_digits.copy()
            
            # 4位以降の数字で、上位3位の最小出現回数と同じ（同率）の数字を追加
            if len(sorted_digits) > 3:
                for digit, count in sorted_digits[3:]:
                    if count == top3_min_count:
                        predictions.append(digit)
                    elif count < top3_min_count:
                        # 上位3位の最小出現回数より小さい場合は追加しない
                        break
        
        counts_dict = {str(digit): count for digit, count in sorted_digits}
        
        rankings[pattern_key] = {
            'ranking': predictions,
            'counts': counts_dict,
            'total_samples': sum(digit_count_dict.values())
        }
    
    return rankings

def calculate_rankings(digit_counts: Dict) -> Dict:
    """ランキングを作成（旧バージョン - 上位3位まで）"""
    rankings = {}
    
    for pattern_key, digit_count_dict in digit_counts.items():
        # 出現回数の降順でソート、同率の場合は数字の昇順でソート
        sorted_digits = sorted(
            digit_count_dict.items(),
            key=lambda x: (-x[1], x[0])
        )
        
        # 上位3位までの数字リストを抽出
        top3 = [digit for digit, count in sorted_digits[:3]]
        rankings[pattern_key] = {
            'ranking': top3,
            'counts': {str(digit): count for digit, count in sorted_digits}
        }
    
    return rankings

def calculate_reliability_stats(pattern_counts: Dict, digit_counts: Dict) -> Dict:
    """統計的信頼性指標を計算"""
    reliability_stats = {}
    
    for pattern_key in pattern_counts.keys():
        n = pattern_counts[pattern_key]
        digit_count_dict = digit_counts.get(pattern_key, {})
        
        if n == 0:
            continue
        
        # 各数字の出現回数リスト
        counts = [digit_count_dict.get(d, 0) for d in range(10)]
        
        # 標準偏差を計算
        if n > 1:
            std_dev = np.std(counts, ddof=1)
        else:
            std_dev = 0.0
        
        # 各数字の出現率と95%信頼区間
        digit_stats = {}
        for digit in range(10):
            count = digit_count_dict.get(digit, 0)
            rate = (count / n) * 100 if n > 0 else 0.0
            
            # 95%信頼区間（正規分布を仮定）
            if n > 0:
                se = np.sqrt((rate / 100) * (1 - rate / 100) / n)
                ci_lower = max(0, rate - 1.96 * se * 100)
                ci_upper = min(100, rate + 1.96 * se * 100)
            else:
                ci_lower = ci_upper = 0.0
            
            digit_stats[str(digit)] = {
                'count': count,
                'rate': rate,
                'ci_lower': ci_lower,
                'ci_upper': ci_upper
            }
        
        # 信頼性スコア（サンプル数に基づく）
        if n >= 10:
            reliability_score = 1.0
        elif n >= 5:
            reliability_score = 0.7
        else:
            reliability_score = 0.3
        
        reliability_stats[pattern_key] = {
            'sample_size': n,
            'std_dev': float(std_dev),
            'reliability_score': reliability_score,
            'digit_stats': digit_stats
        }
    
    return reliability_stats

def generate_keisen_master(rankings: Dict, pattern_counts: Dict, n3_rankings: Dict, n4_rankings: Dict) -> Dict:
    """新keisenマスターデータを生成"""
    master = {
        'n3': {},
        'n4': {}
    }
    
    # N3のマスターデータを生成（keisen_master.jsonの構造は[前々回][前回]）
    for column in N3_COLUMNS:
        master['n3'][column] = {}
        for prev2_digit in range(10):
            prev2_str = str(prev2_digit)  # 前々回
            master['n3'][column][prev2_str] = {}
            for prev_digit in range(10):
                prev_str = str(prev_digit)  # 前回
                pattern_key = (column, prev2_str, prev_str)  # (column, 前々回, 前回)
                
                if pattern_key in n3_rankings:
                    ranking = n3_rankings[pattern_key]['ranking']
                    sample_size = pattern_counts.get(pattern_key, 0)
                    
                    # サンプル数が不足している場合は空配列または警告
                    if sample_size < 5:
                        master['n3'][column][prev2_str][prev_str] = []
                    else:
                        master['n3'][column][prev2_str][prev_str] = ranking
                else:
                    master['n3'][column][prev2_str][prev_str] = []
    
    # N4のマスターデータを生成（keisen_master.jsonの構造は[前々回][前回]）
    for column in N4_COLUMNS:
        master['n4'][column] = {}
        for prev2_digit in range(10):
            prev2_str = str(prev2_digit)  # 前々回
            master['n4'][column][prev2_str] = {}
            for prev_digit in range(10):
                prev_str = str(prev_digit)  # 前回
                pattern_key = (column, prev2_str, prev_str)  # (column, 前々回, 前回)
                
                if pattern_key in n4_rankings:
                    ranking = n4_rankings[pattern_key]['ranking']
                    sample_size = pattern_counts.get(pattern_key, 0)
                    
                    # サンプル数が不足している場合は空配列または警告
                    if sample_size < 5:
                        master['n4'][column][prev2_str][prev_str] = []
                    else:
                        master['n4'][column][prev2_str][prev_str] = ranking
                else:
                    master['n4'][column][prev2_str][prev_str] = []
    
    return master

def validate_keisen_master(master: Dict) -> Tuple[bool, List[str]]:
    """keisenマスターデータの検証"""
    errors = []
    
    # N3の検証
    expected_n3_patterns = len(N3_COLUMNS) * 10 * 10
    actual_n3_patterns = 0
    for column in N3_COLUMNS:
        if column not in master['n3']:
            errors.append(f"N3: 桁 '{column}' が存在しません")
            continue
        for prev_str in master['n3'][column]:
            if prev_str not in [str(i) for i in range(10)]:
                errors.append(f"N3: 前回の数字 '{prev_str}' が無効です")
            for prev2_str in master['n3'][column][prev_str]:
                if prev2_str not in [str(i) for i in range(10)]:
                    errors.append(f"N3: 前々回の数字 '{prev2_str}' が無効です")
                actual_n3_patterns += 1
                predictions = master['n3'][column][prev_str][prev2_str]
                if not isinstance(predictions, list):
                    errors.append(f"N3: 予測出目が配列ではありません: {column}/{prev_str}/{prev2_str}")
                else:
                    for pred in predictions:
                        if not isinstance(pred, int) or pred < 0 or pred > 9:
                            errors.append(f"N3: 予測出目が無効です: {pred} (0-9の範囲外)")
    
    if actual_n3_patterns != expected_n3_patterns:
        errors.append(f"N3: パターン数が不正です。期待値: {expected_n3_patterns}, 実際: {actual_n3_patterns}")
    
    # N4の検証
    expected_n4_patterns = len(N4_COLUMNS) * 10 * 10
    actual_n4_patterns = 0
    for column in N4_COLUMNS:
        if column not in master['n4']:
            errors.append(f"N4: 桁 '{column}' が存在しません")
            continue
        for prev_str in master['n4'][column]:
            if prev_str not in [str(i) for i in range(10)]:
                errors.append(f"N4: 前回の数字 '{prev_str}' が無効です")
            for prev2_str in master['n4'][column][prev_str]:
                if prev2_str not in [str(i) for i in range(10)]:
                    errors.append(f"N4: 前々回の数字 '{prev2_str}' が無効です")
                actual_n4_patterns += 1
                predictions = master['n4'][column][prev_str][prev2_str]
                if not isinstance(predictions, list):
                    errors.append(f"N4: 予測出目が配列ではありません: {column}/{prev_str}/{prev2_str}")
                else:
                    for pred in predictions:
                        if not isinstance(pred, int) or pred < 0 or pred > 9:
                            errors.append(f"N4: 予測出目が無効です: {pred} (0-9の範囲外)")
    
    if actual_n4_patterns != expected_n4_patterns:
        errors.append(f"N4: パターン数が不正です。期待値: {expected_n4_patterns}, 実際: {actual_n4_patterns}")
    
    return len(errors) == 0, errors

def save_json(data: Dict, filepath: Path):
    """JSONファイルを保存"""
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"JSONファイル保存完了: {filepath}")

def save_csv_from_dict(data: Dict, filepath: Path):
    """辞書データをCSV形式で保存"""
    rows = []
    for key, value in data.items():
        if isinstance(key, tuple):
            column, prev, prev2 = key
            row = {
                'column': column,
                'prev': prev,
                'prev2': prev2,
                **value
            }
        else:
            row = {'key': str(key), **value}
        rows.append(row)
    
    df = pd.DataFrame(rows)
    df.to_csv(filepath, index=False, encoding='utf-8-sig')
    print(f"CSVファイル保存完了: {filepath}")

def main():
    """メイン処理"""
    parser = argparse.ArgumentParser(
        description='keisen基礎集計スクリプト',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  # 全範囲（1-6850回）
  python %(prog)s --start-round 1 --end-round 6850 --output-suffix all
  
  # 週5以降（1340-6850回）
  python %(prog)s --start-round 1340 --end-round 6850 --output-suffix 1340
  
  # リハーサル導入以降（4801-6850回、デフォルト）
  python %(prog)s --start-round 4801 --end-round 6850 --output-suffix 4801
        """
    )
    parser.add_argument(
        '--start-round',
        type=int,
        default=4801,
        help='集計開始回号（デフォルト: 4801）'
    )
    parser.add_argument(
        '--end-round',
        type=int,
        default=6850,
        help='集計終了回号（デフォルト: 6850）'
    )
    parser.add_argument(
        '--output-suffix',
        type=str,
        default='',
        help='出力ファイル名のサフィックス（例: all, 1340, 4801）'
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        default=BATCH_SIZE,
        help=f'バッチサイズ（デフォルト: {BATCH_SIZE}回号）'
    )
    parser.add_argument(
        '--checkpoint-interval',
        type=int,
        default=CHECKPOINT_INTERVAL,
        help=f'チェックポイント保存間隔（デフォルト: {CHECKPOINT_INTERVAL}回号）'
    )
    parser.add_argument(
        '--resume',
        action='store_true',
        help='チェックポイントから処理を再開する'
    )
    parser.add_argument(
        '--no-checkpoint',
        action='store_true',
        help='チェックポイント機能を無効にする'
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("keisen基礎集計スクリプト開始")
    print("=" * 60)
    print(f"集計範囲: {args.start_round}回 ～ {args.end_round}回")
    if args.output_suffix:
        print(f"出力サフィックス: {args.output_suffix}")
    
    try:
        # チェックポイントファイルの設定
        checkpoint_file = CHECKPOINT_DIR / f"analyze_keisen_base_stats_{args.output_suffix or 'default'}_checkpoint.pkl"
        
        # チェックポイントから復元（--resumeオプションが指定されている場合）
        processed_rounds = set()
        start_processing_round = args.start_round
        n3_pattern_counts = defaultdict(int)
        n3_digit_counts = defaultdict(lambda: defaultdict(int))
        n4_pattern_counts = defaultdict(int)
        n4_digit_counts = defaultdict(lambda: defaultdict(int))
        
        if args.resume and checkpoint_file.exists():
            processed_rounds, last_round, n3_pattern_counts, n3_digit_counts, n4_pattern_counts, n4_digit_counts = load_checkpoint(checkpoint_file)
            start_processing_round = max(start_processing_round, last_round + 1)
            print(f"処理再開: {start_processing_round}回号から開始")
        elif checkpoint_file.exists() and not args.no_checkpoint:
            print(f"⚠️  チェックポイントファイルが存在します: {checkpoint_file}")
            print("   処理を再開する場合は --resume オプションを指定してください")
            print("   新規に処理を開始する場合は、チェックポイントファイルを削除してください")
            response = input("新規に処理を開始しますか？ (y/N): ")
            if response.lower() != 'y':
                print("処理を中断しました")
                sys.exit(0)
        
        # Phase 1: データ準備
        print("\n[Phase 1] データ準備")
        df = load_past_results()
        df = filter_data_range(df, start_round=args.start_round, end_round=args.end_round)
        df = clean_data(df)
        df = extract_previous_numbers(df)
        
        # Phase 2 & 3: パターン出現頻度と当選数字の分布を集計（バッチ処理版）
        print(f"\n[Phase 2-3] パターン出現頻度と当選数字の分布を集計（バッチ処理: {args.batch_size}回号ごと）")
        
        # バッチ処理
        total_rounds = args.end_round - start_processing_round + 1
        num_batches = (total_rounds + args.batch_size - 1) // args.batch_size
        
        with tqdm(total=num_batches, desc="バッチ処理") as pbar:
            for batch_idx in range(num_batches):
                batch_start = start_processing_round + batch_idx * args.batch_size
                batch_end = min(batch_start + args.batch_size - 1, args.end_round)
                
                # バッチデータを抽出
                batch_df = df[(df['round_number'] >= batch_start) & (df['round_number'] <= batch_end)]
                
                if len(batch_df) == 0:
                    continue
                
                # バッチを処理
                n3_pattern_counts, n3_digit_counts = count_pattern_frequency_batch(
                    batch_df, N3_COLUMNS, 'prev_n3', 'prev2_n3', 'n3_winning',
                    n3_pattern_counts, n3_digit_counts
                )
                n4_pattern_counts, n4_digit_counts = count_pattern_frequency_batch(
                    batch_df, N4_COLUMNS, 'prev_n4', 'prev2_n4', 'n4_winning',
                    n4_pattern_counts, n4_digit_counts
                )
                
                # 処理済み回号を記録
                processed_rounds.update(range(batch_start, batch_end + 1))
                
                # チェックポイントを保存（一定間隔ごと）
                if not args.no_checkpoint and batch_end % args.checkpoint_interval == 0:
                    save_checkpoint(
                        checkpoint_file, processed_rounds, batch_end,
                        n3_pattern_counts, n3_digit_counts,
                        n4_pattern_counts, n4_digit_counts
                    )
                
                # メモリを解放
                del batch_df
                gc.collect()
                
                pbar.update(1)
        
        # 最終チェックポイントを保存
        if not args.no_checkpoint:
            save_checkpoint(
                checkpoint_file, processed_rounds, args.end_round,
                n3_pattern_counts, n3_digit_counts,
                n4_pattern_counts, n4_digit_counts
            )
        
        # ランキングを作成（既存のkeisen_master.jsonと同じルールを適用）
        print("\n[Phase 3] ランキングを作成（既存ルール適用）")
        n3_rankings = calculate_rankings_with_rule(n3_digit_counts, n3_pattern_counts)
        n4_rankings = calculate_rankings_with_rule(n4_digit_counts, n4_pattern_counts)
        
        # Phase 4: 統計的信頼性指標を計算
        print("\n[Phase 4] 統計的信頼性指標を計算")
        n3_reliability = calculate_reliability_stats(n3_pattern_counts, n3_digit_counts)
        n4_reliability = calculate_reliability_stats(n4_pattern_counts, n4_digit_counts)
        
        # 結果を出力
        print("\n[出力] 集計結果を出力")
        
        # パターン出現頻度
        n3_frequency_data = {
            f"{col}/{prev}/{prev2}": {'count': count}
            for (col, prev, prev2), count in n3_pattern_counts.items()
        }
        n4_frequency_data = {
            f"{col}/{prev}/{prev2}": {'count': count}
            for (col, prev, prev2), count in n4_pattern_counts.items()
        }
        
        # 出力ファイル名の範囲名を決定（日本語）
        range_name_map = {
            'all': '全範囲',
            '1340': '週5実施開始以降',
            '4801': 'リハーサル導入以降'
        }
        output_suffix = args.output_suffix if args.output_suffix else ""
        range_name = range_name_map.get(output_suffix, 'リハーサル導入以降')  # デフォルトは4801以降
        
        # 出力ディレクトリが存在することを確認
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        
        save_json({
            'n3': n3_frequency_data,
            'n4': n4_frequency_data
        }, OUTPUT_DIR / f"パターン出現頻度_{range_name}.json")
        
        # ランキング結果
        n3_ranking_data = {
            f"{col}/{prev}/{prev2}": ranking_data
            for (col, prev, prev2), ranking_data in n3_rankings.items()
        }
        n4_ranking_data = {
            f"{col}/{prev}/{prev2}": ranking_data
            for (col, prev, prev2), ranking_data in n4_rankings.items()
        }
        
        save_json({
            'n3': n3_ranking_data,
            'n4': n4_ranking_data
        }, OUTPUT_DIR / f"当選数字ランキング_{range_name}.json")
        
        # 信頼性統計
        n3_reliability_data = {
            f"{col}/{prev}/{prev2}": stats
            for (col, prev, prev2), stats in n3_reliability.items()
        }
        n4_reliability_data = {
            f"{col}/{prev}/{prev2}": stats
            for (col, prev, prev2), stats in n4_reliability.items()
        }
        
        save_json({
            'n3': n3_reliability_data,
            'n4': n4_reliability_data
        }, OUTPUT_DIR / f"統計的信頼性指標_{range_name}.json")
        
        # Phase 5: 新keisenマスターデータを生成
        print("\n[Phase 5] 新keisenマスターデータを生成")
        all_pattern_counts = {**n3_pattern_counts, **n4_pattern_counts}
        master = generate_keisen_master(
            {}, all_pattern_counts, n3_rankings, n4_rankings
        )
        
        # 検証
        print("\n[検証] keisenマスターデータの検証")
        is_valid, errors = validate_keisen_master(master)
        if not is_valid:
            print("警告: 検証エラーが見つかりました:")
            for error in errors:
                print(f"  - {error}")
        else:
            print("検証成功: 全てのパターンが正しく定義されています")
        
        # 保存（keisenマスターは data/ 直下に保存）
        save_json(master, DATA_DIR / "keisen_master_new.json")
        
        # 統計サマリー
        print("\n[統計サマリー]")
        print(f"N3パターン総数: {len(n3_pattern_counts)}")
        print(f"N4パターン総数: {len(n4_pattern_counts)}")
        print(f"N3平均出現回数: {np.mean(list(n3_pattern_counts.values())):.2f}")
        print(f"N4平均出現回数: {np.mean(list(n4_pattern_counts.values())):.2f}")
        
        # サンプル数が不足しているパターン
        n3_low_sample = [k for k, v in n3_pattern_counts.items() if v < 5]
        n4_low_sample = [k for k, v in n4_pattern_counts.items() if v < 5]
        print(f"N3サンプル数5未満: {len(n3_low_sample)}パターン")
        print(f"N4サンプル数5未満: {len(n4_low_sample)}パターン")
        
        print("\n" + "=" * 60)
        print("処理完了")
        print("=" * 60)
        
    except Exception as e:
        print(f"エラーが発生しました: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

