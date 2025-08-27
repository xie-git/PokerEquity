import eval7
import random
import itertools
from typing import List, Tuple, Set
import hashlib
import json
from .config import config

def parse_card(card_str: str) -> eval7.Card:
    """Convert string like 'AsKd' to eval7.Card objects."""
    return eval7.Card(card_str)

def parse_cards(cards: List[str]) -> List[eval7.Card]:
    """Convert list of card strings to eval7.Card objects."""
    return [parse_card(card) for card in cards]

def cards_to_string(cards: List[eval7.Card]) -> List[str]:
    """Convert eval7.Card objects back to strings."""
    return [str(card) for card in cards]

def get_remaining_deck(used_cards: List[eval7.Card]) -> List[eval7.Card]:
    """Get remaining cards from deck after removing used cards."""
    all_cards = [eval7.Card(rank + suit) 
                for rank in '23456789TJQKA' 
                for suit in 'cdhs']
    used_set = set(used_cards)
    return [card for card in all_cards if card not in used_set]

def evaluate_hand(cards: List[eval7.Card]) -> int:
    """Evaluate 5-card hand using eval7. Higher is better."""
    return eval7.evaluate(cards)

def calculate_equity_exact(hero_cards: List[eval7.Card], 
                          villain_cards: List[eval7.Card],
                          board: List[eval7.Card]) -> Tuple[float, str]:
    """Calculate exact equity using enumeration."""
    used_cards = hero_cards + villain_cards + board
    remaining = get_remaining_deck(used_cards)
    
    cards_needed = 5 - len(board)
    
    if cards_needed == 0:
        # River - direct comparison
        hero_hand = evaluate_hand(hero_cards + board)
        villain_hand = evaluate_hand(villain_cards + board)
        
        if hero_hand > villain_hand:
            return 100.0, "exact"
        elif hero_hand < villain_hand:
            return 0.0, "exact"
        else:
            return 50.0, "exact"
    
    wins = ties = total = 0
    
    if cards_needed == 1:
        # Turn - iterate 46 possible rivers
        for river in remaining:
            complete_board = board + [river]
            hero_hand = evaluate_hand(hero_cards + complete_board)
            villain_hand = evaluate_hand(villain_cards + complete_board)
            
            if hero_hand > villain_hand:
                wins += 1
            elif hero_hand == villain_hand:
                ties += 1
            total += 1
    
    elif cards_needed == 2:
        # Flop - iterate C(47,2) = 1081 turn+river pairs
        for turn, river in itertools.combinations(remaining, 2):
            complete_board = board + [turn, river]
            hero_hand = evaluate_hand(hero_cards + complete_board)
            villain_hand = evaluate_hand(villain_cards + complete_board)
            
            if hero_hand > villain_hand:
                wins += 1
            elif hero_hand == villain_hand:
                ties += 1
            total += 1
    
    else:
        # Should not happen in this game
        raise ValueError(f"Unexpected cards_needed: {cards_needed}")
    
    equity = (wins + 0.5 * ties) / total * 100
    return equity, "exact"

def calculate_equity_monte_carlo(hero_cards: List[eval7.Card], 
                               villain_cards: List[eval7.Card],
                               board: List[eval7.Card],
                               iterations: int,
                               seed: int) -> Tuple[float, str]:
    """Calculate equity using Monte Carlo simulation."""
    used_cards = hero_cards + villain_cards + board
    remaining = get_remaining_deck(used_cards)
    cards_needed = 5 - len(board)
    
    random.seed(seed)
    wins = ties = 0
    
    for _ in range(iterations):
        # Deal random completion
        completion = random.sample(remaining, cards_needed)
        complete_board = board + completion
        
        hero_hand = evaluate_hand(hero_cards + complete_board)
        villain_hand = evaluate_hand(villain_cards + complete_board)
        
        if hero_hand > villain_hand:
            wins += 1
        elif hero_hand == villain_hand:
            ties += 1
    
    equity = (wins + 0.5 * ties) / iterations * 100
    return equity, f"mc:{iterations}"

def get_canonical_key(hero: str, villain: str, board: List[str]) -> str:
    """Generate canonical cache key for equity calculation."""
    # Sort hands and board for consistent caching regardless of suit randomization
    data = {
        'hero': hero,
        'villain': villain,
        'board': sorted(board) if board else []
    }
    return hashlib.md5(json.dumps(data, sort_keys=True).encode()).hexdigest()

def calculate_equity(hero: str, villain: str, board: List[str], 
                    exact: bool = None, question_id: str = None) -> Tuple[float, str]:
    """
    Main equity calculation function.
    
    Args:
        hero: Hero hand string (e.g., "AsKd")
        villain: Villain hand string (e.g., "QhJh") 
        board: List of board cards (e.g., ["Ah", "Ts", "2c"])
        exact: Force exact calculation (for debugging)
        question_id: Used for seeding MC simulation
    
    Returns:
        (equity_percentage, source_string)
    """
    try:
        hero_cards = [parse_card(hero[:2]), parse_card(hero[2:])]
        villain_cards = [parse_card(villain[:2]), parse_card(villain[2:])]
        board_cards = parse_cards(board) if board else []
        
        # Map board size to street name
        board_size_to_street = {0: "pre", 3: "flop", 4: "turn", 5: "river"}
        street_name = board_size_to_street.get(len(board_cards), "unknown")
        
        # Use exact calculation for flop/turn/river (unless overridden)
        if exact is None:
            exact = street_name != "pre"
        
        if exact and street_name != "pre":
            return calculate_equity_exact(hero_cards, villain_cards, board_cards)
        else:
            # Monte Carlo for preflop (or when forced)
            seed = int(hashlib.md5((question_id or "default" + config.RNG_SEED_SALT).encode()).hexdigest()[:8], 16)
            return calculate_equity_monte_carlo(hero_cards, villain_cards, board_cards, 
                                              config.PREFLOP_MC, seed)
                                              
    except Exception as e:
        raise ValueError(f"Equity calculation failed: {str(e)}")