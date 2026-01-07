'use client';

import { useEffect, useState, useMemo } from 'react';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { usePredictionStore } from '@/lib/store';
import { ArrowLeft } from 'lucide-react';
import Link from 'next/link';
import { AxisPredictionSection } from '@/components/features/AxisPredictionSection';
import { FilterPanel } from '@/components/features/FilterPanel';
import { applyFilters, getMatchingAxes } from '@/lib/utils/prediction-filter';
import type { PredictionItem } from '@/types/prediction';

export default function ResultPage() {
  const {
    currentSession,
    finalPredictions,
    n3FinalPredictions,
    n4FinalPredictions,
    n3AxisCandidates,
    n4AxisCandidates,
    axisCandidates,
    filterState,
    clearFilters
  } = usePredictionStore();

  const [activeTab, setActiveTab] = useState<'n3' | 'n4'>(() => {
    return currentSession.numbersType.toLowerCase() as 'n3' | 'n4';
  });
  const [activeSubTab, setActiveSubTab] = useState<'box' | 'straight'>('box');
  const [showFilterResetNotice, setShowFilterResetNotice] = useState(false);

  // タブ切り替え時にフィルターをリセットし、通知を表示
  const handleTabChange = (newTab: string) => {
    const hasActiveFilters = filterState.selectedAxes.length > 0 || filterState.excludedNumbers.length > 0;
    if (hasActiveFilters && newTab !== activeTab) {
      clearFilters();
      setShowFilterResetNotice(true);
      setTimeout(() => setShowFilterResetNotice(false), 3000);
    }
    setActiveTab(newTab as 'n3' | 'n4');
  };
  // 現在のタブに応じた予測結果を取得
  const currentPredictions = useMemo(() => {
    if (activeTab === 'n3') {
      return n3FinalPredictions || finalPredictions;
    } else if (activeTab === 'n4') {
      return n4FinalPredictions || finalPredictions;
    }
    return null;
  }, [activeTab, n3FinalPredictions, n4FinalPredictions, finalPredictions]);

  // 現在のタブに応じた軸数字候補を取得
  const currentAxisCandidates = useMemo(() => {
    if (activeTab === 'n3') {
      return n3AxisCandidates.length > 0 ? n3AxisCandidates : axisCandidates;
    } else {
      return n4AxisCandidates.length > 0 ? n4AxisCandidates : axisCandidates;
    }
  }, [activeTab, n3AxisCandidates, n4AxisCandidates, axisCandidates]);

  // 現在のサブタブに応じた予測リストを取得
  const currentPredictionList = useMemo(() => {
    if (!currentPredictions) return [];
    return activeSubTab === 'box'
      ? currentPredictions.box
      : currentPredictions.straight;
  }, [currentPredictions, activeSubTab]);

  // フィルター適用後の予測結果
  const filteredPredictions = useMemo(() => {
    return applyFilters(currentPredictionList, filterState);
  }, [currentPredictionList, filterState]);

  // 元の件数とフィルター後の件数
  const originalCount = currentPredictionList.length;
  const filteredCount = filteredPredictions.length;

  // 予測結果アイテムのレンダリング
  const renderPredictionItem = (prediction: PredictionItem, index: number, isBox: boolean) => {
    const matchingAxes = getMatchingAxes(prediction, filterState.selectedAxes);

    return (
      <div
        key={index}
        className={`p-3 rounded-lg border cursor-pointer transition-all hover:bg-muted/50 ${index === 0
          ? isBox
            ? 'border-green-500 bg-green-50'
            : 'border-primary bg-primary/5'
          : 'border-border'
          }`}
      >
        <div className="flex items-center justify-between mb-1">
          <div className="flex items-center gap-2">
            <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold ${index === 0
              ? isBox
                ? 'bg-green-600 text-white'
                : 'bg-primary text-primary-foreground'
              : 'bg-muted text-muted-foreground'
              }`}>
              {index + 1}
            </div>
            <div className="font-mono text-lg font-bold">
              {prediction.number}
            </div>
            {/* マッチした軸を表示 */}
            {matchingAxes.length > 0 && (
              <div className="flex gap-0.5">
                {matchingAxes.map(axis => (
                  <span
                    key={axis}
                    className="text-xs px-1 py-0.5 bg-primary/20 text-primary rounded"
                  >
                    軸{axis}
                  </span>
                ))}
              </div>
            )}
          </div>
          <span className="text-sm font-medium">
            {(prediction.probability * 100).toFixed(1)}%
          </span>
        </div>
        <div className="text-xs text-muted-foreground">
          {prediction.reason}
        </div>
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-background">
      {/* ヘッダー */}
      <header className="bg-primary text-primary-foreground p-4 md:p-6">
        <div className="flex items-center gap-4">
          <Link href="/predict">
            <ArrowLeft className="w-6 h-6 md:w-7 md:h-7" />
          </Link>
          <h1 className="text-xl md:text-2xl font-bold">予測結果</h1>
        </div>
      </header>

      <main className="p-4 md:p-6 lg:p-8 max-w-4xl mx-auto space-y-4">
        {/* セッション情報 */}
        <div className="flex flex-wrap items-center gap-2">
          <Badge variant="outline">第{currentSession.roundNumber}回</Badge>
        </div>

        {/* フィルターリセット通知 */}
        {showFilterResetNotice && (
          <div className="bg-amber-100 border border-amber-300 text-amber-800 px-4 py-2 rounded-lg text-sm animate-in fade-in slide-in-from-top-2 duration-300">
            タブ切り替えのため、フィルター設定をリセットしました
          </div>
        )}

        {/* メインタブ（N3/N4） */}
        <Tabs value={activeTab} onValueChange={handleTabChange} className="w-full">
          <TabsList className="grid w-full grid-cols-2 mb-4">
            <TabsTrigger value="n3">ナンバーズ3</TabsTrigger>
            <TabsTrigger value="n4">ナンバーズ4</TabsTrigger>
          </TabsList>

          {/* N3タブ */}
          <TabsContent value="n3" className="space-y-4">
            {/* AI軸数字予測セクション */}
            <AxisPredictionSection axisCandidates={currentAxisCandidates} />

            {/* フィルター設定パネル */}
            <FilterPanel
              originalCount={originalCount}
              filteredCount={filteredCount}
            />

            {/* サブタブ（ボックス/ストレート） */}
            <Tabs value={activeSubTab} onValueChange={(v) => setActiveSubTab(v as 'box' | 'straight')}>
              <TabsList className="grid w-full grid-cols-2">
                <TabsTrigger value="box">ボックス</TabsTrigger>
                <TabsTrigger value="straight">ストレート</TabsTrigger>
              </TabsList>

              <TabsContent value="box" className="mt-4">
                <Card className="p-4">
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-2">
                      <div className="w-5 h-5 bg-green-500 rounded-sm"></div>
                      <h4 className="text-lg font-semibold">ボックス予測</h4>
                    </div>
                    <Badge variant="outline">{filteredCount}件</Badge>
                  </div>

                  {filteredPredictions.length > 0 ? (
                    <div className="space-y-2">
                      {filteredPredictions.slice(0, 20).map((prediction, index) =>
                        renderPredictionItem(prediction, index, true)
                      )}
                    </div>
                  ) : (
                    <p className="text-center text-muted-foreground py-8">
                      フィルター条件に一致する候補がありません
                    </p>
                  )}
                </Card>
              </TabsContent>

              <TabsContent value="straight" className="mt-4">
                <Card className="p-4">
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-2">
                      <div className="w-5 h-5 bg-primary rounded-sm"></div>
                      <h4 className="text-lg font-semibold">ストレート予測</h4>
                    </div>
                    <Badge variant="outline">{filteredCount}件</Badge>
                  </div>

                  {filteredPredictions.length > 0 ? (
                    <div className="space-y-2">
                      {filteredPredictions.slice(0, 20).map((prediction, index) =>
                        renderPredictionItem(prediction, index, false)
                      )}
                    </div>
                  ) : (
                    <p className="text-center text-muted-foreground py-8">
                      フィルター条件に一致する候補がありません
                    </p>
                  )}
                </Card>
              </TabsContent>
            </Tabs>
          </TabsContent>

          {/* N4タブ */}
          <TabsContent value="n4" className="space-y-4">
            {/* AI軸数字予測セクション */}
            <AxisPredictionSection axisCandidates={currentAxisCandidates} />

            {/* フィルター設定パネル */}
            <FilterPanel
              originalCount={originalCount}
              filteredCount={filteredCount}
            />

            {/* サブタブ（ボックス/ストレート） */}
            <Tabs value={activeSubTab} onValueChange={(v) => setActiveSubTab(v as 'box' | 'straight')}>
              <TabsList className="grid w-full grid-cols-2">
                <TabsTrigger value="box">ボックス</TabsTrigger>
                <TabsTrigger value="straight">ストレート</TabsTrigger>
              </TabsList>

              <TabsContent value="box" className="mt-4">
                <Card className="p-4">
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-2">
                      <div className="w-5 h-5 bg-green-500 rounded-sm"></div>
                      <h4 className="text-lg font-semibold">ボックス予測</h4>
                    </div>
                    <Badge variant="outline">{filteredCount}件</Badge>
                  </div>

                  {filteredPredictions.length > 0 ? (
                    <div className="space-y-2">
                      {filteredPredictions.slice(0, 20).map((prediction, index) =>
                        renderPredictionItem(prediction, index, true)
                      )}
                    </div>
                  ) : (
                    <p className="text-center text-muted-foreground py-8">
                      フィルター条件に一致する候補がありません
                    </p>
                  )}
                </Card>
              </TabsContent>

              <TabsContent value="straight" className="mt-4">
                <Card className="p-4">
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-2">
                      <div className="w-5 h-5 bg-primary rounded-sm"></div>
                      <h4 className="text-lg font-semibold">ストレート予測</h4>
                    </div>
                    <Badge variant="outline">{filteredCount}件</Badge>
                  </div>

                  {filteredPredictions.length > 0 ? (
                    <div className="space-y-2">
                      {filteredPredictions.slice(0, 20).map((prediction, index) =>
                        renderPredictionItem(prediction, index, false)
                      )}
                    </div>
                  ) : (
                    <p className="text-center text-muted-foreground py-8">
                      フィルター条件に一致する候補がありません
                    </p>
                  )}
                </Card>
              </TabsContent>
            </Tabs>
          </TabsContent>
        </Tabs>

      </main>
    </div>
  );
}
