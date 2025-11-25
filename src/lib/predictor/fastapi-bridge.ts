/**
 * FastAPI バックエンドと通信するクライアント
 */

import type { Pattern, Target } from '@/types/prediction';

const FASTAPI_URL = process.env.FASTAPI_URL || 'http://localhost:8000';

const JSON_HEADERS = {
  'Content-Type': 'application/json',
};

interface AxisPredictionRequest {
  round_number: number;
  target: Target;
  rehearsal_digits?: string;
}

interface CombinationPredictionRequest {
  round_number: number;
  target: Target;
  combo_type: 'box' | 'straight';
  best_pattern: Pattern;
  top_axis_digits: number[];
  rehearsal_digits?: string;
  max_combinations: number;
}

export interface AxisPredictionResponse {
  best_pattern: Pattern;
  pattern_scores: Record<Pattern, number>;
  axis_candidates: Array<{
    digit: number;
    score: number;
    pattern: Pattern;
  }>;
}

export interface CombinationPredictionResponse {
  combinations: Array<{
    combination: string;
    score: number;
  }>;
}

async function postToFastAPI<T>(
  endpoint: string,
  body: Record<string, unknown>
): Promise<T> {
  const url = `${FASTAPI_URL}${endpoint}`;

  console.log(`[FastAPI] POST ${url}`);

  const response = await fetch(url, {
    method: 'POST',
    headers: JSON_HEADERS,
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(`FastAPI request failed: ${response.status} ${response.statusText} - ${text}`);
  }

  return response.json() as Promise<T>;
}

export async function predictAxis(
  roundNumber: number,
  target: Target,
  rehearsalDigits?: string
): Promise<AxisPredictionResponse> {
  return postToFastAPI<AxisPredictionResponse>('/api/predict/axis', {
    round_number: roundNumber,
    target,
    rehearsal_digits: rehearsalDigits,
  });
}

export async function predictCombination(
  roundNumber: number,
  target: Target,
  comboType: 'box' | 'straight',
  bestPattern: Pattern,
  topAxisDigits: number[],
  rehearsalDigits?: string
): Promise<CombinationPredictionResponse> {
  return postToFastAPI<CombinationPredictionResponse>('/api/predict/combination', {
    round_number: roundNumber,
    target,
    combo_type: comboType,
    best_pattern: bestPattern,
    top_axis_digits: topAxisDigits,
    rehearsal_digits: rehearsalDigits,
    max_combinations: 100,
  });
}

export interface PredictResult {
  bestPattern: Pattern;
  patternScores: Record<Pattern, number>;
  box: {
    axisCandidates: Array<{
      digit: number;
      score: number;
      confidence: number;
      pattern: Pattern;
      combination?: string;
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
      confidence: number;
      pattern: Pattern;
    }>;
    numberCandidates: Array<{
      combination: string;
      score: number;
    }>;
  };
}

export async function predictTarget(
  roundNumber: number,
  target: Target,
  rehearsalDigits: string
): Promise<PredictResult> {
  console.log(`[FastAPI Bridge] predictTarget(${roundNumber}, ${target})`);

  const axisResult = await predictAxis(roundNumber, target, rehearsalDigits);

  const topAxisDigits = axisResult.axis_candidates
    .slice(0, 10)
    .map((item) => item.digit);

  let boxCombinations: CombinationPredictionResponse | null = null;
  let straightCombinations: CombinationPredictionResponse | null = null;

  try {
    boxCombinations = await predictCombination(
      roundNumber,
      target,
      'box',
      axisResult.best_pattern,
      topAxisDigits,
      rehearsalDigits
    );
  } catch (error: any) {
    if (error?.message?.includes('モデルが見つかりません') || error?.message?.includes('モデルが読み込まれていません')) {
      console.warn(`ボックス組み合わせモデルが見つかりません（${target}）: ${error.message}`);
      boxCombinations = { combinations: [] };
    } else {
      throw error;
    }
  }

  try {
    straightCombinations = await predictCombination(
      roundNumber,
      target,
      'straight',
      axisResult.best_pattern,
      topAxisDigits,
      rehearsalDigits
    );
  } catch (error: any) {
    if (error?.message?.includes('モデルが見つかりません') || error?.message?.includes('モデルが読み込まれていません')) {
      console.warn(`ストレート組み合わせモデルが見つかりません（${target}）: ${error.message}`);
      straightCombinations = { combinations: [] };
    } else {
      throw error;
    }
  }

  return {
    bestPattern: axisResult.best_pattern,
    patternScores: axisResult.pattern_scores,
    box: {
      axisCandidates: axisResult.axis_candidates.map((item) => ({
        digit: item.digit,
        score: item.score,
        confidence: Math.round(item.score / 10),
        pattern: item.pattern,
      })),
      numberCandidates: boxCombinations?.combinations || [],
    },
    straight: {
      axisCandidates: axisResult.axis_candidates.map((item) => ({
        digit: item.digit,
        score: item.score,
        confidence: Math.round(item.score / 10),
        pattern: item.pattern,
      })),
      numberCandidates: straightCombinations?.combinations || [],
    },
  };
}

