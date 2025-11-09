'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card } from '@/components/ui/card';
import { fetchCubes, gridToTSV, type CubeData, type CubesResponse } from '@/lib/cube-api';
import { Copy, Loader2, Grid3x3, Zap, Check } from 'lucide-react';
import { toast } from 'sonner';

export default function CubePage() {
  const [roundNumber, setRoundNumber] = useState<number | ''>('');
  const [cubes, setCubes] = useState<CubeData[]>([]);
  const [currentRoundNumber, setCurrentRoundNumber] = useState<number | null>(null);
  const [extractedDigits, setExtractedDigits] = useState<CubesResponse['extracted_digits'] | null>(null);
  const [activeKeisenType, setActiveKeisenType] = useState<'current' | 'new'>('current');
  const [activeCubeType, setActiveCubeType] = useState<'normal' | 'extreme'>('normal');
  const [activeTarget, setActiveTarget] = useState<'n3' | 'n4'>('n3');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [copiedCubeId, setCopiedCubeId] = useState<string | null>(null);

  const handleGenerate = async () => {
    if (!roundNumber || roundNumber < 1) {
      toast.error('有効な回号を入力してください');
      return;
    }

    setLoading(true);
    setError(null);
    setCubes([]);
    setExtractedDigits(null);

    try {
      const data = await fetchCubes(roundNumber);
      setCubes(data.cubes);
      setCurrentRoundNumber(data.round_number);
      setExtractedDigits(data.extracted_digits);
      toast.success(`${data.cubes.length}個のCUBEを生成しました`);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'CUBE生成に失敗しました';
      setError(errorMessage);
      toast.error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleCopy = async (cube: CubeData) => {
    try {
      const tsv = gridToTSV(cube.grid, cube.rows, cube.cols);
      await navigator.clipboard.writeText(tsv);
      setCopiedCubeId(cube.id);
      toast.success('クリップボードにコピーしました。Excelに貼り付けてください。');
      setTimeout(() => setCopiedCubeId(null), 2000);
    } catch (err) {
      toast.error('コピーに失敗しました');
    }
  };

  // CUBEを階層的にグループ化
  const groupCubesByHierarchy = (cubes: CubeData[]) => {
    const grouped: {
      [keisenType: string]: {
        [cubeType: string]: {
          [target: string]: CubeData[];
        };
      };
    } = {};

    cubes.forEach((cube) => {
      const keisenType = cube.keisen_type;
      const cubeType = cube.cube_type;
      const target = cube.target;

      if (!grouped[keisenType]) {
        grouped[keisenType] = {};
      }
      if (!grouped[keisenType][cubeType]) {
        grouped[keisenType][cubeType] = {};
      }
      if (!grouped[keisenType][cubeType][target]) {
        grouped[keisenType][cubeType][target] = [];
      }

      grouped[keisenType][cubeType][target].push(cube);
    });

    return grouped;
  };

  // 数字を丸数字に変換する関数（①、②、③...）
  const toCircledNumber = (num: number): string => {
    if (num >= 1 && num <= 20) {
      return String.fromCharCode(0x2460 + num - 1);
    }
    return num.toString();
  };

  return (
    <div className="min-h-screen bg-background p-4 md:p-6">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-3xl md:text-4xl font-bold mb-8">CUBE生成</h1>

        {/* 回号入力フォーム */}
        <Card className="p-6 mb-8 bg-white border-2 border-slate-200 shadow-md">
          <div className="flex flex-col sm:flex-row gap-6 items-start sm:items-end">
            <div className="w-full max-w-md">
              <label htmlFor="round-number" className="block text-sm font-bold text-slate-800 mb-3">
                回号を入力
              </label>
              <div className="relative">
                <Input
                  id="round-number"
                  type="number"
                  value={roundNumber}
                  onChange={(e) => {
                    const value = e.target.value;
                    if (value === '' || (/^\d+$/.test(value) && parseInt(value) >= 1)) {
                      setRoundNumber(value ? parseInt(value) : '');
                    }
                  }}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && roundNumber && !loading) {
                      handleGenerate();
                    }
                  }}
                  placeholder="4桁の回号を入力してください（例: 6850）"
                  min={1}
                  disabled={loading}
                  className="w-full h-14 text-xl font-semibold border-2 border-slate-300 focus:border-primary focus:ring-2 focus:ring-primary/20 transition-all"
                  aria-describedby="round-number-help"
                  aria-required="true"
                />
              </div>
              <p id="round-number-help" className="mt-2 text-xs text-slate-500">
                Enterキーで生成できます
              </p>
            </div>
            <div className="flex flex-col items-end gap-2">
              <Button
                onClick={handleGenerate}
                disabled={loading || !roundNumber}
                size="lg"
                className="min-w-[160px] h-14 text-lg font-bold shadow-lg hover:shadow-xl transition-all"
                aria-label="CUBEを生成"
              >
                {loading ? (
                  <>
                    <Loader2 className="mr-2 h-6 w-6 animate-spin" />
                    生成中...
                  </>
                ) : (
                  <>
                    <Grid3x3 className="mr-2 h-6 w-6" />
                    CUBE生成
                  </>
                )}
              </Button>
              {cubes.length > 0 && (() => {
                const n3Cube = cubes.find(c => c.target === 'n3');
                const n4Cube = cubes.find(c => c.target === 'n4');
                return (n3Cube || n4Cube) ? (
                  <div className="flex flex-row gap-6 items-end text-sm text-slate-600">
                    {n3Cube && (
                      <div className="flex flex-col items-end gap-1">
                        <div className="font-semibold text-slate-700">N3</div>
                        <div>前々回：{n3Cube.previous_previous_winning}</div>
                        <div>前回：{n3Cube.previous_winning}</div>
                      </div>
                    )}
                    {n4Cube && (
                      <div className="flex flex-col items-end gap-1">
                        <div className="font-semibold text-slate-700">N4</div>
                        <div>前々回：{n4Cube.previous_previous_winning}</div>
                        <div>前回：{n4Cube.previous_winning}</div>
                      </div>
                    )}
                  </div>
                ) : null;
              })()}
            </div>
          </div>
        </Card>

        {/* ローディング状態 */}
        {loading && (
          <Card className="p-12 mb-8 bg-white border-2 border-slate-200 shadow-md">
            <div className="flex flex-col items-center justify-center gap-4">
              <Loader2 className="h-12 w-12 animate-spin text-primary" />
              <p className="text-lg font-semibold text-slate-700">CUBEを生成しています...</p>
              <p className="text-sm text-slate-500">しばらくお待ちください</p>
            </div>
          </Card>
        )}

        {/* エラーメッセージ */}
        {error && (
          <Card className="p-6 mb-8 bg-destructive/10 border-2 border-destructive shadow-md">
            <div className="flex items-start gap-4">
              <div className="flex-1">
                <p className="text-destructive font-bold text-lg mb-3">エラーが発生しました</p>
                <p className="text-destructive whitespace-pre-wrap text-base mb-4">{error}</p>
                <Button
                  onClick={handleGenerate}
                  variant="outline"
                  className="border-destructive text-destructive hover:bg-destructive hover:text-white"
                  aria-label="エラーを再試行"
                >
                  再試行
                </Button>
              </div>
            </div>
            <p className="text-muted-foreground text-xs mt-4">
              ブラウザのコンソール（F12）で詳細なログを確認できます。
            </p>
          </Card>
        )}

        {/* 情報カード（固定ヘッダー） */}
        {cubes.length > 0 && currentRoundNumber && extractedDigits && (() => {
          const grouped = groupCubesByHierarchy(cubes);
          const keisenData = activeKeisenType === 'current' 
            ? { 
                extractedDigits: extractedDigits.current,
                firstCube: cubes.find(c => c.keisen_type === 'current')
              }
            : { 
                extractedDigits: extractedDigits.new,
                firstCube: cubes.find(c => c.keisen_type === 'new')
              };
          
          if (!keisenData.firstCube) return null;
          
          const cubeData = activeKeisenType === 'current' ? grouped.current : grouped.new;
          
          return (
            <div className="mb-8">
              {/* タブバーコントロール */}
              <div className="mb-6 flex flex-row items-center gap-4 flex-wrap">
                {/* 罫線タイプタブ */}
                <div className="flex items-center bg-slate-100 rounded-full px-1 py-1 gap-1">
                  <button
                    onClick={() => setActiveKeisenType('current')}
                    className={`px-8 py-2.5 text-sm font-bold transition-all rounded-full ${
                      activeKeisenType === 'current'
                        ? 'bg-primary text-primary-foreground shadow-md ring-2 ring-primary ring-offset-2 border-2 border-primary'
                        : 'bg-white text-slate-700 hover:bg-slate-50 border border-transparent'
                    }`}
                  >
                    現罫線
                  </button>
                  <button
                    onClick={() => setActiveKeisenType('new')}
                    className={`px-8 py-2.5 text-sm font-bold transition-all rounded-full ${
                      activeKeisenType === 'new'
                        ? 'bg-primary text-primary-foreground shadow-md ring-2 ring-primary ring-offset-2 border-2 border-primary'
                        : 'bg-white text-slate-700 hover:bg-slate-50 border border-transparent'
                    }`}
                  >
                    新罫線
                  </button>
                </div>

                {/* CUBEタイプタブ */}
                <div className="flex items-center bg-slate-100 rounded-full px-1 py-1 gap-1">
                  <button
                    onClick={() => setActiveCubeType('normal')}
                    className={`px-8 py-2.5 text-xs font-bold transition-all rounded-full flex items-center gap-1.5 ${
                      activeCubeType === 'normal'
                        ? 'bg-primary text-primary-foreground shadow-md ring-2 ring-primary ring-offset-2 border-2 border-primary'
                        : 'bg-white text-slate-700 hover:bg-slate-50 border border-transparent'
                    }`}
                  >
                    <Grid3x3 className="w-3.5 h-3.5" />
                    通常CUBE
                  </button>
                  <button
                    onClick={() => setActiveCubeType('extreme')}
                    className={`px-8 py-2.5 text-xs font-bold transition-all rounded-full flex items-center gap-1.5 ${
                      activeCubeType === 'extreme'
                        ? 'bg-primary text-primary-foreground shadow-md ring-2 ring-primary ring-offset-2 border-2 border-primary'
                        : 'bg-white text-slate-700 hover:bg-slate-50 border border-transparent'
                    }`}
                  >
                    <Zap className="w-3.5 h-3.5" />
                    極CUBE
                  </button>
                </div>

                {/* N3/N4タブ（通常CUBEの場合のみ表示） */}
                {activeCubeType === 'normal' && (
                  <div className="flex items-center bg-slate-100 rounded-full px-1 py-1 gap-1">
                    <button
                      onClick={() => setActiveTarget('n3')}
                      className={`px-8 py-2.5 text-xs font-bold transition-all rounded-full ${
                        activeTarget === 'n3'
                          ? 'bg-primary text-primary-foreground shadow-md ring-2 ring-primary ring-offset-2 border-2 border-primary'
                          : 'bg-white text-slate-700 hover:bg-slate-50 border border-transparent'
                      }`}
                    >
                      N3
                    </button>
                    <button
                      onClick={() => setActiveTarget('n4')}
                      className={`px-8 py-2.5 text-xs font-bold transition-all rounded-full ${
                        activeTarget === 'n4'
                          ? 'bg-primary text-primary-foreground shadow-md ring-2 ring-primary ring-offset-2 border-2 border-primary'
                          : 'bg-white text-slate-700 hover:bg-slate-50 border border-transparent'
                      }`}
                    >
                      N4
                    </button>
                  </div>
                )}
              </div>

              {/* CUBE表示 */}
              {cubeData && (
                <div className="space-y-8">
                  {activeCubeType === 'normal' && cubeData.normal && (
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                      {cubeData.normal[activeTarget]
                        ?.sort((a, b) => {
                          // 表0追加あり（B2/A2）が上2つ、表0追加なし（B1/A1）が下2つ
                          // それぞれのグループ内で、欠番補足なし（B）が左、欠番補足あり（A）が右
                          const patternOrder: { [key: string]: number } = { B2: 0, A2: 1, B1: 2, A1: 3 };
                          return (patternOrder[a.pattern || ''] ?? 999) - (patternOrder[b.pattern || ''] ?? 999);
                        })
                        .map((cube) => (
                          <CubeCard key={cube.id} cube={cube} onCopy={handleCopy} toCircledNumber={toCircledNumber} copied={copiedCubeId === cube.id} />
                        ))}
                    </div>
                  )}

                  {activeCubeType === 'extreme' && cubeData.extreme && (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 max-w-5xl">
                      {cubeData.extreme.n3?.map((cube) => (
                        <CubeCard key={cube.id} cube={cube} onCopy={handleCopy} toCircledNumber={toCircledNumber} copied={copiedCubeId === cube.id} />
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })()}
      </div>
    </div>
  );
}

// CUBEカードコンポーネント
function CubeCard({ 
  cube, 
  onCopy, 
  toCircledNumber,
  copied
}: { 
  cube: CubeData; 
  onCopy: (cube: CubeData) => void;
  toCircledNumber: (num: number) => string;
  copied: boolean;
}) {
  const getCenterZeroLabel = (cube: CubeData): string => {
    if (!cube.pattern) {
      // 極CUBEは表0追加なし
      return '表0追加なし';
    }
    // A2/B2は表0追加あり、A1/B1は表0追加なし
    return cube.pattern.endsWith('2') ? '表0追加あり' : '表0追加なし';
  };

  const getMissingFillLabel = (cube: CubeData): string => {
    if (!cube.pattern) {
      // 極CUBEは欠番補足なし
      return '欠番補足なし';
    }
    // A1/A2は欠番補足あり、B1/B2は欠番補足なし
    return cube.pattern.startsWith('A') ? '欠番補足あり' : '欠番補足なし';
  };

  const getTitleText = (cube: CubeData): string => {
    const centerZero = getCenterZeroLabel(cube);
    const missingFill = getMissingFillLabel(cube);
    
    if (centerZero === '表0追加あり') {
      // 表0追加ありの場合は2行で表示
      return `${centerZero}\n${missingFill}`;
    } else {
      // 表0追加なしの場合は1行で表示
      return `${centerZero} / ${missingFill}`;
    }
  };

  const nums = cube.predicted_digits || [];

  return (
    <Card className="p-5 hover:shadow-xl transition-all border-2 border-slate-200 shadow-md">
      <div className="flex justify-between items-start mb-4">
        <div className="flex-1">
          <div className="text-xs font-bold text-slate-500 mb-1 uppercase tracking-wide">
            {cube.cube_type === 'extreme' ? '極CUBE' : '通常CUBE'}
          </div>
          <h3 className="font-bold text-base mb-1 whitespace-pre-line">
            {getTitleText(cube)}
          </h3>
          {/* 元数字リスト（抽出数字） */}
          <div className="font-bold text-base text-slate-700 tracking-wide">
            抽出数字：{nums.length > 0 ? nums.join('  ') : 'データなし'}
          </div>
        </div>
        <Button
          size="default"
          variant={copied ? "default" : "outline"}
          onClick={() => onCopy(cube)}
          className={`h-10 shrink-0 min-w-[100px] transition-all ${
            copied ? 'bg-green-500 text-white border-green-500' : ''
          }`}
          aria-label={`${cube.id}のCUBEをコピー`}
        >
          {copied ? (
            <>
              <Check className="h-4 w-4 mr-1" />
              コピー済
            </>
          ) : (
            <>
              <Copy className="h-4 w-4 mr-1" />
              コピー
            </>
          )}
        </Button>
      </div>
      <div className="overflow-x-auto">
        <table className="border-collapse border-2 border-slate-400 text-sm w-full" role="table" aria-label={`${getMissingFillLabel(cube)}のCUBEテーブル`}>
          <thead>
            <tr>
              <th className="border-2 border-slate-400 bg-slate-200 p-2 w-10 h-10 font-bold" scope="col"></th>
              {Array.from({ length: cube.cols }, (_, i) => (
                <th key={i} className="border-2 border-slate-400 bg-slate-200 p-2 w-10 h-10 font-bold" scope="col">
                  {toCircledNumber(i + 1)}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {Array.from({ length: cube.rows }, (_, rowIdx) => (
              <tr key={rowIdx}>
                <th className="border-2 border-slate-400 bg-slate-200 p-2 w-10 h-10 font-bold" scope="row">
                  {toCircledNumber(rowIdx + 1)}
                </th>
                {Array.from({ length: cube.cols }, (_, colIdx) => {
                  const value = cube.grid[rowIdx + 1]?.[colIdx + 1];
                  return (
                    <td
                      key={colIdx}
                      className="border-2 border-slate-400 p-2 w-10 h-10 text-center font-semibold"
                    >
                      {value !== null && value !== undefined ? value : ''}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Card>
  );
}
