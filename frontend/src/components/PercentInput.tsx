import React, { useState, useEffect, useRef } from 'react'
import { Input } from './ui/Input'
import { Button } from './ui/Button'
import { ChevronUp, ChevronDown } from 'lucide-react'
import { clampEquity } from '../lib/utils'

interface PercentInputProps {
  value: number
  onChange: (value: number) => void
  onSubmit: () => void
  disabled?: boolean
  autoFocus?: boolean
}

export function PercentInput({ 
  value, 
  onChange, 
  onSubmit,
  disabled = false,
  autoFocus = false 
}: PercentInputProps) {
  const [inputValue, setInputValue] = useState(value.toString())
  const inputRef = useRef<HTMLInputElement>(null)
  const isUserTypingRef = useRef(false)
  
  // Sync inputValue with value prop (only when user is not actively typing)
  useEffect(() => {
    if (!isUserTypingRef.current) {
      setInputValue(value.toFixed(1))
    }
  }, [value])

  
  useEffect(() => {
    if (autoFocus && inputRef.current) {
      inputRef.current.focus()
      inputRef.current.select()
    }
  }, [autoFocus])

  // Reset typing flag when component unmounts (for new questions)
  useEffect(() => {
    return () => {
      isUserTypingRef.current = false
    }
  }, [])

  // Add wheel event listener with passive: false to allow preventDefault
  useEffect(() => {
    const inputElement = inputRef.current
    if (!inputElement) return

    const handleWheel = (e: WheelEvent) => {
      e.preventDefault() // Prevent page scroll
      const delta = e.deltaY > 0 ? -1 : 1 // Scroll down = -1%, scroll up = +1%
      const result = Math.round((value + delta) * 10) / 10
      const clampedResult = clampEquity(result)
      onChange(clampedResult)
      setInputValue(clampedResult.toFixed(1)) // Immediately update input display
    }

    inputElement.addEventListener('wheel', handleWheel, { passive: false })
    return () => inputElement.removeEventListener('wheel', handleWheel)
  }, [value, onChange])
  
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = e.target.value
    isUserTypingRef.current = true // User is actively typing
    setInputValue(newValue)
    
    // Only update parent if we have a valid complete number
    const numValue = parseFloat(newValue)
    if (!isNaN(numValue) && newValue.trim() !== '' && newValue !== '.') {
      onChange(clampEquity(numValue))
    }
  }
  
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      onSubmit()
    }
    // Arrow keys are now handled globally in the Game component
  }

  
  const adjustValue = (delta: number) => {
    const result = Math.round((value + delta) * 10) / 10 // Fix floating point precision
    onChange(clampEquity(result))
  }
  
  return (
    <div className="flex flex-col items-center gap-4">
      <div className="relative">
        <Input
          ref={inputRef}
          type="text"
          value={inputValue}
          onChange={handleInputChange}
          onKeyDown={handleKeyDown}
          onBlur={() => {
            isUserTypingRef.current = false // User stopped typing
            const numValue = parseFloat(inputValue)
            if (isNaN(numValue) || inputValue.trim() === '') {
              setInputValue(value.toFixed(1))
            } else {
              const clampedValue = clampEquity(numValue)
              setInputValue(clampedValue.toFixed(1))
              // Ensure parent component gets the clamped value
              if (clampedValue !== value) {
                onChange(clampedValue)
              }
            }
          }}
          disabled={disabled}
          className="w-32 text-center text-lg font-mono pr-8"
          placeholder="50.0"
        />
        <span className="absolute right-3 top-1/2 transform -translate-y-1/2 text-muted-foreground">
          %
        </span>
      </div>
      
      <div className="flex gap-2">
        <Button
          variant="outline"
          size="sm"
          onClick={() => adjustValue(-1)}
          disabled={disabled}
        >
          -1%
        </Button>
        <Button
          variant="outline"
          size="sm"
          onClick={() => adjustValue(-0.1)}
          disabled={disabled}
        >
          <ChevronDown className="h-4 w-4" />
        </Button>
        <Button
          variant="outline"
          size="sm"
          onClick={() => adjustValue(0.1)}
          disabled={disabled}
        >
          <ChevronUp className="h-4 w-4" />
        </Button>
        <Button
          variant="outline"
          size="sm"
          onClick={() => adjustValue(1)}
          disabled={disabled}
        >
          +1%
        </Button>
      </div>
      
      <Button
        size="lg"
        onClick={onSubmit}
        disabled={disabled}
        className="px-8"
      >
        Submit Guess
      </Button>
      
      <div className="text-xs text-muted-foreground text-center">
        Arrow keys: ±1% | Scroll wheel: ±1% (hover over input) | Buttons: fine control<br />
        Press Enter to submit
      </div>
    </div>
  )
}