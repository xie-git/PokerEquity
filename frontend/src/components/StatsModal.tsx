import { motion, AnimatePresence } from 'framer-motion'
import { useQuery } from '@tanstack/react-query'
import { Button } from './ui/Button'
import { api } from '../lib/api'
import { useGameStore } from '../store/gameStore'
import { formatTime } from '../lib/utils'
import { 
  BarChart3, 
  Clock, 
  TrendingUp, 
  X, 
  Calendar,
  Target,
  Zap,
  Activity
} from 'lucide-react'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell
} from 'recharts'

interface StatsModalProps {
  isOpen: boolean
  onClose: () => void
}

interface TimeAnalytics {
  avgTimeMs: number
  medianTimeMs: number
  fastestTimeMs: number
  slowestTimeMs: number
  speedDistribution: { category: string; count: number; percentage: number }[]
  accuracyBySpeed: { category: string; avgAccuracy: number; count: number }[]
}

interface PerformanceData {
  date: string
  avgAccuracy: number
  avgTimeMs: number
  handsPlayed: number
}

// Mock data for development - will be replaced with real API calls
const mockTimeAnalytics: TimeAnalytics = {
  avgTimeMs: 11800,
  medianTimeMs: 9500,
  fastestTimeMs: 2300,
  slowestTimeMs: 45200,
  speedDistribution: [
    { category: 'Lightning', count: 45, percentage: 15 },
    { category: 'Fast', count: 120, percentage: 40 },
    { category: 'Normal', count: 105, percentage: 35 },
    { category: 'Careful', count: 30, percentage: 10 }
  ],
  accuracyBySpeed: [
    { category: 'Lightning', avgAccuracy: 5.2, count: 45 },
    { category: 'Fast', avgAccuracy: 3.8, count: 120 },
    { category: 'Normal', avgAccuracy: 2.9, count: 105 },
    { category: 'Careful', avgAccuracy: 2.1, count: 30 }
  ]
}

const mockPerformanceData: PerformanceData[] = [
  { date: '2024-08-20', avgAccuracy: 4.2, avgTimeMs: 15300, handsPlayed: 23 },
  { date: '2024-08-21', avgAccuracy: 3.8, avgTimeMs: 13200, handsPlayed: 31 },
  { date: '2024-08-22', avgAccuracy: 3.1, avgTimeMs: 12100, handsPlayed: 28 },
  { date: '2024-08-23', avgAccuracy: 2.9, avgTimeMs: 11800, handsPlayed: 35 },
  { date: '2024-08-24', avgAccuracy: 2.7, avgTimeMs: 11200, handsPlayed: 42 },
  { date: '2024-08-25', avgAccuracy: 2.4, avgTimeMs: 10900, handsPlayed: 38 },
  { date: '2024-08-26', avgAccuracy: 2.2, avgTimeMs: 10500, handsPlayed: 41 },
  { date: '2024-08-27', avgAccuracy: 2.1, avgTimeMs: 10200, handsPlayed: 33 }
]

const SPEED_COLORS = {
  Lightning: '#8b5cf6',
  Fast: '#10b981', 
  Normal: '#3b82f6',
  Careful: '#f59e0b'
}

export function StatsModal({ isOpen, onClose }: StatsModalProps) {
  const { deviceId } = useGameStore()
  
  const { data: stats, isLoading } = useQuery({
    queryKey: ['enhancedStats', deviceId],
    queryFn: () => api.getEnhancedPlayerStats(deviceId),
    enabled: isOpen,
  })
  
  // Extract time analytics and performance data from API response
  const timeAnalytics = stats?.timeAnalytics || mockTimeAnalytics
  const performanceData = stats?.performanceData || mockPerformanceData
  
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
            <div className="bg-background border rounded-lg shadow-lg w-full max-w-4xl max-h-[90vh] overflow-y-auto">
              {/* Header */}
              <div className="flex items-center justify-between p-6 border-b">
                <div className="flex items-center gap-2">
                  <BarChart3 className="h-6 w-6 text-primary" />
                  <h2 className="text-2xl font-bold">Performance Analytics</h2>
                </div>
                <Button variant="ghost" size="icon" onClick={onClose}>
                  <X className="h-4 w-4" />
                </Button>
              </div>
              
              <div className="p-6 space-y-8">
                {isLoading ? (
                  <div className="text-center py-8">
                    <div className="text-muted-foreground">Loading analytics...</div>
                  </div>
                ) : !stats || stats.games_played === 0 ? (
                  <div className="text-center py-8">
                    <Activity className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                    <div className="text-muted-foreground">
                      Play some hands to see your analytics!
                    </div>
                  </div>
                ) : (
                  <>
                    {/* Lifetime Overview */}
                    <div>
                      <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                        <Calendar className="h-5 w-5" />
                        Lifetime Statistics
                      </h3>
                      
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        <div className="bg-muted/50 rounded-lg p-4 text-center">
                          <div className="text-2xl font-bold text-primary">
                            {stats.games_played}
                          </div>
                          <div className="text-sm text-muted-foreground">
                            Total Hands
                          </div>
                        </div>
                        
                        <div className="bg-muted/50 rounded-lg p-4 text-center">
                          <div className="text-2xl font-bold text-primary">
                            {stats.avg_delta.toFixed(1)}%
                          </div>
                          <div className="text-sm text-muted-foreground">
                            Avg Accuracy
                          </div>
                        </div>
                        
                        <div className="bg-muted/50 rounded-lg p-4 text-center">
                          <div className="text-2xl font-bold text-primary">
                            {formatTime(timeAnalytics.avgTimeMs)}
                          </div>
                          <div className="text-sm text-muted-foreground">
                            Avg Time
                          </div>
                        </div>
                        
                        <div className="bg-muted/50 rounded-lg p-4 text-center">
                          <div className="text-2xl font-bold text-green-600">
                            {stats.perfects}
                          </div>
                          <div className="text-sm text-muted-foreground">
                            Perfect (≤0.5%)
                          </div>
                        </div>
                      </div>
                    </div>
                    
                    {/* Performance Trend Chart */}
                    <div>
                      <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                        <TrendingUp className="h-5 w-5" />
                        Accuracy Trend (Last 30 Days)
                      </h3>
                      
                      <div className="bg-muted/20 rounded-lg p-4 h-64">
                        <ResponsiveContainer width="100%" height="100%">
                          <LineChart data={performanceData}>
                            <CartesianGrid strokeDasharray="3 3" />
                            <XAxis 
                              dataKey="date" 
                              tickFormatter={(value) => new Date(String(value)).toLocaleDateString()}
                            />
                            <YAxis 
                              label={{ value: 'Avg Error (%)', angle: -90, position: 'insideLeft' }}
                            />
                            <Tooltip 
                              labelFormatter={(value) => new Date(String(value)).toLocaleDateString()}
                              formatter={(value: number) => [`${value.toFixed(1)}%`, 'Avg Error']}
                            />
                            <Line 
                              type="monotone" 
                              dataKey="avgAccuracy" 
                              stroke="#3b82f6" 
                              strokeWidth={2}
                              dot={{ r: 4 }}
                            />
                          </LineChart>
                        </ResponsiveContainer>
                      </div>
                    </div>
                    
                    {/* Time Analytics */}
                    <div>
                      <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                        <Clock className="h-5 w-5" />
                        Time Analytics
                      </h3>
                      
                      <div className="grid md:grid-cols-2 gap-6">
                        {/* Speed Distribution */}
                        <div>
                          <h4 className="font-medium mb-3">Speed Distribution</h4>
                          <div className="bg-muted/20 rounded-lg p-4 h-48">
                            <ResponsiveContainer width="100%" height="100%">
                              <PieChart>
                                <Pie
                                  data={timeAnalytics.speedDistribution}
                                  cx="50%"
                                  cy="50%"
                                  outerRadius={60}
                                  fill="#8884d8"
                                  dataKey="percentage"
                                  label={({ category, percentage }: { category: string; percentage: number }) => `${category}: ${percentage}%`}
                                >
                                  {timeAnalytics.speedDistribution.map((entry, index) => (
                                    <Cell 
                                      key={`cell-${index}`} 
                                      fill={SPEED_COLORS[entry.category as keyof typeof SPEED_COLORS]} 
                                    />
                                  ))}
                                </Pie>
                                <Tooltip />
                              </PieChart>
                            </ResponsiveContainer>
                          </div>
                        </div>
                        
                        {/* Accuracy by Speed */}
                        <div>
                          <h4 className="font-medium mb-3">Accuracy by Speed</h4>
                          <div className="bg-muted/20 rounded-lg p-4 h-48">
                            <ResponsiveContainer width="100%" height="100%">
                              <BarChart data={timeAnalytics.accuracyBySpeed}>
                                <CartesianGrid strokeDasharray="3 3" />
                                <XAxis dataKey="category" />
                                <YAxis label={{ value: 'Avg Error (%)', angle: -90, position: 'insideLeft' }} />
                                <Tooltip formatter={(value: number) => `${value}%`} />
                                <Bar 
                                  dataKey="avgAccuracy" 
                                  fill="#3b82f6"
                                />
                              </BarChart>
                            </ResponsiveContainer>
                          </div>
                        </div>
                      </div>
                      
                      {/* Time Records */}
                      <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mt-6">
                        <div className="bg-muted/50 rounded-lg p-3 text-center">
                          <div className="text-lg font-semibold text-green-600">
                            {formatTime(timeAnalytics.fastestTimeMs)}
                          </div>
                          <div className="text-xs text-muted-foreground">Fastest</div>
                        </div>
                        
                        <div className="bg-muted/50 rounded-lg p-3 text-center">
                          <div className="text-lg font-semibold text-primary">
                            {formatTime(timeAnalytics.medianTimeMs)}
                          </div>
                          <div className="text-xs text-muted-foreground">Median</div>
                        </div>
                        
                        <div className="bg-muted/50 rounded-lg p-3 text-center">
                          <div className="text-lg font-semibold text-orange-600">
                            {formatTime(timeAnalytics.slowestTimeMs)}
                          </div>
                          <div className="text-xs text-muted-foreground">Slowest</div>
                        </div>
                      </div>
                    </div>
                    
                    {/* Street Performance */}
                    {Object.keys(stats.by_street).length > 0 && (
                      <div>
                        <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                          <Target className="h-5 w-5" />
                          Performance by Street
                        </h3>
                        
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                          {['pre', 'flop', 'turn', 'river'].map(street => {
                            const streetStats = stats.by_street[street]
                            if (!streetStats) return null
                            
                            return (
                              <div key={street} className="bg-muted/30 rounded-lg p-4">
                                <div className="font-medium capitalize mb-2">
                                  {street === 'pre' ? 'Preflop' : street}
                                </div>
                                
                                <div className="space-y-2">
                                  <div>
                                    <div className="text-lg font-semibold text-primary">
                                      {streetStats.avg_delta.toFixed(1)}%
                                    </div>
                                    <div className="text-xs text-muted-foreground">
                                      Avg Error
                                    </div>
                                  </div>
                                  
                                  <div>
                                    <div className="text-sm font-medium">
                                      {streetStats.attempts}
                                    </div>
                                    <div className="text-xs text-muted-foreground">
                                      Hands
                                    </div>
                                  </div>
                                </div>
                              </div>
                            )
                          })}
                        </div>
                      </div>
                    )}
                    
                    {/* Insights */}
                    <div>
                      <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                        <Zap className="h-5 w-5" />
                        Performance Insights
                      </h3>
                      
                      <div className="bg-blue-50 dark:bg-blue-950/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
                        <ul className="space-y-2 text-sm">
                          <li className="flex items-start gap-2">
                            <span className="text-blue-600">•</span>
                            <span>
                              Your accuracy is improving - 15% better than last week!
                            </span>
                          </li>
                          <li className="flex items-start gap-2">
                            <span className="text-blue-600">•</span>
                            <span>
                              You perform best in the "Normal" speed range (8-20s).
                            </span>
                          </li>
                          <li className="flex items-start gap-2">
                            <span className="text-blue-600">•</span>
                            <span>
                              Turn decisions are your strongest street.
                            </span>
                          </li>
                        </ul>
                      </div>
                    </div>
                  </>
                )}
              </div>
              
              <div className="border-t p-6 text-xs text-muted-foreground text-center">
                Statistics are stored locally and persist across sessions
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  )
}