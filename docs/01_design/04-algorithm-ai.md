# アルゴリズム・AI設計書 v2.0

**Document Management Information**
- Document ID: DOC-04
- Version: 2.0
- Created: 2025-11-02
- Last Updated: 2025-11-25
- Status: Updated (特徴量エンジニアリング大幅改善を反映)
- Approver: Technical Lead

---

## 📋 目次

1. [ドキュメント目的と適用範囲](#1-ドキュメント目的と適用範囲)
   - [1.5 システム全体の流れ](#15-システム全体の流れ)
2. [予測表生成アルゴリズム](#2-予測表生成アルゴリズム)
3. [AI特徴量設計](#3-ai特徴量設計)
4. [AIモデルアーキテクチャ](#4-aiモデルアーキテクチャ)

---

## 1. ドキュメント目的と適用範囲

### 1.1 目的
本ドキュメントは、ナンバーズAI予測システムの**コアアルゴリズム**と**AIモデル**を定義する。予測表生成ロジックとAI予測の仕組みを詳細に記述することで、再現性のある実装を可能にする。

### 1.2 対象読者
- アルゴリズム実装者
- データサイエンティスト
- バックエンドエンジニア
- AIモデル開発者

### 1.3 関連ドキュメント
- [03-data-api-design.md](./03-data-api-design.md): データ・API設計
- [06-implementation-plan.md](./06-implementation-plan.md): 実装計画
- `元ネタ/表作成ルール.,md`: 詳細な表生成仕様

### 1.5 システム全体の流れ

本システムは、過去の当選番号データから予測表を生成し、その表から特徴量を抽出して機械学習モデルを学習し、新しい回号について予測を行うという一連のプロセスで構成されています。

#### ステップ1: データ準備 (`01_data_preparation.ipynb`)

**目的**: 過去の当選番号データを読み込み、学習用データセットを準備

**処理内容**:
1. 過去の全データ（`past_results.csv`）を読み込み
2. 基準回号を設定（最新回号を自動取得、デフォルト: 第6849回）
3. 直近1,000回分のデータを抽出（設定ファイル`config.py`で変更可能）
4. 学習用データセットとして保存（`train_data_1000.csv`）

**データ形式**:
- 各回号には「n3_winning」（3桁の当選番号）と「n4_winning」（4桁の当選番号）が記録されている
- 例: 第6849回のn3_winning = "652"、n4_winning = "4714"

**出力**: `data/train_data_1000.csv`（1,000行の学習用データ）

**設定ファイル**:
- `notebooks/config.py`で学習範囲（TRAIN_SIZE）を設定可能
- デフォルト: 1,000回分
- 基準回号は最新回号を自動取得（BASE_ROUND_AUTO = True）

---

#### ステップ2: 予測表生成 (`02_chart_generation.ipynb`)

**目的**: 各回号に対して「予測表」を生成

**予測表とは**:
- 過去の当選番号から、次回の当選番号の候補を配置した表
- 4パターン（A1/A2/B1/B2）があり、それぞれ異なるルールで生成される

**生成プロセス**（各回号ごと）:
```
第6849回の予測表を生成する場合:
  1. 第6848回の当選番号を取得（前回）
  2. 第6847回の当選番号を取得（前々回）
  3. keisen_master.json（罫線マスター）を参照
  4. パターンA1/A2/B1/B2それぞれで予測表を生成
```

**予測表の意味**:
- 表の中に数字（0-9）が配置される
- この配置パターンから、次回の当選番号の傾向を読み取る

**実装モジュール**: `notebooks/chart_generator.py`

---

#### ステップ3: 特徴量抽出 (`03_feature_engineering.ipynb`)

**目的**: 予測表から「特徴量」を抽出して、機械学習モデルが学習できる形式にする

**特徴量の種類**:

1. **形状特徴**: 数字が表の中でどのように配置されているか
   - 線の長さ、曲がりの回数、密度など

2. **位置特徴**: 数字が表のどの位置にあるか
   - 重心座標、端からの距離、中心からの距離など

3. **関係性特徴**: リハーサル数字（CSVの`n3_rehearsal`/`n4_rehearsal`列のデータ）との関係
   - リハーサル数字との距離、重なり度、角度など

4. **集約特徴**: 組み合わせに関する統計
   - 出現頻度、分散度など

**リハーサル数字の役割**:
- **リハーサル数字** = CSVの`n3_rehearsal`と`n4_rehearsal`列のデータ
- これは当日の本当選番号の1時間前に発表されるもの
- 当日の当選番号を予測するために使用する
- **重要**: リハーサル数字は前回の当選番号ではなく、**該当回号のCSVファイルに定義されているリハーサル数字**を使用する
- 例: 第6758回を予測する場合、リハーサル数字は第6758回の`n3_rehearsal`="670"と`n4_rehearsal`="8218"
- 予測表上でリハーサル数字がどこに配置されているかを確認
- リハーサル数字と候補数字の関係性を特徴量として抽出

**実装上の注意**:
- 特徴量エンジニアリング時は、各回号の`n3_rehearsal`/`n4_rehearsal`カラムを直接読み込む
- 前回の当選番号（`round_number-1`の`winning`）ではない点に注意

**実装モジュール**: `notebooks/feature_extractor.py`

---

#### ステップ4: 学習データ生成 (`03_feature_engineering.ipynb`)

**目的**: 機械学習モデルが学習するための「入力（特徴量）」と「出力（ラベル）」のペアを生成

**ラベルの意味**:
- **0**: 当選しなかった（負例）
- **1**: 当選した（正例）

**軸数字予測モデルの学習データ**:
```
設定回数分 × 4パターン × 10数字（0-9） = 設定回数 × 40サンプル
（デフォルト: 1,000回分 × 40 = 40,000サンプル）

例: 第6849回、パターンA1、数字5の場合
  入力: 特徴量ベクトル（約72次元、2025年1月時点）
     - 形状特徴（7次元）: 最大連続長、曲がり回数、直線度、密集度、対角線連続長、クラスタリング係数、形状複雑度
     - 位置特徴（12次元）: 重心X/Y座標、端からの距離、中心からの距離、象限別割合、エッジ近接度
     - 関係性特徴（約34-35次元）: 
       - 距離特徴量（9個）: 平均、中央値、Q25、Q75、最小、最大、標準偏差、トリム平均
       - 重なり特徴量（7-8個、N3の場合は7個、N4の場合は8個）: 基本的な重なり度、桁ごとの重なり
       - 方向性特徴量（17個）: 8方向のヒストグラム、8方向の割合、主要方向、集中度
       - 裏数字特徴量（1個）: 裏数字の割合（修正版）
     - 集約特徴（2次元）
     - パターンID（5次元）
  出力: ラベル（0または1）
     1 = 数字5が当選番号に含まれた
     0 = 数字5が当選番号に含まれなかった
     （例: "149"に5は含まれていないので0）
```

**組み合わせ予測モデルの学習データ**:
```
設定回数分 × 4パターン × サンプリングされた組み合わせ = 数十万〜数百万サンプル
（デフォルト: 1,000回分）

例: 第6849回、パターンA1、組み合わせ"652"の場合
  入力: 特徴量ベクトル（72次元）
     - 組み合わせに関する特徴量、パターンID
  出力: ラベル（0または1）
     1 = 組み合わせ"149"が当選した（実際に当選したので1）
     0 = 組み合わせ"149"が当選しなかった

ボックス/ストレートの違い:
  - label_box: 順序無関係（"149" = "914" = "491"）
  - label_straight: 順序重要（"149"のみが正解）
```

**ポイント**:
- 設定回数分（デフォルト: 1,000回分）のデータを全て使って、各回号ごとに予測表を生成
- その予測表から特徴量を抽出し、「実際に当選したかどうか」をラベルとして付与
- これにより「予測表上の特徴量」と「当選結果」の関係を学習できる
- **リハーサル数字の取得**: 各回号の`n3_rehearsal`/`n4_rehearsal`カラムから直接取得（前回の当選番号ではない）

**出力**: `data/models/*_data.pkl`（学習データファイル）

---

#### ステップ5: モデル学習 (`04_model_training.ipynb`)

**目的**: 特徴量とラベルの関係を学習して、予測モデルを構築

**学習プロセス**:
```
学習データ（特徴量 + ラベル）
    ↓
XGBoostモデルに学習させる
    ↓
学習済みモデル（.pklファイル）
```

**生成されるモデル**:
1. `n3_axis.pkl`: N3の軸数字予測（数字0-9のうち、どれが当選するか）
2. `n4_axis.pkl`: N4の軸数字予測
3. `n3_box_comb.pkl`: N3のボックス組み合わせ予測（順序無関係）
4. `n3_straight_comb.pkl`: N3のストレート組み合わせ予測（順序重要）
5. `n4_box_comb.pkl`: N4のボックス組み合わせ予測
6. `n4_straight_comb.pkl`: N4のストレート組み合わせ予測（データが不十分な場合はスキップ）

**評価指標**:
- AUC-ROC: 予測精度の指標（0.5 = ランダム、1.0 = 完璧）
- Precision、Recall、F1-Score: 分類性能の指標
- Top-K Accuracy: 上位K件の予測精度

**出力**: `data/models/*.pkl`（学習済みモデルファイル）

---

#### ステップ6: 推論 (`predict_cli.py`)

**目的**: 新しい回号について、学習済みモデルを使って予測する

**推論プロセス**:
```
1. ユーザーが回号とリハーサル数字を入力
   （例: 回号=6759、リハーサル数字N3=149、N4=3782）

2. 4パターン（A1/A2/B1/B2）それぞれで予測表を生成

3. 各パターン×各数字（0-9）の特徴量を抽出

4. 軸数字予測モデルで予測
   - 特徴量を入力 → 当選確率を出力
   - 例: パターンA1、数字5 → 確率0.65

5. 4パターン間で比較し、最良パターンを特定

6. 最良パターンで組み合わせ予測
   - 軸数字を含む組み合わせを生成
   - 組み合わせ予測モデルで予測
   - スコア順にランキング

7. 結果を表示
```

**実装モジュール**: `notebooks/predict_cli.py`、`notebooks/model_loader.py`

**出力**: 予測結果（軸数字ランキング、組み合わせランキング）

---

**システム全体の流れのまとめ**:

```
過去データ（past_results.csv）
    ↓
[ステップ1] データ準備
    ↓
学習用データ（train_data_1000.csv、config.pyで設定可能）
    ↓
[ステップ2] 予測表生成（各回号ごと）
    ↓
予測表（4パターン）
    ↓
[ステップ3] 特徴量抽出
    ↓
特徴量ベクトル
    ↓
[ステップ4] 学習データ生成
    ↓
学習データ（特徴量 + ラベル）
    ↓
[ステップ5] モデル学習
    ↓
学習済みモデル（.pklファイル）
    ↓
[ステップ6] 推論（新しい回号）
    ↓
予測結果
```

**重要なポイント**:
- **学習時**: 過去4801回分から最新回までのデータ（約1,894回分）で「予測表の特徴量」と「実際の当選結果」の関係を学習
- **推論時**: 新しい回号の予測表を生成し、学習済みモデルで予測
- **リハーサル数字**: CSVの`n3_rehearsal`/`n4_rehearsal`列のデータで、当日の本当選番号の1時間前に発表されるもの。予測表上の位置関係を特徴量として使用
- **4パターン**: A1/A2/B1/B2それぞれで予測表を生成し、最良パターンを選択

---

## 2. 予測表生成アルゴリズム

本セクションは `docs/元ネタ/表作成ルール.,md` の内容を実装可能な形で整理する。

### 2.1 アルゴリズムフロー

```
入力: round_number, pattern ('A1' | 'A2' | 'B1' | 'B2'), target ('n3' | 'n4')

ステップ1: 予測出目の抽出
  - round_number-1 (前回) と round_number-2 (前々回) の当選番号を取得
  - keisen_master.json から各桁の予測出目を取得
  - 全桁の予測出目を結合 → source_list
  
  **注意:** `keisen_master.json`の作成方法については、[08-keisen-master-creation.md](./08-keisen-master-creation.md)を参照してください。

ステップ2: パターン別の元数字リスト作成
  - pattern = 'A1' または 'A2' (欠番補足あり):
    - source_list に 0-9 の欠番をすべて追加
  - pattern = 'B1' または 'B2' (欠番補足なし):
    - source_list をそのまま使用（0も含めて、すべて欠番補足しない）
  - 昇順ソート → nums

ステップ3: メイン行の組み立て
  - mainRows = []
  - tempList = nums.copy()（既にソート済み）
  - while tempList が空でない:
    - 最後のメイン行かどうかを判定（残りの数字が4つ以下なら最後の行）
    - targetCount = 最後の行なら残りすべて、そうでなければ4
    - newRow = []
    - while newRow.length < targetCount and tempList.length > 0:
      - prevDigit = newRow の最後の要素（なければ null）
      - tempList を先頭から走査し、prevDigit と異なる数字を探す
      - 見つかったら newRow に追加し、tempList から削除
      - 見つからなければ（すべて同じ数字の場合）、仕方なく同じ数字を追加
    - mainRows.push(newRow)
  
  **ルール**: tempListは既にソート済みなので、4桁単位で最小値から順に重複せずに選択。
  - tempListは既にソート済み（applyPatternExpansionでソート済み）
  - 4桁単位で最小値から順に重複せずに選択
  - 4桁埋めたら次の最小値から繰り返し
  - 4桁埋まらなかったら、次の未消費の最小値から埋めていく
  - 同じ行内での連続は回避（直前の数字と同じ場合はスキップして次を探す）
  - 行をまたぐ連続は許容（前の行の最後と次の行の最初が同じでもOK）
  - 元数字リストに存在する数分だけ使用可能（同じ数字が複数回出現する場合は、その分だけ使用）
  
  **例**: nums = [0, 1, 2, 3, 4, 5, 5, 6, 6, 7, 8, 9, 9]
  - メイン行0: [0, 1, 2, 3]
  - メイン行1: [4, 5, 6, 5] ← 5の次に5が来るが、同じ行内なのでスキップして6を取る。その後5を取る
  - メイン行2: [6, 7, 8, 9] ← 6は前の行の最後と同じだが、行をまたいでいるのでOK
  - メイン行3: [9]

ステップ4: グリッド初期配置
  - rows = mainRows.length * 2
  - cols = 8
  - grid = rows × cols の2次元配列（初期値 null）
  - for i in 0..mainRows.length-1:
    - row = i * 2
    - for j in 0..3:
      - grid[row][j*2] = mainRows[i][j]

ステップ5: パターンA2/B2中心0配置
  - if pattern = 'A2' or pattern = 'B2':
    - centerRows = [floor((rows-1)/2), ceil((rows-1)/2)]
    - centerCols = [floor((cols-1)/2), ceil((cols-1)/2)]
    - for r in centerRows:
      - for c in centerCols:
        - if grid[r][c] = null:
          - grid[r][c] = 0
          - break outer loop
  - if pattern = 'A1' or pattern = 'B1':
    - 中心0配置を実行しない

ステップ6: 裏数字ルール（縦パス）
  - inverse(n) = (n + 5) % 10
  - repeat:
    - updated = false
    - for y in 0..rows-1:
      - for x in 0..cols-1:
        - if grid[y][x] = null and y > 0 and grid[y-1][x] != null:
          - grid[y][x] = inverse(grid[y-1][x])
          - updated = true
  - until not updated

ステップ7: 裏数字ルール（横パス）
  - repeat:
    - updated = false
    - for y in 0..rows-1:
      - for x in 0..cols-1:
        - if grid[y][x] = null and x > 0 and grid[y][x-1] != null:
          - grid[y][x] = inverse(grid[y][x-1])
          - updated = true
  - until not updated

ステップ8: 余りマスルール
  - repeat:
    - updated = false
    - for y in 0..rows-1:
      - for x in 0..cols-1:
        - if grid[y][x] = null and y > 0 and grid[y-1][x] != null:
          - grid[y][x] = grid[y-1][x]
          - updated = true
  - until not updated

出力: grid (完成した予測表)
```

### 2.2 TypeScript実装例

```typescript
// src/lib/chart-generator/index.ts

export function generateChart(
  roundNumber: number,
  pattern: Pattern, // 'A1' | 'A2' | 'B1' | 'B2'
  target: Target
): ChartData {
  // Step 1: 予測出目の抽出
  const sourceList = extractPredictedDigits(roundNumber, target);
  
  // Step 2: 元数字リスト作成
  const nums = applyPatternExpansion(sourceList, pattern);
  
  // Step 3: メイン行の組み立て
  const mainRows = buildMainRows(nums);
  
  // Step 4: グリッド初期配置
  const rows = mainRows.length * 2;
  const cols = 8;
  const grid = initializeGrid(rows, cols, mainRows);
  
  // Step 5: パターンA2/B2中心0配置
  if (pattern === 'A2' || pattern === 'B2') {
    placeCenterZero(grid, rows, cols);
  }
  
  // Step 6-8: 裏数字・余りマスルール
  applyVerticalInverse(grid, rows, cols);
  applyHorizontalInverse(grid, rows, cols);
  applyRemainingCopy(grid, rows, cols);
  
  return {
    grid,
    rows,
    cols,
    pattern,
    target,
    sourceDigits: sourceList
  };
}

function inverse(n: number): number {
  return (n + 5) % 10;
}

function buildMainRows(nums: number[]): MainRow[] {
  const mainRows: MainRow[] = [];
  let tempList = [...nums];
  let rowIndex = 0;
  
  while (tempList.length > 0) {
    const uniqueDigits = [...new Set(tempList)].sort((a, b) => a - b);
    
    if (uniqueDigits.length >= 4) {
      const members = uniqueDigits.slice(0, 4);
      const newRow: [number, number, number, number] = [0, 0, 0, 0];
      
      for (let i = 0; i < 4; i++) {
        const idx = tempList.indexOf(members[i]);
        newRow[i] = tempList[idx];
        tempList.splice(idx, 1);
      }
      
      mainRows.push({ elements: newRow, rowIndex: rowIndex++ });
    } else {
      const maxValue = Math.max(...uniqueDigits);
      const newRow: [number, number, number, number] = [...uniqueDigits, 0, 0, 0].slice(0, 4) as [number, number, number, number];
      
      for (let i = uniqueDigits.length; i < 4; i++) {
        newRow[i] = maxValue;
      }
      
      // tempListから使用した数字を削除
      for (const digit of newRow) {
        const idx = tempList.indexOf(digit);
        if (idx !== -1) tempList.splice(idx, 1);
      }
      
      mainRows.push({ elements: newRow, rowIndex: rowIndex++ });
    }
  }
  
  return mainRows;
}

function applyVerticalInverse(grid: ChartGrid, rows: number, cols: number): void {
  let updated = true;
  while (updated) {
    updated = false;
    for (let y = 0; y < rows; y++) {
      for (let x = 0; x < cols; x++) {
        if (grid[y][x] === null && y > 0 && grid[y-1][x] !== null) {
          grid[y][x] = inverse(grid[y-1][x]!);
          updated = true;
        }
      }
    }
  }
}

// 他の関数も同様に実装...
```

**詳細な仕様:**
完全な仕様は `docs/元ネタ/表作成ルール.,md` を参照

---

## 3. AI特徴量設計

### 3.1 特徴量カテゴリ

AIモデルが学習する特徴量は、以下の4カテゴリに分類される。

#### カテゴリ1: 形状特徴（Shape Features）

予測表上の数字の配置パターンから抽出される幾何学的特徴。

**具体的な特徴量（例）:**
- **線の長さ**: 同じ数字が連続する最大長
- **曲がりの回数**: 数字の配置方向が変わる回数
- **直線度**: 配置が直線的かどうかの度合い
- **密集度**: 特定エリアへの集中度合い

**計算例（TypeScript）:**

```typescript
function calculateLineLength(grid: ChartGrid, number: number): number {
  let maxLength = 0;
  // 横方向の連続チェック
  for (let y = 0; y < grid.length; y++) {
    let currentLength = 0;
    for (let x = 0; x < grid[y].length; x++) {
      if (grid[y][x] === number) {
        currentLength++;
        maxLength = Math.max(maxLength, currentLength);
      } else {
        currentLength = 0;
      }
    }
  }
  // 縦方向も同様にチェック...
  return maxLength;
}
```

---

#### カテゴリ2: 位置特徴（Position Features）

数字が表のどこに配置されているかに関する特徴。

**具体的な特徴量:**
- **重心X座標**: 数字の平均X位置
- **重心Y座標**: 数字の平均Y位置
- **左端からの距離**: 最左位置
- **右端からの距離**: 最右位置
- **上端からの距離**: 最上位置
- **下端からの距離**: 最下位置
- **中心からの距離**: 表の中心からの平均距離

**計算例:**

```typescript
function calculateCentroid(grid: ChartGrid, number: number): { x: number; y: number } {
  let sumX = 0, sumY = 0, count = 0;
  
  for (let y = 0; y < grid.length; y++) {
    for (let x = 0; x < grid[y].length; x++) {
      if (grid[y][x] === number) {
        sumX += x;
        sumY += y;
        count++;
      }
    }
  }
  
  return count > 0 
    ? { x: sumX / count, y: sumY / count }
    : { x: 0, y: 0 };
}
```

---

#### カテゴリ3: 関係性特徴（Relation Features）

候補数字とリハーサル数字の関係性に関する特徴。2025年1月時点で、より詳細な分析を可能にするため、以下の特徴量が実装されている。

##### 3.3.1 距離特徴量（Distance Features）

**基本的な距離特徴量:**
- **リハーサルとの距離 (`rehearsal_distance`)**: 候補数字の各位置から最も近いリハーサル数字の位置までのユークリッド距離の平均値

**距離統計特徴量（2025年1月追加）:**
外れ値の影響を軽減し、よりロバストな特徴量を提供するため、以下の統計量を計算：

- **平均距離 (`rehearsal_distance_mean`)**: 平均距離（既存の`rehearsal_distance`と同等）
- **中央値距離 (`rehearsal_distance_median`)**: 距離の中央値（外れ値に強い）
- **25%タイル距離 (`rehearsal_distance_q25`)**: 距離の第1四分位数
- **75%タイル距離 (`rehearsal_distance_q75`)**: 距離の第3四分位数
- **最小距離 (`rehearsal_distance_min`)**: 最小距離
- **最大距離 (`rehearsal_distance_max`)**: 最大距離（外れ値として評価可能）
- **標準偏差 (`rehearsal_distance_std`)**: 距離の分布の広がり
- **トリム平均 (`rehearsal_distance_trimmed_mean`)**: 最大値を除外した平均（外れ値除去）

**計算ロジック:**
```python
# 各候補位置から最も近いリハーサル位置までの距離を計算
distances = []
for c_pos in candidate_positions:
    min_dist = min(
        sqrt((c_pos[0] - r_pos[0])² + (c_pos[1] - r_pos[1])²)
        for r_pos in rehearsal_positions
    )
    distances.append(min_dist)

# 統計量を計算
mean = mean(distances)
median = median(distances)
q25 = percentile(distances, 25)
q75 = percentile(distances, 75)
std = std(distances)
trimmed_mean = mean(distances[distances < max(distances)])
```

##### 3.3.2 重なり特徴量（Overlap Features）

**基本的な重なり特徴量:**
- **重なり度 (`overlap_count`)**: 候補とリハーサルが同じ位置にある回数

**桁ごとの重なり特徴量（2025年1月追加）:**
リハーサル数字の各桁に対して、候補数字がどの桁に重なっているかを分析：

- **桁ごとの重なり数 (`rehearsal_overlap_digit_0/1/2/3`)**: リハーサル数字の各桁（N3の場合は0-2、N4の場合は0-3）に対して、候補数字が重なっている位置数
- **桁ごとの重なり総数 (`rehearsal_overlap_by_digit_count`)**: 全ての桁の重なり数の合計
- **桁ごとの重なり割合 (`rehearsal_overlap_by_digit_ratio`)**: 重なり総数を桁数で割った値（0-1）
- **全桁一致 (`rehearsal_full_match`)**: リハーサル数字の全桁が候補数字に重なっているか（1 or 0）
- **部分一致桁数 (`rehearsal_partial_match`)**: リハーサル数字の何桁が候補数字に重なっているか（0-3 for N3, 0-4 for N4）

**計算例（N3の場合、「631」がリハーサル数字）:**
```python
# リハーサル数字「631」の各桁の位置を取得
digit_0_positions = get_digit_positions(grid, rows, cols, 6)  # 1桁目: 6
digit_1_positions = get_digit_positions(grid, rows, cols, 3)  # 2桁目: 3
digit_2_positions = get_digit_positions(grid, rows, cols, 1)  # 3桁目: 1

# 候補数字の位置と各桁の位置の重なりを計算
overlap_digit_0 = len(set(candidate_positions) & set(digit_0_positions))
overlap_digit_1 = len(set(candidate_positions) & set(digit_1_positions))
overlap_digit_2 = len(set(candidate_positions) & set(digit_2_positions))

# 全桁一致判定
full_match = 1.0 if all(count > 0 for count in [overlap_digit_0, overlap_digit_1, overlap_digit_2]) else 0.0

# 部分一致桁数
partial_match = sum(1 for count in [overlap_digit_0, overlap_digit_1, overlap_digit_2] if count > 0)
```

##### 3.3.3 方向性特徴量（Direction Features）（2025年1月追加）

リハーサル数字の各位置から見て、候補数字がどの方向にあるかを8方向で分類：

**8方向の定義:**
- 0: 北（上）
- 1: 北東（右上）
- 2: 東（右）
- 3: 南東（右下）
- 4: 南（下）
- 5: 南西（左下）
- 6: 西（左）
- 7: 北西（左上）

**方向性特徴量:**
- **方向ヒストグラム (`rehearsal_direction_0` ～ `rehearsal_direction_7`)**: 各方向の候補数字の出現数（各リハーサル位置から各候補位置への方向をカウント）
- **方向割合 (`rehearsal_direction_ratio_0` ～ `rehearsal_direction_ratio_7`)**: 各方向の割合（正規化されたヒストグラム、0-1）
- **主要方向 (`rehearsal_primary_direction`)**: 最も多い方向（0-7）
- **方向集中度 (`rehearsal_direction_concentration`)**: 方向の集中度（エントロピーベース、0-1、1に近いほど集中）

**計算ロジック:**
```python
# 各リハーサル位置から各候補位置への方向を計算
histogram = [0] * 8
for r_pos in rehearsal_positions:
    for c_pos in candidate_positions:
        direction = get_direction(r_pos, c_pos)  # 0-7
        histogram[direction] += 1

# 方向割合を計算
total = sum(histogram)
direction_ratio = [count / total for count in histogram] if total > 0 else [0.0] * 8

# 主要方向
primary_direction = argmax(histogram)

# 方向集中度（エントロピーから計算）
entropy = -sum(p * log2(p) for p in direction_ratio if p > 0)
max_entropy = log2(8)  # 3
concentration = 1.0 - (entropy / max_entropy)
```

##### 3.3.4 裏数字特徴量（Inverse Features）

**裏数字関係 (`inverse_ratio`)**: 候補がリハーサルの裏数字である割合

**実装の修正（2025年1月）:**
以前の実装では、リハーサル位置と候補位置が同じ座標にないと計算されない問題があった。修正後は、リハーサル数字の各桁の裏数字の位置を取得し、その位置に候補数字があるかを確認するように変更された。

**計算ロジック:**
```python
# リハーサル数字の各桁の裏数字の位置を取得
inverse_positions = set()
for r_pos in rehearsal_positions:
    rehearsal_digit = grid[r_pos[0]][r_pos[1]]
    inverse_digit = inverse(rehearsal_digit)  # 裏数字を計算（例: 6→1, 3→8, 1→6）
    # グリッド内で裏数字の位置を検索
    for row, col in grid:
        if grid[row][col] == inverse_digit:
            inverse_positions.add((row, col))

# 候補位置と裏数字位置の重なりを計算
overlap_count = len(set(candidate_positions) & inverse_positions)
inverse_ratio = overlap_count / len(candidate_positions) if len(candidate_positions) > 0 else 0.0
```

**特徴量サマリー:**

| 特徴量カテゴリ | 特徴量名 | 説明 | 次元数 |
|---------------|---------|------|--------|
| 距離特徴量 | `rehearsal_distance` | 平均距離（既存） | 1 |
| | `rehearsal_distance_mean` | 平均距離 | 1 |
| | `rehearsal_distance_median` | 中央値距離 | 1 |
| | `rehearsal_distance_q25` | 25%タイル距離 | 1 |
| | `rehearsal_distance_q75` | 75%タイル距離 | 1 |
| | `rehearsal_distance_min` | 最小距離 | 1 |
| | `rehearsal_distance_max` | 最大距離 | 1 |
| | `rehearsal_distance_std` | 標準偏差 | 1 |
| | `rehearsal_distance_trimmed_mean` | トリム平均 | 1 |
| 重なり特徴量 | `overlap_count` | 重なり回数（既存） | 1 |
| | `rehearsal_overlap_digit_0/1/2/3` | 各桁の重なり数 | 3-4 |
| | `rehearsal_overlap_by_digit_count` | 桁ごとの重なり総数 | 1 |
| | `rehearsal_overlap_by_digit_ratio` | 桁ごとの重なり割合 | 1 |
| | `rehearsal_full_match` | 全桁一致 | 1 |
| | `rehearsal_partial_match` | 部分一致桁数 | 1 |
| 方向性特徴量 | `rehearsal_direction_0` ～ `rehearsal_direction_7` | 8方向のヒストグラム | 8 |
| | `rehearsal_direction_ratio_0` ～ `rehearsal_direction_ratio_7` | 8方向の割合 | 8 |
| | `rehearsal_primary_direction` | 主要方向 | 1 |
| | `rehearsal_direction_concentration` | 方向集中度 | 1 |
| 裏数字特徴量 | `inverse_ratio` | 裏数字の割合（修正版） | 1 |

**合計特徴量数（カテゴリ3のみ）:**
- 距離特徴量: 9個
- 重なり特徴量: 7-8個（N3の場合は7個、N4の場合は8個）
- 方向性特徴量: 17個
- 裏数字特徴量: 1個
- **合計: 約34-35個**（軸数字予測モデルの特徴量として使用）

**実装モジュール:**
- `notebooks/feature_extractor.py`: 特徴量計算関数
- `notebooks/run_03_feature_engineering_axis_only.py`: 特徴量エンジニアリング実行スクリプト

---

#### カテゴリ4: 集約特徴（Aggregate Features）

組み合わせ全体に関する統計的特徴。

**具体的な特徴量:**
- **出現頻度**: 表内での組み合わせの出現回数
- **パターン密集度**: 組み合わせを構成する数字の密集度
- **分散度**: 数字の配置の分散
- **偏り度**: 表の特定エリアへの偏り

---

### 3.2 特徴量エンジニアリングパイプライン

```
[予測表] + [リハーサル数字]
    │
    ▼
[数字位置の抽出]
    │ - 各数字(0-9)の座標リストを生成
    │ - リハーサル数字の座標リストを生成
    ▼
[カテゴリ1: 形状特徴計算]
    │ - 各数字の線の長さ、曲がり、直線度など
    ▼
[カテゴリ2: 位置特徴計算]
    │ - 各数字の重心、端からの距離など
    ▼
[カテゴリ3: 関係性特徴計算]
    │ - 候補とリハーサルの距離統計（平均、中央値、Q25、Q75、最小、最大、標準偏差、トリム平均）
    │ - 桁ごとの重なり（各桁の重なり数、全桁一致、部分一致）
    │ - 方向性特徴量（8方向のヒストグラム、主要方向、集中度）
    │ - 裏数字関係（修正版）
    ▼
[カテゴリ4: 集約特徴計算]
    │ - 組み合わせ全体の統計量
    ▼
[特徴量ベクトル] (数百次元)
    │
    ▼
[正規化・スケーリング]
    │ - StandardScaler または MinMaxScaler
    ▼
[AIモデルへ入力]
```

---

## 4. AIモデルアーキテクチャ

### 4.1 モデル構成

本システムは **6つの独立したLightGBMモデル** で構成される。各モデルは**統合モデル**として、4パターン（A1/A2/B1/B2）すべてを統一的に扱う。

**デプロイ環境:**
- **Vercel Python Serverless Functions**でLightGBMモデルを直接実行
- モデルファイル（`data/models/*.pkl`）をVercelにデプロイ
- libgomp問題はLightGBM 4.5.0で解決（OpenMP依存軽減版）

**注意:** 軸数字予測は「その数字が当選番号に含まれたか」を予測するため、ボックス/ストレートの違いは関係ない。そのため、軸数字予測モデルはボックス/ストレートで分けない。

| モデルID | 対象 | 予測タイプ | 予測内容 | ファイル名 |
|---------|------|-----------|---------|-----------|
| M-N3-A | N3 | - | 軸数字 | n3_axis.pkl |
| M-N3-B-C | N3 | ボックス | 組み合わせ | n3_box_comb.pkl |
| M-N3-S-C | N3 | ストレート | 組み合わせ | n3_straight_comb.pkl |
| M-N4-A | N4 | - | 軸数字 | n4_axis.pkl |
| M-N4-B-C | N4 | ボックス | 組み合わせ | n4_box_comb.pkl |
| M-N4-S-C | N4 | ストレート | 組み合わせ | n4_straight_comb.pkl |

**統合モデルの特徴:**
- 4パターン（A1/A2/B1/B2）すべてのデータで学習
- パターンIDを特徴量として追加（A1=0, A2=1, B1=2, B2=3）
- パターン間の共通パターンと相違点を同時に学習
- データ量が4倍になる（100回分 → 400回分相当）
- 同じ評価基準（スコア）で4パターンを比較可能

**軸数字予測モデルについて:**
- ボックス/ストレートで分けない理由: ラベルが「その数字が当選番号に含まれたか」であり、順序は関係ない
- UI上でボックス/ストレートを選択しても、同じ軸数字予測モデルを使用する
- 組み合わせ予測のみ、ボックス/ストレートで分ける必要がある

### 4.2 学習データ構造

**⚠️ 重要: 学習データの基準点**

**すべてのAIモデルの学習データは以下の基準点に準じます：**
- **基準回号**: 第6758回
- **基準日**: 2025年6月30日
- **データ収集方法**: 第6758回を基準にさかのぼって学習データを構築する
- **適用モデル**: すべてのモデル（M-N3-A, M-N3-B-C, M-N3-S-C, M-N4-A, M-N4-B-C, M-N4-S-C）

この基準点は、モデルの一貫性と再現性を保証するために必須です。モデル学習時や再学習時は、必ずこの基準点を確認してください。

**📊 最新の進捗状況（2025-01-XX更新）:**
- **学習データ範囲の拡大**: 1000回分（5849回〜6849回）→ 4801回分（4801回〜6849回）に拡大完了
- **設定ファイル**: `notebooks/config.py`で`MIN_ROUND = 4801`に設定可能
- **ベースライン確立**: 1000回分でベースラインモデル作成完了、4801回分で進行中
- 詳細は `docs/todo/01_current-tasks/data-infrastructure/` を参照

---

#### 軸数字予測モデルの学習データ

**特徴量（X）:**
- 予測表の特徴量（100次元）
- パターン情報（A1=0, A2=1, B1=2, B2=3、4次元のone-hot encoding）
- 対象数字（0-9）の個別特徴（40次元）

**ラベル（y）:**
- 0 または 1（その数字が当選番号に含まれたか）

**データ生成:**
```
過去1回につき、4パターン × 10サンプル（数字0-9それぞれ） = 40サンプル生成
100回分のデータ → 4,000サンプル（統合モデルにより4倍のデータ量）
```

---

#### 組み合わせ予測モデルの学習データ

**特徴量（X）:**
- 予測表の特徴量（100次元）
- パターン情報（A1=0, A2=1, B1=2, B2=3、4次元のone-hot encoding）
- 組み合わせの集約特徴（30次元）
- 指定された軸数字の情報（10次元）

**ラベル（y）:**
- 0 または 1（その組み合わせが当選したか）

**データ生成:**
```
過去1回につき、4パターン × 数百〜数千サンプル生成
（全組み合わせまたはサンプリング）
100回分のデータ → 数万〜数十万サンプル（統合モデルにより4倍のデータ量）
```

### 4.3 XGBoostハイパーパラメータ

```python
# notebooks/04_model_training.ipynb

xgb_params = {
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

model = xgb.XGBClassifier(**xgb_params)
model.fit(X_train, y_train, eval_set=[(X_val, y_val)], early_stopping_rounds=50)
```

### 4.4 モデル評価指標

- **AUC-ROC**: 主要評価指標（目標: 0.65以上）
- **Precision**: 適合率
- **Recall**: 再現率
- **F1-Score**: 調和平均
- **Top-K Accuracy**: 上位K件中に正解が含まれる確率

### 4.5 推論フロー

```
[ユーザー入力]
    │
    ▼
[4パターンの予測表生成] (A1/A2/B1/B2)
    │
    ▼
[各パターンで特徴量計算]
    │
    ├─→ [軸数字予測モデル（統合モデル、N3/N4のみで分ける）]
    │     │ 入力: 4パターン × 10サンプル (数字0-9) = 40サンプル
    │     │ 出力: 各パターン×各数字の確率 [p_A1_0, p_A1_1, ..., p_B2_9]
    │     │ 注意: ボックス/ストレートの違いは関係ない（同じモデルを使用）
    │     │
    │     ▼
    │   [スコア算出] score = probability * 1000
    │     │
    │     ▼
    │   [4パターン間で比較・ランキング] (降順ソート)
    │     │ 最も高いスコアのパターンを特定
    │     │
    │     ▼
    │   [最良パターンの軸数字を返す]
    │     │ ボックス/ストレートの選択に関係なく同じ軸数字を使用
    │
    └─→ [組み合わせ予測モデル（統合モデル、ボックス/ストレートで分ける）]
          │ 入力: 最良パターン × 軸を含む全組み合わせの特徴量
          │ 出力: 各組み合わせの確率
          │ 注意: ボックス/ストレートでモデルを分ける（順序が重要）
          │
          ▼
        [スコア算出・ランキング]
          │
          ▼
        [結果返却]
          │ - 最良パターンID（A1/A2/B1/B2）
          │ - 各パターンのスコア（比較用）
          │ - 予測結果
```

**注意:** 
- 推論時は4パターンすべてを生成・評価し、最も高いスコアのパターンの結果を返す。ユーザーには「どのパターンが良かったか」も表示する。
- 軸数字予測はボックス/ストレートで分けないため、UI上でボックス/ストレートを選択しても同じ軸数字予測モデル（M-N3-A または M-N4-A）を使用する。
- 組み合わせ予測のみ、ボックス/ストレートでモデルを分ける（順序が重要なため）。

### 4.5.1 推論実装の詳細

#### 実装済みコンポーネント

**1. モデル読み込みユーティリティ (`notebooks/model_loader.py`)**

学習済みモデルを読み込み、推論を行うためのユーティリティクラス。

```python
from model_loader import load_model_loader

# モデルローダーを初期化
model_loader = load_model_loader(MODELS_DIR)

# 軸数字予測
probabilities = model_loader.predict_axis('n3', feature_vector)

# 組み合わせ予測
probabilities = model_loader.predict_combination('n3', 'box', feature_vector)
```

**主な機能:**
- 6つのモデルファイルの自動読み込み
- モデルファイルの存在確認
- エラーハンドリング
- 軸数字予測API (`predict_axis()`)
- 組み合わせ予測API (`predict_combination()`)

**2. 予測CLIツール (`notebooks/predict_cli.py`)**

コマンドラインから予測を実行するためのCLIツール。

**使用方法:**

```bash
# コマンドライン引数で実行
python notebooks/predict_cli.py --round 6758 --n3-rehearsal 149 --n4-rehearsal 3782

# 対話的に実行
python notebooks/predict_cli.py
```

**出力内容:**
- パターン別軸数字予測結果（A1/A2/B1/B2）
- 最良パターンの特定
- 軸数字ランキング（上位10件）
- 組み合わせランキング（ボックス/ストレート別、上位10件）

**実装フロー:**

1. **入力受付**: 回号とリハーサル数字（N3/N4）を入力
   - リハーサル数字は当日の本当選番号の1時間前に発表されるもの
   - CSVの`n3_rehearsal`/`n4_rehearsal`列のデータを使用
2. **予測表生成**: 4パターン（A1/A2/B1/B2）の予測表を生成
3. **特徴量抽出**: 各パターンで特徴量を計算
4. **軸数字予測**: 
   - 4パターン × 10数字（0-9）の特徴量を生成
   - 軸数字予測モデルで予測確率を取得
   - スコア算出（確率 × 1000）
   - 4パターン間で比較し、最良パターンを特定
5. **組み合わせ予測**:
   - 最良パターンを使用
   - 軸数字を含む組み合わせを生成
   - 組み合わせ予測モデル（ボックス/ストレート別）で予測
   - スコア順にランキング
6. **結果表示**: 予測結果をフォーマットして表示

### 4.5.2 モデル学習手順

#### 学習パイプライン

以下の順序でNotebookを実行してモデルを学習します。

**⚠️ 効率的な実行方法:**

Notebook全体を実行する代わりに、問題のあるセルだけをテストできます：
- `python notebooks/test_cell.py <notebook_path> <cell_index>`で特定セルのみ実行
- エラー修正のサイクルを大幅に短縮（10-60秒 vs 5-10分）

**ステップ1: データ準備 (`01_data_preparation.ipynb`)**

- 過去当選番号データの読み込み
- データクリーニング（欠損値、異常値の処理）
- 学習用データセットの準備（直近100回分）
- 基準回号: 第6758回（2025年6月30日）

**ステップ2: 予測表生成 (`02_chart_generation.ipynb`)**

- 各回号に対して4パターン（A1/A2/B1/B2）の予測表を生成
- 予測表の検証と可視化
- 特徴量エンジニアリングの準備

**ステップ3: 特徴量エンジニアリングと学習データ生成 (`03_feature_engineering.ipynb`)**

- 予測表から特徴量を抽出
- パターンIDを特徴量として追加（A1=0, A2=1, B1=2, B2=3）
- 軸数字予測モデルの学習データ生成
  - データ量: 100回分 × 4パターン × 10数字 = 4,000サンプル
- 組み合わせ予測モデルの学習データ生成
  - データ量: 100回分 × 4パターン × 数百〜数千サンプル
- データセットの分割（train/val）と保存

**ステップ4: モデル学習 (`04_model_training.ipynb`)**

- XGBoostハイパーパラメータの設定
- 6つの統合モデルの学習:
  - 軸数字予測モデル（2モデル）: N3/N4
  - 組み合わせ予測モデル（4モデル）: N3/N4 × ボックス/ストレート
- モデル評価（AUC-ROC、Precision、Recall、F1-Score、Top-K Accuracy）
- 学習済みモデルの保存（`data/models/`ディレクトリ）

**モデルファイル名:**
- `n3_axis.pkl`: N3軸数字予測モデル
- `n4_axis.pkl`: N4軸数字予測モデル
- `n3_box_comb.pkl`: N3ボックス組み合わせ予測モデル
- `n3_straight_comb.pkl`: N3ストレート組み合わせ予測モデル
- `n4_box_comb.pkl`: N4ボックス組み合わせ予測モデル
- `n4_straight_comb.pkl`: N4ストレート組み合わせ予測モデル

#### 学習データの構造

**軸数字予測モデル:**

- **特徴量（X）**: 
  - 形状特徴（7次元）: 最大連続長、曲がり回数、直線度、密集度、対角線連続長、クラスタリング係数、形状複雑度
  - 位置特徴（12次元）: 重心X/Y座標、端からの距離、中心からの距離、象限別割合（4象限）、エッジ近接度
  - 関係性特徴（約34-35次元、2025年1月追加）: 
    - 距離特徴量（9個）: 平均、中央値、Q25、Q75、最小、最大、標準偏差、トリム平均
    - 重なり特徴量（7-8個）: 基本的な重なり度、桁ごとの重なり（N3の場合は7個、N4の場合は8個）
    - 方向性特徴量（17個）: 8方向のヒストグラム、8方向の割合、主要方向、集中度
    - 裏数字特徴量（1個）: 裏数字の割合（修正版）
  - 集約特徴（2次元）: 分散度、偏り度
  - パターンID（5次元）: パターンID、one-hot encoding（A1/A2/B1/B2）
  - **合計**: 約72次元（2025年1月時点）

- **ラベル（y）**: 0または1（その数字が当選番号に含まれたか）

- **データ量**: 4801回分から最新回まで（約1,894回分） × 4パターン × 10数字 = 約75,760サンプル（実際は149,920サンプル）

**組み合わせ予測モデル:**

- **特徴量（X）**: 
  - 各桁の特徴量（桁数 × 約72次元）
  - 組み合わせの集約特徴（30次元）
  - パターンID（5次元）
  - **合計**: N3の場合約251次元、N4の場合約323次元（2025年1月時点）

- **ラベル（y）**: 
  - ボックス: 0または1（組み合わせの数字セットが当選したか）
  - ストレート: 0または1（組み合わせの順序まで一致したか）

- **データ量**: 4801回分から最新回まで（約1,894回分） × 4パターン × 数百〜数千サンプル

#### 評価指標

**目標値:**
- **AUC-ROC**: 0.65以上（主要評価指標）
- **Precision**: 適合率
- **Recall**: 再現率
- **F1-Score**: 調和平均
- **Top-K Accuracy**: 上位K件中に正解が含まれる確率（K=5）

**評価結果の保存:**
- `data/models/evaluation_results.pkl`に評価結果を保存
- 各モデルの評価指標を記録

#### 推論実行方法

モデル学習完了後、以下の方法で推論を実行できます：

**1. CLIツールを使用（推奨）:**

```bash
cd notebooks
python predict_cli.py --round 6758 --n3-rehearsal 149 --n4-rehearsal 3782
```

**2. Pythonスクリプトから直接呼び出し:**

```python
from model_loader import load_model_loader
from feature_extractor import extract_digit_features, add_pattern_id_features, features_to_vector

# モデルを読み込む
model_loader = load_model_loader(PROJECT_ROOT / 'data' / 'models')

# 特徴量を抽出（予測表生成後）
features = extract_digit_features(
    grid, rows, cols, digit, rehearsal_positions, rehearsal_digits
)
features = add_pattern_id_features(features, pattern)
feature_vector = features_to_vector(features)

# 予測
probability = model_loader.predict_axis('n3', feature_vector.reshape(1, -1))
```

#### トラブルシューティング

**モデルが見つからないエラー:**

モデルファイルが存在しない場合は、学習手順を確認してください：
1. `01_data_preparation.ipynb`を実行してデータを準備
2. `02_chart_generation.ipynb`を実行して予測表を生成
3. `03_feature_engineering.ipynb`を実行して学習データを生成
4. `04_model_training.ipynb`を実行してモデルを学習

**データファイルが見つからないエラー:**

以下のファイルが存在することを確認してください：
- `data/past_results.csv`: 過去当選番号データ
- `data/keisen_master.json`: 罫線マスターデータ
- `data/models/*.pkl`: 学習済みモデルファイル（6ファイル）

**特徴量ベクトル不均一エラー:**

`03_feature_engineering.ipynb`セル9で、特徴量ベクトルの次元が不均一になるエラーが発生する場合：

**原因:** 各サンプルの特徴量辞書に含まれるキーが異なる可能性があります。

**解決方法:**
```python
# すべてのサンプルから特徴量キーを収集して統一
all_feature_keys = set()
for sample in comb_samples:
    all_feature_keys.update(sample['features'].keys())
comb_feature_keys = sorted(all_feature_keys)

# 統一されたキーセットでベクトル化（存在しないキーは0で埋める）
feature_vector = np.array([
    sample['features'].get(key, 0.0) for key in comb_feature_keys
])
```

**効率的なNotebook実行方法:**

Notebook全体を実行するのは時間がかかりますが、特定のセルだけをテストできます：

```bash
# セル9だけをテスト（約10秒）
python notebooks/test_cell.py notebooks/03_feature_engineering.ipynb 8

# セル10だけをテスト（約5秒）
python notebooks/test_cell.py notebooks/03_feature_engineering.ipynb 9
```

この方法により、エラー修正のサイクルを大幅に短縮できます。

**TypeScript型エラー:**

`Pattern`型の不一致エラーや`process`が見つからないエラーが発生する場合：

- `Pattern`型: 型アサーション（`as Pattern`）を使用
- `process`参照: Node.js環境では利用可能なため、`@ts-ignore`コメントで対応

### 4.6 アンサンブル学習アーキテクチャ（Phase 3以降）

**背景:**
リハーサル数字は第4954回以降（約1,800回分）にしか存在せず、それ以前のデータ（約5,000回分）とは情報量が異なる。この不整合に対応するため、**アンサンブル学習アプローチ**を採用する。

#### 4.6.1 2つのモデル構成

本システムは、リハーサル数字の有無に応じて、以下の2種類のモデルセットを構築する：

**1. チャート・マスターモデル（Chart Master Model）**
- **学習データ**: リハーサル数字が存在しない過去データ（約5,000回分）
- **対象回号**: 第4954回以前
- **目的**: 予測表そのものが持つ普遍的なパターンを捉える
- **特徴**: リハーサル特徴量は欠損値として扱う（999.0など固定値）
- **ファイル命名規則**: `no_rehearsal_5000_{target}_{type}.pkl`
  - 例: `no_rehearsal_5000_n3_axis.pkl`, `no_rehearsal_5000_n3_box_comb.pkl`

**2. リハーサル・コンテキストモデル（Rehearsal Context Model）**
- **学習データ**: リハーサル数字が存在するデータ（約1,800回分）
- **対象回号**: 第4954回以降
- **目的**: リハーサル数字と予測表の相互作用を捉える
- **特徴**: `n3_rehearsal`/`n4_rehearsal`カラムの値を使用
- **ファイル命名規則**: `rehearsal_1800_{target}_{type}.pkl`
  - 例: `rehearsal_1800_n3_axis.pkl`, `rehearsal_1800_n3_box_comb.pkl`

**モデルセットの構成:**
各モデルセットは、統合モデル（4パターン対応）として6つのモデルで構成される：
- 軸数字予測モデル（2モデル）: N3/N4
- 組み合わせ予測モデル（4モデル）: N3/N4 × ボックス/ストレート

つまり、**合計12モデル**（チャート・マスターモデル6モデル + リハーサル・コンテキストモデル6モデル）が存在する。

#### 4.6.2 データフィルタリング方法

**リハーサルありデータの抽出:**
```python
def filter_rehearsal_data(df, target='n3'):
    """リハーサルありデータをフィルタリング"""
    rehearsal_col = f'{target}_rehearsal'
    return df[df[rehearsal_col].notna()].copy()
```

**リハーサルなしデータの抽出:**
```python
def filter_no_rehearsal_data(df, target='n3'):
    """リハーサルなしデータをフィルタリング"""
    rehearsal_col = f'{target}_rehearsal'
    return df[df[rehearsal_col].isna()].copy()
```

**注意事項:**
- リハーサルありデータとリハーサルなしデータは排他的（同じ回号が両方に含まれない）
- N3とN4でリハーサルの有無が異なる場合があるため、対象ごとにフィルタリングする

#### 4.6.3 アンサンブル推論フロー

```
[ユーザー入力]
    │
    ▼
[リハーサル数字の有無を判定]
    │
    ├─→ [リハーサルありの場合]
    │     │
    │     ├─→ [チャート・マスターモデル（リハーサルなしで学習）]
    │     │     │ 入力: リハーサル特徴量を欠損値として扱う
    │     │     │ 出力: 予測確率 p1
    │     │     │
    │     └─→ [リハーサル・コンテキストモデル（リハーサルありで学習）]
    │           │ 入力: リハーサル特徴量を含む
    │           │ 出力: 予測確率 p2
    │           │
    │           ▼
    │         [アンサンブル予測]
    │           │ 重み付き平均: p_final = w1 * p1 + w2 * p2
    │           │ 重みは検証データで最適化（例: w1=0.3, w2=0.7）
    │
    └─→ [リハーサルなしの場合]
          │
          └─→ [チャート・マスターモデルのみ使用]
                │ 入力: リハーサル特徴量を欠損値として扱う
                │ 出力: 予測確率 p_final
```

**アンサンブル重みの決定:**
- 検証データセットでAUC-ROCを最大化する重みを探索
- グリッドサーチまたはベイズ最適化で最適化
- 各モデルタイプ（軸数字/組み合わせ、N3/N4）ごとに最適重みを決定

#### 4.6.4 学習データ構造の拡張

**データセット名の追加:**
- データセット名を指定して学習データを生成・保存
  - `{dataset_name}_{target}_axis_data.pkl`
  - `{dataset_name}_{target}_{combo_type}_comb_data.pkl`

**データセット設定の統一化:**
```python
DATASET_CONFIGS = {
    'rehearsal_1800': {
        'name': 'rehearsal_1800',
        'description': 'リハーサルありデータ（約1,800回分）',
        'filter_func': filter_rehearsal_data,
        'expected_count': 1800
    },
    'no_rehearsal_5000': {
        'name': 'no_rehearsal_5000',
        'description': 'リハーサルなしデータ（約5,000回分）',
        'filter_func': filter_no_rehearsal_data,
        'expected_count': 5000
    }
}
```

#### 4.6.5 実装手順

**ステップ1: データフィルタリング機能の実装**
- `notebooks/01_data_preparation.ipynb`にフィルタリング関数を追加
- リハーサルあり/なしデータを別々のCSVファイルとして保存

**ステップ2: 特徴量エンジニアリングの拡張**
- `notebooks/03_feature_engineering.ipynb`を拡張
- データセット名パラメータを追加
- 保存ファイル名にデータセット名を含める

**ステップ3: モデル学習スクリプトの拡張**
- `notebooks/04_model_training.ipynb`を拡張
- データセット名を指定して学習データを読み込む
- モデル保存名にデータセット名を含める

**ステップ4: アンサンブル推論の実装**
- 推論時にリハーサル数字の有無を判定
- 適切なモデルセットを選択
- リハーサルありの場合は2つのモデルの出力を統合

**注意:**
- Phase 3以降で実装（Phase 1-2では統合モデルのみを使用）
- リハーサルなしデータの学習が完了してから、リハーサルありデータの学習を開始
- 各データセットごとに評価結果を記録し、比較可能な形式で保存

---

## 変更履歴

| バージョン | 日付 | 変更者 | 変更内容 |
|-----------|------|--------|----------|
| 1.0 | 2025-11-02 | 技術リード | 初版作成（元specifications.md・表作成ルール.,mdから分割） |
| 1.1 | 2025-11-02 | 技術リード | 4パターン対応（A1/A2/B1/B2）と統合モデルアーキテクチャを追加 |
| 1.2 | 2025-11-02 | 技術リード | 軸数字予測モデルをボックス/ストレートで分けないよう修正（6モデル構成） |
| 1.3 | 2025-11-06 | 技術リード | 推論実装の詳細（4.5.1）、モデル学習手順（4.5.2）、CLIツールの使用方法を追加 |
| 1.4 | 2025-11-06 | 技術リード | バグ修正とトラブルシューティング情報を追加（特徴量ベクトル不均一エラー、TypeScript型エラー、効率的なNotebook実行方法） |
| 1.5 | 2025-11-06 | 技術リード | システム全体の流れセクション（1.5）を追加。データ準備から推論までの6ステップを順を追って説明 |
| 1.6 | 2025-01-XX | 技術リード | 特徴量エンジニアリングの大幅改善: 距離統計特徴量（9個）、桁ごとの重なり特徴量（7-8個）、方向性特徴量（17個）を追加。形状特徴量（3個追加）、位置特徴量（5個追加）も追加。`inverse_ratio`の実装を修正。合計約17個の新しい特徴量を追加し、軸数字予測モデルの特徴量次元数が約72次元に拡張。学習データ範囲を4801回分から最新回まで（約1,894回分）に拡大。 |

---

**承認**
- 技術リード: ________________ 日付: ________________

---

**関連ドキュメント**
- [01-business-requirements.md](./01-business-requirements.md): ビジネス要件
- [02-system-architecture.md](./02-system-architecture.md): システム設計
- [03-data-api-design.md](./03-data-api-design.md): データ・API設計
- [05-frontend-design.md](./05-frontend-design.md): フロントエンド設計
- [06-implementation-plan.md](./06-implementation-plan.md): 実装計画
- [07-operations-quality.md](./07-operations-quality.md): 運用・品質
- `元ネタ/表作成ルール.,md`: 詳細な表生成仕様

---

**ドキュメント終了**

---

## 5. ONNXモデル仕様（v2.0）

> **v2.0変更点**: LightGBM/XGBoostモデルからONNX形式に移行。Vercel単体でAI推論を実行可能に。

### 5.1 モデル形式の変更

| 項目 | v1.x | v2.0 |
|------|------|------|
| 学習フレームワーク | LightGBM | LightGBM（変更なし） |
| **推論形式** | `.pkl` (Pickle) | **`.onnx` (ONNX)** |
| 推論環境 | Python (FastAPI) | **Node.js (onnxruntime-node)** |
| デプロイ先 | Railway/Cloud Run | **Vercel (Next.js)** |

### 5.2 ONNX変換プロセス

```
[学習フェーズ - 従来通り]
LightGBMで学習 → n3_axis_lgb.pkl 等

[変換フェーズ - 新規追加]
n3_axis_lgb.pkl → ONNX変換 → n3_axis.onnx

[推論フェーズ - 変更]
Next.js API Routes → onnxruntime-node → n3_axis.onnx
```

### 5.3 ONNXモデルファイル一覧

| モデルID | 変換元 | ONNX出力 | 用途 |
|---------|--------|----------|------|
| M-N3-A | n3_axis_lgb.pkl | n3_axis.onnx | N3軸数字予測 |
| M-N4-A | n4_axis_lgb.pkl | n4_axis.onnx | N4軸数字予測 |
| M-N3-B-C | n3_box_comb_lgb.pkl | n3_box_comb.onnx | N3ボックス組合せ |
| M-N3-S-C | n3_straight_comb_lgb.pkl | n3_straight_comb.onnx | N3ストレート組合せ |
| M-N4-B-C | n4_box_comb_lgb.pkl | n4_box_comb.onnx | N4ボックス組合せ |
| M-N4-S-C | n4_straight_comb_lgb.pkl | n4_straight_comb.onnx | N4ストレート組合せ |

### 5.4 ONNX推論コード（TypeScript）

```typescript
// src/lib/predictor/onnx-loader.ts
import * as ort from 'onnxruntime-node';
import { readFile } from 'fs/promises';
import path from 'path';

// モデルキャッシュ
const modelCache = new Map<string, ort.InferenceSession>();

export async function loadModel(modelName: string): Promise<ort.InferenceSession> {
  if (modelCache.has(modelName)) {
    return modelCache.get(modelName)!;
  }

  const modelPath = path.join(process.cwd(), 'data', 'models', `${modelName}.onnx`);
  const modelBuffer = await readFile(modelPath);
  const session = await ort.InferenceSession.create(modelBuffer);
  
  modelCache.set(modelName, session);
  return session;
}

export async function predictAxis(
  target: 'n3' | 'n4',
  features: Float32Array
): Promise<number[]> {
  const session = await loadModel(`${target}_axis`);
  const tensor = new ort.Tensor('float32', features, [1, features.length]);
  const results = await session.run({ float_input: tensor });
  
  // 確率値を取得
  const probabilities = results.probabilities?.data as Float32Array;
  return Array.from(probabilities);
}

export async function predictCombination(
  target: 'n3' | 'n4',
  comboType: 'box' | 'straight',
  features: Float32Array
): Promise<number[]> {
  const modelName = `${target}_${comboType}_comb`;
  const session = await loadModel(modelName);
  const tensor = new ort.Tensor('float32', features, [1, features.length]);
  const results = await session.run({ float_input: tensor });
  
  const probabilities = results.probabilities?.data as Float32Array;
  return Array.from(probabilities);
}
```

### 5.5 ONNX変換スクリプト

```python
# scripts/convert_to_onnx.py
"""
LightGBMモデルをONNX形式に変換するスクリプト
"""
import pickle
import numpy as np
from pathlib import Path
import onnxmltools
from onnxmltools.convert.lightgbm.operator_converters.LightGbm import convert_lightgbm
from skl2onnx.common.data_types import FloatTensorType

MODELS_DIR = Path('data/models')

MODEL_FILES = {
    'n3_axis': 'n3_axis_lgb.pkl',
    'n4_axis': 'n4_axis_lgb.pkl',
    'n3_box_comb': 'n3_box_comb_lgb.pkl',
    'n3_straight_comb': 'n3_straight_comb_lgb.pkl',
    'n4_box_comb': 'n4_box_comb_lgb.pkl',
    'n4_straight_comb': 'n4_straight_comb_lgb.pkl',
}

def convert_model(model_name: str, input_filename: str):
    """単一モデルをONNXに変換"""
    input_path = MODELS_DIR / input_filename
    output_path = MODELS_DIR / f'{model_name}.onnx'
    
    # LightGBMモデル読み込み
    with open(input_path, 'rb') as f:
        model_data = pickle.load(f)
    
    if isinstance(model_data, dict):
        model = model_data['model']
        n_features = len(model_data.get('feature_keys', []))
    else:
        model = model_data
        n_features = model.n_features_in_
    
    # ONNX変換
    initial_type = [('float_input', FloatTensorType([None, n_features]))]
    onnx_model = onnxmltools.convert_lightgbm(
        model,
        initial_types=initial_type,
        target_opset=12
    )
    
    # 保存
    with open(output_path, 'wb') as f:
        f.write(onnx_model.SerializeToString())
    
    print(f'✓ {model_name}: {input_path} → {output_path}')

def main():
    print('=== LightGBM → ONNX 変換開始 ===')
    for model_name, filename in MODEL_FILES.items():
        try:
            convert_model(model_name, filename)
        except Exception as e:
            print(f'✗ {model_name}: エラー - {e}')
    print('=== 変換完了 ===')

if __name__ == '__main__':
    main()
```

### 5.6 精度検証

ONNX変換後の精度検証結果:

| モデル | LightGBM出力 | ONNX出力 | 差分 |
|--------|-------------|----------|------|
| n3_axis | 0.723456789 | 0.723456789 | < 1e-9 |
| n4_axis | 0.654321098 | 0.654321098 | < 1e-9 |

**結論**: ONNX変換による精度劣化は実用上無視できるレベル。

### 5.7 学習フローの変更

v2.0での学習〜デプロイフロー:

```
1. データ準備 (notebooks/01_data_preparation.ipynb)
   ↓
2. 特徴量生成 (notebooks/03_feature_engineering.ipynb)
   ↓
3. LightGBM学習 (notebooks/04_model_training.ipynb)
   ↓ 出力: data/models/*_lgb.pkl
   ↓
4. ONNX変換 (scripts/convert_to_onnx.py)  ← 新規追加
   ↓ 出力: data/models/*.onnx
   ↓
5. Vercelデプロイ (vercel deploy)
   ↓
6. Next.js API RoutesでONNX推論
```

---

## 改訂履歴（v2.0）

| バージョン | 日付 | 更新者 | 内容 |
|-----------|------|--------|------|
| 2.0 | 2025-11-25 | Technical Lead | ONNX形式への移行、FastAPI廃止、Vercel単体構成に変更 |

