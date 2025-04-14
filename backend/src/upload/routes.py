from flask import Blueprint, request, jsonify
import logging

try:
    from .. import firebase
except ImportError:
    from __init__ import firebase


# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Create a blueprint for text upload
upload_bp = Blueprint("upload_bp", __name__)
db = firebase.database()

@upload_bp.route("/api/upload", methods=["POST"])
def upload_text():
    """Handle plain text uploads and process text to create a new deck."""
    # logging.info("Received a text upload request.")

    # Parse the JSON payload
    data = request.get_json()
    if not data:
        # logging.warning("No JSON payload in the request.")
        return jsonify({"message": "No JSON payload provided"}), 400

    # Extract text and localId from the payload
    text = data.get("text")
    local_id = data.get("localId")
    visibility = data.get("visibility")
    description = data.get("description")
    title = data.get("title")


    if not text:
        # logging.warning("No text provided in the request.")
        return jsonify({"message": "No text provided"}), 400

    if not local_id:
        # logging.warning("No localId provided in the request.")
        return jsonify({"message": "No localId provided"}), 400

    # logging.info(f"Processing text for localId: {local_id}")
    logging.info(f"Text content: {text}")
    logging.info(f"localId: {local_id}")
    logging.info(f"visivility: {visibility}")
    logging.info(f"Description: {description}")
    logging.info(f"Deck Title: {title}")

    # Validate the text length
    if len(text) > 10000:
        # logging.warning("Text exceeds maximum length.")
        return jsonify({"message": "Text exceeds maximum length of 10000 characters"}), 400
    if len(text) < 10:
        # logging.warning("Text is too short.")
        return jsonify({"message": "Text is too short, minimum length is 10 characters"}), 400

    # Process the text (e.g., generate flashcards)
    try:
        flashcards = process_text(text)  # Replace with your text processing logic
        deck = { "deck": {
            "title": title,
            "description": description,
            "visibility": visibility}
        }
        flashcard_json = {**deck, **flashcards}
        return create_new_deck(local_id, flashcard_json)
    except Exception as e:
        # logging.error(f"Error processing text: {str(e)}")
        return jsonify({"message": f"Error processing text: {str(e)}"}), 500

def process_text(text):
    """Mock function to process text and generate flashcards."""
    # Replace this with your actual text processing logic
    return {"cards": [{
        "front": "What is AI?", 
        "back": "Artificial Intelligence",
        "hint": "A field of computer science"
        },
        {
        "front": "What is Python?",
        "back": "A programming language",
        "hint": "Used for web development"
        },
        {
        "front": "What is Flask?",
        "back": "A web framework for Python",
        "hint": "Used for building web applications"
        }],
    }

def create_new_deck(user_id, flashcard_json):
    """Save the flashcard JSON as a new deck in the database."""

    if not flashcard_json or not user_id:
        return jsonify(message="Missing required data", status=400), 400

    # Decode the file content
    import_data = flashcard_json

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
    logging.info(f"Deck created: {flashcard_json}")
    return jsonify({"deckId": deck_id, "message": "Deck imported successfully", "status": 201}), 201


    