import unittest
import json
from datetime import datetime, timedelta, timezone
from unittest.mock import patch, MagicMock

from src.api import create_app


class TestStatisticsDashboard(unittest.TestCase):
    """Test cases for the flashcard statistics dashboard feature."""

    def setUp(self):
        """Set up test client and mocked database."""
        self.app = create_app()
        self.client = self.app.test_client()

        # Set up common test variables
        self.test_user_id = "test_user_123"
        self.test_deck_id = "test_deck_456"
        self.test_card_ids = ["card1", "card2", "card3", "card4", "card5"]

        # Mock the database for consistent testing
        self.db_mock = MagicMock()
        self.firebase_patch = patch("src.deck.routes.db", self.db_mock)
        self.firebase_patch.start()

    def tearDown(self):
        """Clean up after each test."""
        self.firebase_patch.stop()

    def setup_mock_cards(self, with_cards=True):
        """Helper to set up mock cards for testing."""
        if with_cards:
            # Mock 5 cards in the deck
            cards_val = {
                "card1": {"front": "Question 1", "back": "Answer 1", "hint": "Hint 1", "deckId": self.test_deck_id},
                "card2": {"front": "Question 2", "back": "Answer 2", "hint": "Hint 2", "deckId": self.test_deck_id},
                "card3": {"front": "Question 3", "back": "Answer 3", "hint": "Hint 3", "deckId": self.test_deck_id},
                "card4": {"front": "Question 4", "back": "Answer 4", "hint": "Hint 4", "deckId": self.test_deck_id},
                "card5": {"front": "Question 5", "back": "Answer 5", "hint": "Hint 5", "deckId": self.test_deck_id},
            }

            # Create mock card query results
            mock_card_results = MagicMock()
            mock_card_results.val.return_value = cards_val

            # Set up card objects to be returned by .each()
            mock_cards = []
            for card_id, card_data in cards_val.items():
                mock_card = MagicMock()
                mock_card.key.return_value = card_id
                mock_card.val.return_value = card_data
                mock_cards.append(mock_card)

            mock_card_results.each.return_value = mock_cards
        else:
            # Empty deck (no cards)
            mock_card_results = MagicMock()
            mock_card_results.val.return_value = None
            mock_card_results.each.return_value = []

        # Set up the database mock for card queries
        mock_card_query = MagicMock()
        mock_card_query.equal_to.return_value = mock_card_results

        self.db_mock.child.return_value.order_by_child.return_value = mock_card_query
        return mock_card_results

    def setup_mock_progress(self, progress_data=None):
        """Helper to set up mock progress data for testing."""
        # Create mock progress reference
        mock_progress_ref = MagicMock()
        mock_progress_ref.val.return_value = progress_data

        # Configure the database mock to return our prepared progress data
        self.db_mock.child.return_value.child.return_value.child.return_value.get.return_value = mock_progress_ref

    def test_empty_deck_statistics(self):
        """Test 1: Get statistics for an empty deck (no cards)."""
        # Set up an empty deck
        self.setup_mock_cards(with_cards=False)
        self.setup_mock_progress({})

        # Make the API request
        response = self.client.get(f"/deck/{self.test_deck_id}/card-statistics/{self.test_user_id}")
        data = json.loads(response.data)

        # Check the response
        self.assertEqual(response.status_code, 200)
        self.assertIn("message", data)
        self.assertEqual(data["message"], "No cards found for this deck")
        self.assertIn("statistics", data)

    def test_unreviewed_cards_statistics(self):
        """Test 2: Get statistics for a deck with unreviewed cards only."""
        # Set up cards
        self.setup_mock_cards()
        # Set up empty progress (no reviews yet)
        self.setup_mock_progress({})

        # Make the API request
        response = self.client.get(f"/deck/{self.test_deck_id}/card-statistics/{self.test_user_id}")
        data = json.loads(response.data)

        # Check the response
        self.assertEqual(response.status_code, 200)
        self.assertIn("statistics", data)
        stats = data["statistics"]

        # Verify statistics for unreviewed cards
        self.assertEqual(stats["total_cards"], 5)
        self.assertEqual(stats["reviewed_cards"], 0)
        self.assertEqual(stats["unreviewed_cards"], 5)
        self.assertEqual(stats["confidence_levels"]["low"], 0)
        self.assertEqual(stats["confidence_levels"]["medium"], 0)
        self.assertEqual(stats["confidence_levels"]["high"], 0)
        self.assertEqual(stats["performance"]["accuracy_rate"], 0)

        # Check card_data array
        self.assertEqual(len(stats["cards_data"]), 5)
        for card in stats["cards_data"]:
            self.assertFalse(card["reviewed"])
            self.assertEqual(card["confidence"], 0)
            self.assertEqual(card["correct_count"], 0)
            self.assertIsNone(card["next_review"])

    def test_reviewed_cards_statistics(self):
        """Test 3: Get statistics for a deck with reviewed cards."""
        # Set up cards
        self.setup_mock_cards()

        # Current time for testing
        now = datetime.now(timezone.utc)
        tomorrow = (now + timedelta(days=1)).isoformat()
        next_week = (now + timedelta(days=7)).isoformat()

        # Mock progress data with reviews
        progress_data = {
            "card1": {
                "interval": 1,
                "repetitions": 1,
                "ease_factor": 2.5,
                "last_review": now.isoformat(),
                "next_review": tomorrow,
                "confidence": 3,
                "correct": 1,
            },
            "card2": {
                "interval": 7,
                "repetitions": 3,
                "ease_factor": 2.7,
                "last_review": now.isoformat(),
                "next_review": next_week,
                "confidence": 4,
                "correct": 3,
            },
        }
        self.setup_mock_progress(progress_data)

        # Make the API request
        response = self.client.get(f"/deck/{self.test_deck_id}/card-statistics/{self.test_user_id}")
        data = json.loads(response.data)

        # Check the response
        self.assertEqual(response.status_code, 200)
        stats = data["statistics"]

        # Verify statistics
        self.assertEqual(stats["total_cards"], 5)
        self.assertEqual(stats["reviewed_cards"], 2)
        self.assertEqual(stats["unreviewed_cards"], 3)

        # Check card data for reviewed cards
        reviewed_cards = [c for c in stats["cards_data"] if c["reviewed"]]
        self.assertEqual(len(reviewed_cards), 2)

    def test_review_schedule_counts(self):
        """Test 4: Verify correct review schedule counts (today, tomorrow, etc.)."""
        # Set up cards
        self.setup_mock_cards()

        # Current time for testing
        now = datetime.now(timezone.utc)
        today = now.isoformat()
        tomorrow = (now + timedelta(days=1)).isoformat()
        this_week = (now + timedelta(days=3)).isoformat()
        next_week = (now + timedelta(days=10)).isoformat()
        later = (now + timedelta(days=30)).isoformat()

        # Mock progress data with different review schedules
        progress_data = {
            "card1": {"next_review": today, "confidence": 2, "correct": 0, "repetitions": 1},
            "card2": {"next_review": tomorrow, "confidence": 3, "correct": 1, "repetitions": 2},
            "card3": {"next_review": this_week, "confidence": 4, "correct": 2, "repetitions": 3},
            "card4": {"next_review": next_week, "confidence": 5, "correct": 3, "repetitions": 4},
            "card5": {"next_review": later, "confidence": 5, "correct": 5, "repetitions": 5},
        }
        self.setup_mock_progress(progress_data)

        # Make the API request
        response = self.client.get(f"/deck/{self.test_deck_id}/card-statistics/{self.test_user_id}")
        data = json.loads(response.data)

        # Check the response
        self.assertEqual(response.status_code, 200)
        stats = data["statistics"]

        # Verify review schedule counts
        schedule = stats["review_schedule"]
        self.assertEqual(schedule["today"], 1)
        self.assertEqual(schedule["tomorrow"], 1)
        self.assertEqual(schedule["this_week"], 1)
        self.assertEqual(schedule["next_week"], 1)
        self.assertEqual(schedule["later"], 1)

    def test_confidence_level_categorization(self):
        """Test 5: Verify confidence level categorization (low, medium, high)."""
        # Set up cards
        self.setup_mock_cards()

        # Mock progress data with different confidence levels
        progress_data = {
            "card1": {"confidence": 0, "next_review": datetime.now(timezone.utc).isoformat(), "repetitions": 1},
            "card2": {"confidence": 1, "next_review": datetime.now(timezone.utc).isoformat(), "repetitions": 1},
            "card3": {"confidence": 2, "next_review": datetime.now(timezone.utc).isoformat(), "repetitions": 1},
            "card4": {"confidence": 3, "next_review": datetime.now(timezone.utc).isoformat(), "repetitions": 1},
            "card5": {"confidence": 5, "next_review": datetime.now(timezone.utc).isoformat(), "repetitions": 1},
        }
        self.setup_mock_progress(progress_data)

        # Make the API request
        response = self.client.get(f"/deck/{self.test_deck_id}/card-statistics/{self.test_user_id}")
        data = json.loads(response.data)

        # Check the response
        stats = data["statistics"]

        # Verify confidence level categorization
        self.assertEqual(stats["confidence_levels"]["low"], 2)  # 0-1 are low
        self.assertEqual(stats["confidence_levels"]["medium"], 2)  # 2-3 are medium
        self.assertEqual(stats["confidence_levels"]["high"], 1)  # 4-5 are high

    def test_performance_metrics(self):
        """Test 6: Verify performance metrics (accuracy rate calculation)."""
        # Set up cards
        self.setup_mock_cards()

        # Mock progress data with different performance metrics
        progress_data = {
            "card1": {"correct": 0, "repetitions": 1, "next_review": datetime.now(timezone.utc).isoformat()},
            "card2": {"correct": 1, "repetitions": 1, "next_review": datetime.now(timezone.utc).isoformat()},
            "card3": {"correct": 2, "repetitions": 2, "next_review": datetime.now(timezone.utc).isoformat()},
            "card4": {"correct": 3, "repetitions": 4, "next_review": datetime.now(timezone.utc).isoformat()},
            "card5": {"correct": 5, "repetitions": 5, "next_review": datetime.now(timezone.utc).isoformat()},
        }
        self.setup_mock_progress(progress_data)

        # Make the API request
        response = self.client.get(f"/deck/{self.test_deck_id}/card-statistics/{self.test_user_id}")
        data = json.loads(response.data)

        # Check the response
        stats = data["statistics"]

        # Calculate expected accuracy rate
        total_correct = 0 + 1 + 2 + 3 + 5
        total_repetitions = 1 + 1 + 2 + 4 + 5
        expected_accuracy = round((total_correct / total_repetitions) * 100, 2)

        # Verify performance metrics
        self.assertEqual(stats["performance"]["correct_count"], total_correct)
        self.assertEqual(stats["performance"]["total_reviews"], total_repetitions)
        self.assertEqual(stats["performance"]["accuracy_rate"], expected_accuracy)

    def test_invalid_deck_id(self):
        """Test 7: Test with invalid deck ID."""
        # Set up mock to return no cards for invalid deck ID
        invalid_deck_id = "nonexistent_deck"

        # Configure card query to return no results
        mock_card_query = MagicMock()
        mock_card_results = MagicMock()
        mock_card_results.val.return_value = None
        mock_card_query.equal_to.return_value = mock_card_results
        self.db_mock.child.return_value.order_by_child.return_value = mock_card_query

        # Make the API request with invalid deck ID
        response = self.client.get(f"/deck/{invalid_deck_id}/card-statistics/{self.test_user_id}")
        data = json.loads(response.data)

        # Check the response for proper error handling
        self.assertEqual(response.status_code, 200)  # API still returns 200 for empty results
        self.assertEqual(data["message"], "No cards found for this deck")
        self.assertIn("statistics", data)

    def test_invalid_user_id(self):
        """Test 8: Test with invalid user ID."""
        # Set up cards
        self.setup_mock_cards()

        # Set up empty progress data for invalid user
        self.setup_mock_progress({})

        # Make the API request with invalid user ID
        invalid_user_id = "nonexistent_user"
        response = self.client.get(f"/deck/{self.test_deck_id}/card-statistics/{invalid_user_id}")
        data = json.loads(response.data)

        # Check the response - should return valid statistics but with all unreviewed cards
        self.assertEqual(response.status_code, 200)
        stats = data["statistics"]
        self.assertEqual(stats["total_cards"], 5)
        self.assertEqual(stats["reviewed_cards"], 0)
        self.assertEqual(stats["unreviewed_cards"], 5)

    def test_after_recording_answers(self):
        """Test 9: Test statistics after recording answers with varying quality levels."""
        # This test simulates recording answers and then checking statistics

        # First, set up cards and initial empty progress
        self.setup_mock_cards()
        self.setup_mock_progress({})

        # Now simulate recording answers by updating progress data
        # In a real test, we would call the record_answer endpoint
        # Here we'll directly update our mock data

        now = datetime.now(timezone.utc)
        updated_progress_data = {
            "card1": {
                "interval": 1,
                "repetitions": 1,
                "ease_factor": 2.5,
                "last_review": now.isoformat(),
                "next_review": (now + timedelta(days=1)).isoformat(),
                "confidence": 0,  # Very low confidence (wrong answer)
                "correct": 0,
            },
            "card2": {
                "interval": 1,
                "repetitions": 2,
                "ease_factor": 2.6,
                "last_review": now.isoformat(),
                "next_review": (now + timedelta(days=1)).isoformat(),
                "confidence": 3,  # Medium confidence (correct answer with hesitation)
                "correct": 1,
            },
            "card3": {
                "interval": 6,
                "repetitions": 3,
                "ease_factor": 2.7,
                "last_review": now.isoformat(),
                "next_review": (now + timedelta(days=6)).isoformat(),
                "confidence": 5,  # High confidence (perfect recall)
                "correct": 3,
            },
        }
        self.setup_mock_progress(updated_progress_data)

        # Make the API request to get updated statistics
        response = self.client.get(f"/deck/{self.test_deck_id}/card-statistics/{self.test_user_id}")
        data = json.loads(response.data)

        # Check the response
        stats = data["statistics"]

        # Verify statistics reflect the recorded answers
        self.assertEqual(stats["reviewed_cards"], 3)
        self.assertEqual(stats["unreviewed_cards"], 2)
        self.assertEqual(stats["confidence_levels"]["low"], 1)  # One card with confidence 0
        self.assertEqual(stats["confidence_levels"]["medium"], 1)  # One card with confidence 3
        self.assertEqual(stats["confidence_levels"]["high"], 1)  # One card with confidence 5

        # Verify performance metrics
        total_correct = 0 + 1 + 3
        total_reviews = 1 + 2 + 3
        expected_accuracy = round((total_correct / total_reviews) * 100, 2)
        self.assertEqual(stats["performance"]["accuracy_rate"], expected_accuracy)

    def test_confidence_review_schedule_relationship(self):
        """Test 10: Test relationship between confidence scores and review schedules."""
        # Set up cards
        self.setup_mock_cards()

        now = datetime.now(timezone.utc)

        # Create progress data where higher confidence leads to longer intervals
        progress_data = {
            "card1": {
                "confidence": 1,  # Low confidence
                "next_review": (now + timedelta(days=1)).isoformat(),  # Short interval
                "repetitions": 1,
                "correct": 0,
            },
            "card2": {
                "confidence": 3,  # Medium confidence
                "next_review": (now + timedelta(days=3)).isoformat(),  # Medium interval
                "repetitions": 2,
                "correct": 1,
            },
            "card3": {
                "confidence": 5,  # High confidence
                "next_review": (now + timedelta(days=14)).isoformat(),  # Long interval
                "repetitions": 3,
                "correct": 3,
            },
        }
        self.setup_mock_progress(progress_data)

        # Make the API request
        response = self.client.get(f"/deck/{self.test_deck_id}/card-statistics/{self.test_user_id}")
        data = json.loads(response.data)

        # Check the response
        stats = data["statistics"]

        # Verify review schedule reflects confidence levels
        # Low confidence card (card1) due tomorrow
        self.assertEqual(stats["review_schedule"]["tomorrow"], 1)

        # Medium confidence card (card2) due this week
        self.assertEqual(stats["review_schedule"]["this_week"], 1)

        # High confidence card (card3) due next week or later
        self.assertEqual(stats["review_schedule"]["next_week"], 1)
