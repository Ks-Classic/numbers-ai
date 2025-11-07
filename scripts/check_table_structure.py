#!/usr/bin/env python3
"""テーブル構造を確認するスクリプト"""
import requests
from bs4 import BeautifulSoup

url = 'https://www.hpfree.com/numbers/rehearsal2021-1.html'
print(f"ページを取得中: {url}...")

r = requests.get(url)
r.encoding = 'shift-jis'
soup = BeautifulSoup(r.text, 'html.parser')

tables = soup.find_all('table')
print(f"\nテーブル数: {len(tables)}\n")

for i, table in enumerate(tables[:10]):
    rows = table.find_all('tr')
    if not rows:
        continue
    
    # 最初の行の列数を確認
    first_row_cells = rows[0].find_all(['td', 'th'])
    col_count = len(first_row_cells)
    
    # データ行を確認（回号を含む行）
    data_rows = []
    for row in rows:
        row_text = row.get_text()
        if '第5726回' in row_text or '第5599回' in row_text:
            cells = row.find_all(['td', 'th'])
            data_rows.append((row_text[:50], len(cells)))
    
    print(f"テーブル{i+1}:")
    print(f"  列数: {col_count}")
    print(f"  行数: {len(rows)}")
    if data_rows:
        print(f"  データ行の例:")
        for row_text, cell_count in data_rows[:2]:
            print(f"    - {row_text[:50]}... (列数: {cell_count})")
    print()

