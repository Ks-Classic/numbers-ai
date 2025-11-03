# アルゴリズム・AI設計書 v1.2

**Document Management Information**
- Document ID: DOC-04
- Version: 1.2
- Created: 2025-11-02
- Last Updated: 2025-11-02
- Status: Confirmed
- Approver: Technical Lead

---

## 📋 目次

1. [ドキュメント目的と適用範囲](#1-ドキュメント目的と適用範囲)
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
    - source_list に 0 が含まれていなければ 0 を1つ追加（0以外の欠番は追加しない）
  - 昇順ソート → nums

ステップ3: メイン行の組み立て
  - mainRows = []
  - while nums が空でない:
    - uniqueDigits = nums のユニーク値（昇順）
    - if uniqueDigits.length >= 4:
      - members = uniqueDigits[0..3]
      - newRow = nums から members の各値を1個ずつ取り出して配列化
      - mainRows.push(newRow)
      - nums から newRow で使った数字を削除
    - else:
      - newRow = uniqueDigits の全要素
      - while newRow.length < 4:
        - newRow.push(max(uniqueDigits))
      - mainRows.push(newRow)
      - nums から newRow で使った数字を削除

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

候補数字とリハーサル数字の関係性に関する特徴。

**具体的な特徴量:**
- **リハーサルとの距離**: 候補ラインとリハーサルラインの平均距離
- **重なり度**: 候補とリハーサルが同じ位置にある回数
- **角度**: 候補ラインとリハーサルラインの角度差
- **裏数字関係**: 候補がリハーサルの裏数字である割合

**計算例:**

```typescript
function calculateRehearsalDistance(
  candidatePositions: {x: number, y: number}[],
  rehearsalPositions: {x: number, y: number}[]
): number {
  if (candidatePositions.length === 0 || rehearsalPositions.length === 0) {
    return Infinity;
  }
  
  let totalDistance = 0;
  for (const cPos of candidatePositions) {
    let minDist = Infinity;
    for (const rPos of rehearsalPositions) {
      const dist = Math.sqrt(
        Math.pow(cPos.x - rPos.x, 2) + Math.pow(cPos.y - rPos.y, 2)
      );
      minDist = Math.min(minDist, dist);
    }
    totalDistance += minDist;
  }
  
  return totalDistance / candidatePositions.length;
}
```

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
    │ - 候補とリハーサルの距離、重なりなど
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

本システムは **6つの独立したXGBoostモデル** で構成される。各モデルは**統合モデル**として、4パターン（A1/A2/B1/B2）すべてを統一的に扱う。

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

---

## 変更履歴

| バージョン | 日付 | 変更者 | 変更内容 |
|-----------|------|--------|----------|
| 1.0 | 2025-11-02 | 技術リード | 初版作成（元specifications.md・表作成ルール.,mdから分割） |
| 1.1 | 2025-11-02 | 技術リード | 4パターン対応（A1/A2/B1/B2）と統合モデルアーキテクチャを追加 |
| 1.2 | 2025-11-02 | 技術リード | 軸数字予測モデルをボックス/ストレートで分けないよう修正（6モデル構成） |

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

