#!/usr/bin/env python3
"""
リハーサル数字可視化用のHTTPサーバー

指定回号の全パターンのデータを生成して返すAPIサーバー

使用方法:
    python3 visualization_server.py [--port 8000]
"""
import pandas as pd
import numpy as np
import sys
import argparse
import json
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from typing import Optional
import traceback

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

# データを一度だけ読み込む
DATA_DIR = PROJECT_ROOT / 'data'
train_csv_path = DATA_DIR / 'train_data_from_4801.csv'
train_df = None
keisen_master = None

def load_data():
    """データを読み込む"""
    global train_df, keisen_master
    if train_df is None:
        train_df = pd.read_csv(train_csv_path)
    if keisen_master is None:
        keisen_master = load_keisen_master(DATA_DIR)

def generate_visualization_data(round_number, pattern, target='n3'):
    """指定回号・パターンのデータを生成"""
    load_data()
    
    # 指定回号のデータを取得
    if round_number not in train_df['round_number'].values:
        return None
    
    row = train_df[train_df['round_number'] == round_number].iloc[0]
    
    # リハーサル数字が存在するかチェック
    if pd.isna(row[f'{target}_rehearsal']) or str(row[f'{target}_rehearsal']) == 'NULL' or str(row[f'{target}_rehearsal']) == 'nan':
        return None
    
    # 予測表を生成
    rehearsal_digits = str(row[f'{target}_rehearsal']).replace('.0', '').zfill(3)
    winning_digits = str(row[f'{target}_winning']).replace('.0', '').zfill(3)
    
    grid, rows, cols = generate_chart(train_df, keisen_master, round_number, pattern, target)
    
    # リハーサル数字と当選番号の位置を取得
    rehearsal_positions = get_rehearsal_positions(grid, rows, cols, rehearsal_digits)
    winning_positions = get_rehearsal_positions(grid, rows, cols, winning_digits)
    
    # グリッドをシリアライズ可能な形式に変換（1-indexedから0-indexedに変換）
    grid_serializable = []
    for r in range(1, rows + 1):
        grid_serializable.append([])
        for c in range(1, cols + 1):
            val = grid[r][c]
            grid_serializable[r - 1].append(int(val) if val is not None else None)
    
    # 各数字の特徴量を計算
    feature_results = []
    for digit in range(10):
        digit_positions = get_digit_positions(grid, rows, cols, digit)
        
        if len(digit_positions) == 0:
            continue
        
        rehearsal_dist = calculate_rehearsal_distance(digit_positions, rehearsal_positions)
        overlap = calculate_overlap_count(digit_positions, rehearsal_positions)
        inverse_ratio = calculate_inverse_ratio(digit_positions, rehearsal_positions, grid)
        
        is_winning = str(digit) in winning_digits
        is_rehearsal = str(digit) in rehearsal_digits
        
        feature_results.append({
            'digit': int(digit),
            'positions_count': len(digit_positions),
            'rehearsal_distance': float(rehearsal_dist),
            'overlap_count': int(overlap),
            'inverse_ratio': float(inverse_ratio),
            'is_winning': bool(is_winning),
            'is_rehearsal': bool(is_rehearsal)
        })
    
    return {
        'round_number': int(round_number),
        'target': target,
        'pattern': pattern,
        'rehearsal_digits': rehearsal_digits,
        'winning_digits': winning_digits,
        'rehearsal_positions': [[int(p[0]), int(p[1])] for p in rehearsal_positions],
        'winning_positions': [[int(p[0]), int(p[1])] for p in winning_positions],
        'feature_results': feature_results,
        'grid': grid_serializable,
        'grid_size': {'rows': int(rows), 'cols': int(cols)}
    }

class VisualizationHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        """GETリクエストを処理"""
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        query_params = parse_qs(parsed_path.query)
        
        # CORSヘッダーを追加
        self.send_response(200)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        
        if path == '/api/rounds':
            # 利用可能な回号リストを返す（リハーサル番号も含む）
            load_data()
            rounds = sorted(train_df['round_number'].unique(), reverse=True)
            rounds_filtered = [r for r in rounds if r >= 6000]
            
            rounds_data = []
            for round_num in rounds_filtered:
                row = train_df[train_df['round_number'] == round_num].iloc[0]
                n3_rehearsal = row['n3_rehearsal']
                n4_rehearsal = row['n4_rehearsal']
                
                # リハーサル番号を文字列に変換
                if pd.notna(n3_rehearsal) and str(n3_rehearsal) != 'NULL' and str(n3_rehearsal) != 'nan':
                    n3_rehearsal_str = str(n3_rehearsal).replace('.0', '').zfill(3)
                else:
                    n3_rehearsal_str = None
                
                if pd.notna(n4_rehearsal) and str(n4_rehearsal) != 'NULL' and str(n4_rehearsal) != 'nan':
                    n4_rehearsal_str = str(n4_rehearsal).replace('.0', '').zfill(4)
                else:
                    n4_rehearsal_str = None
                
                rounds_data.append({
                    'round_number': int(round_num),
                    'n3_rehearsal': n3_rehearsal_str,
                    'n4_rehearsal': n4_rehearsal_str
                })
            
            response = {
                'success': True,
                'rounds': rounds_data
            }
            self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))
        
        elif path == '/api/generate':
            # 指定回号の全パターンのデータを生成
            try:
                round_number = int(query_params.get('round', [None])[0])
                target = query_params.get('target', ['n3'])[0]
                
                if not round_number or round_number < 6000:
                    response = {
                        'success': False,
                        'error': '回号は6000以上を指定してください。'
                    }
                    self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))
                    return
                
                patterns = ['A1', 'A2', 'B1', 'B2']
                result = {}
                
                for pattern in patterns:
                    data = generate_visualization_data(round_number, pattern, target)
                    if data:
                        result[pattern] = data
                
                if len(result) == 0:
                    response = {
                        'success': False,
                        'error': f'回号 {round_number} のデータが見つかりません。'
                    }
                else:
                    response = {
                        'success': True,
                        'round_number': round_number,
                        'data': result
                    }
                
                self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))
            
            except Exception as e:
                response = {
                    'success': False,
                    'error': f'エラーが発生しました: {str(e)}',
                    'traceback': traceback.format_exc()
                }
                self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))
        
        else:
            response = {
                'success': False,
                'error': 'Unknown endpoint'
            }
            self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))
    
    def do_OPTIONS(self):
        """OPTIONSリクエストを処理（CORS用）"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def log_message(self, format, *args):
        """ログメッセージを抑制"""
        pass

def main():
    parser = argparse.ArgumentParser(description='リハーサル数字可視化用HTTPサーバー')
    parser.add_argument('--port', type=int, default=8000,
                        help='サーバーのポート番号（デフォルト: 8000）')
    args = parser.parse_args()
    
    server_address = ('', args.port)
    httpd = HTTPServer(server_address, VisualizationHandler)
    
    print(f"サーバーを起動しました: http://localhost:{args.port}")
    print(f"利用可能なエンドポイント:")
    print(f"  GET /api/rounds - 利用可能な回号リスト")
    print(f"  GET /api/generate?round=<回号>&target=n3 - 指定回号の全パターンデータを生成")
    print("\nCtrl+Cで停止します")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nサーバーを停止しました")
        httpd.shutdown()

if __name__ == '__main__':
    main()

