import { create } from 'zustand';
import type { PredictionState } from '@/types/prediction';
import type { StatisticsData } from '@/types/statistics';
import type { HistoryItem } from '@/types/prediction';

export const usePredictionStore = create<PredictionState>((set) => ({
  currentSession: {
    sessionId: null,
    roundNumber: 6701,
    numbersType: 'N4',
    patternType: 'A',
    rehearsalN3: '',
    rehearsalN4: '',
    selectedAxes: []
  },
  axisCandidates: [],
  finalPredictions: null,

  setSessionData: (data) => set((state) => ({
    currentSession: { ...state.currentSession, ...data }
  })),

  setAxisCandidates: (candidates) => set({ axisCandidates: candidates }),

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
      patternType: 'A',
      rehearsalN3: '',
      rehearsalN4: '',
      selectedAxes: []
    },
    axisCandidates: [],
    finalPredictions: null
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


