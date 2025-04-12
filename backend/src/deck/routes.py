# MIT License
#
# Copyright (c) 2022 John Damilola, Leo Hsiang, Swarangi Gaurkar, Kritika Javali, Aaron Dias Barreto
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""routes.py is a file in deck folder that has all the functions defined that manipulate the deck. All CRUD functions are defined here."""

from flask import Blueprint, jsonify, request
from flask_cors import cross_origin
from datetime import datetime, timedelta, timezone
import json
import base64

try:
    from .. import firebase
except ImportError:
    from __init__ import firebase


deck_bp = Blueprint("deck_bp", __name__)
db = firebase.database()


@deck_bp.route("/deck/<id>", methods=["GET"])
@cross_origin(supports_credentials=True)
def getdeck(id):
    """This method fetches a specific deck by its ID."""
    try:
        deck = db.child("deck").child(id).get()
        return jsonify(deck=deck.val(), message="Fetched deck successfully", status=200), 200
    except Exception as e:
        return jsonify(decks=[], message=f"An error occurred: {e}", status=400), 400


@deck_bp.route("/deck/<id>/stats", methods=["GET"])
@cross_origin(supports_credentials=True)
def get_deck_stats(id):
    """This method calculates stats of a specific deck by its ID."""
    try:
        leaderboard_entries = db.child("leaderboard").child(id).get()
        total_users = 0
        total_correct = 0
        total_incorrect = 0
        if leaderboard_entries.val():
            for entry in leaderboard_entries.each():
                data = entry.val()
                total_correct += data.get("correct", 0)
                total_incorrect += data.get("incorrect", 0)
                total_users += 1
        avg_correct = total_correct / total_users if total_users > 0 else 0
        avg_incorrect = total_incorrect / total_users if total_users > 0 else 0
        return jsonify(
            {
                "average_correct": avg_correct,
                "average_incorrect": avg_incorrect,
                "total_users": total_users,
                "message": "Deck performance statistics fetched successfully",
                "status": 200,
            }
        ), 200
    except Exception as e:
        return jsonify({"message": f"Error fetching deck stats: {e}", "status": 400}), 400


@deck_bp.route("/deck/all", methods=["GET"])
@cross_origin(supports_credentials=True)
def getdecks():
    """Fetch all decks. Shows private decks for authenticated users and public decks for non-authenticated users."""
    args = request.args
    localId = args.get("localId")

    try:
        decks = []
        if localId:
            user_decks = db.child("deck").order_by_child("userId").equal_to(localId).get()
            for deck in user_decks.each():
                obj = deck.val()
                obj["id"] = deck.key()
                cards = db.child("card").order_by_child("deckId").equal_to(deck.key()).get()
                obj["cards_count"] = len(cards.val()) if cards.val() else 0
                decks.append(obj)
        else:
            alldecks = db.child("deck").order_by_child("visibility").equal_to("public").get()
            for deck in alldecks.each():
                obj = deck.val()
                obj["id"] = deck.key()
                cards = db.child("card").order_by_child("deckId").equal_to(deck.key()).get()
                obj["cards_count"] = len(cards.val()) if cards.val() else 0
                decks.append(obj)

        return jsonify(decks=decks, message="Fetching decks successfully", status=200), 200
    except Exception as e:
        return jsonify(decks=[], message=f"An error occurred {e}", status=400), 400


@deck_bp.route("/deck/create", methods=["POST"])
@cross_origin(supports_credentials=True)
def create():
    """Create a new deck."""
    try:
        data = request.get_json()
        localId = data["localId"]
        title = data["title"]
        description = data["description"]
        visibility = data["visibility"]

        db.child("deck").push(
            {
                "userId": localId,
                "title": title,
                "description": description,
                "visibility": visibility,
                "cards_count": 0,
                "lastOpened": None,
            }
        )

        return jsonify(message="Create Deck Successful", status=201), 201
    except Exception as e:
        return jsonify(message=f"Create Deck Failed {e}", status=400), 400


@deck_bp.route("/deck/update/<id>", methods=["PATCH"])
@cross_origin(supports_credentials=True)
def update(id):
    """Update an existing deck."""
    try:
        data = request.get_json()
        localId = data["localId"]
        title = data["title"]
        description = data["description"]
        visibility = data["visibility"]

        db.child("deck").child(id).update(
            {"userId": localId, "title": title, "description": description, "visibility": visibility}
        )

        return jsonify(message="Update Deck Successful", status=201), 201
    except Exception as e:
        return jsonify(message=f"Update Deck Failed {e}", status=400), 400


@deck_bp.route("/deck/delete/<id>", methods=["DELETE"])
@cross_origin(supports_credentials=True)
def delete(id):
    """Delete a deck."""
    try:
        db.child("deck").child(id).remove()
        return jsonify(message="Delete Deck Successful", status=200), 200
    except Exception as e:
        return jsonify(message=f"Delete Deck Failed {e}", status=400), 400


@deck_bp.route("/deck/updateLastOpened/<id>", methods=["PATCH"])
@cross_origin(supports_credentials=True)
def update_last_opened(id):
    """Update the lastOpened timestamp when a deck is opened."""
    try:
        current_time = datetime.utcnow().isoformat()
        db.child("deck").child(id).update({"lastOpened": current_time})
        return jsonify(message="Deck lastOpened updated successfully", status=200), 200
    except Exception as e:
        return jsonify(message=f"Failed to update lastOpened: {e}", status=400), 400


@deck_bp.route("/deck/<deckId>/leaderboard", methods=["GET"])
@cross_origin(supports_credentials=True)
def get_leaderboard(deckId):
    """This endpoint fetches the leaderboard data for a specific deck."""
    try:
        # Fetch leaderboard data for the given deck
        leaderboard_entries = db.child("leaderboard").child(deckId).get()
        leaderboard = []
        for entry in leaderboard_entries.each():
            data = entry.val()
            leaderboard.append(
                {
                    "userEmail": data.get("userEmail"),
                    "correct": data.get("correct", 0),
                    "incorrect": data.get("incorrect", 0),
                    "lastAttempt": data.get("lastAttempt"),
                }
            )

        # Sort leaderboard by score (correct answers) then by last attempt (descending)
        leaderboard.sort(key=lambda x: (x["correct"], x["lastAttempt"]), reverse=True)

        return jsonify(
            {"leaderboard": leaderboard, "message": "Leaderboard data fetched successfully", "status": 200}
        ), 200
    except Exception as e:
        return jsonify({"leaderboard": [], "message": f"An error occurred: {e}", "status": 400}), 400


@deck_bp.route("/deck/<deck_id>/update-leaderboard", methods=["POST"])
@cross_origin(supports_credentials=True)
def update_leaderboard(deck_id):
    try:
        data = request.get_json()
        # Extract values from the request body
        user_id = data.get("userId")  # Get userId from request body
        user_email = data.get("userEmail")  # Keep for logging or notification
        correct = data.get("correct")
        incorrect = data.get("incorrect")

        if not user_id:
            return jsonify({"message": "User ID is required"}), 400  # Validate userId presence

        # Use user_id from request body to update the leaderboard
        leaderboard_ref = db.child("leaderboard").child(deck_id).child(user_id)
        leaderboard_ref.update(
            {
                "userEmail": user_email,
                "correct": correct,
                "incorrect": incorrect,
                "lastAttempt": datetime.now().isoformat(),
            }
        )

        return jsonify({"message": "Leaderboard updated successfully"}), 200

    except Exception as e:
        return jsonify({"message": "Failed to update leaderboard", "error": str(e)}), 500


@deck_bp.route("/deck/<deckId>/user-score/<userId>", methods=["GET"])
@cross_origin(supports_credentials=True)
def get_user_score(deckId, userId):
    """This endpoint fetches the user's score for a specific deck. If the user doesn't exist, return zero for all score values."""
    try:
        # Fetch the user's leaderboard entry for the specified deck
        leaderboard_entry = db.child("leaderboard").child(deckId).child(userId).get()

        if leaderboard_entry.val() is not None:  # Check if the entry has data
            data = leaderboard_entry.val()  # Get the value of the entry
            score_data = {
                "correct": data.get("correct", 0),
                "incorrect": data.get("incorrect", 0),
            }
            return jsonify({"score": score_data, "message": "User score fetched successfully", "status": 200}), 200
        else:
            # Return zero for all score values if no entry exists
            return jsonify(
                {
                    "score": {"correct": 0, "incorrect": 0},
                    "message": "No score found for the user, returning zeros.",
                    "status": 200,  # Not Found status, as the user has no scores yet
                }
            ), 200

    except Exception as e:
        return jsonify({"message": f"An error occurred: {e}", "status": 400}), 400


@deck_bp.route("/deck/<user_id>/record-answer", methods=["POST"])
@cross_origin(supports_credentials=True)
def record_answer(user_id):
    """Update card progress using SM-2 algorithm with frontend-provided ease"""
    try:
        data = request.get_json()
        front = data.get("front")
        back = data.get("back")
        hint = data.get("hint")
        quality = data.get("quality")

        if None in (user_id, front, back, hint, quality):
            return jsonify({"message": "All fields must be provided"}), 400

        # Find card by front/back/hint
        query_result = db.child("card").order_by_child("front").equal_to(front).get()
        card_id = next(
            (
                card.key()
                for card in query_result.each()
                if card.val().get("back") == back and card.val().get("hint") == hint
            ),
            None,
        )
        print("user id", user_id)
        print("card_id", card_id)

        if not card_id:
            return jsonify({"message": "Card not found"}), 404

        progress_ref = db.child("user_card_progress").child(user_id).child(card_id)

        progress = progress_ref.get().val() or {
            "interval": 1,
            "repetitions": 0,
            "ease_factor": 2.5,
            "next_review": datetime.now(timezone.utc).isoformat(),
        }

        # Extract current values
        current_interval = progress["interval"]
        current_repetitions = progress["repetitions"]
        current_ease = progress["ease_factor"]

        # https://github.com/thyagoluciano/sm2
        if quality < 3:  # Incorrect or needs retry
            new_interval = 1
            new_repetitions = 0
            new_ease = max(1.3, current_ease - 0.2)
            next_review_delta = timedelta(days=1)
        else:  # Correct answer
            new_repetitions = current_repetitions + 1

            # Calculate interval
            if current_repetitions == 0:
                new_interval = 1
            elif current_repetitions == 1:
                new_interval = 6
            else:
                new_interval = round(current_interval * current_ease, 2)

            # Calculate new ease factor (SM-2 formula)
            quality_bonus = 0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02)
            new_ease = max(1.3, current_ease + quality_bonus)
            next_review_delta = timedelta(days=new_interval)

        progress_update = {
            "interval": new_interval,
            "repetitions": new_repetitions,
            "ease_factor": new_ease,
            "next_review": (datetime.now(timezone.utc) + next_review_delta).isoformat(),
            "last_review": datetime.now(timezone.utc).isoformat(),
        }

        db.child("user_card_progress").child(user_id).child(card_id).update(progress_update)

        return jsonify(
            {
                "message": "Progress updated",
                "nextReview": progress_update["next_review"],
                "newInterval": new_interval,
                "newEase": new_ease,
            }
        ), 200

    except Exception as e:
        return jsonify({"message": f"Error: {str(e)}"}), 500


@deck_bp.route("/deck/<deck_id>/practice-cards/<user_id>", methods=["GET"])
@cross_origin(supports_credentials=True)
def get_practice_cards(deck_id, user_id):
    """Get cards due for review using spaced repetition"""
    try:
        deck_cards = db.child("card").order_by_child("deckId").equal_to(deck_id).get()
        card_ids = [card.key() for card in deck_cards.each()]

        progress_ref = db.child("user_card_progress").child(user_id).get()
        all_progress = progress_ref.val() or {}

        practice_cards = []
        now = datetime.now(timezone.utc)  # Use UTC consistently

        for card_id in card_ids:
            card_data = db.child("card").child(card_id).get().val()
            progress = all_progress.get(card_id)

            if not progress:
                practice_cards.append({**card_data, "progress": None, "due_date": datetime.min.isoformat()})
                continue

            try:
                next_review = datetime.fromisoformat(progress["next_review"])
                if next_review <= now:
                    practice_cards.append({**card_data, "progress": progress, "due_date": progress["next_review"]})
            except (KeyError, ValueError):
                practice_cards.append({**card_data, "progress": progress, "due_date": datetime.min.isoformat()})

        # Sort priority:
        # 1. New cards (denoted by no progress)
        # 2. Oldest due dates
        # 3. Lowest ease factors
        practice_cards.sort(key=lambda x: (x["due_date"], x["progress"]["ease_factor"] if x["progress"] else 0))

        result_cards = []
        for card in practice_cards[:20]:
            card.pop("due_date", None)
            result_cards.append(card)

        return jsonify({"cards": result_cards, "message": "Spaced repetition cards retrieved"}), 200

    except Exception as e:
        return jsonify({"message": f"Error: {str(e)}"}), 500


@deck_bp.route("/deck/<deck_id>/practice-schedule/<user_id>", methods=["GET"])
@cross_origin(supports_credentials=True)
def practice_schedule(deck_id, user_id):
    """Get the practice schedule for future iterations of cards"""
    try:
        deck_cards = db.child("card").order_by_child("deckId").equal_to(deck_id).get()
        card_ids = [card.key() for card in deck_cards.each()]

        progress_ref = db.child("user_card_progress").child(user_id).get()
        all_progress = progress_ref.val() or {}

        practice_cards = []
        now = datetime.now(timezone.utc)  # Use UTC consistently

        for card_id in card_ids:
            card_data = db.child("card").child(card_id).get().val()
            progress = all_progress.get(card_id)

            if not progress:
                practice_cards.append({**card_data, "progress": None, "due_date": datetime.min.isoformat()})
                continue

            try:
                next_review = datetime.fromisoformat(progress["next_review"])
                if next_review <= now:
                    practice_cards.append({**card_data, "progress": progress, "due_date": progress["next_review"]})
            except (KeyError, ValueError):
                practice_cards.append({**card_data, "progress": progress, "due_date": datetime.min.isoformat()})

        # Sort priority:
        # 1. New cards (denoted by no progress)
        # 2. Oldest due dates
        # 3. Lowest ease factors
        practice_cards.sort(key=lambda x: (x["due_date"], x["progress"]["ease_factor"] if x["progress"] else 0))

        result_cards = []
        for card in practice_cards[:20]:
            card.pop("due_date", None)
            result_cards.append(card)

        return jsonify({"cards": result_cards, "message": "Spaced repetition cards retrieved"}), 200

    except Exception as e:
        return jsonify({"message": f"Error: {str(e)}"}), 500


@deck_bp.route("/deck/<id>/export", methods=["GET"])
@cross_origin(supports_credentials=True)
def export_deck(id):
    """Export a deck and its cards to a JSON file"""
    try:
        # Get the deck
        deck = db.child("deck").child(id).get().val()
        if not deck:
            return jsonify(message="Deck not found", status=404), 404

        # Get all cards for this deck
        cards = db.child("card").order_by_child("deckId").equal_to(id).get()

        # Prepare export data
        export_data = {
            "deck": {"title": deck["title"], "description": deck["description"], "visibility": deck["visibility"]},
            "cards": [],
        }

        # Add cards if they exist
        if cards.val():
            for card in cards.each():
                card_data = card.val()
                export_data["cards"].append(
                    {
                        "front": card_data.get("front", ""),
                        "back": card_data.get("back", ""),
                        "hint": card_data.get("hint", ""),
                    }
                )

        # Convert to JSON string and encode
        json_str = json.dumps(export_data, indent=2)
        encoded_data = base64.b64encode(json_str.encode()).decode()

        return jsonify(
            {
                "data": encoded_data,
                "filename": f"{deck['title'].replace(' ', '_')}.json",
                "message": "Deck exported successfully",
                "status": 200,
            }
        ), 200

    except Exception as e:
        return jsonify(message=f"Export failed: {e}", status=400), 400


@deck_bp.route("/deck/import", methods=["POST"])
@cross_origin(supports_credentials=True)
def import_deck():
    """Import a deck and its cards from a JSON file"""
    try:
        data = request.get_json()
        file_content = data.get("fileContent")  # Base64 encoded file content
        user_id = data.get("userId")

        if not file_content or not user_id:
            return jsonify(message="Missing required data", status=400), 400

        # Decode the file content
        try:
            decoded_content = base64.b64decode(file_content).decode()
            import_data = json.loads(decoded_content)
        except Exception as _:
            return jsonify(message="Invalid file format", status=400), 400

        # Validate the structure
        if "deck" not in import_data or "cards" not in import_data:
            return jsonify(message="Invalid file structure", status=400), 400

        # Create the deck
        deck_data = import_data["deck"]
        deck_data["userId"] = user_id
        deck_data["cards_count"] = len(import_data["cards"])
        deck_data["lastOpened"] = None

        new_deck = db.child("deck").push(deck_data)
        deck_id = new_deck["name"]  # Get the new deck ID

        # Create the cards
        for card in import_data["cards"]:
            card["deckId"] = deck_id
            card["userId"] = user_id
            db.child("card").push(card)

        return jsonify({"deckId": deck_id, "message": "Deck imported successfully", "status": 201}), 201

    except Exception as e:
        return jsonify(message=f"Import failed: {e}", status=400), 400


@deck_bp.route("/deck/<deck_id>/card-statistics/<user_id>", methods=["GET"])
@cross_origin(supports_credentials=True)
def card_statistics(deck_id, user_id):
    """Get comprehensive statistics about cards in a deck for a specific user"""
    try:
        # Get all cards for this deck
        deck_cards = db.child("card").order_by_child("deckId").equal_to(deck_id).get()
        if not deck_cards.val():
            return jsonify({"message": "No cards found for this deck", "statistics": {}}), 200

        # Fetch progress data for all cards
        progress_ref = db.child("user_card_progress").child(user_id).get()
        all_progress = progress_ref.val() or {}

        # Initialize statistics containers
        now = datetime.now(timezone.utc)
        today = now.replace(hour=0, minute=0, second=0, microsecond=0)

        statistics = {
            "total_cards": 0,
            "reviewed_cards": 0,
            "unreviewed_cards": 0,
            "review_schedule": {"today": 0, "tomorrow": 0, "this_week": 0, "next_week": 0, "later": 0},
            "confidence_levels": {
                "low": 0,  # Quality 0-1
                "medium": 0,  # Quality 2-3
                "high": 0,  # Quality 4-5
            },
            "performance": {"correct_count": 0, "total_reviews": 0, "accuracy_rate": 0},
            "cards_data": [],
        }

        # Process each card in the deck
        for card in deck_cards.each():
            card_id = card.key()
            card_data = card.val()
            statistics["total_cards"] += 1

            # Get card progress
            progress = all_progress.get(card_id)

            # Card data to return
            card_info = {
                "id": card_id,
                "front": card_data.get("front", ""),
                "back": card_data.get("back", ""),
                "next_review": None,
                "confidence": 0,
                "correct_count": 0,
                "reviewed": False,
            }

            # No progress data means the card hasn't been reviewed yet
            if not progress:
                statistics["unreviewed_cards"] += 1
                statistics["cards_data"].append(card_info)
                continue

            # Card has been reviewed at least once
            statistics["reviewed_cards"] += 1
            card_info["reviewed"] = True

            # Extract confidence level if available
            confidence = progress.get("confidence", 0)
            card_info["confidence"] = confidence

            if confidence <= 1:
                statistics["confidence_levels"]["low"] += 1
            elif confidence <= 3:
                statistics["confidence_levels"]["medium"] += 1
            else:
                statistics["confidence_levels"]["high"] += 1

            # Get correct answer count
            correct_count = progress.get("correct", 0)
            card_info["correct_count"] = correct_count
            statistics["performance"]["correct_count"] += correct_count

            # Count total reviews based on repetitions if available
            total_reviews = progress.get("repetitions", 0)
            if progress.get("last_review"):  # If there was at least one review
                total_reviews = max(1, total_reviews)
            statistics["performance"]["total_reviews"] += total_reviews

            # Process next review date
            try:
                next_review_str = progress.get("next_review")
                if next_review_str:
                    next_review = datetime.fromisoformat(next_review_str)
                    card_info["next_review"] = next_review_str

                    # Calculate which schedule bucket this falls into
                    delta_days = (next_review - today).days

                    if delta_days < 0:  # Overdue, count as today
                        statistics["review_schedule"]["today"] += 1
                    elif delta_days == 0:  # Due today
                        statistics["review_schedule"]["today"] += 1
                    elif delta_days == 1:  # Due tomorrow
                        statistics["review_schedule"]["tomorrow"] += 1
                    elif delta_days < 7:  # Due this week
                        statistics["review_schedule"]["this_week"] += 1
                    elif delta_days < 14:  # Due next week
                        statistics["review_schedule"]["next_week"] += 1
                    else:  # Due later
                        statistics["review_schedule"]["later"] += 1
            except (ValueError, TypeError):
                # If date parsing fails, consider it as not reviewed
                pass

            # Add card data to the list
            statistics["cards_data"].append(card_info)

        # Calculate overall accuracy rate
        if statistics["performance"]["total_reviews"] > 0:
            statistics["performance"]["accuracy_rate"] = round(
                (statistics["performance"]["correct_count"] / statistics["performance"]["total_reviews"]) * 100, 2
            )

        return jsonify(
            {"statistics": statistics, "message": "Card statistics retrieved successfully", "status": 200}
        ), 200

    except Exception as e:
        return jsonify({"message": f"Error retrieving card statistics: {str(e)}", "status": 400}), 400
