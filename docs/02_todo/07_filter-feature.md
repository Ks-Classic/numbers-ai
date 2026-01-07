# 軸数字・削除数字フィルター機能 実装TODO

**作成日**: 2026-01-07
**ステータス**: ✅ 実装完了
**関連設計書**: `docs/01_design/05-frontend-design.md`

---

## 📋 概要

当選番号予測結果に対して、以下のフィルター機能を追加する：
1. **軸数字フィルター**: 選択した軸数字を含む番号のみ表示（AND/OR条件）
2. **削除数字フィルター**: 指定した数字を含む番号を除外

両フィルターはAND条件で同時適用される。

---

## 🏗️ 実装タスク

### Phase 1: 状態管理の拡張

- [x] **1.1 Zustand storeにフィルター状態を追加**
  - ファイル: `src/lib/store.ts`
  - 追加する状態:
    ```typescript
    filterState: {
      selectedAxes: number[];
      axisCondition: 'AND' | 'OR';
      excludedNumbers: number[];
    }
    ```
  - 追加するアクション:
    - `toggleFilterAxis(axis: number)`
    - `setAxisCondition(condition: 'AND' | 'OR')`
    - `addExcludedNumber(num: number)`
    - `removeExcludedNumber(num: number)`
    - `clearFilters()`

### Phase 2: フィルターユーティリティ関数

- [x] **2.1 フィルターロジックの実装**
  - ファイル: `src/lib/utils/prediction-filter.ts`（新規作成）
  - 関数:
    - `filterByAxes(predictions, axes, condition)`
    - `filterByExclusion(predictions, excluded)`
    - `applyFilters(predictions, filterState)` - 統合フィルター

### Phase 3: UIコンポーネント

- [x] **3.1 AxisPredictionSection コンポーネント**
  - ファイル: `src/components/features/AxisPredictionSection.tsx`（新規作成）
  - 機能:
    - AI予測軸数字をチップ形式で表示
    - タップで選択/解除
    - スコア表示
    - 「＋軸を追加」ボタン

- [x] **3.2 FilterPanel コンポーネント**
  - ファイル: `src/components/features/FilterPanel.tsx`（新規作成）
  - 機能:
    - 折り畳み可能なパネル
    - 選択中の軸数字表示（バッジ形式、個別削除可）
    - AND/ORトグル
    - 削除数字表示
    - フィルター効果（件数表示）

- [x] **3.3 NumberInputModal コンポーネント**
  - ファイル: `src/components/features/NumberInputModal.tsx`（新規作成）
  - 機能:
    - 0-9の数字グリッド
    - 複数選択対応
    - 選択済みハイライト
    - 軸追加/削除数字追加の両用途

### Phase 4: ResultPage の更新

- [x] **4.1 ResultPageの改修**
  - ファイル: `src/app/predict/result/page.tsx`
  - 変更内容:
    - 「全予測一覧」タブを削除
    - AxisPredictionSection を追加
    - FilterPanel を追加
    - フィルター適用済み結果表示
    - リアルタイム更新

### Phase 5: スタイリング

- [x] **5.1 コンポーネントスタイル**
  - チップコンポーネント（選択状態のスタイル）
  - フィルターパネル（折り畳みアニメーション）
  - NumberInputModal（グリッドレイアウト）

---

## 📁 ファイル構成

```
src/
├── lib/
│   ├── store.ts                          # 更新：filterState追加
│   └── utils/
│       └── prediction-filter.ts          # 新規：フィルターロジック
│
├── components/
│   └── features/
│       ├── AxisPredictionSection.tsx     # 新規：軸数字予測セクション
│       ├── FilterPanel.tsx               # 新規：フィルター設定パネル
│       └── NumberInputModal.tsx          # 新規：数字入力モーダル
│
└── app/
    └── predict/
        └── result/
            └── page.tsx                  # 更新：フィルター機能統合
```

---

## 🧪 テスト項目

- [x] 軸数字選択でフィルターが正しく適用される
- [x] AND条件：全ての軸を含む番号のみ表示
- [x] OR条件：いずれかの軸を含む番号を表示
- [x] 削除数字で番号が正しく除外される
- [x] 軸フィルターと削除フィルターが同時に動作する
- [x] フィルター解除で元の結果に戻る
- [x] N3/N4タブ切り替え時にフィルター状態がリセットされる

---

## 📊 完了基準

- [x] 全てのUIコンポーネントが実装されている
- [x] フィルターがリアルタイムで反映される
- [x] モバイルで操作しやすいUI
- [x] エッジケース（軸0件、全除外など）の処理
