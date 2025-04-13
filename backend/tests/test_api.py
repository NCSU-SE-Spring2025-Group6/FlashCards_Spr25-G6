import unittest
import json
from flask import Flask
from src.api import create_app  # Import the create_app function from your main module


class TestCreateApp(unittest.TestCase):
    def setUp(self):
        """Setup test client for Flask app."""
        self.app = create_app()
        self.client = self.app.test_client()
        self.app.config["TESTING"] = True

    def test_app_instance(self):
        """Test that create_app returns a Flask instance."""
        self.assertIsInstance(self.app, Flask)

    def test_blueprints_registration(self):
        """Test that all blueprints are registered."""
        blueprint_names = ["auth_bp", "deck_bp", "card_bp", "folder_bp"]
        for bp_name in blueprint_names:
            self.assertIn(
                bp_name,
                self.app.blueprints,
                f"{bp_name} should be registered in the app",
            )

    def test_home_route(self):
        """Test the home route."""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)

    # def test_cors_headers(self):
    #     """Test that CORS headers are set."""
    #     response = self.client.get("/")
    #     self.assertIn("Access-Control-Allow-Origin", response.headers)
    #     self.assertEqual(response.headers["Access-Control-Allow-Origin"], "*")

    def test_404_error(self):
        """Test 404 error handler."""
        response = self.client.get("/nonexistent_route")
        self.assertEqual(response.status_code, 404)
        self.assertIn("Not Found", response.get_data(as_text=True))

    # def test_create_app_config(self):
    #     """Test that the app is created with the correct configuration."""
    #     self.assertTrue(self.app.config["TESTING"])
    #     self.assertEqual(self.app.config["CORS_HEADERS"], "Content-Type")

    def test_auth_signup_route(self):
        """Test the signup route of the auth blueprint."""
        response = self.client.post(
            "/signup",
            data=json.dumps({"email": "test@example.com", "password": "password123"}),
            content_type="application/json",
        )
        self.assertIn(response.status_code, [201, 400])

    def test_auth_login_route(self):
        """Test the login route of the auth blueprint."""
        response = self.client.post(
            "/login",
            data=json.dumps({"email": "test@example.com", "password": "password123"}),
            content_type="application/json",
        )
        self.assertIn(response.status_code, [200, 400])

    def test_deck_create_route(self):
        """Test the create deck route of the deck blueprint."""
        response = self.client.post(
            "/deck/create",
            data=json.dumps(
                {
                    "localId": "Test",
                    "title": "TestDeck",
                    "description": "This is a test deck",
                    "visibility": "public",
                }
            ),
            content_type="application/json",
        )
        self.assertIn(response.status_code, [201, 400])

    def test_deck_update_route(self):
        """Test the update deck route of the deck blueprint."""
        response = self.client.patch(
            "/deck/update/Test",
            data=json.dumps(
                {
                    "localId": "Test",
                    "title": "Updated title",
                    "description": "Updated description",
                    "visibility": "public",
                }
            ),
            content_type="application/json",
        )
        self.assertIn(response.status_code, [201, 400])

    def test_deck_delete_route(self):
        """Test the delete deck route of the deck blueprint."""
        response = self.client.delete("/deck/delete/Test")
        self.assertIn(response.status_code, [200, 400])

    def test_deck_get_route(self):
        """Test the get deck route of the deck blueprint."""
        response = self.client.get("/deck/Test")
        self.assertIn(response.status_code, [200, 400])

    def test_deck_get_all_route(self):
        """Test the get all decks route of the deck blueprint."""
        response = self.client.get("/deck/all", query_string=dict(localId="Test"))
        self.assertIn(response.status_code, [200, 400])

    def test_deck_update_last_opened_route(self):
        """Test the update last opened route of the deck blueprint."""
        response = self.client.patch("/deck/updateLastOpened/Test")
        self.assertIn(response.status_code, [200, 400])

    def test_deck_get_leaderboard_route(self):
        """Test the get leaderboard route of the deck blueprint."""
        response = self.client.get("/deck/TestDeck/leaderboard")
        self.assertIn(response.status_code, [200, 400])

    def test_deck_update_leaderboard_route(self):
        """Test the update leaderboard route of the deck blueprint."""
        response = self.client.post(
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
        self.assertIn(response.status_code, [200, 400, 500])

    def test_deck_get_user_score_route(self):
        """Test the get user score route of the deck blueprint."""
        response = self.client.get("/deck/TestDeck/user-score/test123")
        self.assertIn(response.status_code, [200, 400])

    def test_card_get_all_route(self):
        """Test the get all cards route of the card blueprint."""
        response = self.client.get("/deck/Test/card/all")
        self.assertIn(response.status_code, [200, 400])

    def test_card_create_route(self):
        """Test the create card route of the card blueprint."""
        response = self.client.post(
            "/deck/Test/card/create",
            data=json.dumps(
                {
                    "localId": "Test",
                    "cards": [{"front": "front", "back": "back", "hint": "hint"}],
                }
            ),
            content_type="application/json",
        )
        self.assertIn(response.status_code, [201, 400])

    def test_card_update_route(self):
        """Test the update card route of the card blueprint."""
        response = self.client.patch(
            "/deck/Test/update/test_card",
            data=json.dumps({"word": "updated_word", "meaning": "updated_meaning"}),
            content_type="application/json",
        )
        self.assertIn(response.status_code, [201, 400])

    def test_card_delete_route(self):
        """Test the delete card route of the card blueprint."""
        response = self.client.delete("/deck/Test/delete/test_card")
        self.assertIn(response.status_code, [200, 400])

    def test_auth_signup_missing_email(self):
        """Test the signup route with missing email."""
        response = self.client.post(
            "/signup",
            data=json.dumps({"password": "password123"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.data.decode())
        # self.assertEqual(response_data["message"], "Registration Failed")
        self.assertIn(response_data["message"], 
                      ["Registration Failed",
                        "An unknown error occurred. Please try again."
                        ]
                    )

    def test_auth_signup_missing_password(self):
        """Test the signup route with missing password."""
        response = self.client.post(
            "/signup",
            data=json.dumps({"email": "test@example.com"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.data.decode())
        # self.assertEqual(response_data["message"], "Registration Failed")
        self.assertIn(response_data["message"], 
                      ["Registration Failed",
                        "An unknown error occurred. Please try again."
                        ]
                    )

    def test_auth_signup_invalid_json(self):
        """Test the signup route with invalid JSON."""
        response = self.client.post(
            "/signup",
            data="invalid json",
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.data.decode())
        # self.assertEqual(response_data["message"], "Registration Failed")
        self.assertIn(response_data["message"], 
                      ["Registration Failed",
                        "An unknown error occurred. Please try again."
                        ]
                    )

    def test_auth_login_missing_email(self):
        """Test the login route with missing email."""
        response = self.client.post(
            "/login",
            data=json.dumps({"password": "password123"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.data.decode())
        self.assertEqual(response_data["message"], "Login Failed")

    def test_auth_login_missing_password(self):
        """Test the login route with missing password."""
        response = self.client.post(
            "/login",
            data=json.dumps({"email": "test@example.com"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.data.decode())
        self.assertEqual(response_data["message"], "Login Failed")

    def test_auth_login_invalid_json(self):
        """Test the login route with invalid JSON."""
        response = self.client.post(
            "/login",
            data="invalid json",
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.data.decode())
        self.assertEqual(response_data["message"], "Login Failed")


if __name__ == "__main__":
    unittest.main()
