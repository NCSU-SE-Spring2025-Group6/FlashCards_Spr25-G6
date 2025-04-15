"""routes.py is a file in the user folder that has all the functions defined that manipulate the user."""

from flask import Blueprint, jsonify  # type: ignore
from flask_cors import cross_origin  # type: ignore
# from __init__ import firebase

try:
    from .. import firebase
except ImportError:
    from __init__ import firebase

user_bp = Blueprint("user_bp", __name__)

db = firebase.database()

user_bp.route("/user/<user_id>/stats", methods=["GET"])

@user_bp.route('/user/<user_id>/stats', methods=['GET'])
@cross_origin(supports_credentials=True)
def get_user_stats(user_id):
    """Fetch aggregated user performance across all decks."""
    try:
        leaderboard_entries = db.child("leaderboard").get()
        total_correct = 0
        total_incorrect = 0
        total_decks = 0

        if leaderboard_entries.val():
            for deck in leaderboard_entries.each():
                deck_data = deck.val()
                if user_id in deck_data:
                    user_data = deck_data[user_id]
                    total_correct += user_data.get("correct", 0)
                    total_incorrect += user_data.get("incorrect", 0)
                    total_decks += 1

        return jsonify(
            {
                "total_correct": total_correct,
                "total_incorrect": total_incorrect,
                "total_decks": total_decks,
                "message": "User statistics fetched successfully",
                "status": 200,
            }
        ), 200
    except Exception as e:
        return jsonify({"message": f"Error fetching user stats: {e}", "status": 400}), 400


@user_bp.route("/user/<user_id>/progress", methods=["GET"])
@cross_origin(supports_credentials=True)
def get_user_progress(user_id):
    """Fetch user's progress over time across all decks."""
    try:
        leaderboard_entries = db.child("leaderboard").get()
        progress_data = []

        if leaderboard_entries.val():
            for deck in leaderboard_entries.each():
                deck_data = deck.val()
                if user_id in deck_data:
                    user_data = deck_data[user_id]
                    progress_data.append(
                        {
                            "deckId": deck.key(),
                            "correct": user_data.get("correct", 0),
                            "incorrect": user_data.get("incorrect", 0),
                            "lastAttempt": user_data.get("lastAttempt", ""),
                        }
                    )

        return jsonify({"progress": progress_data, "message": "User progress fetched successfully", "status": 200}), 200
    except Exception as e:
        return jsonify({"message": f"Error fetching user progress: {e}", "status": 400}), 400
