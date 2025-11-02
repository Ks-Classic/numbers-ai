'use client';

import { useEffect } from 'react';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { useStatisticsStore } from '@/lib/store';
import { sampleStatisticsData, samplePredictionTypeStats } from '@/lib/sample-data';
import { Navigation } from '@/components/shared/Navigation';
import { TrendingUp, Target, Award, BarChart3 } from 'lucide-react';

export default function StatisticsPage() {
  const { statisticsData, setStatisticsData } = useStatisticsStore();

  useEffect(() => {
    // サンプルデータをストアに設定
    setStatisticsData(sampleStatisticsData);
  }, [setStatisticsData]);

  if (!statisticsData) {
    return <div>Loading...</div>;
  }

  return (
    <div className="min-h-screen bg-background pb-16">
      {/* ヘッダー */}
      <header className="bg-primary text-primary-foreground p-4 md:p-6">
        <div className="flex items-center gap-3">
          <BarChart3 className="w-7 h-7 md:w-8 md:h-8" />
          <h1 className="text-xl md:text-2xl font-bold">統計・分析</h1>
        </div>
      </header>

      <main className="p-4 md:p-6 lg:p-8 max-w-6xl mx-auto space-y-6">
        {/* 概要統計カード */}
        <Card className="p-4 md:p-6">
          <div className="flex items-center gap-3 mb-6">
            <TrendingUp className="w-6 h-6 text-primary" />
            <h2 className="text-xl md:text-2xl font-semibold">的中率推移（30日）</h2>
          </div>

          {/* 簡易チャート（実際にはRechartsを使用） */}
          <div className="mb-6">
            <div className="flex items-end justify-between h-32 md:h-40 mb-3">
              {statisticsData.trend_data.map((point, index) => (
                <div key={index} className="flex flex-col items-center gap-2">
                  <div
                    className="w-8 md:w-10 bg-primary rounded-t-sm transition-all duration-300"
                    style={{ height: `${point.accuracy * 100}%` }}
                  />
                  <span className="text-xs md:text-sm text-muted-foreground font-medium">
                    {point.date.split('-')[2]}
                  </span>
                </div>
              ))}
            </div>
            <div className="flex justify-between text-sm text-muted-foreground">
              <span>10/1</span>
              <span className="font-medium">平均: {statisticsData.metrics.overall_accuracy * 100}%</span>
              <span>10/30</span>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4 md:gap-6">
            <div className="text-center p-4 bg-muted/50 rounded-lg">
              <div className="text-3xl md:text-4xl font-bold text-green-600 mb-2">
                {statisticsData.metrics.overall_accuracy * 100}%
              </div>
              <div className="text-sm md:text-base text-muted-foreground">平均的中率</div>
            </div>
            <div className="text-center p-4 bg-muted/50 rounded-lg">
              <div className="text-3xl md:text-4xl font-bold text-blue-600 mb-2">
                {statisticsData.metrics.axis_accuracy * 100}%
              </div>
              <div className="text-sm md:text-base text-muted-foreground">軸的中率</div>
            </div>
          </div>
        </Card>

        {/* 軸数字別的中率と予測タイプ別実績 */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* 軸数字別的中率 */}
          <Card className="p-4 md:p-6">
            <div className="flex items-center gap-3 mb-6">
              <Target className="w-6 h-6 text-primary" />
              <h2 className="text-xl md:text-2xl font-semibold">軸数字別的中率</h2>
            </div>

            <div className="space-y-4">
              {statisticsData.axis_breakdown.map((axis) => (
                <div key={axis.axis} className="flex items-center gap-4">
                  <div className="w-12 h-12 md:w-14 md:h-14 bg-primary text-primary-foreground rounded-full flex items-center justify-center font-bold text-lg">
                    {axis.axis}
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <div className="flex-1 bg-muted rounded-full h-3 overflow-hidden">
                        <div
                          className="h-full bg-primary rounded-full transition-all duration-500"
                          style={{ width: `${axis.accuracy * 100}%` }}
                        />
                      </div>
                      <span className="text-base md:text-lg font-medium min-w-[4rem]">
                        {(axis.accuracy * 100).toFixed(0)}%
                      </span>
                    </div>
                    <div className="text-sm text-muted-foreground">
                      {axis.hits}/{axis.total_used} 回的中
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </Card>

          {/* 予測タイプ別実績 */}
          <Card className="p-4 md:p-6">
            <div className="flex items-center gap-3 mb-6">
              <Award className="w-6 h-6 text-primary" />
              <h2 className="text-xl md:text-2xl font-semibold">予測タイプ別実績</h2>
            </div>

            <div className="space-y-4">
              {samplePredictionTypeStats.map((stat) => (
                <div key={stat.name} className="flex items-center gap-4">
                  <div className="w-5 h-5 rounded-sm" style={{ backgroundColor: stat.fill }}></div>
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <span className="text-base md:text-lg font-medium">{stat.name}</span>
                      <div className="flex-1 bg-muted rounded-full h-3 overflow-hidden">
                        <div
                          className="h-full rounded-full transition-all duration-500"
                          style={{
                            width: `${stat.value}%`,
                            backgroundColor: stat.fill
                          }}
                        />
                      </div>
                      <span className="text-base md:text-lg font-medium min-w-[4rem]">
                        {stat.value}%
                      </span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </Card>
        </div>

        {/* 詳細統計情報 */}
        <Card className="p-4 md:p-6">
          <h2 className="text-xl md:text-2xl font-semibold mb-6">詳細統計情報</h2>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center p-4 bg-muted/50 rounded-lg">
              <div className="text-3xl md:text-4xl font-bold text-primary mb-2">
                {statisticsData.metrics.total_predictions}
              </div>
              <div className="text-sm md:text-base text-muted-foreground">総予測数</div>
            </div>

            <div className="text-center p-4 bg-muted/50 rounded-lg">
              <div className="text-3xl md:text-4xl font-bold text-green-600 mb-2">
                {statisticsData.metrics.hits.straight + statisticsData.metrics.hits.box}
              </div>
              <div className="text-sm md:text-base text-muted-foreground">総的中数</div>
            </div>

            <div className="text-center p-4 bg-muted/50 rounded-lg">
              <div className="text-3xl md:text-4xl font-bold text-blue-600 mb-2">
                {statisticsData.metrics.straight_accuracy * 100}%
              </div>
              <div className="text-sm md:text-base text-muted-foreground">ストレート的中率</div>
            </div>

            <div className="text-center p-4 bg-muted/50 rounded-lg">
              <div className="text-3xl md:text-4xl font-bold text-purple-600 mb-2">
                {statisticsData.metrics.box_accuracy * 100}%
              </div>
              <div className="text-sm md:text-base text-muted-foreground">ボックス的中率</div>
            </div>
          </div>
        </Card>
      </main>

      {/* ナビゲーション */}
      <Navigation />
    </div>
  );
}

