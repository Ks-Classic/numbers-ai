#!/usr/bin/env python3
"""データ結合をテストするスクリプト"""
import sys
sys.path.insert(0, 'scripts')
from fetch_past_results import fetch_page, parse_n4_table, parse_n3_table, combine_data
from bs4 import BeautifulSoup
from pathlib import Path

url = 'https://www.hpfree.com/numbers/rehearsal2021-1.html'
print(f"ページを取得中: {url}...")

html_content = fetch_page(url)
soup = BeautifulSoup(html_content, 'html.parser')

# N4とN3のデータを取得
n4_data = parse_n4_table(soup, url=url)
n3_data = parse_n3_table(soup, url=url)

print(f"\n取得したデータ:")
print(f"  N4データ: {len(n4_data)}件")
print(f"  N3データ: {len(n3_data)}件")

# データを結合
output_file = Path('data/past_results.csv')
data = combine_data(n4_data, n3_data, 5726, max_rounds=128, merge_mode=True, output_file=output_file)

print(f"\n結合したデータ: {len(data)}件")
print(f"\n最初の5件:")
for row in data[:5]:
    print(f"  第{row['round_number']}回: N3当選={row['n3_winning']}, N3リハーサル={row['n3_rehearsal']}, N4当選={row['n4_winning']}, N4リハーサル={row['n4_rehearsal']}")

