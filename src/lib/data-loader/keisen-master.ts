/**
 * 罫線マスターデータの読み込みユーティリティ
 */

import { promises as fs } from 'fs';
import path from 'path';
import { KeisenMaster, DataLoadError, ColumnName, PredictedDigits, N3KeisenMaster, N4KeisenMaster, ColumnRules } from './types';

/**
 * JSONファイルのパス（プロジェクトルートからの相対パス）
 */
const JSON_FILE_PATH = path.join(process.cwd(), 'data', 'keisen_master.json');

/**
 * 罫線マスターデータをキャッシュする変数
 */
let cachedKeisenMaster: KeisenMaster | null = null;

/**
 * 罫線マスターデータを読み込む
 * 
 * @param useCache キャッシュを使用するか（デフォルト: true）
 * @returns 罫線マスターデータ
 * @throws DataLoadError ファイル読み込みエラーまたはデータフォーマットエラー
 */
export async function loadKeisenMaster(useCache: boolean = true): Promise<KeisenMaster> {
  // キャッシュから返す
  if (useCache && cachedKeisenMaster) {
    return cachedKeisenMaster;
  }
  
  try {
    const fileContent = await fs.readFile(JSON_FILE_PATH, 'utf-8');
    const data = JSON.parse(fileContent) as unknown;
    
    // データの検証
    const validatedData = validateKeisenMaster(data);
    
    // キャッシュに保存
    if (useCache) {
      cachedKeisenMaster = validatedData;
    }
    
    return validatedData;
  } catch (error) {
    if (error instanceof DataLoadError) {
      throw error;
    }
    
    if ((error as NodeJS.ErrnoException).code === 'ENOENT') {
      throw new DataLoadError(
        `データファイルが見つかりません: ${JSON_FILE_PATH}`,
        error
      );
    }
    
    if (error instanceof SyntaxError) {
      throw new DataLoadError(
        `JSONファイルのパースに失敗しました: ${error.message}`,
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
 * 罫線マスターデータのバリデーション
 * 
 * @param data 検証するデータ
 * @returns 検証済みの罫線マスターデータ
 * @throws DataLoadError バリデーションエラー
 */
function validateKeisenMaster(data: unknown): KeisenMaster {
  if (!data || typeof data !== 'object') {
    throw new DataLoadError('罫線マスターデータがオブジェクトではありません');
  }
  
  const obj = data as Record<string, unknown>;
  
  // n3とn4が存在するか確認
  if (!obj.n3 || typeof obj.n3 !== 'object') {
    throw new DataLoadError('n3データが存在しません');
  }
  
  if (!obj.n4 || typeof obj.n4 !== 'object') {
    throw new DataLoadError('n4データが存在しません');
  }
  
  // N3の検証
  const n3Data = obj.n3 as Record<string, unknown>;
  validateN3KeisenMaster(n3Data);
  
  // N4の検証
  const n4Data = obj.n4 as Record<string, unknown>;
  validateN4KeisenMaster(n4Data);
  
  return data as KeisenMaster;
}

/**
 * N3の罫線マスターデータを検証
 */
function validateN3KeisenMaster(data: Record<string, unknown>): void {
  const requiredColumns: Array<'百の位' | '十の位' | '一の位'> = ['百の位', '十の位', '一の位'];
  
  for (const columnName of requiredColumns) {
    if (!data[columnName] || typeof data[columnName] !== 'object') {
      throw new DataLoadError(`N3の${columnName}データが存在しません`);
    }
    
    validateColumnRules(data[columnName] as Record<string, unknown>, `N3.${columnName}`);
  }
}

/**
 * N4の罫線マスターデータを検証
 */
function validateN4KeisenMaster(data: Record<string, unknown>): void {
  const requiredColumns: Array<'千の位' | '百の位' | '十の位' | '一の位'> = [
    '千の位',
    '百の位',
    '十の位',
    '一の位',
  ];
  
  for (const columnName of requiredColumns) {
    if (!data[columnName] || typeof data[columnName] !== 'object') {
      throw new DataLoadError(`N4の${columnName}データが存在しません`);
    }
    
    validateColumnRules(data[columnName] as Record<string, unknown>, `N4.${columnName}`);
  }
}

/**
 * 桁ごとの予測ルールを検証
 * 
 * JSONの構造: 外側のキーが前々回、内側のキーが前回
 * 例: "4": { "0": [...], "1": [...], ... } → 前々回=4、前回=0の場合
 */
function validateColumnRules(
  rules: Record<string, unknown>,
  context: string
): void {
  // 前々回の数字は0-9である必要がある（外側のキー）
  for (let prevPrevDigit = 0; prevPrevDigit <= 9; prevPrevDigit++) {
    const prevPrevKey = String(prevPrevDigit);
    
    if (!rules[prevPrevKey] || typeof rules[prevPrevKey] !== 'object') {
      throw new DataLoadError(`${context}の前々回数字"${prevPrevDigit}"のデータが存在しません`);
    }
    
    const prevMap = rules[prevPrevKey] as Record<string, unknown>;
    
    // 前回の数字は0-9である必要がある（内側のキー）
    for (let prevDigit = 0; prevDigit <= 9; prevDigit++) {
      const prevKey = String(prevDigit);
      
      if (!(prevKey in prevMap)) {
        throw new DataLoadError(
          `${context}の前々回"${prevPrevDigit}"、前回"${prevDigit}"のデータが存在しません`
        );
      }
      
      const predictedDigits = prevMap[prevKey];
      
      // 予測出目は配列である必要がある
      if (!Array.isArray(predictedDigits)) {
        throw new DataLoadError(
          `${context}の前々回"${prevPrevDigit}"、前回"${prevDigit}"の予測出目が配列ではありません`
        );
      }
      
      // 配列の各要素は0-9の数値である必要がある
      for (const digit of predictedDigits) {
        if (typeof digit !== 'number' || digit < 0 || digit > 9 || !Number.isInteger(digit)) {
          throw new DataLoadError(
            `${context}の前々回"${prevPrevDigit}"、前回"${prevDigit}"の予測出目に不正な値が含まれています: ${digit}`
          );
        }
      }
    }
  }
}

/**
 * 指定された条件で予測出目を取得
 * 
 * @param target 'n3' または 'n4'
 * @param columnName 桁名（例: '百の位'）
 * @param previousDigit 前回の数字（0-9）
 * @param previousPreviousDigit 前々回の数字（0-9）
 * @returns 予測出目の配列
 * @throws DataLoadError データ読み込みエラーまたはデータが見つからない場合
 */
export async function getPredictedDigits(
  target: 'n3' | 'n4',
  columnName: ColumnName,
  previousDigit: number,
  previousPreviousDigit: number
): Promise<PredictedDigits> {
  // 入力値の検証
  if (!Number.isInteger(previousDigit) || previousDigit < 0 || previousDigit > 9) {
    throw new DataLoadError(`前回の数字が不正です: ${previousDigit}`);
  }
  
  if (!Number.isInteger(previousPreviousDigit) || previousPreviousDigit < 0 || previousPreviousDigit > 9) {
    throw new DataLoadError(`前々回の数字が不正です: ${previousPreviousDigit}`);
  }
  
  const master = await loadKeisenMaster();
  
  const targetData = master[target];
  
  if (!targetData || typeof targetData !== 'object') {
    throw new DataLoadError(`${target}データが見つかりません`);
  }
  
  // targetに応じて適切な型をアサート
  let columnData: ColumnRules | undefined;
  if (target === 'n3') {
    const n3Data = targetData as N3KeisenMaster;
    if (columnName === '百の位' || columnName === '十の位' || columnName === '一の位') {
      columnData = n3Data[columnName];
    } else {
      throw new DataLoadError(`N3では${columnName}は使用できません`);
    }
  } else {
    const n4Data = targetData as N4KeisenMaster;
    if (columnName === '千の位' || columnName === '百の位' || columnName === '十の位' || columnName === '一の位') {
      columnData = n4Data[columnName];
    } else {
      throw new DataLoadError(`N4では${columnName}は使用できません`);
    }
  }
  
  if (!columnData || typeof columnData !== 'object') {
    throw new DataLoadError(`${target}の${columnName}データが見つかりません`);
  }
  
  // JSONの構造: 外側のキーが前々回、内側のキーが前回
  // 例: "4": { "0": [...], "1": [...], ... } → 前々回=4、前回=0の場合
  const previousPreviousMap = columnData[String(previousPreviousDigit)];
  
  if (!previousPreviousMap || typeof previousPreviousMap !== 'object') {
    throw new DataLoadError(
      `${target}の${columnName}で前々回"${previousPreviousDigit}"のデータが見つかりません`
    );
  }
  
  const predictedDigits = previousPreviousMap[String(previousDigit)];
  
  if (!Array.isArray(predictedDigits)) {
    throw new DataLoadError(
      `${target}の${columnName}で前々回"${previousPreviousDigit}"、前回"${previousDigit}"の予測出目が見つかりません`
    );
  }
  
  return predictedDigits;
}

/**
 * キャッシュをクリアする
 */
export function clearKeisenMasterCache(): void {
  cachedKeisenMaster = null;
}

