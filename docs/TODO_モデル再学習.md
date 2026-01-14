# 🔴 緊急TODO: 予測モデルの再学習

**作成日**: 2026-01-15  
**優先度**: 🔴 高（現在のモデルは99.3%間違ったデータで学習されている）  
**ステータス**: 未着手

---

## 📋 背景・問題の概要

### 発覚した問題

2026年1月15日に、過去データの重大な不具合を発見・修正しました：

- **問題**: 回号6847 (2025-10-31) 以前の6,824回号分のデータで、`n3_rehearsal/n4_rehearsal`列と`n3_winning/n4_winning`列が**逆**に格納されていた
- **修正内容**: リハーサル列と本番列をスワップして正しいデータに修正済み（GitHubにもプッシュ済み）
- **モデルへの影響**: 現在のモデルは2025年11月18日に生成されており、**学習データの99.3%が間違っていた**

### 影響の深刻度

- **間違ったデータ**: 6,824回号 (99.3%)
- **正しいデータ**: わずか50回号 (0.7%)
- **評価**: ❌ **極めて深刻** - モデルは本番番号ではなくリハーサル番号を学習していた

---

## 🎯 実施すべき作業

### Phase 1: 現状確認と準備（30分）

#### 1.1 データの最終確認

```bash
# 修正されたデータの確認
head -20 data/past_results.csv

# 6847付近のデータ確認
awk -F',' 'NR==1 || ($1 >= 6845 && $1 <= 6850)' data/past_results.csv
```

**期待される出力**:
```
6847,2025-10-31,4,806,7007,395,0137
```
- N3_rehearsal=806（本番番号ではなくリハーサル番号）
- N3_winning=395（リハーサル番号ではなく本番番号）

#### 1.2 現在のモデルファイルのバックアップ

```bash
# 日付付きバックアップディレクトリを作成
mkdir -p data/models_backup/before_retraining_20260115

# 既存モデルをバックアップ
cp -r data/models/combination_batches data/models_backup/before_retraining_20260115/
cp data/models/combination_checkpoint.pkl data/models_backup/before_retraining_20260115/

# バックアップ確認
ls -lh data/models_backup/before_retraining_20260115/
```

### Phase 2: モデル生成環境の調査と再構築（1-2時間）

#### 2.1 過去のモデル生成方法を調査

**確認すべきファイル・ディレクトリ**:
- `scripts/01_model_generation/` - モデル生成関連スクリプト
- `scripts/README.md` - モデル生成手順の記載
- Git履歴（2025年11月18日前後のコミット）

```bash
# 2025年11月18日前後のコミット履歴を確認
git log --since="2025-11-01" --until="2025-12-01" --oneline

# モデル生成関連のコミットを詳細確認
git log --grep="model" --since="2025-11-01" --until="2025-12-01" -p
```

#### 2.2 必要なスクリプト・ライブラリの確認

以下のファイルが存在するか確認（存在しない場合はGit履歴から復元が必要）:

- [ ] `notebooks/run_03_feature_engineering_combination_only.py` - 特徴量生成
- [ ] `notebooks/run_05_model_training_combination.py` - モデル学習
- [ ] 依存ライブラリリスト（requirements.txt等）

```bash
# 削除されたファイルをGit履歴から検索
git log --all --full-history --oneline -- '*feature_engineering*.py'
git log --all --full-history --oneline -- '*model_training*.py'

# 見つかったら復元
git checkout <commit-hash> -- <file-path>
```

#### 2.3 Python環境の準備

```bash
# 仮想環境の作成
python3 -m venv venv_model_training
source venv_model_training/bin/activate

# 必要なライブラリのインストール（要確認）
pip install pandas numpy scikit-learn joblib
# その他、モデル生成に必要なライブラリを追加
```

### Phase 3: モデルの再学習（数時間〜1日）

#### 3.1 特徴量エンジニアリング

```bash
# 特徴量生成スクリプトを実行
python notebooks/run_03_feature_engineering_combination_only.py

# 進捗モニタリング（別ターミナル）
bash scripts/01_model_generation/monitoring/monitor_combination_engineering.sh
```

#### 3.2 モデル学習

```bash
# モデル学習スクリプトを実行
python notebooks/run_05_model_training_combination.py

# 学習状況の確認
ls -lht data/models/combination_batches/*.pkl | head -10
```

### Phase 4: モデルの検証とデプロイ（30分〜1時間）

#### 4.1 ローカルでの動作確認

```bash
# テスト予測を実行（最新の回号で）
# api/py/combination.py を使用してローカルテスト
python -c "
import sys
sys.path.insert(0, 'core')
from pathlib import Path
# ... テストコード ...
"
```

#### 4.2 GitHubへのコミット

```bash
# 新しいモデルファイルをステージング
git add data/models/combination_batches/*.pkl
git add data/models/combination_checkpoint.pkl

# コミット
git commit -m "feat: 正しいデータで予測モデルを再学習

- 回号6847以前のデータ修正後、正しい本番当選番号で再学習
- 旧モデル（99.3%間違ったデータで学習）を新モデルで置き換え
- 学習日: $(date +%Y-%m-%d)
- 学習データ: 6,874回号（全て正しいデータ）"

# プッシュ
git push origin main
```

#### 4.3 Vercelでの自動デプロイ確認

- [ ] Vercelダッシュボードでデプロイ状況を確認
- [ ] デプロイ完了後、本番環境で予測をテスト
- [ ] 予測結果が正常に返ってくることを確認

### Phase 5: モニタリングと検証（継続的）

#### 5.1 予測精度のモニタリング

```bash
# 精度確認スクリプトを定期実行
python scripts/test_model_accuracy.py
```

#### 5.2 実際の当選番号との比較

- 新しいモデルの予測結果を記録
- 実際の当選番号と比較
- 精度の改善を確認

---

## 📁 関連ファイル

### 今回の修正で作成・更新されたファイル

- ✅ `data/past_results.csv` - リハーサル/本番列を修正（GitHubプッシュ済み）
- ✅ `scripts/fix_rehearsal_winning_swap.py` - データ修正スクリプト
- ✅ `scripts/test_model_accuracy.py` - モデル精度確認スクリプト
- ✅ `data/past_results_before_swap_20260115_010223.csv` - 修正前のバックアップ

### モデル関連ファイル（要確認）

- ❓ `notebooks/run_03_feature_engineering_combination_only.py` - 存在確認が必要
- ❓ `notebooks/run_05_model_training_combination.py` - 存在確認が必要
- 📁 `data/models/combination_batches/` - 現在のモデル（2025-11-18生成）
- 📁 `data/models_backup/` - バックアップ保存先

### 予測実行ファイル（参考）

- `api/py/combination.py` - Vercel Python関数（組み合わせ予測）
- `api/py/axis.py` - Vercel Python関数（軸数字予測）
- `core/model_loader.py` - モデル読み込みロジック
- `core/feature_extractor.py` - 特徴量抽出ロジック

---

## ⚠️ 注意事項

### データの取り扱い

- ✅ **修正済み**: GitHubの`data/past_results.csv`は既に正しいデータ
- ⚠️ **モデル未更新**: Vercelにデプロイされているモデルは古いまま
- 💡 **暫定対応**: モデル再学習までは統計ベースの予測のみを信頼する

### モデル生成時の考慮事項

1. **データの整合性確認**
   - 学習前に`data/past_results.csv`の6847前後のデータを再確認
   - NULLデータの除外処理が正しく動作するか確認

2. **計算リソース**
   - モデル学習には数時間〜1日かかる可能性
   - メモリ使用量に注意（大量のPickleファイル生成）

3. **バージョン管理**
   - 新しいモデルのメタデータを記録（学習日、データ範囲等）
   - 古いモデルは削除せずバックアップ保持

---

## 🔍 トラブルシューティング

### Q1: モデル生成スクリプトが見つからない

**A**: Git履歴から復元する

```bash
# 削除されたファイルを探す
git log --all --full-history --diff-filter=D --oneline -- '*model*.py'

# 特定のコミットからファイルを復元
git checkout <commit-hash> -- <file-path>
```

### Q2: メモリ不足エラーが発生

**A**: バッチサイズを小さくするか、段階的に処理

```python
# スクリプト内のバッチサイズを調整
BATCH_SIZE = 1000  # デフォルト値より小さく
```

### Q3: Vercelデプロイ時にモデルファイルが大きすぎる

**A**: `.vercelignore`で不要なモデルファイルを除外

```
# .vercelignore
data/models_backup/
*.pkl.old
```

---

## 📊 成功の指標

モデル再学習が成功したと判断できる基準：

- [ ] モデルファイルのタイムスタンプが更新されている
- [ ] `scripts/test_model_accuracy.py`の実行結果が「正しいデータ: 100%」
- [ ] ローカルでの予測テストが正常に動作
- [ ] Vercel本番環境での予測が正常に動作
- [ ] 予測結果が以前と大きく変わっている（data/past_results.csvの修正が反映されている）

---

## 💡 次回作業開始時のチェックリスト

```bash
# 1. このドキュメントを開く
cat docs/TODO_モデル再学習.md

# 2. データが正しく修正されているか確認
awk -F',' 'NR==1 || $1==6847' data/past_results.csv

# 3. 現在のモデルをバックアップ
mkdir -p data/models_backup/before_retraining_$(date +%Y%m%d)
cp -r data/models/combination_batches data/models_backup/before_retraining_$(date +%Y%m%d)/

# 4. Phase 2から作業開始
# → モデル生成スクリプトの調査・復元
```

---

**最終更新**: 2026-01-15  
**次回確認事項**: モデル生成スクリプトの存在確認とGit履歴からの復元
