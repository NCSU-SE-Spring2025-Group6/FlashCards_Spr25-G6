from flask import Flask
import sys

sys.path.append("backend/src")
import unittest
from unittest.mock import patch, MagicMock, ANY
import json
from src.deck.routes import deck_bp
from pathlib import Path
from unittest.mock import call

# Add the parent directory to sys.path
sys.path.append(str(Path(__file__).parent.parent))


class TestDeck(unittest.TestCase):
    @classmethod
    def setUp(self):
        self.app = Flask(__name__, instance_relative_config=False)
        self.app.register_blueprint(deck_bp)
        self.app = self.app.test_client()
        # self.client = self.app.test_client()

    def test_deck_id_route_get_valid_id(self):
        """Test the deck/id route of our app with a valid deck id"""
        with self.app:
            self.app.post(
                "/login",
                data=json.dumps(dict(email="aaronadb@gmail.com", password="flashcards123")),
                content_type="application/json",
                follow_redirects=True,
            )
            self.app.post(
                "/deck/create",
                data=json.dumps(
                    dict(
                        localId="Test",
                        title="TestDeck",
                        description="This is a test deck",
                        visibility="public",
                    )
                ),
                content_type="application/json",
            )
            response = self.app.get("/deck/Test")
            assert response.status_code == 200

    def test_deck_id_route_post(self):
        """Test the deck/id route of our app with the post method"""
        with self.app:
            self.app.post(
                "/login",
                data=json.dumps(dict(email="aaronadb@gmail.com", password="flashcards123")),
                content_type="application/json",
                follow_redirects=True,
            )
            self.app.post(
                "/deck/create",
                data=json.dumps(
                    dict(
                        localId="Test",
                        title="TestDeck",
                        description="This is a test deck",
                        visibility="public",
                    )
                ),
                content_type="application/json",
            )
            response = self.app.post("/deck/Test")
            assert response.status_code == 405

    # TODO: (lnotspotl) Figure out why this test halts
    # def test_deck_all_route(self):
    #    '''Test the deck/all route of our app'''
    #    response=self.app.get('/deck/all',query_string=dict(localId='Test'))
    #    assert response.status_code==200
    def test_deck_all_route_post(self):
        """Test that the post request to the '/deck/all' route is not allowed"""
        response = self.app.post("/deck/all")
        assert response.status_code == 405

    def test_create_deck_route(self):
        """Test the create deck route of our app"""
        response = self.app.post(
            "/deck/create",
            data=json.dumps(
                dict(
                    localId="Test",
                    title="TestDeck",
                    description="This is a test deck",
                    visibility="public",
                )
            ),
            content_type="application/json",
        )
        assert response.status_code == 201

    def test_update_deck_route_post(self):
        """Test the deck/update route of our app with"""
        with self.app:
            self.app.post(
                "/login",
                data=json.dumps(dict(email="aaronadb@gmail.com", password="flashcards123")),
                content_type="application/json",
                follow_redirects=True,
            )
            self.app.post(
                "/deck/create",
                data=json.dumps(
                    dict(
                        localId="Test",
                        title="TestDeck",
                        description="This is a test deck",
                        visibility="public",
                    )
                ),
                content_type="application/json",
            )
            response = self.app.patch(
                "/deck/update/Test",
                data=json.dumps(
                    dict(
                        localId="Test",
                        title="TestDeck",
                        description="This is a test deck",
                        visibility="public",
                    )
                ),
                content_type="application/json",
            )
            assert response.status_code == 201

    def test_delete_deck_route_post(self):
        """Test the deck/delete route of our app with"""
        with self.app:
            self.app.post(
                "/login",
                data=json.dumps(dict(email="aaronadb@gmail.com", password="flashcards123")),
                content_type="application/json",
                follow_redirects=True,
            )
            self.app.post(
                "/deck/create",
                data=json.dumps(
                    dict(
                        localId="Test",
                        title="TestDeck",
                        description="This is a test deck",
                        visibility="public",
                    )
                ),
                content_type="application/json",
            )
            response = self.app.delete("/deck/delete/Test")
            assert response.status_code == 200

    def test_update_last_opened_deck_route_failure(self):
        """Test the deck/updateLastOpened/<id> route of our app with failure scenario"""
        with self.app:
            # Arrange: Mock the database update to raise an exception
            with patch("src.deck.routes.db.child") as mock_db:
                mock_db.return_value.child.return_value.update.side_effect = Exception("Database update failed")
                # Simulate user login and deck creation
                self.app.post(
                    "/login",
                    data=json.dumps(dict(email="aaronadb@gmail.com", password="flashcards123")),
                    content_type="application/json",
                    follow_redirects=True,
                )
                self.app.post(
                    "/deck/create",
                    data=json.dumps(
                        dict(
                            localId="Test",
                            title="TestDeck",
                            description="This is a test deck",
                            visibility="public",
                        )
                    ),
                    content_type="application/json",
                )

                # Act: Send a request to update the last opened timestamp
                response = self.app.patch("/deck/updateLastOpened/Test", content_type="application/json")

                # Assert: Check the response status code for failure
                assert response.status_code == 400
                response_data = json.loads(response.data)
                assert response_data["message"] == "Failed to update lastOpened: Database update failed"

    @patch("src.deck.routes.db")  # Mock the database connection
    def test_get_leaderboard_route(self, mock_db):
        """Test the deck/<deckId>/leaderboard route of our app"""
        with self.app:
            # Arrange: Set up mock return value for leaderboard entries
            mock_entries = MagicMock()
            mock_entries.each.return_value = [
                MagicMock(
                    val=lambda: {
                        "userEmail": "user1@example.com",
                        "correct": 10,
                        "incorrect": 2,
                        "lastAttempt": "2024-01-01T12:00:00",
                    }
                ),
                MagicMock(
                    val=lambda: {
                        "userEmail": "user2@example.com",
                        "correct": 15,
                        "incorrect": 1,
                        "lastAttempt": " 2024-01-02T12:00:00",
                    }
                ),
                MagicMock(
                    val=lambda: {
                        "userEmail": "user3@example.com",
                        "correct": 5,
                        "incorrect": 0,
                        "lastAttempt": "2024-01-03T12:00:00",
                    }
                ),
            ]
            mock_db.child.return_value.child.return_value.get.return_value = mock_entries

            # Act: Send a request to get the leaderboard for a specific deck
            response = self.app.get("/deck/TestDeck/leaderboard")

            # Assert: Check the response status code and the content of the response
            assert response.status_code == 200
            response_data = json.loads(response.data)
            assert response_data["status"] == 200
            assert len(response_data["leaderboard"]) == 3
            assert response_data["leaderboard"][0]["userEmail"] == "user2@example.com"  # Highest score
            assert response_data["leaderboard"][1]["userEmail"] == "user1@example.com"  # Second highest score
            assert response_data["leaderboard"][2]["userEmail"] == "user3@example.com"  # Lowest score

    @patch("src.deck.routes.db")  # Mock the database connection
    def test_update_leaderboard_success(self, mock_db):
        """Test the /deck/<deck_id>/update-leaderboard route of our app for a successful update"""
        with self.app:
            # Arrange: Set up mock data
            deck_id = "TestDeck"
            user_id = "user123"
            user_email = "user@example.com"
            correct = 10
            incorrect = 2

            # Mock the database update
            mock_leaderboard_ref = MagicMock()
            mock_db.child.return_value.child.return_value.child.return_value = mock_leaderboard_ref

            # Act: Send a POST request to update the leaderboard
            response = self.app.post(
                f"/deck/{deck_id}/update-leaderboard",
                data=json.dumps(
                    {
                        "userId": user_id,
                        "userEmail": user_email,
                        "correct": correct,
                        "incorrect": incorrect,
                    }
                ),
                content_type="application/json",
            )
            # Assert: Check the response status code and message
            assert response.status_code == 200
            response_data = json.loads(response.data)
            assert response_data["message"] == "Leaderboard updated successfully"
            # Assert that the database update was called with the correct parameters
            mock_leaderboard_ref.update.assert_called_once_with(
                {
                    "userEmail": user_email,
                    "correct": correct,
                    "incorrect": incorrect,
                    "lastAttempt": ANY,  # Check that it's called but not the exact timestamp
                }
            )

    @patch("src.deck.routes.db")  # Mock the database connection
    def test_get_user_score_success(self, mock_db):
        """Test the /deck/<deckId>/user-score/<userId> route for a successful score fetch"""
        deck_id = "TestDeck"
        user_id = "user123"

        # Mock the database return value for a user that exists
        mock_leaderboard_entry = MagicMock()
        mock_leaderboard_entry.val.return_value = {"correct": 10, "incorrect": 2}
        mock_db.child.return_value.child.return_value.child.return_value.get.return_value = mock_leaderboard_entry
        # Act: Send a GET request to fetch the user's score
        response = self.app.get(f"/deck/{deck_id}/user-score/{user_id}")

        # Assert: Check the response status code and message
        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data["score"] == {"correct": 10, "incorrect": 2}
        assert response_data["message"] == "User score fetched successfully"

    @patch("src.deck.routes.db")  # Mock the database connection
    def test_get_user_score_no_entry(self, mock_db):
        """Test the /deck/<deckId>/user-score/<userId> route when no score entry exists"""
        deck_id = "TestDeck"
        user_id = "user123"

        # Mock the database return value for a user that does not exist
        mock_leaderboard_entry = MagicMock()
        mock_leaderboard_entry.val.return_value = None
        mock_db.child.return_value.child.return_value.child.return_value.get.return_value = mock_leaderboard_entry
        # Act: Send a GET request to fetch the user's score
        response = self.app.get(f"/deck/{deck_id}/user-score/{user_id}")

        # Assert: Check the response status code and message
        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data["score"] == {"correct": 0, "incorrect": 0}
        assert response_data["message"] == "No score found for the user, returning zeros."

    @patch("src.deck.routes.db")  # Mock the database connection
    def test_get_user_score_error(self, mock_db):
        """Test the /deck/<deckId>/user-score/<userId> route when an error occurs"""
        deck_id = "TestDeck"
        user_id = "user123"

        # Simulate an exception when accessing the database
        mock_db.child.return_value.child.return_value.child.return_value.get.side_effect = Exception("Database error")
        # Act: Send a GET request to fetch the user's score
        response = self.app.get(f"/deck/{deck_id}/user-score/{user_id}")

        # Assert: Check the response status code and message
        assert response.status_code == 400
        response_data = json.loads(response.data)
        assert response_data["message"] == "An error occurred: Database error"

    @patch("src.deck.routes.db")
    def test_get_deck_error(self, mock_db):
        """Test error handling in getdeck route"""
        # Mock the database to raise an exception
        mock_db.child.return_value.child.return_value.get.side_effect = Exception("Database error")

        response = self.app.get("/deck/Test")
        assert response.status_code == 400
        response_data = json.loads(response.data)
        assert response_data["decks"] == []
        assert "An error occurred: Database error" in response_data["message"]

    @patch("src.deck.routes.db")
    def test_get_decks_with_cards(self, mock_db):
        """Test getdecks route with cards count"""
        # Create mock objects
        mock_deck = MagicMock()
        mock_deck_data = {
            "userId": "Test",
            "title": "TestDeck",
            "description": "Test Description",
            "visibility": "public",
        }
        mock_deck.val.return_value = mock_deck_data
        mock_deck.key.return_value = "deck123"
        # Create mock for decks query
        mock_decks_query = MagicMock()
        mock_decks_query.each.return_value = [mock_deck]
        # Create mock for cards query
        mock_cards_query = MagicMock()
        mock_cards_query.val.return_value = {"card1": {}, "card2": {}}  # Two cards

        # Set up the chain for deck query
        mock_db.child.return_value.order_by_child.return_value.equal_to.return_value.get.side_effect = [
            mock_decks_query,  # First call for decks
            mock_cards_query,  # Second call for cards
        ]
        # Make the request
        response = self.app.get("/deck/all", query_string=dict(localId="Test"))

        # Assertions
        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert len(response_data["decks"]) > 0  # Verify we have at least one deck
        assert response_data["decks"][0]["cards_count"] == 2
        assert response_data["decks"][0]["title"] == "TestDeck"
        assert response_data["decks"][0]["id"] == "deck123"
        # Verify the mock calls
        mock_db.child.assert_has_calls([call("deck"), call("card")], any_order=True)

    @patch("src.deck.routes.db")
    def test_get_decks_error(self, mock_db):
        """Test error handling in getdecks route"""
        # Mock the database to raise an exception
        mock_db.child.return_value.order_by_child.return_value.equal_to.side_effect = Exception("Database error")

        response = self.app.get("/deck/all", query_string=dict(localId="Test"))
        assert response.status_code == 400
        response_data = json.loads(response.data)
        assert response_data["decks"] == []
        assert "An error occurred Database error" in response_data["message"]

    @patch("src.deck.routes.db")
    def test_update_deck_error(self, mock_db):
        """Test error handling in update route"""
        # Mock the database to raise an exception
        mock_db.child.return_value.child.return_value.update.side_effect = Exception("Database error")

        response = self.app.patch(
            "/deck/update/Test",
            data=json.dumps(
                dict(
                    localId="Test",
                    title="TestDeck",
                    description="Test Description",
                    visibility="public",
                )
            ),
            content_type="application/json",
        )
        assert response.status_code == 400
        response_data = json.loads(response.data)
        assert "Update Deck Failed Database error" in response_data["message"]

    @patch("src.deck.routes.db")
    def test_delete_deck_error(self, mock_db):
        """Test error handling in delete route"""
        # Mock the database to raise an exception
        mock_db.child.return_value.child.return_value.remove.side_effect = Exception("Database error")

        response = self.app.delete("/deck/delete/Test")
        assert response.status_code == 400
        response_data = json.loads(response.data)
        assert "Delete Deck Failed Database error" in response_data["message"]

    @patch("src.deck.routes.db")
    def test_get_leaderboard_error(self, mock_db):
        """Test error handling in get_leaderboard route"""
        # Mock the database to raise an exception
        mock_db.child.return_value.child.return_value.get.side_effect = Exception("Database error")

        response = self.app.get("/deck/TestDeck/leaderboard")
        assert response.status_code == 400
        response_data = json.loads(response.data)
        assert response_data["leaderboard"] == []
        assert "An error occurred: Database error" in response_data["message"]

    @patch("src.deck.routes.db")
    def test_update_leaderboard_missing_userid(self, mock_db):
        """Test update_leaderboard route with missing userId"""
        response = self.app.post(
            "/deck/TestDeck/update-leaderboard",
            data=json.dumps({"userEmail": "test@example.com", "correct": 10, "incorrect": 2}),
            content_type="application/json",
        )
        assert response.status_code == 400
        response_data = json.loads(response.data)
        assert response_data["message"] == "User ID is required"

    @patch("src.deck.routes.db")
    def test_update_leaderboard_error(self, mock_db):
        """Test error handling in update_leaderboard route"""
        # Mock the database to raise an exception
        mock_db.child.return_value.child.return_value.child.return_value.update.side_effect = Exception(
            "Database error"
        )
        response = self.app.post(
            "/deck/TestDeck/update-leaderboard",
            data=json.dumps(
                {
                    "userId": "test123",
                    "userEmail": "test@example.com",
                    "correct": 10,
                    "incorrect": 2,
                }
            ),
            content_type="application/json",
        )
        assert response.status_code == 500
        response_data = json.loads(response.data)
        assert response_data["message"] == "Failed to update leaderboard"

    def test_create_deck_missing_cards(self):
        """Test creating a deck with missing cards"""
        response = self.client.post(
            "/deck/Test/card/create", data=json.dumps({"localId": "Test"}), content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertEqual(data["message"], "Adding cards Failed")

    def test_create_deck_missing_title(self):
        """Test creating a deck with missing title"""
        response = self.app.post(
            "/deck/create",
            data=json.dumps({"localId": "Test", "description": "This is a test deck", "visibility": "public"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertEqual(data["message"], "Create Deck Failed 'title'")

    def test_create_deck_missing_description(self):
        """Test creating a deck with missing description"""
        response = self.app.post(
            "/deck/create",
            data=json.dumps({"localId": "Test", "title": "TestDeck", "visibility": "public"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertEqual(data["message"], "Create Deck Failed 'description'")

    def test_create_deck_missing_visibility(self):
        """Test creating a deck with missing visibility"""
        response = self.app.post(
            "/deck/create",
            data=json.dumps({"localId": "Test", "title": "TestDeck", "description": "This is a test deck"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertEqual(data["message"], "Create Deck Failed 'visibility'")

    def test_create_deck_invalid_json(self):
        """Test creating a deck with invalid JSON"""
        response = self.app.post("/deck/create", data="invalid json", content_type="application/json")
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertEqual(data["message"], "Create Deck Failed 400: Bad Request")

    def test_update_deck_missing_title(self):
        """Test updating a deck with missing title"""
        response = self.app.patch(
            "/deck/update/Test",
            data=json.dumps({"localId": "Test", "description": "Updated description", "visibility": "public"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertEqual(data["message"], "Update Deck Failed 'title'")

    def test_update_deck_missing_description(self):
        """Test updating a deck with missing description"""
        response = self.app.patch(
            "/deck/update/Test",
            data=json.dumps({"localId": "Test", "title": "Updated title", "visibility": "public"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertEqual(data["message"], "Update Deck Failed 'description'")

    def test_update_deck_missing_visibility(self):
        """Test updating a deck with missing visibility"""
        response = self.app.patch(
            "/deck/update/Test",
            data=json.dumps({"localId": "Test", "title": "Updated title", "description": "Updated description"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertEqual(data["message"], "Update Deck Failed 'visibility'")

    def test_update_deck_invalid_json(self):
        """Test updating a deck with invalid JSON"""
        response = self.app.patch("/deck/update/Test", data="invalid json", content_type="application/json")
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertEqual(data["message"], "Update Deck Failed 400: Bad Request")

    def test_delete_deck_missing_id(self):
        """Test deleting a deck with missing id"""
        response = self.app.delete("/deck/delete/")
        self.assertEqual(response.status_code, 404)

    def test_delete_deck_invalid_json(self):
        """Test deleting a deck with invalid JSON"""
        response = self.app.delete("/deck/delete/Test", data="invalid json", content_type="application/json")
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertEqual(data["message"], "Delete Deck Failed")

    def test_get_deck_missing_id(self):
        """Test fetching a deck with missing id"""
        response = self.app.get("/deck/")
        self.assertEqual(response.status_code, 404)

    def test_get_deck_invalid_json(self):
        """Test fetching a deck with invalid JSON"""
        response = self.app.get("/deck/Test", data="invalid json", content_type="application/json")
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertEqual(data["decks"], [])
        self.assertTrue("An error occurred" in data["message"])

    def test_get_decks_invalid_json(self):
        """Test fetching decks with invalid JSON"""
        response = self.app.get("/deck/all", data="invalid json", content_type="application/json")
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertEqual(data["decks"], [])
        self.assertTrue("An error occurred" in data["message"])

    def test_update_last_opened_missing_id(self):
        """Test updating last opened with missing id"""
        response = self.app.patch("/deck/updateLastOpened/")
        self.assertEqual(response.status_code, 404)

    def test_update_last_opened_invalid_json(self):
        """Test updating last opened with invalid JSON"""
        response = self.app.patch("/deck/updateLastOpened/Test", data="invalid json", content_type="application/json")
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertTrue("Failed to update lastOpened" in data["message"])

    def test_get_leaderboard_missing_deckId(self):
        """Test fetching leaderboard with missing deckId"""
        response = self.app.get("/deck//leaderboard")
        self.assertEqual(response.status_code, 404)

    def test_get_leaderboard_invalid_json(self):
        """Test fetching leaderboard with invalid JSON"""
        response = self.app.get("/deck/TestDeck/leaderboard", data="invalid json", content_type="application/json")
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertEqual(data["leaderboard"], [])
        self.assertTrue("An error occurred" in data["message"])

    def test_update_leaderboard_missing_deckId(self):
        """Test updating leaderboard with missing deckId"""
        response = self.app.post(
            "/deck//update-leaderboard",
            data=json.dumps({"userId": "test123", "userEmail": "test@example.com", "correct": 10, "incorrect": 2}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 404)

    def test_update_leaderboard_invalid_json(self):
        """Test updating leaderboard with invalid JSON"""
        response = self.app.post(
            "/deck/TestDeck/update-leaderboard", data="invalid json", content_type="application/json"
        )
        self.assertEqual(response.status_code, 500)
        data = json.loads(response.data)
        self.assertEqual(data["message"], "Failed to update leaderboard")

    def test_get_user_score_missing_deckId(self):
        """Test fetching user score with missing deckId"""
        response = self.app.get("/deck//user-score/test123")
        self.assertEqual(response.status_code, 404)

    def test_get_user_score_missing_userId(self):
        """Test fetching user score with missing userId"""
        response = self.app.get("/deck/TestDeck/user-score/")
        self.assertEqual(response.status_code, 404)

    def test_get_user_score_invalid_json(self):
        """Test fetching user score with invalid JSON"""
        response = self.app.get(
            "/deck/TestDeck/user-score/test123", data="invalid json", content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertTrue("An error occurred" in data["message"])


if __name__ == "__main__":
    unittest.main()
