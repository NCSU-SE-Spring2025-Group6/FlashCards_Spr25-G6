#
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

from flask import Flask
from flask_cors import CORS


def create_app():
    """Create Flask application."""
    app = Flask(__name__, instance_relative_config=False)

    with app.app_context():
        try:
            from .auth.routes import auth_bp
            from .deck.routes import deck_bp
            from .cards.routes import card_bp
            from .folders.routes import folder_bp
            from .user.routes import user_bp
            from .leaderboard.routes import leaderboard_bp
            from .gamification.routes import gamification_bp
            from .upload.routes import upload_bp
        except ImportError:
            from auth.routes import auth_bp
            from deck.routes import deck_bp
            from cards.routes import card_bp
            from folders.routes import folder_bp
            from user.routes import user_bp
            from leaderboard.routes import leaderboard_bp
            from gamification.routes import gamification_bp
            from upload.routes import upload_bp

        # Register Blueprints
        app.register_blueprint(auth_bp)
        app.register_blueprint(deck_bp)
        app.register_blueprint(card_bp)
        app.register_blueprint(folder_bp)
        app.register_blueprint(user_bp)
        app.register_blueprint(leaderboard_bp)
        app.register_blueprint(gamification_bp)
        app.register_blueprint(upload_bp)

    return app


app = create_app()
app.config["CORS_HEADERS"] = "Content-Type"

# Configure CORS to allow everything from anywhere
cors_config = {
    "origins": "*",
    "methods": ["GET", "HEAD", "POST", "OPTIONS", "PUT", "PATCH", "DELETE"],
    "allow_headers": "*",
    "expose_headers": "*",
    "supports_credentials": True,
    "max_age": 86400,  # 24 hours
}

CORS(app, resources={r"/*": cors_config})

app.debug = True

if __name__ == "__main__":
    app.config.from_mapping({"DEBUG": True})

    app.run(port=5000, debug=True)
