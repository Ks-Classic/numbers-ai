/**
 * 予測表関連の型定義
 */

import type { Target, Pattern } from './prediction';

/**
 * 予測表のグリッド（2次元配列）
 * nullは空白マスを表す
 */
export type ChartGrid = (number | null)[][];

/**
 * 予測表データ
 */
export interface ChartData {
  /** 予測表のグリッド */
  grid: ChartGrid;
  /** 行数 */
  rows: number;
  /** 列数（常に8） */
  cols: number;
  /** パターン（'A1' | 'A2' | 'B1' | 'B2'） */
  pattern: Pattern;
  /** 対象（'n3' または 'n4'） */
  target: Target;
  /** 元数字リスト（source_list、欠番補足前） */
  sourceDigits: number[];
  /** 拡張後の数字リスト（欠番補足後） */
  expandedDigits?: number[];
  /** templist（4桁単位で最小値から順に重複せずに選択した順序） */
  tempList?: number[];
  /** 中心0配置が明示的に実行されたかどうか（A2/B2のみtrue） */
  centerZeroPlaced?: boolean;
}

/**
 * メイン行のデータ
 */
export interface MainRow {
  /** メイン行の要素（1〜4要素） */
  elements: number[];
  /** 行インデックス（0始まり） */
  rowIndex: number;
}

/**
 * 予測表生成時のエラー
 */
export class ChartGenerationError extends Error {
  constructor(message: string, public readonly cause?: unknown) {
    super(message);
    this.name = 'ChartGenerationError';
  }
}

