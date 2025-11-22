"""
モデル読み込みユーティリティ

学習済みモデルを読み込み、推論を行うためのユーティリティ関数を提供します。
"""

import pickle
from pathlib import Path
from typing import Optional, Dict, Literal, List, Union
import numpy as np
import lightgbm as lgb

Pattern = Literal['A1', 'A2', 'B1', 'B2']
Target = Literal['n3', 'n4']
ComboType = Literal['box', 'straight']


class ModelLoader:
    """モデル読み込みクラス"""
    
    def __init__(self, models_dir: Path):
        """初期化
        
        Args:
            models_dir: モデルファイルが保存されているディレクトリ
        """
        self.models_dir = Path(models_dir)
        self.models: Dict[str, lgb.LGBMClassifier] = {}
        self.feature_keys: Dict[str, List[str]] = {}  # モデルごとの特徴量キーリスト
        self.dimension_warnings_shown: Dict[str, bool] = {}  # 次元不一致警告を1回だけ表示するためのフラグ
        self._load_all_models()
    
    def _load_all_models(self) -> None:
        """すべてのモデルを読み込む"""
        # LightGBMモデルファイル名
        model_files = {
            'n3_axis': 'n3_axis_lgb.pkl',
            'n4_axis': 'n4_axis_lgb.pkl',
            'n3_box_comb': 'n3_box_comb_lgb.pkl',
            'n3_straight_comb': 'n3_straight_comb_lgb.pkl',
            'n4_box_comb': 'n4_box_comb_lgb.pkl',
            'n4_straight_comb': 'n4_straight_comb_lgb.pkl'
        }
        
        for model_name, filename in model_files.items():
            model_path = self.models_dir / filename
            if model_path.exists():
                try:
                    with open(model_path, 'rb') as f:
                        model_data = pickle.load(f)
                        
                    # モデルデータが辞書の場合は、モデルと特徴量キーを分離
                    if isinstance(model_data, dict):
                        self.models[model_name] = model_data.get('model', model_data)
                        self.feature_keys[model_name] = model_data.get('feature_keys', [])
                    else:
                        # 古い形式（モデルのみ）の場合
                        self.models[model_name] = model_data
                        self.feature_keys[model_name] = []
                    
                    print(f"モデル読み込み完了: {model_name} (LightGBM)")
                except Exception as e:
                    print(f"警告: モデル読み込みエラー ({model_name}): {e}")
            else:
                print(f"警告: モデルファイルが見つかりません: {model_path}")
    
    def load_model(self, model_name: str) -> Optional[lgb.LGBMClassifier]:
        """指定されたモデルを読み込む
        
        Args:
            model_name: モデル名（例: 'n3_axis', 'n3_box_comb'）
        
        Returns:
            モデルオブジェクト（存在しない場合はNone）
        """
        return self.models.get(model_name)
    
    def model_exists(self, model_name: str) -> bool:
        """モデルが存在するかチェック
        
        Args:
            model_name: モデル名
        
        Returns:
            モデルが存在する場合True
        """
        return model_name in self.models
    
    def align_features(
        self,
        model_name: str,
        features: Dict[str, float]
    ) -> np.ndarray:
        """特徴量をモデルが期待する形式に変換する（自動次元調整）
        
        Args:
            model_name: モデル名
            features: 特徴量辞書
        
        Returns:
            特徴量ベクトル（numpy配列）
        """
        expected_keys = self.feature_keys.get(model_name, [])
        
        if not expected_keys:
            # 特徴量キーが保存されていない場合（古いモデル形式）
            # 現在の特徴量のキーをソートして使用
            sorted_keys = sorted(features.keys())
            return np.array([features.get(key, 0.0) for key in sorted_keys])
        
        # 期待されるキーリストに基づいてベクトルを構築
        # 存在しないキーは0で埋める、余分なキーは無視
        feature_vector = np.array([
            features.get(key, 0.0) for key in expected_keys
        ])
        
        return feature_vector
    
    def predict_axis(self, target: Target, features: np.ndarray) -> np.ndarray:
        """軸数字予測を行う
        
        Args:
            target: 対象（'n3' または 'n4'）
            features: 特徴量ベクトル（形状: (n_samples, n_features)）
        
        Returns:
            予測確率（形状: (n_samples,)）
        """
        model_name = f"{target}_axis"
        model = self.load_model(model_name)
        
        if model is None:
            raise ValueError(f"モデルが見つかりません: {model_name}")
        
        # 次元チェックと自動調整
        expected_dim = model.n_features_in_
        actual_dim = features.shape[1] if len(features.shape) > 1 else len(features)
        
        if expected_dim != actual_dim:
            # 次元が一致しない場合は警告を出して調整（1回だけ）
            if not self.dimension_warnings_shown.get(model_name, False):
                print(f"警告: {model_name}の特徴量次元が不一致 (期待: {expected_dim}, 実際: {actual_dim})。自動調整します。")
                self.dimension_warnings_shown[model_name] = True
            
            if actual_dim < expected_dim:
                # 不足分を0で埋める
                padding = np.zeros((features.shape[0], expected_dim - actual_dim))
                features = np.hstack([features, padding])
            elif actual_dim > expected_dim:
                # 余分な次元を削除
                features = features[:, :expected_dim]
        
        return model.predict_proba(features)[:, 1]
    
    def predict_combination(
        self,
        target: Target,
        combo_type: ComboType,
        features: np.ndarray
    ) -> np.ndarray:
        """組み合わせ予測を行う
        
        Args:
            target: 対象（'n3' または 'n4'）
            combo_type: 組み合わせタイプ（'box' または 'straight'）
            features: 特徴量ベクトル（形状: (n_samples, n_features)）
        
        Returns:
            予測確率（形状: (n_samples,)）
        """
        model_name = f"{target}_{combo_type}_comb"
        model = self.load_model(model_name)
        
        if model is None:
            raise ValueError(f"モデルが見つかりません: {model_name}")
        
        # 次元チェックと自動調整
        expected_dim = model.n_features_in_
        actual_dim = features.shape[1] if len(features.shape) > 1 else len(features)
        
        if expected_dim != actual_dim:
            # 次元が一致しない場合は警告を出して調整（1回だけ）
            if not self.dimension_warnings_shown.get(model_name, False):
                print(f"警告: {model_name}の特徴量次元が不一致 (期待: {expected_dim}, 実際: {actual_dim})。自動調整します。")
                self.dimension_warnings_shown[model_name] = True
            
            if actual_dim < expected_dim:
                # 不足分を0で埋める
                padding = np.zeros((features.shape[0], expected_dim - actual_dim))
                features = np.hstack([features, padding])
            elif actual_dim > expected_dim:
                # 余分な次元を削除
                features = features[:, :expected_dim]
        
        return model.predict_proba(features)[:, 1]
    
    def predict_axis_from_dict(
        self,
        target: Target,
        features: Dict[str, float]
    ) -> float:
        """軸数字予測を行う（特徴量辞書から）
        
        Args:
            target: 対象（'n3' または 'n4'）
            features: 特徴量辞書
        
        Returns:
            予測確率（0-1）
        """
        model_name = f"{target}_axis"
        feature_vector = self.align_features(model_name, features)
        return self.predict_axis(target, feature_vector.reshape(1, -1))[0]
    
    def predict_combination_from_dict(
        self,
        target: Target,
        combo_type: ComboType,
        features: Dict[str, float]
    ) -> float:
        """組み合わせ予測を行う（特徴量辞書から）
        
        Args:
            target: 対象（'n3' または 'n4'）
            combo_type: 組み合わせタイプ（'box' または 'straight'）
            features: 特徴量辞書
        
        Returns:
            予測確率（0-1）
        """
        model_name = f"{target}_{combo_type}_comb"
        feature_vector = self.align_features(model_name, features)
        return self.predict_combination(target, combo_type, feature_vector.reshape(1, -1))[0]
    
    def get_available_models(self) -> list:
        """利用可能なモデルのリストを取得
        
        Returns:
            モデル名のリスト
        """
        return list(self.models.keys())


def load_model_loader(models_dir: Optional[Path] = None) -> ModelLoader:
    """モデルローダーを読み込む
    
    Args:
        models_dir: モデルディレクトリ（Noneの場合はデフォルトパスを使用）
    
    Returns:
        ModelLoaderインスタンス
    """
    if models_dir is None:
        # デフォルトパス: プロジェクトルート/data/models
        from pathlib import Path
        project_root = Path(__file__).parent.parent if '__file__' in globals() else Path.cwd()
        models_dir = project_root / 'data' / 'models'
    
    return ModelLoader(models_dir)


def check_models_exist(models_dir: Path) -> Dict[str, bool]:
    """必要なモデルファイルがすべて存在するかチェック
    
    Args:
        models_dir: モデルディレクトリ
    
    Returns:
        モデル名と存在フラグの辞書
    """
    required_models = [
        'n3_axis_lgb.pkl',
        'n4_axis_lgb.pkl',
        'n3_box_comb_lgb.pkl',
        'n3_straight_comb_lgb.pkl',
        'n4_box_comb_lgb.pkl',
        'n4_straight_comb_lgb.pkl'
    ]
    
    results = {}
    for model_file in required_models:
        model_path = models_dir / model_file
        results[model_file] = model_path.exists()
    
    return results
