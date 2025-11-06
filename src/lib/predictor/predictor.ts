/**
 * 予測処理の実装
 * 
 * FastAPIサーバーを呼び出して予測を実行します。
 */

import type { Target, Pattern } from '@/types/prediction';

/**
 * FastAPIサーバーからの軸数字予測レスポンス
 */
interface AxisPredictionResponse {
  best_pattern: Pattern;
  pattern_scores: Record<Pattern, number>;
  axis_candidates: Array<{
    digit: number;
    score: number;
    pattern: Pattern;
  }>;
}

/**
 * FastAPIサーバーからの組み合わせ予測レスポンス
 */
interface CombinationPredictionResponse {
  combinations: Array<{
    combination: string;
    score: number;
  }>;
}

/**
 * 予測結果
 */
export interface PredictResult {
  bestPattern: Pattern;
  patternScores: Record<Pattern, number>;
  box: {
    axisCandidates: Array<{
      digit: number;
      score: number;
      pattern: Pattern;
    }>;
    numberCandidates: Array<{
      combination: string;
      score: number;
    }>;
  };
  straight: {
    axisCandidates: Array<{
      digit: number;
      score: number;
      pattern: Pattern;
    }>;
    numberCandidates: Array<{
      combination: string;
      score: number;
    }>;
  };
}

/**
 * FastAPIサーバーにリクエストを送信する
 */
async function fetchFromFastAPI<T>(
  url: string,
  endpoint: string,
  body: unknown
): Promise<T> {
  const response = await fetch(`${url}${endpoint}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(body),
  });
  
  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(
      `FastAPI request failed: ${response.status} ${response.statusText} - ${errorText}`
    );
  }
  
  return response.json();
}

/**
 * 軸数字を予測する
 */
async function predictAxis(
  fastApiUrl: string,
  roundNumber: number,
  target: Target,
  rehearsalDigits?: string
): Promise<AxisPredictionResponse> {
  return fetchFromFastAPI<AxisPredictionResponse>(
    fastApiUrl,
    '/api/predict/axis',
    {
      round_number: roundNumber,
      target,
      rehearsal_digits: rehearsalDigits,
    }
  );
}

/**
 * 組み合わせを予測する
 */
async function predictCombination(
  fastApiUrl: string,
  roundNumber: number,
  target: Target,
  comboType: 'box' | 'straight',
  bestPattern: Pattern,
  topAxisDigits: number[],
  rehearsalDigits?: string
): Promise<CombinationPredictionResponse> {
  return fetchFromFastAPI<CombinationPredictionResponse>(
    fastApiUrl,
    '/api/predict/combination',
    {
      round_number: roundNumber,
      target,
      combo_type: comboType,
      best_pattern: bestPattern,
      top_axis_digits: topAxisDigits,
      rehearsal_digits: rehearsalDigits,
      max_combinations: 100,
    }
  );
}

/**
 * 対象（N3またはN4）の予測を実行する
 */
export async function predictTarget(
  fastApiUrl: string,
  roundNumber: number,
  target: Target,
  rehearsalDigits: string
): Promise<PredictResult> {
  try {
    // 1. 軸数字を予測
    const axisResult = await predictAxis(
      fastApiUrl,
      roundNumber,
      target,
      rehearsalDigits
    );
    
    // 上位10個の軸数字を取得
    const topAxisDigits = axisResult.axis_candidates
      .slice(0, 10)
      .map((item) => item.digit);
    
    // 2. ボックスとストレートの組み合わせを予測（モデルが見つからない場合はスキップ）
    let boxCombinations: CombinationPredictionResponse | null = null;
    let straightCombinations: CombinationPredictionResponse | null = null;
    
    try {
      boxCombinations = await predictCombination(
        fastApiUrl,
        roundNumber,
        target,
        'box',
        axisResult.best_pattern,
        topAxisDigits,
        rehearsalDigits
      );
    } catch (error: any) {
      // モデルが見つからない場合は空の結果を返す
      if (error?.message?.includes('モデルが見つかりません') || 
          error?.message?.includes('モデルが読み込まれていません')) {
        console.warn(`ボックス組み合わせ予測モデルが見つかりません（${target}）。スキップします。`);
        boxCombinations = { combinations: [] };
      } else {
        throw error;
      }
    }
    
    try {
      straightCombinations = await predictCombination(
        fastApiUrl,
        roundNumber,
        target,
        'straight',
        axisResult.best_pattern,
        topAxisDigits,
        rehearsalDigits
      );
    } catch (error: any) {
      // モデルが見つからない場合は空の結果を返す
      if (error?.message?.includes('モデルが見つかりません') || 
          error?.message?.includes('モデルが読み込まれていません')) {
        console.warn(`ストレート組み合わせ予測モデルが見つかりません（${target}）。スキップします。`);
        straightCombinations = { combinations: [] };
      } else {
        throw error;
      }
    }
    
    return {
      bestPattern: axisResult.best_pattern,
      patternScores: axisResult.pattern_scores,
      box: {
        axisCandidates: axisResult.axis_candidates,
        numberCandidates: boxCombinations?.combinations || [],
      },
      straight: {
        axisCandidates: axisResult.axis_candidates,
        numberCandidates: straightCombinations?.combinations || [],
      },
    };
  } catch (error) {
    console.error(`予測エラー (${target}):`, error);
    throw error;
  }
}

