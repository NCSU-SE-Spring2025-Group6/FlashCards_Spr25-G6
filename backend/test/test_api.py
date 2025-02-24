import unittest
from flask import Flask, jsonify
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
    def test_cors_headers(self):
        """Test that CORS headers are set."""
        response = self.client.get("/")
        self.assertIn("Access-Control-Allow-Origin", response.headers)
        self.assertEqual(response.headers["Access-Control-Allow-Origin"], "*")
    def test_404_error(self):
        """Test 404 error handler."""
        response = self.client.get("/nonexistent_route")
        self.assertEqual(response.status_code, 404)
        self.assertIn("Not Found", response.get_data(as_text=True))
    def test_create_app_config(self):
        """Test that the app is created with the correct configuration."""
        self.assertTrue(self.app.config["TESTING"])
        self.assertEqual(self.app.config["CORS_HEADERS"], "Content-Type")

if __name__ == "__main__":
    unittest.main()
    
    def test_index_route(self):
        """Test the index route of our app."""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)

if __name__ == "__main__":
    unittest.main()
    