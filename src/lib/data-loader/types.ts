/**
 * データ読み込み関連の型定義
 */

/**
 * 回号（4桁整数: 1-9999）
 */
export type RoundNumber = number;

/**
 * 過去の当選結果データ
 */
export interface PastResult {
  /** 回号（4桁整数） */
  roundNumber: RoundNumber;
  /** 抽選日（YYYY-MM-DD形式） */
  drawDate: string;
  /** 曜日（0-4の整数、NULL可）
   * 0: 月曜日、1: 火曜日、2: 水曜日、3: 木曜日、4: 金曜日
   */
  weekday: number | null;
  /** N3当選番号（3桁文字列、例: "149"） */
  n3Winning: string;
  /** N4当選番号（4桁文字列、例: "6757"） */
  n4Winning: string;
  /** N3リハーサル数字（3桁文字列、NULL可） */
  n3Rehearsal: string | null;
  /** N4リハーサル数字（4桁文字列、NULL可） */
  n4Rehearsal: string | null;
}

/**
 * CSV読み込み時のエラー
 */
export class DataLoadError extends Error {
  constructor(message: string, public readonly cause?: unknown) {
    super(message);
    this.name = 'DataLoadError';
  }
}

/**
 * 罫線マスターデータの型定義
 */

/**
 * N3の桁名
 */
export type N3ColumnName = '百の位' | '十の位' | '一の位';

/**
 * N4の桁名
 */
export type N4ColumnName = '千の位' | '百の位' | '十の位' | '一の位';

/**
 * 桁名のユニオン型
 */
export type ColumnName = N3ColumnName | N4ColumnName;

/**
 * 予測出目の配列（0-9の数値配列）
 */
export type PredictedDigits = number[];

/**
 * 前回の数字をキーとした予測出目のマップ（0-9）
 * 内側のキー（JSONの構造上）
 */
export type PreviousMap = {
  [key: string]: PredictedDigits;
};

/**
 * 前々回の数字をキーとしたマップ（0-9）
 * 外側のキー（JSONの構造上）
 */
export type PreviousPreviousMap = {
  [key: string]: PreviousMap;
};

/**
 * 桁ごとの予測ルール
 * 外側のキーが前々回、内側のキーが前回
 */
export type ColumnRules = PreviousPreviousMap;

/**
 * N3の罫線マスターデータ
 */
export interface N3KeisenMaster {
  '百の位': ColumnRules;
  '十の位': ColumnRules;
  '一の位': ColumnRules;
}

/**
 * N4の罫線マスターデータ
 */
export interface N4KeisenMaster {
  '千の位': ColumnRules;
  '百の位': ColumnRules;
  '十の位': ColumnRules;
  '一の位': ColumnRules;
}

/**
 * 罫線マスターデータ全体
 */
export interface KeisenMaster {
  n3: N3KeisenMaster;
  n4: N4KeisenMaster;
}

