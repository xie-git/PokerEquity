from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
import logging
import os
from datetime import datetime, timezone
from typing import List

from .models import init_db, get_db
from .game import (
    QuestionData, GradeRequest, GradeResponse, StatsResponse, EnhancedStatsResponse,
    create_question, grade_answer, get_daily_questions, get_player_stats, get_enhanced_player_stats
)
from .services import timed_endpoint, metrics
from .config import config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Poker Equity Trainer API",
    description="API for heads-up poker equity training game",
    version="1.0.0"
)

# Initialize database
init_db()

# Health check endpoint
@app.get("/healthz")
async def health_check():
    """Health check endpoint for monitoring."""
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "cache_size": metrics.request_times.__len__() if hasattr(metrics, 'request_times') else 0
    }

# Metrics endpoint
@app.get("/api/metrics")
async def get_metrics():
    """Get basic performance metrics."""
    return {
        "request_stats": metrics.get_stats(),
        "app_env": config.APP_ENV,
        "preflop_mc": config.PREFLOP_MC
    }

# Deal a new question
@app.post("/api/deal", response_model=QuestionData)
@timed_endpoint("deal")
async def deal_question(mode: str = "drill", opponent_type: str = "balanced", db: Session = Depends(get_db)):
    """Generate a new random poker question."""
    try:
        question = await create_question(db, mode, opponent_type)
        return question
    except Exception as e:
        logger.error(f"Error dealing question: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate question")

# Grade an answer
@app.post("/api/grade", response_model=GradeResponse)
@timed_endpoint("grade")
async def grade_question(request: GradeRequest, db: Session = Depends(get_db)):
    """Grade a player's equity guess."""
    try:
        # Validate input
        if not (0 <= request.guess_equity_hero <= 100):
            raise ValueError("Guess must be between 0 and 100")
        
        if request.elapsed_ms < 0:
            raise ValueError("Elapsed time cannot be negative")
        
        response = await grade_answer(request, db)
        return response
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error grading answer: {e}")
        raise HTTPException(status_code=500, detail="Failed to grade answer")

# Get daily questions
@app.get("/api/daily", response_model=List[QuestionData])
@timed_endpoint("daily")
async def get_daily(device_id: str, db: Session = Depends(get_db)):
    """Get deterministic daily questions for a device."""
    try:
        if not device_id or len(device_id) < 3:
            raise ValueError("Valid device_id is required")
        
        # Use UTC date for consistency
        date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
        questions = await get_daily_questions(device_id, date_str, db)
        return questions
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting daily questions: {e}")
        raise HTTPException(status_code=500, detail="Failed to get daily questions")

# Get player statistics
@app.get("/api/me/stats", response_model=StatsResponse)
@timed_endpoint("stats")
async def get_stats(device_id: str, db: Session = Depends(get_db)):
    """Get player statistics."""
    try:
        if not device_id or len(device_id) < 3:
            raise ValueError("Valid device_id is required")
        
        stats = await get_player_stats(device_id, db)
        return stats
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get statistics")

# Get enhanced player statistics with time analytics
@app.get("/api/me/stats/enhanced", response_model=EnhancedStatsResponse)
@timed_endpoint("enhanced_stats")
async def get_enhanced_stats(device_id: str, db: Session = Depends(get_db)):
    """Get enhanced player statistics with time analytics."""
    try:
        if not device_id or len(device_id) < 3:
            raise ValueError("Valid device_id is required")
        
        stats = await get_enhanced_player_stats(device_id, db)
        return stats
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting enhanced stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get enhanced statistics")

# Define frontend serving AFTER all API routes
def setup_frontend_routes():
    """Set up frontend serving routes - called after API routes are defined."""
    frontend_path = "/app/frontend/dist"
    
    # Mount static files if they exist (production)
    if os.path.exists(frontend_path):
        app.mount("/assets", StaticFiles(directory=f"{frontend_path}/assets"), name="assets")
        
        @app.get("/")
        async def serve_frontend():
            """Serve the React frontend."""
            return FileResponse(f"{frontend_path}/index.html")
        
        @app.get("/{full_path:path}")
        async def serve_spa(full_path: str):
            """Serve SPA - fallback to index.html for client-side routing."""            
            # Check if static file exists
            file_path = f"{frontend_path}/{full_path}"
            if os.path.exists(file_path) and os.path.isfile(file_path):
                return FileResponse(file_path)
            
            # Fallback to index.html for client-side routing
            return FileResponse(f"{frontend_path}/index.html")
    else:
        # Development mode - just return API info
        @app.get("/")
        async def dev_root():
            return {
                "message": "Poker Equity Trainer API",
                "docs": "/docs",
                "health": "/healthz",
                "frontend": "Run frontend separately in development"
            }

# Call after all API routes are defined
setup_frontend_routes()

# Add request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests for debugging."""
    start_time = datetime.now()
    response = await call_next(request)
    duration = datetime.now() - start_time
    
    logger.info(f"{request.method} {request.url.path} - {response.status_code} - {duration.total_seconds():.3f}s")
    return response

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app:app", 
        host="0.0.0.0", 
        port=8000, 
        reload=config.APP_ENV == "dev"
    )