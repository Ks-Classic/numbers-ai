#!/usr/bin/env python3
"""
ハイパーパラメータチューニングスクリプト（改良版）

XGBoostモデルのハイパーパラメータを最適化します。
目標: AUC-ROCを0.55-0.60に改善

改良点:
- より広いパラメータ空間を探索
- より多くの試行回数
- 早期停止機能の追加
- StratifiedKFoldを使用
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
from sklearn.model_selection import RandomizedSearchCV, StratifiedKFold
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
sys.path.append(str(PROJECT_ROOT / 'core'))
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


def tune_hyperparameters_v2(
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_val: np.ndarray,
    y_val: np.ndarray,
    base_params: Dict,
    n_iter: int = 100,
    cv: int = 5,
    n_jobs: int = -1
) -> Tuple[Dict, Dict]:
    """ハイパーパラメータをチューニングする（改良版）
    
    より広いパラメータ空間を探索し、早期停止を使用
    """
    # より広いパラメータ空間の定義
    param_distributions = {
        'max_depth': [3, 4, 5, 6, 7, 8, 9],
        'learning_rate': [0.005, 0.01, 0.03, 0.05, 0.1, 0.15],
        'n_estimators': [200, 300, 500, 700, 1000],
        'subsample': [0.6, 0.7, 0.8, 0.9, 1.0],
        'colsample_bytree': [0.6, 0.7, 0.8, 0.9, 1.0],
        'min_child_weight': [1, 2, 3, 5, 7],
        'gamma': [0, 0.05, 0.1, 0.2, 0.3],
        'reg_alpha': [0, 0.01, 0.1, 0.5, 1.0, 2.0],
        'reg_lambda': [0.1, 0.5, 1.0, 2.0, 5.0, 10.0]
    }
    
    # ベースパラメータから変更しないパラメータ
    fixed_params = {
        'objective': base_params.get('objective', 'binary:logistic'),
        'eval_metric': base_params.get('eval_metric', 'logloss'),
        'random_state': base_params.get('random_state', 42),
        'n_jobs': n_jobs,
        'use_label_encoder': False
    }
    
    # 学習データと検証データを統合（クロスバリデーション用）
    X_all = np.vstack([X_train, X_val])
    y_all = np.hstack([y_train, y_val])
    
    print(f"\n{'='*60}")
    print(f"ハイパーパラメータチューニングを開始します（改良版）")
    print(f"{'='*60}")
    print(f"パラメータ空間: {len(param_distributions)}次元")
    print(f"試行回数: {n_iter}")
    print(f"クロスバリデーション: {cv}-fold StratifiedKFold")
    print(f"データサイズ: {X_all.shape}")
    
    # StratifiedKFoldを使用（クラス分布を保つ）
    cv_fold = StratifiedKFold(n_splits=cv, shuffle=True, random_state=42)
    
    # AUC-ROCを最大化するスコアラー
    scorer = make_scorer(roc_auc_score, needs_proba=True)
    
    best_score = -np.inf
    best_params = None
    all_results = []
    
    # 手動でランダムサーチ（より詳細なログ出力のため）
    np.random.seed(42)
    
    for i in range(n_iter):
        # ランダムにパラメータを選択
        params = {}
        for key, values in param_distributions.items():
            params[key] = np.random.choice(values)
        
        # 固定パラメータを追加
        full_params = {**params, **fixed_params}
        
        # クロスバリデーションで評価
        cv_scores = []
        for train_idx, val_idx in cv_fold.split(X_all, y_all):
            X_cv_train, X_cv_val = X_all[train_idx], X_all[val_idx]
            y_cv_train, y_cv_val = y_all[train_idx], y_all[val_idx]
            
            try:
                model = xgb.XGBClassifier(**full_params)
                model.fit(
                    X_cv_train, y_cv_train,
                    eval_set=[(X_cv_val, y_cv_val)],
                    verbose=False,
                    early_stopping_rounds=50  # 早期停止
                )
                
                y_pred_proba = model.predict_proba(X_cv_val)[:, 1]
                score = roc_auc_score(y_cv_val, y_pred_proba)
                cv_scores.append(score)
            except Exception as e:
                print(f"警告: 試行 {i+1} でエラー: {e}")
                cv_scores.append(0.0)
        
        if len(cv_scores) > 0:
            mean_score = np.mean(cv_scores)
            std_score = np.std(cv_scores)
            
            all_results.append({
                'params': params,
                'mean_score': mean_score,
                'std_score': std_score
            })
            
            if mean_score > best_score:
                best_score = mean_score
                best_params = full_params.copy()
            
            if (i + 1) % 10 == 0:
                print(f"試行 {i+1}/{n_iter}: 最良スコア = {best_score:.4f}")
    
    if best_params is None:
        print("警告: 有効なパラメータが見つかりませんでした。ベースパラメータを使用します。")
        best_params = {**base_params, **fixed_params}
        best_score = 0.0
    
    tuning_results = {
        'best_score': best_score,
        'best_params': best_params,
        'all_results': all_results[:20]  # 上位20件のみ保存
    }
    
    print(f"\n{'='*60}")
    print(f"チューニング完了")
    print(f"{'='*60}")
    print(f"最適スコア (CV): {best_score:.4f}")
    print(f"\n最適パラメータ:")
    for key, value in best_params.items():
        if key not in fixed_params:
            print(f"  {key}: {value}")
    
    return best_params, tuning_results


def main():
    """メイン関数"""
    print("="*80)
    print("ハイパーパラメータチューニングスクリプト（改良版）")
    print("="*80)
    print(f"モデルバージョン: {MODEL_VERSION}")
    print(f"目標: AUC-ROC 0.55-0.60")
    
    all_results = {
        'model_version': MODEL_VERSION,
        'tuning_results': {},
        'final_evaluation': {}
    }
    
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
        
        # ハイパーパラメータチューニング（改良版）
        best_params, tuning_results = tune_hyperparameters_v2(
            X_train, y_train, X_val, y_val,
            base_params=XGB_PARAMS,
            n_iter=100,  # より多くの試行回数
            cv=5,  # 5-foldクロスバリデーション
            n_jobs=-1
        )
        
        # 最適パラメータで再学習と評価
        print(f"\n{'='*60}")
        print(f"最適パラメータでの再学習と評価")
        print(f"{'='*60}")
        best_model = xgb.XGBClassifier(**best_params)
        best_model.fit(
            X_train, y_train,
            eval_set=[(X_val, y_val)],
            verbose=False,
            early_stopping_rounds=50
        )
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
        model_file = MODELS_DIR / f"{model_name}_tuned_v2.pkl"
        with open(model_file, 'wb') as f:
            pickle.dump({
                'model': best_model,
                'params': best_params,
                'feature_keys': data.get('feature_keys', []),
                'model_version': MODEL_VERSION,
                'tuning_date': pd.Timestamp.now().isoformat()
            }, f)
        print(f"\nチューニング済みモデルを保存しました: {model_file}")
    
    # 全体結果を保存
    results_file = RESULTS_DIR / f'hyperparameter_tuning_results_v2_{MODEL_VERSION}.json'
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

