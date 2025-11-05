/**
 * 対象（'n3' または 'n4'）
 */
export type Target = 'n3' | 'n4';

/**
 * パターン（4パターン対応）
 * - A1: 欠番補足あり（0〜9全追加）+ 中心0配置なし
 * - A2: 欠番補足あり（0〜9全追加）+ 中心0配置あり
 * - B1: 欠番補足なし（0のみ追加）+ 中心0配置なし
 * - B2: 欠番補足なし（0のみ追加）+ 中心0配置あり
 */
export type Pattern = 'A1' | 'A2' | 'B1' | 'B2';

export interface AxisCandidate {
  axis: number;
  confidence: number;
  chart_score: number;
  rehearsal_score: number;
  reason: string;
  score: number; // 総合スコア（985など）
  source: Pattern; // 出所：A1/A2/B1/B2
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
  source?: Pattern; // 出所：A1/A2/B1/B2
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
    patternType: Pattern; // 4パターン対応：A1/A2/B1/B2
    rehearsalN3: string;
    rehearsalN4: string;
    selectedAxes: number[];
  };

  // 軸候補（現在選択中のnumbersTypeに対応）
  axisCandidates: AxisCandidate[];

  // 最終予測結果（現在選択中のnumbersTypeに対応）
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
  toggleAxis: (axis: number) => void;
  setFinalPredictions: (predictions: {
    straight: PredictionItem[];
    box: PredictionItem[];
  } | null) => void;
  setN3Data: (candidates: AxisCandidate[], predictions: {
    straight: PredictionItem[];
    box: PredictionItem[];
  } | null) => void;
  setN4Data: (candidates: AxisCandidate[], predictions: {
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
