"""
学習設定ファイル

学習範囲やモデルパラメータを一元管理します。
異なる学習範囲での実験を管理しやすくするため、設定ファイルで切り替え可能にします。
"""

# 学習データ設定
# 選択肢:
#   1. TRAIN_SIZE = 1000（直近1000回分、5849〜6849）
#   2. TRAIN_SIZE = None かつ MIN_ROUND = 4801（4801回まで、約2049回分、リハーサル数字がある範囲すべて）
TRAIN_SIZE = None  # 学習に使用する回数（直近N回分）。Noneの場合はMIN_ROUNDから最新回まで
BASE_ROUND_AUTO = True  # True: 最新回号を自動取得、False: BASE_ROUNDを手動指定
BASE_ROUND = None  # BASE_ROUND_AUTOがFalseの場合に使用
MIN_ROUND = 4801  # 最小回号（TRAIN_SIZE=Noneの場合に使用）。4801を指定すると4801回から最新回まで

# データファイル名
if TRAIN_SIZE is not None:
    TRAIN_DATA_CSV = f'train_data_{TRAIN_SIZE}.csv'
elif MIN_ROUND is not None:
    TRAIN_DATA_CSV = f'train_data_from_{MIN_ROUND}.csv'
else:
    TRAIN_DATA_CSV = 'train_data.csv'

# モデル保存設定
MODELS_DIR = 'data/models'
# モデルバージョン（学習範囲に基づく）
if TRAIN_SIZE is not None:
    MODEL_VERSION = f'v{TRAIN_SIZE}'
elif MIN_ROUND is not None:
    MODEL_VERSION = f'v_from_{MIN_ROUND}'
else:
    MODEL_VERSION = 'v_all'

# XGBoostハイパーパラメータ
XGB_PARAMS = {
    'objective': 'binary:logistic',
    'eval_metric': 'logloss',
    'max_depth': 6,
    'learning_rate': 0.05,
    'n_estimators': 500,
    'subsample': 0.8,
    'colsample_bytree': 0.8,
    'min_child_weight': 3,
    'gamma': 0.1,
    'reg_alpha': 0.1,
    'reg_lambda': 1.0,
    'random_state': 42,
    'n_jobs': -1
}

# 特徴量設定
MAX_COMBINATIONS_PER_DIGIT = 20  # 組み合わせ予測モデルの各数字ごとの最大組み合わせ数

# データ分割設定
TRAIN_VAL_SPLIT = 0.8  # 学習データと検証データの分割比率（80%が学習データ）

# 出力設定
VERBOSE = True  # 詳細なログ出力

