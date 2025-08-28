import { useState, useEffect, useCallback } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { useGameStore } from '../store/gameStore'
import { api } from '../lib/api'
import { parseCard, parseHand } from '../lib/utils'
import { Hand, Board } from './Card'
import { PercentInput } from './PercentInput'
import { EquityDial } from './EquityDial'
import { ResultModal } from './ResultModal'
import { Timer } from './Timer'
import { Button } from './ui/Button'
import { Loader2 } from 'lucide-react'
import type { GradeRequest } from '../lib/types'

export function Game() {
  const {
    mode,
    gameState,
    currentQuestion,
    lastResult,
    deviceId,
    dailyQuestions,
    dailyIndex,
    startTime,
    opponentType,
    setGameState,
    setCurrentQuestion,
    setLastResult,
    startQuestion,
    getElapsedTime,
    setDailyQuestions,
    nextDailyQuestion,
  } = useGameStore()
  
  const [equityGuess, setEquityGuessOriginal] = useState(50)
  const [submittedGuess, setSubmittedGuess] = useState<number | null>(null)
  
  const setEquityGuess = useCallback((value: number | ((prev: number) => number)) => {
    const newValue = typeof value === 'function' ? value(equityGuess) : value
    setEquityGuessOriginal(newValue)
  }, [equityGuess])
  
  // Deal new question mutation
  const dealMutation = useMutation({
    mutationFn: () => api.dealQuestion(mode, opponentType),
    onSuccess: (question) => {
      setCurrentQuestion(question)
      setEquityGuess(50)
      startQuestion()
    },
    onError: (error) => {
      console.error('Failed to deal question:', error)
      setGameState('loading')
    }
  })
  
  // Grade answer mutation
  const gradeMutation = useMutation({
    mutationFn: (request: GradeRequest) => api.gradeAnswer(request),
    onSuccess: (result) => {
      setLastResult(result)
      setGameState('result')
    },
    onError: (error) => {
      console.error('Failed to grade answer:', error)
    }
  })
  
  // Daily questions query
  const { refetch: fetchDailyQuestions } = useQuery({
    queryKey: ['daily', deviceId],
    queryFn: () => api.getDailyQuestions(deviceId),
    enabled: false,
  })
  
  // Handle daily questions success
  const handleDailyQuestionsSuccess = (questions: any[]) => {
    setDailyQuestions(questions)
    if (questions.length > 0) {
      const firstQuestion = questions[0]
      setCurrentQuestion(firstQuestion)
      setEquityGuess(50)
      startQuestion()
    }
  }
  
  // Load initial question
  useEffect(() => {
    if (mode === 'drill' || mode === 'hidden') {
      dealMutation.mutate()
    } else {
      // Daily mode - check if we have questions loaded
      if (dailyQuestions.length === 0 || dailyIndex === 0) {
        fetchDailyQuestions().then(result => {
          if (result.data) handleDailyQuestionsSuccess(result.data)
        })
      } else if (dailyIndex < dailyQuestions.length) {
        // Continue with existing daily questions
        const question = dailyQuestions[dailyIndex]
        setCurrentQuestion(question)
        setEquityGuess(50)
        startQuestion()
      }
    }
  }, [mode]) // Only run when mode changes
  
  // Handle next question
  const handleNext = useCallback(() => {
    setLastResult(null)
    setSubmittedGuess(null) // Reset submitted guess
    
    if (mode === 'drill' || mode === 'hidden') {
      dealMutation.mutate()
    } else {
      // Daily mode
      const nextQuestion = nextDailyQuestion()
      if (nextQuestion) {
        setCurrentQuestion(nextQuestion)
        setEquityGuess(50)
        startQuestion()
      } else {
        // All daily questions completed
        setGameState('loading')
        setCurrentQuestion(null)
      }
    }
  }, [mode, dealMutation, nextDailyQuestion, setCurrentQuestion, setEquityGuess, startQuestion, setLastResult, setGameState])
  
  // Handle submit guess
  const handleSubmit = useCallback(() => {
    if (!currentQuestion || gameState !== 'input') return
    
    setSubmittedGuess(equityGuess) // Store the submitted guess
    
    const gradeRequest: GradeRequest = {
      id: currentQuestion.id,
      guess_equity_hero: equityGuess,
      elapsed_ms: getElapsedTime(),
      device_id: deviceId,
    }
    
    gradeMutation.mutate(gradeRequest)
  }, [currentQuestion, equityGuess, getElapsedTime, deviceId, gameState, gradeMutation])
  
  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.code === 'Space') {
        // Only handle Space when not typing in an input
        if (e.target instanceof HTMLInputElement) return
        e.preventDefault()
        if (gameState === 'result') {
          handleNext()
        } else if (gameState === 'input') {
          handleSubmit()
        }
      } else if (e.key === 'ArrowUp' || e.key === 'ArrowDown') {
        // Handle arrow keys globally for equity adjustment
        if (gameState === 'input') {
          e.preventDefault()
          const increment = e.key === 'ArrowUp' ? 1 : -1
          setEquityGuess(prev => Math.max(0, Math.min(100, Math.round((prev + increment) * 10) / 10)))
        }
      } else if (e.key === 'Enter') {
        // Handle Enter key globally for submit
        if (gameState === 'input') {
          e.preventDefault()
          handleSubmit()
        }
      }
    }
    
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [gameState, handleNext, handleSubmit, setEquityGuess])
  
  // Loading state
  if (gameState === 'loading' || !currentQuestion) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] gap-4">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
        <div className="text-muted-foreground">
          {mode === 'daily' && dailyIndex >= dailyQuestions.length 
            ? "All daily questions completed! Come back tomorrow for new challenges."
            : "Loading next hand..."
          }
        </div>
        {mode === 'daily' && dailyIndex >= dailyQuestions.length && (
          <Button onClick={() => { window.location.reload() }}>
            Play Drill Mode
          </Button>
        )}
      </div>
    )
  }
  
  const heroCards = parseHand(currentQuestion.hero)
  const isRangeMode = currentQuestion.villain.startsWith('range_')
  const rangeOpponentType = isRangeMode ? currentQuestion.villain.replace('range_', '') : null
  const villainCards = !isRangeMode && currentQuestion.villain ? parseHand(currentQuestion.villain) : null
  const boardCards = currentQuestion.board.map(parseCard)
  
  return (
    <div className="container mx-auto px-4 py-8">
      {/* Mode indicator and Timer */}
      <div className="flex items-center justify-center mb-6 gap-4">
        <div className="inline-flex items-center gap-2 bg-muted px-3 py-1 rounded-full text-sm">
          <span className="capitalize">{mode} Mode</span>
          {mode === 'daily' && (
            <span className="text-muted-foreground">
              {dailyIndex}/{dailyQuestions.length}
            </span>
          )}
        </div>
        
        {gameState === 'input' && (
          <Timer 
            startTime={startTime}
            isRunning={true}
            size="lg"
            className="bg-primary/10 px-3 py-1 rounded-full"
          />
        )}
      </div>
      
      {/* Game board */}
      <div className="max-w-4xl mx-auto">
        <div className="grid gap-8">
          {/* Hands */}
          <div className="flex justify-between items-center">
            <Hand cards={heroCards} label="Hero (You)" size="lg" />
            <div className="text-4xl text-muted-foreground">vs</div>
            {isRangeMode ? (
              <div className="flex flex-col items-center gap-2">
                <h3 className="text-sm font-medium text-muted-foreground capitalize">{rangeOpponentType} Range</h3>
                <div className="flex gap-1">
                  <div className="w-20 h-28 bg-gradient-to-b from-purple-600 to-purple-800 border border-purple-500 rounded-lg shadow-sm flex items-center justify-center text-white font-bold text-xs text-center">
                    {rangeOpponentType === 'tight' ? 'Top 20%' : 
                     rangeOpponentType === 'loose' ? 'Top 40%' :
                     rangeOpponentType === 'random' ? 'Any 2' : 'Top 25%'}
                  </div>
                </div>
              </div>
            ) : villainCards ? (
              <Hand cards={villainCards} label="Villain" size="lg" />
            ) : (
              <div className="flex flex-col items-center gap-2">
                <h3 className="text-sm font-medium text-muted-foreground">Loading...</h3>
                <div className="flex gap-1">
                  <div className="w-20 h-28 bg-muted rounded-lg animate-pulse"></div>
                  <div className="w-20 h-28 bg-muted rounded-lg animate-pulse"></div>
                </div>
              </div>
            )}
          </div>
          
          {/* Board */}
          <div className="flex justify-center">
            <Board 
              cards={boardCards} 
              street={currentQuestion.street} 
              size="lg" 
            />
          </div>
          
          {/* Equity visualization */}
          <div className="flex justify-center">
            {gameState === 'input' && (
              <EquityDial value={equityGuess} size="lg" />
            )}
          </div>
          
          {/* Input */}
          <div className="flex justify-center">
            {gameState === 'input' && (
              <PercentInput
                key={currentQuestion?.id} // Reset component for each new question
                value={equityGuess}
                onChange={setEquityGuess}
                onSubmit={handleSubmit}
                disabled={gradeMutation.isPending}
                autoFocus={true}
              />
            )}
            
            {gradeMutation.isPending && (
              <div className="flex items-center gap-2 text-muted-foreground">
                <Loader2 className="h-4 w-4 animate-spin" />
                <span>Calculating...</span>
              </div>
            )}
          </div>
          
          {/* Tags */}
          {currentQuestion.tags.length > 0 && (
            <div className="flex justify-center">
              <div className="flex gap-2 flex-wrap">
                {currentQuestion.tags.map(tag => (
                  <span 
                    key={tag}
                    className="px-2 py-1 bg-muted text-muted-foreground rounded text-xs"
                  >
                    {tag.replace('_', ' ')}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
      
      {/* Result modal */}
      {lastResult && submittedGuess !== null && currentQuestion && (
        <ResultModal
          isOpen={gameState === 'result'}
          result={lastResult}
          guess={submittedGuess}
          currentQuestion={currentQuestion}
          onNext={handleNext}
        />
      )}
    </div>
  )
}