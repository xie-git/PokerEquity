import { motion } from 'framer-motion'

interface EquityDialProps {
  value?: number
  guess?: number
  truth?: number
  revealed?: boolean
  size?: 'sm' | 'md' | 'lg'
}

const sizes = {
  sm: { size: 120, stroke: 8, text: 'text-lg' },
  md: { size: 160, stroke: 10, text: 'text-2xl' },
  lg: { size: 200, stroke: 12, text: 'text-3xl' }
}

export function EquityDial({ 
  value = 0, 
  guess, 
  truth, 
  revealed = false, 
  size = 'md' 
}: EquityDialProps) {
  const { size: dialSize, stroke, text } = sizes[size]
  const radius = (dialSize - stroke) / 2
  const circumference = 2 * Math.PI * radius
  const center = dialSize / 2
  
  // Calculate stroke dash offset for the arc
  const valueOffset = circumference - (value / 100) * circumference
  const guessOffset = guess ? circumference - (guess / 100) * circumference : circumference
  const truthOffset = truth ? circumference - (truth / 100) * circumference : circumference
  
  return (
    <div className="flex flex-col items-center gap-2">
      <div className="relative" style={{ width: dialSize, height: dialSize }}>
        {/* Background circle */}
        <svg width={dialSize} height={dialSize} className="transform -rotate-90">
          <circle
            cx={center}
            cy={center}
            r={radius}
            fill="none"
            stroke="currentColor"
            strokeWidth={stroke}
            className="text-muted/20"
          />
          
          {/* Current value arc */}
          {!revealed && (
            <motion.circle
              cx={center}
              cy={center}
              r={radius}
              fill="none"
              stroke="currentColor"
              strokeWidth={stroke}
              strokeLinecap="round"
              strokeDasharray={circumference}
              strokeDashoffset={valueOffset}
              className="text-primary"
              initial={{ strokeDashoffset: circumference }}
              animate={{ strokeDashoffset: valueOffset }}
              transition={{ duration: 0.6, ease: "easeOut" }}
            />
          )}
          
          {/* Revealed state - show both guess and truth */}
          {revealed && guess !== undefined && (
            <motion.circle
              cx={center}
              cy={center}
              r={radius}
              fill="none"
              stroke="currentColor"
              strokeWidth={stroke}
              strokeLinecap="round"
              strokeDasharray={circumference}
              strokeDashoffset={guessOffset}
              className="text-blue-500"
              initial={{ strokeDashoffset: circumference }}
              animate={{ strokeDashoffset: guessOffset }}
              transition={{ duration: 0.6, ease: "easeOut" }}
            />
          )}
          
          {revealed && truth !== undefined && (
            <motion.circle
              cx={center}
              cy={center}
              r={radius - stroke/2}
              fill="none"
              stroke="currentColor"
              strokeWidth={stroke/2}
              strokeLinecap="round"
              strokeDasharray={circumference - stroke}
              strokeDashoffset={truthOffset}
              className="text-green-500"
              initial={{ strokeDashoffset: circumference }}
              animate={{ strokeDashoffset: truthOffset }}
              transition={{ duration: 0.8, ease: "easeOut", delay: 0.2 }}
            />
          )}
        </svg>
        
        {/* Center text */}
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="text-center">
            <div className={`${text} font-bold`}>
              {revealed && truth !== undefined 
                ? `${truth.toFixed(1)}%`
                : `${value.toFixed(1)}%`
              }
            </div>
            {revealed && guess !== undefined && truth !== undefined && (
              <div className="text-xs text-muted-foreground mt-1">
                Guess: {guess.toFixed(1)}%
              </div>
            )}
          </div>
        </div>
      </div>
      
      {/* Legend for revealed state */}
      {revealed && guess !== undefined && truth !== undefined && (
        <div className="flex gap-4 text-xs">
          <div className="flex items-center gap-1">
            <div className="w-3 h-3 bg-blue-500 rounded-full"></div>
            <span>Your guess</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-3 h-3 bg-green-500 rounded-full"></div>
            <span>True equity</span>
          </div>
        </div>
      )}
    </div>
  )
}