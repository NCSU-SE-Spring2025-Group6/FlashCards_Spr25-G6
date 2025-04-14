from flask import Blueprint, request, jsonify
import logging
import re
import requests
from dotenv import load_dotenv
import os
import json


try:
    from .. import firebase
except ImportError:
    from __init__ import firebase

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Create a blueprint for text upload
upload_bp = Blueprint("upload_bp", __name__)
db = firebase.database()

# GEMINI_API_KEY = "YOUR_GEMINI_API_KEY"  # Replace with your actual API key
# Load environment variables from .env file 
load_dotenv()
# Retrieve the Gemini API key from the environment variables
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

@upload_bp.route("/api/upload", methods=["POST"])
def upload_text():
    """Handle plain text uploads and process text to create a new deck."""
    # Parse the JSON payload
    data = request.get_json()
    if not data:
        return jsonify({"message": "No JSON payload provided"}), 400

    # Extract text and other fields from the payload
    text = data.get("text")
    local_id = data.get("localId")
    visibility = data.get("visibility")
    description = data.get("description")
    title = data.get("title")

    if not text:
        return jsonify({"message": "No text provided"}), 400

    if not local_id:
        return jsonify({"message": "No localId provided"}), 400

    logging.info(f"Processing text for localId: {local_id}")
    logging.info(f"Visibility: {visibility}, Description: {description}, Title: {title}")

    # Validate the text length
    if len(text) > 1000000:
        return jsonify({"message": "Text exceeds maximum length of 10000 characters"}), 400
    if len(text) < 10:
        return jsonify({"message": "Text is too short, minimum length is 10 characters"}), 400

    # Process the text (e.g., generate flashcards)
    try:
        logging.info("Generating flashcards from text.")
        flashcards = process_text_with_gemini(text)  # Use the Gemini API for text processing
        logging.info(f"Generated flashcards: {flashcards}")

        # Convert the generated flashcards to JSON
        deck = {
            "deck": {
                "title": title,
                "description": description,
                "visibility": visibility,
            }
        }
        flashcard_json = {**deck, **flashcards}
        logging.info(f"Flashcard JSON: {flashcard_json}")
        return create_new_deck(local_id, flashcard_json)
    except Exception as e:
        logging.error(f"Error processing text: {str(e)}")
        return jsonify({"message": f"Error processing text: {str(e)}"}), 500


def process_text_with_gemini(text):
    """Process text and generate flashcards using the Gemini API."""
    # Clean the text by removing non-alphanumeric characters (except spaces and basic punctuation)
    cleaned_text = re.sub(r"[^a-zA-Z0-9\s.,!?']", " ", text)

    # Normalize whitespace by stripping leading/trailing spaces and replacing multiple spaces with a single space
    cleaned_text = re.sub(r"\s+", " ", cleaned_text).strip()

    # Define the prompt for generating flashcards
    prompt = (
        f"Create flashcards in the following (dictionary) format:\n"
        f"{{\"cards\": [{{\"front\": \"Question 1\", \"back\": \"Answer 1\", \"hint\": \"Hint 1\"}}, {{\"front\": \"Question 2\", \"back\": \"Answer 2\", \"hint\": \"Hint 2\"}}]}}"
        f"\n\nUse the following text to generate the flashcards:\n\n"
        f"\"{cleaned_text}\"\n\n"
        f"Strictly follow the the format and ensure the flashcards are relevant to the text."
    )

    # Define the payload for the Gemini API
    payload = {
        "contents": [
            {
                "parts": [{"text": prompt}]
            }
        ]
    }

    # Make a POST request to the Gemini API
    headers = {
        "Content-Type": "application/json"
    }
    try:
        response = requests.post(
            f"{GEMINI_API_URL}?key={GEMINI_API_KEY}",
            headers=headers,
            json=payload
        )
        # Check if the request was successful
        if response.status_code != 200:
            raise Exception(f"Gemini API error: {response.status_code} - {response.text}")

        # Parse the response from the Gemini API
        flashcards = response.json()
        try:
            flashcards_json =  json.loads(flashcards['candidates'][0]["content"]['parts'][0]['text'][7:-4])
            return flashcards_json
        except json.JSONDecodeError as e:
            logging.error(f"JSON Decode Error: {str(e)}")
            raise
    except Exception as e:
        logging.error(f"Error communicating with Gemini API: {str(e)}")
        raise


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


