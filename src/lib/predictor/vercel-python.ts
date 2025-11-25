/**
 * Vercel Python Serverless Functions クライアント
 * 
 * /api/py/axis と /api/py/combination を呼び出す
 */

// 軸数字予測の戻り値型
export type AxisPredictionResult = {
  success: boolean;
  best_pattern: 'A1' | 'A2' | 'B1' | 'B2';
  pattern_scores: Record<string, number>;
  axis_candidates: Array<{
    digit: number;
    score: number;
    pattern: string;
  }>;
};

// 組み合わせ予測の戻り値型
export type CombinationPredictionResult = {
  success: boolean;
  combinations: Array<{
    combination: string;
    score: number;
  }>;
};

/**
 * ベースURLを取得
 * Vercel環境では相対パス、ローカルでは絶対パスを使用
 */
function getBaseUrl(): string {
  // サーバーサイドでの実行
  if (typeof window === 'undefined') {
    // Vercel環境
    if (process.env.VERCEL_URL) {
      return `https://${process.env.VERCEL_URL}`;
    }
    // ローカル開発環境
    return process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3000';
  }
  // クライアントサイド
  return '';
}

/**
 * 軸数字予測API呼び出し
 */
export async function predictAxis(
  roundNumber: number,
  target: 'n3' | 'n4',
  rehearsalDigits?: string,
  csvContent?: string
): Promise<AxisPredictionResult> {
  const baseUrl = getBaseUrl();
  const url = `${baseUrl}/api/py/axis`;

  console.log(`[predictAxis] Calling ${url}`);

  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      round_number: roundNumber,
      target,
      rehearsal_digits: rehearsalDigits,
      csv_content: csvContent,
    }),
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Axis prediction failed: ${response.status} - ${errorText}`);
  }

  const result = await response.json() as AxisPredictionResult;

  if (!result.success) {
    throw new Error(`Axis prediction failed: ${JSON.stringify(result)}`);
  }

  return result;
}

/**
 * 組み合わせ予測API呼び出し
 */
export async function predictCombination(
  roundNumber: number,
  target: 'n3' | 'n4',
  comboType: 'box' | 'straight',
  bestPattern: 'A1' | 'A2' | 'B1' | 'B2',
  topAxisDigits: number[],
  rehearsalDigits?: string,
  csvContent?: string
): Promise<CombinationPredictionResult> {
  const baseUrl = getBaseUrl();
  const url = `${baseUrl}/api/py/combination`;

  console.log(`[predictCombination] Calling ${url}`);

  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      round_number: roundNumber,
      target,
      combo_type: comboType,
      best_pattern: bestPattern,
      top_axis_digits: topAxisDigits,
      rehearsal_digits: rehearsalDigits,
      csv_content: csvContent,
    }),
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Combination prediction failed: ${response.status} - ${errorText}`);
  }

  const result = await response.json() as CombinationPredictionResult;

  if (!result.success) {
    throw new Error(`Combination prediction failed: ${JSON.stringify(result)}`);
  }

  return result;
}

