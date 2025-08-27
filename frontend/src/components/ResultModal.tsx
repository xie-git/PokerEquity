import { motion, AnimatePresence } from 'framer-motion'
import { Button } from './ui/Button'
import { EquityDial } from './EquityDial'
import { GradeResponse } from '../lib/types'
import { getScoreColor, getScoreLabel, getStreakBonus } from '../lib/utils'
import { Trophy, Target, TrendingUp, Zap } from 'lucide-react'

interface ResultModalProps {
  isOpen: boolean
  result: GradeResponse
  guess: number
  onNext: () => void
}

export function ResultModal({ isOpen, result, guess, onNext }: ResultModalProps) {
  const streakBonus = getStreakBonus(result.streak)
  
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
            <div className="bg-background border rounded-lg shadow-lg p-6 w-full max-w-md">
              {/* Header */}
              <div className="text-center mb-6">
                <div className="flex items-center justify-center gap-2 mb-2">
                  <Trophy className={`h-6 w-6 ${getScoreColor(result.score)}`} />
                  <h2 className="text-2xl font-bold">
                    {getScoreLabel(result.score)}
                  </h2>
                </div>
                
                <div className="flex items-center justify-center gap-4 text-sm text-muted-foreground">
                  <div className="flex items-center gap-1">
                    <Target className="h-4 w-4" />
                    <span>±{result.delta}%</span>
                  </div>
                  
                  {result.streak > 0 && (
                    <div className="flex items-center gap-1">
                      <Zap className="h-4 w-4 text-yellow-500" />
                      <span>{result.streak} streak</span>
                    </div>
                  )}
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
              
              {/* Score breakdown */}
              <div className="bg-muted/50 rounded-lg p-4 mb-6">
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div className="text-center">
                    <div className="font-semibold text-lg">
                      {Math.round(result.score / (1 + streakBonus/100))}
                    </div>
                    <div className="text-muted-foreground">Base Score</div>
                  </div>
                  
                  <div className="text-center">
                    <div className="font-semibold text-lg text-primary">
                      {result.score}
                    </div>
                    <div className="text-muted-foreground">
                      Final Score
                      {streakBonus > 0 && (
                        <span className="text-yellow-600 ml-1">
                          (+{streakBonus}%)
                        </span>
                      )}
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