import type { Target, Pattern } from '@/types/prediction';

interface ApiPredictResponse {
  success: boolean;
  data: {
    roundNumber: number;
    generatedAt: string;
    n3?: PredictionPayload;
    n4?: PredictionPayload;
  };
  error?: {
    code: string;
    message: string;
  };
}

interface PredictionPayload {
  bestPattern: Pattern;
  patternScores: Record<Pattern, number>;
  box: PredictionSection;
  straight: PredictionSection;
}

interface PredictionSection {
  axisCandidates: Array<{
    digit: number;
    score: number;
    confidence: number;
    source: Pattern;
  }>;
  numberCandidates: Array<{
    numbers: string;
    score: number;
    confidence: number;
    source: Pattern;
    rank: number;
  }>;
}

async function fetchPredictAPI(body: {
  roundNumber: number;
  n3Rehearsal?: string;
  n4Rehearsal?: string;
}): Promise<ApiPredictResponse> {
  const url = '/api/predict';

  console.log('=== Next.js Prediction Fetch ===');
  console.log('Request Body:', JSON.stringify(body));

  const response = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Prediction API error: ${response.status} ${response.statusText} - ${errorText}`);
  }

  const payload = (await response.json()) as ApiPredictResponse;

  if (!payload.success) {
    throw new Error(payload.error?.message || 'Prediction API returned failure');
  }

  console.log('Prediction API response received');
  return payload;
}

export async function predictTarget(
  roundNumber: number,
  target: Target,
  rehearsalDigits: string
): Promise<PredictionPayload> {
  const body = target === 'n3'
    ? { roundNumber, n3Rehearsal: rehearsalDigits }
    : { roundNumber, n4Rehearsal: rehearsalDigits };

  const payload = await fetchPredictAPI(body);
  const prediction = payload.data[target];

  if (!prediction) {
    throw new Error(`${target.toUpperCase()} の予測結果が返却されませんでした`);
  }

  return prediction;
}

