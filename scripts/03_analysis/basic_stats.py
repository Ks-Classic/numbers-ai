#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基礎集計スクリプト - 4801回〜6550回
設計書: docs/02_todo/05_data_analysis/05-09_基礎集計設計.md
"""
import pandas as pd
import numpy as np
from collections import Counter
from datetime import datetime
import json
import os


def load_data(csv_path, start_round=4801, end_round=6550):
    df = pd.read_csv(csv_path, dtype=str)
    df['round_number'] = df['round_number'].astype(int)
    df = df[(df['round_number'] >= start_round) & (df['round_number'] <= end_round)]
    df = df[df['n3_winning'].notna() & (df['n3_winning'] != 'NULL')]
    df = df[df['n4_winning'].notna() & (df['n4_winning'] != 'NULL')]
    if 'weekday' in df.columns:
        df['weekday'] = pd.to_numeric(df['weekday'], errors='coerce')
    if 'draw_date' in df.columns:
        df['draw_date'] = pd.to_datetime(df['draw_date'], errors='coerce')
        df['month'] = df['draw_date'].dt.month
    return df


def count_position_match(s1, s2):
    s1, s2 = s1.zfill(len(s2)), s2.zfill(len(s1))
    return sum(c1 == c2 for c1, c2 in zip(s1, s2))


def count_digit_match(s1, s2):
    return sum((Counter(s1) & Counter(s2)).values())


def analyze_zorume(number_str, num_digits):
    s = str(number_str).zfill(num_digits)
    cnt = Counter(s)
    max_repeat = max(cnt.values())
    if max_repeat == num_digits:
        return f'{num_digits}ゾロ'
    elif max_repeat == num_digits - 1:
        return f'{num_digits - 1}ゾロ'
    elif max_repeat == 2:
        return '2ゾロ'
    return 'なし'


def has_consecutive(number_str, num_digits):
    s = str(number_str).zfill(num_digits)
    for i in range(len(s) - 1):
        d1, d2 = int(s[i]), int(s[i + 1])
        if abs(d1 - d2) == 1:
            return True
    return False


def analyze_digit_distribution_by_position(df, col, num_digits):
    result = {f'桁{i + 1}': Counter() for i in range(num_digits)}
    for val in df[col]:
        s = str(val).zfill(num_digits)
        for i, d in enumerate(s):
            result[f'桁{i + 1}'][d] += 1
    return result


def analyze_rehearsal_winning_match(df, reh_col, win_col, num_digits, target_name):
    valid = df[df[reh_col].notna() & (df[reh_col] != 'NULL')].copy()
    total = len(valid)
    if total == 0:
        return None
    pos_counts = Counter()
    dig_counts = Counter()
    for _, row in valid.iterrows():
        reh = str(row[reh_col]).zfill(num_digits)
        win = str(row[win_col]).zfill(num_digits)
        pos_counts[count_position_match(reh, win)] += 1
        dig_counts[count_digit_match(reh, win)] += 1
    return {
        'target': target_name,
        'total': total,
        'position_match': {i: {'count': pos_counts.get(i, 0), 'rate': pos_counts.get(i, 0) / total * 100} for i in range(num_digits + 1)},
        'digit_match': {i: {'count': dig_counts.get(i, 0), 'rate': dig_counts.get(i, 0) / total * 100} for i in range(num_digits + 1)},
        'exact_match': {'count': pos_counts.get(num_digits, 0), 'rate': pos_counts.get(num_digits, 0) / total * 100}
    }


def analyze_digit_difference(df, reh_col, win_col, num_digits, target_name):
    valid = df[df[reh_col].notna() & (df[reh_col] != 'NULL')].copy()
    if len(valid) == 0:
        return None
    numeric_diffs = []
    position_diffs = {f'桁{i + 1}': [] for i in range(num_digits)}
    for _, row in valid.iterrows():
        reh = str(row[reh_col]).zfill(num_digits)
        win = str(row[win_col]).zfill(num_digits)
        numeric_diffs.append(int(win) - int(reh))
        for i in range(num_digits):
            position_diffs[f'桁{i + 1}'].append(int(win[i]) - int(reh[i]))
    return {
        'target': target_name,
        'total': len(valid),
        'numeric_diff': {'mean': np.mean(numeric_diffs), 'std': np.std(numeric_diffs), 'min': min(numeric_diffs), 'max': max(numeric_diffs)},
        'position_diff': {pos: {'mean': np.mean(diffs), 'std': np.std(diffs), 'distribution': dict(Counter(diffs))} for pos, diffs in position_diffs.items()}
    }


def analyze_digit_cooccurrence(df, reh_col, win_col, num_digits, target_name):
    valid = df[df[reh_col].notna() & (df[reh_col] != 'NULL')].copy()
    if len(valid) == 0:
        return None
    cooccur_counts = {str(d): 0 for d in range(10)}
    total = len(valid)
    for _, row in valid.iterrows():
        reh = str(row[reh_col]).zfill(num_digits)
        win = str(row[win_col]).zfill(num_digits)
        for d in set(reh) & set(win):
            cooccur_counts[d] += 1
    return {'target': target_name, 'total': total, 'cooccurrence': {d: {'count': cnt, 'rate': cnt / total * 100} for d, cnt in cooccur_counts.items()}}


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.abspath(os.path.join(script_dir, '../../data/past_results.csv'))
    output_dir = os.path.abspath(os.path.join(script_dir, '../../data/analysis'))
    os.makedirs(output_dir, exist_ok=True)
    
    print(f'Loading: {csv_path}')
    df = load_data(csv_path)
    print(f'Loaded {len(df)} records (4801-6550)')
    
    results = {'generated_at': datetime.now().isoformat(), 'data_range': {'start': 4801, 'end': 6550}, 'total_records': len(df)}
    
    print('\n' + '=' * 70)
    print('基礎集計結果')
    print('=' * 70)
    
    # 1. リハーサル数字データ有効性
    print('\n【1. リハーサル数字データ有効性】')
    rehearsal_validity = {}
    for target, col in [('N3', 'n3_rehearsal'), ('N4', 'n4_rehearsal')]:
        valid_count = len(df[df[col].notna() & (df[col] != 'NULL')])
        rate = valid_count / len(df) * 100
        rehearsal_validity[target] = {'count': valid_count, 'rate': rate}
        print(f'  {target}: {valid_count}回 ({rate:.1f}%)')
    results['rehearsal_validity'] = rehearsal_validity
    
    # 2. リハーサル数字と当選番号の一致分析
    print('\n【2. リハーサル数字と当選番号の一致】')
    match_analysis = {}
    for target, reh_col, win_col, nd in [('N3', 'n3_rehearsal', 'n3_winning', 3), ('N4', 'n4_rehearsal', 'n4_winning', 4)]:
        result = analyze_rehearsal_winning_match(df, reh_col, win_col, nd, target)
        if result:
            match_analysis[target] = result
            print(f'\n  {target} (n={result["total"]})')
            print('    位置一致: ' + ', '.join(f'{i}桁:{result["position_match"][i]["count"]}({result["position_match"][i]["rate"]:.1f}%)' for i in range(nd, -1, -1)))
            print('    数字一致: ' + ', '.join(f'{i}個:{result["digit_match"][i]["count"]}({result["digit_match"][i]["rate"]:.1f}%)' for i in range(nd, -1, -1)))
            print(f'    完全一致: {result["exact_match"]["count"]}回 ({result["exact_match"]["rate"]:.2f}%)')
    results['rehearsal_winning_match'] = match_analysis
    
    # 3. 当選番号の基礎統計
    print('\n【3. 当選番号の基礎統計】')
    winning_stats = {}
    
    print('\n  [数字(0-9)の出現頻度]')
    digit_frequency = {}
    for target, col, nd in [('N3', 'n3_winning', 3), ('N4', 'n4_winning', 4)]:
        digits = ''.join(str(v).zfill(nd) for v in df[col])
        cnt = Counter(digits)
        total_digits = len(digits)
        digit_frequency[target] = {d: {'count': cnt[d], 'rate': cnt[d] / total_digits * 100} for d in '0123456789'}
        print(f'    {target}: ' + ', '.join(f'{d}:{cnt[d]}({cnt[d] / total_digits * 100:.1f}%)' for d in '0123456789'))
    winning_stats['digit_frequency'] = digit_frequency
    
    print('\n  [桁位置別の数字分布]')
    position_distribution = {}
    for target, col, nd in [('N3', 'n3_winning', 3), ('N4', 'n4_winning', 4)]:
        dist = analyze_digit_distribution_by_position(df, col, nd)
        position_distribution[target] = {pos: dict(cnt) for pos, cnt in dist.items()}
        print(f'    {target}:')
        for pos, cnt in dist.items():
            print(f'      {pos}: ' + ', '.join(f'{d}:{cnt[d]}' for d in '0123456789'))
    winning_stats['position_distribution'] = position_distribution
    
    print('\n  [ゾロ目の出現頻度]')
    zorume_stats = {}
    for target, col, nd in [('N3', 'n3_winning', 3), ('N4', 'n4_winning', 4)]:
        zorume_cnt = Counter(analyze_zorume(v, nd) for v in df[col])
        total = len(df)
        zorume_stats[target] = {k: {'count': v, 'rate': v / total * 100} for k, v in zorume_cnt.items()}
        print(f'    {target}: ' + ', '.join(f'{k}:{v}({v / total * 100:.1f}%)' for k, v in zorume_cnt.most_common()))
    winning_stats['zorume'] = zorume_stats
    
    print('\n  [連番の出現頻度]')
    consecutive_stats = {}
    for target, col, nd in [('N3', 'n3_winning', 3), ('N4', 'n4_winning', 4)]:
        consec_count = sum(1 for v in df[col] if has_consecutive(v, nd))
        rate = consec_count / len(df) * 100
        consecutive_stats[target] = {'count': consec_count, 'rate': rate}
        print(f'    {target}: {consec_count}回 ({rate:.1f}%)')
    winning_stats['consecutive'] = consecutive_stats
    
    print('\n  [合計値の分布]')
    sum_stats = {}
    for target, col, nd in [('N3', 'n3_winning', 3), ('N4', 'n4_winning', 4)]:
        sums = [sum(int(d) for d in str(v).zfill(nd)) for v in df[col]]
        sum_stats[target] = {'mean': np.mean(sums), 'std': np.std(sums), 'min': min(sums), 'max': max(sums), 'distribution': dict(Counter(sums))}
        print(f'    {target}: 平均={np.mean(sums):.1f}, 標準偏差={np.std(sums):.1f}, 範囲={min(sums)}-{max(sums)}')
    winning_stats['sum_stats'] = sum_stats
    results['winning_stats'] = winning_stats
    
    # 4. リハーサル数字の基礎集計
    print('\n【4. リハーサル数字の基礎集計】')
    rehearsal_stats = {}
    
    print('\n  [数字(0-9)の出現頻度]')
    reh_digit_freq = {}
    for target, col, nd in [('N3', 'n3_rehearsal', 3), ('N4', 'n4_rehearsal', 4)]:
        valid = df[df[col].notna() & (df[col] != 'NULL')]
        if len(valid) > 0:
            digits = ''.join(str(v).zfill(nd) for v in valid[col])
            cnt = Counter(digits)
            total_digits = len(digits)
            reh_digit_freq[target] = {d: {'count': cnt[d], 'rate': cnt[d] / total_digits * 100} for d in '0123456789'}
            print(f'    {target}: ' + ', '.join(f'{d}:{cnt[d]}({cnt[d] / total_digits * 100:.1f}%)' for d in '0123456789'))
    rehearsal_stats['digit_frequency'] = reh_digit_freq
    
    print('\n  [桁位置別の数字分布]')
    reh_pos_dist = {}
    for target, col, nd in [('N3', 'n3_rehearsal', 3), ('N4', 'n4_rehearsal', 4)]:
        valid = df[df[col].notna() & (df[col] != 'NULL')]
        if len(valid) > 0:
            dist = analyze_digit_distribution_by_position(valid, col, nd)
            reh_pos_dist[target] = {pos: dict(cnt) for pos, cnt in dist.items()}
            print(f'    {target}:')
            for pos, cnt in dist.items():
                print(f'      {pos}: ' + ', '.join(f'{d}:{cnt[d]}' for d in '0123456789'))
    rehearsal_stats['position_distribution'] = reh_pos_dist
    
    print('\n  [ゾロ目の出現頻度]')
    reh_zorume = {}
    for target, col, nd in [('N3', 'n3_rehearsal', 3), ('N4', 'n4_rehearsal', 4)]:
        valid = df[df[col].notna() & (df[col] != 'NULL')]
        if len(valid) > 0:
            zorume_cnt = Counter(analyze_zorume(v, nd) for v in valid[col])
            total = len(valid)
            reh_zorume[target] = {k: {'count': v, 'rate': v / total * 100} for k, v in zorume_cnt.items()}
            print(f'    {target}: ' + ', '.join(f'{k}:{v}({v / total * 100:.1f}%)' for k, v in zorume_cnt.most_common()))
    rehearsal_stats['zorume'] = reh_zorume
    results['rehearsal_stats'] = rehearsal_stats
    
    # 5. リハーサル数字と当選番号の相関
    print('\n【5. リハーサル数字と当選番号の相関】')
    correlation_stats = {}
    
    print('\n  [合計値の相関]')
    sum_correlation = {}
    for target, reh_col, win_col, nd in [('N3', 'n3_rehearsal', 'n3_winning', 3), ('N4', 'n4_rehearsal', 'n4_winning', 4)]:
        valid = df[df[reh_col].notna() & (df[reh_col] != 'NULL')]
        if len(valid) > 0:
            reh_sums = [sum(int(d) for d in str(v).zfill(nd)) for v in valid[reh_col]]
            win_sums = [sum(int(d) for d in str(v).zfill(nd)) for v in valid[win_col]]
            corr = np.corrcoef(reh_sums, win_sums)[0, 1]
            sum_correlation[target] = {'correlation': corr}
            print(f'    {target}: 相関係数={corr:.4f}')
    correlation_stats['sum_correlation'] = sum_correlation
    
    print('\n  [数字の共起分析]')
    cooccurrence = {}
    for target, reh_col, win_col, nd in [('N3', 'n3_rehearsal', 'n3_winning', 3), ('N4', 'n4_rehearsal', 'n4_winning', 4)]:
        result = analyze_digit_cooccurrence(df, reh_col, win_col, nd, target)
        if result:
            cooccurrence[target] = result['cooccurrence']
            print(f'    {target}: ' + ', '.join(f'{d}:{result["cooccurrence"][d]["count"]}({result["cooccurrence"][d]["rate"]:.1f}%)' for d in '0123456789'))
    correlation_stats['cooccurrence'] = cooccurrence
    
    print('\n  [差分の分布]')
    diff_stats = {}
    for target, reh_col, win_col, nd in [('N3', 'n3_rehearsal', 'n3_winning', 3), ('N4', 'n4_rehearsal', 'n4_winning', 4)]:
        result = analyze_digit_difference(df, reh_col, win_col, nd, target)
        if result:
            diff_stats[target] = result
            print(f'    {target}:')
            print(f'      数値差分: 平均={result["numeric_diff"]["mean"]:.1f}, 標準偏差={result["numeric_diff"]["std"]:.1f}')
            for pos, pos_stats in result['position_diff'].items():
                print(f'      {pos}: 平均={pos_stats["mean"]:.2f}, 標準偏差={pos_stats["std"]:.2f}')
    correlation_stats['difference'] = diff_stats
    results['correlation_stats'] = correlation_stats
    
    # 6. 時系列・周期性分析
    print('\n【6. 時系列・周期性分析】')
    time_series_stats = {}
    
    print('\n  [曜日別]')
    weekday_names = ['月', '火', '水', '木', '金', '土', '日']
    valid = df[df['weekday'].notna()]
    weekday_stats = {}
    for wd in range(7):
        cnt = len(valid[valid['weekday'] == wd])
        if cnt > 0:
            weekday_stats[weekday_names[wd]] = {'count': cnt, 'rate': cnt / len(valid) * 100}
            print(f'    {weekday_names[wd]}曜: {cnt}回 ({cnt / len(valid) * 100:.1f}%)')
    time_series_stats['weekday'] = weekday_stats
    
    print('\n  [月別]')
    if 'month' in df.columns:
        valid = df[df['month'].notna()]
        month_stats = {}
        for m in range(1, 13):
            cnt = len(valid[valid['month'] == m])
            if cnt > 0:
                month_stats[f'{m}月'] = {'count': cnt, 'rate': cnt / len(valid) * 100}
                print(f'    {m}月: {cnt}回 ({cnt / len(valid) * 100:.1f}%)')
        time_series_stats['month'] = month_stats
    results['time_series_stats'] = time_series_stats
    
    print('\n' + '=' * 70)
    
    # JSON出力
    json_path = os.path.join(output_dir, 'basic_stats_summary.json')
    def convert_numpy(obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, dict):
            return {k: convert_numpy(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_numpy(i) for i in obj]
        return obj
    results = convert_numpy(results)
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f'\nJSON出力: {json_path}')
    
    # CSV出力
    csv_path = os.path.join(output_dir, 'digit_distribution.csv')
    rows = []
    for target in ['N3', 'N4']:
        if target in winning_stats['position_distribution']:
            for pos, dist in winning_stats['position_distribution'][target].items():
                for digit, count in dist.items():
                    rows.append({'type': '当選番号', 'target': target, 'position': pos, 'digit': digit, 'count': count})
        if target in rehearsal_stats.get('position_distribution', {}):
            for pos, dist in rehearsal_stats['position_distribution'][target].items():
                for digit, count in dist.items():
                    rows.append({'type': 'リハーサル', 'target': target, 'position': pos, 'digit': digit, 'count': count})
    pd.DataFrame(rows).to_csv(csv_path, index=False, encoding='utf-8')
    print(f'CSV出力: {csv_path}')
    
    csv_path2 = os.path.join(output_dir, 'rehearsal_winning_analysis.csv')
    rows2 = []
    for target, data in match_analysis.items():
        for match_type in ['position_match', 'digit_match']:
            for digits, stats in data[match_type].items():
                rows2.append({'target': target, 'match_type': '位置一致' if match_type == 'position_match' else '数字一致', 'digits': digits, 'count': stats['count'], 'rate': stats['rate']})
    pd.DataFrame(rows2).to_csv(csv_path2, index=False, encoding='utf-8')
    print(f'CSV出力: {csv_path2}')
    print('\n完了!')


if __name__ == '__main__':
    main()
