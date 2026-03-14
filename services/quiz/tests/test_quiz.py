import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from app.main import app
from app.services.auth import get_current_user, get_current_student

client = TestClient(app)

def override_get_current_user(): return MagicMock(id="user123")
def override_get_current_student(): return MagicMock(id="student123", role="student")

app.dependency_overrides[get_current_user] = override_get_current_user
app.dependency_overrides[get_current_student] = override_get_current_student

class MockCursor:
    def __init__(self, data): self.data = data
    async def to_list(self, length=None): return self.data

class MockQuery:
    def __init__(self, data): self.data = data
    def limit(self, l): return MockCursor(self.data)

class MockQuestions:
    def find(self, query):
        return MockQuery([{"_id": "q1", "topic": "Biology", "text": "Q1", "difficulty": "medium"}])
    def aggregate(self, pipeline):
        return MockCursor([{"topic": "Biology", "subject": "Science"}])
    async def find_one(self, query):
        return {"_id": "q1", "answer": "Cell", "topic": "Biology", "subject": "Science"}

class MockAnswers:
    async def insert_one(self, doc): pass

class MockDB:
    def __init__(self):
        self.questions = MockQuestions()
        self.answers = MockAnswers()

mock_db_instance = MockDB()

@pytest.fixture(autouse=True)
def mock_get_database():
    with patch("app.routes.quiz.get_database", return_value=mock_db_instance):
        yield mock_db_instance

@patch("app.routes.quiz.quiz_cache.get", return_value=None)
@patch("app.routes.quiz.quiz_cache.set")
def test_get_quiz_no_cache(mock_set, mock_get, mock_get_database):
    response = client.get("/quiz?topic=Biology&limit=1")
    assert response.status_code == 200
    assert response.json()[0]["topic"] == "Biology"
    mock_set.assert_called_once()

@patch("app.routes.quiz.quiz_cache.get")
def test_get_quiz_cached(mock_get, mock_get_database):
    mock_get.return_value = [{"id": "q1", "topic": "Biology", "text": "Cached Q1", "difficulty": "medium"}]
    response = client.get("/quiz?topic=Biology")
    assert response.status_code == 200
    assert response.json()[0]["text"] == "Cached Q1"

def test_get_topics(mock_get_database):
    response = client.get("/topics")
    assert response.status_code == 200
    assert len(response.json()) == 1

@patch("app.routes.quiz.update_difficulty_after_answer", return_value="hard")
def test_submit_answer_correct(mock_update, mock_get_database):
    response = client.post(
        "/submit-answer",
        json={"question_id": "q1", "selected_answer": "Cell"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["is_correct"] is True
    assert data["new_difficulty"] == "hard"
