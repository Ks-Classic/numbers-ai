/**
 * CUBE生成APIクライアント
 */

export interface CubeData {
  id: string;
  keisen_type: 'current' | 'new';
  cube_type: 'normal' | 'extreme';
  target: 'n3' | 'n4';
  pattern: 'A1' | 'A2' | 'B1' | 'B2' | null;
  grid: (number | null)[][];
  rows: number;
  cols: number;
  previous_winning: string;
  previous_previous_winning: string;
  previous_rehearsal: string | null;
  previous_previous_rehearsal: string | null;
  predicted_digits: number[];
}

export interface ExtractedDigits {
  withMissingFill: number[]; // A1/A2（欠番補足あり）
  withoutMissingFill: number[]; // B1/B2（欠番補足なし）
}

export interface CubesResponse {
  round_number: number;
  cubes: CubeData[];
  current_winning: {
    n3: string | null;
    n4: string | null;
  };
  current_rehearsal: {
    n3: string | null;
    n4: string | null;
  };
  extracted_digits: {
    current: {
      n3: ExtractedDigits;
      n4: ExtractedDigits;
    };
    new: {
      n3: ExtractedDigits;
      n4: ExtractedDigits;
    };
  };
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || '/api/cube';

export async function fetchCubes(roundNumber: number): Promise<CubesResponse> {
  try {
    // Next.jsのAPIルート経由でアクセス（相対パス）
    const url = `${API_BASE_URL}/${roundNumber}`;
    console.log(`[CUBE API] リクエスト送信: ${url}`);
    
    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });
    
    console.log(`[CUBE API] レスポンス受信: status=${response.status}, ok=${response.ok}`);
    
    if (!response.ok) {
      let errorDetail = `HTTP error! status: ${response.status}`;
      let errorData: any = null;
      try {
        const text = await response.text();
        console.error(`[CUBE API] エラーレスポンス（テキスト）:`, text);
        if (text) {
          try {
            errorData = JSON.parse(text);
            console.error(`[CUBE API] エラーレスポンス（JSON）:`, errorData);
          } catch (e) {
            // JSONパースに失敗した場合はテキストをそのまま使用
            errorDetail = text || errorDetail;
          }
        }
        if (errorData) {
          errorDetail = errorData.error || errorData.detail || errorData.message || JSON.stringify(errorData) || errorDetail;
        }
      } catch (e) {
        console.error(`[CUBE API] エラーレスポンスの読み取りに失敗:`, e);
        errorDetail = `レスポンスの読み取りに失敗しました: ${e instanceof Error ? e.message : String(e)}`;
      }
      throw new Error(errorDetail);
    }
    
    const data = await response.json();
    console.log(`[CUBE API] 成功: ${data.cubes?.length || 0}個のCUBEを取得`);
    return data;
  } catch (error) {
    if (error instanceof TypeError && error.message.includes('fetch')) {
      console.error(`[CUBE API] ネットワークエラー: サーバーに接続できません (${API_BASE_URL})`);
      throw new Error(`サーバーに接続できません。APIサーバーが起動しているか確認してください。\nURL: ${API_BASE_URL}`);
    }
    console.error(`[CUBE API] エラー:`, error);
    throw error;
  }
}

/**
 * 数字を丸数字に変換する関数（①、②、③...）
 */
function toCircledNumber(num: number): string {
  if (num >= 1 && num <= 20) {
    // ①(0x2460) から ⑳(0x2473) まで
    return String.fromCharCode(0x2460 + num - 1);
  }
  // 20を超える場合は通常の数字を返す
  return num.toString();
}

/**
 * CUBEグリッドをExcel貼り付け用のTSV形式に変換
 */
export function gridToTSV(grid: (number | null)[][], rows: number, cols: number): string {
  const lines: string[] = [];
  
  // ヘッダー行（列番号を丸数字で）
  const header = ['', ...Array.from({ length: cols }, (_, i) => toCircledNumber(i + 1))];
  lines.push(header.join('\t'));
  
  // データ行（行番号を丸数字で）
  for (let row = 1; row <= rows; row++) {
    const rowData = [toCircledNumber(row)];
    for (let col = 1; col <= cols; col++) {
      const value = grid[row]?.[col];
      rowData.push(value !== null && value !== undefined ? value.toString() : '');
    }
    lines.push(rowData.join('\t'));
  }
  
  return lines.join('\n');
}

