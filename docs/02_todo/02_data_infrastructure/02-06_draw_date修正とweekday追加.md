# 02-06 draw_date修正とweekday追加

## 概要
`past_results.csv`の`draw_date`を正しく取得し、基礎集計に必要な`weekday`カラムを追加する。みずほ銀行から全件（1-4800回）の日付を取得し、hpfree.comから取得するデータ（4801回以降）は回号差から平日のみをカウントして日付を計算する。定期更新時も同様の方法で日付を計算する。

## 背景
- `draw_date`がNULLのレコードが存在（hpfree.comから取得したデータ）
- hpfree.comのページには日付情報が含まれていない
- 基礎集計で曜日が必要だが、現在は`draw_date`から計算する必要がある
- 定期更新時（毎日平日）に最新回号を取得する際、日付をどう計算するか

## 詳細タスク

### Phase 1: 日付計算関数の実装

- [x] 回号差から平日のみをカウントして日付を計算する関数（`calculate_draw_date_from_round_diff`）を作成
  - `scripts/fetch_past_results.py`に追加
  - `is_draw_day`関数を使用して平日判定と年末年始除外
  - 回号差が正の場合は未来、負の場合は過去に計算

- [x] 日付から曜日を計算する関数（`calculate_weekday`）を作成
  - `scripts/fetch_past_results.py`に追加
  - 0-4の整数を返す（0:月, 1:火, 2:水, 3:木, 4:金）

### Phase 2: データ取得スクリプトの更新

- [x] `combine_data`関数を更新
  - マージモード時に既存データの最新回号と日付を基準に日付を計算
  - `weekday`も自動計算して追加
  - `output_file`パラメータを追加して既存データを読み込めるように

- [x] `save_to_csv`関数を更新
  - `weekday`カラムを追加
  - 既存データに`weekday`がない場合は`draw_date`から計算

- [x] `combine_data`関数の呼び出し箇所を更新
  - `output_file`パラメータを追加

### Phase 3: weekdayカラム追加スクリプトの作成

- [x] `scripts/add_weekday_column.py`を作成
  - 既存データの`draw_date`から`weekday`を計算して追加
  - バックアップを作成してから更新

### Phase 4: データ整合性検証スクリプトの作成

- [x] `scripts/validate_date_weekday.py`を作成
  - `draw_date`と`weekday`の整合性を検証
  - 回号と日付の順序が正しいか確認

### Phase 5: TypeScript型定義の更新

- [x] `src/lib/data-loader/types.ts`を更新
  - `PastResult`インターフェースに`weekday`フィールドを追加

- [x] `src/lib/data-loader/past-results.ts`を更新
  - `weekday`カラムのパース処理を追加
  - `weekday`カラムが存在しない場合の処理を追加

### Phase 6: ドキュメントの更新

- [x] `docs/01_design/03-data-api-design.md`を更新
  - `past_results.csv`のカラム定義に`weekday`を追加
  - 日付取得方法の説明を追加
  - データベーススキーマにも`weekday`を追加

### Phase 7: データ取得・更新の実行

- [ ] みずほ銀行から全件（1-4800回）の日付を取得・更新
  - コマンド: `python3 scripts/fetch_past_results.py --from-round 1 --to-round 4800 --update-null`
  - または: `python3 scripts/fetch_past_results.py --update-null`

- [ ] `weekday`カラムを追加
  - コマンド: `python3 scripts/add_weekday_column.py`

- [ ] データ整合性を検証
  - コマンド: `python3 scripts/validate_date_weekday.py`

## 完了した作業

- 2025-11-07: 日付計算関数とweekday計算関数を実装
- 2025-11-07: `combine_data`関数と`save_to_csv`関数を更新
- 2025-11-07: `add_weekday_column.py`スクリプトを作成
- 2025-11-07: `validate_date_weekday.py`スクリプトを作成
- 2025-11-07: TypeScript型定義を更新
- 2025-11-07: データモデル設計ドキュメントを更新

## 注意事項

- `weekday`カラムは後方互換性のためオプション（既存データにない場合は`draw_date`から計算）
- 定期更新時は既存データの最新回号と日付を基準に計算するため、正確な日付が必要
- みずほ銀行から全件の日付を取得することで、4801回以降の日付計算の基準が正確になる

## 実行コマンド

```bash
# みずほ銀行から全件の日付を取得・更新（NULLの日付のみ更新）
python3 scripts/fetch_past_results.py --update-null

# または、1-4800回を全件取得
python3 scripts/fetch_past_results.py --from-round 1 --to-round 4800

# weekdayカラムを追加
python3 scripts/add_weekday_column.py

# データ整合性を検証
python3 scripts/validate_date_weekday.py
```

## 関連ファイル

- `scripts/fetch_past_results.py`: データ取得スクリプト（更新済み）
- `scripts/add_weekday_column.py`: weekdayカラム追加スクリプト（新規作成）
- `scripts/validate_date_weekday.py`: データ整合性検証スクリプト（新規作成）
- `src/lib/data-loader/past-results.ts`: TypeScriptデータローダー（更新済み）
- `src/lib/data-loader/types.ts`: TypeScript型定義（更新済み）
- `docs/01_design/03-data-api-design.md`: データモデル設計（更新済み）
- `data/past_results.csv`: 過去当選番号データ

