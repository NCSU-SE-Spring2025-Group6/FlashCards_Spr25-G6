"""routes.py is a file in the leaderboard folder that has all the functions defined that manipulate the leaderboard."""

from flask import Blueprint, jsonify  # type: ignore
from flask_cors import cross_origin  # type: ignore
# from __init__ import firebase

try:
    from .. import firebase
except ImportError:
    from __init__ import firebase

leaderboard_bp = Blueprint("leaderboard_bp", __name__)

db = firebase.database()


@leaderboard_bp.route("/leaderboard/global", methods=["GET"])
@cross_origin(supports_credentials=True)
def get_global_leaderboard():
    """Fetch a global leaderboard across all decks."""
    try:
        leaderboard_entries = db.child("leaderboard").get()
        global_scores = {}

        if leaderboard_entries.val():
            for deck in leaderboard_entries.each():
                deck_data = deck.val()
                for user_id, data in deck_data.items():
                    if user_id not in global_scores:
                        global_scores[user_id] = {
                            "userEmail": data.get("userEmail"),
                            "total_correct": 0,
                            "total_incorrect": 0,
                        }
                    global_scores[user_id]["total_correct"] += data.get("correct", 0)
                    global_scores[user_id]["total_incorrect"] += data.get("incorrect", 0)

        leaderboard = sorted(global_scores.values(), key=lambda x: x["total_correct"], reverse=True)

        return jsonify(
            {"leaderboard": leaderboard, "message": "Global leaderboard fetched successfully", "status": 200}
        ), 200
    except Exception as e:
        return jsonify({"message": f"Error fetching global leaderboard: {e}", "status": 400}), 400
