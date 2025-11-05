'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { usePredictionStore } from '@/lib/store';
import { sampleFinalPredictions } from '@/lib/sample-data';
import { ArrowLeft, Share2, RotateCcw, TrendingUp } from 'lucide-react';
import Link from 'next/link';

export default function ResultPage() {
  const router = useRouter();
  const { currentSession } = usePredictionStore();
  const [selectedAxes, setSelectedAxes] = useState<number[]>([]);
  const [activeTab, setActiveTab] = useState('n3');

  const handleShare = () => {
    // 共有機能（今回はアラートで代用）
    alert('共有機能は開発中です');
  };

  const handleReanalyze = () => {
    // 軸選択画面に戻る
    router.push('/predict/axis');
  };

  const toggleAxis = (axis: number) => {
    setSelectedAxes(prev =>
      prev.includes(axis)
        ? prev.filter(a => a !== axis)
        : [...prev, axis]
    );
  };

  // すべての予測結果を確率順に並び替えて取得
  const getAllPredictions = () => {
    const allPredictions: Array<{
      number: string;
      probability: number;
      reason: string;
      pattern: string;
      type: 'straight' | 'box';
    }> = [];

    // N3-Aの予測結果
    sampleFinalPredictions.n3_a.straight.forEach(pred => {
      allPredictions.push({
        number: pred.number,
        probability: pred.probability,
        reason: pred.reason,
        pattern: 'N3-A',
        type: 'straight'
      });
    });
    sampleFinalPredictions.n3_a.box.forEach(pred => {
      allPredictions.push({
        number: pred.number,
        probability: pred.probability,
        reason: pred.reason,
        pattern: 'N3-A',
        type: 'box'
      });
    });

    // N3-Bの予測結果
    sampleFinalPredictions.n3_b.straight.forEach(pred => {
      allPredictions.push({
        number: pred.number,
        probability: pred.probability,
        reason: pred.reason,
        pattern: 'N3-B',
        type: 'straight'
      });
    });
    sampleFinalPredictions.n3_b.box.forEach(pred => {
      allPredictions.push({
        number: pred.number,
        probability: pred.probability,
        reason: pred.reason,
        pattern: 'N3-B',
        type: 'box'
      });
    });

    // N4-Aの予測結果
    sampleFinalPredictions.n4_a.straight.forEach(pred => {
      allPredictions.push({
        number: pred.number,
        probability: pred.probability,
        reason: pred.reason,
        pattern: 'N4-A',
        type: 'straight'
      });
    });
    sampleFinalPredictions.n4_a.box.forEach(pred => {
      allPredictions.push({
        number: pred.number,
        probability: pred.probability,
        reason: pred.reason,
        pattern: 'N4-A',
        type: 'box'
      });
    });

    // N4-Bの予測結果
    sampleFinalPredictions.n4_b.straight.forEach(pred => {
      allPredictions.push({
        number: pred.number,
        probability: pred.probability,
        reason: pred.reason,
        pattern: 'N4-B',
        type: 'straight'
      });
    });
    sampleFinalPredictions.n4_b.box.forEach(pred => {
      allPredictions.push({
        number: pred.number,
        probability: pred.probability,
        reason: pred.reason,
        pattern: 'N4-B',
        type: 'box'
      });
    });

    return allPredictions.sort((a, b) => b.probability - a.probability);
  };

  return (
    <div className="min-h-screen bg-background">
      {/* ヘッダー */}
      <header className="bg-primary text-primary-foreground p-4 md:p-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link href="/predict/axis">
              <ArrowLeft className="w-6 h-6 md:w-7 md:h-7" />
            </Link>
            <h1 className="text-xl md:text-2xl font-bold">ナンバーズAI予測アプリ</h1>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="ghost" size="sm" onClick={handleShare}>
              <Share2 className="w-4 h-4" />
            </Button>
            <Button variant="ghost" size="sm" onClick={handleReanalyze}>
              <RotateCcw className="w-4 h-4" />
            </Button>
          </div>
        </div>
      </header>

      <main className="p-4 md:p-6 lg:p-8 max-w-6xl mx-auto">
        {/* タイトル */}
        <div className="mb-8">
          <h2 className="text-2xl md:text-3xl font-bold mb-4">🏆 全パターン予測結果</h2>
          <div className="flex flex-wrap items-center gap-2 mb-4">
            <Badge className="bg-green-100 text-green-800">ナンバーズ3・4全パターン</Badge>
            <Badge variant="outline">自動予測実行済み</Badge>
          </div>
        </div>

        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="grid w-full grid-cols-3 mb-8">
            <TabsTrigger value="n3">ナンバーズ3</TabsTrigger>
            <TabsTrigger value="n4">ナンバーズ4</TabsTrigger>
            <TabsTrigger value="all">全予測一覧</TabsTrigger>
          </TabsList>

          {/* ナンバーズ3タブ */}
          <TabsContent value="n3" className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* パターンA */}
              <Card className="p-4 md:p-6">
                <div className="flex items-center gap-3 mb-6">
                  <Badge variant="outline">パターンA</Badge>
                </div>

                <div className="space-y-4">
                  <div>
                    <div className="flex items-center gap-2 mb-3">
                      <TrendingUp className="w-5 h-5 text-primary" />
                      <h4 className="text-lg font-semibold">ストレート予測</h4>
                    </div>
                    <div className="space-y-2">
                      {sampleFinalPredictions.n3_a.straight.map((prediction, index) => (
                        <div
                          key={index}
                          className={`p-3 rounded-lg border cursor-pointer transition-all hover:bg-muted/50 ${
                            index === 0 ? 'border-primary bg-primary/5' : 'border-border'
                          }`}
                        >
                          <div className="flex items-center justify-between mb-1">
                            <div className="flex items-center gap-2">
                              <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold ${
                                index === 0 ? 'bg-primary text-primary-foreground' : 'bg-muted text-muted-foreground'
                              }`}>
                                {index + 1}
                              </div>
                              <div className="font-mono text-lg font-bold">
                                {prediction.number}
                              </div>
                            </div>
                            <span className="text-sm font-medium">
                              {(prediction.probability * 100).toFixed(1)}%
                            </span>
                          </div>
                          <div className="text-xs text-muted-foreground">
                            {prediction.reason}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div>
                    <div className="flex items-center gap-2 mb-3">
                      <div className="w-5 h-5 bg-green-500 rounded-sm"></div>
                      <h4 className="text-lg font-semibold">ボックス予測</h4>
                    </div>
                    <div className="space-y-2">
                      {sampleFinalPredictions.n3_a.box.map((prediction, index) => (
                        <div
                          key={index}
                          className={`p-3 rounded-lg border cursor-pointer transition-all hover:bg-muted/50 ${
                            index === 0 ? 'border-green-500 bg-green-50' : 'border-border'
                          }`}
                        >
                          <div className="flex items-center justify-between mb-1">
                            <div className="flex items-center gap-2">
                              <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold ${
                                index === 0 ? 'bg-green-600 text-white' : 'bg-muted text-muted-foreground'
                              }`}>
                                {index + 1}
                              </div>
                              <div className="font-mono text-lg font-bold">
                                {prediction.number}
                              </div>
                            </div>
                            <span className="text-sm font-medium">
                              {(prediction.probability * 100).toFixed(1)}%
                            </span>
                          </div>
                          <div className="text-xs text-muted-foreground">
                            {prediction.reason}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </Card>

              {/* パターンB */}
              <Card className="p-4 md:p-6">
                <div className="flex items-center gap-3 mb-6">
                  <Badge variant="outline">パターンB</Badge>
                </div>

                <div className="space-y-4">
                  <div>
                    <div className="flex items-center gap-2 mb-3">
                      <TrendingUp className="w-5 h-5 text-primary" />
                      <h4 className="text-lg font-semibold">ストレート予測</h4>
                    </div>
                    <div className="space-y-2">
                      {sampleFinalPredictions.n3_b.straight.map((prediction, index) => (
                        <div
                          key={index}
                          className={`p-3 rounded-lg border cursor-pointer transition-all hover:bg-muted/50 ${
                            index === 0 ? 'border-primary bg-primary/5' : 'border-border'
                          }`}
                        >
                          <div className="flex items-center justify-between mb-1">
                            <div className="flex items-center gap-2">
                              <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold ${
                                index === 0 ? 'bg-primary text-primary-foreground' : 'bg-muted text-muted-foreground'
                              }`}>
                                {index + 1}
                              </div>
                              <div className="font-mono text-lg font-bold">
                                {prediction.number}
                              </div>
                            </div>
                            <span className="text-sm font-medium">
                              {(prediction.probability * 100).toFixed(1)}%
                            </span>
                          </div>
                          <div className="text-xs text-muted-foreground">
                            {prediction.reason}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div>
                    <div className="flex items-center gap-2 mb-3">
                      <div className="w-5 h-5 bg-green-500 rounded-sm"></div>
                      <h4 className="text-lg font-semibold">ボックス予測</h4>
                    </div>
                    <div className="space-y-2">
                      {sampleFinalPredictions.n3_b.box.map((prediction, index) => (
                        <div
                          key={index}
                          className={`p-3 rounded-lg border cursor-pointer transition-all hover:bg-muted/50 ${
                            index === 0 ? 'border-green-500 bg-green-50' : 'border-border'
                          }`}
                        >
                          <div className="flex items-center justify-between mb-1">
                            <div className="flex items-center gap-2">
                              <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold ${
                                index === 0 ? 'bg-green-600 text-white' : 'bg-muted text-muted-foreground'
                              }`}>
                                {index + 1}
                              </div>
                              <div className="font-mono text-lg font-bold">
                                {prediction.number}
                              </div>
                            </div>
                            <span className="text-sm font-medium">
                              {(prediction.probability * 100).toFixed(1)}%
                            </span>
                          </div>
                          <div className="text-xs text-muted-foreground">
                            {prediction.reason}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </Card>
            </div>
          </TabsContent>

          {/* ナンバーズ4タブ */}
          <TabsContent value="n4" className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* パターンA */}
              <Card className="p-4 md:p-6">
                <div className="flex items-center gap-3 mb-6">
                  <Badge variant="outline">パターンA</Badge>
                </div>

                <div className="space-y-4">
                  <div>
                    <div className="flex items-center gap-2 mb-3">
                      <TrendingUp className="w-5 h-5 text-primary" />
                      <h4 className="text-lg font-semibold">ストレート予測</h4>
                    </div>
                    <div className="space-y-2">
                      {sampleFinalPredictions.n4_a.straight.map((prediction, index) => (
                        <div
                          key={index}
                          className={`p-3 rounded-lg border cursor-pointer transition-all hover:bg-muted/50 ${
                            index === 0 ? 'border-primary bg-primary/5' : 'border-border'
                          }`}
                        >
                          <div className="flex items-center justify-between mb-1">
                            <div className="flex items-center gap-2">
                              <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold ${
                                index === 0 ? 'bg-primary text-primary-foreground' : 'bg-muted text-muted-foreground'
                              }`}>
                                {index + 1}
                              </div>
                              <div className="font-mono text-lg font-bold">
                                {prediction.number}
                              </div>
                            </div>
                            <span className="text-sm font-medium">
                              {(prediction.probability * 100).toFixed(1)}%
                            </span>
                          </div>
                          <div className="text-xs text-muted-foreground">
                            {prediction.reason}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div>
                    <div className="flex items-center gap-2 mb-3">
                      <div className="w-5 h-5 bg-green-500 rounded-sm"></div>
                      <h4 className="text-lg font-semibold">ボックス予測</h4>
                    </div>
                    <div className="space-y-2">
                      {sampleFinalPredictions.n4_a.box.map((prediction, index) => (
                        <div
                          key={index}
                          className={`p-3 rounded-lg border cursor-pointer transition-all hover:bg-muted/50 ${
                            index === 0 ? 'border-green-500 bg-green-50' : 'border-border'
                          }`}
                        >
                          <div className="flex items-center justify-between mb-1">
                            <div className="flex items-center gap-2">
                              <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold ${
                                index === 0 ? 'bg-green-600 text-white' : 'bg-muted text-muted-foreground'
                              }`}>
                                {index + 1}
                              </div>
                              <div className="font-mono text-lg font-bold">
                                {prediction.number}
                              </div>
                            </div>
                            <span className="text-sm font-medium">
                              {(prediction.probability * 100).toFixed(1)}%
                            </span>
                          </div>
                          <div className="text-xs text-muted-foreground">
                            {prediction.reason}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </Card>

              {/* パターンB */}
              <Card className="p-4 md:p-6">
                <div className="flex items-center gap-3 mb-6">
                  <Badge variant="outline">パターンB</Badge>
                </div>

                <div className="space-y-4">
                  <div>
                    <div className="flex items-center gap-2 mb-3">
                      <TrendingUp className="w-5 h-5 text-primary" />
                      <h4 className="text-lg font-semibold">ストレート予測</h4>
                    </div>
                    <div className="space-y-2">
                      {sampleFinalPredictions.n4_b.straight.map((prediction, index) => (
                        <div
                          key={index}
                          className={`p-3 rounded-lg border cursor-pointer transition-all hover:bg-muted/50 ${
                            index === 0 ? 'border-primary bg-primary/5' : 'border-border'
                          }`}
                        >
                          <div className="flex items-center justify-between mb-1">
                            <div className="flex items-center gap-2">
                              <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold ${
                                index === 0 ? 'bg-primary text-primary-foreground' : 'bg-muted text-muted-foreground'
                              }`}>
                                {index + 1}
                              </div>
                              <div className="font-mono text-lg font-bold">
                                {prediction.number}
                              </div>
                            </div>
                            <span className="text-sm font-medium">
                              {(prediction.probability * 100).toFixed(1)}%
                            </span>
                          </div>
                          <div className="text-xs text-muted-foreground">
                            {prediction.reason}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div>
                    <div className="flex items-center gap-2 mb-3">
                      <div className="w-5 h-5 bg-green-500 rounded-sm"></div>
                      <h4 className="text-lg font-semibold">ボックス予測</h4>
                    </div>
                    <div className="space-y-2">
                      {sampleFinalPredictions.n4_b.box.map((prediction, index) => (
                        <div
                          key={index}
                          className={`p-3 rounded-lg border cursor-pointer transition-all hover:bg-muted/50 ${
                            index === 0 ? 'border-green-500 bg-green-50' : 'border-border'
                          }`}
                        >
                          <div className="flex items-center justify-between mb-1">
                            <div className="flex items-center gap-2">
                              <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold ${
                                index === 0 ? 'bg-green-600 text-white' : 'bg-muted text-muted-foreground'
                              }`}>
                                {index + 1}
                              </div>
                              <div className="font-mono text-lg font-bold">
                                {prediction.number}
                              </div>
                            </div>
                            <span className="text-sm font-medium">
                              {(prediction.probability * 100).toFixed(1)}%
                            </span>
                          </div>
                          <div className="text-xs text-muted-foreground">
                            {prediction.reason}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </Card>
            </div>
          </TabsContent>

          {/* 全予測一覧タブ */}
          <TabsContent value="all" className="space-y-6">
            <Card className="p-4 md:p-6">
              <div className="flex items-center gap-3 mb-6">
                <TrendingUp className="w-6 h-6 text-primary" />
                <h3 className="text-xl md:text-2xl font-semibold">全予測結果（確率順）</h3>
              </div>

              <div className="space-y-3">
                {getAllPredictions().slice(0, 20).map((prediction, index) => (
                  <div
                    key={index}
                    className={`p-3 md:p-4 rounded-lg border cursor-pointer transition-all hover:bg-muted/50 hover:shadow-sm ${
                      index === 0 ? 'border-primary bg-primary/5 shadow-sm' : 'border-border'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-3">
                        <div className={`w-10 h-10 md:w-12 md:h-12 rounded-full flex items-center justify-center text-base md:text-lg font-bold transition-colors ${
                          index === 0 ? 'bg-primary text-primary-foreground' : 'bg-muted text-muted-foreground'
                        }`}>
                          {index + 1}
                        </div>
                        <div>
                          <div className="font-mono text-lg md:text-xl font-bold">
                            {prediction.number}
                          </div>
                          <div className="flex items-center gap-2 mt-1">
                            <Badge variant="outline" className="text-xs">
                              {prediction.pattern}
                            </Badge>
                            <Badge variant={prediction.type === 'straight' ? 'default' : 'secondary'} className="text-xs">
                              {prediction.type === 'straight' ? 'ストレート' : 'ボックス'}
                            </Badge>
                          </div>
                        </div>
                      </div>
                      <div className="text-right">
                        <span className="text-lg md:text-xl font-bold text-primary">
                          {(prediction.probability * 100).toFixed(1)}%
                        </span>
                      </div>
                    </div>
                    <div className="text-xs md:text-sm text-muted-foreground leading-relaxed">
                      {prediction.reason}
                    </div>
                  </div>
                ))}
              </div>

              <div className="mt-6 text-center">
                <Button variant="ghost" size="sm" className="text-muted-foreground">
                  もっと見る ▼
                </Button>
              </div>
            </Card>
          </TabsContent>
        </Tabs>

        {/* アクションボタン */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-8">
          <Button variant="outline" onClick={handleShare} className="h-12 text-base">
            <Share2 className="w-5 h-5 mr-2" />
            共有
          </Button>
          <Button variant="outline" onClick={handleReanalyze} className="h-12 text-base">
            <RotateCcw className="w-5 h-5 mr-2" />
            再分析
          </Button>
        </div>
      </main>
    </div>
  );
}

