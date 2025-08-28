import eval7
import random
import itertools
from typing import List, Tuple, Set, Optional
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

# Range filtering functions for realistic opponent modeling
def get_hand_rank_value(rank: str) -> int:
    """Convert card rank to numeric value for comparisons."""
    rank_values = {'2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, 
                   '9': 9, 'T': 10, 'J': 11, 'Q': 12, 'K': 13, 'A': 14}
    return rank_values.get(rank, 0)

def classify_preflop_hand(card1: eval7.Card, card2: eval7.Card) -> Tuple[str, int]:
    """Classify a preflop hand and return (hand_type, strength_score)."""
    rank1, suit1 = str(card1)[0], str(card1)[1]
    rank2, suit2 = str(card2)[0], str(card2)[1]
    
    val1, val2 = get_hand_rank_value(rank1), get_hand_rank_value(rank2)
    high_rank, low_rank = max(val1, val2), min(val1, val2)
    is_suited = suit1 == suit2
    is_pair = val1 == val2
    
    # Classify hand type and assign strength score (0-100)
    if is_pair:
        # Pocket pairs: AA=100, KK=95, QQ=90, etc.
        strength = min(100, 50 + (high_rank - 2) * 4)
        return f"{rank1 if val1 == high_rank else rank2}{rank1 if val1 == high_rank else rank2}", strength
    
    # High card hands
    high_char = [r for r, v in [('2', 2), ('3', 3), ('4', 4), ('5', 5), ('6', 6), ('7', 7), 
                               ('8', 8), ('9', 9), ('T', 10), ('J', 11), ('Q', 12), ('K', 13), ('A', 14)] if v == high_rank][0]
    low_char = [r for r, v in [('2', 2), ('3', 3), ('4', 4), ('5', 5), ('6', 6), ('7', 7), 
                              ('8', 8), ('9', 9), ('T', 10), ('J', 11), ('Q', 12), ('K', 13), ('A', 14)] if v == low_rank][0]
    
    # Base strength from high card
    strength = high_rank * 3
    
    # Bonus for kicker
    strength += low_rank * 1.5
    
    # Bonus for suited
    if is_suited:
        strength += 8
        hand_str = f"{high_char}{low_char}s"
    else:
        hand_str = f"{high_char}{low_char}o"
    
    # Bonus for connected cards
    gap = abs(high_rank - low_rank)
    if gap == 0:  # pair, already handled
        pass
    elif gap == 1:  # connected
        strength += 5
    elif gap == 2:  # one gap
        strength += 3
    elif gap == 3:  # two gap  
        strength += 1
    
    return hand_str, min(100, int(strength))

def get_preflop_range_threshold(opponent_type: str, street: str) -> int:
    """Get the minimum hand strength for different opponent types and positions."""
    thresholds = {
        'tight': {
            'pre': 70,  # Top ~15% of hands
            'flop': 60,
            'turn': 70, 
            'river': 75
        },
        'balanced': {
            'pre': 55,  # Top ~25% of hands
            'flop': 45,
            'turn': 55,
            'river': 60
        },
        'loose': {
            'pre': 35,  # Top ~40% of hands
            'flop': 30,
            'turn': 40,
            'river': 45
        },
        'random': {
            'pre': 0,   # All hands (current behavior)
            'flop': 0,
            'turn': 0,
            'river': 0
        }
    }
    
    return thresholds.get(opponent_type, thresholds['balanced']).get(street, 50)

def has_pair_or_better(hand: List[eval7.Card], board: List[eval7.Card]) -> bool:
    """Check if hand makes at least a pair with the board."""
    if not board:
        return False
        
    hand_ranks = set(str(card)[0] for card in hand)
    board_ranks = set(str(card)[0] for card in board)
    
    # Pocket pair
    if len(hand_ranks) == 1:
        return True
        
    # Pair with board
    if hand_ranks & board_ranks:
        return True
        
    return False

def has_draw(hand: List[eval7.Card], board: List[eval7.Card]) -> bool:
    """Check if hand has a decent draw (flush draw or open-ended straight draw)."""
    if len(board) < 3:
        return False
    
    all_cards = hand + board
    
    # Check flush draw (4 to a flush)
    suits = {}
    for card in all_cards:
        suit = str(card)[1]
        suits[suit] = suits.get(suit, 0) + 1
        if suits[suit] >= 4:
            return True
    
    # Check straight draw (simplified - look for 4 in a row)
    ranks = [get_hand_rank_value(str(card)[0]) for card in all_cards]
    ranks = sorted(set(ranks))
    
    for i in range(len(ranks) - 3):
        if ranks[i+3] - ranks[i] == 3:  # 4 in a row
            return True
    
    # Check for A-low straight draw
    if 14 in ranks and 2 in ranks and 3 in ranks and 4 in ranks:
        return True
        
    return False

def filter_villain_range(remaining_deck: List[eval7.Card], 
                        board: List[eval7.Card], 
                        street: str,
                        opponent_type: str = 'balanced') -> List[Tuple[eval7.Card, eval7.Card]]:
    """Filter villain's possible hands based on street and opponent type."""
    
    if opponent_type == 'random':
        # Return all possible hands (current behavior)
        return list(itertools.combinations(remaining_deck, 2))
    
    valid_hands = []
    threshold = get_preflop_range_threshold(opponent_type, street)
    
    for card1, card2 in itertools.combinations(remaining_deck, 2):
        if street == 'pre':
            # Preflop: filter by hand strength
            _, strength = classify_preflop_hand(card1, card2)
            if strength >= threshold:
                valid_hands.append((card1, card2))
        else:
            # Postflop: more complex logic
            hand = [card1, card2]
            
            # Always include strong hands (pair or better)
            if has_pair_or_better(hand, board):
                valid_hands.append((card1, card2))
                continue
            
            # Include draws on flop and turn
            if street in ['flop', 'turn'] and has_draw(hand, board):
                valid_hands.append((card1, card2))
                continue
                
            # Include some bluffs and overcards based on opponent type
            if street != 'river':  # No random bluffs on river
                hand_ranks = [get_hand_rank_value(str(card)[0]) for card in hand]
                board_ranks = [get_hand_rank_value(str(card)[0]) for card in board]
                max_hand_rank = max(hand_ranks)
                max_board_rank = max(board_ranks) if board_ranks else 0
                
                # Overcards to board
                if max_hand_rank > max_board_rank:
                    if opponent_type == 'loose' or (opponent_type == 'balanced' and max_hand_rank >= 11):  # J+
                        valid_hands.append((card1, card2))
    
    # Ensure we don't filter too aggressively - keep at least 20% of hands
    min_hands = len(list(itertools.combinations(remaining_deck, 2))) * 0.2
    if len(valid_hands) < min_hands:
        # Fall back to top X hands by preflop strength
        all_hands = []
        for card1, card2 in itertools.combinations(remaining_deck, 2):
            _, strength = classify_preflop_hand(card1, card2)
            all_hands.append(((card1, card2), strength))
        
        all_hands.sort(key=lambda x: x[1], reverse=True)
        valid_hands = [hand for hand, _ in all_hands[:int(min_hands)]]
    
    return valid_hands

def calculate_range_equity(hero: str, board: List[str], 
                          opponent_type: str = 'balanced',
                          exact: bool = None, question_id: str = None) -> Tuple[float, str]:
    """
    Calculate equity against villain's filtered range based on opponent type.
    
    Args:
        hero: Hero hand string (e.g., "AsKd")
        board: List of board cards (e.g., ["Ah", "Ts", "2c"])
        opponent_type: Type of opponent ('tight', 'balanced', 'loose', 'random')
        exact: Force exact calculation (for debugging)
        question_id: Used for seeding MC simulation
    
    Returns:
        (equity_percentage, source_string)
    """
    try:
        hero_cards = [parse_card(hero[:2]), parse_card(hero[2:])]
        board_cards = parse_cards(board) if board else []
        
        # Get all remaining cards for villain range
        used_cards = hero_cards + board_cards
        remaining = get_remaining_deck(used_cards)
        
        # Map board size to street name
        board_size_to_street = {0: "pre", 3: "flop", 4: "turn", 5: "river"}
        street_name = board_size_to_street.get(len(board_cards), "unknown")
        
        # Filter villain's range based on opponent type and street
        filtered_villain_hands = filter_villain_range(remaining, board_cards, street_name, opponent_type)
        
        # Use exact calculation for river, Monte Carlo for earlier streets
        if exact is None:
            exact = street_name == "river" and len(filtered_villain_hands) < 500
        
        if exact and street_name == "river":
            return calculate_filtered_range_equity_exact(hero_cards, board_cards, filtered_villain_hands, opponent_type)
        else:
            # Monte Carlo for earlier streets or large ranges
            seed = int(hashlib.md5((question_id or "default" + config.RNG_SEED_SALT).encode()).hexdigest()[:8], 16)
            iterations = min(10000, len(filtered_villain_hands))
            return calculate_filtered_range_equity_monte_carlo(hero_cards, board_cards, filtered_villain_hands, iterations, seed, opponent_type)
                                              
    except Exception as e:
        raise ValueError(f"Range equity calculation failed: {str(e)}")

def calculate_filtered_range_equity_exact(hero_cards: List[eval7.Card], 
                                         board_cards: List[eval7.Card],
                                         filtered_hands: List[Tuple[eval7.Card, eval7.Card]],
                                         opponent_type: str) -> Tuple[float, str]:
    """Calculate exact range equity against filtered villain hands."""
    if len(board_cards) != 5:
        raise ValueError("Exact range equity only supported on river (5 board cards)")
    
    wins = ties = total = 0
    hero_hand_value = evaluate_hand(hero_cards + board_cards)
    
    # Enumerate filtered villain hands only
    for villain_card1, villain_card2 in filtered_hands:
        villain_cards = [villain_card1, villain_card2]
        villain_hand_value = evaluate_hand(villain_cards + board_cards)
        
        if hero_hand_value > villain_hand_value:
            wins += 1
        elif hero_hand_value == villain_hand_value:
            ties += 1
        total += 1
    
    if total == 0:
        return 50.0, f"range_{opponent_type}_exact"
    
    equity = (wins + 0.5 * ties) / total * 100
    return equity, f"range_{opponent_type}_exact"

def calculate_range_equity_exact(hero_cards: List[eval7.Card], 
                                board_cards: List[eval7.Card],
                                remaining_deck: List[eval7.Card]) -> Tuple[float, str]:
    """Calculate exact range equity by enumerating all villain hands."""
    if len(board_cards) != 5:
        raise ValueError("Exact range equity only supported on river (5 board cards)")
    
    wins = ties = total = 0
    hero_hand_value = evaluate_hand(hero_cards + board_cards)
    
    # Enumerate all possible villain 2-card combinations
    import itertools
    for villain_card1, villain_card2 in itertools.combinations(remaining_deck, 2):
        villain_cards = [villain_card1, villain_card2]
        villain_hand_value = evaluate_hand(villain_cards + board_cards)
        
        if hero_hand_value > villain_hand_value:
            wins += 1
        elif hero_hand_value == villain_hand_value:
            ties += 1
        total += 1
    
    equity = (wins + 0.5 * ties) / total * 100
    return equity, "range_exact"

def calculate_filtered_range_equity_monte_carlo(hero_cards: List[eval7.Card],
                                               board_cards: List[eval7.Card], 
                                               filtered_hands: List[Tuple[eval7.Card, eval7.Card]],
                                               iterations: int,
                                               seed: int,
                                               opponent_type: str) -> Tuple[float, str]:
    """Calculate range equity using Monte Carlo sampling from filtered hands."""
    random.seed(seed)
    wins = ties = 0
    cards_needed = 5 - len(board_cards)
    
    # Get remaining deck excluding hero cards and board
    all_cards = [eval7.Card(rank + suit) for rank in '23456789TJQKA' for suit in 'cdhs']
    used_cards = set(hero_cards + board_cards)
    available_for_completion = [card for card in all_cards if card not in used_cards]
    
    if not filtered_hands:
        return 50.0, f"range_{opponent_type}_mc:{iterations}"
    
    for _ in range(min(iterations, len(filtered_hands) * 10)):  # Reasonable upper limit
        # Sample random villain hand from filtered range
        villain_cards = list(random.choice(filtered_hands))
        
        # Deal remaining board cards if needed
        if cards_needed > 0:
            # Remove villain cards from available completion cards
            completion_available = [card for card in available_for_completion if card not in villain_cards]
            if len(completion_available) >= cards_needed:
                board_completion = random.sample(completion_available, cards_needed)
                complete_board = board_cards + board_completion
            else:
                continue  # Skip if not enough cards available
        else:
            complete_board = board_cards
        
        # Compare hands
        hero_hand_value = evaluate_hand(hero_cards + complete_board)
        villain_hand_value = evaluate_hand(villain_cards + complete_board)
        
        if hero_hand_value > villain_hand_value:
            wins += 1
        elif hero_hand_value == villain_hand_value:
            ties += 1
    
    total_simulations = wins + ties + (min(iterations, len(filtered_hands) * 10) - wins - ties)
    if total_simulations == 0:
        return 50.0, f"range_{opponent_type}_mc:{iterations}"
    
    equity = (wins + 0.5 * ties) / total_simulations * 100
    return equity, f"range_{opponent_type}_mc:{total_simulations}"

def calculate_range_equity_monte_carlo(hero_cards: List[eval7.Card],
                                     board_cards: List[eval7.Card], 
                                     remaining_deck: List[eval7.Card],
                                     iterations: int,
                                     seed: int) -> Tuple[float, str]:
    """Calculate range equity using Monte Carlo sampling."""
    random.seed(seed)
    wins = ties = 0
    cards_needed = 5 - len(board_cards)
    
    for _ in range(iterations):
        # Sample random villain hand and board completion
        available = remaining_deck.copy()
        
        # Deal 2 cards to villain
        villain_cards = random.sample(available, 2)
        available = [card for card in available if card not in villain_cards]
        
        # Deal remaining board cards if needed
        if cards_needed > 0:
            board_completion = random.sample(available, cards_needed)
            complete_board = board_cards + board_completion
        else:
            complete_board = board_cards
        
        # Compare hands
        hero_hand_value = evaluate_hand(hero_cards + complete_board)
        villain_hand_value = evaluate_hand(villain_cards + complete_board)
        
        if hero_hand_value > villain_hand_value:
            wins += 1
        elif hero_hand_value == villain_hand_value:
            ties += 1
    
    equity = (wins + 0.5 * ties) / iterations * 100
    return equity, f"range_mc:{iterations}"

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