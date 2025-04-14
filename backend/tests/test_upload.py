import pytest
import json
from flask import Flask
from src.upload.routes import (
    upload_bp, 
    process_text_with_gemini, 
    create_new_deck
)

import sys
from pathlib import Path

# Add the parent directory to sys.path
sys.path.append(str(Path(__file__).parent.parent))

# Mock Firebase database
class MockFirebaseDatabase:
    def __init__(self):
        self.data = {}

    def child(self, name):
        return self

    def push(self, data):
        deck_id = "mock_deck_id"
        self.data[deck_id] = data
        return {"name": deck_id}

# Mock Firebase initialization
@pytest.fixture
def app():
    app = Flask(__name__)
    app.register_blueprint(upload_bp)
    app.config["TESTING"] = True
    global db
    db = MockFirebaseDatabase()
    return app

@pytest.fixture
def client(app):
    return app.test_client()

# Test cases
def test_upload_text_success(client, monkeypatch):
    """Test the /api/upload endpoint with valid input."""

    # Mock the Gemini API response
    def mock_process_text_with_gemini(text):
        return {
            "cards": [
                {"front": "What is AI?", "back": "Artificial Intelligence", "hint": "Think about machines."},
                {"front": "What is ML?", "back": "Machine Learning", "hint": "Subset of AI."}
            ]
        }

    monkeypatch.setattr("src.upload.routes.process_text_with_gemini", mock_process_text_with_gemini)

    # Mock request data
    data = {
        "text": "Explain AI and ML.",
        "localId": "user123",
        "visibility": "public",
        "description": "AI and ML basics",
        "title": "AI Basics"
    }

    response = client.post("/api/upload", json=data)
    assert response.status_code == 201
    response_data = response.get_json()
    assert response_data["message"] == "Deck imported successfully"

def test_upload_text_missing_text(client):
    """Test the /api/upload endpoint with missing text."""
    data = {
        "localId": "user123",
        "visibility": "public",
        "description": "AI and ML basics",
        "title": "AI Basics"
    }

    response = client.post("/api/upload", json=data)
    assert response.status_code == 400
    response_data = response.get_json()
    assert response_data["message"] == "No text provided"

def test_upload_text_short_text(client):
    """Test the /api/upload endpoint with text that is too short."""
    data = {
        "text": "Short",
        "localId": "user123",
        "visibility": "public",
        "description": "AI and ML basics",
        "title": "AI Basics"
    }

    response = client.post("/api/upload", json=data)
    assert response.status_code == 400
    response_data = response.get_json()
    assert response_data["message"] == "Text is too short, minimum length is 10 characters"

def test_process_text_with_gemini(monkeypatch):
    """Test the process_text_with_gemini function."""

    # Mock the Gemini API response
    def mock_post(url, headers, json):
        class MockResponse:
            def __init__(self):
                self.status_code = 200

            def json(self):
                return {
                    "candidates": [
                        {
                            "content": {
                                "parts": [
                                    {
                                        "text": '```json{"cards": [{"front": "What is AI?", "back": "Artificial Intelligence", "hint": "Think about machines."}]}```\n'
                                    }
                                ]
                            }
                        }
                    ]
                }

        return MockResponse()

    monkeypatch.setattr("requests.post", mock_post)

    text = "Explain AI and ML."
    flashcards = process_text_with_gemini(text)
    assert "cards" in flashcards
    assert flashcards["cards"][0]["front"] == "What is AI?"
    assert flashcards["cards"][0]["back"] == "Artificial Intelligence"

def test_create_new_deck(app):
    """Test the create_new_deck function."""
    user_id = "user123"
    flashcard_json = {
        "deck": {
            "title": "AI Basics",
            "description": "AI and ML basics",
            "visibility": "public"
        },
        "cards": [
            {"front": "What is AI?", "back": "Artificial Intelligence", "hint": "Think about machines."},
            {"front": "What is ML?", "back": "Machine Learning", "hint": "Subset of AI."}
        ]
    }

    # Push an application context
    with app.app_context():
        response = create_new_deck(user_id, flashcard_json)
        assert response[-1] == 201
        response_data = response[0].get_json()
        assert response_data["message"] == "Deck imported successfully"