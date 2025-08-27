import { Button } from './ui/Button'
import { Moon, Sun, BarChart3 } from 'lucide-react'
import { useGameStore } from '../store/gameStore'

interface GameHeaderProps {
  onShowStats: () => void
}

export function GameHeader({ onShowStats }: GameHeaderProps) {
  const { mode, setMode, settings, updateSettings } = useGameStore()
  
  const toggleDarkMode = () => {
    updateSettings({ darkMode: !settings.darkMode })
    document.documentElement.classList.toggle('dark')
  }
  
  return (
    <header className="border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container flex h-16 items-center justify-between">
        {/* Logo */}
        <div className="flex items-center gap-2">
          <div className="text-2xl font-bold text-primary">♠</div>
          <h1 className="text-xl font-bold">Poker Equity Trainer</h1>
        </div>
        
        {/* Mode selector */}
        <div className="flex items-center gap-1 bg-muted rounded-lg p-1">
          <Button
            variant={mode === 'drill' ? 'default' : 'ghost'}
            size="sm"
            onClick={() => setMode('drill')}
          >
            Drill Mode
          </Button>
          <Button
            variant={mode === 'daily' ? 'default' : 'ghost'}
            size="sm"
            onClick={() => setMode('daily')}
          >
            Daily 10
          </Button>
        </div>
        
        {/* Actions */}
        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            size="icon"
            onClick={onShowStats}
          >
            <BarChart3 className="h-4 w-4" />
          </Button>
          
          <Button
            variant="ghost"
            size="icon"
            onClick={toggleDarkMode}
          >
            {settings.darkMode ? (
              <Sun className="h-4 w-4" />
            ) : (
              <Moon className="h-4 w-4" />
            )}
          </Button>
        </div>
      </div>
    </header>
  )
}