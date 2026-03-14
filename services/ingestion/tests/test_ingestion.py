import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from app.main import app

client = TestClient(app)

from app.services.auth import get_current_teacher

def override_get_current_teacher():
    return {"_id": "teacher123", "role": "teacher"}

app.dependency_overrides[get_current_teacher] = override_get_current_teacher

class MockSources:
    def __init__(self):
        self.doc = None
    async def find_one(self, query):
        if self.doc == "not_found": return None
        return {
            "_id": "src_123",
            "status": "completed",
            "filename": "test.pdf",
            "chunk_count": 5
        }
    async def insert_one(self, doc):
        pass

class MockDB:
    def __init__(self):
        self.sources = MockSources()

mock_db_instance = MockDB()

@pytest.fixture(autouse=True)
def mock_get_database():
    with patch("app.routes.ingest.get_database", return_value=mock_db_instance):
        yield mock_db_instance

def test_ingest_pdf_unsupported_file():
    response = client.post(
        "/ingest",
        data={"grade": 1, "subject": "Science"},
        files={"file": ("test.txt", b"dummy", "text/plain")}
    )
    assert response.status_code == 400

@patch("app.routes.ingest.BackgroundTasks.add_task")
@patch("app.routes.ingest.generate_source_id", return_value="src_123")
def test_ingest_pdf_success(mock_gen_id, mock_bg_task, mock_get_database):
    response = client.post(
        "/ingest",
        data={"grade": 1, "subject": "Science", "topic": "Biology"},
        files={"file": ("test.pdf", b"dummy pdf", "application/pdf")}
    )
    assert response.status_code == 200
    assert response.json()["source_id"] == "src_123"
    mock_bg_task.assert_called_once()

def test_get_ingest_status_not_found(mock_get_database):
    mock_get_database.sources.doc = "not_found"
    response = client.get("/ingest/src_999/status")
    assert response.status_code == 404

def test_get_ingest_status_success(mock_get_database):
    mock_get_database.sources.doc = "found"
    response = client.get("/ingest/src_123/status")
    assert response.status_code == 200
    assert response.json()["status"] == "completed"
