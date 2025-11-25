import { spawn } from 'node:child_process';
import { once } from 'node:events';

type ProxyRequest = {
  endpoint: '/api/predict/axis' | '/api/predict/combination';
  body: Record<string, unknown>;
};

type ProxyResponse = {
  status_code: number;
  body: Record<string, unknown>;
};

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

async function callPythonProxy(payload: ProxyRequest): Promise<ProxyResponse> {
  const child = spawn('python3', ['scripts/node_predict_proxy.py'], {
    stdio: ['pipe', 'pipe', 'inherit'],
  });

  child.stdin.write(JSON.stringify(payload));
  child.stdin.end();

  const chunks: Buffer[] = [];
  child.stdout.on('data', (chunk) => chunks.push(Buffer.from(chunk)));

  const [code] = await once(child, 'exit');
  if (code !== 0) {
    throw new Error(`node_predict_proxy exited with ${code}`);
  }

  const resultRaw = Buffer.concat(chunks).toString('utf-8').trim();
  try {
    return JSON.parse(resultRaw);
  } catch (err) {
    throw new Error(`Malformed proxy output: ${resultRaw}`);
  }
}

export async function predictAxis(
  roundNumber: number,
  target: 'n3' | 'n4',
  rehearsalDigits?: string
): Promise<AxisPredictionResult> {
  const response = await callPythonProxy({
    endpoint: '/api/predict/axis',
    body: {
      round_number: roundNumber,
      target,
      rehearsal_digits: rehearsalDigits,
    },
  });

  const body = response.body as AxisPredictionResult;
  if (!body.success) {
    throw new Error(`Axis prediction failed: ${JSON.stringify(body)}`);
  }

  return body;
}

export async function predictCombination(
  roundNumber: number,
  target: 'n3' | 'n4',
  comboType: 'box' | 'straight',
  bestPattern: 'A1' | 'A2' | 'B1' | 'B2',
  topAxisDigits: number[],
  rehearsalDigits?: string
): Promise<CombinationPredictionResult> {
  const response = await callPythonProxy({
    endpoint: '/api/predict/combination',
    body: {
      round_number: roundNumber,
      target,
      combo_type: comboType,
      best_pattern: bestPattern,
      top_axis_digits: topAxisDigits,
      rehearsal_digits: rehearsalDigits,
    },
  });

  const body = response.body as CombinationPredictionResult;
  if (!body.success) {
    throw new Error(`Combination prediction failed: ${JSON.stringify(body)}`);
  }

  return body;
}

