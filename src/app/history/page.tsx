'use client';

import { useEffect } from 'react';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { useHistoryStore } from '@/lib/store';
import { sampleHistoryData } from '@/lib/sample-data';
import { Navigation } from '@/components/shared/Navigation';
import { History as HistoryIcon, Filter, Eye, TrendingUp, TrendingDown } from 'lucide-react';

export default function HistoryPage() {
  const { historyData, setHistoryData } = useHistoryStore();

  useEffect(() => {
    // サンプルデータをストアに設定
    setHistoryData(sampleHistoryData);
  }, [setHistoryData]);

  return (
    <div className="min-h-screen bg-background pb-16">
      {/* ヘッダー */}
      <header className="bg-primary text-primary-foreground p-4 md:p-6">
        <div className="flex items-center gap-3">
          <HistoryIcon className="w-7 h-7 md:w-8 md:h-8" />
          <h1 className="text-xl md:text-2xl font-bold">予測履歴</h1>
        </div>
      </header>

      <main className="p-4 md:p-6 lg:p-8 max-w-6xl mx-auto">
        {/* フィルター */}
        <Card className="p-4 md:p-6 mb-8">
          <div className="flex items-center gap-3 mb-4">
            <Filter className="w-6 h-6 text-primary" />
            <span className="text-lg font-medium">フィルター</span>
          </div>

          <div className="flex flex-col sm:flex-row gap-4">
            <Select defaultValue="all">
              <SelectTrigger className="flex-1">
                <SelectValue placeholder="タイプを選択" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">全て</SelectItem>
                <SelectItem value="N3">ナンバーズ3</SelectItem>
                <SelectItem value="N4">ナンバーズ4</SelectItem>
              </SelectContent>
            </Select>

            <Select defaultValue="all">
              <SelectTrigger className="flex-1">
                <SelectValue placeholder="期間を選択" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">全て</SelectItem>
                <SelectItem value="month">今月</SelectItem>
                <SelectItem value="week">今週</SelectItem>
                <SelectItem value="today">今日</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </Card>

        {/* 履歴リスト */}
        <div className="space-y-4 md:space-y-6">
          {historyData.map((item) => (
            <Card key={item.id} className="p-4 md:p-6 hover:shadow-lg transition-shadow">
              <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4 mb-4">
                <div className="flex items-center gap-3">
                  <Badge variant={item.numbers_type === 'N3' ? 'default' : 'secondary'} className="text-sm">
                    {item.numbers_type}
                  </Badge>
                  <span className="text-base md:text-lg text-muted-foreground font-medium">
                    {item.date} ({item.round}回)
                  </span>
                </div>

                <div className="flex items-center gap-2">
                  {item.is_hit ? (
                    <Badge className="bg-green-100 text-green-800 text-sm">
                      <TrendingUp className="w-4 h-4 mr-1" />
                      的中
                    </Badge>
                  ) : (
                    <Badge variant="destructive" className="text-sm">
                      <TrendingDown className="w-4 h-4 mr-1" />
                      はずれ
                    </Badge>
                  )}
                </div>
              </div>

              <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
                <div className="space-y-2">
                  <div className="text-sm text-muted-foreground">選択軸</div>
                  <div className="font-mono text-lg md:text-xl font-bold">
                    {item.selected_axes.join(', ')}
                  </div>
                </div>

                <div className="space-y-2">
                  <div className="text-sm text-muted-foreground">予測番号</div>
                  <div className="font-mono text-lg md:text-xl font-bold">
                    {item.predicted_number}
                  </div>
                  <div className="text-xs text-muted-foreground">
                    {item.prediction_type === 'straight' ? 'ストレート' : 'ボックス'}
                  </div>
                </div>

                <div className="space-y-2">
                  <div className="text-sm text-muted-foreground">当選番号</div>
                  <div className="font-mono text-lg md:text-xl font-bold">
                    {item.actual_winning}
                  </div>
                </div>

                <div className="space-y-2">
                  <div className="text-sm text-muted-foreground">信頼度</div>
                  <div className="text-xl md:text-2xl font-bold text-primary">
                    {(item.confidence * 100).toFixed(1)}%
                  </div>
                </div>
              </div>

              <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center pt-4 border-t gap-3">
                <div className="text-sm text-muted-foreground">
                  予測日時: {new Date(item.predicted_at).toLocaleDateString('ja-JP')}
                </div>

                <Button variant="ghost" size="sm" className="self-start sm:self-auto">
                  <Eye className="w-4 h-4 mr-2" />
                  詳細を見る
                </Button>
              </div>
            </Card>
          ))}
        </div>

        {/* さらに読み込みボタン */}
        <div className="text-center mt-8">
          <Button variant="outline" size="lg">
            さらに読み込む
          </Button>
        </div>
      </main>

      {/* ナビゲーション */}
      <Navigation />
    </div>
  );
}

