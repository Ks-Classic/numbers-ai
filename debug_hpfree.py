#!/usr/bin/env python3
"""
hpfree.comのページ構造をデバッグするスクリプト
"""

import requests
from bs4 import BeautifulSoup

URL = "https://www.hpfree.com/numbers/rehearsal.html"

def main():
    print(f"Fetching {URL}...")
    response = requests.get(URL, headers={
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    })
    
    if response.status_code != 200:
        print(f"Error: Status code {response.status_code}")
        return
    
    print(f"✓ Page fetched successfully (length: {len(response.text)} bytes)")
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # テーブルを探す
    tables = soup.find_all('table')
    print(f"\n📊 Found {len(tables)} table(s)")
    
    for idx, table in enumerate(tables):
        print(f"\n{'='*60}")
        print(f"Table {idx + 1}:")
        print(f"{'='*60}")
        
        rows = table.find_all('tr')
        print(f"  Rows: {len(rows)}")
        
        # 最初の5行を表示
        for row_idx, row in enumerate(rows[:10]):
            cells = row.find_all(['td', 'th'])
            print(f"\n  Row {row_idx + 1} ({len(cells)} cells):")
            
            cell_texts = []
            for cell_idx, cell in enumerate(cells):
                text = cell.get_text(strip=True)
                cell_texts.append(text)
                if cell_idx < 12:  # 最初の12セルのみ表示
                    print(f"    Cell {cell_idx}: '{text}'")
            
            # 回号を探す
            row_text = ' '.join(cell_texts)
            if '第' in row_text and '回' in row_text:
                print(f"  ⭐ Round found in row: {row_text[:100]}")
    
    # inputタグを探す（番号入力フィールド）
    print(f"\n{'='*60}")
    print("Searching for input fields...")
    print(f"{'='*60}")
    
    inputs = soup.find_all('input')
    print(f"\n📝 Found {len(inputs)} input field(s)")
    
    for idx, inp in enumerate(inputs[:20]):  # 最初の20個
        input_type = inp.get('type', 'text')
        input_name = inp.get('name', '')
        input_value = inp.get('value', '')
        input_id = inp.get('id', '')
        
        print(f"\nInput {idx + 1}:")
        print(f"  Type: {input_type}")
        print(f"  Name: {input_name}")
        print(f"  ID: {input_id}")
        print(f"  Value: {input_value}")
        
        # 周辺のテキストも確認
        parent = inp.parent
        if parent:
            parent_text = parent.get_text(strip=True)[:100]
            print(f"  Parent text: {parent_text}")

if __name__ == '__main__':
    main()
