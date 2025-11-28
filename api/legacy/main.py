"""
FastAPI AI推論エンジン

予測表とリハーサル数字から特徴量を計算し、AIモデルで推論を実行します。
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from pathlib import Path
import sys

# プロジェクトルートのパスを設定
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT / 'core'))

from model_loader import load_model_loader
from chart_generator import load_keisen_master, generate_chart, ChartGenerationError, apply_pattern_expansion, build_main_rows
from feature_extractor import (
    extract_digit_features,
    extract_combination_features,
    add_pattern_id_features,
    add_keisen_pattern_features,
    features_to_vector,
    get_rehearsal_positions
)
import pandas as pd
import numpy as np
import json
import logging
import traceback

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# CUBE生成用のインポート
sys.path.append(str(PROJECT_ROOT / 'scripts'))
from production.generate_extreme_cube import generate_extreme_cube
from production.fetch_past_results import fetch_latest_data_for_api


app = FastAPI(title="Numbers AI Prediction API", version="1.0.0")

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 本番環境では適切に設定する
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# グローバル変数（モデルとデータ）
DATA_DIR = PROJECT_ROOT / 'data'
MODELS_DIR = DATA_DIR / 'models'
model_loader = None
df = None
keisen_master = None

# ファイルの更新日時を記録（自動リロード用）
_file_mtimes = {
    'csv': None,
    'keisen_master': None,
    'models': {}
}


def load_data_and_models(force_reload: bool = False):
    """モデルとデータを読み込む（更新検知付き）"""
    global model_loader, df, keisen_master, _file_mtimes
    
    try:
        # CSVファイルの更新チェック
        csv_path = DATA_DIR / 'past_results.csv'
        if not csv_path.exists():
            raise FileNotFoundError(f"データファイルが見つかりません: {csv_path}")
        
        csv_mtime = csv_path.stat().st_mtime
        if force_reload or _file_mtimes['csv'] is None or csv_mtime > _file_mtimes['csv']:
            print("過去データを読み込み中...")
            df = pd.read_csv(csv_path)
            df = df.sort_values('round_number', ascending=False).reset_index(drop=True)
            _file_mtimes['csv'] = csv_mtime
            print(f"✓ 過去データの読み込み完了（{len(df)}件）")
        
        # 罫線マスターの更新チェック
        keisen_path = DATA_DIR / 'keisen_master.json'
        if keisen_path.exists():
            keisen_mtime = keisen_path.stat().st_mtime
            if force_reload or _file_mtimes['keisen_master'] is None or keisen_mtime > _file_mtimes['keisen_master']:
                print("罫線マスターデータを読み込み中...")
                keisen_master = load_keisen_master(DATA_DIR)
                _file_mtimes['keisen_master'] = keisen_mtime
                print("✓ 罫線マスターデータの読み込み完了")
        
        # モデルファイルの更新チェック
        model_files = {
            'n3_axis': 'n3_axis_lgb.pkl',
            'n4_axis': 'n4_axis_lgb.pkl',
            'n3_box_comb': 'n3_box_comb_lgb.pkl',
            'n3_straight_comb': 'n3_straight_comb_lgb.pkl',
            'n4_box_comb': 'n4_box_comb_lgb.pkl',
            'n4_straight_comb': 'n4_straight_comb_lgb.pkl'
        }
        
        models_updated = False
        for model_name, filename in model_files.items():
            model_path = MODELS_DIR / filename
            if model_path.exists():
                model_mtime = model_path.stat().st_mtime
                if force_reload or model_name not in _file_mtimes['models'] or model_mtime > _file_mtimes['models'][model_name]:
                    models_updated = True
                    _file_mtimes['models'][model_name] = model_mtime
        
        if models_updated or model_loader is None:
            print("モデルを読み込み中...")
            model_loader = load_model_loader(MODELS_DIR)
            print("✓ モデルの読み込み完了")
        
        return True
    except Exception as e:
        print(f"エラー: モデルまたはデータの読み込みに失敗しました: {e}")
        raise


@app.on_event("startup")
async def startup_event():
    """アプリケーション起動時にモデルとデータを読み込む"""
    try:
        load_data_and_models(force_reload=True)
        print("✓ アプリケーションの起動が完了しました")
    except Exception as e:
        # 起動時のエラーをログに記録するが、アプリケーションは起動を続ける
        # （後続のリクエストで再試行できるようにする）
        print(f"警告: 起動時のデータ/モデル読み込みに失敗しました: {e}")
        print("後続のリクエストで再試行されます")
        import traceback
        traceback.print_exc()


# ==================== リクエスト/レスポンス型定義 ====================

class PredictAxisRequest(BaseModel):
    round_number: int = Field(..., ge=1, le=9999)
    target: str = Field(..., pattern="^(n3|n4)$")
    rehearsal_digits: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "round_number": 6758,
                "target": "n3",
                "rehearsal_digits": "149"
            }
        }


class AxisPrediction(BaseModel):
    digit: int
    score: float
    pattern: str


class PredictAxisResponse(BaseModel):
    best_pattern: str
    pattern_scores: Dict[str, float]
    axis_candidates: List[AxisPrediction]


class PredictCombinationRequest(BaseModel):
    round_number: int = Field(..., ge=1, le=9999)
    target: str = Field(..., pattern="^(n3|n4)$")
    combo_type: str = Field(..., pattern="^(box|straight)$")
    best_pattern: str = Field(..., pattern="^(A1|A2|B1|B2)$")
    top_axis_digits: List[int] = Field(..., min_items=1, max_items=10)
    rehearsal_digits: Optional[str] = None
    max_combinations: int = Field(default=100, ge=1, le=1000)


class CombinationPrediction(BaseModel):
    combination: str
    score: float


class PredictCombinationResponse(BaseModel):
    combinations: List[CombinationPrediction]


# ==================== エンドポイント ====================

@app.post("/api/predict/axis", response_model=PredictAxisResponse)
async def predict_axis(request: PredictAxisRequest):
    """
    軸数字を予測する
    
    4パターン（A1/A2/B1/B2）すべての予測表を生成し、
    各パターン×各数字（0-9）に対する予測を実行します。
    
    モデルとデータファイルの更新を自動検知して再読み込みします。
    """
    global model_loader, df, keisen_master
    
    # ファイル更新をチェックして必要に応じて再読み込み
    try:
        load_data_and_models(force_reload=False)
    except Exception as e:
        print(f"警告: データ/モデルの再読み込みに失敗しました（既存データを使用）: {e}")
    
    if model_loader is None:
        raise HTTPException(status_code=500, detail="モデルが読み込まれていません")
    
    if df is None or keisen_master is None:
        raise HTTPException(status_code=500, detail="データが読み込まれていません")
    
    patterns = ['A1', 'A2', 'B1', 'B2']
    pattern_results = {}
    pattern_max_scores = {}
    
    # 必要なデータ（前回・前々回）があるか確認し、なければ取得
    required_rounds = [request.round_number - 1, request.round_number - 2]
    missing_rounds = []
    
    for r in required_rounds:
        if r > 0 and len(df[df['round_number'] == r]) == 0:
            missing_rounds.append(r)
    
    if missing_rounds:
        print(f"データ不足: 第{missing_rounds}回のデータがありません。取得を試みます。")
        try:
            new_rows = []
            for r in missing_rounds:
                # データ取得
                fetched_data = fetch_latest_data_for_api(r)
                if fetched_data:
                    new_rows.append(fetched_data)
            
            if new_rows:
                # DataFrameに追加
                new_df = pd.DataFrame(new_rows)
                # 既存のDataFrameと結合
                df = pd.concat([df, new_df], ignore_index=True)
                # 回号でソート
                df = df.sort_values('round_number', ascending=False).reset_index(drop=True)
                
                # データ型変換（文字列型に統一）
                df['n3_winning'] = df['n3_winning'].astype(str).str.replace('.0', '', regex=False)
                df['n4_winning'] = df['n4_winning'].astype(str).str.replace('.0', '', regex=False)
                # 先頭0を補完
                df['n3_winning'] = df['n3_winning'].apply(lambda x: str(x).zfill(3) if pd.notna(x) and str(x) != 'NULL' else x)
                df['n4_winning'] = df['n4_winning'].apply(lambda x: str(x).zfill(4) if pd.notna(x) and str(x) != 'NULL' else x)
                
                print(f"✓ {len(new_rows)}件のデータを追加しました")
        except Exception as e:
            print(f"⚠ データ自動取得エラー: {e}")
            # エラーが出ても既存データで続行

    try:
        # 各パターンで予測を実行
        for pattern in patterns:
            # 予測表を生成
            grid, rows, cols = generate_chart(
                df, keisen_master, request.round_number, pattern, request.target
            )
            
            # リハーサル位置を取得
            rehearsal_positions = None
            if request.rehearsal_digits:
                rehearsal_positions = get_rehearsal_positions(
                    grid, rows, cols, request.rehearsal_digits
                )
            
            # 前回・前々回の当選番号を取得（罫線パターン特徴量用）
            previous_winning = None
            previous_previous_winning = None
            previous_row = df[df['round_number'] == request.round_number - 1]
            previous_previous_row = df[df['round_number'] == request.round_number - 2]
            
            if len(previous_row) > 0:
                previous_winning = str(previous_row[f'{request.target}_winning'].iloc[0]).replace('.0', '')
                if request.target == 'n3' and len(previous_winning) < 3:
                    previous_winning = previous_winning.zfill(3)
                elif request.target == 'n4' and len(previous_winning) < 4:
                    previous_winning = previous_winning.zfill(4)
            
            if len(previous_previous_row) > 0:
                previous_previous_winning = str(previous_previous_row[f'{request.target}_winning'].iloc[0]).replace('.0', '')
                if request.target == 'n3' and len(previous_previous_winning) < 3:
                    previous_previous_winning = previous_previous_winning.zfill(3)
                elif request.target == 'n4' and len(previous_previous_winning) < 4:
                    previous_previous_winning = previous_previous_winning.zfill(4)
            
            # 各数字（0-9）の特徴量を抽出して予測
            digit_scores = []
            for digit in range(10):
                features = extract_digit_features(
                    grid, rows, cols, digit, rehearsal_positions
                )
                features = add_pattern_id_features(features, pattern)
                
                # 罫線パターンID特徴量を追加
                if previous_winning and previous_previous_winning:
                    features = add_keisen_pattern_features(
                        features, previous_winning, previous_previous_winning, request.target
                    )
                
                feature_vector = features_to_vector(features)
                
                # 予測確率を取得
                proba = model_loader.predict_axis(
                    request.target, feature_vector.reshape(1, -1)
                )[0]
                
                # スコア算出（確率 × 1000）
                score = proba * 1000
                digit_scores.append({
                    'digit': digit,
                    'score': float(score),
                    'pattern': pattern
                })
            
            # スコア順にソート（降順）
            digit_scores.sort(key=lambda x: x['score'], reverse=True)
            pattern_results[pattern] = digit_scores
            
            # パターンの最高スコアを記録
            if digit_scores:
                pattern_max_scores[pattern] = max(s['score'] for s in digit_scores)
        
        # 最良パターンを特定（最高スコアが最も高いパターン）
        best_pattern = max(pattern_max_scores.items(), key=lambda x: x[1])[0]
        
        # 全パターン統合の軸数字ランキング
        all_axis_scores = {}
        for pattern, digit_scores in pattern_results.items():
            for item in digit_scores:
                digit = item['digit']
                score = item['score']
                if digit not in all_axis_scores or score > all_axis_scores[digit]['score']:
                    all_axis_scores[digit] = {
                        'digit': digit,
                        'score': score,
                        'pattern': pattern
                    }
        
        axis_candidates = sorted(
            all_axis_scores.values(),
            key=lambda x: x['score'],
            reverse=True
        )
        
        return PredictAxisResponse(
            best_pattern=best_pattern,
            pattern_scores={p: pattern_max_scores.get(p, 0.0) for p in patterns},
            axis_candidates=[
                AxisPrediction(**item) for item in axis_candidates
            ]
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"予測エラー: {str(e)}")


@app.post("/api/predict/combination", response_model=PredictCombinationResponse)
async def predict_combination(request: PredictCombinationRequest):
    """
    組み合わせを予測する
    
    指定された軸数字を含む組み合わせを生成し、予測を実行します。
    
    モデルとデータファイルの更新を自動検知して再読み込みします。
    """
    global model_loader, df, keisen_master
    
    # ファイル更新をチェックして必要に応じて再読み込み
    try:
        load_data_and_models(force_reload=False)
    except Exception as e:
        print(f"警告: データ/モデルの再読み込みに失敗しました（既存データを使用）: {e}")
    
    if model_loader is None:
        raise HTTPException(status_code=500, detail="モデルが読み込まれていません")
    
    if df is None or keisen_master is None:
        raise HTTPException(status_code=500, detail="データが読み込まれていません")
    
    # 必要なデータ（前回・前々回）があるか確認し、なければ取得
    required_rounds = [request.round_number - 1, request.round_number - 2]
    missing_rounds = []
    
    for r in required_rounds:
        if r > 0 and len(df[df['round_number'] == r]) == 0:
            missing_rounds.append(r)
    
    if missing_rounds:
        print(f"データ不足: 第{missing_rounds}回のデータがありません。取得を試みます。")
        try:
            new_rows = []
            for r in missing_rounds:
                # データ取得
                fetched_data = fetch_latest_data_for_api(r)
                if fetched_data:
                    new_rows.append(fetched_data)
            
            if new_rows:
                # DataFrameに追加
                new_df = pd.DataFrame(new_rows)
                # 既存のDataFrameと結合
                df = pd.concat([df, new_df], ignore_index=True)
                # 回号でソート
                df = df.sort_values('round_number', ascending=False).reset_index(drop=True)
                
                # データ型変換（文字列型に統一）
                df['n3_winning'] = df['n3_winning'].astype(str).str.replace('.0', '', regex=False)
                df['n4_winning'] = df['n4_winning'].astype(str).str.replace('.0', '', regex=False)
                # 先頭0を補完
                df['n3_winning'] = df['n3_winning'].apply(lambda x: str(x).zfill(3) if pd.notna(x) and str(x) != 'NULL' else x)
                df['n4_winning'] = df['n4_winning'].apply(lambda x: str(x).zfill(4) if pd.notna(x) and str(x) != 'NULL' else x)
                
                print(f"✓ {len(new_rows)}件のデータを追加しました")
        except Exception as e:
            print(f"⚠ データ自動取得エラー: {e}")
            # エラーが出ても既存データで続行

    try:
        # 予測表を生成
        grid, rows, cols = generate_chart(
            df, keisen_master, request.round_number, request.best_pattern, request.target
        )
        
        # リハーサル位置を取得
        rehearsal_positions = None
        if request.rehearsal_digits:
            rehearsal_positions = get_rehearsal_positions(
                grid, rows, cols, request.rehearsal_digits
            )
        
        # 組み合わせを生成（軸数字を含む組み合わせを優先）
        digit_count = 3 if request.target == 'n3' else 4
        combinations = []
        
        # 軸数字を含む組み合わせを生成
        for axis_digit in request.top_axis_digits[:5]:  # 上位5つの軸数字を使用
            other_digits = [d for d in range(10) if d != axis_digit]
            
            if request.target == 'n3':
                # N3: 軸数字 + 他の2数字
                for i, d1 in enumerate(other_digits):
                    for d2 in other_digits[i+1:]:
                        combo = ''.join(map(str, sorted([axis_digit, d1, d2])))
                        if combo not in combinations:
                            combinations.append(combo)
            else:
                # N4: 軸数字 + 他の3数字
                for i, d1 in enumerate(other_digits):
                    for j, d2 in enumerate(other_digits[i+1:]):
                        for d3 in other_digits[i+j+2:]:
                            combo = ''.join(map(str, sorted([axis_digit, d1, d2, d3])))
                            if combo not in combinations:
                                combinations.append(combo)
            
            if len(combinations) >= request.max_combinations:
                break
        
        # モデルが存在するか確認
        model_name = f"{request.target}_{request.combo_type}_comb"
        if model_name not in model_loader.get_available_models():
            # モデルが見つからない場合は空の結果を返す（エラーではなくスキップ）
            print(f"警告: モデルが見つかりません: {model_name}。空の結果を返します。")
            return PredictCombinationResponse(combinations=[])
        
        # 前回・前々回の当選番号を取得（罫線パターン特徴量用）
        previous_winning = None
        previous_previous_winning = None
        previous_row = df[df['round_number'] == request.round_number - 1]
        previous_previous_row = df[df['round_number'] == request.round_number - 2]
        
        if len(previous_row) > 0:
            previous_winning = str(previous_row[f'{request.target}_winning'].iloc[0]).replace('.0', '')
            if request.target == 'n3' and len(previous_winning) < 3:
                previous_winning = previous_winning.zfill(3)
            elif request.target == 'n4' and len(previous_winning) < 4:
                previous_winning = previous_winning.zfill(4)
        
        if len(previous_previous_row) > 0:
            previous_previous_winning = str(previous_previous_row[f'{request.target}_winning'].iloc[0]).replace('.0', '')
            if request.target == 'n3' and len(previous_previous_winning) < 3:
                previous_previous_winning = previous_previous_winning.zfill(3)
            elif request.target == 'n4' and len(previous_previous_winning) < 4:
                previous_previous_winning = previous_previous_winning.zfill(4)
        
        # 特徴量を抽出して予測
        combo_scores = []
        for combo in combinations[:request.max_combinations]:
            features = extract_combination_features(
                grid, rows, cols, combo, rehearsal_positions
            )
            features = add_pattern_id_features(features, request.best_pattern)
            
            # 罫線パターンID特徴量を追加
            if previous_winning and previous_previous_winning:
                features = add_keisen_pattern_features(
                    features, previous_winning, previous_previous_winning, request.target
                )
            
            feature_vector = features_to_vector(features)
            
            try:
                # 予測確率を取得
                proba = model_loader.predict_combination(
                    request.target, request.combo_type, feature_vector.reshape(1, -1)
                )[0]
                
                # スコア算出（確率 × 1000）
                score = proba * 1000
                combo_scores.append({
                    'combination': combo,
                    'score': float(score)
                })
            except ValueError as e:
                # モデル関連のエラーの場合はスキップ
                if "モデルが見つかりません" in str(e):
                    print(f"警告: {e}。組み合わせ予測をスキップします。")
                    break
                raise
        
        # スコア順にソート（降順）
        combo_scores.sort(key=lambda x: x['score'], reverse=True)
        
        return PredictCombinationResponse(
            combinations=[
                CombinationPrediction(**item) for item in combo_scores
            ]
        )
        
    except Exception as e:
        # モデルが見つからないエラーの場合は空の結果を返す
        if "モデルが見つかりません" in str(e):
            print(f"警告: {e}。空の結果を返します。")
            return PredictCombinationResponse(combinations=[])
        raise HTTPException(status_code=500, detail=f"組み合わせ予測エラー: {str(e)}")


@app.get("/health")
async def health_check():
    """ヘルスチェック"""
    return {
        "status": "ok",
        "model_loaded": model_loader is not None,
        "data_loaded": df is not None and keisen_master is not None
    }


@app.post("/api/reload")
async def reload_models_and_data():
    """
    モデルとデータを強制的に再読み込みする
    
    このエンドポイントを呼び出すことで、ファイルの更新日時に関係なく
    強制的にモデルとデータを再読み込みできます。
    """
    try:
        load_data_and_models(force_reload=True)
        return {
            "success": True,
            "message": "モデルとデータを再読み込みしました"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"再読み込みエラー: {str(e)}")


def load_keisen_master_by_type(keisen_type: str) -> dict:
    """罫線マスターデータを読み込む（種類指定）
    
    Args:
        keisen_type: 'current'（現罫線）または'new'（新罫線）
    
    Returns:
        罫線マスターデータ
    """
    if keisen_type == 'new':
        keisen_path = DATA_DIR / 'keisen_master_new.json'
    else:
        keisen_path = DATA_DIR / 'keisen_master.json'
    
    if not keisen_path.exists():
        raise FileNotFoundError(f"罫線マスターファイルが見つかりません: {keisen_path}")
    
    with open(keisen_path, 'r', encoding='utf-8') as f:
        return json.load(f)


@app.get("/api/cube/{round_number}")
async def get_cubes(round_number: int):
    """
    指定回号で10個のCUBEを生成する
    
    - 通常CUBE: 現罫線 × 4パターン（A1, A2, B1, B2） × N3/N4 = 8個
    - 極CUBE: 現罫線 × 1パターン + 新罫線 × 1パターン = 2個
    - 合計: 10個のCUBE
    
    Args:
        round_number: 回号
    
    Returns:
        CUBEデータの辞書
    """
    global df
    
    logger.info(f"CUBE生成リクエスト受信: 回号={round_number}")
    
    try:
        if df is None:
            logger.error("データが読み込まれていません")
            raise HTTPException(status_code=500, detail="データが読み込まれていません")
        
        # データを読み込む
        try:
            load_data_and_models(force_reload=False)
            logger.info("データ/モデルの読み込み完了")
        except Exception as e:
            logger.warning(f"データ/モデルの再読み込みに失敗しました（既存データを使用）: {e}")
            logger.warning(traceback.format_exc())
        
        # 罫線マスターデータを読み込む
        logger.info("罫線マスターデータを読み込み中...")
        try:
            keisen_master_current = load_keisen_master_by_type('current')
            logger.info("現罫線マスターデータの読み込み完了")
        except Exception as e:
            logger.error(f"現罫線マスターデータの読み込みに失敗: {e}")
            logger.error(traceback.format_exc())
            raise HTTPException(status_code=500, detail=f"現罫線マスターデータの読み込みに失敗: {str(e)}")
        
        try:
            keisen_master_new = load_keisen_master_by_type('new')
            logger.info("新罫線マスターデータの読み込み完了")
        except Exception as e:
            logger.error(f"新罫線マスターデータの読み込みに失敗: {e}")
            logger.error(traceback.format_exc())
            raise HTTPException(status_code=500, detail=f"新罫線マスターデータの読み込みに失敗: {str(e)}")
        
        # 前回・前々回の当選番号を取得（共通情報）
        previous_row = df[df['round_number'] == round_number - 1]
        previous_previous_row = df[df['round_number'] == round_number - 2]
        
        if len(previous_row) == 0:
            raise HTTPException(status_code=404, detail=f"前回の当選番号が見つかりません（回号: {round_number - 1}）")
        if len(previous_previous_row) == 0:
            raise HTTPException(status_code=404, detail=f"前々回の当選番号が見つかりません（回号: {round_number - 2}）")
        
        previous_n3 = str(previous_row['n3_winning'].iloc[0]).replace('.0', '').zfill(3)
        previous_n4 = str(previous_row['n4_winning'].iloc[0]).replace('.0', '').zfill(4)
        previous_previous_n3 = str(previous_previous_row['n3_winning'].iloc[0]).replace('.0', '').zfill(3)
        previous_previous_n4 = str(previous_previous_row['n4_winning'].iloc[0]).replace('.0', '').zfill(4)
        
        cubes = []
        
        # 予測出目を取得するヘルパー関数
        def get_source_list(keisen_master_dict: dict, target: str) -> List[int]:
            from chart_generator import extract_predicted_digits
            return extract_predicted_digits(df, keisen_master_dict, round_number, target)
        
        # 通常CUBE: 現罫線 × 4パターン（A1, A2, B1, B2）
        patterns = ['A1', 'A2', 'B1', 'B2']
        targets = ['n3', 'n4']
        
        logger.info("通常CUBE（現罫線）の生成を開始...")
        for target in targets:
            source_list = get_source_list(keisen_master_current, target)
            previous_winning = previous_n3 if target == 'n3' else previous_n4
            previous_previous_winning = previous_previous_n3 if target == 'n3' else previous_previous_n4
            
            for pattern in patterns:
                try:
                    logger.debug(f"現罫線 {target} {pattern} のCUBE生成中...")
                    grid, rows, cols = generate_chart(
                        df, keisen_master_current, round_number, pattern, target
                    )
                    # templistを取得（通常CUBEと同じ定義）
                    nums = apply_pattern_expansion(source_list, pattern)
                    _, temp_list = build_main_rows(nums)
                    cubes.append({
                        'id': f'current_normal_{target}_{pattern}',
                        'keisen_type': 'current',
                        'cube_type': 'normal',
                        'target': target,
                        'pattern': pattern,
                        'grid': grid,
                        'rows': rows,
                        'cols': cols,
                        'previous_winning': previous_winning,
                        'previous_previous_winning': previous_previous_winning,
                        'predicted_digits': temp_list
                    })
                    logger.debug(f"現罫線 {target} {pattern} のCUBE生成完了")
                except Exception as e:
                    logger.warning(f"現罫線 {target} {pattern} のCUBE生成に失敗: {e}")
                    logger.warning(traceback.format_exc())
        
        # 通常CUBE: 新罫線 × 4パターン（A1, A2, B1, B2）
        logger.info("通常CUBE（新罫線）の生成を開始...")
        for target in targets:
            source_list = get_source_list(keisen_master_new, target)
            previous_winning = previous_n3 if target == 'n3' else previous_n4
            previous_previous_winning = previous_previous_n3 if target == 'n3' else previous_previous_n4
            
            for pattern in patterns:
                try:
                    logger.debug(f"新罫線 {target} {pattern} のCUBE生成中...")
                    grid, rows, cols = generate_chart(
                        df, keisen_master_new, round_number, pattern, target
                    )
                    # templistを取得（通常CUBEと同じ定義）
                    nums = apply_pattern_expansion(source_list, pattern)
                    _, temp_list = build_main_rows(nums)
                    cubes.append({
                        'id': f'new_normal_{target}_{pattern}',
                        'keisen_type': 'new',
                        'cube_type': 'normal',
                        'target': target,
                        'pattern': pattern,
                        'grid': grid,
                        'rows': rows,
                        'cols': cols,
                        'previous_winning': previous_winning,
                        'previous_previous_winning': previous_previous_winning,
                        'predicted_digits': temp_list
                    })
                    logger.debug(f"新罫線 {target} {pattern} のCUBE生成完了")
                except Exception as e:
                    logger.warning(f"新罫線 {target} {pattern} のCUBE生成に失敗: {e}")
                    logger.warning(traceback.format_exc())
        
        # 極CUBE: 現罫線 × 1パターン（N3のみ）
        logger.info("極CUBE（現罫線）の生成を開始...")
        try:
            source_list = get_source_list(keisen_master_current, 'n3')
            # B1パターンでtemplist（nums）を作成
            nums = apply_pattern_expansion(source_list, 'B1')
            # templistを取得（通常CUBEと同じ定義）
            _, temp_list = build_main_rows(nums)
            grid, rows, cols = generate_extreme_cube(
                df, keisen_master_current, round_number
            )
            cubes.append({
                'id': 'current_extreme_n3',
                'keisen_type': 'current',
                'cube_type': 'extreme',
                'target': 'n3',
                'pattern': None,
                'grid': grid,
                'rows': rows,
                'cols': cols,
                'previous_winning': previous_n3,
                'previous_previous_winning': previous_previous_n3,
                'predicted_digits': temp_list
            })
            logger.info("極CUBE（現罫線）の生成完了")
        except Exception as e:
            logger.warning(f"現罫線 極CUBE の生成に失敗: {e}")
            logger.warning(traceback.format_exc())
        
        # 極CUBE: 新罫線 × 1パターン（N3のみ）
        logger.info("極CUBE（新罫線）の生成を開始...")
        try:
            source_list = get_source_list(keisen_master_new, 'n3')
            # B1パターンでtemplist（nums）を作成
            nums = apply_pattern_expansion(source_list, 'B1')
            # templistを取得（通常CUBEと同じ定義）
            _, temp_list = build_main_rows(nums)
            grid, rows, cols = generate_extreme_cube(
                df, keisen_master_new, round_number
            )
            cubes.append({
                'id': 'new_extreme_n3',
                'keisen_type': 'new',
                'cube_type': 'extreme',
                'target': 'n3',
                'pattern': None,
                'grid': grid,
                'rows': rows,
                'cols': cols,
                'previous_winning': previous_n3,
                'previous_previous_winning': previous_previous_n3,
                'predicted_digits': temp_list
            })
            logger.info("極CUBE（新罫線）の生成完了")
        except Exception as e:
            logger.warning(f"新罫線 極CUBE の生成に失敗: {e}")
            logger.warning(traceback.format_exc())
        
        logger.info(f"CUBE生成完了: {len(cubes)}個のCUBEを生成しました")
        
        return {
            'round_number': round_number,
            'cubes': cubes
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"CUBE生成中に予期しないエラーが発生しました: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"CUBE生成エラー: {str(e)}")

