#!/usr/bin/env python3
"""N3テーブルのデータ抽出をテストするスクリプト"""
import requests
from bs4 import BeautifulSoup
import re
import sys
sys.path.insert(0, 'scripts')
from fetch_past_results import extract_number_from_cell, parse_n3_table

url = 'https://www.hpfree.com/numbers/rehearsal2021-1.html'
print(f"ページを取得中: {url}...")

r = requests.get(url)
r.encoding = 'shift-jis'
soup = BeautifulSoup(r.text, 'html.parser')

# N3テーブルを直接テスト
print("\nN3テーブルを解析中...")
n3_data = parse_n3_table(soup, url=url)

print(f"\n取得したN3データ: {len(n3_data)}件")
if n3_data:
    for round_num in sorted(n3_data.keys(), reverse=True)[:5]:
        data = n3_data[round_num]
        print(f"  第{round_num}回: N3当選={data['n3_winning']}, N3リハーサル={data['n3_rehearsal']}")
else:
    print("  N3データが取得できませんでした")
    
    # デバッグ: 8列のテーブルを確認
    tables = soup.find_all('table')
    print(f"\nデバッグ: テーブル数={len(tables)}")
    for i, table in enumerate(tables):
        rows = table.find_all('tr')
        if not rows:
            continue
        first_row_cells = rows[0].find_all(['td', 'th'])
        col_count = len(first_row_cells)
        if col_count == 8:
            print(f"\n  テーブル{i+1}は8列です")
            # 最初のデータ行を確認
            for row in rows:
                cells = row.find_all(['td', 'th'])
                row_text = row.get_text().strip()
                if '第5726回' in row_text and len(cells) == 8:
                    print(f"    第5726回の行を発見:")
                    for j, cell in enumerate(cells):
                        cell_text = cell.get_text().strip()
                        digit = extract_number_from_cell(cell_text)
                        print(f"      セル{j}: '{cell_text}' -> 抽出された数字: '{digit}'")
                    break

