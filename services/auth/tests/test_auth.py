import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from app.main import app

client = TestClient(app)

DUMMY_USER = {
    "_id": "user123",
    "username": "teacher@test.com",
    "hashed_password": "$2b$12$dummyhashedpassword",
    "role": "teacher",
    "grade": None
}

class MockCollection:
    def __init__(self, name):
        self.name = name
        self.doc = None
        
    async def find_one(self, query):
        if self.doc == "duplicate": return DUMMY_USER
        if self.doc == "not_found": return None
        return DUMMY_USER if self.name == "users" else None

    async def insert_one(self, doc):
        return type("InsertResult", (), {"inserted_id": "user123"})

    async def count_documents(self, query):
        return 0

class MockCounters:
    async def find_one_and_update(self, filter, update, upsert=False, return_document=False):
        return {"_id": "user_id", "seq": 1}

class MockDB:
    def __init__(self):
        self.users = MockCollection("users")
        self.counters = MockCounters()

mock_db_instance = MockDB()

@pytest.fixture(autouse=True)
def mock_get_database():
    with patch("app.routes.auth.get_database", return_value=mock_db_instance):
        yield mock_db_instance

def test_register_user_success(mock_get_database):
    mock_get_database.users.doc = "not_found"
    response = client.post(
        "/auth/register",
        json={
            "username": "newteacher@test.com",
            "password": "password123",
            "role": "teacher"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "newteacher@test.com"

def test_register_user_duplicate(mock_get_database):
    mock_get_database.users.doc = "duplicate"
    response = client.post(
        "/auth/register",
        json={
            "username": "teacher@test.com",
            "password": "password123",
            "role": "teacher"
        }
    )
    assert response.status_code == 400

def test_login_success(mock_get_database):
    mock_get_database.users.doc = "found"
    with patch("app.routes.auth.verify_password", return_value=True):
        response = client.post(
            "/auth/login",
            data={
                "username": "teacher@test.com",
                "password": "password123"
            }
        )
        assert response.status_code == 200
        assert "access_token" in response.json()

def test_login_failure(mock_get_database):
    mock_get_database.users.doc = "not_found"
    response = client.post(
        "/auth/login",
        data={
            "username": "wrong@test.com",
            "password": "password123"
        }
    )
    assert response.status_code == 401

