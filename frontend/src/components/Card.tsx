import { Card as CardType } from '../lib/types'

interface CardProps {
  rank: string
  suit: string
  size?: 'sm' | 'md' | 'lg'
}

const suitSymbols = {
  'c': '♣',
  'd': '♦',
  'h': '♥',
  's': '♠'
} as const

const suitColors = {
  'c': 'text-black',
  'd': 'text-red-600',
  'h': 'text-red-600',
  's': 'text-black'
} as const

const sizes = {
  sm: 'w-12 h-16 text-sm',
  md: 'w-16 h-20 text-base',
  lg: 'w-20 h-28 text-lg'
}

export function Card({ rank, suit, size = 'md' }: CardProps) {
  const suitSymbol = suitSymbols[suit as keyof typeof suitSymbols] || suit
  const suitColor = suitColors[suit as keyof typeof suitColors] || 'text-black'
  
  return (
    <div className={`
      ${sizes[size]}
      bg-white border border-gray-300 rounded-lg shadow-sm
      flex flex-col items-center justify-center
      poker-card card-shadow
      relative
    `}>
      {/* Top left */}
      <div className="absolute top-1 left-1 flex flex-col items-center leading-none">
        <span className={`font-bold ${suitColor}`}>{rank}</span>
        <span className={`text-xs ${suitColor}`}>{suitSymbol}</span>
      </div>
      
      {/* Center suit */}
      <div className={`${suitColor} text-2xl font-bold`}>
        {suitSymbol}
      </div>
      
      {/* Bottom right (rotated) */}
      <div className="absolute bottom-1 right-1 flex flex-col items-center leading-none rotate-180">
        <span className={`font-bold ${suitColor}`}>{rank}</span>
        <span className={`text-xs ${suitColor}`}>{suitSymbol}</span>
      </div>
    </div>
  )
}

interface HandProps {
  cards: [CardType, CardType]
  label?: string
  size?: 'sm' | 'md' | 'lg'
}

export function Hand({ cards, label, size = 'md' }: HandProps) {
  return (
    <div className="flex flex-col items-center gap-2">
      {label && (
        <h3 className="text-sm font-medium text-muted-foreground">{label}</h3>
      )}
      <div className="flex gap-1">
        <Card rank={cards[0].rank} suit={cards[0].suit} size={size} />
        <Card rank={cards[1].rank} suit={cards[1].suit} size={size} />
      </div>
    </div>
  )
}

interface BoardProps {
  cards: CardType[]
  street: string
  size?: 'sm' | 'md' | 'lg'
}

export function Board({ cards, street, size = 'md' }: BoardProps) {
  const emptySlots = 5 - cards.length
  
  return (
    <div className="flex flex-col items-center gap-2">
      <h3 className="text-sm font-medium text-muted-foreground">
        Board ({street})
      </h3>
      <div className="flex gap-1">
        {cards.map((card, index) => (
          <Card key={index} rank={card.rank} suit={card.suit} size={size} />
        ))}
        {Array.from({ length: emptySlots }).map((_, index) => (
          <div 
            key={`empty-${index}`} 
            className={`
              ${sizes[size]}
              border-2 border-dashed border-gray-300 rounded-lg
              flex items-center justify-center
              text-gray-400 text-xs
            `}
          >
            ?
          </div>
        ))}
      </div>
    </div>
  )
}