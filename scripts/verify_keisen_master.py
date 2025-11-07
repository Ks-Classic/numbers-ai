#!/usr/bin/env python3
"""
keisen_master.json検証スクリプト
1340-6391回のデータから、前々回・前回パターンごとの当選数字の出現回数を集計し、
既存のkeisen_master.jsonの予測出目が実データの上位に含まれているかを検証する。
"""

import pandas as pd
import json
import numpy as np
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Tuple

# データディレクトリのパス
DATA_DIR = Path(__file__).parent.parent / "data"
OUTPUT_DIR = DATA_DIR

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

def filter_data_range(df: pd.DataFrame, start_round: int = 1340, end_round: int = 6391) -> pd.DataFrame:
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
    """パターン出現頻度を集計"""
    pattern_counts = defaultdict(int)
    digit_counts = defaultdict(lambda: defaultdict(int))
    
    for _, row in df.iterrows():
        prev = row[prev_col]
        prev2 = row[prev2_col]
        winning = row[winning_col]
        
        # 各桁を抽出
        prev_digits = extract_digits(prev, len(columns))
        prev2_digits = extract_digits(prev2, len(columns))
        winning_digits = extract_digits(winning, len(columns))
        
        # 各桁ごとにパターンを集計
        for i, column in enumerate(columns):
            prev_digit = str(prev_digits[i])  # 前回の該当桁
            prev2_digit = str(prev2_digits[i])  # 前々回の該当桁
            winning_digit = winning_digits[i]
            
            # パターン出現回数をカウント
            # keisen_master.jsonの構造は[前々回][前回]なので、pattern_keyも(column, 前々回, 前回)の順序にする
            pattern_key = (column, prev2_digit, prev_digit)
            pattern_counts[pattern_key] += 1
            
            # 当選数字の出現回数をカウント
            digit_counts[pattern_key][winning_digit] += 1
    
    return pattern_counts, digit_counts

def calculate_rankings(digit_counts: Dict) -> Dict:
    """ランキングを作成（出現回数1回以上の数字を全て含める）"""
    rankings = {}
    
    for pattern_key, digit_count_dict in digit_counts.items():
        # 出現回数の降順でソート、同率の場合は数字の昇順でソート
        sorted_digits = sorted(
            digit_count_dict.items(),
            key=lambda x: (-x[1], x[0])
        )
        
        # 出現回数1回以上の数字を全て含める（制限なし）
        all_digits = [digit for digit, count in sorted_digits if count >= 1]
        counts_dict = {str(digit): count for digit, count in sorted_digits}
        
        rankings[pattern_key] = {
            'ranking': all_digits,
            'counts': counts_dict,
            'total_samples': sum(digit_count_dict.values())
        }
    
    return rankings

def load_keisen_master() -> Dict:
    """既存のkeisen_master.jsonを読み込む"""
    file_path = DATA_DIR / "keisen_master.json"
    if not file_path.exists():
        raise FileNotFoundError(f"keisen_master.jsonが見つかりません: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        master = json.load(f)
    
    print(f"keisen_master.json読み込み完了")
    return master

def verify_keisen_master(actual_rankings: Dict, keisen_master: Dict, columns: List[str], n_type: str) -> List[Dict]:
    """keisen_master.jsonの予測出目が実データの上位に含まれているかを検証"""
    verification_results = []
    
    for column in columns:
        if column not in keisen_master[n_type]:
            continue
        
        # keisen_master.jsonの構造は[前々回][前回]
        for prev2_digit in range(10):
            prev2_str = str(prev2_digit)  # 前々回
            if prev2_str not in keisen_master[n_type][column]:
                continue
            
            for prev_digit in range(10):
                prev_str = str(prev_digit)  # 前回
                if prev_str not in keisen_master[n_type][column][prev2_str]:
                    continue
                
                # pattern_keyは(column, 前々回, 前回)の順序
                # keisen_master.jsonの構造は[前々回][前回]なので、順序を合わせる
                pattern_key = (column, prev2_str, prev_str)
                keisen_predictions = keisen_master[n_type][column][prev2_str][prev_str]
                
                if pattern_key not in actual_rankings:
                    verification_results.append({
                        'n_type': n_type,
                        'column': column,
                        'prev': prev_str,
                        'prev2': prev2_str,
                        'status': 'NO_DATA',
                        'keisen_predictions': keisen_predictions,
                        'actual_ranking': [],
                        'actual_counts': {},
                        'total_samples': 0,
                        'match_count': 0,
                        'match_rate': 0.0
                    })
                    continue
                
                actual_ranking = actual_rankings[pattern_key]['ranking']
                actual_counts = actual_rankings[pattern_key]['counts']
                total_samples = actual_rankings[pattern_key]['total_samples']
                
                # keisen_master.jsonの予測出目が実データの上位に含まれているか確認
                # keisen_master.jsonの予測出目の数だけ、実データの上位から取得
                keisen_count = len(keisen_predictions)
                if keisen_count > 0:
                    actual_top_n = actual_ranking[:keisen_count] if len(actual_ranking) >= keisen_count else actual_ranking
                    
                    # 一致数をカウント
                    match_count = len(set(keisen_predictions) & set(actual_top_n))
                    match_rate = match_count / keisen_count if keisen_count > 0 else 0.0
                    
                    # 全てのkeisen予測出目が実データの上位に含まれているか
                    all_matched = all(pred in actual_top_n for pred in keisen_predictions)
                    
                    status = 'MATCH' if all_matched else 'PARTIAL_MATCH' if match_count > 0 else 'MISMATCH'
                else:
                    match_count = 0
                    match_rate = 0.0
                    status = 'EMPTY'
                    actual_top_n = []
                
                verification_results.append({
                    'n_type': n_type,
                    'column': column,
                    'prev': prev_str,
                    'prev2': prev2_str,
                    'status': status,
                    'keisen_predictions': keisen_predictions,
                    'keisen_count': len(keisen_predictions),
                    'actual_ranking': actual_ranking,
                    'actual_top_n': actual_top_n[:len(keisen_predictions)] if keisen_predictions else [],
                    'actual_counts': actual_counts,
                    'total_samples': total_samples,
                    'match_count': match_count,
                    'match_rate': match_rate
                })
    
    return verification_results

def save_verification_results(results: List[Dict], filepath: Path):
    """検証結果をJSON形式で保存"""
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"検証結果保存完了: {filepath}")

def save_verification_summary(results: List[Dict], filepath: Path):
    """検証結果のサマリーをCSV形式で保存"""
    summary_data = []
    for result in results:
        summary_data.append({
            'n_type': result['n_type'],
            'column': result['column'],
            'prev': result['prev'],
            'prev2': result['prev2'],
            'status': result['status'],
            'keisen_count': result.get('keisen_count', 0),
            'total_samples': result.get('total_samples', 0),
            'match_count': result.get('match_count', 0),
            'match_rate': result.get('match_rate', 0.0),
            'keisen_predictions': ','.join(map(str, result['keisen_predictions'])),
            'actual_top_n': ','.join(map(str, result.get('actual_top_n', [])))
        })
    
    df = pd.DataFrame(summary_data)
    df.to_csv(filepath, index=False, encoding='utf-8-sig')
    print(f"検証サマリー保存完了: {filepath}")

def main():
    """メイン処理"""
    print("=" * 60)
    print("keisen_master.json検証スクリプト開始")
    print("=" * 60)
    
    try:
        # Phase 1: データ準備
        print("\n[Phase 1] データ準備")
        df = load_past_results()
        df = filter_data_range(df, start_round=1340, end_round=6391)
        df = clean_data(df)
        df = extract_previous_numbers(df)
        
        # Phase 2: パターン出現頻度と当選数字の分布を集計
        print("\n[Phase 2] パターン出現頻度と当選数字の分布を集計")
        n3_pattern_counts, n3_digit_counts = count_pattern_frequency(
            df, N3_COLUMNS, 'prev_n3', 'prev2_n3', 'n3_winning'
        )
        n4_pattern_counts, n4_digit_counts = count_pattern_frequency(
            df, N4_COLUMNS, 'prev_n4', 'prev2_n4', 'n4_winning'
        )
        
        # ランキングを作成（出現回数1回以上の数字を全て含める）
        print("\n[Phase 3] ランキングを作成")
        n3_rankings = calculate_rankings(n3_digit_counts)
        n4_rankings = calculate_rankings(n4_digit_counts)
        
        # Phase 4: keisen_master.jsonを読み込む
        print("\n[Phase 4] keisen_master.jsonを読み込む")
        keisen_master = load_keisen_master()
        
        # Phase 5: 検証
        print("\n[Phase 5] keisen_master.jsonの検証")
        n3_verification = verify_keisen_master(n3_rankings, keisen_master, N3_COLUMNS, 'n3')
        n4_verification = verify_keisen_master(n4_rankings, keisen_master, N4_COLUMNS, 'n4')
        
        all_verification = n3_verification + n4_verification
        
        # 結果を保存
        print("\n[出力] 検証結果を出力")
        save_verification_results(all_verification, OUTPUT_DIR / "keisen_master_verification.json")
        save_verification_summary(all_verification, OUTPUT_DIR / "keisen_master_verification_summary.csv")
        
        # 統計サマリー
        print("\n[統計サマリー]")
        total_patterns = len(all_verification)
        match_patterns = len([r for r in all_verification if r['status'] == 'MATCH'])
        partial_match_patterns = len([r for r in all_verification if r['status'] == 'PARTIAL_MATCH'])
        mismatch_patterns = len([r for r in all_verification if r['status'] == 'MISMATCH'])
        no_data_patterns = len([r for r in all_verification if r['status'] == 'NO_DATA'])
        empty_patterns = len([r for r in all_verification if r['status'] == 'EMPTY'])
        
        print(f"総パターン数: {total_patterns}")
        print(f"完全一致: {match_patterns} ({match_patterns/total_patterns*100:.1f}%)")
        print(f"部分一致: {partial_match_patterns} ({partial_match_patterns/total_patterns*100:.1f}%)")
        print(f"不一致: {mismatch_patterns} ({mismatch_patterns/total_patterns*100:.1f}%)")
        print(f"データなし: {no_data_patterns} ({no_data_patterns/total_patterns*100:.1f}%)")
        print(f"空パターン: {empty_patterns} ({empty_patterns/total_patterns*100:.1f}%)")
        
        # 平均一致率
        match_rates = [r['match_rate'] for r in all_verification if r['status'] != 'NO_DATA' and r['status'] != 'EMPTY']
        if match_rates:
            print(f"平均一致率: {np.mean(match_rates):.2%}")
        
        print("\n" + "=" * 60)
        print("処理完了")
        print("=" * 60)
        
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        raise

if __name__ == "__main__":
    main()

