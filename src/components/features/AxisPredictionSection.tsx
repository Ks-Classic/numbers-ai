'use client';

import { useState } from 'react';
import { Plus } from 'lucide-react';
import { Card } from '@/components/ui/card';
import { usePredictionStore } from '@/lib/store';
import { NumberInputModal } from './NumberInputModal';
import type { AxisCandidate } from '@/types/prediction';

interface AxisPredictionSectionProps {
    axisCandidates: AxisCandidate[];
}

export function AxisPredictionSection({ axisCandidates }: AxisPredictionSectionProps) {
    const { filterState, toggleFilterAxis } = usePredictionStore();
    const [isModalOpen, setIsModalOpen] = useState(false);

    // AI予測済みの軸数字
    const aiPredictedAxes = axisCandidates.map(c => c.axis);

    // 軸追加時の処理
    const handleAddAxes = (numbers: number[]) => {
        numbers.forEach(num => {
            if (!filterState.selectedAxes.includes(num)) {
                toggleFilterAxis(num);
            }
        });
    };

    return (
        <>
            <Card className="p-4">
                <div className="flex items-center justify-between mb-3">
                    <h3 className="text-lg font-bold flex items-center gap-2">
                        🎯 AI軸数字予測
                    </h3>
                    <span className="text-sm text-muted-foreground">
                        タップで選択
                    </span>
                </div>

                {/* 軸数字チップ */}
                <div className="flex flex-wrap gap-2 mb-3">
                    {axisCandidates.slice(0, 5).map((candidate, index) => {
                        const isSelected = filterState.selectedAxes.includes(candidate.axis);

                        return (
                            <button
                                key={candidate.axis}
                                onClick={() => toggleFilterAxis(candidate.axis)}
                                className={`
                  relative flex flex-col items-center justify-center
                  min-w-[60px] h-[70px] rounded-xl
                  transition-all duration-200
                  ${isSelected
                                        ? 'bg-primary text-primary-foreground shadow-lg scale-105 ring-2 ring-primary/50'
                                        : 'bg-muted hover:bg-muted/80 text-foreground'
                                    }
                `}
                            >
                                {/* 順位バッジ */}
                                {index === 0 && (
                                    <span className="absolute -top-1 -left-1 text-[10px] bg-amber-500 text-white px-1.5 py-0.5 rounded-full">
                                        🥇
                                    </span>
                                )}

                                {/* 選択チェック */}
                                {isSelected && (
                                    <span className="absolute -top-1 -right-1 text-[10px] bg-green-500 text-white w-5 h-5 rounded-full flex items-center justify-center">
                                        ✓
                                    </span>
                                )}

                                {/* 数字 */}
                                <span className="text-2xl font-bold">{candidate.axis}</span>

                                {/* スコア */}
                                <span className={`text-xs ${isSelected ? 'text-primary-foreground/80' : 'text-muted-foreground'}`}>
                                    {candidate.score}pt
                                </span>
                            </button>
                        );
                    })}

                    {/* 追加ボタン */}
                    <button
                        onClick={() => setIsModalOpen(true)}
                        className="
              flex flex-col items-center justify-center
              min-w-[60px] h-[70px] rounded-xl
              border-2 border-dashed border-muted-foreground/30
              hover:border-primary hover:bg-primary/5
              transition-all duration-200
              text-muted-foreground hover:text-primary
            "
                    >
                        <Plus className="w-6 h-6" />
                        <span className="text-xs mt-1">追加</span>
                    </button>
                </div>

                {/* 選択中の軸表示 */}
                {filterState.selectedAxes.length > 0 && (
                    <div className="flex items-center gap-2 text-sm text-muted-foreground">
                        <span>選択中:</span>
                        <div className="flex gap-1">
                            {filterState.selectedAxes.sort((a, b) => a - b).map(axis => (
                                <span
                                    key={axis}
                                    className="px-2 py-0.5 bg-primary/20 text-primary rounded font-bold"
                                >
                                    {axis}
                                </span>
                            ))}
                        </div>
                        <span>（{filterState.selectedAxes.length}個）</span>
                    </div>
                )}
            </Card>

            {/* 軸追加モーダル */}
            <NumberInputModal
                isOpen={isModalOpen}
                onClose={() => setIsModalOpen(false)}
                onConfirm={handleAddAxes}
                title="🎯 軸数字を追加"
                description="AI予測外の軸数字を追加できます"
                initialSelected={[]}
                disabledNumbers={filterState.selectedAxes}
                highlightNumbers={aiPredictedAxes}
                mode="axis"
            />
        </>
    );
}
