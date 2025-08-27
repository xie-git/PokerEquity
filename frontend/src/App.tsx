import { useState, useEffect } from 'react'
import { GameHeader } from './components/GameHeader'
import { Game } from './components/Game'
import { StatsModal } from './components/StatsModal'
import { useGameStore } from './store/gameStore'

function App() {
  const [showStats, setShowStats] = useState(false)
  const { settings } = useGameStore()
  
  // Apply dark mode on mount
  useEffect(() => {
    if (settings.darkMode) {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }
  }, [settings.darkMode])
  
  return (
    <div className="min-h-screen bg-background">
      <GameHeader onShowStats={() => setShowStats(true)} />
      
      <main>
        <Game />
      </main>
      
      <StatsModal 
        isOpen={showStats} 
        onClose={() => setShowStats(false)} 
      />
    </div>
  )
}

export default App