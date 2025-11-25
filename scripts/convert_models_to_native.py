"""
LightGBMモデルをネイティブ形式に変換

scikit-learnのpickle形式からLightGBMのネイティブ形式（.txt）に変換します。
これにより、scikit-learn依存を排除できます。
"""

import pickle
from pathlib import Path
import lightgbm as lgb

def convert_models():
    """モデルを変換"""
    models_dir = Path(__file__).parent.parent / 'data' / 'models'
    
    model_files = [
        'n3_axis_lgb.pkl',
        'n4_axis_lgb.pkl',
        'n3_box_comb_lgb.pkl',
        'n3_straight_comb_lgb.pkl',
        'n4_box_comb_lgb.pkl',
        'n4_straight_comb_lgb.pkl'
    ]
    
    for filename in model_files:
        pkl_path = models_dir / filename
        txt_path = models_dir / filename.replace('.pkl', '.txt')
        
        if not pkl_path.exists():
            print(f"スキップ: {filename} (ファイルが存在しません)")
            continue
        
        try:
            # pickleファイルを読み込む
            with open(pkl_path, 'rb') as f:
                model_data = pickle.load(f)
            
            # モデルを取得
            if isinstance(model_data, dict):
                model = model_data.get('model', model_data)
                feature_keys = model_data.get('feature_keys', [])
            else:
                model = model_data
                feature_keys = []
            
            # LightGBMモデルからBoosterを取得
            if hasattr(model, 'booster_'):
                booster = model.booster_
            elif isinstance(model, lgb.Booster):
                booster = model
            else:
                print(f"エラー: {filename} - 未知のモデル形式: {type(model)}")
                continue
            
            # ネイティブ形式で保存
            booster.save_model(str(txt_path))
            
            # 特徴量キーも保存（JSON形式）
            if feature_keys:
                import json
                keys_path = models_dir / filename.replace('.pkl', '_keys.json')
                with open(keys_path, 'w') as f:
                    json.dump(feature_keys, f, indent=2)
                print(f"✓ {filename} -> {txt_path.name}, {keys_path.name}")
            else:
                print(f"✓ {filename} -> {txt_path.name}")
            
            # モデル情報を表示
            print(f"  特徴量数: {booster.num_feature()}")
            print(f"  木の数: {booster.num_trees()}")
            
        except Exception as e:
            print(f"エラー: {filename} - {e}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    convert_models()

