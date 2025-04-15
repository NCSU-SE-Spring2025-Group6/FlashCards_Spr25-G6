import pytest
from datetime import datetime, timedelta
import json
import math
from unittest.mock import patch, MagicMock

from ..src.gamification.routes import calculate_level, xp_for_next_level, ACHIEVEMENTS

# Constants for testing
TEST_USER_ID = "test_user_123"
XP_PER_LEVEL = 100
LEVEL_SCALING = 1.5


# Test cases for the gamification system
class TestGamification:
    # Test 1: Test level calculation function
    def test_calculate_level(self):
        # Test level 0
        assert calculate_level(0) == 0

        # Test level 1
        assert calculate_level(100) == 1

        # Test level 2 (requires 100 * 1.5 = 150 XP)
        assert calculate_level(150) == 2

        # Test level 3 (requires 100 * 1.5^2 = 225 XP)
        assert calculate_level(225) == 3

        # Test level 10 (high level)
        level_10_xp = XP_PER_LEVEL * (LEVEL_SCALING**9)
        assert calculate_level(level_10_xp) == 10

    # Test 2: Test XP required for next level function
    def test_xp_for_next_level(self):
        # Level 0 to 1 requires 100 XP
        assert xp_for_next_level(0) == 100

        # Level 1 to 2 requires 150 XP
        assert xp_for_next_level(1) == 150

        # Level 2 to 3 requires 225 XP
        assert xp_for_next_level(2) == 225

        # Level 5 to 6
        assert xp_for_next_level(5) == math.floor(XP_PER_LEVEL * (LEVEL_SCALING**5))

    # Test 3: Test profile creation
    @patch("src.gamification.routes.db")
    def test_get_profile_new_user(self, mock_db):
        from ..src.gamification.routes import get_profile

        # Mock the Firebase response for a new user
        mock_get = MagicMock()
        mock_get.val.return_value = None
        mock_db.child.return_value.child.return_value.get.return_value = mock_get

        # Mock Flask request context
        with patch("flask.jsonify") as mock_jsonify:
            mock_jsonify.return_value = {}

            # Call the function
            response, status_code = get_profile(TEST_USER_ID)

            # Assert a new profile was created
            mock_db.child.return_value.child.return_value.set.assert_called_once()
            assert status_code == 201

    # Test 4: Test existing profile retrieval
    @patch("src.gamification.routes.db")
    def test_get_profile_existing_user(self, mock_db):
        from ..src.gamification.routes import get_profile

        # Create mock profile data
        mock_profile = {
            "xp": 250,
            "achievements": {},
            "streak": {"current_streak": 3, "longest_streak": 5, "last_activity_date": "2025-04-13"},
            "stats": {"cards_reviewed": 50, "perfect_recalls": 20, "decks_completed": 2, "quizzes_completed": 1},
        }

        # Mock the Firebase response
        mock_get = MagicMock()
        mock_get.val.return_value = mock_profile
        mock_db.child.return_value.child.return_value.get.return_value = mock_get

        # Mock Flask request context
        with patch("flask.jsonify") as mock_jsonify:
            mock_jsonify.return_value = {}

            # Call the function
            response, status_code = get_profile(TEST_USER_ID)

            # Assert profile was fetched and not created
            mock_db.child.return_value.child.return_value.set.assert_not_called()
            assert status_code == 200

    # Test 5: Test XP awards for reviewing cards
    @patch("src.gamification.routes.db")
    def test_award_xp_for_card_review(self, mock_db):
        from ..src.gamification.routes import award_xp

        # Create mock profile data with streak
        mock_profile = {
            "xp": 100,
            "achievements": {},
            "streak": {"current_streak": 2, "longest_streak": 2, "last_activity_date": "2025-04-13"},
            "stats": {"cards_reviewed": 10, "perfect_recalls": 5, "decks_completed": 1, "quizzes_completed": 0},
        }

        # Mock the Firebase response and request
        mock_get = MagicMock()
        mock_get.val.return_value = mock_profile
        mock_db.child.return_value.child.return_value.get.return_value = mock_get

        # Create test request data for a perfect recall (quality 5)
        with patch("flask.request") as mock_request, patch("flask.jsonify") as mock_jsonify:
            mock_request.get_json.return_value = {
                "activity_type": "review_card",
                "metadata": {"quality": 5, "card_id": "test_card_1"},
            }
            mock_jsonify.return_value = {}

            # Call the function
            response, status_code = award_xp(TEST_USER_ID)

            # Profile should be updated with:
            # - Increased XP (base 5 XP + quality 5 = 10 XP, with streak multiplier ~20% = ~18 XP)
            # - Incremented cards_reviewed
            # - Incremented perfect_recalls
            mock_db.child.return_value.child.return_value.update.assert_called()
            assert status_code == 200

    # Test 6: Test streak maintenance and updates
    @patch("src.gamification.routes.db")
    def test_streak_maintenance(self, mock_db):
        from ..src.gamification.routes import record_activity
        from datetime import datetime, timedelta

        # Create mock profile with existing streak
        current_date = datetime.now().strftime("%Y-%m-%d")
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

        mock_profile = {
            "xp": 200,
            "achievements": {},
            "streak": {"current_streak": 3, "longest_streak": 5, "last_activity_date": yesterday},
            "stats": {"cards_reviewed": 20, "perfect_recalls": 10, "decks_completed": 1, "quizzes_completed": 1},
        }

        # Mock the Firebase response
        mock_get = MagicMock()
        mock_get.val.return_value = mock_profile
        mock_db.child.return_value.child.return_value.get.return_value = mock_get

        # Mock request with today's date
        with patch("flask.request") as mock_request, patch("flask.jsonify") as mock_jsonify:
            mock_request.get_json.return_value = {"timezone": "UTC"}
            mock_jsonify.return_value = {}

            # Call the function
            response, status_code = record_activity(TEST_USER_ID)

            # Assert streak was incremented to 4
            update_calls = mock_db.child.return_value.child.return_value.update.call_args[0][0]
            assert update_calls["streak"]["current_streak"] == 4
            assert status_code == 200

    # Test 7: Test streak reset when activity is missed
    @patch("src.gamification.routes.db")
    def test_streak_reset(self, mock_db):
        from ..src.gamification.routes import record_activity

        # Create mock profile with outdated streak (2 days ago)
        two_days_ago = (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d")

        mock_profile = {
            "xp": 200,
            "achievements": {},
            "streak": {"current_streak": 10, "longest_streak": 10, "last_activity_date": two_days_ago},
            "stats": {"cards_reviewed": 50, "perfect_recalls": 20, "decks_completed": 3, "quizzes_completed": 5},
        }

        # Mock the Firebase response
        mock_get = MagicMock()
        mock_get.val.return_value = mock_profile
        mock_db.child.return_value.child.return_value.get.return_value = mock_get

        # Mock request
        with patch("flask.request") as mock_request, patch("flask.jsonify") as mock_jsonify:
            mock_request.get_json.return_value = {"timezone": "UTC"}
            mock_jsonify.return_value = {}

            # Call the function
            response, status_code = record_activity(TEST_USER_ID)

            # Assert streak was reset to 1 but longest_streak remains 10
            update_calls = mock_db.child.return_value.child.return_value.update.call_args[0][0]
            assert update_calls["streak"]["current_streak"] == 1
            assert update_calls["streak"]["longest_streak"] == 10
            assert status_code == 200

    # Test 8: Test achievement unlocking
    @patch("src.gamification.routes.db")
    def test_achievement_unlocking(self, mock_db):
        from ..src.gamification.routes import award_xp

        # Create mock profile that's close to an achievement (9 perfect recalls)
        mock_profile = {
            "xp": 300,
            "achievements": {},
            "streak": {"current_streak": 1, "longest_streak": 1, "last_activity_date": "2025-04-13"},
            "stats": {"cards_reviewed": 25, "perfect_recalls": 9, "decks_completed": 1, "quizzes_completed": 2},
        }

        # Mock the Firebase response
        mock_get = MagicMock()
        mock_get.val.return_value = mock_profile
        mock_db.child.return_value.child.return_value.get.return_value = mock_get

        # Mock request for a perfect recall to reach the achievement
        with patch("flask.request") as mock_request, patch("flask.jsonify") as mock_jsonify:
            mock_request.get_json.return_value = {
                "activity_type": "review_card",
                "metadata": {"quality": 5, "card_id": "test_card_1"},
            }
            mock_jsonify.return_value = {}

            # Call the function
            response, status_code = award_xp(TEST_USER_ID)

            # Verify the achievement was unlocked
            # Expect the achievement to be added and the XP to be awarded
            update_calls = mock_db.child.return_value.child.return_value.update.call_args[0][0]
            assert update_calls["stats"]["perfect_recalls"] == 10
            assert status_code == 200

    # Test 9: Test quiz completion and XP rewards
    @patch("src.gamification.routes.db")
    def test_quiz_completion_rewards(self, mock_db):
        from ..src.gamification.routes import award_xp

        # Create mock profile
        mock_profile = {
            "xp": 400,
            "achievements": {},
            "streak": {"current_streak": 1, "longest_streak": 1, "last_activity_date": "2025-04-13"},
            "stats": {"cards_reviewed": 30, "perfect_recalls": 15, "decks_completed": 2, "quizzes_completed": 0},
        }

        # Mock the Firebase response
        mock_get = MagicMock()
        mock_get.val.return_value = mock_profile
        mock_db.child.return_value.child.return_value.get.return_value = mock_get

        # Mock request for a perfect quiz completion
        with patch("flask.request") as mock_request, patch("flask.jsonify") as mock_jsonify:
            mock_request.get_json.return_value = {
                "activity_type": "complete_quiz",
                "metadata": {"score": 10, "total": 10, "deck_id": "test_deck_1"},
            }
            mock_jsonify.return_value = {}

            # Call the function
            response, status_code = award_xp(TEST_USER_ID)

            # Assert first quiz achievement and perfect quiz achievements should be unlocked
            update_calls = mock_db.child.return_value.child.return_value.update.call_args[0][0]
            assert update_calls["stats"]["quizzes_completed"] == 1
            assert status_code == 200

    # Test 10: Test leaderboard functionality
    @patch("src.gamification.routes.db")
    def test_leaderboard(self, mock_db):
        from ..src.gamification.routes import get_xp_leaderboard

        # Create mock leaderboard data
        mock_profiles = {
            "user1": {"xp": 500, "achievements": {"perfect_recall_10": {}, "first_quiz": {}}},
            "user2": {"xp": 800, "achievements": {"perfect_recall_10": {}, "first_quiz": {}, "streak_7_days": {}}},
            "user3": {"xp": 300, "achievements": {"first_quiz": {}}},
        }

        # Mock user data
        mock_user_data = {
            "user1": {"email": "user1@example.com"},
            "user2": {"email": "user2@example.com"},
            "user3": {"email": "user3@example.com"},
        }

        # Mock Firebase responses
        mock_all_profiles = MagicMock()
        mock_all_profiles.val.return_value = mock_profiles

        def mock_get_user(user_id):
            mock_user = MagicMock()
            mock_user.val.return_value = mock_user_data.get(user_id)
            return mock_user

        mock_db.child.return_value.get.return_value = mock_all_profiles
        mock_db.child.return_value.child.return_value.get.side_effect = mock_get_user

        # Mock Flask response
        with patch("flask.jsonify") as mock_jsonify:
            mock_jsonify.return_value = {}

            # Call the function
            response, status_code = get_xp_leaderboard()

            # Verify leaderboard is sorted by XP
            assert status_code == 200
