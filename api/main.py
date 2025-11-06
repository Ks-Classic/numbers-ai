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
sys.path.append(str(PROJECT_ROOT / 'notebooks'))

from model_loader import load_model_loader
from chart_generator import load_keisen_master, generate_chart
from feature_extractor import (
    extract_digit_features,
    extract_combination_features,
    add_pattern_id_features,
    features_to_vector,
    get_rehearsal_positions
)
import pandas as pd
import numpy as np

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
            'n3_axis': 'n3_axis.pkl',
            'n4_axis': 'n4_axis.pkl',
            'n3_box_comb': 'n3_box_comb.pkl',
            'n3_straight_comb': 'n3_straight_comb.pkl',
            'n4_box_comb': 'n4_box_comb.pkl',
            'n4_straight_comb': 'n4_straight_comb.pkl'
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
            
            # 各数字（0-9）の特徴量を抽出して予測
            digit_scores = []
            for digit in range(10):
                features = extract_digit_features(
                    grid, rows, cols, digit, rehearsal_positions
                )
                features = add_pattern_id_features(features, pattern)
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
        
        # 特徴量を抽出して予測
        combo_scores = []
        for combo in combinations[:request.max_combinations]:
            features = extract_combination_features(
                grid, rows, cols, combo, rehearsal_positions
            )
            features = add_pattern_id_features(features, request.best_pattern)
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

