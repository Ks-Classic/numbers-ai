/**
 * 罫線マスターデータの読み込みユーティリティ（統一）
 * 
 * 現罫線（keisen_master.json）と新罫線（keisen_master_new.json）の両方を読み込む機能を提供
 */

import { promises as fs } from 'fs';
import path from 'path';
import { KeisenMaster, DataLoadError } from '@/lib/data-loader/types';

/**
 * JSONファイルのパス（プロジェクトルートからの相対パス）
 */
const CURRENT_KEISEN_PATH = path.join(process.cwd(), 'data', 'keisen_master.json');
const NEW_KEISEN_PATH = path.join(process.cwd(), 'data', 'keisen_master_new.json');

/**
 * 罫線マスターデータをキャッシュする変数
 */
let cachedKeisenMasterCurrent: KeisenMaster | null = null;
let cachedKeisenMasterNew: KeisenMaster | null = null;

/**
 * 罫線マスターデータの種類
 */
export type KeisenMasterType = 'current' | 'new';

/**
 * 罫線マスターデータを読み込む（種類指定）
 * 
 * @param keisenType 'current'（現罫線）または'new'（新罫線）
 * @param useCache キャッシュを使用するか（デフォルト: true）
 * @returns 罫線マスターデータ
 * @throws DataLoadError ファイル読み込みエラーまたはデータフォーマットエラー
 */
export async function loadKeisenMasterByType(
  keisenType: KeisenMasterType,
  useCache: boolean = true
): Promise<KeisenMaster> {
  // キャッシュから返す
  if (useCache) {
    if (keisenType === 'current' && cachedKeisenMasterCurrent) {
      return cachedKeisenMasterCurrent;
    }
    if (keisenType === 'new' && cachedKeisenMasterNew) {
      return cachedKeisenMasterNew;
    }
  }
  
  const jsonPath = keisenType === 'new' ? NEW_KEISEN_PATH : CURRENT_KEISEN_PATH;
  
  try {
    const fileContent = await fs.readFile(jsonPath, 'utf-8');
    const data = JSON.parse(fileContent) as unknown;
    
    // データの検証（簡易版、必要に応じて詳細なバリデーションを追加）
    if (!data || typeof data !== 'object') {
      throw new DataLoadError('罫線マスターデータがオブジェクトではありません');
    }
    
    const validatedData = data as KeisenMaster;
    
    // キャッシュに保存
    if (useCache) {
      if (keisenType === 'current') {
        cachedKeisenMasterCurrent = validatedData;
      } else {
        cachedKeisenMasterNew = validatedData;
      }
    }
    
    return validatedData;
  } catch (error) {
    if (error instanceof DataLoadError) {
      throw error;
    }
    
    if ((error as NodeJS.ErrnoException).code === 'ENOENT') {
      throw new DataLoadError(
        `罫線マスターファイルが見つかりません: ${jsonPath}`,
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
      `罫線マスターファイルの読み込みに失敗しました: ${(error as Error).message}`,
      error
    );
  }
}

/**
 * キャッシュをクリアする
 * 
 * @param keisenType クリアする罫線マスターの種類（指定しない場合は両方）
 */
export function clearKeisenMasterCache(keisenType?: KeisenMasterType): void {
  if (!keisenType || keisenType === 'current') {
    cachedKeisenMasterCurrent = null;
  }
  if (!keisenType || keisenType === 'new') {
    cachedKeisenMasterNew = null;
  }
}

