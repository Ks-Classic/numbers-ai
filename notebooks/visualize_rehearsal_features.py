#!/usr/bin/env python3
"""
6849回の予測表を生成し、リハーサル数字と当選番号の関係性特徴量を可視化するスクリプト
"""
import pandas as pd
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent if '__file__' in globals() else Path.cwd()
sys.path.append(str(PROJECT_ROOT / 'notebooks'))

from chart_generator import load_keisen_master, generate_chart
from feature_extractor import (
    get_digit_positions,
    get_rehearsal_positions,
    calculate_rehearsal_distance,
    calculate_overlap_count,
    calculate_inverse_ratio
)

# データの読み込み
DATA_DIR = PROJECT_ROOT / 'data'
train_csv_path = DATA_DIR / 'train_data_from_4801.csv'
train_df = pd.read_csv(train_csv_path)

# 6849回のデータを取得
round_number = 6849
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

print(f"\n{'='*60}")
print(f"N3予測表（パターン{pattern}）の生成と可視化")
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
def is_adjacent(pos1, pos2):
    """2つの位置が縦横斜めで隣接しているかチェック"""
    row1, col1 = pos1
    row2, col2 = pos2
    row_diff = abs(row1 - row2)
    col_diff = abs(col1 - col2)
    
    # 縦横斜めで隣接 = 行差と列差の両方が1以下で、かつ少なくとも一方が1
    return row_diff <= 1 and col_diff <= 1 and (row_diff == 1 or col_diff == 1)

def generate_path_for_digits(positions, color):
    """数字の位置リストからSVGパスを生成（隣接する位置のみを結ぶ）"""
    if len(positions) == 0:
        return ""
    
    if len(positions) == 1:
        # 位置が1つだけの場合は点を描画
        row, col = positions[0]
        x, y = get_cell_center(row, col)
        return f'<circle cx="{x}" cy="{y}" r="3" fill="{color}" opacity="0.8"/>'
    
    # すべての隣接ペアに対して線を描画
    paths = []
    drawn_pairs = set()  # 既に描画したペアを記録
    
    for i in range(len(positions)):
        for j in range(i + 1, len(positions)):
            pos1 = positions[i]
            pos2 = positions[j]
            
            # 隣接しているかチェック
            if is_adjacent(pos1, pos2):
                # ペアを正規化（順序を統一）
                pair_key = tuple(sorted([pos1, pos2]))
                
                if pair_key not in drawn_pairs:
                    drawn_pairs.add(pair_key)
                    
                    row1, col1 = pos1
                    row2, col2 = pos2
                    x1, y1 = get_cell_center(row1, col1)
                    x2, y2 = get_cell_center(row2, col2)
                    
                    paths.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="3" opacity="0.8"/>')
    
    # 孤立した位置（隣接する位置がない）は点で描画
    connected_positions = set()
    for pair_key in drawn_pairs:
        connected_positions.add(pair_key[0])
        connected_positions.add(pair_key[1])
    
    for pos in positions:
        if pos not in connected_positions:
            row, col = pos
            x, y = get_cell_center(row, col)
            paths.append(f'<circle cx="{x}" cy="{y}" r="3" fill="{color}" opacity="0.8"/>')
    
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
# リハーサル数字のパス（赤）
for digit, positions in sorted(rehearsal_by_digit.items()):
    path_html = generate_path_for_digits(positions, "#ff0000")
    if path_html:
        svg_paths.append(path_html)

# 当選番号のパス（青）
for digit, positions in sorted(winning_by_digit.items()):
    path_html = generate_path_for_digits(positions, "#0000ff")
    if path_html:
        svg_paths.append(path_html)

# 両方に含まれる位置（緑）
common_positions = set(rehearsal_positions) & set(winning_positions)
if common_positions:
    common_by_digit = {}
    for pos in common_positions:
        digit = grid[pos[0]][pos[1]]
        if digit not in common_by_digit:
            common_by_digit[digit] = []
        common_by_digit[digit].append(pos)
    
    for digit, positions in sorted(common_by_digit.items()):
        path_html = generate_path_for_digits(positions, "#00ff00")
        if path_html:
            # 緑の場合は太く
            path_html = path_html.replace('stroke-width="3"', 'stroke-width="4"')
            path_html = path_html.replace('stroke-width="4"', 'stroke-width="4"', 1)  # 最初の1つだけ
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

# HTMLファイルとして保存
html_file = PROJECT_ROOT / 'docs' / 'report' / 'rehearsal_chart_6849.html'
with open(html_file, 'w', encoding='utf-8') as f:
    f.write(f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>6849回予測表 - リハーサル数字と当選番号の可視化</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            padding: 20px;
        }}
        h1 {{
            color: #333;
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
    </style>
</head>
<body>
    <h1>6849回予測表（N3、パターンA1）</h1>
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
        <div class="legend-item">
            <svg width="30" height="3" style="vertical-align: middle;"><line x1="0" y1="1.5" x2="30" y2="1.5" stroke="#00ff00" stroke-width="3" opacity="0.8"/></svg>
            <span style="margin-left: 10px;">リハーサルと当選の両方</span>
        </div>
    </div>
    {html_content}
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
output_file = PROJECT_ROOT / 'docs' / 'report' / 'rehearsal_visualization_6849.json'
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

