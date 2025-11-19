#!/usr/bin/env python3
"""
LightGBMモデルの学習スクリプト

学習データを使用して、6つのLightGBMモデルを学習します。
Vercelデプロイ用に軽量化されたパラメータを使用します。
"""

import pandas as pd
import numpy as np
import pickle
from pathlib import Path
import warnings
import gc
warnings.filterwarnings('ignore')

# メモリ使用量監視（オプション）
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    print("注意: psutilがインストールされていません。メモリ使用量の監視はスキップされます。")

import lightgbm as lgb
from sklearn.metrics import (
    roc_auc_score,
    precision_score,
    recall_score,
    f1_score,
    classification_report,
    confusion_matrix
)

# プロジェクトルートのパスを設定
if '__file__' in globals():
    # scripts/tools/training/train_lightgbm_models.py から見て、プロジェクトルートは3階層上
    PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
else:
    PROJECT_ROOT = Path.cwd()
DATA_DIR = PROJECT_ROOT / 'data'
MODELS_DIR = DATA_DIR / 'models'

# 設定ファイルをインポート
import sys
sys.path.append(str(PROJECT_ROOT / 'core'))
from config import LGB_PARAMS, MODEL_VERSION

print(f"プロジェクトルート: {PROJECT_ROOT}")
print(f"データディレクトリ: {DATA_DIR}")
print(f"モデルディレクトリ: {MODELS_DIR}")
print(f"\nモデルバージョン: {MODEL_VERSION}")

# LightGBMハイパーパラメータ設定（設定ファイルから読み込み）
lgb_params = LGB_PARAMS.copy()

print("\nLightGBMハイパーパラメータ:")
for key, value in lgb_params.items():
    print(f"  {key}: {value}")


def calculate_top_k_accuracy(y_true, y_pred_proba, k=5):
    """Top-K Accuracyを計算する
    
    Args:
        y_true: 真のラベル（形状: (n_samples,)）
        y_pred_proba: 予測確率（形状: (n_samples,)）
        k: 上位K件
    
    Returns:
        Top-K Accuracy（0-1）
    """
    # 予測確率が高い順にインデックスをソート
    sorted_indices = np.argsort(y_pred_proba)[::-1]
    
    # 上位K件のインデックス
    top_k_indices = sorted_indices[:k]
    
    # 上位K件中に正解（ラベル=1）が含まれているか
    return 1.0 if np.any(y_true[top_k_indices] == 1) else 0.0


def print_memory_usage(stage=""):
    """メモリ使用量を表示（psutilが利用可能な場合）"""
    if PSUTIL_AVAILABLE:
        process = psutil.Process()
        memory_info = process.memory_info()
        memory_mb = memory_info.rss / (1024 * 1024)
        print(f"  メモリ使用量 ({stage}): {memory_mb:.1f} MB")


def evaluate_model(model, X_val, y_val, model_name=""):
    """モデルを評価する
    
    Args:
        model: 学習済みモデル
        X_val: 検証データの特徴量
        y_val: 検証データのラベル
        model_name: モデル名（ログ出力用）
    
    Returns:
        評価結果の辞書
    """
    # 予測
    y_pred = model.predict(X_val)
    y_pred_proba = model.predict_proba(X_val)[:, 1]
    
    # 評価指標を計算
    auc_roc = roc_auc_score(y_val, y_pred_proba)
    precision = precision_score(y_val, y_pred, zero_division=0)
    recall = recall_score(y_val, y_pred, zero_division=0)
    f1 = f1_score(y_val, y_pred, zero_division=0)
    
    # Top-K Accuracyを計算（K=5）
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


# 軸数字予測モデルの学習
axis_evaluation_results = []

for target in ['n3', 'n4']:
    data_file = MODELS_DIR / f'{target}_axis_data.pkl'
    
    if not data_file.exists():
        print(f"警告: データファイルが見つかりません: {data_file}")
        continue
    
    print(f"\n{'='*60}")
    print(f"N{target[1].upper()}軸数字予測モデルの学習を開始します")
    print(f"{'='*60}")
    
    # データを読み込む
    with open(data_file, 'rb') as f:
        data = pickle.load(f)
    
    X_train = data['X_train']
    X_val = data['X_val']
    y_train = data['y_train']
    y_val = data['y_val']
    
    # 特徴量キーを取得（存在する場合）
    feature_keys = data.get('feature_keys', [])
    
    print(f"\nデータ形状:")
    print(f"  学習データ: {X_train.shape}")
    print(f"  検証データ: {X_val.shape}")
    print(f"  ラベル分布（学習）: {np.bincount(y_train)}")
    print(f"  ラベル分布（検証）: {np.bincount(y_val)}")
    print_memory_usage("データ読み込み後")
    
    # モデルを学習させる
    model = lgb.LGBMClassifier(**lgb_params)
    
    print(f"\nモデルを学習中...")
    model.fit(
        X_train, y_train,
        eval_set=[(X_val, y_val)],
        callbacks=[lgb.early_stopping(50, verbose=False)]
    )
    print_memory_usage("モデル学習後")
    
    # モデルを評価する
    model_name = f"{target}_axis"
    results = evaluate_model(model, X_val, y_val, model_name)
    axis_evaluation_results.append(results)
    
    # モデルと特徴量キーを保存
    model_data = {
        'model': model,
        'feature_keys': feature_keys
    }
    
    # モデルファイル名（LightGBM版）
    model_filename = f'{target}_axis_lgb.pkl'
    model_path = MODELS_DIR / model_filename
    
    with open(model_path, 'wb') as f:
        pickle.dump(model_data, f)
    
    print(f"\nモデル学習完了: {model_name}")
    print(f"モデルファイル保存: {model_path}")
    
    # メモリを解放（重要: 次のモデル学習前にメモリをクリア）
    del data, X_train, X_val, y_train, y_val, model, model_data
    gc.collect()
    print_memory_usage("メモリ解放後")
    print(f"メモリを解放しました。次のモデル学習に進みます。")

print(f"\n{'='*60}")
print(f"軸数字予測モデルの学習が完了しました")
print(f"{'='*60}")


# 組み合わせ予測モデルの学習
comb_evaluation_results = []

for target in ['n3', 'n4']:
    for combo_type in ['box', 'straight']:
        data_file = MODELS_DIR / f'{target}_{combo_type}_comb_data.pkl'
        
        if not data_file.exists():
            print(f"警告: データファイルが見つかりません: {data_file}")
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
        
        # 特徴量キーを取得（存在する場合）
        feature_keys = data.get('feature_keys', [])
        
        print(f"\nデータ形状:")
        print(f"  学習データ: {X_train.shape}")
        print(f"  検証データ: {X_val.shape}")
        print(f"  ラベル分布（学習）: {np.bincount(y_train)}")
        print(f"  ラベル分布（検証）: {np.bincount(y_val)}")
        print_memory_usage("データ読み込み後")
        
        # ラベルが全て同じ場合はスキップ（学習不可能）
        if len(np.unique(y_train)) == 1:
            print(f"\n⚠️ 警告: ラベルが全て同じです（全て{np.unique(y_train)[0]}）。このモデルはスキップします。")
            # メモリを解放してスキップ
            del data, X_train, X_val, y_train, y_val
            gc.collect()
            continue
        
        # モデルを学習させる
        model = lgb.LGBMClassifier(**lgb_params)
        
        print(f"\nモデルを学習中...")
        model.fit(
            X_train, y_train,
            eval_set=[(X_val, y_val)],
            callbacks=[lgb.early_stopping(50, verbose=False)]
        )
        print_memory_usage("モデル学習後")
        
        # モデルを評価する
        model_name = f"{target}_{combo_type}_comb"
        results = evaluate_model(model, X_val, y_val, model_name)
        comb_evaluation_results.append(results)
        
        # モデルと特徴量キーを保存
        model_data = {
            'model': model,
            'feature_keys': feature_keys
        }
        
        # モデルファイル名（LightGBM版）
        model_filename = f'{target}_{combo_type}_comb_lgb.pkl'
        model_path = MODELS_DIR / model_filename
        
        with open(model_path, 'wb') as f:
            pickle.dump(model_data, f)
        
        print(f"\nモデル学習完了: {model_name}")
        print(f"モデルファイル保存: {model_path}")
        
        # メモリを解放（重要: 次のモデル学習前にメモリをクリア）
        del data, X_train, X_val, y_train, y_val, model, model_data
        gc.collect()
        print_memory_usage("メモリ解放後")
        print(f"メモリを解放しました。次のモデル学習に進みます。")

print(f"\n{'='*60}")
print(f"組み合わせ予測モデルの学習が完了しました")
print(f"{'='*60}")


# 評価結果のサマリー
print("\n" + "="*60)
print("全モデルの評価結果サマリー")
print("="*60)

all_results = axis_evaluation_results + comb_evaluation_results

if all_results:
    results_df = pd.DataFrame(all_results)
    print("\n評価指標の一覧:")
    print(results_df.to_string(index=False))
    
    print("\n平均評価指標:")
    print(f"  AUC-ROC: {results_df['auc_roc'].mean():.4f}")
    print(f"  Precision: {results_df['precision'].mean():.4f}")
    print(f"  Recall: {results_df['recall'].mean():.4f}")
    print(f"  F1-Score: {results_df['f1_score'].mean():.4f}")
    print(f"  Top-5 Accuracy: {results_df['top_5_accuracy'].mean():.4f}")
    
    # 評価結果を保存
    evaluation_path = MODELS_DIR / 'evaluation_results_lgb.pkl'
    with open(evaluation_path, 'wb') as f:
        pickle.dump(all_results, f)
    print(f"\n評価結果を保存しました: {evaluation_path}")
else:
    print("\n⚠️ 警告: 評価結果がありません。")

print("\n" + "="*60)
print("LightGBMモデルの学習が完了しました")
print("="*60)

