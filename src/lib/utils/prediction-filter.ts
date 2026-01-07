import type { PredictionItem } from '@/types/prediction';

export interface FilterState {
    selectedAxes: number[];
    axisCondition: 'AND' | 'OR';
    excludedNumbers: number[];
}

/**
 * 軸数字フィルター
 * @param predictions 予測結果
 * @param axes 選択した軸数字
 * @param condition AND: 全ての軸を含む / OR: いずれかの軸を含む
 */
export function filterByAxes(
    predictions: PredictionItem[],
    axes: number[],
    condition: 'AND' | 'OR'
): PredictionItem[] {
    if (axes.length === 0) return predictions;

    return predictions.filter(prediction => {
        const digits = prediction.number.split('').map(Number);

        if (condition === 'AND') {
            // 全ての軸数字を含む
            return axes.every(axis => digits.includes(axis));
        } else {
            // いずれかの軸数字を含む
            return axes.some(axis => digits.includes(axis));
        }
    });
}

/**
 * 削除数字フィルター
 * @param predictions 予測結果
 * @param excluded 除外する数字
 */
export function filterByExclusion(
    predictions: PredictionItem[],
    excluded: number[]
): PredictionItem[] {
    if (excluded.length === 0) return predictions;

    return predictions.filter(prediction => {
        const digits = prediction.number.split('').map(Number);
        // 除外数字を含まない場合のみ残す
        return !excluded.some(ex => digits.includes(ex));
    });
}

/**
 * 統合フィルター（軸フィルター → 削除フィルター の順で適用）
 * @param predictions 予測結果
 * @param filterState フィルター状態
 */
export function applyFilters(
    predictions: PredictionItem[],
    filterState: FilterState
): PredictionItem[] {
    // 1. 軸数字フィルター
    let filtered = filterByAxes(
        predictions,
        filterState.selectedAxes,
        filterState.axisCondition
    );

    // 2. 削除数字フィルター
    filtered = filterByExclusion(filtered, filterState.excludedNumbers);

    return filtered;
}

/**
 * フィルター適用結果の統計を取得
 */
export function getFilterStats(
    originalCount: number,
    filteredCount: number
): { count: number; percentage: number; excluded: number } {
    const excluded = originalCount - filteredCount;
    const percentage = originalCount > 0
        ? Math.round((excluded / originalCount) * 100)
        : 0;

    return {
        count: filteredCount,
        percentage,
        excluded
    };
}

/**
 * 予測結果に含まれる軸数字を取得（どの軸が含まれているかをマーク表示用）
 */
export function getMatchingAxes(
    prediction: PredictionItem,
    selectedAxes: number[]
): number[] {
    const digits = prediction.number.split('').map(Number);
    return selectedAxes.filter(axis => digits.includes(axis));
}
