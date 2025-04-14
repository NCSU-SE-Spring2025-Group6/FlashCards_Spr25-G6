from flask import Blueprint, request, jsonify
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Create a blueprint for text upload
upload_bp = Blueprint("upload_bp", __name__)

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


    if not text:
        # logging.warning("No text provided in the request.")
        return jsonify({"message": "No text provided"}), 400

    if not local_id:
        # logging.warning("No localId provided in the request.")
        return jsonify({"message": "No localId provided"}), 400

    # logging.info(f"Processing text for localId: {local_id}")
    logging.info(f"Text content: {text}")

    # Process the text (e.g., generate flashcards)
    try:
        flashcards = process_text(text)  # Replace with your text processing logic
        flashcard_json = generate_flashcard_json(flashcards)  # Convert to JSON
        create_new_deck(local_id, flashcard_json)  # Save the deck
        return jsonify({"message": "Deck created successfully!"}), 201
    except Exception as e:
        # logging.error(f"Error processing text: {str(e)}")
        return jsonify({"message": f"Error processing text: {str(e)}"}), 500

def process_text(text):
    """Mock function to process text and generate flashcards."""
    # Replace this with your actual text processing logic
    return [
        {"question": "What is AI?", "answer": "Artificial Intelligence"},
        {"question": "What is Flask?", "answer": "A Python web framework"},
    ]

def generate_flashcard_json(flashcards):
    """Convert processed flashcards into JSON format."""
    return [{"question": card["question"], "answer": card["answer"]} for card in flashcards]

def create_new_deck(local_id, flashcard_json):
    """Save the flashcard JSON as a new deck in the database."""
    deck = {
        "localId": local_id,
        "title": "Generated Deck",
        "description": "Deck created from uploaded text",
        "visibility": "public",
        "cards": flashcard_json,
    }
    # Save to database (e.g., Firebase, MongoDB, etc.)
    # Example: db.child("decks").push(deck)
    # logging.info(f"Deck created for localId: {local_id}")