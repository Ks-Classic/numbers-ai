#!/usr/bin/env python3
"""
LightGBMモデルをONNX形式に変換するスクリプト
"""

import pickle
import json
import sys
from pathlib import Path
import numpy as np

try:
    import onnxmltools
    from onnxmltools.convert.common.data_types import FloatTensorType
    import onnxruntime as ort
except ImportError as e:
    print(f"Error: Required libraries not installed")
    print(f"  pip install onnxmltools skl2onnx onnxruntime lightgbm")
    sys.exit(1)

PROJECT_ROOT = Path(__file__).parent.parent
MODELS_DIR = PROJECT_ROOT / 'data' / 'models'

MODEL_FILES = {
    'n3_axis': 'n3_axis_lgb.pkl',
    'n4_axis': 'n4_axis_lgb.pkl',
    'n3_box_comb': 'n3_box_comb_lgb.pkl',
    'n3_straight_comb': 'n3_straight_comb_lgb.pkl',
    'n4_box_comb': 'n4_box_comb_lgb.pkl',
    'n4_straight_comb': 'n4_straight_comb_lgb.pkl',
}

def load_lightgbm_model(model_path: Path):
    with open(model_path, 'rb') as f:
        model_data = pickle.load(f)
    
    if isinstance(model_data, dict):
        model = model_data.get('model', model_data)
        feature_keys = model_data.get('feature_keys', [])
    else:
        model = model_data
        feature_keys = []
    
    try:
        n_features = model.n_features_in_
    except AttributeError:
        n_features = model.num_feature()
    
    return model, feature_keys, n_features


def convert_model(model_name: str, input_filename: str) -> bool:
    input_path = MODELS_DIR / input_filename
    output_path = MODELS_DIR / f'{model_name}.onnx'
    
    if not input_path.exists():
        print(f"  Warning: {input_path} not found, skipping")
        return False
    
    try:
        model, feature_keys, n_features = load_lightgbm_model(input_path)
        print(f"  Features: {n_features}")
        
        # onnxmltoolsのFloatTensorTypeを使用
        initial_type = [('float_input', FloatTensorType([None, n_features]))]
        onnx_model = onnxmltools.convert_lightgbm(
            model,
            initial_types=initial_type,
            target_opset=12
        )
        
        with open(output_path, 'wb') as f:
            f.write(onnx_model.SerializeToString())
        
        size_kb = output_path.stat().st_size / 1024
        print(f"  Output: {output_path.name} ({size_kb:.1f} KB)")
        
        return True
        
    except Exception as e:
        print(f"  Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def verify_model(model_name: str, n_features: int) -> bool:
    """変換後モデルの検証"""
    onnx_path = MODELS_DIR / f'{model_name}.onnx'
    pkl_path = MODELS_DIR / f'{model_name}_lgb.pkl'
    
    if not onnx_path.exists() or not pkl_path.exists():
        return False
    
    try:
        session = ort.InferenceSession(str(onnx_path))
        test_input = np.random.randn(1, n_features).astype(np.float32)
        input_name = session.get_inputs()[0].name
        onnx_output = session.run(None, {input_name: test_input})
        
        model, _, _ = load_lightgbm_model(pkl_path)
        lgb_output = model.predict_proba(test_input)
        
        if len(onnx_output) > 1:
            onnx_proba = onnx_output[1]
        else:
            onnx_proba = onnx_output[0]
        
        max_diff = np.max(np.abs(onnx_proba - lgb_output))
        print(f"  Verify: max diff = {max_diff:.2e}")
        
        return max_diff < 1e-5
        
    except Exception as e:
        print(f"  Verify error: {e}")
        return False


def save_feature_keys():
    feature_keys_all = {}
    
    for model_name, filename in MODEL_FILES.items():
        pkl_path = MODELS_DIR / filename
        if pkl_path.exists():
            _, feature_keys, n_features = load_lightgbm_model(pkl_path)
            feature_keys_all[model_name] = {
                'feature_keys': feature_keys,
                'n_features': n_features
            }
    
    output_path = MODELS_DIR / 'feature_keys.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(feature_keys_all, f, ensure_ascii=False, indent=2)
    
    print(f"\nFeature keys saved: {output_path}")


def main():
    print("=" * 60)
    print("LightGBM -> ONNX Conversion")
    print("=" * 60)
    
    if not MODELS_DIR.exists():
        print(f"Error: Models directory not found: {MODELS_DIR}")
        sys.exit(1)
    
    success_count = 0
    total_count = len(MODEL_FILES)
    converted_models = []
    
    for model_name, filename in MODEL_FILES.items():
        print(f"\nConverting: {model_name}")
        if convert_model(model_name, filename):
            success_count += 1
            converted_models.append(model_name)
    
    save_feature_keys()
    
    # 検証
    print("\n" + "-" * 60)
    print("Verification")
    print("-" * 60)
    for model_name in converted_models:
        pkl_path = MODELS_DIR / f'{model_name}_lgb.pkl'
        if pkl_path.exists():
            _, _, n_features = load_lightgbm_model(pkl_path)
            print(f"\nVerifying: {model_name}")
            verify_model(model_name, n_features)
    
    print("\n" + "=" * 60)
    print(f"Completed: {success_count}/{total_count} models")
    
    total_size = sum(
        (MODELS_DIR / f'{name}.onnx').stat().st_size
        for name in MODEL_FILES.keys()
        if (MODELS_DIR / f'{name}.onnx').exists()
    )
    print(f"Total size: {total_size / 1024 / 1024:.2f} MB")
    
    if total_size > 50 * 1024 * 1024:
        print("Warning: Exceeds Vercel 50MB limit")
    else:
        print("OK: Within Vercel 50MB limit")
    
    print("=" * 60)
    
    return success_count == total_count


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
