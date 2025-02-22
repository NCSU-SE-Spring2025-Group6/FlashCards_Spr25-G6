from flask import Flask
import sys
sys.path.append('backend/src')
import unittest
import pytest
from src.auth.routes import auth_bp
from src.deck.routes import deck_bp
from src.cards.routes import card_bp
import json
from unittest.mock import patch
from pathlib import Path

# Add the parent directory to sys.path
sys.path.append(str(Path(__file__).parent.parent))


class TestAuth(unittest.TestCase):
    @classmethod
    def setUp(self):
        self.app = Flask(__name__, instance_relative_config=False)
        self.app.config['TESTING'] = True
        self.app.register_blueprint(auth_bp)
        self.app.register_blueprint(deck_bp)
        self.app.register_blueprint(card_bp)
        self.client = self.app.test_client()

    def test_index_get_route(self):
        '''Test the index route of our app'''
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
    
    def test_index_post(self):
        '''Test that the post request to the index route is not allowed'''
        response = self.client.post('/')
        self.assertEqual(response.status_code, 405)

    @patch('src.auth.routes.auth')
    def test_signup_route_registered_user(self, mock_auth):
        '''Test the signup route of our app with a registered user'''
        mock_auth.create_user_with_email_and_password.side_effect = Exception("User already exists")
        
        response = self.client.post(
            '/signup',
            data=json.dumps({'email': 'aaronadb@gmail.com', 'password': 'flashcards123'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        
    @patch('src.auth.routes.auth')
    def test_signup_route_unregistered_user_invalid_email(self, mock_auth):
        '''Test the signup route of our app with an unregistered user using an invalid email address'''
        mock_auth.create_user_with_email_and_password.side_effect = Exception("Invalid email")
        
        response = self.client.post(
            '/signup',
            data=json.dumps({'email': 'test@gmail.com', 'password': 'password123'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)

    @patch('src.auth.routes.auth')
    def test_login_route_registered_user(self, mock_auth):
        '''Test the login route of our app with an already registered user'''
        mock_auth.sign_in_with_email_and_password.return_value = {
            'localId': 'testuid123',
            'email': 'aaronadb@gmail.com',
            'idToken': 'sometoken123'
        }

        response = self.client.post(
            '/login',
            data=json.dumps({
                'email': 'aaronadb@gmail.com',
                'password': 'flashcards123'
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.data.decode())
        self.assertIn('message', response_data)
        self.assertEqual(response_data['message'], 'Login Successful')
        self.assertEqual(response_data['status'], 200)
        
    @patch('src.auth.routes.auth')
    def test_login_route_wrong_password(self, mock_auth):
        '''Test the login route of our app with a registered user with a wrong password'''
        mock_auth.sign_in_with_email_and_password.side_effect = Exception("Invalid password")
        
        response = self.client.post(
            '/login',
            data=json.dumps({
                'email': 'aaronadb@gmail.com',
                'password': 'flashcards'
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.data.decode())
        self.assertEqual(response_data['message'], 'Login Failed')
        
    @patch('src.auth.routes.auth')
    def test_login_route_unregistered_user(self, mock_auth):
        '''Test the login route of our app with an unregistered user'''
        mock_auth.sign_in_with_email_and_password.side_effect = Exception("User not found")
        
        response = self.client.post(
            '/login',
            data=json.dumps({
                'email': 'aarondiasbarreto@gmail.com',
                'password': 'flashcards123'
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.data.decode())
        self.assertEqual(response_data['message'], 'Login Failed')

    @patch('src.auth.routes.auth')
    def test_signup_new_user_success(self, mock_auth):
        '''Test successful signup for a new user'''
        mock_auth.create_user_with_email_and_password.return_value = {
            'localId': 'newuserid123',
            'email': 'newuser@gmail.com'
        }
        
        response = self.client.post(
            '/signup',
            data=json.dumps({
                'email': 'newuser@gmail.com',
                'password': 'newpassword123'
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 201)
        response_data = json.loads(response.data.decode())
        self.assertEqual(response_data['message'], 'Registered Successfully')

if __name__ == "__main__":
    unittest.main()