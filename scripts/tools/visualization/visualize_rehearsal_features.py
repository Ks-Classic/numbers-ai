#!/usr/bin/env python3
"""
指定回号の予測表を生成し、リハーサル数字と当選番号の関係性特徴量を可視化するスクリプト

使用方法:
    python3 visualize_rehearsal_features.py [回号]
    
例:
    python3 visualize_rehearsal_features.py 6849
    python3 visualize_rehearsal_features.py 6800
"""
import pandas as pd
import numpy as np
import sys
import argparse
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent if '__file__' in globals() else Path.cwd()
sys.path.append(str(PROJECT_ROOT / 'core'))

from chart_generator import load_keisen_master, generate_chart
from feature_extractor import (
    get_digit_positions,
    get_rehearsal_positions,
    calculate_rehearsal_distance,
    calculate_overlap_count,
    calculate_inverse_ratio
)

# コマンドライン引数の解析
parser = argparse.ArgumentParser(description='リハーサル数字と当選番号の関係性可視化')
parser.add_argument('round_number', type=int, nargs='?', default=6849,
                    help='対象回号（デフォルト: 6849）')
args = parser.parse_args()

round_number = args.round_number

# データの読み込み
DATA_DIR = PROJECT_ROOT / 'data'
train_csv_path = DATA_DIR / 'train_data_from_4801.csv'
train_df = pd.read_csv(train_csv_path)

# 指定回号のデータを取得
if round_number not in train_df['round_number'].values:
    print(f"エラー: 回号 {round_number} のデータが見つかりません。")
    print(f"利用可能な回号範囲: {train_df['round_number'].min()} - {train_df['round_number'].max()}")
    sys.exit(1)

row = train_df[train_df['round_number'] == round_number].iloc[0]

print(f"回号: {round_number}")
print(f"N3 リハーサル数字: {row['n3_rehearsal']}")
print(f"N3 当選番号: {row['n3_winning']}")
print(f"N4 リハーサル数字: {row['n4_rehearsal']}")
print(f"N4 当選番号: {row['n4_winning']}")

# 罫線マスターデータの読み込み
keisen_master = load_keisen_master(DATA_DIR)

# N3の予測表を生成（パターンA1）
target = 'n3'
pattern = 'A1'
rehearsal_digits = str(row[f'{target}_rehearsal']).replace('.0', '').zfill(3)
winning_digits = str(row[f'{target}_winning']).replace('.0', '').zfill(3)

# リハーサル数字が存在するかチェック
if pd.isna(row[f'{target}_rehearsal']) or str(row[f'{target}_rehearsal']) == 'NULL' or str(row[f'{target}_rehearsal']) == 'nan':
    print(f"\nエラー: 回号 {round_number} のN3リハーサル数字が存在しません。")
    sys.exit(1)

print(f"\n{'='*60}")
print(f"N3予測表（パターン{pattern}）の生成と可視化（回号: {round_number}）")
print(f"{'='*60}")

grid, rows, cols = generate_chart(train_df, keisen_master, round_number, pattern, target)

# リハーサル数字と当選番号の位置を取得
rehearsal_positions = get_rehearsal_positions(grid, rows, cols, rehearsal_digits)
winning_positions = get_rehearsal_positions(grid, rows, cols, winning_digits)

# 予測表を色付きHTMLで生成（線でつなぐ版）
# セルのサイズを固定（px単位）
CELL_SIZE = 50
CELL_PADDING = 4
TABLE_MARGIN = 40

# 位置から座標への変換関数
def get_cell_center(row, col):
    """行と列からセルの中心座標を取得"""
    x = TABLE_MARGIN + (col - 1) * CELL_SIZE + CELL_SIZE / 2
    y = TABLE_MARGIN + (row - 1) * CELL_SIZE + CELL_SIZE / 2
    return x, y

# SVG用のパスを生成（隣接する位置のみを結ぶ）
def is_adjacent_horizontal_or_vertical(pos1, pos2):
    """2つの位置が縦横で隣接しているかチェック"""
    row1, col1 = pos1
    row2, col2 = pos2
    row_diff = abs(row1 - row2)
    col_diff = abs(col1 - col2)
    
    # 縦または横で隣接 = 行差または列差が1で、もう一方が0
    return (row_diff == 1 and col_diff == 0) or (row_diff == 0 and col_diff == 1)

def is_adjacent_diagonal(pos1, pos2):
    """2つの位置が斜めで隣接しているかチェック"""
    row1, col1 = pos1
    row2, col2 = pos2
    row_diff = abs(row1 - row2)
    col_diff = abs(col1 - col2)
    
    # 斜めで隣接 = 行差と列差が両方1
    return row_diff == 1 and col_diff == 1

def has_horizontal_or_vertical_neighbor(pos, all_positions):
    """指定位置の周囲8マスに縦横の隣接があるかチェック"""
    row, col = pos
    neighbors = [
        (row - 1, col),  # 上
        (row + 1, col),  # 下
        (row, col - 1),  # 左
        (row, col + 1),  # 右
    ]
    
    for neighbor in neighbors:
        if neighbor in all_positions:
            if is_adjacent_horizontal_or_vertical(pos, neighbor):
                return True
    return False

def generate_path_for_digits(positions, color, offset=0, common_positions_set=None):
    """数字の位置リストからSVGパスを生成（隣接する位置のみを結ぶ）
    
    Args:
        positions: 位置のリスト
        color: 線の色
        offset: 線のオフセット（重なりを避けるため、ピクセル単位）
        common_positions_set: 共通位置のセット（Noneの場合は全て通常描画）
    """
    if len(positions) == 0:
        return ""
    
    if len(positions) == 1:
        # 位置が1つだけの場合は点を描画
        row, col = positions[0]
        x, y = get_cell_center(row, col)
        use_offset = common_positions_set is not None and positions[0] in common_positions_set
        actual_offset = offset if use_offset else 0
        return f'<circle cx="{x + actual_offset}" cy="{y + actual_offset}" r="3" fill="{color}" opacity="0.8"/>'
    
    # 位置をセットに変換（高速検索のため）
    position_set = set(positions)
    
    # グラフを構築して、隣接する位置をグループ化
    paths = []
    visited = set()
    
    def get_neighbors(pos):
        """指定位置の隣接位置（縦横優先、斜めは条件付き）を取得"""
        row, col = pos
        neighbors = []
        
        # 縦横の隣接を優先
        for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            neighbor = (row + dr, col + dc)
            if neighbor in position_set:
                if neighbor not in visited:
                    neighbors.append(neighbor)
        
        # 斜めの隣接（縦横に隣接がない場合のみ）
        if not neighbors:
            for dr, dc in [(1, 1), (1, -1), (-1, 1), (-1, -1)]:
                neighbor = (row + dr, col + dc)
                if neighbor in position_set:
                    # この位置の周囲8マスに縦横の隣接があるかチェック
                    has_hv_neighbor = False
                    for dr2, dc2 in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                        check_pos = (row + dr2, col + dc2)
                        if check_pos in position_set:
                            has_hv_neighbor = True
                            break
                    
                    if not has_hv_neighbor:
                        # 隣接位置の周囲8マスにも縦横の隣接がないかチェック
                        neighbor_has_hv = False
                        for dr2, dc2 in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                            check_pos = (neighbor[0] + dr2, neighbor[1] + dc2)
                            if check_pos in position_set:
                                neighbor_has_hv = True
                                break
                        
                        if not neighbor_has_hv and neighbor not in visited:
                            neighbors.append(neighbor)
        
        return neighbors
    
    # 各未訪問の位置から探索を開始
    for start_pos in positions:
        if start_pos in visited:
            continue
        
        # BFSで連続する位置を探索
        component = []
        queue = [start_pos]
        visited.add(start_pos)
        
        while queue:
            current = queue.pop(0)
            component.append(current)
            
            neighbors = get_neighbors(current)
            for neighbor in neighbors:
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)
        
        # コンポーネントが1つの場合は点を描画
        if len(component) == 1:
            row, col = component[0]
            x, y = get_cell_center(row, col)
            use_offset = common_positions_set is not None and component[0] in common_positions_set
            actual_offset = offset if use_offset else 0
            paths.append(f'<circle cx="{x + actual_offset}" cy="{y + actual_offset}" r="3" fill="{color}" opacity="0.8"/>')
        else:
            # 複数の位置がある場合は、連続する位置を1本のパスとして描画
            # 隣接する位置のリストを作成
            component_set = set(component)
            drawn_pairs = set()
            
            # 隣接関係を構築
            adjacency_map = {}
            for pos in component:
                adjacency_map[pos] = []
            
            for i in range(len(component)):
                for j in range(i + 1, len(component)):
                    pos1 = component[i]
                    pos2 = component[j]
                    
                    # 縦横の隣接をチェック
                    is_hv = is_adjacent_horizontal_or_vertical(pos1, pos2)
                    # 斜めの隣接をチェック（縦横に隣接がない場合のみ）
                    is_diag = False
                    if not is_hv:
                        is_diag = is_adjacent_diagonal(pos1, pos2)
                        if is_diag:
                            # 両方の位置の周囲8マスに縦横の隣接がないかチェック
                            pos1_has_hv = False
                            pos2_has_hv = False
                            
                            for other_pos in component:
                                if other_pos != pos1 and other_pos != pos2:
                                    if is_adjacent_horizontal_or_vertical(pos1, other_pos):
                                        pos1_has_hv = True
                                    if is_adjacent_horizontal_or_vertical(pos2, other_pos):
                                        pos2_has_hv = True
                            
                            if pos1_has_hv or pos2_has_hv:
                                is_diag = False
                    
                    if is_hv or is_diag:
                        pair_key = tuple(sorted([pos1, pos2]))
                        
                        if pair_key not in drawn_pairs:
                            drawn_pairs.add(pair_key)
                            adjacency_map[pos1].append(pos2)
                            adjacency_map[pos2].append(pos1)
            
            # 各隣接ペアを線で結ぶ
            for pair_key in drawn_pairs:
                pos1, pos2 = pair_key
                
                # このペアが共通位置かチェック
                is_common_pair = common_positions_set is not None and \
                               pos1 in common_positions_set and \
                               pos2 in common_positions_set
                actual_offset = offset if is_common_pair else 0
                
                row1, col1 = pos1
                row2, col2 = pos2
                x1, y1 = get_cell_center(row1, col1)
                x2, y2 = get_cell_center(row2, col2)
                
                paths.append(f'<line x1="{x1 + actual_offset}" y1="{y1 + actual_offset}" x2="{x2 + actual_offset}" y2="{y2 + actual_offset}" stroke="{color}" stroke-width="3" opacity="0.8"/>')
    
    return "\n".join(paths)

# リハーサル数字の位置を数字ごとにグループ化
rehearsal_by_digit = {}
for pos in rehearsal_positions:
    digit = grid[pos[0]][pos[1]]
    if digit not in rehearsal_by_digit:
        rehearsal_by_digit[digit] = []
    rehearsal_by_digit[digit].append(pos)

# 当選番号の位置を数字ごとにグループ化
winning_by_digit = {}
for pos in winning_positions:
    digit = grid[pos[0]][pos[1]]
    if digit not in winning_by_digit:
        winning_by_digit[digit] = []
    winning_by_digit[digit].append(pos)

# SVGパスを生成
svg_paths = []
common_positions = set(rehearsal_positions) & set(winning_positions)

# リハーサル数字のパス（赤）- 数字6、3、1すべてを含む
# リハーサル数字全体として、隣接する位置を線でつなげる
path_html = generate_path_for_digits(rehearsal_positions, "#ff0000", offset=-2, common_positions_set=common_positions)
if path_html:
    svg_paths.append(path_html)

# 当選番号のパス（青）- 数字6、8、4すべてを含む
# 当選番号全体として、隣接する位置を線でつなげる
path_html = generate_path_for_digits(winning_positions, "#0000ff", offset=2, common_positions_set=common_positions)
if path_html:
    svg_paths.append(path_html)

svg_paths_html = "\n".join(svg_paths)

# HTMLテーブルを生成
table_width = TABLE_MARGIN * 2 + cols * CELL_SIZE
table_height = TABLE_MARGIN * 2 + rows * CELL_SIZE

html_table = []
html_table.append(f"<div style='position: relative; width: {table_width}px; height: {table_height}px;'>")
html_table.append("<table style='border-collapse: collapse; font-family: monospace; position: relative; z-index: 1; background-color: white;'>")
html_table.append("<tr><th style='border: 1px solid #ccc; padding: 4px; width: 30px; height: 30px; background-color: white;'></th>")
for c in range(1, cols+1):
    html_table.append(f"<th style='border: 1px solid #ccc; padding: 4px; width: {CELL_SIZE-8}px; height: 30px; text-align: center; background-color: white;'>{c}</th>")
html_table.append("</tr>")

for r in range(1, rows+1):
    html_table.append(f"<tr><th style='border: 1px solid #ccc; padding: 4px; width: 30px; height: {CELL_SIZE-8}px; text-align: center; background-color: white;'>{r}</th>")
    for c in range(1, cols+1):
        val = grid[r][c]
        is_rehearsal = (r, c) in rehearsal_positions
        is_winning = (r, c) in winning_positions
        
        if val is None:
            html_table.append(f"<td style='border: 1px solid #ccc; padding: 4px; width: {CELL_SIZE-8}px; height: {CELL_SIZE-8}px; text-align: center; background-color: white;'>.</td>")
        else:
            # 背景色は白に統一（線で識別するため）
            html_table.append(f"<td style='border: 1px solid #ccc; padding: 4px; width: {CELL_SIZE-8}px; height: {CELL_SIZE-8}px; text-align: center; background-color: white; font-weight: bold; font-size: 18px;'>{val}</td>")
    html_table.append("</tr>")
html_table.append("</table>")
# SVGレイヤーをテーブルの上に配置（z-index: 3）
html_table.append(f"<svg width='{table_width}' height='{table_height}' style='position: absolute; top: 0; left: 0; z-index: 3; pointer-events: none;'>")
html_table.append(svg_paths_html)
html_table.append("</svg>")
html_table.append("</div>")

html_content = "\n".join(html_table)

# 各数字（0-9）の特徴量を計算して解説用のデータを準備
feature_explanations = []
for digit in range(10):
    digit_positions = get_digit_positions(grid, rows, cols, digit)
    
    if len(digit_positions) == 0:
        continue
    
    rehearsal_dist = calculate_rehearsal_distance(digit_positions, rehearsal_positions)
    overlap = calculate_overlap_count(digit_positions, rehearsal_positions)
    inverse_ratio = calculate_inverse_ratio(digit_positions, rehearsal_positions, grid)
    
    is_winning = str(digit) in winning_digits
    is_rehearsal = str(digit) in rehearsal_digits
    
    # 具体例の計算
    example_distances = []
    if len(digit_positions) > 0 and len(rehearsal_positions) > 0:
        for c_pos in digit_positions[:3]:  # 最初の3つの位置を例として
            min_dist = float('inf')
            nearest_rehearsal = None
            for r_pos in rehearsal_positions:
                dist = np.sqrt((c_pos[0] - r_pos[0]) ** 2 + (c_pos[1] - r_pos[1]) ** 2)
                if dist < min_dist:
                    min_dist = dist
                    nearest_rehearsal = r_pos
            if nearest_rehearsal is not None:
                example_distances.append({
                    'candidate': c_pos,
                    'nearest_rehearsal': nearest_rehearsal,
                    'distance': min_dist
                })
    
    feature_explanations.append({
        'digit': digit,
        'positions_count': len(digit_positions),
        'rehearsal_distance': rehearsal_dist,
        'overlap_count': overlap,
        'inverse_ratio': inverse_ratio,
        'is_winning': is_winning,
        'is_rehearsal': is_rehearsal,
        'example_distances': example_distances[:3]  # 最初の3つだけ
    })

# 特徴量解説のHTMLを生成
explanation_html = f"""
<div style="margin-top: 40px; padding: 20px; background-color: #f9f9f9; border-radius: 8px;">
    <h2>特徴量の解説（{round_number}回のケース）</h2>
    <p style="margin-bottom: 20px;">
        <strong>リハーサル数字: {rehearsal_digits}</strong> | 
        <strong>当選番号: {winning_digits}</strong>
    </p>
    
    <h3>1. rehearsal_distance（リハーサルとの距離）</h3>
    <p style="margin-left: 20px; margin-bottom: 15px;">
        各候補数字の位置から最も近いリハーサル数字の位置までのユークリッド距離を計算し、その平均値を求めます。<br>
        <strong>計算式:</strong> 各候補位置について、最も近いリハーサル位置までの距離を求め、それらの平均値
    </p>
    
    <h3>2. overlap_count（リハーサルとの重なり）</h3>
    <p style="margin-left: 20px; margin-bottom: 15px;">
        候補数字とリハーサル数字が同じ位置（マス）にある回数をカウントします。<br>
        <strong>計算式:</strong> 候補位置のセットとリハーサル位置のセットの共通部分の要素数
    </p>
    
    <h3>3. inverse_ratio（裏数字の割合）</h3>
    <p style="margin-left: 20px; margin-bottom: 15px;">
        候補数字がリハーサル数字の「裏数字」である割合を計算します。<br>
        <strong>裏数字の定義:</strong> 数字nの裏数字は (9-n) です（例: 0↔9, 1↔8, 2↔7, 3↔6, 4↔5）<br>
        <strong>計算式:</strong> リハーサル位置と同じ位置にある候補数字のうち、それがリハーサル数字の裏数字である割合
    </p>
    
    <h3>各数字の特徴量値（{round_number}回）</h3>
    <table style="border-collapse: collapse; width: 100%; margin-top: 20px; background-color: white;">
        <thead>
            <tr style="background-color: #e0e0e0;">
                <th style="border: 1px solid #ccc; padding: 8px; text-align: center;">数字</th>
                <th style="border: 1px solid #ccc; padding: 8px; text-align: center;">位置数</th>
                <th style="border: 1px solid #ccc; padding: 8px; text-align: center;">rehearsal_distance</th>
                <th style="border: 1px solid #ccc; padding: 8px; text-align: center;">overlap_count</th>
                <th style="border: 1px solid #ccc; padding: 8px; text-align: center;">inverse_ratio</th>
                <th style="border: 1px solid #ccc; padding: 8px; text-align: center;">当選</th>
            </tr>
        </thead>
        <tbody>
"""
for feat in feature_explanations:
    digit = feat['digit']
    bg_color = ""
    if feat['is_rehearsal']:
        bg_color = "background-color: #ffe6e6;"
    elif feat['is_winning']:
        bg_color = "background-color: #e6e6ff;"
    
    explanation_html += f"""
            <tr style="{bg_color}">
                <td style="border: 1px solid #ccc; padding: 8px; text-align: center; font-weight: bold;">{digit}</td>
                <td style="border: 1px solid #ccc; padding: 8px; text-align: center;">{feat['positions_count']}</td>
                <td style="border: 1px solid #ccc; padding: 8px; text-align: center;">{feat['rehearsal_distance']:.3f}</td>
                <td style="border: 1px solid #ccc; padding: 8px; text-align: center;">{feat['overlap_count']}</td>
                <td style="border: 1px solid #ccc; padding: 8px; text-align: center;">{feat['inverse_ratio']:.3f}</td>
                <td style="border: 1px solid #ccc; padding: 8px; text-align: center;">{'✓' if feat['is_winning'] else '✗'}</td>
            </tr>
"""
explanation_html += """
        </tbody>
    </table>
    
    <div style="margin-top: 30px;">
        <h4>具体例: 数字6の場合（リハーサル数字「631」に含まれる）</h4>
        <p style="margin-left: 20px;">
            <strong>リハーサル数字「631」に含まれる数字6:</strong><br>
            <ul style="margin-left: 40px;">
"""
# 数字6の具体例を追加
digit_6_feat = next((f for f in feature_explanations if f['digit'] == 6), None)
if digit_6_feat:
    explanation_html += f"""
                <li>数字6の位置数: {digit_6_feat['positions_count']}個</li>
                <li><strong>overlap_count = {digit_6_feat['overlap_count']}:</strong> 数字6の位置とリハーサル数字「631」の位置が{digit_6_feat['overlap_count']}箇所で一致しています。これは、数字6がリハーサル数字に含まれるため、数字6の位置の多くがリハーサル位置と重なっていることを意味します。</li>
                <li><strong>rehearsal_distance = {digit_6_feat['rehearsal_distance']:.3f}:</strong> 数字6の各位置から最も近いリハーサル位置までの距離の平均が{digit_6_feat['rehearsal_distance']:.3f}です。この値が0に近いほど、数字6の位置がリハーサル位置に近いことを示します。</li>
                <li><strong>inverse_ratio = {digit_6_feat['inverse_ratio']:.3f}:</strong> 数字6の裏数字は3です。リハーサル数字「631」には3が含まれますが、数字6の位置でリハーサル位置と同じ位置にあるもののうち、その位置の数字が3（裏数字）である割合は{digit_6_feat['inverse_ratio']:.3f}です。</li>
            </ul>
    """
explanation_html += """
        </p>
        
        <h4>具体例: 数字8の場合（当選番号「684」に含まれる）</h4>
        <p style="margin-left: 20px;">
"""
digit_8_feat = next((f for f in feature_explanations if f['digit'] == 8), None)
if digit_8_feat:
    explanation_html += f"""
            <ul style="margin-left: 40px;">
                <li>数字8の位置数: {digit_8_feat['positions_count']}個</li>
                <li><strong>overlap_count = {digit_8_feat['overlap_count']}:</strong> 数字8の位置とリハーサル数字「631」の位置が{digit_8_feat['overlap_count']}箇所で一致しています。数字8はリハーサル数字に含まれないため、重なりは0です。</li>
                <li><strong>rehearsal_distance = {digit_8_feat['rehearsal_distance']:.3f}:</strong> 数字8の各位置から最も近いリハーサル位置までの距離の平均が{digit_8_feat['rehearsal_distance']:.3f}です。この値が大きいほど、数字8の位置がリハーサル位置から遠いことを示します。</li>
                <li><strong>inverse_ratio = {digit_8_feat['inverse_ratio']:.3f}:</strong> 数字8の裏数字は1です。リハーサル数字「631」には1が含まれますが、数字8の位置でリハーサル位置と同じ位置にあるもののうち、その位置の数字が1（裏数字）である割合は{digit_8_feat['inverse_ratio']:.3f}です。</li>
            </ul>
    """
explanation_html += """
        </p>
        
        <h4>具体例: 数字4の場合（当選番号「684」に含まれる）</h4>
        <p style="margin-left: 20px;">
"""
digit_4_feat = next((f for f in feature_explanations if f['digit'] == 4), None)
if digit_4_feat:
    explanation_html += f"""
            <ul style="margin-left: 40px;">
                <li>数字4の位置数: {digit_4_feat['positions_count']}個</li>
                <li><strong>overlap_count = {digit_4_feat['overlap_count']}:</strong> 数字4の位置とリハーサル数字「631」の位置が{digit_4_feat['overlap_count']}箇所で一致しています。数字4はリハーサル数字に含まれないため、重なりは0です。</li>
                <li><strong>rehearsal_distance = {digit_4_feat['rehearsal_distance']:.3f}:</strong> 数字4の各位置から最も近いリハーサル位置までの距離の平均が{digit_4_feat['rehearsal_distance']:.3f}です。この値が大きいほど、数字4の位置がリハーサル位置から遠いことを示します。</li>
                <li><strong>inverse_ratio = {digit_4_feat['inverse_ratio']:.3f}:</strong> 数字4の裏数字は5です。リハーサル数字「631」には5が含まれないため、裏数字の割合は{digit_4_feat['inverse_ratio']:.3f}です。</li>
            </ul>
    """
explanation_html += """
        </p>
        
        <h4>特徴量の意味</h4>
        <p style="margin-left: 20px;">
            これらの特徴量は、予測モデルが学習する際に使用されます。各数字について、リハーサル数字との関係性を数値化することで、
            モデルは「リハーサル数字に近い位置の数字は当選しやすいか？」「リハーサル数字と同じ位置の数字は当選しやすいか？」
            といったパターンを学習することができます。
        </p>
    </div>
</div>
"""

# HTMLファイルとして保存
html_file = PROJECT_ROOT / 'docs' / 'report' / f'rehearsal_chart_{round_number}.html'
with open(html_file, 'w', encoding='utf-8') as f:
    f.write(f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{round_number}回予測表 - リハーサル数字と当選番号の可視化</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            padding: 20px;
        }}
        h1 {{
            color: #333;
        }}
        h2 {{
            color: #555;
            margin-top: 30px;
        }}
        h3 {{
            color: #666;
            margin-top: 20px;
        }}
        h4 {{
            color: #777;
            margin-top: 15px;
        }}
        .legend {{
            margin: 20px 0;
            padding: 10px;
            background-color: #f5f5f5;
            border-radius: 5px;
        }}
        .legend-item {{
            margin: 5px 0;
        }}
        .main-content {{
            display: flex;
            gap: 30px;
            align-items: flex-start;
        }}
        .chart-container {{
            flex: 0 0 auto;
        }}
        .explanation-container {{
            flex: 1 1 auto;
            min-width: 400px;
        }}
        @media (max-width: 1200px) {{
            .main-content {{
                flex-direction: column;
            }}
        }}
    </style>
</head>
<body>
    <h1>{round_number}回予測表（N3、パターンA1）</h1>
    <div class="legend">
        <h3>凡例:</h3>
        <div class="legend-item">
            <svg width="30" height="3" style="vertical-align: middle;"><line x1="0" y1="1.5" x2="30" y2="1.5" stroke="#ff0000" stroke-width="3" opacity="0.7"/></svg>
            <span style="margin-left: 10px;">リハーサル数字（631）</span>
        </div>
        <div class="legend-item">
            <svg width="30" height="3" style="vertical-align: middle;"><line x1="0" y1="1.5" x2="30" y2="1.5" stroke="#0000ff" stroke-width="3" opacity="0.7"/></svg>
            <span style="margin-left: 10px;">当選番号（684）</span>
        </div>
    </div>
    <div class="main-content">
        <div class="chart-container">
            {html_content}
        </div>
        <div class="explanation-container">
            {explanation_html}
        </div>
    </div>
</body>
</html>""")

print(f"\n色付き予測表をHTMLファイルとして保存しました: {html_file}")
print("ブラウザで開いて確認してください。")

print(f"\nリハーサル数字 '{rehearsal_digits}' の位置:")
for pos in rehearsal_positions:
    print(f"  ({pos[0]}, {pos[1]}) - 数字: {grid[pos[0]][pos[1]]}")

print(f"\n当選番号 '{winning_digits}' の位置:")
for pos in winning_positions:
    print(f"  ({pos[0]}, {pos[1]}) - 数字: {grid[pos[0]][pos[1]]}")

# 各数字（0-9）の特徴量を計算
print(f"\n{'='*60}")
print("各数字の関係性特徴量")
print(f"{'='*60}")

results = []
for digit in range(10):
    digit_positions = get_digit_positions(grid, rows, cols, digit)
    
    if len(digit_positions) == 0:
        continue
    
    rehearsal_dist = calculate_rehearsal_distance(digit_positions, rehearsal_positions)
    overlap = calculate_overlap_count(digit_positions, rehearsal_positions)
    inverse_ratio = calculate_inverse_ratio(digit_positions, rehearsal_positions, grid)
    
    is_winning = str(digit) in winning_digits
    
    print(f"\n数字 {digit}:")
    print(f"  位置数: {len(digit_positions)}")
    print(f"  リハーサルとの距離: {rehearsal_dist:.3f}")
    print(f"  リハーサルとの重なり: {overlap}")
    print(f"  裏数字の割合: {inverse_ratio:.3f}")
    print(f"  当選番号に含まれる: {'✓' if is_winning else '✗'}")
    
    results.append({
        'digit': digit,
        'positions_count': len(digit_positions),
        'rehearsal_distance': rehearsal_dist,
        'overlap_count': overlap,
        'inverse_ratio': inverse_ratio,
        'is_winning': is_winning
    })

# 予測表をASCIIで表示（簡易版）
print(f"\n予測表（行数: {rows}, 列数: {cols}）:")
print("色付きの詳細版はHTMLファイルをご確認ください。")

# 結果をファイルに保存
import json
output_file = PROJECT_ROOT / 'docs' / 'report' / f'rehearsal_visualization_{round_number}.json'
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump({
        'round_number': round_number,
        'target': target,
        'pattern': pattern,
        'rehearsal_digits': rehearsal_digits,
        'winning_digits': winning_digits,
        'rehearsal_positions': [[int(p[0]), int(p[1])] for p in rehearsal_positions],
        'winning_positions': [[int(p[0]), int(p[1])] for p in winning_positions],
        'feature_results': results,
        'grid_size': {'rows': rows, 'cols': cols}
    }, f, indent=2, ensure_ascii=False)

print(f"\n結果を保存しました: {output_file}")

