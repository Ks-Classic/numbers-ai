
import sys
from pathlib import Path

# Add core to path
sys.path.append(str(Path.cwd() / 'core'))

try:
    from model_loader import load_model_loader, ModelLoader
    print("Successfully imported model_loader")
except ImportError as e:
    print(f"Failed to import model_loader: {e}")
    sys.exit(1)

try:
    import xgboost
    print("Warning: xgboost is still importable (not critical if not used)")
except ImportError:
    print("Confirmed: xgboost is not importable")

try:
    import lightgbm
    print("Successfully imported lightgbm")
except ImportError as e:
    print(f"Failed to import lightgbm: {e}")
    sys.exit(1)

# Try to initialize model loader
try:
    # Use default path
    loader = load_model_loader()
    print("Successfully initialized ModelLoader")
    
    # Check loaded models
    models = loader.get_available_models()
    print(f"Loaded models: {models}")
    
    expected_models = [
        'n3_axis', 'n4_axis', 
        'n3_box_comb', 'n3_straight_comb', 
        'n4_box_comb', 'n4_straight_comb'
    ]
    
    missing = [m for m in expected_models if m not in models]
    if missing:
        print(f"Warning: Missing models: {missing}")
    else:
        print("All expected models loaded")
        
except Exception as e:
    print(f"Error initializing ModelLoader: {e}")
    sys.exit(1)
