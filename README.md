# Numbers-AI — AI-Powered Numbers Prediction System

> A production-grade AI prediction system for Japanese Numbers lottery (Numbers 3/4),  
> combining proprietary domain theory with multi-model XGBoost ensemble and full-stack web application.

[![TypeScript](https://img.shields.io/badge/TypeScript-5.3-blue)](https://www.typescriptlang.org/)
[![Next.js](https://img.shields.io/badge/Next.js-14.2-black)](https://nextjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green)](https://fastapi.tiangolo.com/)
[![XGBoost](https://img.shields.io/badge/XGBoost-2.0-orange)](https://xgboost.readthedocs.io/)
[![Python](https://img.shields.io/badge/Python-3.10-yellow)](https://www.python.org/)
[![React](https://img.shields.io/badge/React-18.3-cyan)](https://react.dev/)

---

## System Scale

| Metric | Value |
|--------|-------|
| Total TypeScript/TSX codebase | **12,200+ lines** |
| Total Python codebase | **30,000+ lines** |
| React UI components | **17 components** |
| API route handlers | **16 endpoints** |
| ML training/analysis scripts | **14,900+ lines across 30+ scripts** |
| Trained model artifacts | **103 files** (incl. 79 vectorized batch files) |
| Training datasets | **6 dedicated datasets** (N3/N4 × axis/box/straight) |
| Feature dimensions | **70+ engineered features** |
| Prediction models | **6 specialized XGBoost models** |
| Design documents | **100+ pages** |
| Data files | **193 files** (CSV, JSON, PKL) |
| Dual-language implementation | TypeScript (Web) + Python (ML) |

---

## Architecture Overview

```
┌──────────────────────────────────────────────────────────────┐
│                    Numbers-AI Architecture                     │
│                                                               │
│  ┌─────────────┐    ┌──────────────┐    ┌──────────────────┐ │
│  │  Next.js     │    │  Next.js     │    │  FastAPI         │ │
│  │  Frontend    │───▶│  API Routes  │───▶│  ML Inference    │ │
│  │  (React/TS)  │    │  (16 routes) │    │  Server (Python) │ │
│  │  12,200+ LoC │    │              │    │  30,000+ LoC     │ │
│  └─────────────┘    └──────┬───────┘    └────────┬─────────┘ │
│                            │                      │           │
│                     ┌──────▼──────────────────────▼────────┐ │
│                     │  Domain Theory Engine                 │ │
│                     │  (Proprietary Algorithm — Patent      │ │
│                     │   Pending — Details Not Published)     │ │
│                     └──────────────┬───────────────────────┘ │
│                                    │                          │
│                  ┌─────────────────▼─────────────────┐       │
│                  │  Feature Engineering Pipeline       │       │
│                  │  70+ dimensions × 4 categories      │       │
│                  │  ┌───────┐ ┌───────┐ ┌──────────┐ │       │
│                  │  │Shape  │ │Pos.   │ │Relation  │ │       │
│                  │  │(7 dim)│ │(12dim)│ │(~35 dim) │ │       │
│                  │  └───────┘ └───────┘ └──────────┘ │       │
│                  └─────────────────┬─────────────────┘       │
│                                    │                          │
│         ┌──────────────────────────▼──────────────────────┐  │
│         │  6× Specialized XGBoost Models                   │  │
│         │  ┌─────────┐ ┌─────────┐ ┌─────────┐           │  │
│         │  │N3 Axis  │ │N3 Box   │ │N3 Str.  │           │  │
│         │  │Predictor│ │Combiner │ │Combiner │           │  │
│         │  └─────────┘ └─────────┘ └─────────┘           │  │
│         │  ┌─────────┐ ┌─────────┐ ┌─────────┐           │  │
│         │  │N4 Axis  │ │N4 Box   │ │N4 Str.  │           │  │
│         │  │Predictor│ │Combiner │ │Combiner │           │  │
│         │  └─────────┘ └─────────┘ └─────────┘           │  │
│         │  103 model artifacts │ 79 vectorized batches     │  │
│         └─────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
```

---

## Technology Stack

| Layer | Technologies |
|-------|-------------|
| **Frontend** | Next.js 14.2, React 18.3, TypeScript 5.3, Tailwind CSS, Redux Toolkit, Framer Motion |
| **Backend API** | Next.js API Routes (16 endpoints) |
| **ML Inference** | FastAPI, Python 3.10 |
| **ML Framework** | XGBoost 2.0, scikit-learn 1.3, LightGBM |
| **Data Pipeline** | pandas, NumPy, custom feature extractors |
| **Infrastructure** | Vercel (Frontend), GitHub CI/CD |
| **State Management** | Redux Toolkit with async thunks |
| **Visualization** | Recharts, custom chart generators |

---

## ML Pipeline

### 6-Model Ensemble Architecture

Each lottery type (N3/N4) has 3 dedicated prediction models:

| Model | Task | Output |
|-------|------|--------|
| **Axis Number Predictor** | Classify digits 0-9 by win probability | Ranked digit scores |
| **Box Combination Model** | Rank unordered number combinations | Top-N candidates |
| **Straight Combination Model** | Rank exact-order combinations | Top-N candidates |

### Feature Engineering

70+ features extracted across 4 categories from the proprietary domain transformation:

- **Shape Features** (7 dims): Spatial pattern geometry
- **Position Features** (12 dims): Grid coordinate statistics
- **Relationship Features** (~35 dims): Multi-directional interaction analysis, distance metrics, overlap patterns
- **Aggregate Features** (~7 dims): Statistical tendency summaries

> **Note**: The feature extraction logic and domain transformation algorithm are proprietary  
> intellectual property. Implementation details are not published in this repository's documentation.

### Training Data Pipeline

```
Historical Data (6,700+ draws)
    → Proprietary Domain Transformation
    → Feature Extraction (70+ dimensions)
    → 6 Dedicated Training Datasets (.pkl)
    → XGBoost Model Training
    → 103 Serialized Model Artifacts
    → 79 Vectorized Combination Batches
```

---

## Project Structure

```
numbers-ai/
├── src/                           # Next.js Web Application (12,200+ LoC)
│   ├── app/                       # App Router + 16 API route handlers
│   │   └── api/                   # REST API endpoints
│   ├── components/                # 17 React components
│   ├── lib/                       # Core business logic
│   │   ├── cube-generator/        # Domain theory engine (proprietary)
│   │   ├── predictor/             # Prediction orchestration
│   │   ├── data-loader/           # Data ingestion layer
│   │   ├── chart-generator/       # Visualization engine
│   │   └── utils/                 # Shared utilities
│   ├── store/                     # Redux state management
│   └── types/                     # TypeScript type definitions
│
├── core/                          # Python core logic modules
├── api/                           # FastAPI ML inference server
│
├── scripts/                       # ML pipeline scripts (25,500+ LoC)
│   ├── training/                  # Model training pipelines
│   ├── analysis/                  # Statistical analysis tools
│   ├── feature_engineering/       # Feature extraction logic
│   └── data_processing/          # Data preparation utilities
│
├── data/                          # Data & Model artifacts (193 files)
│   ├── training_data/             # 6 training datasets (.pkl)
│   ├── models/                    # 103 trained model files
│   │   └── combination_batches/   # 79 vectorized prediction batches
│   ├── archive/                   # Historical reference data
│   └── *.csv                      # 17 data source files
│
├── docs/                          # 100+ design documents
└── notebooks/                     # Jupyter analysis notebooks
```

---

## Key Features

- **AI Axis Prediction**: Scores and ranks digits 0-9 by predicted win probability
- **AI Combination Prediction**: Generates ranked lottery number candidates
- **Dual Support**: Numbers 3 (3-digit) and Numbers 4 (4-digit)
- **Box/Straight Modes**: Both unordered and exact-order predictions
- **Manual Override**: Users can specify custom axis digits for prediction
- **Domain Theory Visualization**: Proprietary transformation results with Excel export
- **Responsive UI**: Mobile-friendly with animated transitions (Framer Motion)

---

## Quick Start

### Prerequisites

- Node.js 20.x+
- pnpm 9.0.0+
- Python 3.10+ (for ML inference)

### Web Application

```bash
git clone https://github.com/Ks-Classic/numbers-ai.git
cd numbers-ai
pnpm install
pnpm dev
```

### ML Inference Server

```bash
cd api
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python run.py
```

---

## Development

```bash
pnpm dev              # Development server (http://localhost:3000)
pnpm build            # Production build
pnpm start            # Production server
pnpm lint             # ESLint
pnpm test:api         # API integration tests
```

---

## License

MIT License — Copyright (c) 2025 Numbers-AI Project

> **Intellectual Property Notice**: While the source code is MIT-licensed,  
> the proprietary prediction theory, domain transformation algorithms,  
> and feature engineering methodology constitute trade secrets  
> and are protected intellectual property.

---

**Last Updated**: 2026-03-13
