# Poker Equity Trainer 🃏

A production-ready web application for training heads-up poker equity intuition. Built with FastAPI, React, and Docker for easy deployment.

![Screenshot](https://img.shields.io/badge/React-18.2-blue) ![Screenshot](https://img.shields.io/badge/FastAPI-0.104-green) ![Screenshot](https://img.shields.io/badge/Docker-Ready-blue)

## 🚀 Quick Start

Your friends can run this in one command:

```bash
git clone <repo-url>
cd PokerEquity
docker-compose up
```

Visit **http://localhost:8000** and start training!

## ✨ Features

### Game Modes
- **Drill Mode**: Infinite random hands for practice
- **Daily 10**: 10 deterministic questions per day per device

### Equity Calculation
- **Exact enumeration** for flop/turn/river (fast, precise)
- **Monte Carlo simulation** for preflop (200,000 iterations)
- **Smart caching** with LRU + TTL for performance

### Scoring System
- Tiered scoring: Perfect (≤0.5%), Close (≤1.0%), Good (≤2.5%)
- **Streak bonuses**: +5% per consecutive close guess (max +50%)
- Detailed explanations for each result

### UI/UX
- Clean, responsive design with Tailwind CSS
- **Keyboard-first**: Arrow keys to adjust, Enter to submit, Space for next
- Dark mode support
- Framer Motion animations for smooth feedback
- Real-time equity visualization

## 🏗️ Architecture

**Single Docker Container** serving both frontend and backend:

```
┌─────────────────┐
│   FastAPI       │ ← Serves React build + API endpoints
├─────────────────┤
│   SQLite DB     │ ← Game data + player stats  
├─────────────────┤
│   LRU Cache     │ ← Equity results (30 day TTL)
├─────────────────┤
│   React SPA     │ ← Built assets served statically
└─────────────────┘
```

## 📊 Game Logic

### Street Distribution
- **Flop**: 35% (most complex decisions)
- **Turn**: 30% (counting outs)  
- **River**: 25% (0% or 100% equity)
- **Preflop**: 10% (hand strength focus)

### Equity Formula
```
Equity = (Wins + 0.5 × Ties) / Total × 100
```

### Scoring Tiers
| Error Range | Base Score | Label |
|-------------|------------|-------|
| ≤ 0.5% | 100 | Perfect! |
| ≤ 1.0% | 85 | Close |
| ≤ 2.5% | 70 | Good |
| > 2.5% | 70 - (error-2.5)×12 | Practice more |

## 🛠️ Development

### Local Development

**Backend**:
```bash
cd backend
pip install -r requirements.txt
python -m uvicorn app:app --reload --port 8000
```

**Frontend**:
```bash
cd frontend  
npm install
npm run dev  # Runs on :5173 with proxy to :8000
```

**Tests**:
```bash
cd backend
python -m pytest tests/ -v
```

### Environment Configuration

Copy `.env.example` to `.env` and customize:

```bash
# Application Environment
APP_ENV=dev

# Database Configuration  
DB_PATH=/app/data/app.db

# Game Settings
DAILY_SIZE=10
PREFLOP_MC=200000
RNG_SEED_SALT=poker_equity_salt_2024

# Cache Settings
CACHE_MAX_SIZE=100000
CACHE_TTL_SECONDS=2592000  # 30 days
```

## 📁 Project Structure

```
PokerEquity/
├── backend/
│   ├── app.py              # FastAPI main application
│   ├── equity.py           # Core evaluation engine
│   ├── game.py             # Game logic & question generation
│   ├── models.py           # SQLAlchemy database models
│   ├── services.py         # LRU cache & metrics
│   ├── config.py           # Environment configuration
│   └── tests/              # Backend test suite
├── frontend/
│   ├── src/
│   │   ├── components/     # React components (Card, EquityDial, etc.)
│   │   ├── lib/            # API client, utilities, types  
│   │   └── store/          # Zustand state management
│   └── package.json
├── Dockerfile              # Multi-stage production build
├── docker-compose.yml      # Single-command deployment
└── README.md
```

## 🔧 API Endpoints

### Core Game API
- `POST /api/deal` → Generate new question
- `POST /api/grade` → Grade player's guess  
- `GET /api/daily?device_id=X` → Get daily questions
- `GET /api/me/stats?device_id=X` → Player statistics

### Monitoring
- `GET /healthz` → Health check
- `GET /api/metrics` → Performance metrics

### Example API Flow

**1. Deal Question**:
```json
POST /api/deal
→ {
  "id": "Q_20250827_12345",
  "street": "flop", 
  "hero": "AsKd",
  "villain": "QhJh",
  "board": ["Ah","Ts","2c"],
  "tags": ["two_tone"]
}
```

**2. Grade Answer**:
```json
POST /api/grade
{
  "id": "Q_20250827_12345",
  "guess_equity_hero": 62.9,
  "elapsed_ms": 2300,
  "device_id": "dev_123"
}
→ {
  "truth": 63.7,
  "delta": 0.8,
  "score": 85,
  "streak": 4,
  "source": "exact",
  "explain": [
    "Villain has ~9 flush outs + 6 straight outs",
    "Top pair + kicker blocker reduces villain equity"
  ]
}
```

## 🎯 Performance

### Benchmarks
- **Flop equity**: ~2ms (exact enumeration of 1,081 runouts)
- **Turn equity**: ~0.5ms (exact enumeration of 46 rivers)  
- **River equity**: ~0.1ms (direct hand comparison)
- **Preflop equity**: ~200ms (200K Monte Carlo iterations)

### Optimizations
- **SQLite WAL mode** for concurrent reads
- **LRU cache** prevents memory leaks (100K max items)
- **Canonical caching** by hand strength (not suits)
- **Frontend query caching** (5min stale time)

## 🐳 Docker Details

**Multi-stage build**:
1. **Frontend builder**: Node.js → static React build
2. **Backend builder**: Python deps installation  
3. **Production image**: Combined FastAPI + React assets

**Production optimizations**:
- Non-root user for security
- Health checks for monitoring
- Volume mounting for data persistence
- Proper signal handling for graceful shutdown

## 🔒 Security Notes

This is designed as a **local/friend-sharing** application:
- No authentication system (device ID only)
- CORS set to permissive for development
- SQLite file-based storage
- No sensitive data handling

For production deployment, consider adding:
- User authentication
- Rate limiting  
- HTTPS termination
- Database encryption

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass: `pytest backend/tests/`
5. Submit a pull request

## 📄 License

MIT License - Feel free to use this for learning and sharing!

---

**Built with ❤️ for the poker community**

*"The beautiful thing about poker is that everybody thinks they can play." - Chris Moneymaker*