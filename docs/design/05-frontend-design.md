# フロントエンド設計書 v1.0

**Document Management Information**
- Document ID: DOC-05
- Version: 1.0
- Created: 2025-11-02
- Last Updated: 2025-11-02
- Status: Confirmed
- Approver: Technical Lead

---

## 📋 目次

1. [ドキュメント目的と適用範囲](#1-ドキュメント目的と適用範囲)
2. [コンポーネント階層](#2-コンポーネント階層)
3. [状態管理](#3-状態管理)
4. [UI/UXガイドライン](#4-uiuxガイドライン)

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
│   ├── RoundInputPage (/predict/input)
│   │   ├── RoundInput
│   │   └── NextButton
│   │
│   ├── RehearsalInputPage (/predict/rehearsal)
│   │   ├── N4RehearsalInput
│   │   ├── N3RehearsalInput
│   │   └── ExecutePredictionButton
│   │
│   └── ResultPage (/predict/result)
│       ├── LoadingState
│       ├── ErrorState
│       └── ResultView
│           ├── Tabs (N3/N4)
│           ├── SubTabs (Box/Straight)
│           ├── ModeSwitch (Axis/Total)
│           ├── AxisCandidates
│           │   └── AxisAccordion[]
│           ├── TotalRanking
│           └── ManualAxisInput
```

---

## 3. 状態管理

### 3.1 Redux状態構造（MVP版はuseStateで代替可）

```typescript
// src/store/slices/prediction-slice.ts

interface PredictionState {
  // 入力状態
  roundNumber: number | null;
  n3Rehearsal: string;
  n4Rehearsal: string;
  
  // API状態
  loading: boolean;
  error: string | null;
  
  // 予測結果
  result: PredictionResult | null;
  
  // UI状態
  activeTarget: 'n3' | 'n4';
  activePredictionType: 'box' | 'straight';
  displayMode: 'axis' | 'total';
}
```

---

## 4. UI/UXガイドライン

### 4.1 モバイルファースト設計

- **最小画面サイズ**: 320px × 568px（iPhone SE）
- **タッチターゲット**: 最小48px × 48px
- **フォントサイズ**: 本文14px、補助12px
- **コントラスト比**: WCAG 2.1 AA準拠（4.5:1以上）

### 4.2 カラーパレット

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

### 4.3 タイポグラフィ

- **見出し1**: 24px / Bold
- **見出し2**: 20px / Bold
- **見出し3**: 18px / SemiBold
- **本文**: 14px / Regular
- **補助**: 12px / Regular
- **フォント**: Inter, Noto Sans JP

### 4.4 アニメーション

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

## 変更履歴

| バージョン | 日付 | 変更者 | 変更内容 |
|-----------|------|--------|----------|
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

