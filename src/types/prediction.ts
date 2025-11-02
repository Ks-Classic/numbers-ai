export interface AxisCandidate {
  axis: number;
  confidence: number;
  chart_score: number;
  rehearsal_score: number;
  reason: string;
  score: number; // 総合スコア（985など）
  source: 'A' | 'B'; // 出所：A=0なし、B=0あり
  // 当選番号候補（この軸を含む組み合わせ）
  candidates?: {
    box: PredictionItem[];
    straight: PredictionItem[];
  };
}

export interface PredictionItem {
  number: string;
  probability: number;
  reason: string;
  score?: number; // スコア（985など）
  source?: 'A' | 'B'; // 出所：A=0なし、B=0あり
  score_breakdown?: {
    chart_proximity: number;
    rehearsal_correlation: number;
    historical_similarity: number;
    statistical_validity: number;
  };
}

export interface PredictionState {
  // 予測セッション
  currentSession: {
    sessionId: string | null;
    roundNumber: number;
    numbersType: 'N3' | 'N4';
    patternType: 'A' | 'B';
    rehearsalN3: string;
    rehearsalN4: string;
    selectedAxes: number[];
  };

  // 軸候補
  axisCandidates: AxisCandidate[];

  // 最終予測結果
  finalPredictions: {
    straight: PredictionItem[];
    box: PredictionItem[];
  } | null;

  // アクション
  setSessionData: (data: Partial<PredictionState['currentSession']>) => void;
  setAxisCandidates: (candidates: AxisCandidate[]) => void;
  toggleAxis: (axis: number) => void;
  setFinalPredictions: (predictions: {
    straight: PredictionItem[];
    box: PredictionItem[];
  } | null) => void;
  resetSession: () => void;
}

export interface HistoryItem {
  id: number;
  round: number;
  date: string;
  numbers_type: 'N3' | 'N4';
  selected_axes: number[];
  predicted_number: string;
  prediction_type: 'straight' | 'box';
  actual_winning: string;
  is_hit: boolean;
  confidence: number;
  predicted_at: string;
}
