import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { GameMode, GameState, GameSettings, Question, GradeResponse } from '../lib/types'
import { getDeviceId } from '../lib/api'

interface GameStore {
  // Game state
  mode: GameMode
  gameState: GameState
  currentQuestion: Question | null
  lastResult: GradeResponse | null
  startTime: number
  
  // Range mode settings
  opponentType: 'tight' | 'balanced' | 'loose' | 'random'
  
  // Settings
  settings: GameSettings
  deviceId: string
  
  // Daily mode
  dailyQuestions: Question[]
  dailyIndex: number
  
  // Actions
  setMode: (mode: GameMode) => void
  setGameState: (state: GameState) => void
  setCurrentQuestion: (question: Question | null) => void
  setLastResult: (result: GradeResponse | null) => void
  setOpponentType: (type: 'tight' | 'balanced' | 'loose' | 'random') => void
  startQuestion: () => void
  getElapsedTime: () => number
  updateSettings: (settings: Partial<GameSettings>) => void
  setDailyQuestions: (questions: Question[]) => void
  nextDailyQuestion: () => Question | null
  reset: () => void
}

export const useGameStore = create<GameStore>()(
  persist(
    (set, get) => ({
      // Initial state
      mode: 'drill',
      gameState: 'loading',
      currentQuestion: null,
      lastResult: null,
      startTime: 0,
      
      // Range mode settings
      opponentType: 'balanced',
      
      settings: {
        darkMode: false,
        soundEnabled: true,
      },
      deviceId: getDeviceId(),
      
      dailyQuestions: [],
      dailyIndex: 0,
      
      // Actions
      setMode: (mode) => set({ mode }),
      setGameState: (gameState) => set({ gameState }),
      setCurrentQuestion: (currentQuestion) => set({ currentQuestion }),
      setLastResult: (lastResult) => set({ lastResult }),
      setOpponentType: (opponentType) => set({ opponentType }),
      
      startQuestion: () => set({ 
        startTime: Date.now(), 
        gameState: 'input',
        lastResult: null 
      }),
      
      getElapsedTime: () => Date.now() - get().startTime,
      
      updateSettings: (newSettings) => set((state) => ({
        settings: { ...state.settings, ...newSettings }
      })),
      
      setDailyQuestions: (questions) => set({ 
        dailyQuestions: questions, 
        dailyIndex: 0 
      }),
      
      nextDailyQuestion: () => {
        const state = get()
        if (state.dailyIndex >= state.dailyQuestions.length) {
          return null
        }
        const question = state.dailyQuestions[state.dailyIndex]
        set({ dailyIndex: state.dailyIndex + 1 })
        return question
      },
      
      reset: () => set({
        currentQuestion: null,
        lastResult: null,
        startTime: 0,
        gameState: 'loading',
        dailyIndex: 0,
      }),
    }),
    {
      name: 'poker-equity-game',
      partialize: (state) => ({
        mode: state.mode,
        settings: state.settings,
        deviceId: state.deviceId,
        dailyIndex: state.dailyIndex,
      }),
    }
  )
)