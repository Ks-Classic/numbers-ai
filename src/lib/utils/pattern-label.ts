/**
 * パターン名を分かりやすい表現に変換するユーティリティ
 */

import type { Pattern } from '@/types/prediction';

/**
 * パターンの説明を取得
 * @param pattern パターン（A1/A2/B1/B2）
 * @returns パターンの説明オブジェクト
 */
export function getPatternDescription(pattern: Pattern): {
  label: string;
  centerZero: boolean;
  missingFill: boolean;
} {
  switch (pattern) {
    case 'A1':
      return {
        label: '表0追加なし・欠番補足あり',
        centerZero: false,
        missingFill: true,
      };
    case 'A2':
      return {
        label: '表0追加あり・欠番補足あり',
        centerZero: true,
        missingFill: true,
      };
    case 'B1':
      return {
        label: '表0追加なし・欠番補足なし',
        centerZero: false,
        missingFill: false,
      };
    case 'B2':
      return {
        label: '表0追加あり・欠番補足なし',
        centerZero: true,
        missingFill: false,
      };
  }
}

/**
 * パターン名を短いラベルに変換（表示用）
 * @param pattern パターン（A1/A2/B1/B2）
 * @returns 短いラベル（例: "表0なし・欠番あり"）
 */
export function getPatternLabel(pattern: Pattern): string {
  return getPatternDescription(pattern).label;
}

/**
 * パターン名を短いラベルに変換（コンパクト版）
 * @param pattern パターン（A1/A2/B1/B2）
 * @returns 短いラベル（例: "表0なし/欠番あり"）
 */
export function getPatternLabelCompact(pattern: Pattern): string {
  const desc = getPatternDescription(pattern);
  const centerZeroLabel = desc.centerZero ? '表0あり' : '表0なし';
  const missingFillLabel = desc.missingFill ? '欠番あり' : '欠番なし';
  return `${centerZeroLabel}/${missingFillLabel}`;
}

