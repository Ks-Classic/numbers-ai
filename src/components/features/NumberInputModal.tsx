'use client';

import { useState, useEffect } from 'react';
import { X } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface NumberInputModalProps {
    isOpen: boolean;
    onClose: () => void;
    onConfirm: (numbers: number[]) => void;
    title: string;
    description?: string;
    initialSelected?: number[];
    disabledNumbers?: number[];  // AI予測済みなど選択不可の数字
    highlightNumbers?: number[]; // ハイライト表示する数字（AI予測済み等）
    mode: 'axis' | 'exclusion';  // 軸追加 or 削除数字
}

export function NumberInputModal({
    isOpen,
    onClose,
    onConfirm,
    title,
    description,
    initialSelected = [],
    disabledNumbers = [],
    highlightNumbers = [],
    mode
}: NumberInputModalProps) {
    const [selected, setSelected] = useState<number[]>(initialSelected);

    useEffect(() => {
        setSelected(initialSelected);
    }, [initialSelected, isOpen]);

    const toggleNumber = (num: number) => {
        if (disabledNumbers.includes(num)) return;

        setSelected(prev =>
            prev.includes(num)
                ? prev.filter(n => n !== num)
                : [...prev, num]
        );
    };

    const handleConfirm = () => {
        onConfirm(selected);
        onClose();
    };

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
            {/* オーバーレイ */}
            <div
                className="absolute inset-0 bg-black/60 backdrop-blur-sm"
                onClick={onClose}
            />

            {/* モーダル */}
            <div className="relative bg-card rounded-2xl shadow-2xl w-[90vw] max-w-sm mx-4 overflow-hidden animate-in fade-in zoom-in-95 duration-200">
                {/* ヘッダー */}
                <div className="flex items-center justify-between p-4 border-b border-border">
                    <h3 className="text-lg font-bold">{title}</h3>
                    <button
                        onClick={onClose}
                        className="p-1 rounded-full hover:bg-muted transition-colors"
                    >
                        <X className="w-5 h-5" />
                    </button>
                </div>

                {/* コンテンツ */}
                <div className="p-4">
                    {description && (
                        <p className="text-sm text-muted-foreground mb-4">{description}</p>
                    )}

                    {/* 数字グリッド */}
                    <div className="grid grid-cols-5 gap-2">
                        {[0, 1, 2, 3, 4, 5, 6, 7, 8, 9].map(num => {
                            const isSelected = selected.includes(num);
                            const isDisabled = disabledNumbers.includes(num);
                            const isHighlighted = highlightNumbers.includes(num);

                            return (
                                <button
                                    key={num}
                                    onClick={() => toggleNumber(num)}
                                    disabled={isDisabled}
                                    className={`
                    relative w-14 h-14 rounded-xl font-bold text-xl
                    transition-all duration-200
                    flex items-center justify-center
                    ${isDisabled
                                            ? 'bg-muted text-muted-foreground cursor-not-allowed opacity-50'
                                            : isSelected
                                                ? mode === 'exclusion'
                                                    ? 'bg-red-500 text-white shadow-lg scale-105'
                                                    : 'bg-primary text-primary-foreground shadow-lg scale-105'
                                                : 'bg-muted hover:bg-muted/80 text-foreground'
                                        }
                  `}
                                >
                                    {num}
                                    {isHighlighted && !isDisabled && (
                                        <span className="absolute -top-1 -right-1 text-[10px] bg-amber-500 text-white px-1 rounded">
                                            AI
                                        </span>
                                    )}
                                    {isSelected && (
                                        <span className="absolute -top-1 -right-1 text-[10px] bg-green-500 text-white w-4 h-4 rounded-full flex items-center justify-center">
                                            ✓
                                        </span>
                                    )}
                                </button>
                            );
                        })}
                    </div>

                    {/* 選択中の表示 */}
                    {selected.length > 0 && (
                        <div className="mt-4 p-3 bg-muted rounded-lg">
                            <p className="text-sm text-muted-foreground mb-1">
                                {mode === 'exclusion' ? '除外する数字:' : '追加する軸:'}
                            </p>
                            <div className="flex flex-wrap gap-1">
                                {selected.sort((a, b) => a - b).map(num => (
                                    <span
                                        key={num}
                                        className={`px-2 py-1 rounded text-sm font-bold ${mode === 'exclusion'
                                                ? 'bg-red-100 text-red-700'
                                                : 'bg-primary/20 text-primary'
                                            }`}
                                    >
                                        {num}
                                    </span>
                                ))}
                            </div>
                        </div>
                    )}
                </div>

                {/* フッター */}
                <div className="flex gap-2 p-4 border-t border-border">
                    <Button
                        variant="outline"
                        onClick={onClose}
                        className="flex-1"
                    >
                        キャンセル
                    </Button>
                    <Button
                        onClick={handleConfirm}
                        className={`flex-1 ${mode === 'exclusion' ? 'bg-red-500 hover:bg-red-600' : ''}`}
                    >
                        {selected.length > 0 ? `${selected.length}個を追加` : '完了'}
                    </Button>
                </div>
            </div>
        </div>
    );
}
