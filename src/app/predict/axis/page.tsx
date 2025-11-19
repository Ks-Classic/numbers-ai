'use client';

import { useState, useMemo } from 'react';
import { Card } from '@/components/ui/card';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { usePredictionStore } from '@/lib/store';
import { sampleAxisCandidates, sampleAxisCandidatesN4 } from '@/lib/sample-data';
import { ArrowLeft, ChevronDown, ChevronUp } from 'lucide-react';
import Link from 'next/link';
import type { PredictionItem } from '@/types/prediction';

export default function AxisPage() {
  // データ取得（ストアから取得）
  const { 
    axisCandidates: storeAxisCandidates, 
    finalPredictions, 
    currentSession, 
    setSessionData,
    n3AxisCandidates,
    n4AxisCandidates,
    n3FinalPredictions,
    n4FinalPredictions,
  } = usePredictionStore();
  
  // メインタブ: N3/N4（ストアの値と同期）
  const [mainTab, setMainTab] = useState<'N3' | 'N4'>(currentSession.numbersType);
  // サブタブ: box/straight
  const [subTab, setSubTab] = useState<'box' | 'straight'>('box');
  // 表示モード: 軸数字候補 or 総合ランキング
  const [viewMode, setViewMode] = useState<'axis' | 'overall'>('axis');
  // 展開中の軸
  const [expandedAxes, setExpandedAxes] = useState<Set<number>>(new Set());
  // モーダル表示状態
  const [openDialog, setOpenDialog] = useState<'score' | 'source' | null>(null);
  // 手動指定用のstate
  const [customAxis, setCustomAxis] = useState<string>('');
  const [isCustomExpanded, setIsCustomExpanded] = useState(false);
  const [customCandidates, setCustomCandidates] = useState<PredictionItem[]>([]);
  const [isCalculating, setIsCalculating] = useState(false); // 計算中フラグ

  // N3/N4に応じてデータをフィルタリング
  const axisCandidates = useMemo(() => {
    console.log('axisCandidates再計算:', {
      mainTab,
      currentSessionNumbersType: currentSession.numbersType,
      storeAxisCandidatesLength: storeAxisCandidates.length,
      n3AxisCandidatesLength: n3AxisCandidates.length,
      n4AxisCandidatesLength: n4AxisCandidates.length,
    });
    
    // mainTabに応じて適切なデータを返す
    if (mainTab === 'N3') {
      if (n3AxisCandidates.length > 0) {
        console.log('N3データを使用（n3AxisCandidates）:', n3AxisCandidates.length, '件');
        return n3AxisCandidates;
      }
      console.log('N3サンプルデータを使用');
      return sampleAxisCandidates;
    } else {
      if (n4AxisCandidates.length > 0) {
        console.log('N4データを使用（n4AxisCandidates）:', n4AxisCandidates.length, '件');
        return n4AxisCandidates;
      }
      console.log('N4サンプルデータを使用');
      return sampleAxisCandidatesN4;
    }
  }, [mainTab, n3AxisCandidates, n4AxisCandidates]);
  
  // タブ切り替え時に手動指定状態をリセット
  const handleMainTabChange = (v: string) => {
    const newTab = v as 'N3' | 'N4';
    console.log('=== タブ切り替え開始 ===');
    console.log('タブ切り替え:', {
      from: mainTab,
      to: newTab,
      currentSessionNumbersType: currentSession.numbersType,
      storeAxisCandidatesLength: storeAxisCandidates.length,
      n3AxisCandidatesLength: n3AxisCandidates.length,
      n4AxisCandidatesLength: n4AxisCandidates.length,
    });
    
    setMainTab(newTab);
    // ストアのnumbersTypeも更新（これによりaxisCandidatesが再計算される）
    setSessionData({ numbersType: newTab });
    setCustomAxis('');
    setIsCustomExpanded(false);
    setCustomCandidates([]);
    
    console.log('タブ切り替え完了:', {
      newTab,
      storeAxisCandidatesLength: storeAxisCandidates.length,
      n3AxisCandidatesLength: n3AxisCandidates.length,
      n4AxisCandidatesLength: n4AxisCandidates.length,
    });
    console.log('=== タブ切り替え終了 ===');
  };

  const handleSubTabChange = (v: string) => {
    setSubTab(v as 'box' | 'straight');
    setCustomAxis('');
    setIsCustomExpanded(false);
    setCustomCandidates([]);
  };

  // 軸の展開/折りたたみ
  const toggleAxisExpansion = (axis: number) => {
    const newExpanded = new Set(expandedAxes);
    if (newExpanded.has(axis)) {
      newExpanded.delete(axis);
    } else {
      newExpanded.add(axis);
    }
    setExpandedAxes(newExpanded);
  };

  // 総合ランキング用：全候補をスコア順に取得
  const allCandidates = useMemo((): PredictionItem[] => {
    console.log('allCandidates再計算:', {
      subTab,
      axisCandidatesLength: axisCandidates.length,
    });
    
    const all: PredictionItem[] = [];
    if (Array.isArray(axisCandidates)) {
      axisCandidates.forEach((axis, idx) => {
        if (subTab === 'box' && axis.candidates?.box && Array.isArray(axis.candidates.box)) {
          console.log(`軸数字${axis.axis}のbox候補数:`, axis.candidates.box.length);
          all.push(...axis.candidates.box);
        } else if (subTab === 'straight' && axis.candidates?.straight && Array.isArray(axis.candidates.straight)) {
          console.log(`軸数字${axis.axis}のstraight候補数:`, axis.candidates.straight.length);
          all.push(...axis.candidates.straight);
        }
      });
    }
    
    console.log('allCandidates収集結果:', {
      subTab,
      totalCount: all.length,
      sampleNumbers: all.slice(0, 5).map(item => item.number),
    });
    
    // スコア順にソート（降順）、重複を除去（番号が同じものは1つだけ）
    const unique = all.filter((item, index, self) => 
      item.number && index === self.findIndex(t => t.number === item.number)
    );
    const sorted = unique.sort((a, b) => (b.score || 0) - (a.score || 0)).slice(0, 20);
    
    console.log('allCandidates最終結果:', {
      subTab,
      uniqueCount: sorted.length,
      sampleNumbers: sorted.slice(0, 5).map(item => item.number),
    });
    
    return sorted;
  }, [axisCandidates, subTab]);

  // 手動指定軸の候補を計算
  const calculateCustomCandidates = async () => {
    const axisNum = parseInt(customAxis);
    if (isNaN(axisNum) || axisNum < 0 || axisNum > 9) {
      alert('0-9の数字を入力してください');
      return;
    }

    console.log('手動指定軸の候補を計算開始:', {
      axisNum,
      subTab,
      mainTab,
      currentSessionNumbersType: currentSession.numbersType,
    });

    // まず既存の候補からフィルタリングを試みる
    const localCandidates: PredictionItem[] = [];
    if (Array.isArray(axisCandidates)) {
      axisCandidates.forEach(axis => {
        if (subTab === 'box' && axis.candidates?.box && Array.isArray(axis.candidates.box)) {
          localCandidates.push(...axis.candidates.box);
        } else if (subTab === 'straight' && axis.candidates?.straight && Array.isArray(axis.candidates.straight)) {
          localCandidates.push(...axis.candidates.straight);
        }
      });
    }

    // 指定された軸数字を含む候補をフィルタリング
    const filtered = localCandidates.filter(item => {
      return item.number && item.number.includes(axisNum.toString());
    });

    // 既存の候補に該当するものがある場合は、それを使用
    if (filtered.length > 0) {
      console.log('既存の候補からフィルタリング:', filtered.length, '件');
      const sorted = filtered.sort((a, b) => (b.score || 0) - (a.score || 0)).slice(0, 10); // 10位まで
      setCustomCandidates(sorted);
      setIsCustomExpanded(true);
      return;
    }

    // 既存の候補にない場合、APIを呼び出して新しく予測を実行
    console.log('既存の候補にないため、APIを呼び出して新しく予測を実行します');
    
    try {
      setIsCalculating(true);
      // ローディング状態を設定
      setIsCustomExpanded(false);
      
      const target = mainTab.toLowerCase() as 'n3' | 'n4';
      const rehearsalDigits = target === 'n3' ? currentSession.rehearsalN3 : currentSession.rehearsalN4;
      
      if (!rehearsalDigits) {
        alert('リハーサル数字が設定されていません');
        setIsCalculating(false);
        return;
      }

      // 最良パターンを取得（currentSessionから、またはデフォルト）
      const bestPattern = currentSession.patternType || 'A1';

      // 組み合わせ予測APIを呼び出し（指定された軸数字のみを使用）
      // Next.js API Routeを使用（Vercel Python関数またはFastAPIサーバーに自動的にルーティング）
      const response = await fetch('/api/predict/combination', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          round_number: currentSession.roundNumber,
          target: target,
          combo_type: subTab,
          best_pattern: bestPattern,
          top_axis_digits: [axisNum], // 指定された軸数字のみを使用
          rehearsal_digits: rehearsalDigits,
          max_combinations: 100,
        }),
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`予測エラー: ${response.status} ${response.statusText} - ${errorText}`);
      }

      const result = await response.json();
      
      console.log('API予測結果:', {
        combinationsCount: result.combinations?.length || 0,
      });

      // レスポンスをPredictionItem形式に変換
      const candidates: PredictionItem[] = (result.combinations || []).map((item: any) => ({
        number: item.combination,
        score: item.score,
        probability: item.score / 1000, // スコアを確率に変換
        reason: `スコア: ${item.score.toFixed(1)}`,
        source: bestPattern as any,
      }));

      // スコア順にソート
      const sorted = candidates.sort((a, b) => (b.score || 0) - (a.score || 0)).slice(0, 10); // 10位まで
      
      setCustomCandidates(sorted);
      setIsCustomExpanded(true);
      
      console.log('手動指定軸の候補を計算完了:', sorted.length, '件');
    } catch (error: any) {
      console.error('手動指定軸の予測エラー:', error);
      alert(`予測エラー: ${error.message || '予測の実行に失敗しました'}`);
    } finally {
      setIsCalculating(false);
    }
  };

  return (
    <div className="min-h-screen bg-background pb-16">
      {/* ヘッダー */}
      <header className="bg-primary text-primary-foreground p-3 md:p-4">
        <div className="flex items-center gap-2">
          <Link href="/predict/rehearsal">
            <ArrowLeft className="w-6 h-6 md:w-7 md:h-7" />
          </Link>
          <h1 className="text-base md:text-lg font-semibold">分析結果</h1>
        </div>
      </header>

      <main className="p-4 md:p-6 lg:p-8 max-w-6xl mx-auto">
        {/* タイトル */}
        <div className="mb-4">
          <h2 className="text-lg md:text-xl font-semibold mb-1">
            第{currentSession.roundNumber}回
          </h2>
        </div>

        {/* メインタブ：N3/N4 */}
        <Tabs value={mainTab} onValueChange={handleMainTabChange} className="mb-4">
          <TabsList className="grid w-full grid-cols-2 h-10 bg-muted/50 rounded-lg p-1 mb-4">
            <TabsTrigger 
              value="N3" 
              className="text-sm md:text-base font-medium data-[state=active]:bg-primary data-[state=active]:text-primary-foreground data-[state=active]:font-semibold data-[state=active]:shadow-sm data-[state=inactive]:text-muted-foreground transition-all"
            >
              {mainTab === 'N3' && <span className="mr-1 text-xs">●</span>}N3
            </TabsTrigger>
            <TabsTrigger 
              value="N4" 
              className="text-sm md:text-base font-medium data-[state=active]:bg-primary data-[state=active]:text-primary-foreground data-[state=active]:font-semibold data-[state=active]:shadow-sm data-[state=inactive]:text-muted-foreground transition-all"
            >
              {mainTab === 'N4' && <span className="mr-1 text-xs">●</span>}N4
            </TabsTrigger>
          </TabsList>

          <TabsContent value={mainTab}>
            {/* サブタブ：ボックス/ストレート */}
            <Tabs value={subTab} onValueChange={handleSubTabChange} className="mb-4">
              <TabsList className="grid w-full grid-cols-2 h-9 bg-muted/50 rounded-lg p-1 mb-4">
                <TabsTrigger 
                  value="box" 
                  className="text-sm md:text-base font-medium data-[state=active]:bg-primary data-[state=active]:text-primary-foreground data-[state=active]:font-semibold data-[state=active]:shadow-sm data-[state=inactive]:text-muted-foreground transition-all"
                >
                  {subTab === 'box' && <span className="mr-1 text-xs">●</span>}ボックス
                </TabsTrigger>
                <TabsTrigger 
                  value="straight" 
                  className="text-sm md:text-base font-medium data-[state=active]:bg-primary data-[state=active]:text-primary-foreground data-[state=active]:font-semibold data-[state=active]:shadow-sm data-[state=inactive]:text-muted-foreground transition-all"
                >
                  {subTab === 'straight' && <span className="mr-1 text-xs">●</span>}ストレート
                </TabsTrigger>
              </TabsList>

              <TabsContent value={subTab}>
                {/* 表示モード切り替え：軸数字候補 / 総合ランキング */}
                <div className="mb-4">
                  <div className="inline-flex rounded-lg bg-muted/50 p-1 border border-border">
                    <button
                      onClick={() => setViewMode('axis')}
                      className={`px-4 py-2 rounded-md text-sm md:text-base font-medium transition-all ${
                        viewMode === 'axis'
                          ? 'text-primary-foreground bg-primary font-semibold shadow-sm'
                          : 'text-muted-foreground hover:text-foreground hover:bg-muted/80'
                      }`}
                    >
                      {viewMode === 'axis' && <span className="mr-1 text-xs">●</span>}
                      軸数字
                    </button>
                    <button
                      onClick={() => setViewMode('overall')}
                      className={`px-4 py-2 rounded-md text-sm md:text-base font-medium transition-all ${
                        viewMode === 'overall'
                          ? 'text-primary-foreground bg-primary font-semibold shadow-sm'
                          : 'text-muted-foreground hover:text-foreground hover:bg-muted/80'
                      }`}
                    >
                      {viewMode === 'overall' && <span className="mr-1 text-xs">●</span>}
                      総合
                    </button>
                  </div>
                </div>

                {viewMode === 'overall' ? (
                  /* 総合ランキング：軸数字なしで全候補を表示 */
                  <Card className="p-4 md:p-5">
                    <div className="overflow-x-auto">
                      <table className="w-full">
                        <thead>
                          <tr className="border-b-2 border-border">
                            <th className="text-left p-2.5 text-sm md:text-base font-semibold">#</th>
                            <th className="text-left p-2.5 text-sm md:text-base font-semibold">番号</th>
                            <th 
                              className="text-left p-2.5 text-sm md:text-base font-semibold cursor-pointer hover:text-primary underline underline-offset-2 transition-colors"
                              onClick={(e) => {
                                e.stopPropagation();
                                setOpenDialog('score');
                              }}
                            >
                              スコア
                            </th>
                          </tr>
                        </thead>
                        <tbody>
                          {allCandidates.length > 0 ? (
                            allCandidates.map((item, index) => (
                              <tr key={index} className="border-b border-border hover:bg-muted/50 transition-colors">
                                    <td className="p-2.5 text-sm md:text-base">{index + 1}</td>
                                    <td className="p-2.5 text-base md:text-lg font-bold">{item.number}</td>
                                    <td 
                                      className="p-2.5 text-sm md:text-base cursor-pointer hover:text-primary underline underline-offset-1 transition-colors"
                                      onClick={(e) => {
                                        e.stopPropagation();
                                        setOpenDialog('score');
                                      }}
                                    >
                                      {typeof item.score === 'number' ? item.score.toFixed(1) : (item.score || '-')}
                                    </td>
                              </tr>
                            ))
                          ) : (
                            <tr>
                              <td colSpan={3} className="p-4 text-center text-sm text-muted-foreground">
                                候補が見つかりませんでした
                              </td>
                            </tr>
                          )}
                        </tbody>
                      </table>
                    </div>
                  </Card>
                ) : (
                  /* 軸数字候補リスト（アコーディオン） */
                  <div className="space-y-3">
                    {Array.isArray(axisCandidates) && axisCandidates
                      .sort((a, b) => (b.score || 0) - (a.score || 0))
                      .slice(0, 5) // 軸数字は5位まで表示
                      .map((axis, index) => {
                        const isExpanded = expandedAxes.has(axis.axis);
                        const candidates = subTab === 'box' ? (axis.candidates?.box || []) : (axis.candidates?.straight || []);
                        
                        console.log(`軸数字${axis.axis}表示:`, {
                          subTab,
                          boxCount: axis.candidates?.box?.length || 0,
                          straightCount: axis.candidates?.straight?.length || 0,
                          selectedCandidatesCount: candidates.length,
                          selectedSampleNumbers: candidates.slice(0, 3).map((c: any) => c.number),
                        });

                        return (
                          <Card key={axis.axis} className="overflow-hidden">
                            {/* 軸ヘッダー */}
                            <div
                              className="p-3 md:p-4 cursor-pointer hover:bg-muted/50 transition-colors"
                              onClick={() => toggleAxisExpansion(axis.axis)}
                            >
                              <div className="flex items-center justify-between gap-3">
                                <div className="flex items-center gap-3 flex-1 min-w-0">
                                  <div className="w-12 h-12 md:w-14 md:h-14 rounded-full bg-primary text-primary-foreground flex items-center justify-center text-lg md:text-xl font-bold flex-shrink-0">
                                    {axis.axis}
                                  </div>
                                  <div className="flex items-center gap-3 flex-1 min-w-0">
                                    <span className="text-sm md:text-base font-medium whitespace-nowrap">
                                      {index + 1}位
                                    </span>
                                    <span className="text-muted-foreground">|</span>
                                    <span 
                                      className="text-sm md:text-base font-bold whitespace-nowrap cursor-pointer hover:text-primary underline underline-offset-2 transition-colors"
                                      onClick={(e) => {
                                        e.stopPropagation();
                                        setOpenDialog('score');
                                      }}
                                    >
                                      スコア: {typeof axis.score === 'number' ? axis.score.toFixed(1) : axis.score}
                                    </span>
                                  </div>
                                </div>
                                <div className="flex-shrink-0">
                                  {isExpanded ? (
                                    <ChevronUp className="w-5 h-5 text-muted-foreground" />
                                  ) : (
                                    <ChevronDown className="w-5 h-5 text-muted-foreground" />
                                  )}
                                </div>
                              </div>
                            </div>

                            {/* 当選番号候補リスト（展開時のみ表示） */}
                            {isExpanded && candidates && candidates.length > 0 && (
                              <div className="border-t border-border bg-muted/30 p-3 md:p-4">
                                <div className="overflow-x-auto">
                                  <table className="w-full">
                                    <thead>
                                      <tr className="border-b-2 border-border">
                                        <th className="text-left p-2.5 text-sm md:text-base font-semibold">#</th>
                                        <th className="text-left p-2.5 text-sm md:text-base font-semibold">番号</th>
                                        <th 
                                          className="text-left p-2.5 text-sm md:text-base font-semibold cursor-pointer hover:text-primary underline underline-offset-2 transition-colors"
                                          onClick={(e) => {
                                            e.stopPropagation();
                                            setOpenDialog('score');
                                          }}
                                        >
                                          スコア
                                        </th>
                                      </tr>
                                    </thead>
                                    <tbody>
                                      {candidates.slice(0, 10).map((item, idx) => ( // 軸数字内の番号は10位まで表示
                                        <tr key={idx} className="border-b border-border hover:bg-muted/50 transition-colors">
                                          <td className="p-2.5 text-sm md:text-base">{idx + 1}</td>
                                          <td className="p-2.5 text-base md:text-lg font-bold">{item.number}</td>
                                          <td 
                                            className="p-2.5 text-sm md:text-base cursor-pointer hover:text-primary underline underline-offset-1 transition-colors"
                                            onClick={(e) => {
                                              e.stopPropagation();
                                              setOpenDialog('score');
                                            }}
                                          >
                                            {typeof item.score === 'number' ? item.score.toFixed(1) : (item.score || '-')}
                                          </td>
                                        </tr>
                                      ))}
                                    </tbody>
                                  </table>
                                </div>
                              </div>
                            )}
                          </Card>
                        );
                      })}

                    {/* 手動指定ブロック */}
                    <Card className="overflow-hidden border-2 border-dashed border-primary/30 bg-muted/20">
                      <div className="p-3 md:p-4">
                        <div className="flex items-center gap-3">
                          <div className="w-12 h-12 md:w-14 md:h-14 rounded-full border-2 border-primary bg-background flex items-center justify-center flex-shrink-0">
                            <Input
                              type="tel"
                              value={customAxis}
                              onChange={(e) => {
                                const value = e.target.value.replace(/[^0-9]/g, '').slice(0, 1);
                                setCustomAxis(value);
                                setIsCustomExpanded(false);
                                setCustomCandidates([]);
                              }}
                              className="w-full h-full text-center text-xl md:text-2xl font-bold p-0 border-0 focus-visible:ring-0 focus-visible:ring-offset-0 bg-transparent rounded-full placeholder:text-muted-foreground/50"
                              placeholder="?"
                              inputMode="numeric"
                              pattern="[0-9]*"
                              maxLength={1}
                            />
                          </div>
                          <div className="flex items-center gap-2 flex-1 min-w-0">
                            <span className="text-sm md:text-base font-medium whitespace-nowrap">
                              指定
                            </span>
                            <Button
                              onClick={(e) => {
                                e.stopPropagation();
                                calculateCustomCandidates();
                              }}
                              disabled={!customAxis || isCalculating}
                              size="sm"
                              className="text-xs md:text-sm h-8 md:h-9 px-4"
                            >
                              {isCalculating ? '計算中...' : '計算'}
                            </Button>
                          </div>
                          <div className="ml-auto flex-shrink-0">
                            {isCustomExpanded ? (
                              <ChevronUp 
                                className="w-5 h-5 text-muted-foreground cursor-pointer hover:text-foreground transition-colors"
                                onClick={(e) => {
                                  e.stopPropagation();
                                  setIsCustomExpanded(false);
                                }}
                              />
                            ) : (
                              <ChevronDown 
                                className="w-5 h-5 text-muted-foreground cursor-pointer hover:text-foreground transition-colors"
                                onClick={(e) => {
                                  e.stopPropagation();
                                  if (customCandidates.length > 0) {
                                    setIsCustomExpanded(true);
                                  }
                                }}
                              />
                            )}
                          </div>
                        </div>

                        {/* 当選番号候補リスト（展開時のみ表示） */}
                        {isCustomExpanded && customCandidates.length > 0 && (
                          <div className="border-t border-border bg-muted/30 p-3 md:p-4 mt-3">
                            <div className="overflow-x-auto">
                              <table className="w-full">
                                <thead>
                                  <tr className="border-b-2 border-border">
                                    <th className="text-left p-2.5 text-sm md:text-base font-semibold">#</th>
                                    <th className="text-left p-2.5 text-sm md:text-base font-semibold">番号</th>
                                    <th 
                                      className="text-left p-2.5 text-sm md:text-base font-semibold cursor-pointer hover:text-primary underline underline-offset-2 transition-colors"
                                      onClick={(e) => {
                                        e.stopPropagation();
                                        setOpenDialog('score');
                                      }}
                                    >
                                      スコア
                                    </th>
                                  </tr>
                                </thead>
                                <tbody>
                                  {customCandidates.map((item, idx) => (
                                    <tr key={idx} className="border-b border-border hover:bg-muted/50 transition-colors">
                                      <td className="p-2.5 text-sm md:text-base">{idx + 1}</td>
                                      <td className="p-2.5 text-base md:text-lg font-bold">{item.number}</td>
                                      <td 
                                        className="p-2.5 text-sm md:text-base cursor-pointer hover:text-primary underline underline-offset-1 transition-colors"
                                        onClick={(e) => {
                                          e.stopPropagation();
                                          setOpenDialog('score');
                                        }}
                                      >
                                        {typeof item.score === 'number' ? item.score.toFixed(1) : (item.score || '-')}
                                      </td>
                                    </tr>
                                  ))}
                                </tbody>
                              </table>
                            </div>
                          </div>
                        )}
                      </div>
                    </Card>
                  </div>
                )}
              </TabsContent>
            </Tabs>
          </TabsContent>
        </Tabs>
      </main>

      {/* スコア説明モーダル */}
      <Dialog open={openDialog === 'score'} onOpenChange={(open) => !open && setOpenDialog(null)}>
        <DialogContent className="max-w-[90vw] sm:max-w-lg max-h-[85vh] overflow-y-auto p-5 md:p-6">
          <DialogHeader>
            <DialogTitle className="text-lg md:text-xl font-bold">スコア</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 text-base md:text-lg leading-relaxed">
            <div>
              <h3 className="font-semibold mb-2">AIスコアとは？</h3>
              <p className="mb-2">
                これは、AIが過去の膨大なデータから学習した<strong className="font-semibold">「勝ちパターン」に、この候補がどれだけ似ているかを評価した「有望さ」を示す点数</strong>です。
              </p>
              <p>
                点数が高いほど、AIが「過去の当選例と照らし合わせて、非常に興味深い形や位置関係にある」と判断していることを示します。
              </p>
            </div>
            <div className="pt-2 border-t">
              <p className="font-semibold text-primary mb-2">【重要】</p>
              <p>
                このスコアは、当選を保証する<strong className="font-semibold">「確率（%）」ではありません</strong>。あくまで、たくさんの候補の中から、どれがより有望かを比較・検討するための<strong className="font-semibold">「AI独自の評価点」</strong>としてご活用ください。
              </p>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* 出所説明モーダル */}
      <Dialog open={openDialog === 'source'} onOpenChange={(open) => !open && setOpenDialog(null)}>
        <DialogContent className="max-w-[90vw] sm:max-w-lg max-h-[85vh] overflow-y-auto p-5 md:p-6">
          <DialogHeader>
            <DialogTitle className="text-lg md:text-xl font-bold">出所（0なし / 0あり）とは？</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 text-base md:text-lg leading-relaxed">
            <div>
              <p className="mb-2">
                このAIは、2種類の異なるルールで作られた予測表（チャート）を同時に分析しています。
              </p>
              <p>
                この「出所」は、その候補が<strong className="font-semibold">「どちらの表から見つけ出されたか」</strong>を示しています。
              </p>
            </div>
            <div className="pt-2 border-t">
              <p className="font-semibold text-primary mb-2">【活用ヒント】</p>
              <p>
                もし、スコアランキングの上位に<strong className="font-semibold">「0なし」</strong>の候補が多く並んでいる日があれば、その日は「0なし」の表が示すパターンの影響が強い、と考えることができます。2つの世界のどちらが優勢かを見極める、重要な手がかりとなります。
              </p>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}

