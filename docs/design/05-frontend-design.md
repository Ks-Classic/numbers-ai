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
    └── ResultView
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
  
  // アクション
  setSessionData: (data: Partial<PredictionState['currentSession']>) => void;
  setAxisCandidates: (candidates: AxisCandidate[]) => void;
  setFinalPredictions: (predictions: ...) => void;
  setN3Data: (candidates: AxisCandidate[], predictions: ...) => void;
  setN4Data: (candidates: AxisCandidate[], predictions: ...) => void;
  toggleAxis: (axis: number) => void;
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

- [ ] ナビゲーションの実装
- [ ] 404ページの実装
- [ ] エラーページの実装
- [ ] 画面遷移アニメーションの実装
- [ ] React Queryの導入（オプション）

---

## 変更履歴

| バージョン | 日付 | 変更者 | 変更内容 |
|-----------|------|--------|----------|
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
