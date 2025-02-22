import unittest
from flask import Flask
from unittest.mock import patch
from src.api import create_app  # Import the create_app function from your main module

class TestCreateApp(unittest.TestCase):
    
    def setUp(self):
        """Setup test client for Flask app."""
        self.app = create_app()
        self.client = self.app.test_client()
        self.app.config['TESTING'] = True

    def test_app_instance(self):
        """Test that create_app returns a Flask instance."""
        self.assertIsInstance(self.app, Flask)

    def test_blueprints_registration(self):
        """Test that all blueprints are registered."""
        blueprint_names = ['auth_bp', 'deck_bp', 'card_bp', 'folder_bp']
        
        for bp_name in blueprint_names:
            self.assertIn(bp_name, self.app.blueprints, f"{bp_name} should be registered in the app")

if __name__ == '__main__':
    unittest.main()
