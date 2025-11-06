#!/usr/bin/env python3
"""
組み合わせ予測モデルの学習スクリプト

組み合わせ予測モデル（N3/N4 × ボックス/ストレート）を学習します。
"""

import pandas as pd
import numpy as np
import pickle
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

import xgboost as xgb
from sklearn.metrics import (
    roc_auc_score,
    precision_score,
    recall_score,
    f1_score,
    classification_report,
    confusion_matrix
)

# プロジェクトルートのパスを設定
PROJECT_ROOT = Path(__file__).parent.parent if '__file__' in globals() else Path.cwd()
DATA_DIR = PROJECT_ROOT / 'data'
MODELS_DIR = DATA_DIR / 'models'

# 設定ファイルをインポート
import sys
sys.path.append(str(PROJECT_ROOT / 'notebooks'))
from config import XGB_PARAMS, MODEL_VERSION

print(f"プロジェクトルート: {PROJECT_ROOT}")
print(f"データディレクトリ: {DATA_DIR}")
print(f"モデルディレクトリ: {MODELS_DIR}")
print(f"\nモデルバージョン: {MODEL_VERSION}")

# XGBoostハイパーパラメータ設定
xgb_params = XGB_PARAMS.copy()

print("\nXGBoostハイパーパラメータ:")
for key, value in xgb_params.items():
    print(f"  {key}: {value}")

# 評価関数
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

# 組み合わせ予測モデルの学習
comb_models = {}
comb_evaluation_results = []

for target in ['n3', 'n4']:
    for combo_type in ['box', 'straight']:
        data_file = MODELS_DIR / f'{target}_{combo_type}_comb_data.pkl'
        
        if not data_file.exists():
            print(f"\n警告: データファイルが見つかりません: {data_file}")
            continue
        
        print(f"\n{'='*60}")
        print(f"N{target[1].upper()} {combo_type.upper()}組み合わせ予測モデルの学習を開始します")
        print(f"{'='*60}")
        
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
        
        # ラベルが全て0または全て1の場合はスキップ
        if len(np.bincount(y_train)) == 1 or len(np.bincount(y_val)) == 1:
            print(f"\n警告: ラベルが全て同じ値のため、{model_name}モデルの学習をスキップします")
            print(f"  学習データのラベル分布: {np.bincount(y_train)}")
            print(f"  検証データのラベル分布: {np.bincount(y_val)}")
            continue
        
        # 正例が少ない場合はscale_pos_weightを調整
        pos_count = np.sum(y_train == 1)
        neg_count = np.sum(y_train == 0)
        if pos_count > 0 and neg_count > 0:
            scale_pos_weight = neg_count / pos_count
            print(f"  正例/負例の比率: {pos_count}/{neg_count} (scale_pos_weight={scale_pos_weight:.2f})")
        else:
            scale_pos_weight = 1.0
        
        # モデルを学習させる
        model_params = xgb_params.copy()
        if scale_pos_weight > 1.0:
            model_params['scale_pos_weight'] = scale_pos_weight
        
        model = xgb.XGBClassifier(**model_params)
        
        print(f"\nモデルを学習中...")
        model.fit(
            X_train, y_train,
            eval_set=[(X_val, y_val)],
            verbose=False
        )
        
        # モデルを評価する
        model_name = f"{target}_{combo_type}_comb"
        results = evaluate_model(model, X_val, y_val, model_name)
        comb_evaluation_results.append(results)
        
        # モデルを保存
        comb_models[model_name] = model
        
        print(f"\nモデル学習完了: {model_name}")

print(f"\n{'='*60}")
print(f"組み合わせ予測モデルの学習が完了しました")
print(f"{'='*60}")

# モデル保存
if not MODELS_DIR.exists():
    MODELS_DIR.mkdir(parents=True, exist_ok=True)

print("\n組み合わせ予測モデルを保存中...")
for model_name, model in comb_models.items():
    model_file = MODELS_DIR / f"{model_name}.pkl"
    with open(model_file, 'wb') as f:
        pickle.dump(model, f)
    print(f"  保存完了: {model_file}")

# 評価結果も保存
eval_results_file = MODELS_DIR / 'evaluation_results_combination.pkl'
with open(eval_results_file, 'wb') as f:
    pickle.dump({
        'combination_results': comb_evaluation_results,
        'model_version': MODEL_VERSION
    }, f)
print(f"\n評価結果を保存しました: {eval_results_file}")

print(f"\n✅ すべての組み合わせ予測モデルを保存しました: {MODELS_DIR}")

# 評価結果のサマリー
print("\n" + "="*60)
print("評価結果サマリー")
print("="*60)

if comb_evaluation_results:
    results_df = pd.DataFrame(comb_evaluation_results)
    print("\n評価指標の一覧:")
    print(results_df.to_string(index=False))
    
    print("\n各評価指標の平均値:")
    print(f"  AUC-ROC: {results_df['auc_roc'].mean():.4f}")
    print(f"  Precision: {results_df['precision'].mean():.4f}")
    print(f"  Recall: {results_df['recall'].mean():.4f}")
    print(f"  F1-Score: {results_df['f1_score'].mean():.4f}")
    print(f"  Top-5 Accuracy: {results_df['top_5_accuracy'].mean():.4f}")
    
    # 目標値との比較
    print("\n目標値との比較:")
    print(f"  AUC-ROC目標: 0.55以上")
    for _, row in results_df.iterrows():
        status = "✅" if row['auc_roc'] >= 0.55 else "❌"
        print(f"    {row['model_name']}: {row['auc_roc']:.4f} {status}")
else:
    print("\n警告: 学習されたモデルがありません")

