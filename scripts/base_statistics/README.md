# 基礎集計スクリプト（base_statistics）

**基礎集計（base_statistics）**に関するスクリプトをカテゴリごとに整理したディレクトリです。

**用語の定義**:
- **データ分析**: データを分析する全体的な活動（上位概念）
- **基礎集計（base_statistics）**: データ分析の中の一つのフェーズ。予測モデル作成前の基礎的な統計集計を実施する段階

## ディレクトリ構造

```
scripts/base_statistics/
├── 01_keisen_base_stats/          # Phase 1: keisen基礎集計
│   ├── analyze_keisen_base_stats.py
│   └── run_keisen_base_stats_all_ranges.py
├── 02_keisen_comparison/          # Phase 2: 旧keisen vs 新keisen比較
├── 03_temporal_analysis/          # Phase 3: 時系列・周期性分析
├── 04_digit_patterns/             # Phase 4: 数値パターン分析（将来実装）
├── 05_cube_characteristics/       # Phase 5: CUBE特性分析
├── 06_correlation/                 # Phase 6: 相関分析
├── 07_anomaly_detection/           # Phase 7: 異常値・外れ値分析
└── 08_extreme_cube/                # 極CUBE基礎集計
```

## 各カテゴリの説明

### 01_keisen_base_stats: keisen基礎集計

**目的**: keisen作成のための基礎統計を実施する。

**スクリプト**:
- `analyze_keisen_base_stats.py`: 指定範囲のデータから、前々回・前回パターンごとの当選数字の出現頻度とランキングを集計
- `run_keisen_base_stats_all_ranges.py`: 3パターンの集計範囲（全範囲、週5以降、4801以降）で一括実行

**出力ファイル**:
- `data/base_statistics/01_keisen_base_stats/パターン出現頻度_{範囲名}.json`: パターン出現頻度
- `data/base_statistics/01_keisen_base_stats/当選数字ランキング_{範囲名}.json`: 当選数字のランキング
- `data/base_statistics/01_keisen_base_stats/統計的信頼性指標_{範囲名}.json`: 統計的信頼性指標

**範囲名**:
- `全範囲`: 1-6850回（suffix: all）
- `週5実施開始以降`: 1340-6850回（suffix: 1340）
- `リハーサル導入以降`: 4801-6850回（suffix: 4801）

**使用方法**:
```bash
# 単一範囲の集計
python scripts/base_statistics/01_keisen_base_stats/analyze_keisen_base_stats.py \
  --start-round 4801 --end-round 6850 --output-suffix 4801

# 全範囲パターンの一括実行
python scripts/base_statistics/01_keisen_base_stats/run_keisen_base_stats_all_ranges.py

# チェックポイントから処理を再開（処理が中断された場合）
python scripts/base_statistics/01_keisen_base_stats/analyze_keisen_base_stats.py \
  --start-round 4801 --end-round 6850 --output-suffix 4801 --resume

# バッチサイズを調整（メモリ不足の場合）
python scripts/base_statistics/01_keisen_base_stats/analyze_keisen_base_stats.py \
  --start-round 4801 --end-round 6850 --output-suffix 4801 --batch-size 250
```

**メモリ対策機能**:
- **チェックポイント機能**: 処理済み回号を保存し、中断後も再開可能
- **バッチ処理**: 500回号ごとにバッチ処理（`--batch-size`で調整可能）
- **進捗表示**: `tqdm`による進捗バー表示
- **メモリ管理**: バッチ処理後にメモリを解放（`gc.collect()`）

### 02_keisen_comparison: 旧keisen vs 新keisen比較

**目的**: keisen更新による予測精度への影響評価。

**実装予定**: 旧keisen（1340-6391回）と新keisen（4801-6850回）で生成したCUBEを比較分析するスクリプト。

### 03_temporal_analysis: 時系列・周期性分析

**目的**: 時間軸に基づく周期性とトレンドの検出。

**実装予定**: 曜日、月相（月齢）、季節、月、年・四半期などの時間軸で当選番号の出現パターンを分析するスクリプト。

### 04_digit_patterns: 数値パターン分析

**目的**: 数字の出現パターンと組み合わせ特性の分析。

**実装予定**: 各数字（0-9）の出現頻度、よく出現する数字の組み合わせ、連続性・周期性を分析するスクリプト。

### 05_cube_characteristics: CUBE特性分析

**目的**: CUBEの構造特性と当選番号との関係性の分析。

**実装予定**: CUBEのサイズ、密度、メイン行の特性を分析するスクリプト。

### 06_correlation: 相関分析

**目的**: 変数間の相関関係と相互依存性の分析。

**実装予定**: リハーサル数字と当選番号、N3とN4、前回・前々回との相関を分析するスクリプト。

### 07_anomaly_detection: 異常値・外れ値分析

**目的**: 統計的に異常なパターンと外れ値の検出。

**実装予定**: CUBE内に出現しなかった回、リハーサル数字と当選番号が全く重ならなかった回などの異常パターンを検出するスクリプト。

### 08_extreme_cube: 極CUBE基礎集計

**目的**: リハーサル数字非依存の全期間統計分析。

**実装予定**: 極CUBE内での当選番号出現分析、数字の出現パターン、時系列・周期性分析を実施するスクリプト。

## 関連ドキュメント

- [基礎集計設計書](../../docs/01_design/09-data-analysis-design.md)
- [基礎集計メモリ最適化設計](../../docs/01_design/09-data-analysis-design-memory-optimization.md)
- [ToDo: データ分析（基礎集計）](../../docs/02_todo/05_data_analysis/)

