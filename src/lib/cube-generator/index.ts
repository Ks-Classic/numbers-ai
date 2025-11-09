/**
 * CUBE生成モジュールのエクスポート（統一）
 * 
 * 予測アプリとCUBE表示ページの両方で使用する統一されたCUBE生成機能を提供
 */

// 通常CUBE生成
export { generateChart } from './chart-generator';

// 極CUBE生成
export { generateExtremeCube } from './extreme-cube';

// 罫線マスターローダー
export { 
  loadKeisenMasterByType, 
  clearKeisenMasterCache,
  type KeisenMasterType 
} from './keisen-master-loader';

// 型定義
export * from './types';

