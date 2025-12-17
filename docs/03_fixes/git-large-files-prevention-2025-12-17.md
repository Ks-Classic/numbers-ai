# Git巨大ファイル防止ルール

**作成日**: 2025-12-17  
**問題**: Vercelデプロイが5分以上かかる  
**原因**: Git履歴に482MBの巨大ファイルが存在していた

## 実施した対策

### 1. Git履歴のクリーンアップ

`git-filter-repo`を使用して以下を履歴から完全削除：

| 削除対象 | 理由 |
|---------|------|
| `data/models/*_data.pkl` | 学習データ（各42MB） |
| `data/models/*.pkl` | 巨大なモデルファイル |
| `**/venv/` | Python仮想環境 |
| `scripts/venv_onnx/` | ONNX変換用仮想環境 |
| `data/training_data/` | 学習用CSVデータ |
| `data/models/combination_batches/` | バッチ処理中間ファイル |

**結果**: Git packサイズ **482MB → 10MB** (98%削減)

### 2. Pre-commitフック

`.git/hooks/pre-commit` に5MB以上のファイルをブロックするフックを設置。

コミット時に自動でサイズチェックが実行され、巨大ファイルがあればエラーになります。

### 3. .gitignore強化

すべての`.pkl`ファイルを禁止し、必要なモデルファイルのみ許可：

**✅ 許可（Gitに含める）:**
- `data/models/*.onnx` - ONNXモデル（軽量）
- `data/models/*_lgb.txt` - LightGBMモデル（テキスト形式）
- `data/models/*_keys.json` - 特徴量キー
- `data/past_results.csv` - 過去データ
- `data/keisen_master.json` - 罫線マスタ

**❌ 禁止（Gitに含めない）:**
- `*.pkl` - すべてのPickleファイル
- `**/venv/` - 仮想環境
- `data/training_data/` - 学習データ
- `data/models/combination_batches/` - 中間ファイル

## 今後の注意事項

1. **新しいモデルファイルを追加する場合**
   - `.pkl`形式は使わず、`.onnx`または`.txt`形式を使用
   - 5MB以上のファイルは事前に確認

2. **pre-commitフックでエラーになった場合**
   - `.gitignore`に追加するか、ファイル形式を変更

3. **Vercelデプロイ**
   - `git push` でGitHub経由の自動デプロイを推奨
   - `vercel --prod` CLIは使用しない（遅い）

## 確認方法

```bash
# Gitリポジトリサイズ確認
du -sh .git/

# 追跡ファイルサイズ確認
git ls-files | xargs -I{} sh -c 'test -f "{}" && stat -c %s "{}"' | awk '{s+=$1} END {printf "%.2f MB\n", s/1024/1024}'

# 巨大ファイルの検索
find . -path ./node_modules -prune -o -path ./.git -prune -o -size +5M -type f -print
```
