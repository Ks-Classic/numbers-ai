'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card } from '@/components/ui/card';
import { fetchCubes, gridToTSV, type CubeData, type CubesResponse } from '@/lib/cube-api';
import { Copy, Loader2, Grid3x3, Zap, Check, RefreshCw, X, Info } from 'lucide-react';
import { toast } from 'sonner';

export default function CubePage() {
  const [roundNumber, setRoundNumber] = useState<number | ''>('');
  const [cubes, setCubes] = useState<CubeData[]>([]);
  const [currentRoundNumber, setCurrentRoundNumber] = useState<number | null>(null);
  const [extractedDigits, setExtractedDigits] = useState<CubesResponse['extracted_digits'] | null>(null);
  const [currentWinning, setCurrentWinning] = useState<CubesResponse['current_winning'] | null>(null);
  const [currentRehearsal, setCurrentRehearsal] = useState<CubesResponse['current_rehearsal'] | null>(null);
  // 手動編集用のstate
  const [manualWinning, setManualWinning] = useState<{ n3: string; n4: string }>({ n3: '', n4: '' });
  const [manualRehearsal, setManualRehearsal] = useState<{ n3: string; n4: string }>({ n3: '', n4: '' });
  const [activeKeisenType, setActiveKeisenType] = useState<'current' | 'new'>('current');
  const [activeCubeType, setActiveCubeType] = useState<'normal' | 'extreme'>('normal');
  const [activeTarget, setActiveTarget] = useState<'n3' | 'n4'>('n3');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [copiedCubeId, setCopiedCubeId] = useState<string | null>(null);
  const [updatingData, setUpdatingData] = useState(false);
  const [updateStatus, setUpdateStatus] = useState<'idle' | 'checking' | 'updating' | 'completed' | 'error'>('idle');
  const [updateNotification, setUpdateNotification] = useState<{
    type: 'success' | 'info';
    message: string;
    details?: {
      latestRoundNumber?: number;
      lastModified?: string;
      dataCount?: number;
      workflowUrl?: string;
    };
  } | null>(null);
  
  // フィルタ状態を追加（デフォルト: N3と当選番号のみオン）
  const [showN3, setShowN3] = useState(true);
  const [showN4, setShowN4] = useState(false);
  const [showWinning, setShowWinning] = useState(true);
  const [showRehearsal, setShowRehearsal] = useState(false);

  const handleGenerate = async () => {
    if (!roundNumber || roundNumber < 1) {
      toast.error('有効な回号を入力してください');
      return;
    }

    setLoading(true);
    setError(null);
    setCubes([]);
    setExtractedDigits(null);
    setCurrentWinning(null);
    setCurrentRehearsal(null);

    try {
      // 手動編集値がある場合はクエリパラメータとして送信
      const params = new URLSearchParams();
      if (manualWinning.n3) params.append('n3_winning', manualWinning.n3);
      if (manualWinning.n4) params.append('n4_winning', manualWinning.n4);
      if (manualRehearsal.n3) params.append('n3_rehearsal', manualRehearsal.n3);
      if (manualRehearsal.n4) params.append('n4_rehearsal', manualRehearsal.n4);
      
      const queryString = params.toString();
      const url = `/api/cube/${roundNumber}${queryString ? `?${queryString}` : ''}`;
      
      const response = await fetch(url, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ error: 'CUBE生成に失敗しました' }));
        throw new Error(errorData.error || 'CUBE生成に失敗しました');
      }

      const data = await response.json();
      console.log('[handleGenerateCubes] APIレスポンス:', {
        round_number: data.round_number,
        current_winning: data.current_winning,
        current_rehearsal: data.current_rehearsal,
        cubes_count: data.cubes?.length,
      });
      setCubes(data.cubes);
      setCurrentRoundNumber(data.round_number);
      setExtractedDigits(data.extracted_digits);
      setCurrentWinning(data.current_winning);
      setCurrentRehearsal(data.current_rehearsal);
      console.log('[handleGenerateCubes] state更新完了');
      toast.success(`${data.cubes.length}個のCUBEを生成しました`);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'CUBE生成に失敗しました';
      setError(errorMessage);
      toast.error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateData = async () => {
    setUpdatingData(true);
    setUpdateStatus('checking');
    setUpdateNotification(null);
    
    try {
      // まず、現在のデータ状態をチェック
      const statusResponse = await fetch('/api/check-data-status');
      const statusData = await statusResponse.json();
      
      if (statusResponse.ok && statusData.success) {
        const currentLatestRound = statusData.latestRoundNumber;
        
        // 外部から最新回号を取得して比較
        try {
          const latestRoundResponse = await fetch('/api/get-latest-round');
          const latestRoundData = await latestRoundResponse.json();
          
          // 外部から最新回号が取得できた場合、比較する
          if (latestRoundResponse.ok && latestRoundData.success && latestRoundData.latestRoundNumber) {
            const externalLatestRound = latestRoundData.latestRoundNumber;
            
            // すでに最新データの場合
            if (currentLatestRound >= externalLatestRound) {
              setUpdateStatus('idle');
              setUpdateNotification({
                type: 'info',
                message: 'すでに最新データになっています。',
                details: {
                  latestRoundNumber: currentLatestRound,
                  lastModified: statusData.lastModified,
                  dataCount: statusData.dataCount,
                },
              });
              toast.info('すでに最新データです');
              setUpdatingData(false);
              return;
            }
          }
        } catch (error) {
          // 外部からの最新回号取得に失敗した場合は、更新を続行
          console.warn('外部からの最新回号取得に失敗:', error);
        }
        
        // データ更新APIを呼び出し
        setUpdateStatus('updating');
        const response = await fetch('/api/update-data', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
        });

        const data = await response.json();

        if (!response.ok) {
          // エラーの詳細を取得
          const errorMessage = data.error || 'データ更新に失敗しました';
          const errorDetail = data.detail ? (typeof data.detail === 'string' ? data.detail : JSON.stringify(data.detail)) : '';
          const fullErrorMessage = errorDetail 
            ? `${errorMessage}\n\n詳細: ${errorDetail}`
            : errorMessage;
          
          console.error('データ更新APIエラー:', {
            status: response.status,
            error: data.error,
            detail: data.detail,
            statusCode: data.status,
            apiUrl: data.apiUrl,
          });
          
          throw new Error(fullErrorMessage);
        }

        // 更新開始通知を表示
        setUpdateNotification({
          type: 'success',
          message: 'データ更新を開始しました。完了までお待ちください...',
          details: {
            latestRoundNumber: currentLatestRound,
            lastModified: statusData.lastModified,
            dataCount: statusData.dataCount,
            workflowUrl: data.workflowUrl,
          },
        });
        
        toast.success('データ更新を開始しました');
        
        // ワークフローIDがある場合、ポーリングを開始
        if (data.workflowId) {
          pollWorkflowStatus(data.workflowId, currentLatestRound);
        } else {
          // ワークフローIDが取得できない場合、一定時間後に完了とみなす
          setTimeout(() => {
            checkDataUpdateComplete(currentLatestRound);
          }, 60000); // 60秒後に確認
        }
      } else {
        // ステータスチェックに失敗した場合でも更新を試行
        setUpdateStatus('updating');
        const response = await fetch('/api/update-data', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
        });

        const data = await response.json();

        if (!response.ok) {
          // エラーの詳細を取得
          const errorMessage = data.error || 'データ更新に失敗しました';
          const errorDetail = data.detail ? (typeof data.detail === 'string' ? data.detail : JSON.stringify(data.detail)) : '';
          const fullErrorMessage = errorDetail 
            ? `${errorMessage}\n\n詳細: ${errorDetail}`
            : errorMessage;
          
          console.error('データ更新APIエラー:', {
            status: response.status,
            error: data.error,
            detail: data.detail,
            statusCode: data.status,
            apiUrl: data.apiUrl,
          });
          
          throw new Error(fullErrorMessage);
        }

        setUpdateNotification({
          type: 'success',
          message: 'データ更新を開始しました。完了までお待ちください...',
          details: {
            workflowUrl: data.workflowUrl,
          },
        });
        
        toast.success('データ更新を開始しました');
        
        // ワークフローIDがある場合、ポーリングを開始
        if (data.workflowId) {
          pollWorkflowStatus(data.workflowId, null);
        }
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'データ更新に失敗しました';
      setUpdateStatus('error');
      
      // エラー通知を表示
      setUpdateNotification({
        type: 'info',
        message: errorMessage,
      });
      
      toast.error(errorMessage);
      console.error('データ更新エラー:', err);
    } finally {
      setUpdatingData(false);
    }
  };

  // ワークフロー実行状況をポーリング
  const pollWorkflowStatus = async (workflowId: string, previousLatestRound: number | null) => {
    const maxAttempts = 60; // 最大60回（5分間）
    let attempts = 0;
    
    const poll = async () => {
      if (attempts >= maxAttempts) {
        setUpdateStatus('error');
        setUpdateNotification({
          type: 'info',
          message: 'データ更新の確認がタイムアウトしました。GitHub Actionsで実行状況を確認してください。',
          details: updateNotification?.details,
        });
        // タイムアウトでもローディング状態をリセット
        setUpdatingData(false);
        return;
      }
      
      attempts++;
      
      try {
        const response = await fetch(`/api/check-workflow-status?workflow_id=${workflowId}`);
        const data = await response.json();
        
        if (response.ok && data.success) {
          if (data.status === 'completed') {
            // ワークフローが完了したら、データの更新を確認
            if (data.conclusion === 'success') {
              setUpdateStatus('completed');
              checkDataUpdateComplete(previousLatestRound);
            } else {
              setUpdateStatus('error');
              setUpdateNotification({
                type: 'info',
                message: `データ更新が失敗しました（${data.conclusion || 'unknown'}）。GitHub Actionsで詳細を確認してください。`,
                details: {
                  ...updateNotification?.details,
                  workflowUrl: data.htmlUrl,
                },
              });
              toast.error('データ更新が失敗しました');
              // エラーでもローディング状態をリセット
              setUpdatingData(false);
            }
          } else {
            // まだ実行中の場合、継続してポーリング
            setUpdateNotification({
              type: 'success',
              message: `データ更新中... (${data.status === 'in_progress' ? '実行中' : '待機中'})`,
              details: updateNotification?.details,
            });
            
            // 5秒後に再チェック
            setTimeout(poll, 5000);
          }
        } else {
          // エラーの場合、5秒後に再試行
          setTimeout(poll, 5000);
        }
      } catch (error) {
        console.error('ワークフロー状況確認エラー:', error);
        // エラーの場合、5秒後に再試行
        setTimeout(poll, 5000);
      }
    };
    
    // 初回は3秒後に開始（ワークフローが開始されるまで少し待つ）
    setTimeout(poll, 3000);
  };

  // データ更新が完了したか確認
  const checkDataUpdateComplete = async (previousLatestRound: number | null) => {
    console.log('[checkDataUpdateComplete] 開始', { previousLatestRound });
    try {
      const statusResponse = await fetch('/api/check-data-status');
      const statusData = await statusResponse.json();
      
      console.log('[checkDataUpdateComplete] statusData:', {
        success: statusData.success,
        latestRoundNumber: statusData.latestRoundNumber,
        source: statusData.source,
        dataCount: statusData.dataCount,
      });
      
      if (statusResponse.ok && statusData.success) {
        const newLatestRound = statusData.latestRoundNumber;
        
        // データが更新されたか確認
        const isDataUpdated = previousLatestRound === null || newLatestRound > previousLatestRound;
        console.log('[checkDataUpdateComplete] データ更新チェック:', {
          previousLatestRound,
          newLatestRound,
          isDataUpdated,
        });
        
        // ローカル環境の場合、常にGitHubの最新データで同期を試行
        if (statusData.source === 'local') {
          console.log('[checkDataUpdateComplete] ローカルファイル同期を開始...');
          try {
            const syncResponse = await fetch('/api/sync-local-data', {
              method: 'POST',
            });
            const syncData = await syncResponse.json();
            
            console.log('[checkDataUpdateComplete] 同期レスポンス:', {
              ok: syncResponse.ok,
              status: syncResponse.status,
              data: syncData,
            });
            
            if (syncResponse.ok) {
              console.log('[checkDataUpdateComplete] ✅ ローカルファイルをGitHubの最新データで更新しました');
              
              // 同期後、再度データ状態を確認（最新データを反映）
              const updatedStatusResponse = await fetch('/api/check-data-status');
              const updatedStatusData = await updatedStatusResponse.json();
              
              if (updatedStatusResponse.ok && updatedStatusData.success) {
                const updatedLatestRound = updatedStatusData.latestRoundNumber;
                console.log('[checkDataUpdateComplete] 同期後の最新回号:', updatedLatestRound);
                
                setUpdateNotification({
                  type: 'success',
                  message: 'データ更新が完了しました！',
                  details: {
                    latestRoundNumber: updatedLatestRound,
                    lastModified: updatedStatusData.lastModified,
                    dataCount: updatedStatusData.dataCount,
                    workflowUrl: updateNotification?.details?.workflowUrl,
                  },
                });
                toast.success(`データ更新が完了しました（最新回号: 第${updatedLatestRound}回）`);
                return;
              }
            } else {
              console.warn('[checkDataUpdateComplete] ⚠️ ローカルファイルの同期に失敗:', syncData);
            }
          } catch (error) {
            console.error('[checkDataUpdateComplete] ❌ ローカルファイルの同期エラー:', error);
            // エラーでも続行（GitHubのデータは更新されている）
          }
        }
        
        // 同期が不要な場合、または同期後の再チェックが不要な場合
        // データが更新されていない場合でも、完了通知を表示
        if (isDataUpdated) {
          setUpdateNotification({
            type: 'success',
            message: 'データ更新が完了しました！',
            details: {
              latestRoundNumber: newLatestRound,
              lastModified: statusData.lastModified,
              dataCount: statusData.dataCount,
              workflowUrl: updateNotification?.details?.workflowUrl,
            },
          });
          toast.success(`データ更新が完了しました（最新回号: 第${newLatestRound}回）`);
        } else {
          setUpdateNotification({
            type: 'success',
            message: 'データ更新が完了しました（更新するデータはありませんでした）。',
            details: {
              latestRoundNumber: newLatestRound,
              lastModified: statusData.lastModified,
              dataCount: statusData.dataCount,
              workflowUrl: updateNotification?.details?.workflowUrl,
            },
          });
          toast.success('データ更新が完了しました');
        }
        
        // ローディング状態をリセット
        setUpdateStatus('idle');
        setUpdatingData(false);
      } else {
        console.error('[checkDataUpdateComplete] statusResponseが失敗:', {
          ok: statusResponse.ok,
          status: statusResponse.status,
          data: statusData,
        });
        // エラーでもローディング状態をリセット
        setUpdateStatus('idle');
        setUpdatingData(false);
      }
    } catch (error) {
      console.error('[checkDataUpdateComplete] ❌ データ更新確認エラー:', error);
      setUpdateNotification({
        type: 'success',
        message: 'データ更新が完了しました（確認中にエラーが発生しました）。',
        details: updateNotification?.details,
      });
      toast.success('データ更新が完了しました');
      // エラーでもローディング状態をリセット
      setUpdateStatus('idle');
      setUpdatingData(false);
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

  // 表示用の当選番号・リハーサルを取得（CSV優先、なければ手動編集値）
  const getDisplayWinning = () => {
    const result = {
      n3: currentWinning?.n3 || manualWinning.n3 || '---',
      n4: currentWinning?.n4 || manualWinning.n4 || '---',
    };
    // デバッグログ（開発時のみ）
    if (process.env.NODE_ENV === 'development') {
      console.log('[getDisplayWinning]', {
        currentWinning,
        manualWinning,
        result,
      });
    }
    return result;
  };

  const getDisplayRehearsal = () => {
    const result = {
      n3: currentRehearsal?.n3 || manualRehearsal.n3 || '---',
      n4: currentRehearsal?.n4 || manualRehearsal.n4 || '---',
    };
    // デバッグログ（開発時のみ）
    if (process.env.NODE_ENV === 'development') {
      console.log('[getDisplayRehearsal]', {
        currentRehearsal,
        manualRehearsal,
        result,
      });
    }
    return result;
  };

  // 数字のカテゴリを判定する関数（入力回号の当選番号・リハーサルのみ）
  const getNumberCategories = (num: number, cube: CubeData): {
    n3Winning: boolean;
    n3Rehearsal: boolean;
    n4Winning: boolean;
    n4Rehearsal: boolean;
  } => {
    const result = {
      n3Winning: false,
      n3Rehearsal: false,
      n4Winning: false,
      n4Rehearsal: false,
    };

    // CSVデータまたは手動編集値を使用
    const displayWinning = getDisplayWinning();
    const displayRehearsal = getDisplayRehearsal();

    // 入力回号の当選番号・リハーサルをチェック
    if (displayWinning.n3 && displayWinning.n3 !== '---') {
      const digits = displayWinning.n3.split('').map(Number);
      if (digits.includes(num)) result.n3Winning = true;
    }

    if (displayRehearsal.n3 && displayRehearsal.n3 !== '---') {
      const digits = displayRehearsal.n3.split('').map(Number);
      if (digits.includes(num)) {
        result.n3Rehearsal = true;
      }
    }

    if (displayWinning.n4 && displayWinning.n4 !== '---') {
      const digits = displayWinning.n4.split('').map(Number);
      if (digits.includes(num)) result.n4Winning = true;
    }

    if (displayRehearsal.n4 && displayRehearsal.n4 !== '---') {
      const digits = displayRehearsal.n4.split('').map(Number);
      if (digits.includes(num)) {
        result.n4Rehearsal = true;
      }
    }

    // デバッグログ（N3とN4のリハーサルが両方trueの場合のみ）
    if (result.n3Rehearsal && result.n4Rehearsal) {
      console.log(`[getNumberCategories] 数字 ${num} はN3リハーサル(${displayRehearsal.n3})とN4リハーサル(${displayRehearsal.n4})の両方に含まれます`);
    }

    return result;
  };

  // セルのコーナーインジケーター情報を取得する関数
  const getCellCornerIndicators = (num: number, cube: CubeData): Array<{ color: string; position: 'top-left' | 'top-right' | 'bottom-left' | 'bottom-right' }> => {
    const categories = getNumberCategories(num, cube);
    
    // フィルタ適用
    const activeCategories = {
      n3Winning: categories.n3Winning && showN3 && showWinning,
      n3Rehearsal: categories.n3Rehearsal && showN3 && showRehearsal,
      n4Winning: categories.n4Winning && showN4 && showWinning,
      n4Rehearsal: categories.n4Rehearsal && showN4 && showRehearsal,
    };

    const corners: Array<{ color: string; position: 'top-left' | 'top-right' | 'bottom-left' | 'bottom-right' }> = [];
    
    // コーナーの位置と色を設定
    if (activeCategories.n3Winning) {
      corners.push({ color: '#fee2e2', position: 'top-left' }); // 赤（N3当選）
    }
    if (activeCategories.n3Rehearsal) {
      corners.push({ color: '#dbeafe', position: 'top-right' }); // 青（N3リハーサル）
    }
    if (activeCategories.n4Winning) {
      corners.push({ color: '#fef3c7', position: 'bottom-left' }); // 黄（N4当選）
    }
    if (activeCategories.n4Rehearsal) {
      corners.push({ color: '#d1fae5', position: 'bottom-right' }); // 緑（N4リハーサル）
    }

    return corners;
  };

  // セルの背景色スタイルを取得する関数
  const getCellBackgroundStyle = (num: number, cube: CubeData): React.CSSProperties => {
    const categories = getNumberCategories(num, cube);
    
    // N3リハーサルとN4リハーサルの両方に含まれる数字の場合、淡い紫で塗る
    if (categories.n3Rehearsal && categories.n4Rehearsal) {
      return { backgroundColor: '#f3e8ff' }; // 淡い紫（purple-100相当）
    }
    
    return {};
  };

  return (
    <div className="min-h-screen bg-background p-4 md:p-6">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-3xl md:text-4xl font-bold mb-8">CUBE生成</h1>

        {/* データ更新ボタン */}
        <Card className="p-4 mb-6 bg-blue-50 border-2 border-blue-200 shadow-md">
          <div className="flex items-center justify-between">
            <div className="flex-1">
              <p className="text-sm font-semibold text-blue-900 mb-1">最新の当選番号データ</p>
              <p className="text-xs text-blue-700">最新の当選番号データを取得して更新します</p>
            </div>
            <Button
              onClick={handleUpdateData}
              disabled={updatingData || updateStatus === 'updating' || updateStatus === 'checking'}
              variant="outline"
              size="sm"
              className="ml-4 border-blue-300 text-blue-700 hover:bg-blue-100"
            >
              {updatingData || updateStatus === 'updating' || updateStatus === 'checking' ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  {updateStatus === 'checking' ? '確認中...' : '更新中...'}
                </>
              ) : (
                <>
                  <RefreshCw className="mr-2 h-4 w-4" />
                  データ更新
                </>
              )}
            </Button>
          </div>
        </Card>

        {/* データ更新通知 */}
        {updateNotification && (
          <Card className={`p-4 mb-6 border-2 shadow-md ${
            updateNotification.type === 'success' 
              ? updateStatus === 'completed'
                ? 'bg-green-50 border-green-200'
                : updateStatus === 'error'
                ? 'bg-red-50 border-red-200'
                : 'bg-blue-50 border-blue-200'
              : updateNotification.message.includes('すでに最新')
              ? 'bg-blue-50 border-blue-200'
              : 'bg-red-50 border-red-200'
          }`}>
            <div className="flex items-start gap-3">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-2">
                  {updateStatus === 'completed' ? (
                    <Check className="h-5 w-5 text-green-600" />
                  ) : updateStatus === 'updating' || updateStatus === 'checking' ? (
                    <Loader2 className="h-5 w-5 text-blue-600 animate-spin" />
                  ) : updateNotification.type === 'success' ? (
                    <Check className="h-5 w-5 text-green-600" />
                  ) : updateNotification.message.includes('すでに最新') ? (
                    <Info className="h-5 w-5 text-blue-600" />
                  ) : (
                    <X className="h-5 w-5 text-red-600" />
                  )}
                  <p className={`text-sm font-semibold whitespace-pre-wrap ${
                    updateStatus === 'completed'
                      ? 'text-green-900'
                      : updateStatus === 'error'
                      ? 'text-red-900'
                      : updateNotification.type === 'success' 
                      ? 'text-blue-900'
                      : updateNotification.message.includes('すでに最新')
                      ? 'text-blue-900'
                      : 'text-red-900'
                  }`}>
                    {updateNotification.message}
                  </p>
                </div>
                {updateNotification.details && (
                  <div className="ml-7 text-xs space-y-1">
                    {updateNotification.details.latestRoundNumber && (
                      <p className={`${
                        updateStatus === 'completed'
                          ? 'text-green-700'
                          : updateStatus === 'error'
                          ? 'text-red-700'
                          : updateNotification.type === 'success' 
                          ? 'text-blue-700' 
                          : updateNotification.message.includes('すでに最新')
                          ? 'text-blue-700'
                          : 'text-red-700'
                      }`}>
                        現在の最新回号: 第{updateNotification.details.latestRoundNumber}回
                      </p>
                    )}
                    {updateNotification.details.dataCount && (
                      <p className={`${
                        updateStatus === 'completed'
                          ? 'text-green-700'
                          : updateStatus === 'error'
                          ? 'text-red-700'
                          : updateNotification.type === 'success' 
                          ? 'text-blue-700' 
                          : updateNotification.message.includes('すでに最新')
                          ? 'text-blue-700'
                          : 'text-red-700'
                      }`}>
                        データ件数: {updateNotification.details.dataCount.toLocaleString()}件
                      </p>
                    )}
                    {updateNotification.details.workflowUrl && (
                      <p className={`${
                        updateStatus === 'completed'
                          ? 'text-green-700'
                          : updateStatus === 'error'
                          ? 'text-red-700'
                          : 'text-blue-700'
                      }`}>
                        <a 
                          href={updateNotification.details.workflowUrl} 
                          target="_blank" 
                          rel="noopener noreferrer"
                          className="underline hover:no-underline"
                        >
                          GitHub Actionsで実行状況を確認
                        </a>
                      </p>
                    )}
                  </div>
                )}
              </div>
              <Button
                onClick={() => {
                  setUpdateNotification(null);
                  setUpdateStatus('idle');
                }}
                variant="ghost"
                size="sm"
                className={`h-6 w-6 p-0 hover:bg-opacity-20 ${
                  updateStatus === 'completed'
                    ? 'hover:bg-green-600 text-green-700'
                    : updateStatus === 'error'
                    ? 'hover:bg-red-600 text-red-700'
                    : updateNotification.type === 'success' 
                    ? 'hover:bg-blue-600 text-blue-700' 
                    : updateNotification.message.includes('すでに最新')
                    ? 'hover:bg-blue-600 text-blue-700'
                    : 'hover:bg-red-600 text-red-700'
                }`}
                aria-label="通知を閉じる"
              >
                <X className="h-4 w-4" />
              </Button>
            </div>
          </Card>
        )}

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

              {/* インジケーター説明と手動編集 */}
              <div className="mb-6">
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                  <Card className="p-4 bg-slate-50 border-2 border-slate-200 shadow-md">
                    <div className="grid grid-cols-5 gap-x-2 gap-y-1.5 text-xs items-center whitespace-nowrap">
                      {/* 左側：インジケーター説明 */}
                      <div className="col-span-3">
                        <div className="grid grid-cols-3 gap-x-2 gap-y-1.5">
                          <div className="font-semibold text-slate-600"></div>
                          <div className="font-semibold text-slate-600">当選番号</div>
                          <div className="font-semibold text-slate-600">リハーサル</div>
                          
                          <div className="font-semibold text-slate-700">N3</div>
                          <div className="flex items-center gap-1">
                            <div className="w-2.5 h-2.5 rounded-full shrink-0" style={{ backgroundColor: '#fee2e2', border: '1px solid #fca5a5' }}></div>
                            <span className="text-slate-600">{getDisplayWinning().n3}</span>
                          </div>
                          <div className="flex items-center gap-1">
                            <div className="w-2.5 h-2.5 rounded-full shrink-0" style={{ backgroundColor: '#dbeafe', border: '1px solid #93c5fd' }}></div>
                            <span className="text-slate-600">{getDisplayRehearsal().n3}</span>
                          </div>
                          
                          <div className="font-semibold text-slate-700">N4</div>
                          <div className="flex items-center gap-1">
                            <div className="w-2.5 h-2.5 rounded-full shrink-0" style={{ backgroundColor: '#fef3c7', border: '1px solid #fcd34d' }}></div>
                            <span className="text-slate-600">{getDisplayWinning().n4}</span>
                          </div>
                          <div className="flex items-center gap-1">
                            <div className="w-2.5 h-2.5 rounded-full shrink-0" style={{ backgroundColor: '#d1fae5', border: '1px solid #6ee7b7' }}></div>
                            <span className="text-slate-600">{getDisplayRehearsal().n4}</span>
                          </div>
                        </div>
                      </div>
                      
                      {/* 右側：手動編集フォーム */}
                      <div className="col-span-2 pl-2 border-l border-slate-300">
                        <div className="text-xs font-semibold text-slate-700 mb-1.5 mt-2">手動編集</div>
                        <div className="grid grid-cols-2 gap-1.5">
                          <div>
                            <label className="block text-slate-600 mb-0.5 text-xs">N3当選</label>
                            <Input
                              type="text"
                              placeholder="123"
                              value={manualWinning.n3}
                              onChange={(e) => {
                                const value = e.target.value.replace(/[^0-9]/g, '').slice(0, 3);
                                setManualWinning(prev => ({ ...prev, n3: value }));
                              }}
                              className="h-6 text-xs px-2 py-1"
                            />
                          </div>
                          <div>
                            <label className="block text-slate-600 mb-0.5 text-xs">N3リハ</label>
                            <Input
                              type="text"
                              placeholder="456"
                              value={manualRehearsal.n3}
                              onChange={(e) => {
                                const value = e.target.value.replace(/[^0-9]/g, '').slice(0, 3);
                                setManualRehearsal(prev => ({ ...prev, n3: value }));
                              }}
                              className="h-6 text-xs px-2 py-1"
                            />
                          </div>
                          <div>
                            <label className="block text-slate-600 mb-0.5 text-xs">N4当選</label>
                            <Input
                              type="text"
                              placeholder="1234"
                              value={manualWinning.n4}
                              onChange={(e) => {
                                const value = e.target.value.replace(/[^0-9]/g, '').slice(0, 4);
                                setManualWinning(prev => ({ ...prev, n4: value }));
                              }}
                              className="h-6 text-xs px-2 py-1"
                            />
                          </div>
                          <div>
                            <label className="block text-slate-600 mb-0.5 text-xs">N4リハ</label>
                            <Input
                              type="text"
                              placeholder="5678"
                              value={manualRehearsal.n4}
                              onChange={(e) => {
                                const value = e.target.value.replace(/[^0-9]/g, '').slice(0, 4);
                                setManualRehearsal(prev => ({ ...prev, n4: value }));
                              }}
                              className="h-6 text-xs px-2 py-1"
                            />
                          </div>
                        </div>
                      </div>
                    </div>
                  </Card>
                </div>
              </div>

              {/* フィルタコントロール */}
              <div className="mb-6 flex flex-wrap gap-4 items-center">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-semibold text-slate-700">番号 印表示</span>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => setShowN3(!showN3)}
                    className={`px-4 py-2 text-xs font-bold rounded-full transition-all ${
                      showN3
                        ? 'bg-blue-100 text-slate-900 shadow-sm border-2 border-blue-500'
                        : 'bg-white text-slate-500 border border-slate-300'
                    }`}
                  >
                    N3
                  </button>
                  <button
                    onClick={() => setShowN4(!showN4)}
                    className={`px-4 py-2 text-xs font-bold rounded-full transition-all ${
                      showN4
                        ? 'bg-blue-100 text-slate-900 shadow-sm border-2 border-blue-500'
                        : 'bg-white text-slate-500 border border-slate-300'
                    }`}
                  >
                    N4
                  </button>
                  <button
                    onClick={() => setShowWinning(!showWinning)}
                    className={`px-4 py-2 text-xs font-bold rounded-full transition-all ${
                      showWinning
                        ? 'bg-blue-100 text-slate-900 shadow-sm border-2 border-blue-500'
                        : 'bg-white text-slate-500 border border-slate-300'
                    }`}
                  >
                    当選番号
                  </button>
                  <button
                    onClick={() => setShowRehearsal(!showRehearsal)}
                    className={`px-4 py-2 text-xs font-bold rounded-full transition-all ${
                      showRehearsal
                        ? 'bg-blue-100 text-slate-900 shadow-sm border-2 border-blue-500'
                        : 'bg-white text-slate-500 border border-slate-300'
                    }`}
                  >
                    リハーサル
                  </button>
                </div>
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
                          <CubeCard 
                            key={cube.id} 
                            cube={cube} 
                            onCopy={handleCopy} 
                            toCircledNumber={toCircledNumber} 
                            copied={copiedCubeId === cube.id}
                            getCellCornerIndicators={getCellCornerIndicators}
                            getCellBackgroundStyle={getCellBackgroundStyle}
                          />
                        ))}
                    </div>
                  )}

                  {activeCubeType === 'extreme' && cubeData.extreme && (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-2 gap-6 max-w-4xl">
                      {cubeData.extreme.n3?.map((cube) => (
                        <CubeCard 
                          key={cube.id} 
                          cube={cube} 
                          onCopy={handleCopy} 
                          toCircledNumber={toCircledNumber} 
                          copied={copiedCubeId === cube.id}
                          getCellCornerIndicators={getCellCornerIndicators}
                          getCellBackgroundStyle={getCellBackgroundStyle}
                        />
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
  copied,
  getCellCornerIndicators,
  getCellBackgroundStyle,
}: { 
  cube: CubeData; 
  onCopy: (cube: CubeData) => void;
  toCircledNumber: (num: number) => string;
  copied: boolean;
  getCellCornerIndicators: (num: number, cube: CubeData) => Array<{ color: string; position: 'top-left' | 'top-right' | 'bottom-left' | 'bottom-right' }>;
  getCellBackgroundStyle: (num: number, cube: CubeData) => React.CSSProperties;
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
    <Card className="p-5 hover:shadow-xl transition-all border-2 border-slate-200 shadow-md overflow-hidden">
      <div className="flex justify-between items-start mb-4">
        <div className="flex-1 min-w-0">
          <div className="text-xs font-bold text-slate-500 mb-1 uppercase tracking-wide">
            {cube.cube_type === 'extreme' ? '極CUBE' : '通常CUBE'}
          </div>
          <h3 className="font-bold text-base mb-1 whitespace-pre-line">
            {getTitleText(cube)}
          </h3>
          {/* 元数字リスト（抽出数字） */}
          <div className="font-bold text-base text-slate-700 tracking-wide break-words">
            抽出数字：{nums.length > 0 ? nums.join('  ') : 'データなし'}
          </div>
        </div>
        <Button
          size="default"
          variant={copied ? "default" : "outline"}
          onClick={() => onCopy(cube)}
          className={`h-10 shrink-0 min-w-[100px] transition-all ml-2 ${
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
      <div className="overflow-x-auto -mx-5 px-5">
        <table className="border-collapse border-2 border-slate-400 text-xs w-full table-auto min-w-full" role="table" aria-label={`${getMissingFillLabel(cube)}のCUBEテーブル`}>
          <thead>
            <tr>
              <th className="border-2 border-slate-400 bg-slate-200 p-1 w-8 h-8 font-bold text-center" scope="col"></th>
              {Array.from({ length: cube.cols }, (_, i) => (
                <th key={i} className="border-2 border-slate-400 bg-slate-200 p-1 w-8 h-8 font-bold text-center" scope="col">
                  {toCircledNumber(i + 1)}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {Array.from({ length: cube.rows }, (_, rowIdx) => (
              <tr key={rowIdx}>
                <th className="border-2 border-slate-400 bg-slate-200 p-1 w-8 h-8 font-bold text-center" scope="row">
                  {toCircledNumber(rowIdx + 1)}
                </th>
                {Array.from({ length: cube.cols }, (_, colIdx) => {
                  const value = cube.grid[rowIdx + 1]?.[colIdx + 1];
                  const corners = value !== null && value !== undefined ? getCellCornerIndicators(value, cube) : [];
                  const bgStyle = value !== null && value !== undefined ? getCellBackgroundStyle(value, cube) : {};
                  
                  return (
                    <td
                      key={colIdx}
                      className="border-2 border-slate-400 p-1 w-8 h-8 text-center font-semibold relative min-w-[2rem]"
                      style={bgStyle}
                    >
                      {value !== null && value !== undefined ? value : ''}
                      
                      {/* コーナーインジケーター */}
                      {corners.map((corner, idx) => {
                        const positionStyles: Record<string, React.CSSProperties> = {
                          'top-left': { top: '2px', left: '2px' },
                          'top-right': { top: '2px', right: '2px' },
                          'bottom-left': { bottom: '2px', left: '2px' },
                          'bottom-right': { bottom: '2px', right: '2px' },
                        };
                        
                        return (
                          <div
                            key={idx}
                            className="absolute w-2 h-2 rounded-full"
                            style={{
                              ...positionStyles[corner.position],
                              backgroundColor: corner.color,
                              border: '1px solid rgba(0, 0, 0, 0.2)',
                              zIndex: 10,
                            }}
                            title={
                              corner.position === 'top-left' ? 'N3当選' :
                              corner.position === 'top-right' ? 'N3リハーサル' :
                              corner.position === 'bottom-left' ? 'N4当選' :
                              'N4リハーサル'
                            }
                          />
                        );
                      })}
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
