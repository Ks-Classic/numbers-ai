#!/usr/bin/env python3
"""N3テーブルのデータを確認するスクリプト"""
import requests
from bs4 import BeautifulSoup
import re

url = 'https://www.hpfree.com/numbers/rehearsal2021-1.html'
print(f"ページを取得中: {url}...")

r = requests.get(url)
r.encoding = 'shift-jis'
soup = BeautifulSoup(r.text, 'html.parser')

tables = soup.find_all('table')

# N3テーブル（8列）を探す
for i, table in enumerate(tables):
    rows = table.find_all('tr')
    if not rows:
        continue
    
    first_row_cells = rows[0].find_all(['td', 'th'])
    col_count = len(first_row_cells)
    
    if col_count == 8:
        print(f"\nN3テーブル（テーブル{i+1}）を発見:")
        print(f"  列数: {col_count}")
        print(f"  行数: {len(rows)}")
        
        # 最初の5行のデータを表示
        for row_idx, row in enumerate(rows[:6]):
            cells = row.find_all(['td', 'th'])
            row_text = row.get_text().strip()
            
            # 回号を含む行のみ表示
            if '第' in row_text and '回' in row_text:
                round_match = re.search(r'第(\d+)回', row_text)
                if round_match:
                    round_num = round_match.group(1)
                    print(f"\n  第{round_num}回:")
                    print(f"    セル数: {len(cells)}")
                    for cell_idx, cell in enumerate(cells[:8]):
                        cell_text = cell.get_text().strip()
                        print(f"    セル{cell_idx}: '{cell_text}'")
                    break

