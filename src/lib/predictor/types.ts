/**
 * 予測処理に関する型定義
 */

import type { Pattern, Target } from '@/types/prediction';

/**
 * 軸数字予測結果
 */
export interface AxisPredictionResult {
  digit: number;
  score: number;
  pattern: Pattern;
}

/**
 * パターン別の軸数字予測結果
 */
export interface AxisByPattern {
  [pattern: string]: AxisPredictionResult[];
}

/**
 * 組み合わせ予測結果
 */
export interface CombinationPredictionResult {
  combination: string;
  score: number;
  pattern: Pattern;
}

/**
 * 予測実行パラメータ
 */
export interface PredictParams {
  roundNumber: number;
  target: Target;
  rehearsalDigits?: string;
}

/**
 * 最良パターンと軸数字ランキング
 */
export interface BestPatternResult {
  bestPattern: Pattern;
  patternScores: Record<Pattern, number>;
  axisCandidates: Array<{
    digit: number;
    score: number;
    pattern: Pattern;
  }>;
}

