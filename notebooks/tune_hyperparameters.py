#!/usr/bin/env python3
"""
ハイパーパラメータチューニングスクリプト

XGBoostモデルのハイパーパラメータを最適化します。
目標: AUC-ROCを0.55-0.60に改善
"""

import pickle
import json
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')

import xgboost as xgb
from sklearn.model_selection import RandomizedSearchCV
from sklearn.metrics import (
    roc_auc_score,
    precision_score,
    recall_score,
    f1_score,
    make_scorer
)

# プロジェクトルートのパスを設定
try:
    PROJECT_ROOT = Path(__file__).resolve().parent.parent
except NameError:
    PROJECT_ROOT = Path.cwd().parent if Path.cwd().name == 'notebooks' else Path.cwd()

DATA_DIR = PROJECT_ROOT / 'data'
MODELS_DIR = DATA_DIR / 'models'
RESULTS_DIR = PROJECT_ROOT / 'docs' / 'report'

# 出力ディレクトリを作成
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# 設定ファイルをインポート
import sys
sys.path.append(str(PROJECT_ROOT / 'notebooks'))
from config import XGB_PARAMS, MODEL_VERSION


def calculate_top_k_accuracy(y_true, y_pred_proba, k=5):
    """Top-K Accuracyを計算する"""
    sorted_indices = np.argsort(y_pred_proba)[::-1]
    top_k_indices = sorted_indices[:k]
    return 1.0 if np.any(y_true[top_k_indices] == 1) else 0.0


def evaluate_model(model, X_val, y_val, model_name=""):
    """モデルを評価する"""
    y_pred = model.predict(X_val)
    y_pred_proba = model.predict_proba(X_val)[:, 1]
    
    auc_roc = roc_auc_score(y_val, y_pred_proba)
    precision = precision_score(y_val, y_pred, zero_division=0)
    recall = recall_score(y_val, y_pred, zero_division=0)
    f1 = f1_score(y_val, y_pred, zero_division=0)
    top_k_acc = calculate_top_k_accuracy(y_val, y_pred_proba, k=5)
    
    results = {
        'model_name': model_name,
        'auc_roc': auc_roc,
        'precision': precision,
        'recall': recall,
        'f1_score': f1,
        'top_5_accuracy': top_k_acc
    }
    
    print(f"\n=== {model_name} の評価結果 ===")
    print(f"AUC-ROC: {auc_roc:.4f}")
    print(f"Precision: {precision:.4f}")
    print(f"Recall: {recall:.4f}")
    print(f"F1-Score: {f1:.4f}")
    print(f"Top-5 Accuracy: {top_k_acc:.4f}")
    
    return results


def tune_hyperparameters(
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_val: np.ndarray,
    y_val: np.ndarray,
    base_params: Dict,
    n_iter: int = 50,
    cv: int = 3,
    n_jobs: int = -1
) -> Tuple[Dict, Dict]:
    """ハイパーパラメータをチューニングする
    
    Args:
        X_train: 学習データの特徴量
        y_train: 学習データのラベル
        X_val: 検証データの特徴量
        y_val: 検証データのラベル
        base_params: ベースパラメータ
        n_iter: ランダムサーチの試行回数
        cv: クロスバリデーションの分割数
        n_jobs: 並列実行数
    
    Returns:
        (最適パラメータ, チューニング結果)
    """
    # パラメータ空間の定義
    param_distributions = {
        'max_depth': [4, 5, 6, 7, 8],
        'learning_rate': [0.01, 0.05, 0.1],
        'n_estimators': [300, 500, 700],
        'subsample': [0.7, 0.8, 0.9],
        'colsample_bytree': [0.7, 0.8, 0.9],
        'reg_alpha': [0.01, 0.1, 1.0],
        'reg_lambda': [0.1, 1.0, 10.0]
    }
    
    # ベースパラメータから変更しないパラメータを設定
    fixed_params = {
        'objective': base_params.get('objective', 'binary:logistic'),
        'eval_metric': base_params.get('eval_metric', 'logloss'),
        'min_child_weight': base_params.get('min_child_weight', 3),
        'gamma': base_params.get('gamma', 0.1),
        'random_state': base_params.get('random_state', 42),
        'n_jobs': n_jobs
    }
    
    # XGBoostモデルを作成
    base_model = xgb.XGBClassifier(**fixed_params)
    
    # AUC-ROCを最大化するスコアラーを作成
    scorer = make_scorer(roc_auc_score, needs_proba=True)
    
    # 学習データと検証データを統合（クロスバリデーション用）
    X_all = np.vstack([X_train, X_val])
    y_all = np.hstack([y_train, y_val])
    
    print(f"\n{'='*60}")
    print(f"ハイパーパラメータチューニングを開始します")
    print(f"{'='*60}")
    print(f"パラメータ空間: {len(param_distributions)}次元")
    print(f"試行回数: {n_iter}")
    print(f"クロスバリデーション: {cv}-fold")
    print(f"データサイズ: {X_all.shape}")
    
    # RandomizedSearchCVを実行
    random_search = RandomizedSearchCV(
        estimator=base_model,
        param_distributions=param_distributions,
        n_iter=n_iter,
        cv=cv,
        scoring=scorer,
        n_jobs=n_jobs,
        random_state=42,
        verbose=1,
        return_train_score=True
    )
    
    random_search.fit(X_all, y_all)
    
    # 最適パラメータを取得
    best_params = random_search.best_params_.copy()
    best_params.update(fixed_params)
    
    # チューニング結果を整理
    tuning_results = {
        'best_score': random_search.best_score_,
        'best_params': best_params,
        'cv_results': {
            'mean_test_score': random_search.cv_results_['mean_test_score'].tolist(),
            'std_test_score': random_search.cv_results_['std_test_score'].tolist(),
            'params': random_search.cv_results_['params']
        }
    }
    
    print(f"\n{'='*60}")
    print(f"チューニング完了")
    print(f"{'='*60}")
    print(f"最適スコア (CV): {random_search.best_score_:.4f}")
    print(f"\n最適パラメータ:")
    for key, value in best_params.items():
        if key not in fixed_params:
            print(f"  {key}: {value}")
    
    return best_params, tuning_results


def main():
    """メイン関数"""
    print("="*80)
    print("ハイパーパラメータチューニングスクリプト")
    print("="*80)
    print(f"モデルバージョン: {MODEL_VERSION}")
    print(f"目標: AUC-ROC 0.55-0.60")
    
    all_results = {
        'model_version': MODEL_VERSION,
        'tuning_results': {},
        'final_evaluation': {}
    }
    
    # 特徴量数を確認（新規特徴量を含むかどうかを判定）
    feature_count = None
    for target in ['n3', 'n4']:
        data_file = MODELS_DIR / f'{target}_axis_data.pkl'
        if data_file.exists():
            with open(data_file, 'rb') as f:
                data = pickle.load(f)
            feature_count = data['X_train'].shape[1]
            break
    
    # N3とN4の軸数字予測モデルをチューニング
    for target in ['n3', 'n4']:
        print(f"\n{'='*80}")
        print(f"モデル: {target}_axis")
        print(f"{'='*80}")
        
        data_file = MODELS_DIR / f'{target}_axis_data.pkl'
        
        if not data_file.exists():
            print(f"警告: データファイルが見つかりません: {data_file}")
            continue
        
        # データを読み込む
        with open(data_file, 'rb') as f:
            data = pickle.load(f)
        
        X_train = data['X_train']
        X_val = data['X_val']
        y_train = data['y_train']
        y_val = data['y_val']
        feature_keys = data.get('feature_keys', [])  # 特徴量キーを取得
        
        print(f"\nデータ形状:")
        print(f"  学習データ: {X_train.shape}")
        print(f"  検証データ: {X_val.shape}")
        print(f"  ラベル分布（学習）: {np.bincount(y_train)}")
        print(f"  ラベル分布（検証）: {np.bincount(y_val)}")
        
        # 現在のパラメータでベースライン評価
        print(f"\n{'='*60}")
        print(f"ベースラインモデルの評価（現在のパラメータ）")
        print(f"{'='*60}")
        baseline_model = xgb.XGBClassifier(**XGB_PARAMS)
        baseline_model.fit(X_train, y_train)
        baseline_results = evaluate_model(baseline_model, X_val, y_val, f"{target}_axis_baseline")
        
        # ハイパーパラメータチューニング
        best_params, tuning_results = tune_hyperparameters(
            X_train, y_train, X_val, y_val,
            base_params=XGB_PARAMS,
            n_iter=50,  # 試行回数
            cv=3,  # 3-foldクロスバリデーション
            n_jobs=-1
        )
        
        # 最適パラメータで再学習と評価
        print(f"\n{'='*60}")
        print(f"最適パラメータでの再学習と評価")
        print(f"{'='*60}")
        best_model = xgb.XGBClassifier(**best_params)
        best_model.fit(X_train, y_train, eval_set=[(X_val, y_val)], verbose=False)
        best_results = evaluate_model(best_model, X_val, y_val, f"{target}_axis_tuned")
        
        # 改善度を計算
        improvement = {
            'auc_roc': best_results['auc_roc'] - baseline_results['auc_roc'],
            'precision': best_results['precision'] - baseline_results['precision'],
            'recall': best_results['recall'] - baseline_results['recall'],
            'f1_score': best_results['f1_score'] - baseline_results['f1_score'],
            'top_5_accuracy': best_results['top_5_accuracy'] - baseline_results['top_5_accuracy']
        }
        
        print(f"\n{'='*60}")
        print(f"改善結果")
        print(f"{'='*60}")
        print(f"AUC-ROC: {baseline_results['auc_roc']:.4f} → {best_results['auc_roc']:.4f} ({improvement['auc_roc']:+.4f})")
        print(f"Precision: {baseline_results['precision']:.4f} → {best_results['precision']:.4f} ({improvement['precision']:+.4f})")
        print(f"F1-Score: {baseline_results['f1_score']:.4f} → {best_results['f1_score']:.4f} ({improvement['f1_score']:+.4f})")
        print(f"Top-5 Accuracy: {baseline_results['top_5_accuracy']:.4f} → {best_results['top_5_accuracy']:.4f} ({improvement['top_5_accuracy']:+.4f})")
        
        # 結果を保存
        model_name = f"{target}_axis"
        all_results['tuning_results'][model_name] = {
            'baseline': baseline_results,
            'tuned': best_results,
            'improvement': improvement,
            'best_params': best_params,
            'tuning_details': tuning_results
        }
        
        # 最適パラメータで学習したモデルを保存
        model_file = MODELS_DIR / f"{model_name}_tuned.pkl"
        with open(model_file, 'wb') as f:
            pickle.dump({
                'model': best_model,
                'params': best_params,
                'feature_keys': data.get('feature_keys', []),
                'model_version': MODEL_VERSION,
                'tuning_date': pd.Timestamp.now().isoformat()
            }, f)
        print(f"\nチューニング済みモデルを保存しました: {model_file}")
    
    # 全体結果を保存（新規特徴量を含むものは別ファイル名）
    # 現在のデータが新規特徴量を含むかどうかを確認（72次元かどうか）
    if feature_count and feature_count >= 70:  # 新規特徴量を含む（72次元）
        model_version_suffix = f"{MODEL_VERSION}_with_new_features"
    else:
        model_version_suffix = MODEL_VERSION
    
    results_file = RESULTS_DIR / f'hyperparameter_tuning_results_{model_version_suffix}.json'
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2, default=str)
    print(f"\nチューニング結果を保存しました: {results_file}")
    
    # サマリーを表示
    print(f"\n{'='*80}")
    print(f"最終サマリー")
    print(f"{'='*80}")
    for model_name, results in all_results['tuning_results'].items():
        baseline = results['baseline']
        tuned = results['tuned']
        improvement = results['improvement']
        
        print(f"\n{model_name}:")
        print(f"  AUC-ROC: {baseline['auc_roc']:.4f} → {tuned['auc_roc']:.4f} ({improvement['auc_roc']:+.4f})")
        print(f"  Top-5 Accuracy: {baseline['top_5_accuracy']:.4f} → {tuned['top_5_accuracy']:.4f} ({improvement['top_5_accuracy']:+.4f})")
    
    print(f"\n{'='*80}")
    print(f"チューニング完了")
    print(f"{'='*80}")


if __name__ == '__main__':
    main()

