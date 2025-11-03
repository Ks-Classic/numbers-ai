/**
 * 過去当選番号データの読み込みユーティリティ
 */

import { promises as fs } from 'fs';
import path from 'path';
import { PastResult, DataLoadError, RoundNumber } from './types';

/**
 * CSVファイルのパス（プロジェクトルートからの相対パス）
 */
const CSV_FILE_PATH = path.join(process.cwd(), 'data', 'past_results.csv');

/**
 * CSVファイルから過去当選番号データを読み込む
 * 
 * @returns 過去当選番号データの配列（回号の降順）
 * @throws DataLoadError ファイル読み込みエラーまたはデータフォーマットエラー
 */
export async function loadPastResults(): Promise<PastResult[]> {
  try {
    const fileContent = await fs.readFile(CSV_FILE_PATH, 'utf-8');
    return parseCSV(fileContent);
  } catch (error) {
    if (error instanceof DataLoadError) {
      throw error;
    }
    
    if ((error as NodeJS.ErrnoException).code === 'ENOENT') {
      throw new DataLoadError(
        `データファイルが見つかりません: ${CSV_FILE_PATH}`,
        error
      );
    }
    
    throw new DataLoadError(
      `データファイルの読み込みに失敗しました: ${(error as Error).message}`,
      error
    );
  }
}

/**
 * CSV文字列をパースしてPastResult配列に変換
 * 
 * @param csvContent CSVファイルの内容
 * @returns 過去当選番号データの配列
 * @throws DataLoadError パースエラーまたはデータフォーマットエラー
 */
function parseCSV(csvContent: string): PastResult[] {
  const lines = csvContent.trim().split('\n');
  
  if (lines.length < 2) {
    throw new DataLoadError('CSVファイルにデータが含まれていません');
  }
  
  // ヘッダー行をスキップ
  const headerLine = lines[0];
  const expectedHeaders = ['round_number', 'draw_date', 'n3_winning', 'n4_winning', 'n3_rehearsal', 'n4_rehearsal'];
  const headers = headerLine.split(',').map(h => h.trim());
  
  // ヘッダーの検証
  if (!expectedHeaders.every(h => headers.includes(h))) {
    throw new DataLoadError(
      `CSVヘッダーが不正です。期待されるカラム: ${expectedHeaders.join(', ')}`
    );
  }
  
  // データ行をパース
  const results: PastResult[] = [];
  
  for (let i = 1; i < lines.length; i++) {
    const line = lines[i].trim();
    
    // 空行をスキップ
    if (!line) {
      continue;
    }
    
    try {
      const result = parseCSVLine(line, headers);
      if (result) {
        results.push(result);
      }
    } catch (error) {
      throw new DataLoadError(
        `CSVの${i + 1}行目のパースに失敗しました: ${(error as Error).message}`,
        error
      );
    }
  }
  
  // 回号の降順でソート（最新が先頭）
  results.sort((a, b) => b.roundNumber - a.roundNumber);
  
  return results;
}

/**
 * CSVの1行をパースしてPastResultオブジェクトに変換
 * 
 * @param line CSVの1行
 * @param headers ヘッダー行の配列
 * @returns PastResultオブジェクト、またはnull（無効な行の場合）
 */
function parseCSVLine(line: string, headers: string[]): PastResult | null {
  const values = line.split(',').map(v => v.trim());
  
  // ヘッダー数と値の数が一致しない場合は無視
  if (values.length !== headers.length) {
    return null;
  }
  
  // ヘッダーのインデックスを取得
  const getValue = (headerName: string): string => {
    const index = headers.indexOf(headerName);
    return index >= 0 ? values[index] : '';
  };
  
  const roundNumberStr = getValue('round_number');
  const drawDate = getValue('draw_date');
  const n3Winning = getValue('n3_winning');
  const n4Winning = getValue('n4_winning');
  const n3Rehearsal = getValue('n3_rehearsal');
  const n4Rehearsal = getValue('n4_rehearsal');
  
  // NULL値の正規化（NULL文字列を空文字に変換）
  const normalizeNull = (value: string): string => {
    if (value === 'NULL' || value === 'null') {
      return '';
    }
    return value;
  };
  
  const normalizedN3Winning = normalizeNull(n3Winning);
  const normalizedN4Winning = normalizeNull(n4Winning);
  
  // 必須フィールドの検証（NULLまたは空文字の場合はスキップ）
  if (!roundNumberStr || !drawDate || !normalizedN3Winning || !normalizedN4Winning) {
    return null;
  }
  
  // 回号のパースと検証
  const roundNumber = parseInt(roundNumberStr, 10);
  if (isNaN(roundNumber) || roundNumber < 1 || roundNumber > 9999) {
    throw new Error(`回号が不正です: ${roundNumberStr}`);
  }
  
  // 日付形式の検証（簡易チェック）
  if (!/^\d{4}-\d{2}-\d{2}$/.test(drawDate)) {
    throw new Error(`日付形式が不正です: ${drawDate}`);
  }
  
  // 当選番号のフォーマット検証
  if (!/^\d{3}$/.test(normalizedN3Winning)) {
    throw new Error(`N3当選番号が不正です: ${n3Winning}`);
  }
  
  if (!/^\d{4}$/.test(normalizedN4Winning)) {
    throw new Error(`N4当選番号が不正です: ${n4Winning}`);
  }
  
  // リハーサル数字の処理（NULLまたは空文字の場合はnull）
  const parseRehearsal = (value: string): string | null => {
    if (!value || value === 'NULL' || value === 'null') {
      return null;
    }
    return value;
  };
  
  const n3RehearsalParsed = parseRehearsal(n3Rehearsal);
  const n4RehearsalParsed = parseRehearsal(n4Rehearsal);
  
  // リハーサル数字のフォーマット検証（存在する場合）
  if (n3RehearsalParsed && !/^\d{3}$/.test(n3RehearsalParsed)) {
    throw new Error(`N3リハーサル数字が不正です: ${n3RehearsalParsed}`);
  }
  
  if (n4RehearsalParsed && !/^\d{4}$/.test(n4RehearsalParsed)) {
    throw new Error(`N4リハーサル数字が不正です: ${n4RehearsalParsed}`);
  }
  
  return {
    roundNumber,
    drawDate,
    n3Winning: normalizedN3Winning,
    n4Winning: normalizedN4Winning,
    n3Rehearsal: n3RehearsalParsed,
    n4Rehearsal: n4RehearsalParsed,
  };
}

/**
 * 指定された回号の過去当選番号データを取得
 * 
 * @param roundNumber 回号
 * @returns 過去当選番号データ、見つからない場合はnull
 * @throws DataLoadError データ読み込みエラー
 */
export async function getPastResultByRoundNumber(
  roundNumber: RoundNumber
): Promise<PastResult | null> {
  const results = await loadPastResults();
  return results.find(r => r.roundNumber === roundNumber) || null;
}

/**
 * 指定された回号の前回の当選番号データを取得
 * 
 * @param roundNumber 回号
 * @returns 前回の当選番号データ、見つからない場合はnull
 * @throws DataLoadError データ読み込みエラー
 */
export async function getPreviousResult(
  roundNumber: RoundNumber
): Promise<PastResult | null> {
  return getPastResultByRoundNumber(roundNumber - 1);
}

/**
 * 指定された回号の前々回の当選番号データを取得
 * 
 * @param roundNumber 回号
 * @returns 前々回の当選番号データ、見つからない場合はnull
 * @throws DataLoadError データ読み込みエラー
 */
export async function getPreviousPreviousResult(
  roundNumber: RoundNumber
): Promise<PastResult | null> {
  return getPastResultByRoundNumber(roundNumber - 2);
}

