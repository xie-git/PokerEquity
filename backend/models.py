from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, create_engine, text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.sql import func
import os
import uuid
from .config import config

Base = declarative_base()

class Question(Base):
    __tablename__ = "questions"
    
    id = Column(String, primary_key=True)
    street = Column(String, nullable=False)  # pre, flop, turn, river
    hero = Column(String, nullable=False)    # AsKd
    villain = Column(String, nullable=False) # QhJh
    board = Column(Text, nullable=True)      # JSON array: ["Ah","Ts","2c","9h"]
    truth = Column(Float, nullable=False)    # Precomputed equity
    source = Column(String, nullable=False)  # "exact" or "mc:200000"
    tags = Column(Text, nullable=True)       # JSON array: ["two_tone","connected"]
    created_at = Column(DateTime, server_default=func.now())
    
    answers = relationship("Answer", back_populates="question")

class Answer(Base):
    __tablename__ = "answers"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    question_id = Column(String, ForeignKey("questions.id"), nullable=False)
    machine_id = Column(String, nullable=False)  # UUID for persistent tracking
    device_id = Column(String, nullable=True)    # Legacy field, kept for compatibility
    guess = Column(Float, nullable=False)
    truth = Column(Float, nullable=False)
    delta = Column(Float, nullable=False)
    score = Column(Integer, nullable=False)
    elapsed_ms = Column(Integer, nullable=False)  # Total decision time
    think_time_ms = Column(Integer, nullable=True)  # Time to first input
    mode = Column(String, nullable=False)  # "drill" or "daily"
    session_id = Column(String, nullable=True)  # For grouping hands in sessions
    created_at = Column(DateTime, server_default=func.now())
    
    question = relationship("Question", back_populates="answers")

class MachineStats(Base):
    __tablename__ = "machine_stats"
    
    machine_id = Column(String, primary_key=True)
    total_hands = Column(Integer, default=0)
    total_time_ms = Column(Integer, default=0)  # Total time spent playing
    avg_accuracy = Column(Float, default=0.0)  # Current rolling average
    best_accuracy = Column(Float, default=100.0)  # Best single-hand accuracy
    worst_accuracy = Column(Float, default=0.0)  # Worst single-hand accuracy  
    perfect_count = Column(Integer, default=0)  # Hands with <=0.5% error
    close_count = Column(Integer, default=0)    # Hands with <=1.0% error
    current_streak = Column(Integer, default=0) # Current streak of close guesses
    best_streak = Column(Integer, default=0)    # Best streak ever
    fastest_time_ms = Column(Integer, nullable=True)  # Fastest decision
    slowest_time_ms = Column(Integer, nullable=True)  # Slowest decision
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

class SessionStats(Base):
    __tablename__ = "session_stats"
    
    id = Column(String, primary_key=True)  # UUID
    machine_id = Column(String, nullable=False)
    started_at = Column(DateTime, server_default=func.now())
    ended_at = Column(DateTime, nullable=True)
    hands_played = Column(Integer, default=0)
    avg_accuracy = Column(Float, default=0.0)
    total_time_ms = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)

class PerformanceSnapshot(Base):
    __tablename__ = "performance_snapshots"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    machine_id = Column(String, nullable=False)
    date = Column(DateTime, server_default=func.now())
    hands_played_today = Column(Integer, default=0)
    avg_accuracy_today = Column(Float, default=0.0)
    avg_time_today_ms = Column(Integer, default=0)
    rolling_accuracy_50 = Column(Float, nullable=True)  # Last 50 hands
    rolling_accuracy_100 = Column(Float, nullable=True) # Last 100 hands
    rolling_accuracy_500 = Column(Float, nullable=True) # Last 500 hands
    street_performance = Column(Text, nullable=True)  # JSON: {pre: {avg_acc, avg_time}, ...}
    time_distribution = Column(Text, nullable=True)   # JSON: speed category distribution

# Database setup
def get_engine():
    # Ensure directory exists
    db_dir = os.path.dirname(config.DB_PATH)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir)
    
    engine = create_engine(f"sqlite:///{config.DB_PATH}")
    
    # SQLite optimizations
    with engine.connect() as conn:
        conn.execute(text("PRAGMA journal_mode=WAL"))
        conn.execute(text("PRAGMA synchronous=NORMAL"))
        conn.execute(text("PRAGMA temp_store=MEMORY"))
        conn.execute(text("PRAGMA mmap_size=268435456"))  # 256MB
    
    return engine

engine = get_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_or_create_machine_id(db: SessionLocal) -> str:
    """Get or create a persistent machine ID for lifetime stats tracking."""
    # Try to find existing machine stats (there should only be one per machine)
    machine_stat = db.query(MachineStats).first()
    
    if machine_stat:
        return machine_stat.machine_id
    
    # Create new machine ID
    machine_id = str(uuid.uuid4())
    new_machine_stat = MachineStats(machine_id=machine_id)
    db.add(new_machine_stat)
    db.commit()
    
    return machine_id

def get_or_create_session(machine_id: str, db: SessionLocal) -> str:
    """Get current active session or create a new one."""
    # Find active session
    active_session = (db.query(SessionStats)
                     .filter(SessionStats.machine_id == machine_id)
                     .filter(SessionStats.is_active == True)
                     .first())
    
    if active_session:
        return active_session.id
    
    # Create new session
    session_id = str(uuid.uuid4())
    new_session = SessionStats(
        id=session_id,
        machine_id=machine_id,
        is_active=True
    )
    db.add(new_session)
    db.commit()
    
    return session_id