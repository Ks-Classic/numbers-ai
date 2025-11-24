/**
 * 予測処理の実装
 * 
 * FastAPIサーバーまたはVercel Python関数を呼び出して予測を実行します。
 */

import type { Target, Pattern } from '@/types/prediction';

/**
 * 環境変数の確認（Vercel Python関数を使用するかどうか）
 * Vercel環境（本番またはvercel dev）では相対パスを使用する
 */
const USE_VERCEL_PYTHON = process.env.USE_VERCEL_PYTHON === 'true' || !!process.env.VERCEL;
const FASTAPI_URL = process.env.FASTAPI_URL || 'http://localhost:8000';


/**
 * 軸数字予測レスポンス
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
 * 組み合わせ予測レスポンス
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
 * FastAPIサーバーまたはVercel Python関数にリクエストを送信する
 */
async function fetchFromAPI<T>(
  endpoint: string,
  body: unknown
): Promise<T> {
  let url: string;

  if (USE_VERCEL_PYTHON) {
    // Vercel Python関数を呼び出す
    if (typeof window === 'undefined') {
      // サーバーサイド（Next.js API Route）から呼び出す場合は絶対URLが必要
      // VERCEL_URLはhttpsを含まないため付与する
      const baseUrl = process.env.VERCEL_URL
        ? `https://${process.env.VERCEL_URL}`
        : 'http://localhost:3000'; // ローカルフォールバック
      url = `${baseUrl}${endpoint}`;
    } else {
      // クライアントサイドから呼び出す場合は相対パスでOK
      url = endpoint;
    }
  } else {
    // FastAPIサーバーを呼び出す
    url = `${FASTAPI_URL}${endpoint}`;
  }

  console.log(`[API Request] ${endpoint}`, {
    url,
    body
  });

  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    });

    console.log(`[API Response Status] ${endpoint}: ${response.status} ${response.statusText}`);

    if (!response.ok) {
      const errorText = await response.text();
      console.error(`[API Error] ${endpoint}:`, errorText);
      throw new Error(
        `API request failed: ${response.status} ${response.statusText} - ${errorText}`
      );
    }

    // Vercel Python関数の場合は、レスポンスボディをパースする必要がある
    if (USE_VERCEL_PYTHON) {
      const result = await response.json();
      console.log(`[API Response Body] ${endpoint}:`, JSON.stringify(result).substring(0, 200) + '...');

      // Vercel Python関数のレスポンス形式に応じて調整
      if (result.body) {
        try {
          // bodyが文字列（JSON文字列）の場合
          if (typeof result.body === 'string') {
            return JSON.parse(result.body);
          }
          // bodyがすでにオブジェクトの場合
          return result.body;
        } catch (e) {
          console.error(`[API Parse Error] ${endpoint}: Failed to parse body`, e);
          return result.body;
        }
      }
      return result;
    }

    const json = await response.json();
    console.log(`[API Response Data] ${endpoint}:`, JSON.stringify(json).substring(0, 200) + '...');
    return json;
  } catch (error) {
    console.error(`[API Fetch Error] ${endpoint}:`, error);
    throw error;
  }
}

/**
 * 軸数字を予測する
 */
async function predictAxis(
  roundNumber: number,
  target: Target,
  rehearsalDigits?: string
): Promise<AxisPredictionResponse> {
  return fetchFromAPI<AxisPredictionResponse>(
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
export async function predictCombination(
  roundNumber: number,
  target: Target,
  comboType: 'box' | 'straight',
  bestPattern: Pattern,
  topAxisDigits: number[],
  rehearsalDigits?: string
): Promise<CombinationPredictionResponse> {
  return fetchFromAPI<CombinationPredictionResponse>(
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
  roundNumber: number,
  target: Target,
  rehearsalDigits: string
): Promise<PredictResult> {
  try {
    // 1. 軸数字を予測
    const axisResult = await predictAxis(
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

