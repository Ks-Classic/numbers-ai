#!/usr/bin/env python3
"""
ナンバーズ過去当選番号・リハーサル番号取得スクリプト

Webページから直接データを取得して、past_results.csvを作成します。

データソース: https://www.hpfree.com/numbers/rehearsal.html
最新回号を自動取得し、そこから過去分を取得します。
過去分のページは自動で探索します。

使い方:
    python3 fetch_past_results.py [output_file] [--limit N] [--use-fallback]

オプション:
    output_file      出力ファイルパス（デフォルト: data/past_results.csv）
    --limit N        取得する最大件数（デフォルト: 300、手動実行時は1000など大量取得可能）
    --use-fallback   Webスクレイピング失敗時に検索APIを使用

出力:
    data/past_results.csv (デフォルト)
"""

import sys
import csv
import re
import time
import os
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urljoin

try:
    import requests
    from bs4 import BeautifulSoup
    HAS_DEPS = True
except ImportError:
    HAS_DEPS = False
    print("エラー: 必要なパッケージがインストールされていません。")
    print("以下のコマンドを実行してください:")
    print("  pip install requests beautifulsoup4")
    sys.exit(1)

# 環境変数からAPIキーを読み込み
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenvがなくても動作するようにする

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
SERP_API_KEY = os.getenv('SERP_API_KEY')

# 最新版ページのURL
LATEST_PAGE_URL = 'https://www.hpfree.com/numbers/rehearsal.html'
BASE_PAGE_URL = 'https://www.hpfree.com/numbers/'

# みずほ銀行のページURL（4800回以前用）
MIZUHO_BASE_URL = 'https://www.mizuhobank.co.jp/takarakuji/check/numbers/backnumber/'
MIZUHO_INDEX_URL = 'https://www.mizuhobank.co.jp/takarakuji/check/numbers/backnumber/index.html'

# リハーサル番号が取得可能になる回号
REHEARSAL_AVAILABLE_FROM = 4801


def extract_number_from_cell(cell_text: str) -> Optional[str]:
    """
    セルから数値を抽出（特殊表記に対応）
    
    対応する特殊表記:
    - 取り消し線: 8̶
    - 変更記号: 7→5, 8̶→0
    - 括弧付き注釈: (不), (落), (早)
    - 複合: 8̶→0(不)(不), 7→5(不)(落)
    
    Args:
        cell_text: セルのテキスト内容
        
    Returns:
        抽出された数値（1桁の文字列）、またはNone
    """
    if not cell_text:
        return None
    
    # テキストを正規化（空白を除去）
    text = cell_text.strip()
    
    # 取り消し線を含む変更パターン: 8̶→0 または 8→0
    # 矢印の後の数字を取得（最終的な値）
    # 矢印記号: → (U+2192) または → (全角)
    arrow_match = re.search(r'[→→→](\d+)', text)
    if arrow_match:
        # 矢印の後の数字を返す（最終的な値）
        return arrow_match.group(1)
    
    # 取り消し線だけの場合（例: 8̶）、単純な数字を探す
    # 取り消し線記号（U+0336）を除去
    text = re.sub(r'[\u0336\u0335\u0332]', '', text)  # 各種取り消し線記号
    
    # 括弧付きの注釈を除去: (不), (落), (早) など
    text = re.sub(r'\([^)]*\)', '', text)
    
    # 数字のみを抽出
    digits = re.findall(r'\d', text)
    if digits:
        # 最初の数字を返す（通常は1桁のはず）
        return digits[0]
    
    return None


def get_latest_round_number() -> Optional[int]:
    """
    最新版ページから最新の回号を取得する
    
    Returns:
        最新の回号、またはNone
    """
    print(f"📥 最新版ページを取得中: {LATEST_PAGE_URL}...")
    html_content = fetch_page(LATEST_PAGE_URL)
    
    if not html_content:
        print("⚠ 最新版ページの取得に失敗しました")
        return None
    
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # 最新の回号を探す（表の最初の行から）
    tables = soup.find_all('table')
    
    for table in tables:
        rows = table.find_all('tr')
        for row in rows:
            row_text = row.get_text()
            # 回号のパターンを探す（第XXXX回）
            round_matches = re.findall(r'第(\d+)回', row_text)
            if round_matches:
                # 最新の回号（最大値）を返す
                round_numbers = [int(r) for r in round_matches]
                if round_numbers:
                    latest_round = max(round_numbers)
                    print(f"✓ 最新回号を取得しました: 第{latest_round}回")
                    return latest_round
    
    print("⚠ 最新回号が見つかりませんでした")
    return None


def find_past_pages(base_url: str) -> List[str]:
    """
    過去分のページを自動探索する
    
    Args:
        base_url: ベースURL
        
    Returns:
        見つかったページURLのリスト
    """
    print(f"\n🔍 過去分のページを探索中...")
    found_pages = []
    
    # まず最新版ページからリンクを取得
    html_content = fetch_page(LATEST_PAGE_URL)
    if not html_content:
        print("⚠ 最新版ページの取得に失敗しました")
        return found_pages
    
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # 過去分へのリンクを探す（rehearsal20XX-X.html のパターン）
    links = soup.find_all('a', href=True)
    
    for link in links:
        href = link.get('href', '')
        # rehearsal20XX-X.html のパターンを探す
        match = re.search(r'rehearsal(\d{4})-(\d+)\.html', href)
        if match:
            year = int(match.group(1))
            quarter = int(match.group(2))
            
            # 絶対URLに変換
            if href.startswith('/'):
                full_url = f"{BASE_PAGE_URL.rstrip('/')}{href}"
            elif href.startswith('http'):
                full_url = href
            else:
                full_url = urljoin(BASE_PAGE_URL, href)
            
            if full_url not in found_pages:
                found_pages.append(full_url)
                print(f"  ✓ ページを発見: {href} ({year}年{quarter}期)")
    
    # 見つからない場合は、既知のパターンで生成
    if not found_pages:
        print("  ⚠ リンクからページが見つかりませんでした。既知のパターンで生成します...")
        current_year = datetime.now().year
        
        # 過去5年分を生成（半期ごとに4ページ）
        for year in range(current_year - 4, current_year + 1):
            for quarter in range(1, 5):
                page_url = f"{BASE_PAGE_URL}rehearsal{year}-{quarter}.html"
                found_pages.append(page_url)
    
    print(f"✓ {len(found_pages)}件のページを発見しました")
    return found_pages


def is_draw_day(date: datetime = None) -> bool:
    """
    抽選日かどうかを判定（平日かつ年末年始でない）
    
    Args:
        date: 判定する日付（デフォルト: 今日）
        
    Returns:
        抽選日の場合True
    """
    if date is None:
        date = datetime.now()
    
    # 週末を除外（月曜=0, 日曜=6）
    weekday = date.weekday()
    if weekday >= 5:  # 土曜日(5)または日曜日(6)
        return False
    
    # 年末年始を除外（12/29〜1/3）
    month = date.month
    day = date.day
    
    if month == 12 and day >= 29:
        return False
    if month == 1 and day <= 3:
        return False
    
    return True


def calculate_draw_date_from_round_diff(base_date: datetime, round_diff: int) -> datetime:
    """
    基準日と回号差から抽選日を計算（平日のみをカウント）
    
    Args:
        base_date: 基準となる日付（既知の抽選日）
        round_diff: 回号の差（新しい回号 - 基準回号）
    
    Returns:
        計算された抽選日
    """
    if round_diff == 0:
        return base_date
    
    # 回号差が正の場合は未来、負の場合は過去
    current_date = base_date
    count = 0
    direction = 1 if round_diff > 0 else -1
    
    while count < abs(round_diff):
        current_date += timedelta(days=direction)
        if is_draw_day(current_date):
            count += 1
    
    return current_date


def calculate_weekday(draw_date: Optional[str]) -> Optional[int]:
    """
    日付から曜日を計算（0-4の整数）
    
    Args:
        draw_date: 日付文字列（YYYY-MM-DD形式、NULL可）
    
    Returns:
        曜日（0:月, 1:火, 2:水, 3:木, 4:金）、NULLの場合はNone
    """
    if not draw_date or draw_date == 'NULL' or not draw_date.strip():
        return None
    
    try:
        date_obj = datetime.strptime(draw_date, '%Y-%m-%d')
        weekday = date_obj.weekday()
        # ナンバーズは平日のみ抽選のため、0-4の値のみ
        if weekday < 5:
            return weekday
        return None
    except (ValueError, TypeError):
        return None


def fetch_with_gemini_api(query: str) -> Optional[str]:
    """
    Gemini APIを使用して情報を取得する
    
    Args:
        query: 検索クエリ
        
    Returns:
        取得した情報、またはNone
    """
    if not GEMINI_API_KEY:
        return None
    
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={GEMINI_API_KEY}"
        
        payload = {
            "contents": [{
                "parts": [{
                    "text": f"ナンバーズの最新当選番号について検索してください。{query} 最新の回号、N3当選番号、N4当選番号、リハーサル数字を教えてください。JSON形式で返してください。"
                }]
            }]
        }
        
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        if 'candidates' in result and len(result['candidates']) > 0:
            content = result['candidates'][0]['content']['parts'][0]['text']
            return content
        
        return None
    except Exception as e:
        print(f"⚠ Gemini API取得エラー: {e}")
        return None


def fetch_with_serp_api(query: str) -> Optional[str]:
    """
    SerpAPI (Google Search API)を使用して情報を取得する
    
    Args:
        query: 検索クエリ
        
    Returns:
        取得した情報、またはNone
    """
    if not SERP_API_KEY:
        return None
    
    try:
        url = "https://serpapi.com/search"
        params = {
            "q": query,
            "api_key": SERP_API_KEY,
            "engine": "google",
            "hl": "ja",
            "gl": "jp"
        }
        
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        # 検索結果のスニペットを返す
        if 'organic_results' in result and len(result['organic_results']) > 0:
            snippets = [r.get('snippet', '') for r in result['organic_results'][:3]]
            return '\n'.join(snippets)
        
        return None
    except Exception as e:
        print(f"⚠ SerpAPI取得エラー: {e}")
        return None


def parse_fallback_data(api_result: str) -> Optional[Dict[int, Dict[str, str]]]:
    """
    APIから取得したデータをパースして辞書形式に変換
    
    Args:
        api_result: APIから取得したテキスト
        
    Returns:
        回号をキーとした辞書、またはNone
    """
    if not api_result:
        return None
    
    results = {}
    
    # JSON形式を試す
    try:
        # JSON形式の部分を抽出
        json_match = re.search(r'\{[^{}]*"round_number"[^{}]*\}', api_result)
        if json_match:
            data = json.loads(json_match.group())
            round_number = data.get('round_number')
            if round_number:
                results[round_number] = {
                    'n3_winning': data.get('n3_winning', ''),
                    'n4_winning': data.get('n4_winning', ''),
                    'n3_rehearsal': data.get('n3_rehearsal', ''),
                    'n4_rehearsal': data.get('n4_rehearsal', ''),
                }
                return results
    except:
        pass
    
    # テキスト形式から抽出を試す
    # 回号のパターンを探す
    round_match = re.search(r'第(\d+)回', api_result)
    if round_match:
        round_number = int(round_match.group(1))
        
        # N3当選番号
        n3_match = re.search(r'N3[：:]\s*(\d{3})', api_result)
        n3_winning = n3_match.group(1) if n3_match else ''
        
        # N4当選番号
        n4_match = re.search(r'N4[：:]\s*(\d{4})', api_result)
        n4_winning = n4_match.group(1) if n4_match else ''
        
        # リハーサル数字
        n3_rehearsal_match = re.search(r'リハーサル[：:]\s*(\d{3})', api_result)
        n3_rehearsal = n3_rehearsal_match.group(1) if n3_rehearsal_match else ''
        
        n4_rehearsal_match = re.search(r'N4.*リハーサル[：:]\s*(\d{4})', api_result)
        n4_rehearsal = n4_rehearsal_match.group(1) if n4_rehearsal_match else ''
        
        results[round_number] = {
            'n3_winning': n3_winning,
            'n4_winning': n4_winning,
            'n3_rehearsal': n3_rehearsal,
            'n4_rehearsal': n4_rehearsal,
        }
        
        return results
    
    return None


def fetch_with_fallback(base_url: str, max_rounds: int) -> Tuple[Dict[int, Dict[str, str]], Dict[int, Dict[str, str]]]:
    """
    Webスクレイピングに失敗した場合、検索APIでフォールバック
    
    Args:
        base_url: ベースURL
        max_rounds: 取得する最大件数
        
    Returns:
        (n4_data, n3_data) のタプル
    """
    print("\n⚠ Webスクレイピングに失敗しました。検索APIでフォールバックを試行します...")
    
    n4_data = {}
    n3_data = {}
    
    # 最新の回号を検索
    query = "ナンバーズ 最新 当選番号 リハーサル"
    
    # Gemini APIを優先的に試す
    if GEMINI_API_KEY:
        print("📡 Gemini APIで検索中...")
        api_result = fetch_with_gemini_api(query)
        if api_result:
            parsed = parse_fallback_data(api_result)
            if parsed:
                # N4とN3のデータを分ける
                for round_num, data in parsed.items():
                    if data.get('n4_winning'):
                        n4_data[round_num] = {
                            'n4_winning': data.get('n4_winning', ''),
                            'n4_rehearsal': data.get('n4_rehearsal', ''),
                        }
                    if data.get('n3_winning'):
                        n3_data[round_num] = {
                            'n3_winning': data.get('n3_winning', ''),
                            'n3_rehearsal': data.get('n3_rehearsal', ''),
                        }
                if n4_data or n3_data:
                    print(f"✓ Gemini APIでデータを取得しました（{len(n4_data)}件のN4、{len(n3_data)}件のN3）")
                    return n4_data, n3_data
    
    # SerpAPIを試す
    if SERP_API_KEY:
        print("📡 SerpAPIで検索中...")
        api_result = fetch_with_serp_api(query)
        if api_result:
            parsed = parse_fallback_data(api_result)
            if parsed:
                for round_num, data in parsed.items():
                    if data.get('n4_winning'):
                        n4_data[round_num] = {
                            'n4_winning': data.get('n4_winning', ''),
                            'n4_rehearsal': data.get('n4_rehearsal', ''),
                        }
                    if data.get('n3_winning'):
                        n3_data[round_num] = {
                            'n3_winning': data.get('n3_winning', ''),
                            'n3_rehearsal': data.get('n3_rehearsal', ''),
                        }
                if n4_data or n3_data:
                    print(f"✓ SerpAPIでデータを取得しました（{len(n4_data)}件のN4、{len(n3_data)}件のN3）")
                    return n4_data, n3_data
    
    print("✗ 検索APIでもデータを取得できませんでした")
    return n4_data, n3_data


def fetch_page(url: str, max_retries: int = 3) -> Optional[str]:
    """
    WebページのHTMLを取得
    
    Args:
        url: 取得するURL
        max_retries: 最大リトライ回数
        
    Returns:
        HTMLコンテンツ、またはNone（404エラーの場合もNoneを返す）
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    for attempt in range(max_retries):
        try:
            response = requests.get(url, headers=headers, timeout=30)
            
            # 404エラーの場合は特別処理（ページが存在しない）
            if response.status_code == 404:
                print(f"   ⚠ 404エラー: ページが存在しません - {url}")
                return None
            
            response.raise_for_status()
            
            # エンコーディングを自動検出
            if response.encoding is None or response.encoding == 'ISO-8859-1':
                response.encoding = response.apparent_encoding or 'shift-jis'
            
            return response.text
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                print(f"   ⚠ 404エラー: ページが存在しません - {url}")
                return None
            print(f"⚠ 取得エラー (試行 {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # 指数バックオフ
            else:
                return None
        except Exception as e:
            print(f"⚠ 取得エラー (試行 {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # 指数バックオフ
            else:
                return None
    
    return None


def parse_mizuhobank_csv(csv_content: str, round_number: int, max_round: Optional[int] = None) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    みずほ銀行のCSVファイルからN3とN4の当選番号を抽出（リハーサル番号はなし）
    
    lottery.jsの824-825行目を参考:
    - N3: results[i - from][3][1] (4行目の2列目)
    - N4: results[i - from][10][1] (11行目の2列目)
    
    Args:
        csv_content: CSVファイルの内容（Shift_JISエンコーディング）
        round_number: 回号
        max_round: 取得する最大回号（Noneの場合は制限なし）
        
    Returns:
        (n3_winning, n4_winning, draw_date) のタプル。見つからない場合はNone
    """
    # 最大回号のチェック
    if max_round and round_number > max_round:
        return None, None, None
    
    try:
        # Shift_JISからUTF-8に変換
        if isinstance(csv_content, bytes):
            csv_text = csv_content.decode('shift_jis', errors='ignore')
        else:
            csv_text = csv_content
        
        # 全角数字を半角に変換（lottery.jsの処理を再現）
        csv_text = re.sub(r'[０-９]', lambda m: str(ord(m.group(0)) - 0xFEE0), csv_text)
        
        # 行に分割
        lines = csv_text.split('\n')
        # 空行を除去
        lines = [line.strip() for line in lines if line.strip()]
        
        if round_number <= 2705:
            print(f"   デバッグ: 第{round_number}回のCSV行数: {len(lines)}")
            print(f"   デバッグ: 最初の5行: {lines[:5]}")
        
        # プレフィックス行（A50など）をスキップ
        # 注意: スキップ後も、元のCSVファイルの行番号で考える必要がある
        # A50をスキップした後:
        # - 元の2行目（ヘッダー）→ lines[0]
        # - 元の4行目（N3）→ lines[2]（0-indexedで3行目）
        # - 元の11行目（N4）→ lines[9]（0-indexedで10行目）
        skip_prefix = False
        if lines and lines[0].startswith('A5'):
            skip_prefix = True
            lines = lines[1:]
            if round_number <= 2705:
                print(f"   デバッグ: プレフィックス行をスキップしました")
        
        if len(lines) < 11:
            print(f"   デバッグ: 第{round_number}回のCSV行数が不足しています（{len(lines)}行、必要: 11行以上）")
            if round_number <= 2705:
                print(f"   デバッグ: 全行内容: {lines}")
            return None, None, None
        
        # ヘッダー行から回号と日付を抽出
        # 形式: 第2701回ナンバーズ,数字選択式全国自治宝くじ,平成21年10月8日,...
        header_line = lines[0] if len(lines) > 0 else ''
        if round_number <= 2705:
            print(f"   デバッグ: 第{round_number}回のヘッダー行: {header_line[:100]}")
        
        date_match = re.search(r'(平成|令和|昭和)(\d+|元)年(\d{1,2})月(\d{1,2})日', header_line)
        draw_date = ''
        if date_match:
            era = date_match.group(1)
            year_str = date_match.group(2)
            month = date_match.group(3).zfill(2)
            day = date_match.group(4).zfill(2)
            
            # 元号を西暦に変換
            if era == '平成':
                year = 1988 + (1 if year_str == '元' else int(year_str))
            elif era == '令和':
                year = 2018 + (1 if year_str == '元' else int(year_str))
            elif era == '昭和':
                year = 1925 + (1 if year_str == '元' else int(year_str))
            else:
                year = None
            
            if year:
                draw_date = f"{year}-{month}-{day}"
                if round_number <= 2705:
                    print(f"   デバッグ: 第{round_number}回の日付: {draw_date}")
        else:
            if round_number <= 2705:
                print(f"   デバッグ: 第{round_number}回の日付が見つかりません")
        
        # N3の当選番号を抽出
        # 元のCSVファイルの4行目 = プレフィックススキップ後は lines[2]（0-indexedで3行目）
        # 形式: ナンバーズ３抽せん数字,493
        n3_winning = None
        n3_line_idx = 2 if skip_prefix else 3  # プレフィックスをスキップした場合は2、そうでなければ3
        if len(lines) > n3_line_idx:
            n3_line = lines[n3_line_idx]
            if round_number <= 2705:
                print(f"   デバッグ: 第{round_number}回のN3行（インデックス{n3_line_idx}）: {n3_line}")
            n3_parts = n3_line.split(',')
            # CSVファイルでは「ナンバーズ51」がN3、「ナンバーズ52」がN4を表す
            if len(n3_parts) >= 2 and ('ナンバーズ51' in n3_parts[0] or 'ナンバーズ３' in n3_parts[0]):
                n3_winning = n3_parts[1].strip()
                # 3桁の数字のみを抽出（先頭の0も含む）
                n3_match = re.search(r'(\d{3})', n3_winning)
                if n3_match:
                    n3_winning = n3_match.group(1)
                    if round_number <= 2705:
                        print(f"   デバッグ: 第{round_number}回のN3抽出成功: {n3_winning}")
                else:
                    n3_winning = None
                    if round_number <= 2705:
                        print(f"   デバッグ: 第{round_number}回のN3から数字が見つかりません: {n3_winning}")
            else:
                if round_number <= 2705:
                    print(f"   デバッグ: 第{round_number}回のN3行の形式が不正: {n3_line}")
                    print(f"   デバッグ: N3行の分割結果: {n3_parts}")
        
        # N4の当選番号を抽出
        # 元のCSVファイルの11行目 = プレフィックススキップ後は lines[9]（0-indexedで10行目）
        # 形式: ナンバーズ４抽せん数字,1640
        n4_winning = None
        n4_line_idx = 9 if skip_prefix else 10  # プレフィックスをスキップした場合は9、そうでなければ10
        if len(lines) > n4_line_idx:
            n4_line = lines[n4_line_idx]
            if round_number <= 2705:
                print(f"   デバッグ: 第{round_number}回のN4行（インデックス{n4_line_idx}）: {n4_line}")
            n4_parts = n4_line.split(',')
            # CSVファイルでは「ナンバーズ51」がN3、「ナンバーズ52」がN4を表す
            if len(n4_parts) >= 2 and ('ナンバーズ52' in n4_parts[0] or 'ナンバーズ４' in n4_parts[0]):
                n4_winning = n4_parts[1].strip()
                # 4桁の数字のみを抽出（先頭の0も含む）
                n4_match = re.search(r'(\d{4})', n4_winning)
                if n4_match:
                    n4_winning = n4_match.group(1)
                    if round_number <= 2705:
                        print(f"   デバッグ: 第{round_number}回のN4抽出成功: {n4_winning}")
                else:
                    n4_winning = None
                    if round_number <= 2705:
                        print(f"   デバッグ: 第{round_number}回のN4から数字が見つかりません: {n4_winning}")
            else:
                if round_number <= 2705:
                    print(f"   デバッグ: 第{round_number}回のN4行の形式が不正: {n4_line}")
                    print(f"   デバッグ: N4行の分割結果: {n4_parts}")
        
        if round_number <= 2705:
            print(f"   デバッグ: 第{round_number}回の最終結果: N3={n3_winning}, N4={n4_winning}, Date={draw_date}")
        
        return n3_winning, n4_winning, draw_date
        
    except Exception as e:
        print(f"   デバッグ: 第{round_number}回のCSV解析エラー: {e}")
        import traceback
        traceback.print_exc()
        return None, None, None


def fetch_mizuhobank_csv(round_number: int, session: Optional[requests.Session] = None) -> Optional[str]:
    """
    みずほ銀行のCSVファイルを取得
    
    lottery.jsの920行目を参考:
    url: path + 'A10' + typeData[type].prefix + ('0000' + index).slice(-4) + '.CSV'
    ナンバーズの場合: /retail/takarakuji/numbers/csv/A1002701.CSV
    
    Args:
        round_number: 回号
        session: requests.Sessionオブジェクト（再利用用、Noneの場合は新規作成）
        
    Returns:
        CSVファイルの内容（Shift_JISエンコーディング）、またはNone
    """
    csv_url = f'https://www.mizuhobank.co.jp/retail/takarakuji/numbers/csv/A100{round_number:04d}.CSV'
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    # セッションが提供されていない場合は新規作成
    if session is None:
        session = requests.Session()
        session.headers.update(headers)
    
    try:
        if round_number <= 2705:
            print(f"   デバッグ: CSVファイルを取得中: {csv_url}")
        response = session.get(csv_url, timeout=30)
        
        if response.status_code == 404:
            if round_number <= 2705:
                print(f"   デバッグ: 404エラー - CSVファイルが見つかりません: {csv_url}")
            return None
        
        # 403エラー（アクセス拒否）の場合もスキップ
        if response.status_code == 403:
            if round_number <= 2705:
                print(f"   デバッグ: 403エラー - アクセスが拒否されました: {csv_url}")
            return None
        
        response.raise_for_status()
        
        # Shift_JISエンコーディングで取得
        response.encoding = 'shift_jis'
        
        if round_number <= 2705:
            print(f"   デバッグ: CSVファイルを取得しました（{len(response.text)}文字）")
        return response.text
        
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 403:
            if round_number <= 2705:
                print(f"   デバッグ: 403エラー - アクセスが拒否されました: {csv_url}")
            return None
        raise
    except Exception as e:
        if round_number <= 2705:
            print(f"   デバッグ: CSVファイル取得エラー: {e}")
        return None


def parse_mizuhobank_table(soup: BeautifulSoup, max_round: Optional[int] = None) -> Tuple[Dict[int, Dict[str, str]], Dict[int, Dict[str, str]]]:
    """
    みずほ銀行のHTMLページからN3とN4の当選番号と日付を抽出（リハーサル番号はなし）
    
    Args:
        soup: BeautifulSoupオブジェクト
        max_round: 取得する最大回号（Noneの場合は制限なし）
        
    Returns:
        (n4_data, n3_data) のタプル
    """
    n4_data = {}
    n3_data = {}
    
    # テーブルを探す
    tables = soup.find_all('table')
    
    for table in tables:
        rows = table.find_all('tr')
        
        for row in rows:
            cells = row.find_all(['td', 'th'])
            if len(cells) < 5:  # 最低限の列数が必要
                continue
            
            # 回号を探す（最初のセルまたは2番目のセル）
            round_number = None
            for i in range(min(2, len(cells))):
                cell_text = cells[i].get_text().strip()
                # 回号のパターンを探す（例: "第1234回" または "1234"）
                round_match = re.search(r'第?(\d+)回?', cell_text)
                if round_match:
                    round_number = int(round_match.group(1))
                    break
            
            if not round_number:
                continue
            
            # 最大回号のチェック
            if max_round and round_number > max_round:
                continue
            
            # 日付を探す（通常は回号の次のセル）
            draw_date = None
            date_cell_idx = 1 if round_number else 0
            if date_cell_idx < len(cells):
                date_text = cells[date_cell_idx].get_text().strip()
                # 日付のパターンを探す（例: "2025/01/10" または "2025-01-10"）
                date_match = re.search(r'(\d{4})[/\-年](\d{1,2})[/\-月](\d{1,2})', date_text)
                if date_match:
                    year = date_match.group(1)
                    month = date_match.group(2).zfill(2)
                    day = date_match.group(3).zfill(2)
                    draw_date = f"{year}-{month}-{day}"
            
            # N4当選番号を探す（4桁の数字）
            n4_winning = None
            for cell in cells:
                cell_text = cell.get_text().strip()
                # 4桁の数字を探す
                n4_match = re.search(r'(\d{4})', cell_text)
                if n4_match:
                    n4_winning = n4_match.group(1)
                    break
            
            # N3当選番号を探す（3桁の数字、N4の後に）
            n3_winning = None
            n4_found = False
            for cell in cells:
                cell_text = cell.get_text().strip()
                if n4_winning and n4_winning in cell_text:
                    n4_found = True
                    continue
                if n4_found:
                    # 3桁の数字を探す
                    n3_match = re.search(r'(\d{3})', cell_text)
                    if n3_match:
                        n3_winning = n3_match.group(1)
                        break
            
            # データを保存
            if n4_winning:
                n4_data[round_number] = {
                    'n4_winning': n4_winning,
                    'n4_rehearsal': '',  # 4800回以前はリハーサル番号なし
                    'draw_date': draw_date or '',
                }
            
            if n3_winning:
                n3_data[round_number] = {
                    'n3_winning': n3_winning,
                    'n3_rehearsal': '',  # 4800回以前はリハーサル番号なし
                    'draw_date': draw_date or '',
                }
    
    return n4_data, n3_data


def find_mizuhobank_pages(target_min_round: Optional[int] = None, target_max_round: Optional[int] = None) -> List[str]:
    """
    みずほ銀行のページ一覧からリンクを取得
    
    Args:
        target_min_round: 取得対象の最小回号（指定された場合、必要な範囲のURLのみ生成）
        target_max_round: 取得対象の最大回号（指定された場合、必要な範囲のURLのみ生成）
    
    Returns:
        見つかったページURLのリスト
    """
    print(f"\n🔍 みずほ銀行のページ一覧を取得中: {MIZUHO_INDEX_URL}...")
    html_content = fetch_page(MIZUHO_INDEX_URL)
    
    if not html_content:
        print("⚠ みずほ銀行のページ一覧の取得に失敗しました")
        return []
    
    soup = BeautifulSoup(html_content, 'html.parser')
    found_pages = []
    
    # 範囲が指定されている場合、必要な範囲のURLのみを生成
    if target_min_round is not None and target_max_round is not None:
        # URL形式が2種類ある：
        # 1. num0001.html形式: 第1回～第2700回（20回ごと）
        # 2. detail.html?fromto=XXXX_YYYY&type=numbers形式: 第2701回～第4800回（20回ごと）
        
        # 第1回～第2700回の範囲が必要な場合
        if target_min_round <= 2700:
            min_range = max(1, target_min_round)
            max_range = min(2700, target_max_round)
            # 20回ごとの開始回号を計算
            start_round = ((min_range - 1) // 20) * 20 + 1
            end_round = ((max_range - 1) // 20) * 20 + 1
            
            for start in range(start_round, end_round + 1, 20):
                if start > max_range:
                    break
                page_num = f"{start:04d}"
                url = urljoin(MIZUHO_BASE_URL, f'num{page_num}.html')
                found_pages.append(url)
        
        # 第2701回～第4800回の範囲が必要な場合
        if target_max_round >= 2701:
            min_range = max(2701, target_min_round)
            max_range = min(4800, target_max_round)
            
            # 2701回から始まる20回ごとの範囲を生成
            # 2701, 2721, 2741, ... のように20回ごとに開始
            start_round = ((min_range - 1) // 20) * 20 + 1
            # 2701未満の場合は2701に調整（念のため）
            if start_round < 2701:
                start_round = 2701
            
            # 終了回号を計算（20回ごとの最後の回号）
            end_round = ((max_range - 1) // 20) * 20 + 1
            
            # 20回ごとにURLを生成
            for start in range(start_round, end_round + 1, 20):
                if start > max_range:
                    break
                end = min(start + 19, max_range)
                url = urljoin(MIZUHO_BASE_URL, f'detail.html?fromto={start}_{end}&type=numbers')
                found_pages.append(url)
        
        print(f"   範囲指定: 第{target_min_round}回 ～ 第{target_max_round}回")
        print(f"   ✓ {len(found_pages)}件のURLを生成しました")
        if found_pages:
            print(f"   最初の3件: {found_pages[:3]}")
            if len(found_pages) > 3:
                print(f"   最後の3件: {found_pages[-3:]}")
        
        return found_pages
    
    # 範囲が指定されていない場合、既存のロジックで全範囲のURLを生成
    # （B表）A表以前の当せん番号の範囲のリンクを探す
    # リンクを探す（numXXXX.html または detail.html?fromto=... のパターン）
    links = soup.find_all('a', href=True)
    
    print(f"   デバッグ: 見つかったリンク数: {len(links)}")
    
    # デバッグ: リンクの一部を表示（backnumber関連のもの）
    debug_count = 0
    backnumber_related = []
    for link in links:
        href = link.get('href', '')
        text = link.get_text().strip()
        
        # backnumber関連のリンクを探す
        if 'backnumber' in href.lower() or 'num' in href.lower() or 'detail' in href.lower():
            backnumber_related.append((href, text))
            debug_count += 1
            if debug_count <= 10:
                print(f"   デバッグ: バックナンバー関連リンク [{debug_count}]: {href[:100]} (テキスト: {text[:30]})")
    
    print(f"   デバッグ: バックナンバー関連リンク数: {len(backnumber_related)}")
    
    # 実際のリンクが見つからない場合は、直接URLを生成する
    # num0001.html, num0021.html, ... のパターンで生成
    # または detail.html?fromto=XXXX_YYYY&type=numbers のパターンで生成
    
    # まず、直接リンクを探す
    for link in links:
        href = link.get('href', '')
        # num0001.html のようなパターン
        if re.search(r'num\d+\.html', href):
            if href.startswith('/'):
                full_url = f"https://www.mizuhobank.co.jp{href}"
            elif href.startswith('http'):
                full_url = href
            else:
                full_url = urljoin(MIZUHO_BASE_URL, href)
            
            if full_url not in found_pages:
                found_pages.append(full_url)
        
        # detail.html?fromto=... のパターン
        elif 'detail.html' in href and 'fromto=' in href:
            if href.startswith('/'):
                full_url = f"https://www.mizuhobank.co.jp{href}"
            elif href.startswith('http'):
                full_url = href
            else:
                full_url = urljoin(MIZUHO_BASE_URL, href)
            
            if full_url not in found_pages:
                found_pages.append(full_url)
    
    # もしリンクが見つからない場合は、テーブル内のリンクも探す
    if not found_pages:
        print("   デバッグ: テーブル内のリンクを検索中...")
        tables = soup.find_all('table')
        print(f"   デバッグ: 見つかったテーブル数: {len(tables)}")
        
        for table in tables:
            table_links = table.find_all('a', href=True)
            print(f"   デバッグ: テーブル内のリンク数: {len(table_links)}")
            for link in table_links[:10]:  # 最初の10件を表示
                href = link.get('href', '')
                text = link.get_text().strip()
                print(f"   デバッグ: テーブル内リンク: {href[:100]} (テキスト: {text[:30]})")
                
                # numXXXX.html または detail.html を含むリンクを探す
                if re.search(r'num\d+\.html', href) or ('detail.html' in href and 'fromto=' in href):
                    if href.startswith('/'):
                        full_url = f"https://www.mizuhobank.co.jp{href}"
                    elif href.startswith('http'):
                        full_url = href
                    else:
                        full_url = urljoin(MIZUHO_BASE_URL, href)
                    
                    if full_url not in found_pages:
                        found_pages.append(full_url)
                        print(f"   デバッグ: テーブル内で発見: {href[:100]}")
    
    # それでもリンクが見つからない場合は、直接URLを生成
    if not found_pages:
        print("   デバッグ: リンクが見つからないため、直接URLを生成します")
        
        # URL形式が2種類ある：
        # 1. num0001.html形式: 第1回～第2700回（20回ごと）
        # 2. detail.html?fromto=XXXX_YYYY&type=numbers形式: 第2701回～第4800回（20回ごと）
        
        # 第1回～第2700回: num0001.html形式
        for start_round in range(1, 2701, 20):
            page_num = f"{start_round:04d}"
            url = urljoin(MIZUHO_BASE_URL, f'num{page_num}.html')
            found_pages.append(url)
        
        print(f"   デバッグ: numXXXX.html形式を{len(found_pages)}件生成しました")
        
        # 第2701回～第4800回: detail.html?fromto=XXXX_YYYY&type=numbers形式
        detail_url_count = 0
        for start_round in range(2701, 4801, 20):
            end_round = min(start_round + 19, 4800)
            url = urljoin(MIZUHO_BASE_URL, f'detail.html?fromto={start_round}_{end_round}&type=numbers')
            found_pages.append(url)
            detail_url_count += 1
        
        print(f"   デバッグ: detail.html形式を{detail_url_count}件生成しました（合計{len(found_pages)}件）")
        
        # 最初の数件をテスト
        if found_pages:
            test_url = found_pages[0]
            print(f"   デバッグ: テストURL: {test_url}")
            test_content = fetch_page(test_url)
            if test_content:
                print(f"   ✓ テストURLにアクセス成功 ({len(test_content)}文字)")
            else:
                print(f"   ✗ テストURLにアクセス失敗")
        
        # 2701回以降のURLもテスト
        if len(found_pages) > 135:  # num0001.html形式が135件ある場合
            test_url2 = found_pages[135]  # 最初のdetail.html形式
            print(f"   デバッグ: テストURL2 (detail.html形式): {test_url2}")
            test_content2 = fetch_page(test_url2)
            if test_content2:
                print(f"   ✓ テストURL2にアクセス成功 ({len(test_content2)}文字)")
            else:
                print(f"   ✗ テストURL2にアクセス失敗")
    
    print(f"✓ {len(found_pages)}件のページを発見しました")
    if found_pages:
        print(f"   最初の5件: {found_pages[:5]}")
    
    return found_pages


def parse_n4_table(soup: BeautifulSoup, latest_only: bool = False, url: Optional[str] = None) -> Dict[int, Dict[str, str]]:
    """
    N4の表データを抽出（4桁）
    
    N4テーブルの構造:
    - 回号 | 千位(リ) | 百位(リ) | 十位(リ) | 一位(リ) | リ/本 | 千位(本) | 百位(本) | 十位(本) | 一位(本)
    - 左側（セル1-4）: N4リハーサル（4桁）
    - 右側（セル6-9）: N4当選番号（4桁）
    
    Args:
        soup: BeautifulSoupオブジェクト
        latest_only: Trueの場合、最新の1行のみを取得
        url: ページのURL（テーブル構造の判定に使用）
        
    Returns:
        回号をキーとした辞書
    """
    results = {}
    
    # 表を探す（4桁の数字を含むテーブル = N4テーブル）
    tables = soup.find_all('table')
    
    for table in tables:
        rows = table.find_all('tr')
        
        for row in rows:
            cells = row.find_all(['td', 'th'])
            
            # 回号を含むセルを探す
            row_text = row.get_text()
            round_match = re.search(r'第(\d+)回', row_text)
            if not round_match:
                continue
            
            round_number = int(round_match.group(1))
            
            try:
                # N4テーブルは4桁の数字を含む（10列以上）
                # 構造: 回号 | 千位(リ) | 百位(リ) | 十位(リ) | 一位(リ) | リ/本 | 千位(本) | 百位(本) | 十位(本) | 一位(本)
                if len(cells) < 10:
                    continue
                
                # 4桁の数字が含まれているか確認（セル1-4とセル6-9の両方に数字がある）
                has_4_digits_left = False
                has_4_digits_right = False
                
                # 左側の4桁（リハーサル）- セル1-4
                n4_rehearsal_digits = []
                for i in range(1, 5):
                    if i < len(cells):
                        cell_text = cells[i].get_text().strip()
                        digit = extract_number_from_cell(cell_text)
                        if digit:
                            n4_rehearsal_digits.append(digit)
                
                if len(n4_rehearsal_digits) == 4:
                    has_4_digits_left = True
                
                # 右側の4桁（当選番号）- セル6-9
                n4_winning_digits = []
                for i in range(6, 10):
                    if i < len(cells):
                        cell_text = cells[i].get_text().strip()
                        digit = extract_number_from_cell(cell_text)
                        if digit:
                            n4_winning_digits.append(digit)
                
                if len(n4_winning_digits) == 4:
                    has_4_digits_right = True
                
                # 4桁の数字が両方ある場合のみN4テーブルとして処理
                if not (has_4_digits_left and has_4_digits_right):
                    continue
                
                n4_rehearsal = ''.join(n4_rehearsal_digits)
                n4_winning = ''.join(n4_winning_digits)
                
                results[round_number] = {
                    'n4_winning': n4_winning,
                    'n4_rehearsal': n4_rehearsal,
                }
                
                # 最新のみ取得の場合、最初の有効な行で終了
                if latest_only:
                    return results
                    
            except (ValueError, IndexError) as e:
                continue
    
    return results


def parse_n3_table(soup: BeautifulSoup, latest_only: bool = False, url: Optional[str] = None) -> Dict[int, Dict[str, str]]:
    """
    N3の表データを抽出（3桁）
    
    N3テーブルの構造:
    - 回号 | 百位(リ) | 十位(リ) | 一位(リ) | リ/本 | 百位(本) | 十位(本) | 一位(本)
    - 左側（セル1-3）: N3リハーサル（3桁）
    - 右側（セル5-7）: N3当選番号（3桁）
    
    Args:
        soup: BeautifulSoupオブジェクト
        latest_only: Trueの場合、最新の1行のみを取得
        url: ページのURL（テーブル構造の判定に使用）
        
    Returns:
        回号をキーとした辞書
    """
    results = {}
    
    # 表を探す（3桁の数字を含むテーブル = N3テーブル）
    tables = soup.find_all('table')
    
    for table in tables:
        rows = table.find_all('tr')
        
        for row in rows:
            cells = row.find_all(['td', 'th'])
            
            # 回号を含むセルを探す
            row_text = row.get_text()
            round_match = re.search(r'第(\d+)回', row_text)
            if not round_match:
                continue
            
            round_number = int(round_match.group(1))
            
            try:
                # N3テーブルは3桁の数字を含む（8列以上、ただし10列未満）
                # 構造: 回号 | 百位(リ) | 十位(リ) | 一位(リ) | リ/本 | 百位(本) | 十位(本) | 一位(本)
                # N4テーブルは10列なので、8列以上10列未満のテーブルをN3テーブルとして処理
                if len(cells) < 8 or len(cells) >= 10:
                    continue
                
                # 左側の3桁（リハーサル）- セル1-3
                n3_rehearsal_digits = []
                for i in range(1, 4):
                    if i < len(cells):
                        cell_text = cells[i].get_text().strip()
                        digit = extract_number_from_cell(cell_text)
                        if digit:
                            n3_rehearsal_digits.append(digit)
                
                if len(n3_rehearsal_digits) != 3:
                    continue
                
                # 右側の3桁（当選番号）- セル5-7
                n3_winning_digits = []
                for i in range(5, 8):
                    if i < len(cells):
                        cell_text = cells[i].get_text().strip()
                        digit = extract_number_from_cell(cell_text)
                        if digit:
                            n3_winning_digits.append(digit)
                
                if len(n3_winning_digits) != 3:
                    continue
                
                n3_rehearsal = ''.join(n3_rehearsal_digits)
                n3_winning = ''.join(n3_winning_digits)
                
                results[round_number] = {
                    'n3_winning': n3_winning,
                    'n3_rehearsal': n3_rehearsal,
                }
                
                # 最新のみ取得の場合、最初の有効な行で終了
                if latest_only:
                    return results
                    
            except (ValueError, IndexError) as e:
                continue
    
    return results


def combine_data(n4_data: Dict[int, Dict[str, str]], n3_data: Dict[int, Dict[str, str]], latest_round: int, max_rounds: int = 300, merge_mode: bool = False, output_file: Optional[Path] = None) -> List[Dict[str, str]]:
    """
    N4とN3のデータを結合
    
    Args:
        n4_data: N4のデータ辞書
        n3_data: N3のデータ辞書
        latest_round: 最新の回号
        max_rounds: 取得する最大件数
        merge_mode: マージモードの場合、取得したデータをそのまま使用
        output_file: CSVファイルパス（マージモード時に既存データの最新回号と日付を取得するために使用）
        
    Returns:
        結合したデータのリスト
    """
    results = []
    
    # 取得したデータの回号と一致するものを使用
    available_rounds = set(n4_data.keys()) | set(n3_data.keys())
    
    if not available_rounds:
        return results
    
    # マージモードの場合は、取得したデータの最大回号を使用
    if merge_mode and available_rounds:
        latest_round = max(available_rounds)
    
    # マージモードの場合、既存データの最新回号と日付を取得して日付計算の基準とする
    base_round = None
    base_date = None
    if merge_mode and output_file and output_file.exists():
        existing_data = load_existing_csv(output_file)
        if existing_data:
            # 既存データから最新回号と日付を取得
            existing_dict = {}
            for row in existing_data:
                try:
                    round_num = int(row.get('round_number', 0))
                    if round_num > 0:
                        existing_dict[round_num] = row
                except (ValueError, TypeError):
                    continue
            
            if existing_dict:
                base_round = max(existing_dict.keys())
                base_row = existing_dict[base_round]
                base_date_str = base_row.get('draw_date', '')
                if base_date_str and base_date_str != 'NULL' and base_date_str.strip():
                    try:
                        base_date = datetime.strptime(base_date_str, '%Y-%m-%d')
                        print(f"   既存データの基準: 第{base_round}回 ({base_date_str})")
                    except (ValueError, TypeError):
                        pass
    
    # マージモードの場合は、取得したデータをそのまま使用
    if merge_mode:
        target_rounds = available_rounds
        print(f"   マージモード: 取得したデータをそのまま使用（{len(target_rounds)}件）")
    else:
        # 最新回から指定件数分の回号を生成
        target_rounds = set(range(latest_round - max_rounds + 1, latest_round + 1))
        target_rounds = target_rounds & available_rounds
        
        # デバッグ情報
        min_round = min(available_rounds)
        max_round = max(available_rounds)
        print(f"   取得データ範囲: 第{min_round}回 ～ 第{max_round}回（{len(available_rounds)}件）")
        print(f"   目標範囲: 第{min(target_rounds) if target_rounds else 'N/A'}回 ～ 第{max(target_rounds) if target_rounds else 'N/A'}回（{len(target_rounds)}件）")
    
    print(f"   一致するデータ: {len(target_rounds)}件")
    
    # N4データがない回号を確認
    missing_n4 = [r for r in target_rounds if r not in n4_data.keys()]
    if missing_n4:
        print(f"   N4データがない回号: {sorted(missing_n4)[:10]}...（{len(missing_n4)}件）")
    
    for round_number in sorted(target_rounds, reverse=True):
        # N4データを取得
        n4_info = n4_data.get(round_number, {})
        n4_winning = n4_info.get('n4_winning', '')
        n4_rehearsal = n4_info.get('n4_rehearsal', '')
        
        # N3データを取得
        n3_info = n3_data.get(round_number, {})
        n3_winning = n3_info.get('n3_winning', '')
        n3_rehearsal = n3_info.get('n3_rehearsal', '')
        
        # 日付を取得（みずほ銀行のデータから取得した日付を優先）
        draw_date = ''
        if n4_info.get('draw_date'):
            draw_date = n4_info.get('draw_date')
        elif n3_info.get('draw_date'):
            draw_date = n3_info.get('draw_date')
        
        # 4801回以降で日付が取得できていない場合、みずほ銀行から日付を取得を試行
        if not draw_date and round_number >= REHEARSAL_AVAILABLE_FROM:
            # みずほ銀行のCSVファイルから日付を取得
            csv_content = fetch_mizuhobank_csv(round_number)
            if csv_content:
                _, _, mizuhobank_date = parse_mizuhobank_csv(csv_content, round_number)
                if mizuhobank_date:
                    draw_date = mizuhobank_date
                    # 取得した日付をデータに保存（次回以降の参照用）
                    if round_number in n4_data:
                        n4_data[round_number]['draw_date'] = draw_date
                    if round_number in n3_data:
                        n3_data[round_number]['draw_date'] = draw_date
        
        # N4またはN3のデータがなければスキップ（マージモードの場合はN3データのみでもOK）
        if not n4_winning and not n3_winning:
            continue
        
        # マージモードの場合は、N4データがなくてもN3データがあれば保存
        if merge_mode and not n4_winning and n3_winning:
            # N3データのみの場合、N4データは空文字列で保存
            n4_winning = ''
            n4_rehearsal = ''
        elif not merge_mode and not n4_winning:
            # 通常モードの場合はN4データ必須
            continue
        
        # 日付が取得できていない場合のみ、計算
        if not draw_date:
            if merge_mode and base_round is not None and base_date is not None:
                # マージモード: 既存データの最新回号と日付を基準に計算
                round_diff = round_number - base_round
                calculated_date = calculate_draw_date_from_round_diff(base_date, round_diff)
                draw_date = calculated_date.strftime('%Y-%m-%d')
            else:
                # 通常モード: 最新回から逆算（簡易版、非推奨）
                days_back = latest_round - round_number
                draw_date_obj = datetime.now() - timedelta(days=days_back)
                draw_date = draw_date_obj.strftime('%Y-%m-%d')
        
        # weekdayを計算
        weekday = calculate_weekday(draw_date)
        weekday_str = str(weekday) if weekday is not None else 'NULL'
        
        results.append({
            'round_number': round_number,
            'draw_date': draw_date,
            'weekday': weekday_str,
            'n3_winning': n3_winning if n3_winning else '',
            'n4_winning': n4_winning,
            'n3_rehearsal': n3_rehearsal if n3_rehearsal else '',
            'n4_rehearsal': n4_rehearsal if n4_rehearsal else '',
        })
    
    return results


def find_missing_rounds(output_file: Path) -> List[int]:
    """
    既存CSVファイルから欠番の回号を検出する
    
    Args:
        output_file: CSVファイルパス
        
    Returns:
        欠番の回号のリスト
    """
    if not output_file.exists():
        return []
    
    existing_data = load_existing_csv(output_file)
    if not existing_data:
        return []
    
    # 既存の回号を取得
    existing_rounds = set()
    for row in existing_data:
        try:
            round_num = int(row.get('round_number', 0))
            if round_num > 0:
                existing_rounds.add(round_num)
        except (ValueError, TypeError):
            continue
    
    if not existing_rounds:
        return []
    
    # 最小回号と最大回号を取得
    min_round = min(existing_rounds)
    max_round = max(existing_rounds)
    
    # 欠番を検出
    missing_rounds = []
    for round_num in range(min_round, max_round + 1):
        if round_num not in existing_rounds:
            missing_rounds.append(round_num)
    
    return sorted(missing_rounds)


def get_existing_round_range(output_file: Path) -> Tuple[Optional[int], Optional[int]]:
    """
    既存CSVファイルから最小回号と最大回号を取得する
    
    Args:
        output_file: CSVファイルパス
        
    Returns:
        (最小回号, 最大回号)のタプル。CSVが存在しない場合は(None, None)
    """
    if not output_file.exists():
        return None, None
    
    existing_data = load_existing_csv(output_file)
    if not existing_data:
        return None, None
    
    round_numbers = []
    for row in existing_data:
        try:
            round_num = int(row.get('round_number', 0))
            if round_num > 0:
                round_numbers.append(round_num)
        except (ValueError, TypeError):
            continue
    
    if not round_numbers:
        return None, None
    
    return min(round_numbers), max(round_numbers)


def load_existing_csv(output_file: Path) -> List[Dict[str, str]]:
    """
    既存のCSVファイルを読み込む
    
    Args:
        output_file: CSVファイルパス
        
    Returns:
        読み込んだデータのリスト
    """
    if not output_file.exists():
        return []
    
    data = []
    try:
        with open(output_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # NULL値を空文字列に変換
                cleaned_row = {}
                for key, value in row.items():
                    cleaned_row[key] = '' if value == 'NULL' else value
                data.append(cleaned_row)
    except Exception as e:
        print(f"⚠ 既存CSVファイルの読み込みエラー: {e}")
        return []
    
    return data


def save_to_csv(data: List[Dict[str, str]], output_file: Path, merge: bool = False, update_null: bool = False):
    """
    CSVファイルに保存
    
    Args:
        data: 保存するデータのリスト
        output_file: 出力ファイルパス
        merge: Trueの場合、既存のCSVファイルとマージする
        update_null: Trueの場合、既存データのNULL値を新しいデータで更新する
    """
    # ディレクトリを作成
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    fieldnames = [
        'round_number',
        'draw_date',
        'weekday',
        'n3_winning',
        'n4_winning',
        'n3_rehearsal',
        'n4_rehearsal'
    ]
    
    # マージモードの場合、既存データを読み込む
    if merge and output_file.exists():
        existing_data = load_existing_csv(output_file)
        # 回号をキーとして既存データを辞書化
        existing_dict = {}
        for row in existing_data:
            round_num = int(row['round_number'])
            # weekdayカラムがない場合は空文字列を設定（後で計算される）
            if 'weekday' not in row:
                row['weekday'] = ''
            existing_dict[round_num] = row
        
        # 新しいデータで既存データを更新または追加
        for row in data:
            round_num = int(row['round_number'])
            if round_num in existing_dict:
                # 既存データがある場合
                if update_null:
                    # NULL値更新モード: 既存データのNULL/空のフィールドを新しいデータで更新
                    existing_row = existing_dict[round_num]
                    for key in fieldnames:
                        existing_value = existing_row.get(key, '')
                        new_value = row.get(key, '')
                        # 4801回以降のdraw_dateは常に更新（みずほ銀行から正しい日付を取得）
                        if key == 'draw_date' and round_num >= REHEARSAL_AVAILABLE_FROM:
                            if new_value and new_value != 'NULL':
                                existing_row[key] = new_value
                        # weekdayの場合は、既存値が空またはNULLの場合、新しい値で更新（draw_dateから計算）
                        elif key == 'weekday':
                            # 既存値が空またはNULLの場合、新しい値で更新
                            if not existing_value or existing_value == 'NULL':
                                if new_value and new_value != 'NULL':
                                    existing_row[key] = new_value
                                elif existing_row.get('draw_date'):
                                    # draw_dateからweekdayを計算
                                    calculated_weekday = calculate_weekday(existing_row.get('draw_date'))
                                    if calculated_weekday is not None:
                                        existing_row[key] = str(calculated_weekday)
                                    else:
                                        existing_row[key] = 'NULL'
                        else:
                            # 既存値がNULLまたは空の場合、新しい値で更新
                            if not existing_value or existing_value == 'NULL':
                                if new_value:
                                    existing_row[key] = new_value
                            # 既存値がある場合も、新しい値が空でなければ更新
                            elif new_value:
                                existing_row[key] = new_value
                    existing_dict[round_num] = existing_row
                else:
                    # 通常のマージモード: 新しいデータで完全に置き換え
                    existing_dict[round_num] = row
            else:
                # 新しい回号の場合、追加
                existing_dict[round_num] = row
        
        # 回号順にソート
        data = [existing_dict[round_num] for round_num in sorted(existing_dict.keys(), reverse=True)]
        
        # 既存データにweekdayがない場合、draw_dateから計算して追加
        for row in data:
            if 'weekday' not in row or not row.get('weekday') or row.get('weekday') == 'NULL':
                draw_date = row.get('draw_date', '')
                if draw_date and draw_date != 'NULL':
                    calculated_weekday = calculate_weekday(draw_date)
                    if calculated_weekday is not None:
                        row['weekday'] = str(calculated_weekday)
                    else:
                        row['weekday'] = 'NULL'
                else:
                    row['weekday'] = 'NULL'
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for row in data:
            # NULL値の処理（空文字列をNULLに変換）
            csv_row = {}
            for key in fieldnames:
                value = row.get(key, '')
                csv_row[key] = value if value else 'NULL'
            
            writer.writerow(csv_row)
    
    print(f"✓ CSVファイルを保存しました: {output_file}")
    print(f"  データ件数: {len(data)}件")


def fetch_multiple_pages(
    base_url: str, 
    max_rounds: int, 
    latest_round: Optional[int] = None,
    target_min_round: Optional[int] = None,
    target_max_round: Optional[int] = None,
    output_file: Optional[Path] = None,
    save_interval: int = 100,  # 100回ごとにCSVに中間保存（回号ベース）
    update_null: bool = False  # NULL値を更新するかどうか
) -> tuple[Dict[int, Dict[str, str]], Dict[int, Dict[str, str]]]:
    """
    複数のページからデータを取得
    
    Args:
        base_url: ベースURL
        max_rounds: 取得する最大件数
        latest_round: 最新の回号（Noneの場合は自動取得）
        target_min_round: 取得対象の最小回号（指定された場合のみ）
        target_max_round: 取得対象の最大回号（指定された場合のみ）
        output_file: CSVファイルパス（指定された場合、100回ごとに中間保存）
        save_interval: CSVに保存する間隔（回数、現在は100回ごと）
        
    Returns:
        (n4_data, n3_data) のタプル
    """
    n4_data = {}
    n3_data = {}
    last_save_count = 0
    consecutive_errors = 0  # 連続エラーカウンター
    max_consecutive_errors = 5  # 最大連続エラー数
    
    # 取得範囲を決定
    if target_min_round is not None and target_max_round is not None:
        # 指定された範囲を使用
        target_min = target_min_round
        target_max = target_max_round
        print(f"   取得対象範囲: 第{target_min}回 ～ 第{target_max}回")
    else:
        # 最新回号を取得
        if latest_round is None:
            latest_round = get_latest_round_number()
            if latest_round is None:
                print("⚠ 最新回号が取得できませんでした")
                return n4_data, n3_data
        
        # 最新回から指定件数分を取得
        target_min = latest_round - max_rounds + 1
        target_max = latest_round
    
    # 4800回以前のデータが必要な場合
    if target_max <= REHEARSAL_AVAILABLE_FROM - 1:
        # 1-2700回: HTMLページから取得、2701-4800回: CSVファイルから取得
        needs_html = target_min <= 2700
        needs_csv = target_max >= 2701
        
        # 1-2700回: HTMLページから取得（並列処理）
        if needs_html:
            html_min = max(1, target_min)
            html_max = min(2700, target_max)
            print(f"   みずほ銀行のHTMLページから取得します（第{html_min}回 ～ 第{html_max}回）")
            
            # HTMLページのURLを生成
            mizuhobank_html_pages = find_mizuhobank_pages(html_min, html_max)
            
            if mizuhobank_html_pages:
                print(f"   ✓ {len(mizuhobank_html_pages)}件のHTMLページURLを生成しました")
                
                # セッションを作成（接続の再利用）
                session = requests.Session()
                session.headers.update({
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                })
                
                def fetch_and_parse_html_page(page_url: str) -> Tuple[Dict[int, Dict[str, str]], Dict[int, Dict[str, str]]]:
                    """HTMLページを取得してパース（並列処理用）"""
                    html_content = fetch_page(page_url)
                    if not html_content:
                        return {}, {}
                    
                    soup = BeautifulSoup(html_content, 'html.parser')
                    page_n4_data, page_n3_data = parse_mizuhobank_table(soup, max_round=html_max)
                    return page_n4_data, page_n3_data
                
                # 並列処理で取得（最大8並列）
                max_workers = 8
                with ThreadPoolExecutor(max_workers=max_workers) as executor:
                    future_to_url = {
                        executor.submit(fetch_and_parse_html_page, page_url): page_url
                        for page_url in mizuhobank_html_pages
                    }
                    
                    for future in as_completed(future_to_url):
                        page_url = future_to_url[future]
                        try:
                            page_n4_data, page_n3_data = future.result()
                            
                            # 取得対象範囲内のデータのみを追加
                            filtered_n4_data = {
                                round_num: data for round_num, data in page_n4_data.items()
                                if html_min <= round_num <= html_max
                            }
                            filtered_n3_data = {
                                round_num: data for round_num, data in page_n3_data.items()
                                if html_min <= round_num <= html_max
                            }
                            
                            n4_data.update(filtered_n4_data)
                            n3_data.update(filtered_n3_data)
                            
                            if filtered_n4_data or filtered_n3_data:
                                print(f"   ✓ {page_url}: N4={len(filtered_n4_data)}件、N3={len(filtered_n3_data)}件")
                        except Exception as e:
                            print(f"   ⚠ {page_url}の処理でエラー: {e}")
                
                session.close()
                print(f"✓ HTMLページから取得完了: N4={len([r for r in n4_data.keys() if html_min <= r <= html_max])}件、N3={len([r for r in n3_data.keys() if html_min <= r <= html_max])}件")
        
        # 2701-4800回: CSVファイルから取得（並列処理）
        if needs_csv:
            csv_min = max(2701, target_min)
            csv_max = min(4800, target_max)
            print(f"   みずほ銀行のCSVファイルから取得します（第{csv_min}回 ～ 第{csv_max}回）")
            print(f"   ⚡ 並列処理で高速化します（最大8並列）")
            
            # セッションを作成（接続の再利用）
            session = requests.Session()
            session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            
            def fetch_and_parse_round(round_num: int) -> Tuple[int, Optional[str], Optional[str], Optional[str], bool]:
                """1回分のデータを取得してパース（並列処理用）"""
                csv_content = fetch_mizuhobank_csv(round_num, session=session)
                if not csv_content:
                    return round_num, None, None, None, False
                
                n3_winning, n4_winning, draw_date = parse_mizuhobank_csv(
                    csv_content, round_num, max_round=csv_max
                )
                return round_num, n3_winning, n4_winning, draw_date, True
            
            # 並列処理で取得（最大8並列、サーバー負荷を考慮）
            max_workers = 8
            total_rounds = csv_max - csv_min + 1
            completed_count = 0
            
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # すべてのタスクを送信
                future_to_round = {
                    executor.submit(fetch_and_parse_round, round_num): round_num
                    for round_num in range(csv_min, csv_max + 1)
                }
                
                # 完了したタスクから順に処理
                for future in as_completed(future_to_round):
                    round_num = future_to_round[future]
                    completed_count += 1
                    
                    try:
                        round_num_result, n3_winning, n4_winning, draw_date, success = future.result()
                        
                        if not success:
                            # 403エラーや404エラーは連続エラーカウントに含めない（一部のファイルが存在しないのは正常）
                            continue
                        
                        # エラーが発生しなかった場合、カウンターをリセット
                        consecutive_errors = 0
                        
                        # データを保存
                        if n3_winning:
                            n3_data[round_num_result] = {
                                'n3_winning': n3_winning,
                                'n3_rehearsal': '',  # 4800回以前はリハーサル番号なし
                                'draw_date': draw_date,
                            }
                        
                        if n4_winning:
                            n4_data[round_num_result] = {
                                'n4_winning': n4_winning,
                                'n4_rehearsal': '',  # 4800回以前はリハーサル番号なし
                                'draw_date': draw_date,
                            }
                        
                        # 進捗表示（100回ごと、または最初の5回）
                        if round_num_result % 100 == 0 or round_num_result <= csv_min + 5:
                            print(f"   ✓ 第{round_num_result}回: N3={n3_winning or 'N/A'}, N4={n4_winning or 'N/A'} ({completed_count}/{total_rounds})")
                        
                        # 100回ごとにCSVに中間保存（回号ベース）
                        if output_file and (round_num_result - csv_min + 1) % 100 == 0:
                            all_rounds = set(n4_data.keys()) | set(n3_data.keys())
                            current_count = len([r for r in all_rounds if target_min <= r <= round_num_result])
                            
                            print(f"\n💾 中間保存（第{round_num_result}回まで）: {current_count}件のデータをCSVに保存します...")
                            all_rounds_list = sorted(all_rounds, reverse=True)
                            latest_round_for_save = max(all_rounds_list) if all_rounds_list else latest_round
                            
                            temp_data = combine_data(n4_data, n3_data, latest_round_for_save, max_rounds=len(all_rounds_list), merge_mode=True, output_file=output_file)
                            save_to_csv(temp_data, output_file, merge=True)
                            print(f"✓ 中間保存完了（第{round_num_result}回まで、{current_count}件）\n")
                        
                        # サーバー負荷軽減のため、少し待機（並列処理なので短縮）
                        if completed_count % 10 == 0:
                            time.sleep(0.1)
                            
                    except Exception as e:
                        print(f"   ⚠ 第{round_num}回の処理でエラー: {e}")
                        consecutive_errors += 1
            
            # セッションを閉じる
            session.close()
            
            print(f"✓ CSVファイルから取得完了: N4={len([r for r in n4_data.keys() if csv_min <= r <= csv_max])}件、N3={len([r for r in n3_data.keys() if csv_min <= r <= csv_max])}件")
        
        # 最後に、残りのデータを保存（100回の倍数でない場合）
        if output_file and (n4_data or n3_data):
            all_rounds = set(n4_data.keys()) | set(n3_data.keys())
            current_count = len([r for r in all_rounds if target_min <= r <= target_max])
            
            # 最後の100回の倍数で保存されていない場合のみ最終保存
            if (target_max - target_min + 1) % 100 != 0:
                print(f"\n💾 最終保存: {current_count}件のデータをCSVに保存します...")
                all_rounds_list = sorted(all_rounds, reverse=True)
                latest_round_for_save = max(all_rounds_list) if all_rounds_list else latest_round
                
                temp_data = combine_data(n4_data, n3_data, latest_round_for_save, max_rounds=len(all_rounds_list), merge_mode=True, output_file=output_file)
                save_to_csv(temp_data, output_file, merge=True)
                print(f"✓ 最終保存完了（{current_count}件）\n")
        
        print(f"\n✓ みずほ銀行から取得完了: N4={len(n4_data)}件、N3={len(n3_data)}件")
        return n4_data, n3_data
    
    # 4801回以降のデータは、既存の方法（hpfree.com）を使用
    # 4800回以前のデータも含む場合は、両方から取得
    needs_hpfree = target_max >= REHEARSAL_AVAILABLE_FROM
    
    if needs_hpfree:
        # 4801回以降の取得範囲を更新
        if target_min <= REHEARSAL_AVAILABLE_FROM - 1:
            target_min = REHEARSAL_AVAILABLE_FROM
        
        print(f"\n📥 hpfree.comから取得します（第{target_min}回 ～ 第{target_max}回）")
        print(f"   ℹ️  当選番号とリハーサル数字をhpfree.comから取得し、")
        print(f"   日付はみずほ銀行のCSVファイルから取得します。")
        
        # 過去分のページを自動探索
        past_pages = find_past_pages(base_url)
        
        # 範囲指定の場合、必要なページを明示的に追加
        # 2021年1月～6月（5599-5726回）のデータは rehearsal2021-1.html に含まれる
        if target_min <= 5726 and target_max >= 5599:
            rehearsal2021_1_url = f"{BASE_PAGE_URL}rehearsal2021-1.html"
            if rehearsal2021_1_url not in past_pages:
                past_pages.insert(0, rehearsal2021_1_url)
                print(f"  ✓ 必要なページを追加: rehearsal2021-1.html")
        
        # 最新版ページも追加
        all_pages = [LATEST_PAGE_URL] + past_pages
        
        # 必要な件数に達するまで順次取得
        for page_url in all_pages:
            print(f"\n📥 ページを取得中: {page_url}...")
            html_content = fetch_page(page_url)
            
            if not html_content:
                print(f"⚠ ページの取得に失敗しました: {page_url}")
                consecutive_errors += 1
                
                # 5回連続でエラーが発生した場合、それまでのデータを保存して終了
                if consecutive_errors >= max_consecutive_errors:
                    print(f"\n⚠ {max_consecutive_errors}回連続でエラーが発生したため、処理を終了します")
                    if output_file and (n4_data or n3_data):
                        print(f"\n💾 取得済みデータをCSVに保存します...")
                        all_rounds = set(n4_data.keys()) | set(n3_data.keys())
                        if all_rounds:
                            all_rounds_list = sorted(all_rounds, reverse=True)
                            latest_round_for_save = max(all_rounds_list) if all_rounds_list else latest_round
                            temp_data = combine_data(n4_data, n3_data, latest_round_for_save, max_rounds=len(all_rounds_list), merge_mode=True)
                            save_to_csv(temp_data, output_file, merge=True)
                            print(f"✓ {len(temp_data)}件のデータを保存しました")
                    return n4_data, n3_data
                
                continue
            
            # エラーが発生しなかった場合、カウンターをリセット
            consecutive_errors = 0
            
            print(f"✓ ページを取得しました ({len(html_content)}文字)")
            
            # HTMLをパース
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # N4データを抽出
            page_n4_data = parse_n4_table(soup, url=page_url)
            # 取得対象範囲内のデータのみを追加
            filtered_n4_data = {
                round_num: data for round_num, data in page_n4_data.items()
                if target_min <= round_num <= target_max
            }
            n4_data.update(filtered_n4_data)
            print(f"✓ {len(filtered_n4_data)}件のN4データを抽出しました（累計: {len(n4_data)}件）")
            
            # N3データを抽出
            page_n3_data = parse_n3_table(soup, url=page_url)
            # 取得対象範囲内のデータのみを追加
            filtered_n3_data = {
                round_num: data for round_num, data in page_n3_data.items()
                if target_min <= round_num <= target_max
            }
            n3_data.update(filtered_n3_data)
            print(f"✓ {len(filtered_n3_data)}件のN3データを抽出しました（累計: {len(n3_data)}件）")
            
            # 4801回以降のデータについて、みずほ銀行から日付を取得（並列処理）
            if target_min >= REHEARSAL_AVAILABLE_FROM:
                rounds_needing_dates = []
                for round_num in set(filtered_n4_data.keys()) | set(filtered_n3_data.keys()):
                    if round_num >= REHEARSAL_AVAILABLE_FROM:
                        # 既に日付が設定されていない場合のみ取得
                        if not filtered_n4_data.get(round_num, {}).get('draw_date') and not filtered_n3_data.get(round_num, {}).get('draw_date'):
                            rounds_needing_dates.append(round_num)
                
                if rounds_needing_dates:
                    print(f"   📅 {len(rounds_needing_dates)}件の回号について、みずほ銀行から日付を取得します...")
                    
                    # セッションを作成（接続の再利用）
                    date_session = requests.Session()
                    date_session.headers.update({
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                    })
                    
                    def fetch_date_for_round(round_num: int) -> Tuple[int, Optional[str]]:
                        """1回分の日付を取得（並列処理用）"""
                        csv_content = fetch_mizuhobank_csv(round_num, session=date_session)
                        if not csv_content:
                            return round_num, None
                        
                        _, _, draw_date = parse_mizuhobank_csv(csv_content, round_num)
                        return round_num, draw_date
                    
                    # 並列処理で日付を取得（最大8並列）
                    max_workers = 8
                    dates_fetched = 0
                    with ThreadPoolExecutor(max_workers=max_workers) as executor:
                        future_to_round = {
                            executor.submit(fetch_date_for_round, round_num): round_num
                            for round_num in rounds_needing_dates
                        }
                        
                        for future in as_completed(future_to_round):
                            round_num = future_to_round[future]
                            try:
                                round_num_result, draw_date = future.result()
                                if draw_date:
                                    # 取得した日付をデータに保存
                                    if round_num_result in n4_data:
                                        n4_data[round_num_result]['draw_date'] = draw_date
                                    if round_num_result in n3_data:
                                        n3_data[round_num_result]['draw_date'] = draw_date
                                    dates_fetched += 1
                            except Exception as e:
                                print(f"   ⚠ 第{round_num}回の日付取得でエラー: {e}")
                    
                    date_session.close()
                    print(f"   ✓ {dates_fetched}件の日付を取得しました")
            
            # 必要な件数に達したか確認（N4とN3の両方を考慮）
            target_rounds_in_data = set()
            for r in n4_data.keys():
                if target_min <= r <= target_max:
                    target_rounds_in_data.add(r)
            for r in n3_data.keys():
                if target_min <= r <= target_max:
                    target_rounds_in_data.add(r)
            
            # 目標範囲内の最小回号が取得できたか確認
            if target_rounds_in_data:
                min_fetched = min(target_rounds_in_data)
                if min_fetched <= target_min and len(target_rounds_in_data) >= max_rounds:
                    print(f"\n✓ 目標範囲内のデータが十分に取得できました（{len(target_rounds_in_data)}件 >= {max_rounds}件、最小回号: 第{min_fetched}回）")
                    break
            
            # 100件ごとにCSVに保存
            if output_file:
                all_rounds = set(n4_data.keys()) | set(n3_data.keys())
                current_count = len([r for r in all_rounds if target_min <= r <= target_max])
                
                if current_count - last_save_count >= save_interval:
                    print(f"\n💾 中間保存: {current_count}件のデータをCSVに保存します...")
                    # データを結合
                    all_rounds_list = sorted(all_rounds, reverse=True)
                    latest_round_for_save = max(all_rounds_list) if all_rounds_list else latest_round
                    
                    temp_data = combine_data(n4_data, n3_data, latest_round_for_save, max_rounds=len(all_rounds_list), merge_mode=True)
                    save_to_csv(temp_data, output_file, merge=True, update_null=update_null)
                    last_save_count = current_count
                    print(f"✓ 中間保存完了（{current_count}件）\n")
            
            # 次のページに進む前に少し待機
            time.sleep(1)
        
        # 最後に、残りのデータを保存（中間保存で保存されていない場合）
        if output_file and (n4_data or n3_data):
            all_rounds = set(n4_data.keys()) | set(n3_data.keys())
            current_count = len([r for r in all_rounds if target_min <= r <= target_max])
            
            # 最後に保存されていないデータがある場合、最終保存を実行
            if current_count > last_save_count:
                print(f"\n💾 最終保存: {current_count}件のデータをCSVに保存します...")
                all_rounds_list = sorted(all_rounds, reverse=True)
                latest_round_for_save = max(all_rounds_list) if all_rounds_list else latest_round
                
                temp_data = combine_data(n4_data, n3_data, latest_round_for_save, max_rounds=len(all_rounds_list), merge_mode=True)
                save_to_csv(temp_data, output_file, merge=True, update_null=update_null)
                print(f"✓ 最終保存完了（{current_count}件）\n")
    
    return n4_data, n3_data


def main():
    if not HAS_DEPS:
        sys.exit(1)
    
    # 引数解析
    output_file = Path(__file__).parent.parent / 'data' / 'past_results.csv'
    max_rounds = 300
    merge_mode = False  # マージモード（自動実行時のみ）
    fill_gaps_mode = False  # 欠番を埋めるモード
    update_null_mode = False  # NULL値を更新するモード
    target_min_round = None  # 取得対象の最小回号
    target_max_round = None  # 取得対象の最大回号
    
    # 引数を解析（順序に関係なく動作するように）
    args = sys.argv[1:]
    i = 0
    while i < len(args):
        arg = args[i]
        
        if arg == '--limit' and i + 1 < len(args):
            try:
                max_rounds = int(args[i + 1])
                i += 2
            except ValueError:
                i += 1
        elif arg == '--merge':
            merge_mode = True
            # --merge の後に数字が続く場合（古い形式の互換性）
            if i + 1 < len(args) and args[i + 1].isdigit():
                max_rounds = int(args[i + 1])
                i += 2
            else:
                # マージモードのデフォルトは1件
                if max_rounds == 300:
                    max_rounds = 1
                i += 1
        elif arg == '--fill-gaps':
            fill_gaps_mode = True
            merge_mode = True  # 欠番を埋める場合はマージモード
            i += 1
        elif arg == '--update-null':
            update_null_mode = True
            merge_mode = True  # NULL値を更新する場合はマージモード
            i += 1
        elif arg == '--from-round' and i + 1 < len(args):
            try:
                target_min_round = int(args[i + 1])
                merge_mode = True  # 範囲指定時はマージモード
                i += 2
            except ValueError:
                i += 1
        elif arg == '--to-round' and i + 1 < len(args):
            try:
                target_max_round = int(args[i + 1])
                merge_mode = True  # 範囲指定時はマージモード
                i += 2
            except ValueError:
                i += 1
        elif arg == '--help' or arg == '-h':
            print("使い方:")
            print("  python3 fetch_past_results.py [output_file] [--limit N] [--use-fallback] [--merge]")
            print("")
            print("オプション:")
            print("  output_file     出力ファイルパス（デフォルト: data/past_results.csv）")
            print("  --limit N       取得する最大件数（デフォルト: 300）")
            print("  --merge         既存CSVファイルとマージ（--limit Nで大量取得も可能）")
            print("  --fill-gaps     欠番の回号を検出して取得してマージ")
            print("  --update-null   既存データのNULL値を新しいデータで更新")
            print("  --from-round N  取得対象の最小回号を指定")
            print("  --to-round N    取得対象の最大回号を指定")
            print("  --use-fallback  Webスクレイピング失敗時に検索APIを使用")
            print("")
            print("例:")
            print("  python3 fetch_past_results.py")
            print("  python3 fetch_past_results.py --limit 1000")
            print("  python3 fetch_past_results.py --merge  # 最新の1回分のみ追加")
            print("  python3 fetch_past_results.py --merge --limit 1000  # 既存CSVの最古回号より前の1000件を取得してマージ")
            print("  python3 fetch_past_results.py --fill-gaps  # 欠番の回号を検出して取得してマージ")
            print("  python3 fetch_past_results.py --update-null  # 既存データのNULL値を更新")
            print("  python3 fetch_past_results.py --from-round 1 --to-round 4800  # 第1回～第4800回を取得")
            print("  python3 fetch_past_results.py --limit 1000 --merge  # 同じ意味")
            sys.exit(0)
        elif not arg.startswith('--'):
            output_file = Path(arg)
            i += 1
        else:
            i += 1
    
    # 最新回号を取得
    print("=" * 80)
    print("ナンバーズ過去当選番号・リハーサル番号取得スクリプト")
    print("=" * 80)
    
    # 表示メッセージを更新
    if fill_gaps_mode:
        print(f"\nモード: 欠番を埋める（既存CSVの欠番を検出して取得）")
    elif update_null_mode:
        print(f"\nモード: NULL値を更新（既存データのNULL値を新しいデータで更新）")
    elif merge_mode:
        if max_rounds == 1:
            print(f"\nモード: マージ（最新の1回分のみ追加）")
        else:
            min_existing_round, max_existing_round = get_existing_round_range(output_file)
            if min_existing_round is not None:
                print(f"\nモード: マージ（既存CSVの最古回号より前の{max_rounds}件を追加）")
            else:
                print(f"\nモード: マージ（最新回から{max_rounds}件を追加）")
    else:
        print(f"\nモード: 上書き（最新回から{max_rounds}件を取得、既存CSVは上書き）")
    
    print(f"出力先: {output_file}\n")
    
    latest_round = get_latest_round_number()
    if latest_round is None:
        print("⚠ 最新回号が取得できませんでした")
        sys.exit(1)
    
    print(f"最新回号: 第{latest_round}回")
    
    # ベースURL
    base_url = BASE_PAGE_URL
    
    # 既存CSVの回号範囲を取得
    min_existing_round, max_existing_round = get_existing_round_range(output_file)
    
    # 範囲指定モードの処理
    if target_min_round is not None or target_max_round is not None:
        # 範囲が指定されている場合
        if target_min_round is None:
            target_min_round = 1  # デフォルトは第1回から
        if target_max_round is None:
            target_max_round = latest_round  # デフォルトは最新回まで
        
        print(f"\nモード: 範囲指定（第{target_min_round}回 ～ 第{target_max_round}回）")
        print(f"📥 指定範囲のデータを取得します（第{target_min_round}回 ～ 第{target_max_round}回）...")
        
        # 指定範囲のデータを取得
        n4_data, n3_data = fetch_multiple_pages(
            base_url,
            target_max_round - target_min_round + 1,  # 範囲内の全件数
            latest_round=None,
            target_min_round=target_min_round,
            target_max_round=target_max_round,
            output_file=output_file,  # 100件ごとにCSVに保存
            update_null=True  # 範囲指定モードでは常にNULL値を更新
        )
        
        print(f"✓ 範囲指定のデータを取得: N4={len(n4_data)}件、N3={len(n3_data)}件")
        
        if not n4_data and not n3_data:
            print("⚠ 指定範囲のデータが取得できませんでした")
            sys.exit(1)
        
        # 取得したデータの範囲を使用
        if n4_data or n3_data:
            all_rounds = set(n4_data.keys()) | set(n3_data.keys())
            if all_rounds:
                latest_round = max(all_rounds)
        
        # 範囲指定モードの場合、fetch_multiple_pages内で既に中間保存が行われているため、
        # 最後の保存はスキップ（中間保存で既にCSVに保存済み）
        print("\n💾 範囲指定モード: 中間保存で既にCSVに保存済みのため、最終保存をスキップします")
        print("=" * 80)
        print("✓ 処理完了")
        print("=" * 80)
        sys.exit(0)
    elif update_null_mode:
        print("\n🔍 NULL値がある回号を検出中...")
        existing_data = load_existing_csv(output_file)
        if not existing_data:
            print("⚠ 既存CSVファイルが見つかりませんでした")
            sys.exit(1)
        
        # NULL値がある回号を検出
        null_rounds = []
        for row in existing_data:
            round_num = int(row.get('round_number', 0))
            if round_num > 0:
                # いずれかのフィールドがNULLまたは空の場合
                has_null = False
                for key in ['draw_date', 'n3_winning', 'n4_winning', 'n3_rehearsal', 'n4_rehearsal']:
                    value = row.get(key, '')
                    if not value or value == 'NULL':
                        has_null = True
                        break
                if has_null:
                    null_rounds.append(round_num)
        
        if not null_rounds:
            print("✓ NULL値はありませんでした")
            sys.exit(0)
        
        print(f"✓ {len(null_rounds)}件のNULL値がある回号を検出しました")
        print(f"   NULL値がある回号: {null_rounds[:20]}{'...' if len(null_rounds) > 20 else ''}")
        
        # NULL値がある回号を含む範囲を取得
        min_null = min(null_rounds)
        max_null = max(null_rounds)
        
        print(f"\n📥 NULL値がある回号を取得します（第{min_null}回 ～ 第{max_null}回）...")
        
        # NULL値がある回号を含む範囲のデータを取得
        n4_data, n3_data = fetch_multiple_pages(
            base_url,
            len(null_rounds),  # NULL値がある回号の数だけ取得
            latest_round=None,
            target_min_round=min_null,
            target_max_round=max_null,
            output_file=output_file,  # 100件ごとにCSVに保存
            update_null=update_null_mode  # NULL値を更新するかどうか
        )
        
        # NULL値がある回号のみをフィルタリング
        filtered_n4_data = {r: n4_data[r] for r in null_rounds if r in n4_data}
        filtered_n3_data = {r: n3_data[r] for r in null_rounds if r in n3_data}
        
        n4_data = filtered_n4_data
        n3_data = filtered_n3_data
        
        print(f"✓ NULL値がある回号のデータを取得: N4={len(n4_data)}件、N3={len(n3_data)}件")
        
        if not n4_data and not n3_data:
            print("⚠ NULL値がある回号のデータが取得できませんでした")
            sys.exit(1)
        
        # 取得したデータの範囲を使用
        if n4_data or n3_data:
            all_rounds = set(n4_data.keys()) | set(n3_data.keys())
            if all_rounds:
                latest_round = max(all_rounds)
    # 欠番を埋めるモードの処理
    elif fill_gaps_mode:
        print("\n🔍 欠番の回号を検出中...")
        missing_rounds = find_missing_rounds(output_file)
        
        if not missing_rounds:
            print("✓ 欠番はありませんでした")
            sys.exit(0)
        
        print(f"✓ {len(missing_rounds)}件の欠番を検出しました")
        print(f"   欠番の回号: {missing_rounds[:20]}{'...' if len(missing_rounds) > 20 else ''}")
        
        # 欠番の回号を含む範囲を取得
        min_missing = min(missing_rounds)
        max_missing = max(missing_rounds)
        
        print(f"\n📥 欠番の回号を取得します（第{min_missing}回 ～ 第{max_missing}回）...")
        print(f"   ℹ️  みずほ銀行から当選番号と日付を取得します。")
        
        # みずほ銀行から直接取得
        n4_data = {}
        n3_data = {}
        
        # セッションを作成（接続の再利用）
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        def fetch_round_from_mizuhobank(round_num: int) -> Tuple[int, Optional[str], Optional[str], Optional[str]]:
            """1回分のデータをみずほ銀行から取得（並列処理用）"""
            # まずCSVファイルから取得を試行
            csv_content = fetch_mizuhobank_csv(round_num, session=session)
            if csv_content:
                n3_winning, n4_winning, draw_date = parse_mizuhobank_csv(csv_content, round_num)
                if n3_winning or n4_winning:
                    return round_num, n3_winning, n4_winning, draw_date
            
            # CSVファイルが取得できない場合、HTMLページから取得を試行（4800回以前のみ）
            if round_num <= 4800:
                # HTMLページのURLを生成
                html_pages = find_mizuhobank_pages(round_num, round_num)
                if html_pages:
                    html_content = fetch_page(html_pages[0])
                    if html_content:
                        soup = BeautifulSoup(html_content, 'html.parser')
                        page_n4_data, page_n3_data = parse_mizuhobank_table(soup, max_round=round_num)
                        if round_num in page_n4_data or round_num in page_n3_data:
                            n4_info = page_n4_data.get(round_num, {})
                            n3_info = page_n3_data.get(round_num, {})
                            return (
                                round_num,
                                n3_info.get('n3_winning'),
                                n4_info.get('n4_winning'),
                                n4_info.get('draw_date') or n3_info.get('draw_date')
                            )
            
            return round_num, None, None, None
        
        # 並列処理で取得（最大8並列）
        max_workers = 8
        completed_count = 0
        total_rounds = len(missing_rounds)
        
        print(f"   ⚡ 並列処理で高速化します（最大{max_workers}並列）")
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_round = {
                executor.submit(fetch_round_from_mizuhobank, round_num): round_num
                for round_num in missing_rounds
            }
            
            for future in as_completed(future_to_round):
                round_num = future_to_round[future]
                completed_count += 1
                
                try:
                    round_num_result, n3_winning, n4_winning, draw_date = future.result()
                    
                    if n3_winning:
                        n3_data[round_num_result] = {
                            'n3_winning': n3_winning,
                            'n3_rehearsal': '',  # みずほ銀行にはリハーサル数字がない
                            'draw_date': draw_date or '',
                        }
                    
                    if n4_winning:
                        n4_data[round_num_result] = {
                            'n4_winning': n4_winning,
                            'n4_rehearsal': '',  # みずほ銀行にはリハーサル数字がない
                            'draw_date': draw_date or '',
                        }
                    
                    # 進捗表示（50回ごと、または最初の5回）
                    if completed_count % 50 == 0 or completed_count <= 5:
                        print(f"   ✓ 第{round_num_result}回: N3={n3_winning or 'N/A'}, N4={n4_winning or 'N/A'}, Date={draw_date or 'N/A'} ({completed_count}/{total_rounds})")
                    
                    # サーバー負荷軽減のため、少し待機
                    if completed_count % 10 == 0:
                        time.sleep(0.1)
                        
                except Exception as e:
                    print(f"   ⚠ 第{round_num}回の処理でエラー: {e}")
        
        session.close()
        
        # 欠番の回号のみをフィルタリング
        filtered_n4_data = {r: n4_data[r] for r in missing_rounds if r in n4_data}
        filtered_n3_data = {r: n3_data[r] for r in missing_rounds if r in n3_data}
        
        n4_data = filtered_n4_data
        n3_data = filtered_n3_data
        
        print(f"\n✓ みずほ銀行から取得完了: N4={len(n4_data)}件、N3={len(n3_data)}件")
        
        if not n4_data and not n3_data:
            print("⚠ 欠番のデータが取得できませんでした")
            sys.exit(1)
        
        # 取得したデータの範囲を使用
        if n4_data or n3_data:
            all_rounds = set(n4_data.keys()) | set(n3_data.keys())
            if all_rounds:
                latest_round = max(all_rounds)
    # マージモードの処理
    elif merge_mode:
        if max_rounds == 1:
            # デフォルト: 最新版ページから最新の1回分のみ取得
            print("📥 マージモード: 最新版ページから最新の1回分のみ取得します...")
            html_content = fetch_page(LATEST_PAGE_URL)
            if html_content:
                soup = BeautifulSoup(html_content, 'html.parser')
                # 最新の1行のみ取得
                n4_data = parse_n4_table(soup, latest_only=True, url=LATEST_PAGE_URL)
                n3_data = parse_n3_table(soup, latest_only=True, url=LATEST_PAGE_URL)
                print(f"✓ 最新データを取得: N4={len(n4_data)}件、N3={len(n3_data)}件")
                
                # 取得したデータの回号を使用（実際に取得できた回号）
                if n4_data:
                    actual_latest_round = max(n4_data.keys())
                elif n3_data:
                    actual_latest_round = max(n3_data.keys())
                else:
                    actual_latest_round = latest_round
                
                latest_round = actual_latest_round
                print(f"実際に取得した回号: 第{latest_round}回")
            else:
                n4_data, n3_data = {}, {}
        else:
            # 大量取得時: 既存CSVの最古回号より前のデータを取得
            if min_existing_round is not None:
                # 既存CSVがある場合: 最古回号より前のデータを取得
                target_min_round = min_existing_round - max_rounds
                target_max_round = min_existing_round - 1
                print(f"📥 マージモード（大量取得）: 既存CSVの最古回号（第{min_existing_round}回）より前の{max_rounds}件を取得します...")
                print(f"   取得範囲: 第{target_min_round}回 ～ 第{target_max_round}回")
                
                # 既存データにない回号のみを取得するために、取得範囲を指定
                n4_data, n3_data = fetch_multiple_pages(
                    base_url, 
                    max_rounds, 
                    latest_round=None,  # 実際にはtarget_max_roundを使用
                    target_min_round=target_min_round,
                    target_max_round=target_max_round,
                    output_file=output_file  # 100件ごとにCSVに保存
                )
                
                # 取得したデータの範囲を使用
                if n4_data or n3_data:
                    all_rounds = set(n4_data.keys()) | set(n3_data.keys())
                    if all_rounds:
                        latest_round = max(all_rounds)
            else:
                # 既存CSVがない場合: 最新回から指定件数を取得
                print(f"📥 マージモード（大量取得）: 既存CSVがないため、最新回から{max_rounds}件を取得します...")
                n4_data, n3_data = fetch_multiple_pages(base_url, max_rounds, latest_round, output_file=output_file)
    else:
        # 通常モード: 複数ページからデータを取得（既存CSVは上書き）
        print(f"📥 通常モード: 最新回から{max_rounds}件を取得します（既存CSVは上書きされます）...")
        n4_data, n3_data = fetch_multiple_pages(base_url, max_rounds, latest_round, output_file=output_file)
    
    # Webスクレイピングに失敗した場合、フォールバック機能を試す
    use_fallback = '--use-fallback' in sys.argv
    
    if not n4_data and not n3_data:
        if use_fallback or (GEMINI_API_KEY or SERP_API_KEY):
            n4_data, n3_data = fetch_with_fallback(base_url, max_rounds)
        
        if not n4_data and not n3_data:
            print("✗ データが取得できませんでした")
            sys.exit(1)
    elif not n4_data:
        # N3データだけでも処理を続行
        print("⚠ N4データが取得できませんでしたが、N3データのみで処理を続行します")
    
    # データを結合
    print("\n🔗 データを結合中...")
    # 欠番を埋めるモードまたはマージモードの場合は、取得したデータをそのまま使用
    data = combine_data(n4_data, n3_data, latest_round, max_rounds, merge_mode=merge_mode or fill_gaps_mode, output_file=output_file)
    print(f"✓ {len(data)}件のデータを結合しました")
    
    if not data:
        print("⚠ データが抽出できませんでした")
        sys.exit(1)
    
    # 抽出結果を表示（最初の5件）
    print("\n【抽出結果（最初の5件）】")
    print("-" * 80)
    for i, row in enumerate(data[:5]):
        print(f"第{row['round_number']}回 ({row['draw_date']}): "
              f"N3={row['n3_winning']}(リ:{row['n3_rehearsal'] or 'なし'}), "
              f"N4={row['n4_winning']}(リ:{row['n4_rehearsal'] or 'なし'})")
    
    if len(data) > 5:
        print(f"... 他 {len(data) - 5}件")
    
    # CSVファイルに保存
    # 注意: fetch_multiple_pages()内で中間保存が行われている場合（output_fileが指定されている場合）、
    # 最終保存はfetch_multiple_pages()内で既に実行されているため、ここではスキップする
    # ただし、output_fileが指定されていない場合（中間保存が無効な場合）のみ、ここで保存する
    was_intermediate_save_used = False
    if target_min_round is not None or target_max_round is not None:
        # 範囲指定モードの場合、fetch_multiple_pages内で既に中間保存が行われている
        was_intermediate_save_used = True
    elif fill_gaps_mode:
        # 欠番を埋めるモードの場合、みずほ銀行から直接取得しているため中間保存は行われていない
        was_intermediate_save_used = False
    elif update_null_mode:
        # NULL値を更新するモードの場合、fetch_multiple_pages内で既に中間保存が行われている
        was_intermediate_save_used = True
    elif merge_mode and max_rounds > 1:
        # マージモード（大量取得）の場合、fetch_multiple_pages内で既に中間保存が行われている
        was_intermediate_save_used = True
    
    if was_intermediate_save_used:
        print("\n💾 中間保存で既にCSVに保存済みのため、最終保存をスキップします")
    else:
        print("\n💾 CSVファイルに保存中...")
        save_to_csv(data, output_file, merge=merge_mode or fill_gaps_mode or update_null_mode, update_null=update_null_mode)
    
    print("\n" + "=" * 80)
    print("✓ 処理完了")
    print("=" * 80)


if __name__ == "__main__":
    main()
