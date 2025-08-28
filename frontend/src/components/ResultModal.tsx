import { motion, AnimatePresence } from 'framer-motion'
import { Button } from './ui/Button'
import { EquityDial } from './EquityDial'
import { Hand, Board } from './Card'
import { GradeResponse, Question } from '../lib/types'
import { formatTime, getSpeedCategory, getSpeedCategoryColor, parseCard, parseHand } from '../lib/utils'
import { Target, TrendingUp, Zap, Clock } from 'lucide-react'
import { useGameStore } from '../store/gameStore'

interface ResultModalProps {
  isOpen: boolean
  result: GradeResponse
  guess: number
  currentQuestion: Question
  onNext: () => void
}

export function ResultModal({ isOpen, result, guess, currentQuestion, onNext }: ResultModalProps) {
  const { getElapsedTime } = useGameStore()
  const elapsedTime = getElapsedTime()
  const speedCategory = getSpeedCategory(elapsedTime)
  const speedColor = getSpeedCategoryColor(speedCategory)
  
  const heroCards = parseHand(currentQuestion.hero)
  const villainCards = currentQuestion.villain ? parseHand(currentQuestion.villain) : null
  const boardCards = currentQuestion.board.map(parseCard)
  const isRangeMode = !currentQuestion.villain
  
  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 z-40"
            onClick={onNext}
          />
          
          {/* Modal */}
          <motion.div
            initial={{ opacity: 0, scale: 0.9, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.9, y: 20 }}
            className="fixed inset-0 z-50 flex items-center justify-center p-4"
          >
            <div className="bg-background border rounded-lg shadow-lg p-6 w-full max-w-lg">
              {/* Header */}
              <div className="text-center mb-6">
                <h2 className="text-2xl font-bold text-foreground mb-2">
                  Result: {result.delta.toFixed(1)}% Error
                </h2>
                
                <div className="flex items-center justify-center gap-4 text-sm text-muted-foreground flex-wrap">
                  <div className="flex items-center gap-1">
                    <Target className="h-4 w-4" />
                    <span>±{result.delta}%</span>
                  </div>
                  
                  <div className="flex items-center gap-1">
                    <Clock className="h-4 w-4" />
                    <span>{formatTime(elapsedTime)}</span>
                    <span className={`ml-1 font-medium ${speedColor}`}>
                      {speedCategory}
                    </span>
                  </div>
                  
                  {result.streak > 0 && (
                    <div className="flex items-center gap-1">
                      <Zap className="h-4 w-4 text-yellow-500" />
                      <span>{result.streak} streak</span>
                    </div>
                  )}
                </div>
              </div>
              
              {/* Hand Visualization */}
              <div className="mb-6 bg-muted/30 rounded-lg p-4">
                <h3 className="text-center text-sm font-medium text-muted-foreground mb-4">Hand Recap</h3>
                
                <div className="flex justify-between items-center mb-4">
                  <Hand cards={heroCards} label="Hero" size="sm" />
                  <div className="text-xl text-muted-foreground">vs</div>
                  {isRangeMode ? (
                    <div className="flex flex-col items-center gap-2">
                      <h3 className="text-sm font-medium text-muted-foreground">Range</h3>
                      <div className="w-12 h-16 bg-gradient-to-b from-purple-600 to-purple-800 border border-purple-500 rounded-lg shadow-sm flex items-center justify-center text-white font-bold text-xs">
                        Any 2
                      </div>
                    </div>
                  ) : (
                    <Hand cards={villainCards!} label="Villain" size="sm" />
                  )}
                </div>
                
                <div className="flex justify-center">
                  <Board cards={boardCards} street={currentQuestion.street} size="sm" />
                </div>
              </div>
              
              {/* Equity visualization */}
              <div className="flex justify-center mb-6">
                <EquityDial
                  truth={result.truth}
                  guess={guess}
                  revealed={true}
                  size="md"
                />
              </div>
              
              {/* Performance summary */}
              <div className="bg-muted/50 rounded-lg p-4 mb-6">
                <div className="grid grid-cols-3 gap-4 text-sm">
                  <div className="text-center">
                    <div className="font-semibold text-lg text-primary">
                      {guess.toFixed(1)}%
                    </div>
                    <div className="text-muted-foreground">Your Guess</div>
                  </div>
                  
                  <div className="text-center">
                    <div className="font-semibold text-lg text-primary">
                      {result.truth.toFixed(1)}%
                    </div>
                    <div className="text-muted-foreground">True Equity</div>
                  </div>
                  
                  <div className="text-center">
                    <div className="font-semibold text-lg">
                      {formatTime(elapsedTime)}
                    </div>
                    <div className={`text-xs font-medium ${speedColor}`}>
                      {speedCategory}
                    </div>
                  </div>
                </div>
              </div>
              
              {/* Explanations */}
              <div className="mb-6">
                <h3 className="font-medium mb-3 flex items-center gap-2">
                  <TrendingUp className="h-4 w-4" />
                  Analysis
                </h3>
                <ul className="space-y-2 text-sm text-muted-foreground">
                  {result.explain.map((explanation, index) => (
                    <li key={index} className="flex items-start gap-2">
                      <span className="text-primary">•</span>
                      <span>{explanation}</span>
                    </li>
                  ))}
                </ul>
              </div>
              
              {/* Source info */}
              <div className="text-xs text-muted-foreground text-center mb-6">
                Calculated using {result.source === 'exact' ? 'exact enumeration' : result.source}
              </div>
              
              {/* Actions */}
              <div className="flex gap-2">
                <Button
                  onClick={onNext}
                  className="flex-1"
                  size="lg"
                >
                  Next Hand
                </Button>
              </div>
              
              <div className="text-xs text-muted-foreground text-center mt-4">
                Press Space for next hand
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  )
}