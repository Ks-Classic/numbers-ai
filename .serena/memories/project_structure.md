# プロジェクト構造の詳細

## ルートディレクトリ
```
numbers-ai/
├── src/                    # ソースコード
├── api/                    # FastAPIサーバー
├── data/                   # データファイル
├── notebooks/              # Jupyter Notebooks
├── docs/                   # ドキュメント
├── scripts/                # スクリプト
├── public/                 # 静的ファイル
└── .serena/                # Serena設定
```

## src/ ディレクトリ構造
```
src/
├── app/                    # Next.js App Router
│   ├── api/                # API Routes
│   │   ├── predict/        # 予測API
│   │   ├── test-chart/     # テストAPI
│   │   └── test-data-loader/ # データローダーテスト
│   ├── predict/            # 予測画面
│   │   ├── loading/        # ローディング画面
│   │   ├── axis/           # 軸数字表示画面
│   │   ├── rehearsal/      # リハーサル入力画面
│   │   └── result/         # 結果表示画面
│   ├── history/            # 履歴画面
│   ├── statistics/         # 統計画面
│   └── settings/           # 設定画面
├── components/             # Reactコンポーネント
│   ├── features/           # 機能コンポーネント
│   ├── layouts/            # レイアウトコンポーネント
│   ├── shared/             # 共有コンポーネント
│   └── ui/                 # UIコンポーネント（Radix UI）
├── lib/                    # ビジネスロジック
│   ├── chart-generator/    # 予測表生成
│   ├── data-loader/        # データ読み込み
│   ├── predictor/          # 予測処理
│   ├── store.ts            # Zustandストア
│   └── utils.ts            # ユーティリティ
└── types/                  # TypeScript型定義
    ├── chart.ts            # 予測表型
    ├── prediction.ts       # 予測結果型
    └── statistics.ts       # 統計型
```

## 主要ファイル

### フロントエンド
- `src/app/page.tsx`: ホーム画面
- `src/app/predict/page.tsx`: 予測入力画面
- `src/app/predict/loading/page.tsx`: ローディング画面
- `src/app/predict/axis/page.tsx`: 軸数字表示画面
- `src/lib/chart-generator/index.ts`: 予測表生成ロジック
- `src/lib/predictor/predictor.ts`: 予測処理実装
- `src/lib/store.ts`: Zustandストア

### バックエンド
- `api/main.py`: FastAPIアプリケーション
- `api/run.py`: サーバー起動スクリプト
- `src/app/api/predict/route.ts`: Next.js API Route

### AI/ML
- `notebooks/01_data_preparation.ipynb`: データ前処理
- `notebooks/02_chart_generation.ipynb`: 予測表生成
- `notebooks/03_feature_engineering.ipynb`: 特徴量エンジニアリング
- `notebooks/04_model_training.ipynb`: モデル学習
- `notebooks/chart_generator.py`: 予測表生成モジュール
- `notebooks/feature_extractor.py`: 特徴量抽出モジュール
- `notebooks/model_loader.py`: モデル読み込みユーティリティ

### データ
- `data/past_results.csv`: 過去当選番号データ（約6,700回分）
- `data/keisen_master.json`: 罫線マスターデータ
- `data/models/`: 学習済みモデル（6つの.pklファイル）
- `data/train_data_100.csv`: 学習用データ（直近100回分）

## 主要シンボル構造

### predictor.ts
- `predictAxis`: 軸数字予測関数
- `predictCombination`: 組み合わせ予測関数
- `fetchFromFastAPI`: FastAPIへのリクエスト関数

### chart-generator/index.ts
- `generateChart`: 予測表生成メイン関数
- `buildMainRows`: メイン行組み立て関数
- `applyVerticalInverse`: 縦パス裏数字適用
- `applyHorizontalInverse`: 横パス裏数字適用
- `applyRemainingCopy`: 余りマスルール適用
- `placeCenterZero`: 中心0配置（A2/B2のみ）

### store.ts
- `usePredictionStore`: 予測状態管理ストア
- `useHistoryStore`: 履歴状態管理ストア
- `useStatisticsStore`: 統計状態管理ストア