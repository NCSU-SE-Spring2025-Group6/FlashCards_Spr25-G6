
from flask import Flask
import sys
sys.path.append('backend/src')
import unittest
import json
import pytest
from unittest.mock import patch
from src.auth.routes import auth_bp
from src.deck.routes import deck_bp
from src.cards.routes import card_bp
from pathlib import Path

# Add the parent directory to sys.path
sys.path.append(str(Path(__file__).parent.parent))

class CardTestApp(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = Flask(__name__, instance_relative_config=False)
        cls.app.config['TESTING'] = True
        cls.app.register_blueprint(deck_bp)
        cls.app.register_blueprint(card_bp)
        cls.app.register_blueprint(auth_bp)
        cls.client = cls.app.test_client()

    def setUp(self):
        # Setup for each test method
        pass

    @patch('src.auth.routes.auth')
    @patch('src.deck.routes.db')
    @patch('src.cards.routes.db')
    def test_deck_card_all_route(self, mock_cards_db, mock_deck_db, mock_auth):
        '''Test the deck/card/all route of our app'''
        # Mock authentication
        mock_auth.sign_in_with_email_and_password.return_value = {
            'localId': 'Test',
            'idToken': 'some_token'
        }

        # Login
        self.client.post(
            '/login',
            data=json.dumps({
                'email': 'aaronadb@gmail.com',
                'password': 'flashcards123'
            }),
            content_type='application/json'
        )

        # Create deck
        self.client.post(
            '/deck/create',
            data=json.dumps({
                'localId': 'Test',
                'title': 'TestDeck',
                'description': 'This is a test deck',
                'visibility': 'public'
            }),
            content_type='application/json'
        )

        # Test get cards
        response = self.client.get('/deck/Test/card/all')
        self.assertEqual(response.status_code, 200)

    @patch('src.auth.routes.auth')
    @patch('src.deck.routes.db')
    def test_deck_card_all_route_post(self, mock_deck_db, mock_auth):
        '''Test that the post request to the '/deck/card/all' route is not allowed'''
        # Mock authentication
        mock_auth.sign_in_with_email_and_password.return_value = {
            'localId': 'Test',
            'idToken': 'some_token'
        }

        # Login
        self.client.post(
            '/login',
            data=json.dumps({
                'email': 'aaronadb@gmail.com',
                'password': 'flashcards123'
            }),
            content_type='application/json'
        )

        # Create deck
        self.client.post(
            '/deck/create',
            data=json.dumps({
                'localId': 'Test',
                'title': 'TestDeck',
                'description': 'This is a test deck',
                'visibility': 'public'
            }),
            content_type='application/json'
        )

        # Test post request to card/all
        response = self.client.post('/deck/Test/card/all')
        self.assertEqual(response.status_code, 405)

    @patch('src.auth.routes.auth')
    @patch('src.deck.routes.db')
    @patch('src.cards.routes.db')
    def test_deck_create_card_route(self, mock_cards_db, mock_deck_db, mock_auth):
        '''Test the create card in a deck route of our app'''
        # Mock authentication
        mock_auth.sign_in_with_email_and_password.return_value = {
            'localId': 'Test',
            'idToken': 'some_token'
        }

        # Mock database responses
        mock_cards_db.child.return_value.push.return_value = {'name': 'test_card_id'}

        # Login
        self.client.post(
            '/login',
            data=json.dumps({
                'email': 'aaronadb@gmail.com',
                'password': 'flashcards123'
            }),
            content_type='application/json'
        )

        # Create deck
        self.client.post(
            '/deck/create',
            data=json.dumps({
                'localId': 'Test',
                'title': 'TestDeck',
                'description': 'This is a test deck',
                'visibility': 'public'
            }),
            content_type='application/json'
        )

        # Create card
        response = self.client.post(
            '/deck/Test/card/create',
            data=json.dumps({
                'localId': 'Test',
                'cards': [{'front': 'front', 'back': 'back', 'hint': 'hint'}]
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 201)

    @patch('src.auth.routes.auth')
    @patch('src.deck.routes.db')
    @patch('src.cards.routes.db')
    def test_get_cards_exception(self, mock_cards_db, mock_deck_db, mock_auth):
        '''Test the error handling of getcards method'''
        # Mock database to raise an exception
        mock_cards_db.child.return_value.order_by_child.return_value.equal_to.side_effect = Exception("Database error")

        response = self.client.get('/deck/Test/card/all')
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertEqual(data['cards'], [])
        self.assertTrue('An error occurred' in data['message'])

    @patch('src.auth.routes.auth')
    @patch('src.deck.routes.db')
    @patch('src.cards.routes.db')
    def test_create_cards_exception(self, mock_cards_db, mock_deck_db, mock_auth):
        '''Test the error handling of createcards method'''
        # Mock database to raise an exception
        mock_cards_db.child.return_value.push.side_effect = Exception("Database error")

        response = self.client.post(
            '/deck/Test/card/create',
            data=json.dumps({
                'localId': 'Test',
                'cards': [{'front': 'front', 'back': 'back', 'hint': 'hint'}]
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertEqual(data['message'], 'Adding cards Failed')

    @patch('src.auth.routes.auth')
    @patch('src.deck.routes.db')
    @patch('src.cards.routes.db')
    def test_update_card(self, mock_cards_db, mock_deck_db, mock_auth):
        '''Test the update card functionality'''
        response = self.client.patch(
            '/deck/test_deck/update/test_card',
            data=json.dumps({
                'word': 'updated_word',
                'meaning': 'updated_meaning'
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertEqual(data['message'], 'Update Card Successful')

    @patch('src.auth.routes.auth')
    @patch('src.deck.routes.db')
    @patch('src.cards.routes.db')
    def test_update_card_exception(self, mock_cards_db, mock_deck_db, mock_auth):
        '''Test error handling in update card functionality'''
        # Mock database to raise an exception
        mock_cards_db.child.return_value.order_by_child.return_value.equal_to.side_effect = Exception("Database error")

        response = self.client.patch(
            '/deck/test_deck/update/test_card',
            data=json.dumps({
                'word': 'updated_word',
                'meaning': 'updated_meaning'
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertTrue('Update Card Failed' in data['message'])

    # @patch('src.auth.routes.auth')
    # @patch('src.deck.routes.db')
    # @patch('src.cards.routes.db')
    # def test_delete_card(self, mock_cards_db, mock_deck_db, mock_auth):
    #     '''Test the delete card functionality'''
    #     response = self.client.delete('/deck/test_deck/delete/test_card')
        
    #     self.assertEqual(response.status_code, 200)
    #     data = json.loads(response.data)
    #     self.assertEqual(data['message'], 'Delete Card Successful')

    @patch('src.auth.routes.auth')
    @patch('src.deck.routes.db')
    @patch('src.cards.routes.db')
    def test_delete_card_exception(self, mock_cards_db, mock_deck_db, mock_auth):
        '''Test error handling in delete card functionality'''
        # Mock database to raise an exception
        mock_cards_db.child.return_value.order_by_child.return_value.equal_to.side_effect = Exception("Database error")

        response = self.client.delete('/deck/test_deck/delete/test_card')
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertEqual(data['message'], 'Delete Card Failed')

    def test_invalid_methods(self):
        '''Test invalid HTTP methods for routes'''
        # Test PUT method on card/all route
        response = self.client.put('/deck/Test/card/all')
        self.assertEqual(response.status_code, 405)

        # Test DELETE method on card/create route
        response = self.client.delete('/deck/Test/card/create')
        self.assertEqual(response.status_code, 405)

if __name__ == "__main__":
    unittest.main()