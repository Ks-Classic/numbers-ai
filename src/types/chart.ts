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
  /** パターン（'A' = 0なし、'B' = 0あり） */
  pattern: Pattern;
  /** 対象（'n3' または 'n4'） */
  target: Target;
  /** 元数字リスト（source_list） */
  sourceDigits: number[];
}

/**
 * メイン行のデータ
 */
export interface MainRow {
  /** メイン行の要素（必ず4要素） */
  elements: [number, number, number, number];
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

