'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { usePredictionStore } from '@/lib/store';
import type { AxisCandidate, PredictionItem } from '@/types/prediction';

// モックの軸数字候補
const mockAxisCandidates: AxisCandidate[] = [
    { axis: 7, confidence: 0.95, chart_score: 450, rehearsal_score: 535, reason: 'リハーサル相関が高い', score: 985, source: 'A1' },
    { axis: 2, confidence: 0.92, chart_score: 420, rehearsal_score: 532, reason: 'チャート出現頻度が高い', score: 952, source: 'A1' },
    { axis: 4, confidence: 0.88, chart_score: 400, rehearsal_score: 516, reason: 'パターンマッチが良好', score: 916, source: 'A1' },
    { axis: 9, confidence: 0.85, chart_score: 380, rehearsal_score: 504, reason: '過去データとの類似性', score: 884, source: 'A1' },
    { axis: 1, confidence: 0.80, chart_score: 360, rehearsal_score: 461, reason: '統計的妥当性', score: 821, source: 'A1' },
    { axis: 5, confidence: 0.75, chart_score: 340, rehearsal_score: 416, reason: '補助指標', score: 756, source: 'A1' },
];

// モックの予測結果
const mockPredictions: { straight: PredictionItem[]; box: PredictionItem[] } = {
    straight: [
        { number: '147', probability: 0.985, reason: '軸7を含む高スコア組み合わせ', score: 985, source: 'A1' },
        { number: '247', probability: 0.972, reason: '軸2,4,7の複合', score: 972, source: 'A1' },
        { number: '279', probability: 0.958, reason: '軸2,7,9の複合', score: 958, source: 'A1' },
        { number: '127', probability: 0.945, reason: '軸1,2,7の複合', score: 945, source: 'A1' },
        { number: '457', probability: 0.932, reason: '軸4,5,7の複合', score: 932, source: 'A1' },
        { number: '179', probability: 0.918, reason: '軸1,7,9の複合', score: 918, source: 'A1' },
        { number: '347', probability: 0.905, reason: '軸4,7の組み合わせ', score: 905, source: 'A1' },
        { number: '257', probability: 0.892, reason: '軸2,5,7の複合', score: 892, source: 'A1' },
        { number: '149', probability: 0.878, reason: '軸1,4,9の複合', score: 878, source: 'A1' },
        { number: '245', probability: 0.865, reason: '軸2,4,5の複合', score: 865, source: 'A1' },
        { number: '357', probability: 0.852, reason: '軸5,7の組み合わせ', score: 852, source: 'A1' },
        { number: '129', probability: 0.838, reason: '軸1,2,9の複合', score: 838, source: 'A1' },
        { number: '459', probability: 0.825, reason: '軸4,5,9の複合', score: 825, source: 'A1' },
        { number: '234', probability: 0.812, reason: '軸2,4の組み合わせ', score: 812, source: 'A1' },
        { number: '567', probability: 0.798, reason: '軸5,7の組み合わせ', score: 798, source: 'A1' },
        { number: '389', probability: 0.785, reason: '軸9の組み合わせ', score: 785, source: 'A1' },
        { number: '012', probability: 0.772, reason: '軸1,2の組み合わせ', score: 772, source: 'A1' },
        { number: '678', probability: 0.758, reason: '7を含む組み合わせ', score: 758, source: 'A1' },
        { number: '890', probability: 0.745, reason: '9を含む組み合わせ', score: 745, source: 'A1' },
        { number: '036', probability: 0.732, reason: '補助候補', score: 732, source: 'A1' },
    ],
    box: [
        { number: '147', probability: 0.978, reason: '軸7を含むボックス高スコア', score: 978, source: 'A1' },
        { number: '247', probability: 0.965, reason: '軸2,4,7の複合ボックス', score: 965, source: 'A1' },
        { number: '279', probability: 0.952, reason: '軸2,7,9の複合ボックス', score: 952, source: 'A1' },
        { number: '127', probability: 0.938, reason: '軸1,2,7の複合ボックス', score: 938, source: 'A1' },
        { number: '457', probability: 0.925, reason: '軸4,5,7の複合ボックス', score: 925, source: 'A1' },
        { number: '179', probability: 0.912, reason: '軸1,7,9の複合ボックス', score: 912, source: 'A1' },
        { number: '347', probability: 0.898, reason: '軸4,7のボックス', score: 898, source: 'A1' },
        { number: '257', probability: 0.885, reason: '軸2,5,7の複合ボックス', score: 885, source: 'A1' },
        { number: '149', probability: 0.872, reason: '軸1,4,9の複合ボックス', score: 872, source: 'A1' },
        { number: '245', probability: 0.858, reason: '軸2,4,5の複合ボックス', score: 858, source: 'A1' },
        { number: '357', probability: 0.845, reason: '軸5,7のボックス', score: 845, source: 'A1' },
        { number: '129', probability: 0.832, reason: '軸1,2,9の複合ボックス', score: 832, source: 'A1' },
        { number: '459', probability: 0.818, reason: '軸4,5,9の複合ボックス', score: 818, source: 'A1' },
        { number: '234', probability: 0.805, reason: '軸2,4のボックス', score: 805, source: 'A1' },
        { number: '567', probability: 0.792, reason: '軸5,7のボックス', score: 792, source: 'A1' },
        { number: '389', probability: 0.778, reason: '軸9のボックス', score: 778, source: 'A1' },
        { number: '012', probability: 0.765, reason: '軸1,2のボックス', score: 765, source: 'A1' },
        { number: '678', probability: 0.752, reason: '7を含むボックス', score: 752, source: 'A1' },
        { number: '890', probability: 0.738, reason: '9を含むボックス', score: 738, source: 'A1' },
        { number: '036', probability: 0.725, reason: '補助候補ボックス', score: 725, source: 'A1' },
    ]
};

export default function TestResultPage() {
    const router = useRouter();
    const { setSessionData, setN3Data, setN4Data } = usePredictionStore();

    useEffect(() => {
        // モックデータをストアにセット
        setSessionData({
            roundNumber: 6701,
            numbersType: 'N3',
            patternType: 'A1',
            rehearsalN3: '149',
            rehearsalN4: '3782',
        });

        // N3用データ
        setN3Data(mockAxisCandidates, mockPredictions);

        // N4用データ（少し変更）
        setN4Data(
            mockAxisCandidates.map(c => ({ ...c, score: c.score - 10 })),
            {
                straight: mockPredictions.straight.map(p => ({
                    ...p,
                    number: p.number + '8',
                    probability: p.probability * 0.98
                })),
                box: mockPredictions.box.map(p => ({
                    ...p,
                    number: p.number + '8',
                    probability: p.probability * 0.98
                })),
            }
        );

        // 結果ページにリダイレクト
        router.push('/predict/result');
    }, [router, setSessionData, setN3Data, setN4Data]);

    return (
        <div className="min-h-screen bg-background flex items-center justify-center">
            <div className="text-center">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
                <p className="text-lg font-medium">テストデータを読み込み中...</p>
                <p className="text-sm text-muted-foreground mt-2">結果画面にリダイレクトします</p>
            </div>
        </div>
    );
}
