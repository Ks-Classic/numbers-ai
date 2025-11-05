import { create } from 'zustand';
import type { PredictionState } from '@/types/prediction';
import type { StatisticsData } from '@/types/statistics';
import type { HistoryItem } from '@/types/prediction';

export const usePredictionStore = create<PredictionState>((set) => ({
  currentSession: {
    sessionId: null,
    roundNumber: 6701,
    numbersType: 'N4',
    patternType: 'A1', // デフォルトはA1
    rehearsalN3: '',
    rehearsalN4: '',
    selectedAxes: []
  },
  axisCandidates: [],
  finalPredictions: null,
  // N3/N4別のデータを保存
  n3AxisCandidates: [],
  n3FinalPredictions: null,
  n4AxisCandidates: [],
  n4FinalPredictions: null,

  setSessionData: (data) => set((state) => ({
    currentSession: { ...state.currentSession, ...data },
    // numbersTypeが変更された場合、対応するデータをaxisCandidatesとfinalPredictionsに設定
    ...(data.numbersType && {
      axisCandidates: data.numbersType === 'N3' ? state.n3AxisCandidates : state.n4AxisCandidates,
      finalPredictions: data.numbersType === 'N3' ? state.n3FinalPredictions : state.n4FinalPredictions,
    }),
  })),

  setAxisCandidates: (candidates) => set({ axisCandidates: candidates }),
  
  setN3Data: (candidates, predictions) => set((state) => ({
    n3AxisCandidates: candidates,
    n3FinalPredictions: predictions,
    // 現在のセッションがN3の場合は、メインのデータも更新
    ...(state.currentSession.numbersType === 'N3' && {
      axisCandidates: candidates,
      finalPredictions: predictions,
    }),
  })),
  
  setN4Data: (candidates, predictions) => set((state) => ({
    n4AxisCandidates: candidates,
    n4FinalPredictions: predictions,
    // 現在のセッションがN4の場合は、メインのデータも更新
    ...(state.currentSession.numbersType === 'N4' && {
      axisCandidates: candidates,
      finalPredictions: predictions,
    }),
  })),

  toggleAxis: (axis) => set((state) => ({
    currentSession: {
      ...state.currentSession,
      selectedAxes: state.currentSession.selectedAxes.includes(axis)
        ? state.currentSession.selectedAxes.filter(a => a !== axis)
        : [...state.currentSession.selectedAxes, axis]
    }
  })),

  setFinalPredictions: (predictions) => set({ finalPredictions: predictions }),

  resetSession: () => set({
    currentSession: {
      sessionId: null,
      roundNumber: 6701,
      numbersType: 'N4',
      patternType: 'A1', // デフォルトはA1
      rehearsalN3: '',
      rehearsalN4: '',
      selectedAxes: []
    },
    axisCandidates: [],
    finalPredictions: null,
    n3AxisCandidates: [],
    n3FinalPredictions: null,
    n4AxisCandidates: [],
    n4FinalPredictions: null,
  })
}));

// 統計データ用のストア
interface StatisticsState {
  statisticsData: StatisticsData | null;
  setStatisticsData: (data: StatisticsData) => void;
}

export const useStatisticsStore = create<StatisticsState>((set) => ({
  statisticsData: null,
  setStatisticsData: (data) => set({ statisticsData: data })
}));

// 履歴データ用のストア
interface HistoryState {
  historyData: HistoryItem[];
  setHistoryData: (data: HistoryItem[]) => void;
}

export const useHistoryStore = create<HistoryState>((set) => ({
  historyData: [],
  setHistoryData: (data) => set({ historyData: data })
}));


