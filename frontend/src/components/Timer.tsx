import { useState, useEffect } from 'react'
import { Clock } from 'lucide-react'
import { formatTime } from '../lib/utils'

interface TimerProps {
  startTime: number
  isRunning: boolean
  className?: string
  showIcon?: boolean
  size?: 'sm' | 'md' | 'lg'
}

const sizeClasses = {
  sm: 'text-sm',
  md: 'text-base',
  lg: 'text-lg'
}

const iconSizes = {
  sm: 'h-3 w-3',
  md: 'h-4 w-4', 
  lg: 'h-5 w-5'
}

export function Timer({ 
  startTime, 
  isRunning, 
  className = '', 
  showIcon = true,
  size = 'md' 
}: TimerProps) {
  const [elapsed, setElapsed] = useState(0)
  
  useEffect(() => {
    if (!isRunning) return
    
    const interval = setInterval(() => {
      setElapsed(Date.now() - startTime)
    }, 100) // Update every 100ms for smooth display
    
    return () => clearInterval(interval)
  }, [startTime, isRunning])
  
  // Update immediately when startTime changes
  useEffect(() => {
    if (isRunning) {
      setElapsed(Date.now() - startTime)
    } else {
      setElapsed(0)
    }
  }, [startTime, isRunning])
  
  return (
    <div className={`flex items-center gap-1.5 font-mono ${sizeClasses[size]} ${className}`}>
      {showIcon && <Clock className={`${iconSizes[size]} text-muted-foreground`} />}
      <span className="text-foreground">
        {formatTime(elapsed)}
      </span>
    </div>
  )
}

interface UseTimerReturn {
  startTime: number
  elapsed: number
  formattedTime: string
  start: () => void
  reset: () => void
}

export function useTimer(): UseTimerReturn {
  const [startTime, setStartTime] = useState(Date.now())
  const [elapsed, setElapsed] = useState(0)
  
  useEffect(() => {
    const interval = setInterval(() => {
      setElapsed(Date.now() - startTime)
    }, 100)
    
    return () => clearInterval(interval)
  }, [startTime])
  
  const start = () => {
    setStartTime(Date.now())
    setElapsed(0)
  }
  
  const reset = () => {
    setStartTime(Date.now())
    setElapsed(0)
  }
  
  return {
    startTime,
    elapsed,
    formattedTime: formatTime(elapsed),
    start,
    reset
  }
}