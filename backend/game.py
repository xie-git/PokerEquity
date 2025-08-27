import random
import json
import hashlib
from datetime import datetime, timezone
from typing import List, Dict, Optional, Tuple
from pydantic import BaseModel
from sqlalchemy.orm import Session
from .models import Question, Answer, get_db
from .equity import calculate_equity, get_canonical_key
from .services import equity_cache
from .config import config

class QuestionData(BaseModel):
    id: str
    street: str
    hero: str
    villain: str
    board: List[str]
    tags: List[str]

class GradeRequest(BaseModel):
    id: str
    guess_equity_hero: float
    elapsed_ms: int
    device_id: Optional[str] = None

class GradeResponse(BaseModel):
    truth: float
    delta: float
    score: int
    streak: int
    source: str
    explain: List[str]

class StatsResponse(BaseModel):
    games_played: int
    avg_delta: float
    perfects: int
    close_rate: float
    by_street: Dict[str, Dict[str, float]]

# Street distribution weights
STREET_WEIGHTS = {
    "flop": 0.35,
    "turn": 0.30, 
    "river": 0.25,
    "pre": 0.10
}

def generate_cards() -> Tuple[str, str, List[str], str, List[str]]:
    """Generate random poker hands and board."""
    # Full deck
    ranks = '23456789TJQKA'
    suits = 'cdhs'
    deck = [rank + suit for rank in ranks for suit in suits]
    
    # Sample street based on weights
    street = random.choices(list(STREET_WEIGHTS.keys()), 
                           weights=list(STREET_WEIGHTS.values()))[0]
    
    # Determine board size
    board_sizes = {"pre": 0, "flop": 3, "turn": 4, "river": 5}
    board_size = board_sizes[street]
    
    # Deal cards
    dealt = random.sample(deck, 4 + board_size)
    hero = dealt[0] + dealt[1]
    villain = dealt[2] + dealt[3]
    board = dealt[4:4 + board_size] if board_size > 0 else []
    
    # Generate texture tags
    tags = generate_texture_tags(board)
    
    return hero, villain, board, street, tags

def generate_texture_tags(board: List[str]) -> List[str]:
    """Generate texture tags for the board."""
    if len(board) < 3:
        return []
    
    tags = []
    
    # Extract suits and ranks
    suits = [card[1] for card in board]
    ranks = [card[0] for card in board]
    
    # Suit analysis
    suit_counts = {}
    for suit in suits:
        suit_counts[suit] = suit_counts.get(suit, 0) + 1
    
    max_suit_count = max(suit_counts.values()) if suit_counts else 0
    
    if max_suit_count >= 3:
        tags.append("monotone")
    elif max_suit_count == 2:
        tags.append("two_tone")
    
    # Pair analysis
    rank_counts = {}
    for rank in ranks:
        rank_counts[rank] = rank_counts.get(rank, 0) + 1
    
    if 2 in rank_counts.values():
        tags.append("paired")
    
    # Connectivity analysis (simplified)
    rank_values = {'2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, 
                   '9': 9, 'T': 10, 'J': 11, 'Q': 12, 'K': 13, 'A': 14}
    values = sorted([rank_values.get(r, 0) for r in ranks])
    
    # Check for connectivity (within 4 ranks)
    if len(values) >= 3 and values[-1] - values[0] <= 4:
        tags.append("connected")
    
    return tags

def calculate_score(delta: float) -> int:
    """Calculate score based on accuracy."""
    if delta <= 0.5:
        return 100
    elif delta <= 1.0:
        return 85
    elif delta <= 2.5:
        return 70
    else:
        return max(0, int(70 - (delta - 2.5) * 12))

def get_player_streak(device_id: Optional[str], db: Session) -> int:
    """Get current streak of close guesses (≤1.0% error)."""
    if not device_id:
        return 0
    
    # Get last 20 answers to check streak
    recent_answers = (db.query(Answer)
                     .filter(Answer.device_id == device_id)
                     .order_by(Answer.created_at.desc())
                     .limit(20)
                     .all())
    
    streak = 0
    for answer in recent_answers:
        if answer.delta <= 1.0:
            streak += 1
        else:
            break
    
    return min(streak, 10)  # Cap at 10 for +50% bonus

def generate_explanation(hero: str, villain: str, board: List[str], street: str) -> List[str]:
    """Generate simple explanation bullets."""
    explanations = []
    
    # Basic explanations based on street
    if street == "river":
        explanations.append("All cards dealt - equity is 0% or 100%")
        explanations.append("Compare final 5-card hands directly")
    elif street == "turn":
        explanations.append("One card to come - count outs and blockers")
        explanations.append("Each out is roughly 2% equity")
    elif street == "flop":
        explanations.append("Two cards to come - multiply outs by 4% rule")
        explanations.append("Consider both turn and river possibilities")
    else:  # preflop
        explanations.append("No community cards - hand strength matters most")
        explanations.append("Position and post-flop playability also important")
    
    return explanations

def generate_question_id() -> str:
    """Generate unique question ID with timestamp."""
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    random_suffix = f"{random.randint(10000, 99999)}"
    return f"Q_{timestamp}_{random_suffix}"

async def create_question(db: Session, mode: str = "drill") -> QuestionData:
    """Create a new question and persist to database."""
    hero, villain, board, street, tags = generate_cards()
    question_id = generate_question_id()
    
    # Check cache first
    cache_key = get_canonical_key(hero, villain, board)
    cached_result = equity_cache.get(cache_key)
    
    if cached_result:
        truth, source = cached_result
    else:
        # Calculate equity and cache
        truth, source = calculate_equity(hero, villain, board, question_id=question_id)
        equity_cache.set(cache_key, (truth, source))
    
    # Save to database
    question = Question(
        id=question_id,
        street=street,
        hero=hero,
        villain=villain,
        board=json.dumps(board),
        truth=truth,
        source=source,
        tags=json.dumps(tags)
    )
    db.add(question)
    db.commit()
    
    return QuestionData(
        id=question_id,
        street=street,
        hero=hero,
        villain=villain,
        board=board,
        tags=tags
    )

async def grade_answer(request: GradeRequest, db: Session) -> GradeResponse:
    """Grade a player's equity guess."""
    # Clamp guess to valid range
    guess = max(0.0, min(100.0, request.guess_equity_hero))
    
    # Get question from database
    question = db.query(Question).filter(Question.id == request.id).first()
    if not question:
        raise ValueError("Question not found")
    
    truth = question.truth
    delta = abs(guess - truth)
    base_score = calculate_score(delta)
    
    # Calculate streak bonus
    streak = get_player_streak(request.device_id, db)
    streak_multiplier = 1.0 + min(streak * 0.05, 0.50)  # Max 50% bonus
    final_score = int(base_score * streak_multiplier)
    
    # Save answer
    answer = Answer(
        question_id=request.id,
        device_id=request.device_id,
        guess=guess,
        truth=truth,
        delta=delta,
        score=final_score,
        elapsed_ms=request.elapsed_ms,
        mode="drill"  # TODO: support daily mode
    )
    db.add(answer)
    db.commit()
    
    # Generate explanation
    board = json.loads(question.board) if question.board else []
    explain = generate_explanation(question.hero, question.villain, board, question.street)
    
    return GradeResponse(
        truth=round(truth, 1),
        delta=round(delta, 1),
        score=final_score,
        streak=streak,
        source=question.source,
        explain=explain
    )

async def get_daily_questions(device_id: str, date_str: str, db: Session) -> List[QuestionData]:
    """Get deterministic daily questions for a device and date."""
    seed_string = f"{date_str}_{device_id}_{config.RNG_SEED_SALT}"
    seed = int(hashlib.md5(seed_string.encode()).hexdigest()[:8], 16)
    random.seed(seed)
    
    questions = []
    for i in range(config.DAILY_SIZE):
        # Generate deterministic question
        hero, villain, board, street, tags = generate_cards()
        question_id = f"DAILY_{date_str}_{device_id}_{i:02d}"
        
        # Check if already exists
        existing = db.query(Question).filter(Question.id == question_id).first()
        if existing:
            questions.append(QuestionData(
                id=existing.id,
                street=existing.street,
                hero=existing.hero,
                villain=existing.villain,
                board=json.loads(existing.board) if existing.board else [],
                tags=json.loads(existing.tags) if existing.tags else []
            ))
            continue
        
        # Calculate and cache equity
        cache_key = get_canonical_key(hero, villain, board)
        cached_result = equity_cache.get(cache_key)
        
        if cached_result:
            truth, source = cached_result
        else:
            truth, source = calculate_equity(hero, villain, board, question_id=question_id)
            equity_cache.set(cache_key, (truth, source))
        
        # Save to database
        question = Question(
            id=question_id,
            street=street,
            hero=hero,
            villain=villain,
            board=json.dumps(board),
            truth=truth,
            source=source,
            tags=json.dumps(tags)
        )
        db.add(question)
        
        questions.append(QuestionData(
            id=question_id,
            street=street,
            hero=hero,
            villain=villain,
            board=board,
            tags=tags
        ))
    
    db.commit()
    return questions

async def get_player_stats(device_id: str, db: Session) -> StatsResponse:
    """Get player statistics."""
    answers = (db.query(Answer)
              .filter(Answer.device_id == device_id)
              .all())
    
    if not answers:
        return StatsResponse(
            games_played=0,
            avg_delta=0.0,
            perfects=0,
            close_rate=0.0,
            by_street={}
        )
    
    total_delta = sum(a.delta for a in answers)
    perfects = sum(1 for a in answers if a.delta <= 0.5)
    close = sum(1 for a in answers if a.delta <= 1.0)
    
    # By street analysis
    by_street = {}
    for answer in answers:
        question = answer.question
        street = question.street
        if street not in by_street:
            by_street[street] = {"attempts": 0, "total_delta": 0.0}
        by_street[street]["attempts"] += 1
        by_street[street]["total_delta"] += answer.delta
    
    # Calculate averages
    for street_data in by_street.values():
        street_data["avg_delta"] = street_data["total_delta"] / street_data["attempts"]
        del street_data["total_delta"]
    
    return StatsResponse(
        games_played=len(answers),
        avg_delta=round(total_delta / len(answers), 1),
        perfects=perfects,
        close_rate=round(close / len(answers), 2),
        by_street=by_street
    )