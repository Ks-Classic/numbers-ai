# 極CUBE生成スクリプト使用ガイド

## 概要

`scripts/production/generate_extreme_cube.py` は、極CUBE（Extreme CUBE）を生成するためのPythonスクリプトです。極CUBEは、リハーサル数字に依存せず、全期間（1-6850回）で一貫性のある分析を可能にするために設計された特別なCUBE形式です。

## 特徴

- **N3のみ**: ナンバーズ3のみを対象とします。
- **1パターンのみ**: パターンB1相当の単一パターンで生成されます。
- **全期間対応**: 第1回から最新回まで、リハーサル数字の有無に関わらず生成可能です。
- **JSON出力**: 分析に適したJSON形式で出力されます。

## 必要要件

- Python 3.8以上
- 依存ライブラリ: `pandas`, `numpy`
- データファイル:
  - `data/past_results.csv`: 過去当選番号データ
  - `data/keisen_master.json`: 罫線マスターデータ

## 使用方法

### 基本的な実行

プロジェクトルートディレクトリから以下のコマンドを実行します。

```bash
# 第3回から最新回までの極CUBEを一括生成
python scripts/production/generate_extreme_cube.py
```

### オプション指定

```bash
# 特定の回号のみ生成
python scripts/production/generate_extreme_cube.py --rounds 6783,6784,6785

# 開始回号を指定して生成
python scripts/production/generate_extreme_cube.py --start-round 6000

# 終了回号を指定して生成
python scripts/production/generate_extreme_cube.py --end-round 1000

# 出力ディレクトリを指定
python scripts/production/generate_extreme_cube.py --output-dir ./my_cubes
```

### コマンドライン引数

| 引数 | 説明 | デフォルト値 |
|------|------|------------|
| `--rounds` | 生成する回号のリスト（カンマ区切り） | なし |
| `--start-round` | 生成を開始する回号 | 3 |
| `--end-round` | 生成を終了する回号 | 最新回 |
| `--output-dir` | 出力先ディレクトリ | `data/extreme_cubes` |
| `--data-dir` | データファイルがあるディレクトリ | `data` |

## 出力ファイル形式

生成されたファイルは `data/extreme_cubes/n3/` ディレクトリに保存されます。

- ファイル名: `round_{回号:04d}.json` (例: `round_6783.json`)
- 形式: JSON

### JSON構造例

```json
{
  "round_number": 6783,
  "target": "n3",
  "pattern": "extreme",
  "grid": [
    [null, null, null, null, null, null, null, null],
    [5, 0, 1, 6, 2, 7, 3, 8],
    [0, 5, 6, 1, 7, 2, 8, 3],
    [null, null, null, null, null, null, null, null],
    [null, null, null, null, null, null, null, null]
  ],
  "grid_size": {
    "rows": 5,
    "cols": 8
  },
  "metadata": {
    "generated_at": "2025-11-28T10:30:00.000000Z",
    "keisen_version": "1.0"
  }
}
```

## API仕様 (Python関数)

スクリプト内の主要な関数は、他のPythonスクリプトからもインポートして使用可能です。

### `generate_extreme_cube`

単一の回号に対する極CUBEを生成します。

```python
from scripts.production.generate_extreme_cube import generate_extreme_cube

grid, rows, cols = generate_extreme_cube(df, keisen_master, round_number)
```

- **引数**:
  - `df` (pd.DataFrame): 過去当選番号データ
  - `keisen_master` (dict): 罫線マスターデータ
  - `round_number` (int): 生成対象の回号
- **戻り値**:
  - `grid` (List[List[Optional[int]]]): 生成されたグリッド（1-indexed）
  - `rows` (int): 行数
  - `cols` (int): 列数
- **例外**:
  - `ChartGenerationError`: 生成に失敗した場合

### `generate_batch_extreme_cubes`

複数の回号に対して一括生成を行います。

```python
from scripts.production.generate_extreme_cube import generate_batch_extreme_cubes

stats = generate_batch_extreme_cubes(
    df=df,
    keisen_master=keisen_master,
    start_round=100,
    end_round=200
)
```

## トラブルシューティング

### よくあるエラー

1. **FileNotFoundError: 過去当選番号データが見つかりません**
   - `data/past_results.csv` が存在するか確認してください。
   - `--data-dir` オプションで正しいディレクトリを指定してください。

2. **ValueError: past_results.csvに'round_number'列がありません**
   - CSVファイルの形式が正しいか確認してください。ヘッダー行が必要です。

3. **ChartGenerationError: 極CUBE生成エラー**
   - 指定した回号の前回・前々回のデータが存在するか確認してください。
   - 回号1, 2は生成できません（過去データ不足のため）。

### パフォーマンス最適化

- 全期間（約6850回分）の生成には数分かかる場合があります。
- 頻繁に再生成する必要がない場合は、一度生成したJSONファイルを再利用することを推奨します。
- ログ出力を抑制したい場合は、スクリプト内の `logging.basicConfig` のレベルを `WARNING` に変更してください。
