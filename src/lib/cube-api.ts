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
}

export interface CubesResponse {
  round_number: number;
  cubes: CubeData[];
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export async function fetchCubes(roundNumber: number): Promise<CubesResponse> {
  try {
    const url = `${API_BASE_URL}/api/cube/${roundNumber}`;
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
      try {
        const errorData = await response.json();
        errorDetail = errorData.detail || errorData.message || errorDetail;
        console.error(`[CUBE API] エラーレスポンス:`, errorData);
      } catch (e) {
        const text = await response.text();
        console.error(`[CUBE API] エラーテキスト:`, text);
        errorDetail = text || errorDetail;
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
 * CUBEグリッドをExcel貼り付け用のTSV形式に変換
 */
export function gridToTSV(grid: (number | null)[][], rows: number, cols: number): string {
  const lines: string[] = [];
  
  // ヘッダー行（列番号）
  const header = ['', ...Array.from({ length: cols }, (_, i) => (i + 1).toString())];
  lines.push(header.join('\t'));
  
  // データ行
  for (let row = 1; row <= rows; row++) {
    const rowData = [row.toString()];
    for (let col = 1; col <= cols; col++) {
      const value = grid[row]?.[col];
      rowData.push(value !== null && value !== undefined ? value.toString() : '');
    }
    lines.push(rowData.join('\t'));
  }
  
  return lines.join('\n');
}

