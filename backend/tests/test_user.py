import pytest
from flask import Flask, jsonify
from flask_cors import cross_origin
from src.user.routes import user_bp, get_user_stats, get_user_progress

# Mock Firebase database
class MockFirebaseDatabase:
    def __init__(self):
        self.data = {}

    def child(self, name):
        return self

    def get(self):
        class MockResponse:
            def __init__(self, data):
                self._data = data

            def val(self):
                return self._data

            def each(self):
                if self._data:
                    return [MockEntry(key, value) for key, value in self._data.items()]
                return []

        return MockResponse(self.data)

class MockEntry:
    def __init__(self, key, value):
        self._key = key
        self._value = value

    def key(self):
        return self._key

    def val(self):
        return self._value

# Mock Firebase initialization
@pytest.fixture
def app():
    app = Flask(__name__)
    app.register_blueprint(user_bp)
    app.config["TESTING"] = True
    global db
    db = MockFirebaseDatabase()
    return app

@pytest.fixture
def client(app):
    return app.test_client()

# # Route for get_user_stats()
# @user_bp.route("/user/<user_id>/stats", methods=["GET"])
# @cross_origin(supports_credentials=True)
# def get_user_stats(user_id):
#     """Fetch aggregated user performance across all decks."""
#     try:
#         leaderboard_entries = db.child("leaderboard").get()
#         total_correct = 0
#         total_incorrect = 0
#         total_decks = 0

#         if leaderboard_entries.val():
#             for deck in leaderboard_entries.each():
#                 deck_data = deck.val()
#                 if user_id in deck_data:
#                     user_data = deck_data[user_id]
#                     total_correct += user_data.get("correct", 0)
#                     total_incorrect += user_data.get("incorrect", 0)
#                     total_decks += 1

#         return jsonify(
#             {
#                 "total_correct": total_correct,
#                 "total_incorrect": total_incorrect,
#                 "total_decks": total_decks,
#                 "message": "User statistics fetched successfully",
#                 "status": 200,
#             }
#         ), 200
#     except Exception as e:
#         return jsonify({"message": f"Error fetching user stats: {e}", "status": 400}), 400

# Test cases for get_user_stats()

def test_get_user_stats_success(client, monkeypatch):
    """Test the /user/<user_id>/stats endpoint with valid data."""
    # Mock leaderboard data
    mock_data = {
        "deck1": {
            "user123": {"correct": 5, "incorrect": 2},
        },
        "deck2": {
            "user123": {"correct": 3, "incorrect": 1},
        },
    }

    # Create a new mock database instance for this test
    mock_db = MockFirebaseDatabase()
    mock_db.data = mock_data

    # Monkeypatch the global db object to use the mock database
    monkeypatch.setattr("src.user.routes.db", mock_db)

    response = client.get("/user/user123/stats")
    assert response.status_code == 200
    response_data = response.get_json()
    assert response_data["total_correct"] == 8
    assert response_data["total_incorrect"] == 3
    assert response_data["total_decks"] == 2
    assert response_data["message"] == "User statistics fetched successfully"

def test_get_user_stats_fail(client, monkeypatch):
    # Create a new mock database instance for this test
    mock_db = MockFirebaseDatabase()
    mock_db.data = {}

    # Monkeypatch the global db object to use the mock database
    monkeypatch.setattr("src.user.routes.db", mock_db)
    # Replace the global db object with an empty mock database
    global db
    db.data = {}

    response = client.get("/user/user123/stats")
    assert response.status_code == 200
    response_data = response.get_json()
    assert response_data["total_correct"] == 0

def test_get_user_stats_error(client, monkeypatch):
    # Create a new mock database instance for this test
    mock_db = MockFirebaseDatabase()

    # Simulate a database error
    def mock_get_error():
        raise Exception("Database error")

    mock_db.get = mock_get_error

    # Monkeypatch the global db object to use the mock database
    monkeypatch.setattr("src.user.routes.db", mock_db)

    # Simulate a database error
    def mock_get_error():
        raise Exception("Database error")

    db.get = mock_get_error

    response = client.get("/user/user123/stats")
    assert response.status_code == 400
    response_data = response.get_json()
    assert response_data["message"].startswith("Error fetching user stats")

# Test cases for get_user_progress()


def test_get_user_progress_no_data(client):
    """Test the /user/<user_id>/progress endpoint with no data."""
    # Replace the global db object with an empty mock database
    global db
    db.data = {}

    response = client.get("/user/user123/progress")
    assert response.status_code == 200
    response_data = response.get_json()
    assert len(response_data["progress"]) == 0
    assert response_data["message"] == "User progress fetched successfully"
