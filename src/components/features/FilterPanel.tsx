'use client';

import { useState } from 'react';
import { ChevronDown, ChevronUp, X, Plus, RotateCcw } from 'lucide-react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { usePredictionStore } from '@/lib/store';
import { NumberInputModal } from './NumberInputModal';

interface FilterPanelProps {
    originalCount: number;
    filteredCount: number;
}

export function FilterPanel({ originalCount, filteredCount }: FilterPanelProps) {
    const [isExpanded, setIsExpanded] = useState(false);
    const [isExclusionModalOpen, setIsExclusionModalOpen] = useState(false);

    const {
        filterState,
        toggleFilterAxis,
        setAxisCondition,
        addExcludedNumber,
        removeExcludedNumber,
        clearFilters
    } = usePredictionStore();

    const hasActiveFilters =
        filterState.selectedAxes.length > 0 ||
        filterState.excludedNumbers.length > 0;

    const excludedPercentage = originalCount > 0
        ? Math.round(((originalCount - filteredCount) / originalCount) * 100)
        : 0;

    // 削除数字追加時の処理
    const handleAddExcluded = (numbers: number[]) => {
        numbers.forEach(num => addExcludedNumber(num));
    };

    return (
        <>
            <Card className="overflow-hidden">
                {/* ヘッダー（常に表示、折り畳みトグル） */}
                <button
                    onClick={() => setIsExpanded(!isExpanded)}
                    className="w-full flex items-center justify-between p-3 hover:bg-muted/50 transition-colors"
                >
                    <div className="flex items-center gap-2">
                        <span className="text-base">🔧</span>
                        <span className="font-medium">フィルター</span>

                        {/* コンパクトサマリー */}
                        {hasActiveFilters && !isExpanded && (
                            <div className="flex items-center gap-1 text-sm">
                                {filterState.selectedAxes.length > 0 && (
                                    <span className="px-2 py-0.5 bg-primary/20 text-primary rounded">
                                        軸[{filterState.selectedAxes.join(',')}]
                                        <span className="text-xs ml-1">{filterState.axisCondition}</span>
                                    </span>
                                )}
                                {filterState.excludedNumbers.length > 0 && (
                                    <span className="px-2 py-0.5 bg-red-100 text-red-700 rounded">
                                        除外[{filterState.excludedNumbers.join(',')}]
                                    </span>
                                )}
                            </div>
                        )}
                    </div>

                    <div className="flex items-center gap-2">
                        {hasActiveFilters && (
                            <span className={`text-sm ${filteredCount > 0 ? 'text-green-600' : 'text-red-500'}`}>
                                {filteredCount}/{originalCount}件
                            </span>
                        )}
                        {isExpanded ? (
                            <ChevronUp className="w-5 h-5 text-muted-foreground" />
                        ) : (
                            <ChevronDown className="w-5 h-5 text-muted-foreground" />
                        )}
                    </div>
                </button>

                {/* 展開時のコンテンツ */}
                {isExpanded && (
                    <div className="px-4 pb-4 space-y-4 border-t border-border pt-4">
                        {/* 軸数字フィルター */}
                        <div>
                            <div className="flex items-center justify-between mb-2">
                                <h4 className="text-sm font-semibold text-muted-foreground">
                                    🎯 軸数字フィルター
                                </h4>
                            </div>

                            {filterState.selectedAxes.length > 0 ? (
                                <>
                                    {/* 選択中の軸 */}
                                    <div className="flex flex-wrap gap-1 mb-2">
                                        {filterState.selectedAxes.sort((a, b) => a - b).map(axis => (
                                            <span
                                                key={axis}
                                                className="inline-flex items-center gap-1 px-2 py-1 bg-primary/20 text-primary rounded-lg text-sm font-bold"
                                            >
                                                {axis}
                                                <button
                                                    onClick={() => toggleFilterAxis(axis)}
                                                    className="hover:bg-primary/30 rounded-full p-0.5"
                                                >
                                                    <X className="w-3 h-3" />
                                                </button>
                                            </span>
                                        ))}
                                    </div>

                                    {/* AND/OR切り替え */}
                                    <div className="flex items-center gap-2">
                                        <span className="text-xs text-muted-foreground">条件:</span>
                                        <div className="flex rounded-lg overflow-hidden border border-border">
                                            <button
                                                onClick={() => setAxisCondition('AND')}
                                                className={`px-3 py-1 text-xs font-medium transition-colors ${filterState.axisCondition === 'AND'
                                                        ? 'bg-primary text-primary-foreground'
                                                        : 'bg-muted hover:bg-muted/80'
                                                    }`}
                                            >
                                                AND
                                                <span className="hidden sm:inline ml-1">（全て含む）</span>
                                            </button>
                                            <button
                                                onClick={() => setAxisCondition('OR')}
                                                className={`px-3 py-1 text-xs font-medium transition-colors ${filterState.axisCondition === 'OR'
                                                        ? 'bg-primary text-primary-foreground'
                                                        : 'bg-muted hover:bg-muted/80'
                                                    }`}
                                            >
                                                OR
                                                <span className="hidden sm:inline ml-1">（いずれか）</span>
                                            </button>
                                        </div>
                                    </div>
                                </>
                            ) : (
                                <p className="text-sm text-muted-foreground">
                                    上の軸数字をタップして選択してください
                                </p>
                            )}
                        </div>

                        {/* 区切り線 */}
                        <div className="border-t border-border" />

                        {/* 削除数字フィルター */}
                        <div>
                            <div className="flex items-center justify-between mb-2">
                                <h4 className="text-sm font-semibold text-muted-foreground">
                                    ❌ 削除数字フィルター
                                </h4>
                                <Button
                                    variant="ghost"
                                    size="sm"
                                    onClick={() => setIsExclusionModalOpen(true)}
                                    className="h-7 text-xs"
                                >
                                    <Plus className="w-3 h-3 mr-1" />
                                    追加
                                </Button>
                            </div>

                            {filterState.excludedNumbers.length > 0 ? (
                                <div className="flex flex-wrap gap-1">
                                    {filterState.excludedNumbers.sort((a, b) => a - b).map(num => (
                                        <span
                                            key={num}
                                            className="inline-flex items-center gap-1 px-2 py-1 bg-red-100 text-red-700 rounded-lg text-sm font-bold"
                                        >
                                            {num}
                                            <button
                                                onClick={() => removeExcludedNumber(num)}
                                                className="hover:bg-red-200 rounded-full p-0.5"
                                            >
                                                <X className="w-3 h-3" />
                                            </button>
                                        </span>
                                    ))}
                                </div>
                            ) : (
                                <p className="text-sm text-muted-foreground">
                                    除外したい数字を追加してください
                                </p>
                            )}
                        </div>

                        {/* 区切り線 */}
                        <div className="border-t border-border" />

                        {/* フィルター効果 */}
                        <div className="flex items-center justify-between">
                            <div className="text-sm">
                                <span className="text-muted-foreground">フィルター効果: </span>
                                <span className="font-bold">
                                    {originalCount}件 → {filteredCount}件
                                </span>
                                {hasActiveFilters && (
                                    <span className="text-red-500 ml-1">
                                        ({excludedPercentage}%除外)
                                    </span>
                                )}
                            </div>

                            {hasActiveFilters && (
                                <Button
                                    variant="ghost"
                                    size="sm"
                                    onClick={clearFilters}
                                    className="h-7 text-xs text-muted-foreground"
                                >
                                    <RotateCcw className="w-3 h-3 mr-1" />
                                    リセット
                                </Button>
                            )}
                        </div>
                    </div>
                )}
            </Card>

            {/* 削除数字追加モーダル */}
            <NumberInputModal
                isOpen={isExclusionModalOpen}
                onClose={() => setIsExclusionModalOpen(false)}
                onConfirm={handleAddExcluded}
                title="❌ 削除する数字を選択"
                description="選択した数字を含む候補は結果から除外されます"
                initialSelected={[]}
                disabledNumbers={filterState.excludedNumbers}
                mode="exclusion"
            />
        </>
    );
}
