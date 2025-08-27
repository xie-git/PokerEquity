import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.app import app
from backend.models import Base, get_db

# Create test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="session")
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client(setup_database):
    return TestClient(app)

class TestAPI:
    
    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/healthz")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
    
    def test_deal_question(self, client):
        """Test dealing a new question."""
        response = client.post("/api/deal")
        assert response.status_code == 200
        
        data = response.json()
        assert "id" in data
        assert data["street"] in ["pre", "flop", "turn", "river"]
        assert len(data["hero"]) == 4  # Two cards
        assert len(data["villain"]) == 4  # Two cards
        assert isinstance(data["board"], list)
        assert isinstance(data["tags"], list)
        
        # Validate board size based on street
        board_sizes = {"pre": 0, "flop": 3, "turn": 4, "river": 5}
        expected_size = board_sizes[data["street"]]
        assert len(data["board"]) == expected_size
    
    def test_grade_answer(self, client):
        """Test grading an answer."""
        # First, deal a question
        deal_response = client.post("/api/deal")
        question = deal_response.json()
        
        # Grade the answer
        grade_request = {
            "id": question["id"],
            "guess_equity_hero": 55.5,
            "elapsed_ms": 2500,
            "device_id": "test_device_123"
        }
        
        response = client.post("/api/grade", json=grade_request)
        assert response.status_code == 200
        
        data = response.json()
        assert "truth" in data
        assert "delta" in data
        assert "score" in data
        assert "streak" in data
        assert "source" in data
        assert "explain" in data
        
        assert 0 <= data["truth"] <= 100
        assert data["delta"] >= 0
        assert 0 <= data["score"] <= 150  # Can be > 100 with streak bonus
        assert data["streak"] >= 0
        assert isinstance(data["explain"], list)
        assert len(data["explain"]) > 0
    
    def test_grade_invalid_question(self, client):
        """Test grading with invalid question ID."""
        grade_request = {
            "id": "invalid_question_id",
            "guess_equity_hero": 50.0,
            "elapsed_ms": 1000
        }
        
        response = client.post("/api/grade", json=grade_request)
        assert response.status_code == 400 or response.status_code == 500
    
    def test_grade_validation(self, client):
        """Test input validation for grading."""
        # Deal a valid question first
        deal_response = client.post("/api/deal")
        question = deal_response.json()
        
        # Test invalid equity (too high)
        grade_request = {
            "id": question["id"],
            "guess_equity_hero": 150.0,  # Invalid
            "elapsed_ms": 1000
        }
        response = client.post("/api/grade", json=grade_request)
        assert response.status_code == 400
        
        # Test invalid elapsed time (negative)
        grade_request = {
            "id": question["id"],
            "guess_equity_hero": 50.0,
            "elapsed_ms": -100  # Invalid
        }
        response = client.post("/api/grade", json=grade_request)
        assert response.status_code == 400
    
    def test_daily_questions(self, client):
        """Test getting daily questions."""
        device_id = "test_device_daily"
        response = client.get(f"/api/daily?device_id={device_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 10  # Default daily size
        
        # Each question should be valid
        for question in data:
            assert "id" in question
            assert question["street"] in ["pre", "flop", "turn", "river"]
            assert len(question["hero"]) == 4
            assert len(question["villain"]) == 4
            assert question["id"].startswith("DAILY_")
        
        # Request again should return same questions (deterministic)
        response2 = client.get(f"/api/daily?device_id={device_id}")
        data2 = response2.json()
        
        assert len(data) == len(data2)
        for q1, q2 in zip(data, data2):
            assert q1["id"] == q2["id"]
            assert q1["hero"] == q2["hero"]
            assert q1["villain"] == q2["villain"]
    
    def test_daily_questions_different_device(self, client):
        """Test that different devices get different daily questions."""
        response1 = client.get("/api/daily?device_id=device1")
        response2 = client.get("/api/daily?device_id=device2")
        
        data1 = response1.json()
        data2 = response2.json()
        
        # Should be different questions for different devices
        assert data1[0]["id"] != data2[0]["id"]
    
    def test_player_stats_empty(self, client):
        """Test stats for player with no games."""
        device_id = "new_test_device"
        response = client.get(f"/api/me/stats?device_id={device_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["games_played"] == 0
        assert data["avg_delta"] == 0.0
        assert data["perfects"] == 0
        assert data["close_rate"] == 0.0
        assert data["by_street"] == {}
    
    def test_player_stats_with_games(self, client):
        """Test stats after playing some games."""
        device_id = "stats_test_device"
        
        # Play a few games
        for i in range(3):
            # Deal question
            deal_response = client.post("/api/deal")
            question = deal_response.json()
            
            # Grade answer
            grade_request = {
                "id": question["id"],
                "guess_equity_hero": 50.0 + i,  # Varying guesses
                "elapsed_ms": 2000 + i * 100,
                "device_id": device_id
            }
            client.post("/api/grade", json=grade_request)
        
        # Check stats
        response = client.get(f"/api/me/stats?device_id={device_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["games_played"] == 3
        assert data["avg_delta"] >= 0
        assert isinstance(data["by_street"], dict)
    
    def test_api_error_handling(self, client):
        """Test various error scenarios."""
        # Missing device_id for daily
        response = client.get("/api/daily")
        assert response.status_code == 422  # FastAPI validation error
        
        # Empty device_id for daily
        response = client.get("/api/daily?device_id=")
        assert response.status_code == 400
        
        # Missing device_id for stats
        response = client.get("/api/me/stats")
        assert response.status_code == 422
        
        # Invalid JSON for grading
        response = client.post("/api/grade", json={})
        assert response.status_code == 422
    
    def test_round_trip_workflow(self, client):
        """Test complete workflow: deal -> grade -> stats."""
        device_id = "workflow_test_device"
        
        # Deal a question
        deal_response = client.post("/api/deal")
        assert deal_response.status_code == 200
        question = deal_response.json()
        
        # Grade with perfect guess (if we knew the truth)
        # For testing, just use 50% as a reasonable guess
        grade_request = {
            "id": question["id"],
            "guess_equity_hero": 50.0,
            "elapsed_ms": 1500,
            "device_id": device_id
        }
        
        grade_response = client.post("/api/grade", json=grade_request)
        assert grade_response.status_code == 200
        result = grade_response.json()
        
        # Check stats updated
        stats_response = client.get(f"/api/me/stats?device_id={device_id}")
        assert stats_response.status_code == 200
        stats = stats_response.json()
        assert stats["games_played"] >= 1
    
    def test_metrics_endpoint(self, client):
        """Test metrics endpoint."""
        response = client.get("/api/metrics")
        assert response.status_code == 200
        
        data = response.json()
        assert "request_stats" in data
        assert "app_env" in data
        assert "preflop_mc" in data