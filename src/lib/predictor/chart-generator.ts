/**
 * 予測表生成処理
 * 
 * 4パターン（A1/A2/B1/B2）の予測表を生成する
 */

import { generateChart } from '@/lib/chart-generator';
import type { Pattern, Target } from '@/types/prediction';
import type { ChartData } from '@/types/chart';

/**
 * 4パターンの予測表を生成する
 * 
 * @param roundNumber 回号
 * @param target 対象（'n3' または 'n4'）
 * @returns パターン別の予測表データ
 */
export async function generateAllPatternCharts(
  roundNumber: number,
  target: Target
): Promise<Record<Pattern, ChartData>> {
  const patterns: Pattern[] = ['A1', 'A2', 'B1', 'B2'];
  const charts: Record<Pattern, ChartData> = {} as Record<Pattern, ChartData>;
  
  for (const pattern of patterns) {
    try {
      charts[pattern] = await generateChart(roundNumber, pattern, target);
    } catch (error) {
      console.error(`予測表生成エラー (${pattern}):`, error);
      throw new Error(
        `予測表生成に失敗しました (パターン: ${pattern}): ${error instanceof Error ? error.message : 'Unknown error'}`
      );
    }
  }
  
  return charts;
}

