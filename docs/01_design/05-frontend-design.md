# フロントエンド設計書 v1.1

**Document Management Information**
- Document ID: DOC-05
- Version: 1.1
- Created: 2025-11-02
- Last Updated: 2025-01-XX
- Status: Confirmed
- Approver: Technical Lead

---

## 📋 目次

1. [ドキュメント目的と適用範囲](#1-ドキュメント目的と適用範囲)
2. [コンポーネント階層](#2-コンポーネント階層)
3. [状態管理](#3-状態管理)
4. [UI/UXガイドライン](#4-uiuxガイドライン)
5. [実装状況](#5-実装状況)

---

## 1. ドキュメント目的と適用範囲

### 1.1 目的
本ドキュメントは、ナンバーズAI予測システムの**フロントエンド設計**を定義する。コンポーネント構造、状態管理、UI/UXガイドラインを明確にすることで、一貫性のあるユーザー体験を提供する。

### 1.2 対象読者
- フロントエンドエンジニア
- UI/UXデザイナー
- フルスタックエンジニア

### 1.3 関連ドキュメント
- [01-business-requirements.md](./01-business-requirements.md): ビジネス要件
- [03-data-api-design.md](./03-data-api-design.md): データ・API設計
- `UIイメージ.md`: 詳細なUI設計

---

## 2. コンポーネント階層

```
App
├── Layout
│   ├── Header
│   └── Navigation
│
├── HomePage (/)
│   └── StartPredictionButton
│
├── PredictPage (/predict)
│   ├── RoundInputPage (/predict)
│   │   ├── RoundInput
│   │   └── NextButton
│   │
│   ├── RehearsalInputPage (/predict/rehearsal)
│   │   ├── N4RehearsalInput
│   │   ├── N3RehearsalInput
│   │   └── ExecutePredictionButton
│   │
│   ├── LoadingPage (/predict/loading)
│   │   ├── LoadingState
│   │   ├── ProgressBar
│   │   ├── ProcessingSteps
│   │   └── ErrorState
│   │
│   └── AxisPage (/predict/axis)
│       ├── Tabs (N3/N4)
│       ├── SubTabs (Box/Straight)
│       ├── ModeSwitch (Axis/Total)
│       ├── AxisCandidates
│       │   └── AxisAccordion[] (最大5位まで)
│       ├── TotalRanking (最大20位まで)
│       └── ManualAxisInput (手動指定軸数字での予測)
│
└── ResultPage (/predict/result)
    ├── Tabs (N3/N4)
    ├── AxisPredictionSection          ← AI軸数字予測表示
    │   ├── AxisCandidateChips[]       ← タップで選択
    │   └── AddAxisButton              ← 軸を手動追加
    ├── FilterPanel                    ← フィルター設定パネル
    │   ├── SelectedAxesDisplay        ← 選択中の軸表示
    │   ├── AxisConditionToggle        ← AND/OR切替
    │   ├── ExcludedNumbersDisplay     ← 削除数字表示
    │   └── AddExclusionButton         ← 削除数字追加
    ├── SubTabs (Box/Straight)
    ├── FilteredResultList             ← フィルター適用済み結果
    └── NumberInputModal               ← 数字入力モーダル
```

---

## 3. 状態管理

### 3.1 Zustand状態構造

```typescript
// src/lib/store.ts

interface PredictionState {
  // 入力状態
  currentSession: {
    sessionId: string | null;
    roundNumber: number;
    numbersType: 'N3' | 'N4';
    patternType: Pattern; // 'A1' | 'A2' | 'B1' | 'B2'
    rehearsalN3: string;
    rehearsalN4: string;
    selectedAxes: number[];
  };
  
  // 予測結果（現在選択中のnumbersTypeに対応）
  axisCandidates: AxisCandidate[];
  finalPredictions: {
    straight: PredictionItem[];
    box: PredictionItem[];
  } | null;
  
  // N3/N4別のデータを保存
  n3AxisCandidates: AxisCandidate[];
  n3FinalPredictions: {
    straight: PredictionItem[];
    box: PredictionItem[];
  } | null;
  n4AxisCandidates: AxisCandidate[];
  n4FinalPredictions: {
    straight: PredictionItem[];
    box: PredictionItem[];
  } | null;
  
  // フィルター状態
  filterState: {
    selectedAxes: number[];          // 選択した軸数字（AI予測から or 手動追加）
    axisCondition: 'AND' | 'OR';     // 軸条件
    excludedNumbers: number[];       // 削除数字
  };
  
  // アクション
  setSessionData: (data: Partial<PredictionState['currentSession']>) => void;
  setAxisCandidates: (candidates: AxisCandidate[]) => void;
  setFinalPredictions: (predictions: ...) => void;
  setN3Data: (candidates: AxisCandidate[], predictions: ...) => void;
  setN4Data: (candidates: AxisCandidate[], predictions: ...) => void;
  toggleAxis: (axis: number) => void;
  
  // フィルターアクション
  toggleFilterAxis: (axis: number) => void;           // 軸を選択/解除
  setAxisCondition: (condition: 'AND' | 'OR') => void; // AND/OR切替
  addExcludedNumber: (num: number) => void;           // 削除数字追加
  removeExcludedNumber: (num: number) => void;        // 削除数字解除
  clearFilters: () => void;                           // フィルターリセット
  resetSession: () => void;
}
```

### 3.2 状態管理の特徴

- **N3/N4別データ保存**: 各予測タイプのデータを別々に保存し、タブ切り替え時に適切なデータを表示
- **自動同期**: `numbersType`が変更された場合、対応するデータを`axisCandidates`と`finalPredictions`に自動設定
- **パターン管理**: 最良パターン（A1/A2/B1/B2）を`patternType`として保存

---

## 4. UI/UXガイドライン

### 4.1 モバイルファースト設計

- **最小画面サイズ**: 320px × 568px（iPhone SE）
- **タッチターゲット**: 最小48px × 48px
- **フォントサイズ**: 本文14px、補助12px
- **コントラスト比**: WCAG 2.1 AA準拠（4.5:1以上）

### 4.2 スコア表示規則

- **小数点表示**: 全てのスコアは小数点1位までの四捨五入で表示
- **表示方法**: `toFixed(1)`を使用して統一

### 4.3 ランキング表示規則

- **総合ランキング**: 最大20位まで表示
- **軸数字ランキング**: 最大5位まで表示
- **軸数字内の番号**: 最大10位まで表示

### 4.4 データフィルタリング規則

- **軸数字内の番号**: 各軸数字に対して、その軸数字を含む組み合わせのみを表示
- **ボックス/ストレート切り替え**: タブ切り替え時に適切なデータを表示

### 4.5 手動指定軸数字機能

- **機能**: 任意の軸数字（0-9）を入力して、その軸数字を含む組み合わせのスコアを算出
- **動作フロー**:
  1. まず既存の候補からフィルタリングを試みる（高速）
  2. 既存の候補にない場合、APIを呼び出して新しく予測を実行
  3. 結果をスコア順にソートして表示（最大10位まで）

### 4.6 カラーパレット

```css
:root {
  /* Primary Colors */
  --primary-blue: #0070f3;
  --primary-dark: #0051cc;
  --primary-light: #3291ff;
  
  /* Secondary Colors */
  --secondary-gray: #666666;
  --secondary-light: #f5f5f5;
  
  /* Semantic Colors */
  --success-green: #00c853;
  --warning-yellow: #ffc107;
  --error-red: #d32f2f;
  
  /* Backgrounds */
  --bg-main: #ffffff;
  --bg-card: #f9fafb;
  --bg-hover: #e5e7eb;
}
```

### 4.7 タイポグラフィ

- **見出し1**: 24px / Bold
- **見出し2**: 20px / Bold
- **見出し3**: 18px / SemiBold
- **本文**: 14px / Regular
- **補助**: 12px / Regular
- **フォント**: Inter, Noto Sans JP

### 4.8 アニメーション

```typescript
// Framer Motion設定

const fadeIn = {
  initial: { opacity: 0, y: 20 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.3 }
};

const slideIn = {
  initial: { x: -100, opacity: 0 },
  animate: { x: 0, opacity: 1 },
  transition: { type: 'spring', stiffness: 100 }
};
```

### 4.9 軸数字フィルター機能

**概要**: AI予測された軸数字を選択し、当選番号候補をフィルタリングする機能

**フロー**:
1. AI予測結果から軸数字候補を表示（スコア順）
2. ユーザーが軸数字をタップして選択（複数選択可）
3. 選択した軸数字で当選番号候補をフィルタリング
4. AND/OR条件を選択可能

**条件ロジック**:
- **AND**: 選択した全ての軸数字を含む番号のみ表示
- **OR**: 選択した軸数字のいずれかを含む番号を表示

```typescript
// フィルタリング例
const filterByAxes = (predictions: string[], axes: number[], condition: 'AND' | 'OR') => {
  return predictions.filter(num => {
    const digits = num.split('').map(Number);
    if (condition === 'AND') {
      return axes.every(axis => digits.includes(axis));
    } else {
      return axes.some(axis => digits.includes(axis));
    }
  });
};
```

### 4.10 削除数字フィルター機能

**概要**: 指定した数字を含む予測候補を除外する機能

**フロー**:
1. ユーザーが削除したい数字を追加（複数追加可）
2. その数字を含む全ての候補を結果から除外
3. 軸数字フィルターとANDで同時適用

```typescript
// フィルタリング例
const filterByExclusion = (predictions: string[], excluded: number[]) => {
  return predictions.filter(num => {
    const digits = num.split('').map(Number);
    return !excluded.some(ex => digits.includes(ex));
  });
};
```

### 4.11 フィルター適用順序

フィルターは以下の順序で適用される（AND条件）:

```
元の予測結果
    │
    ▼
┌─────────────────────┐
│ 1. 軸数字フィルター  │  ← AND/OR条件で適用
└─────────────────────┘
    │
    ▼
┌─────────────────────┐
│ 2. 削除数字フィルター│  ← 軸フィルター結果から除外
└─────────────────────┘
    │
    ▼
フィルター適用後の結果
```

### 4.12 数字入力モーダル

**UI仕様**:
- 0-9の数字グリッド表示
- タップで選択/解除
- 選択済みの数字はハイライト表示
- 「完了」ボタンで閉じる

**用途**:
- 軸数字の追加（AI予測外の軸を手動追加）
- 削除数字の追加

---

## 5. 実装状況

### 5.1 完了した機能 ✅

- ✅ ホーム画面の実装
- ✅ 回号入力画面の実装
- ✅ リハーサル数字入力画面の実装
- ✅ ローディング画面の実装（API呼び出し、エラーハンドリング）
- ✅ 軸数字表示画面の実装
  - ✅ N3/N4タブ切り替え機能
  - ✅ ボックス/ストレート切り替え機能
  - ✅ 軸数字内の番号フィルタリング
  - ✅ 手動指定軸数字での予測機能
  - ✅ スコア表示の小数点1位までの四捨五入
  - ✅ ランキング表示の上限設定
- ✅ Zustandストアの実装（N3/N4別データ対応）
- ✅ API連携の実装（FastAPI呼び出し、エラーハンドリング）
- ✅ エラーハンドリングの実装（ネットワーク、タイムアウト、サーバーエラー）

### 5.2 未実装の機能

- [ ] **軸数字フィルター機能**
  - [ ] AI予測軸数字の選択UI（AxisCandidateChips）
  - [ ] 軸追加ボタン・モーダル
  - [ ] AND/OR条件トグル
  - [ ] 選択状態の管理（Zustand filterState）
- [ ] **削除数字フィルター機能**
  - [ ] 削除数字追加UI
  - [ ] 数字入力モーダル（NumberInputModal）
  - [ ] 削除数字の管理（Zustand filterState）
- [ ] **フィルター適用ロジック**
  - [ ] 軸数字フィルター（AND/OR）
  - [ ] 削除数字フィルター
  - [ ] フィルター結果のリアルタイム更新
- [ ] ナビゲーションの実装
- [ ] 404ページの実装
- [ ] エラーページの実装
- [ ] 画面遷移アニメーションの実装
- [ ] React Queryの導入（オプション）

---

## 変更履歴

| バージョン | 日付 | 変更者 | 変更内容 |
|-----------|------|--------|----------|
| 1.2 | 2026-01-07 | 技術リード | 軸数字フィルター・削除数字フィルター機能仕様を追加 |
| 1.1 | 2025-01-XX | 技術リード | 実装状況セクションを追加、状態管理構造を更新 |
| 1.0 | 2025-11-02 | 技術リード | 初版作成（元specifications.mdから分割） |

---

**承認**
- 技術リード: ________________ 日付: ________________

---

**関連ドキュメント**
- [01-business-requirements.md](./01-business-requirements.md): ビジネス要件
- [02-system-architecture.md](./02-system-architecture.md): システム設計
- [03-data-api-design.md](./03-data-api-design.md): データ・API設計
- [04-algorithm-ai.md](./04-algorithm-ai.md): アルゴリズム・AI
- [06-implementation-plan.md](./06-implementation-plan.md): 実装計画
- [07-operations-quality.md](./07-operations-quality.md): 運用・品質
- `UIイメージ.md`: 詳細なUI設計

---

**ドキュメント終了**
