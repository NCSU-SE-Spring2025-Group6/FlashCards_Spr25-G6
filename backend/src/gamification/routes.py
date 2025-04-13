"""routes.py is a file in the gamification folder that implements XP, achievements, levels, and streaks."""

from flask import Blueprint, jsonify, request
from flask_cors import cross_origin
from datetime import datetime, timedelta, timezone
import json
import math

try:
    from .. import firebase
except ImportError:
    from __init__ import firebase


gamification_bp = Blueprint("gamification_bp", __name__)
db = firebase.database()

# XP Constants
XP_REVIEW_CARD = 5  # Base XP for reviewing a card
XP_CORRECT_ANSWER = {
    0: 0,  # Complete blackout
    1: 1,  # Incorrect - Barely recognized
    2: 2,  # Incorrect - But recognized answer
    3: 5,  # Correct - But difficult recall
    4: 8,  # Correct - After some hesitation
    5: 10,  # Perfect recall
}
XP_PERFECT_DECK = 50  # Bonus for completing all cards in a deck with perfect recall
XP_STREAK_MULTIPLIER = 0.1  # 10% XP bonus per day of streak

# Level system constants
XP_PER_LEVEL = 100  # Base XP required for first level
LEVEL_SCALING = 1.5  # How much each level scales in XP requirement

# Achievement IDs and XP rewards
ACHIEVEMENTS = {
    "streak_3_days": {"name": "Learning Rhythm", "description": "Maintain a 3-day study streak", "xp_reward": 30},
    "streak_7_days": {"name": "Weekly Warrior", "description": "Maintain a 7-day study streak", "xp_reward": 100},
    "streak_30_days": {"name": "Monthly Master", "description": "Maintain a 30-day study streak", "xp_reward": 500},
    "perfect_recall_10": {"name": "Memory Novice", "description": "Get perfect recall on 10 cards", "xp_reward": 50},
    "perfect_recall_50": {"name": "Memory Expert", "description": "Get perfect recall on 50 cards", "xp_reward": 200},
    "perfect_recall_100": {"name": "Memory Master", "description": "Get perfect recall on 100 cards", "xp_reward": 500},
    "complete_deck": {"name": "Deck Complete", "description": "Complete your first deck", "xp_reward": 100},
    "complete_5_decks": {"name": "Deck Collector", "description": "Complete 5 different decks", "xp_reward": 300},
    "first_quiz": {"name": "Quiz Taker", "description": "Complete your first quiz", "xp_reward": 50},
    "perfect_quiz": {"name": "Perfect Quiz", "description": "Get a perfect score on a quiz", "xp_reward": 100},
}


def calculate_level(xp):
    """Calculate user level based on XP"""
    if xp == 0:
        return 0

    # Formula: level = log(xp/base_xp, scaling_factor) + 1
    # This creates increasing XP requirements per level
    return min(100, math.floor(math.log(xp / XP_PER_LEVEL, LEVEL_SCALING) + 1))


def xp_for_next_level(current_level):
    """Calculate XP needed for next level"""
    return math.floor(XP_PER_LEVEL * (LEVEL_SCALING**current_level))


@gamification_bp.route("/gamification/profile/<user_id>", methods=["GET"])
@cross_origin(supports_credentials=True)
def get_profile(user_id):
    """Get or create a user's gamification profile"""
    try:
        # Try to get existing profile
        profile_ref = db.child("user_gamification").child(user_id).get()

        if profile_ref.val():
            # Profile exists, return it
            profile = profile_ref.val()

            # Calculate current level and next level XP
            current_xp = profile.get("xp", 0)
            current_level = calculate_level(current_xp)
            next_level_xp = xp_for_next_level(current_level)

            # Add calculated values to profile
            profile["level"] = current_level
            profile["next_level_xp"] = next_level_xp
            profile["xp_progress"] = (
                current_xp - xp_for_next_level(current_level - 1) if current_level > 0 else current_xp
            )
            profile["xp_needed"] = (
                next_level_xp - xp_for_next_level(current_level - 1) if current_level > 0 else next_level_xp
            )

            return jsonify(
                {"profile": profile, "message": "Gamification profile retrieved successfully", "status": 200}
            ), 200
        else:
            # Profile doesn't exist, create new one
            new_profile = {
                "xp": 0,
                "achievements": {},
                "streak": {"current_streak": 0, "longest_streak": 0, "last_activity_date": None},
                "stats": {"cards_reviewed": 0, "perfect_recalls": 0, "decks_completed": 0, "quizzes_completed": 0},
            }

            # Store new profile
            db.child("user_gamification").child(user_id).set(new_profile)

            # Add level info for frontend
            new_profile["level"] = 0
            new_profile["next_level_xp"] = XP_PER_LEVEL
            new_profile["xp_progress"] = 0
            new_profile["xp_needed"] = XP_PER_LEVEL

            return jsonify({"profile": new_profile, "message": "New gamification profile created", "status": 201}), 201

    except Exception as e:
        return jsonify({"message": f"Error retrieving gamification profile: {str(e)}", "status": 400}), 400


@gamification_bp.route("/gamification/record-activity/<user_id>", methods=["POST"])
@cross_origin(supports_credentials=True)
def record_activity(user_id):
    """Record user activity and update streak"""
    try:
        # Get profile or create if it doesn't exist
        profile_ref = db.child("user_gamification").child(user_id)
        profile = profile_ref.get().val()

        if not profile:
            # Create new profile if it doesn't exist
            profile = {
                "xp": 0,
                "achievements": {},
                "streak": {"current_streak": 0, "longest_streak": 0, "last_activity_date": None},
                "stats": {"cards_reviewed": 0, "perfect_recalls": 0, "decks_completed": 0, "quizzes_completed": 0},
            }

        # Get current date in user's timezone (from request) or UTC
        data = request.get_json() or {}
        user_timezone = data.get("timezone", "UTC")
        current_date = datetime.now(timezone.utc).astimezone(timezone(user_timezone))
        current_date_str = current_date.strftime("%Y-%m-%d")

        streak_data = profile.get("streak", {})
        last_activity_date = streak_data.get("last_activity_date")
        current_streak = streak_data.get("current_streak", 0)
        longest_streak = streak_data.get("longest_streak", 0)

        # If this is first activity ever
        if not last_activity_date:
            current_streak = 1
            longest_streak = 1
        else:
            # Parse last activity date
            last_date = datetime.strptime(last_activity_date, "%Y-%m-%d").date()
            current_date_only = current_date.date()

            # Calculate days difference
            days_diff = (current_date_only - last_date).days

            # Same day - no streak update
            if days_diff == 0:
                pass
            # Next day - increment streak
            elif days_diff == 1:
                current_streak += 1
                longest_streak = max(longest_streak, current_streak)
            # Missed a day or more - reset streak
            else:
                current_streak = 1

        # Update streak data
        profile["streak"] = {
            "current_streak": current_streak,
            "longest_streak": longest_streak,
            "last_activity_date": current_date_str,
        }

        # Update profile
        profile_ref.update(profile)

        # Check for streak achievements
        achievements_earned = []

        if current_streak >= 3 and not profile.get("achievements", {}).get("streak_3_days"):
            achievements_earned.append(self_award_achievement(user_id, "streak_3_days"))

        if current_streak >= 7 and not profile.get("achievements", {}).get("streak_7_days"):
            achievements_earned.append(self_award_achievement(user_id, "streak_7_days"))

        if current_streak >= 30 and not profile.get("achievements", {}).get("streak_30_days"):
            achievements_earned.append(self_award_achievement(user_id, "streak_30_days"))

        # Return updated streak info
        return jsonify(
            {
                "streak": profile["streak"],
                "achievements_earned": achievements_earned,
                "message": "Activity recorded successfully",
                "status": 200,
            }
        ), 200

    except Exception as e:
        return jsonify({"message": f"Error recording activity: {str(e)}", "status": 400}), 400


@gamification_bp.route("/gamification/award-xp/<user_id>", methods=["POST"])
@cross_origin(supports_credentials=True)
def award_xp(user_id):
    """Award XP to a user with various activity types"""
    try:
        data = request.get_json()
        activity_type = data.get("activity_type")
        metadata = data.get("metadata", {})

        if not activity_type:
            return jsonify({"message": "Activity type is required", "status": 400}), 400

        # Get user profile
        profile_ref = db.child("user_gamification").child(user_id)
        profile = profile_ref.get().val() or {
            "xp": 0,
            "achievements": {},
            "streak": {"current_streak": 0, "longest_streak": 0, "last_activity_date": None},
            "stats": {"cards_reviewed": 0, "perfect_recalls": 0, "decks_completed": 0, "quizzes_completed": 0},
        }

        # Base XP to award
        xp_earned = 0
        achievements_earned = []

        # Calculate XP based on activity type
        if activity_type == "review_card":
            # Get quality rating (0-5)
            quality = metadata.get("quality", 0)

            # Base XP for reviewing
            xp_earned = XP_REVIEW_CARD

            # Additional XP based on quality
            quality_xp = XP_CORRECT_ANSWER.get(quality, 0)
            xp_earned += quality_xp

            # Streak multiplier (if any)
            current_streak = profile.get("streak", {}).get("current_streak", 0)
            if current_streak > 1:
                # Apply streak bonus (up to 50% more XP at 5 day streak)
                streak_bonus = min(0.5, current_streak * XP_STREAK_MULTIPLIER)
                xp_earned = math.ceil(xp_earned * (1 + streak_bonus))

            # Update stats
            profile["stats"]["cards_reviewed"] = profile.get("stats", {}).get("cards_reviewed", 0) + 1

            # Track perfect recalls
            if quality == 5:
                perfect_recalls = profile.get("stats", {}).get("perfect_recalls", 0) + 1
                profile["stats"]["perfect_recalls"] = perfect_recalls

                # Check for perfect recall achievements
                if perfect_recalls >= 10 and not profile.get("achievements", {}).get("perfect_recall_10"):
                    achievements_earned.append(self_award_achievement(user_id, "perfect_recall_10"))

                if perfect_recalls >= 50 and not profile.get("achievements", {}).get("perfect_recall_50"):
                    achievements_earned.append(self_award_achievement(user_id, "perfect_recall_50"))

                if perfect_recalls >= 100 and not profile.get("achievements", {}).get("perfect_recall_100"):
                    achievements_earned.append(self_award_achievement(user_id, "perfect_recall_100"))

        elif activity_type == "complete_deck":
            xp_earned = XP_PERFECT_DECK

            # Update stats
            decks_completed = profile.get("stats", {}).get("decks_completed", 0) + 1
            profile["stats"]["decks_completed"] = decks_completed

            # Check for deck completion achievements
            if decks_completed == 1 and not profile.get("achievements", {}).get("complete_deck"):
                achievements_earned.append(self_award_achievement(user_id, "complete_deck"))

            if decks_completed >= 5 and not profile.get("achievements", {}).get("complete_5_decks"):
                achievements_earned.append(self_award_achievement(user_id, "complete_5_decks"))

        elif activity_type == "complete_quiz":
            # Get quiz score
            score = metadata.get("score", 0)
            total = metadata.get("total", 0)

            # Base XP for completing quiz
            xp_earned = 20

            # Bonus XP for good scores
            if total > 0:
                score_percent = score / total
                if score_percent == 1.0:  # Perfect score
                    xp_earned += 30

                    # Award perfect quiz achievement
                    if not profile.get("achievements", {}).get("perfect_quiz"):
                        achievements_earned.append(self_award_achievement(user_id, "perfect_quiz"))

                elif score_percent >= 0.9:  # 90%+ score
                    xp_earned += 20
                elif score_percent >= 0.8:  # 80%+ score
                    xp_earned += 10

            # Update stats
            quizzes_completed = profile.get("stats", {}).get("quizzes_completed", 0) + 1
            profile["stats"]["quizzes_completed"] = quizzes_completed

            # First quiz achievement
            if quizzes_completed == 1 and not profile.get("achievements", {}).get("first_quiz"):
                achievements_earned.append(self_award_achievement(user_id, "first_quiz"))

        # Update user's XP
        current_xp = profile.get("xp", 0)
        new_xp = current_xp + xp_earned
        profile["xp"] = new_xp

        # Calculate levels
        old_level = calculate_level(current_xp)
        new_level = calculate_level(new_xp)
        level_up = new_level > old_level

        # Update the profile
        profile_ref.update(profile)

        # Add calculated level data
        profile["level"] = new_level
        profile["next_level_xp"] = xp_for_next_level(new_level)
        profile["xp_progress"] = new_xp - xp_for_next_level(new_level - 1) if new_level > 0 else new_xp
        profile["xp_needed"] = (
            xp_for_next_level(new_level) - xp_for_next_level(new_level - 1)
            if new_level > 0
            else xp_for_next_level(new_level)
        )

        return jsonify(
            {
                "xp_earned": xp_earned,
                "new_xp": new_xp,
                "level": new_level,
                "level_up": level_up,
                "achievements_earned": achievements_earned,
                "profile": profile,
                "message": "XP awarded successfully",
                "status": 200,
            }
        ), 200

    except Exception as e:
        return jsonify({"message": f"Error awarding XP: {str(e)}", "status": 400}), 400


@gamification_bp.route("/gamification/achievements/<user_id>", methods=["GET"])
@cross_origin(supports_credentials=True)
def get_achievements(user_id):
    """Get all achievements for a user"""
    try:
        # Validate user_id
        if not user_id:
            return jsonify(
                {
                    "achievements": {},
                    "available_achievements": ACHIEVEMENTS,
                    "message": "Invalid user ID",
                    "status": 200,
                }
            ), 200

        # Ensure user gamification profile exists
        profile_ref = db.child("user_gamification").child(user_id)
        profile = profile_ref.get().val()

        # If no profile exists, create a default one
        if not profile:
            # Return empty achievements but available ones
            return jsonify(
                {
                    "achievements": {},
                    "available_achievements": ACHIEVEMENTS,
                    "message": "No achievements found for this user",
                    "status": 200,
                }
            ), 200

        # Get achievements from profile
        user_achievements = profile.get("achievements", {})

        # Return both unlocked achievements and all available achievements
        return jsonify(
            {
                "achievements": user_achievements,
                "available_achievements": ACHIEVEMENTS,
                "message": "Achievements retrieved successfully",
                "status": 200,
            }
        ), 200

    except Exception as e:
        print(f"Error getting achievements: {str(e)}")
        # Return available achievements even on error
        return jsonify(
            {
                "achievements": {},
                "available_achievements": ACHIEVEMENTS,
                "message": f"Error retrieving achievements: {str(e)}",
                "status": 200,  # Return 200 instead of 400 to avoid breaking the UI
            }
        ), 200


@gamification_bp.route("/gamification/leaderboard", methods=["GET"])
@cross_origin(supports_credentials=True)
def get_xp_leaderboard():
    """Get global XP leaderboard"""
    try:
        # Get all user profiles
        all_profiles = db.child("user_gamification").get()

        if not all_profiles.val():
            return jsonify({"leaderboard": [], "message": "No users found", "status": 200}), 200

        # Build leaderboard data
        leaderboard = []
        for user_id, profile in all_profiles.val().items():
            # Get user email from auth if available
            user_email = "Unknown"
            try:
                user_data = db.child("users").child(user_id).get().val()
                if user_data:
                    user_email = user_data.get("email", "User-" + user_id[:5])
            except:
                pass

            xp = profile.get("xp", 0)
            level = calculate_level(xp)

            leaderboard.append(
                {
                    "user_id": user_id,
                    "user_email": user_email,
                    "xp": xp,
                    "level": level,
                    "achievements_count": len(profile.get("achievements", {})),
                }
            )

        # Sort by XP (descending)
        leaderboard.sort(key=lambda x: x["xp"], reverse=True)

        # Add rank
        for i, entry in enumerate(leaderboard):
            entry["rank"] = i + 1

        return jsonify(
            {"leaderboard": leaderboard, "message": "Leaderboard retrieved successfully", "status": 200}
        ), 200

    except Exception as e:
        return jsonify({"message": f"Error retrieving leaderboard: {str(e)}", "status": 400}), 400


def self_award_achievement(user_id, achievement_id):
    """Helper function to award an achievement to a user"""
    if achievement_id not in ACHIEVEMENTS:
        return None

    achievement = ACHIEVEMENTS[achievement_id]
    achievement_data = {
        "id": achievement_id,
        "name": achievement["name"],
        "description": achievement["description"],
        "date_earned": datetime.now(timezone.utc).isoformat(),
        "xp_awarded": achievement["xp_reward"],
    }

    # Get user profile
    profile_ref = db.child("user_gamification").child(user_id)
    profile = profile_ref.get().val() or {"xp": 0, "achievements": {}}

    # Add achievement if not already earned
    if achievement_id not in profile.get("achievements", {}):
        # Update achievements
        if "achievements" not in profile:
            profile["achievements"] = {}
        profile["achievements"][achievement_id] = achievement_data

        # Award XP
        profile["xp"] = profile.get("xp", 0) + achievement["xp_reward"]

        # Update profile
        profile_ref.update(profile)

        return achievement_data

    return None
