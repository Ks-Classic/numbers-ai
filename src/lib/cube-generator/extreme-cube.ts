/**
 * 極CUBE生成ロジック（統一）
 * 
 * 極CUBEの仕様:
 * - N3のみ（N4は対象外）
 * - B1パターンと同じ（欠番補足なし、中心0配置なし）
 * - 最大5行まで（メイン行1,3,5行目）
 * - 2行目と4行目に裏数字を配置（6行目は不要）
 */

import type { ChartGrid } from '@/types/chart';
import { ChartGenerationError } from '@/types/chart';
import { generateChart } from './chart-generator';
import type { KeisenMasterType } from './keisen-master-loader';

/**
 * 裏数字を計算する
 */
function inverse(n: number): number {
  return (n + 5) % 10;
}

/**
 * 裏数字ルール（縦パス）を適用する
 */
function applyVerticalInverse(grid: ChartGrid, rows: number, cols: number): void {
  let updated = true;
  
  while (updated) {
    updated = false;
    
    for (let row = 1; row <= rows; row++) {
      for (let col = 1; col <= cols; col++) {
        if (grid[row][col] === null && row > 1 && grid[row - 1][col] !== null) {
          grid[row][col] = inverse(grid[row - 1][col]!);
          updated = true;
        }
      }
    }
  }
}

/**
 * 裏数字ルール（横パス）を適用する
 */
function applyHorizontalInverse(grid: ChartGrid, rows: number, cols: number): void {
  let updated = true;
  
  while (updated) {
    updated = false;
    
    for (let row = 1; row <= rows; row++) {
      for (let col = 1; col <= cols; col++) {
        if (grid[row][col] === null && col > 1 && grid[row][col - 1] !== null) {
          grid[row][col] = inverse(grid[row][col - 1]!);
          updated = true;
        }
      }
    }
  }
}

/**
 * 極CUBEを生成する
 * 
 * @param roundNumber 回号
 * @param keisenMasterType 罫線マスターの種類（'current' または 'new'、デフォルト: 'current'）
 * @returns 極CUBEのグリッド、行数、列数
 */
export async function generateExtremeCube(
  roundNumber: number,
  keisenMasterType: KeisenMasterType = 'current'
): Promise<{ grid: ChartGrid; rows: number; cols: number }> {
  try {
    // B1パターンで通常CUBEを生成（N3のみ、罫線マスターの種類を指定）
    const chartData = await generateChart(roundNumber, 'B1', 'n3', keisenMasterType);
    
    // 極CUBEは最大5行まで
    const maxRows = 5;
    const rows = Math.min(chartData.rows, maxRows);
    const cols = chartData.cols;
    
    // グリッドを5行までに制限
    const grid: ChartGrid = [];
    for (let row = 0; row <= rows; row++) {
      grid[row] = chartData.grid[row] || [];
    }
    
    // 5行目の余りマスを0で埋める（極CUBE固有）
    if (rows >= 5) {
      for (let col = 1; col <= cols; col++) {
        if (col % 2 === 1 && grid[5][col] === null) {
          // 奇数行（5行目）の奇数列（1, 3, 5, 7列目）で空いているマスを0で埋める
          grid[5][col] = 0;
        }
      }
    }
    
    return { grid, rows, cols };
  } catch (error) {
    if (error instanceof ChartGenerationError) {
      throw error;
    }
    throw new ChartGenerationError(
      `極CUBE生成エラー（回号${roundNumber}）: ${(error as Error).message}`,
      error
    );
  }
}

