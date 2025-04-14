from flask import Blueprint, request, jsonify
import os
from werkzeug.utils import secure_filename
from flask import jsonify
# from chatgpt_model import process_text  # Import your locally running ChatGPT model logic

# try:
#     from .. import firebase
# except ImportError:
#     from __init__ import firebase

# Define constants
UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"txt"}

# Ensure the upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Helper function to check allowed file types
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

# Create a blueprint for file upload
upload_bp = Blueprint("upload_bp", __name__)
# db = firebase.database()

@upload_bp.route("/api/upload", methods=["POST"])
def upload_file():
    """Handle file uploads and process text to create a new deck."""
    return jsonify({"message": "Upload endpoint"}), 200

    if "file" not in request.files:
        return jsonify({"message": "No file part"}), 400


    file = request.files["file"]
    local_id = request.form.get("localId")

    

    if file.filename == "":
        return jsonify({"message": "No selected file"}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)

        # Process the file using the ChatGPT model
        try:
            with open(filepath, "r") as f:
                text = f.read()
            flashcards = process_text(text)  # Process text using ChatGPT model
            flashcard_json = generate_flashcard_json(flashcards)  # Convert to JSON
            create_new_deck(local_id, flashcard_json)  # Create a new deck
            return jsonify({"message": "Deck created successfully!"}), 201
        except Exception as e:
            return jsonify({"message": f"Error processing file: {str(e)}"}), 500

    return jsonify({"message": "Invalid file type"}), 400

def generate_flashcard_json(flashcards):
    """Convert processed flashcards into JSON format."""
    return [{"question": card["question"], "answer": card["answer"]} for card in flashcards]

def create_new_deck(local_id, flashcard_json):
    """Save the flashcard JSON as a new deck in the database."""
    deck = {
        "localId": local_id,
        "title": "Generated Deck",
        "description": "Deck created from uploaded text file",
        "visibility": "public",
        "cards": flashcard_json,
    }
    # Save to database (e.g., Firebase, MongoDB, etc.)
    # db.child("decks").push(deck)