import { motion, AnimatePresence } from 'framer-motion'
import { useQuery } from '@tanstack/react-query'
import { Button } from './ui/Button'
import { api } from '../lib/api'
import { useGameStore } from '../store/gameStore'
import { BarChart3, Trophy, TrendingUp, X } from 'lucide-react'

interface StatsModalProps {
  isOpen: boolean
  onClose: () => void
}

export function StatsModal({ isOpen, onClose }: StatsModalProps) {
  const { deviceId } = useGameStore()
  
  const { data: stats, isLoading } = useQuery({
    queryKey: ['stats', deviceId],
    queryFn: () => api.getPlayerStats(deviceId),
    enabled: isOpen,
  })
  
  const streetOrder = ['pre', 'flop', 'turn', 'river']
  
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
            onClick={onClose}
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
              <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-2">
                  <BarChart3 className="h-6 w-6 text-primary" />
                  <h2 className="text-2xl font-bold">Your Stats</h2>
                </div>
                <Button variant="ghost" size="icon" onClick={onClose}>
                  <X className="h-4 w-4" />
                </Button>
              </div>
              
              {isLoading ? (
                <div className="text-center py-8">
                  <div className="text-muted-foreground">Loading stats...</div>
                </div>
              ) : !stats || stats.games_played === 0 ? (
                <div className="text-center py-8">
                  <Trophy className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                  <div className="text-muted-foreground">
                    Play some hands to see your stats!
                  </div>
                </div>
              ) : (
                <div className="space-y-6">
                  {/* Overall stats */}
                  <div className="grid grid-cols-2 gap-4">
                    <div className="bg-muted/50 rounded-lg p-4 text-center">
                      <div className="text-2xl font-bold text-primary">
                        {stats.games_played}
                      </div>
                      <div className="text-sm text-muted-foreground">
                        Games Played
                      </div>
                    </div>
                    
                    <div className="bg-muted/50 rounded-lg p-4 text-center">
                      <div className="text-2xl font-bold text-primary">
                        {stats.avg_delta.toFixed(1)}%
                      </div>
                      <div className="text-sm text-muted-foreground">
                        Avg Error
                      </div>
                    </div>
                  </div>
                  
                  <div className="grid grid-cols-2 gap-4">
                    <div className="bg-muted/50 rounded-lg p-4 text-center">
                      <div className="text-2xl font-bold text-green-600">
                        {stats.perfects}
                      </div>
                      <div className="text-sm text-muted-foreground">
                        Perfect Guesses
                      </div>
                    </div>
                    
                    <div className="bg-muted/50 rounded-lg p-4 text-center">
                      <div className="text-2xl font-bold text-blue-600">
                        {(stats.close_rate * 100).toFixed(0)}%
                      </div>
                      <div className="text-sm text-muted-foreground">
                        Close Rate (≤1%)
                      </div>
                    </div>
                  </div>
                  
                  {/* By street breakdown */}
                  {Object.keys(stats.by_street).length > 0 && (
                    <div>
                      <h3 className="font-medium mb-3 flex items-center gap-2">
                        <TrendingUp className="h-4 w-4" />
                        Performance by Street
                      </h3>
                      
                      <div className="space-y-3">
                        {streetOrder
                          .filter(street => stats.by_street[street])
                          .map(street => {
                            const streetStats = stats.by_street[street]
                            const accuracy = Math.max(0, 100 - streetStats.avg_delta * 10)
                            
                            return (
                              <div key={street} className="bg-muted/30 rounded-lg p-3">
                                <div className="flex items-center justify-between mb-2">
                                  <span className="font-medium capitalize">
                                    {street === 'pre' ? 'Preflop' : street}
                                  </span>
                                  <div className="text-sm text-muted-foreground">
                                    {streetStats.attempts} hands
                                  </div>
                                </div>
                                
                                <div className="flex items-center gap-2">
                                  <div className="flex-1 bg-muted rounded-full h-2">
                                    <div
                                      className="bg-primary rounded-full h-2 transition-all"
                                      style={{ width: `${Math.min(100, accuracy)}%` }}
                                    />
                                  </div>
                                  <div className="text-sm font-medium">
                                    {streetStats.avg_delta.toFixed(1)}%
                                  </div>
                                </div>
                              </div>
                            )
                          })
                        }
                      </div>
                    </div>
                  )}
                </div>
              )}
              
              <div className="mt-6 pt-6 border-t text-xs text-muted-foreground text-center">
                Stats are stored locally and tied to this device
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  )
}