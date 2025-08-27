from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.sql import func
import os
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
    device_id = Column(String, nullable=True)
    guess = Column(Float, nullable=False)
    truth = Column(Float, nullable=False)
    delta = Column(Float, nullable=False)
    score = Column(Integer, nullable=False)
    elapsed_ms = Column(Integer, nullable=False)
    mode = Column(String, nullable=False)  # "drill" or "daily"
    created_at = Column(DateTime, server_default=func.now())
    
    question = relationship("Question", back_populates="answers")

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