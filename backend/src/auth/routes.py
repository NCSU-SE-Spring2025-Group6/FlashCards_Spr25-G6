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

"""import dependancies"""

from flask import Blueprint, jsonify
from flask import current_app as app
from flask_cors import cross_origin
from flask import request
import requests
import json

try:
    from .. import firebase
except ImportError:
    from __init__ import firebase

auth_bp = Blueprint("auth_bp", __name__)

auth = firebase.auth()


@auth_bp.route("/", methods=["GET"])
@cross_origin(supports_credentials=True)
def index():
    return "Hello"


@auth_bp.route("/signup", methods=["POST"])
@cross_origin(supports_credentials=True)
def signup():
    """this method is used to create new users and register them in firebase

    POST /signup [email, password]
    payload: { email: “string”, password: “string” }
    """
    try:
        data = request.get_json()
        email = data["email"]
        password = data["password"]

        user = auth.create_user_with_email_and_password(email, password)
        """if the registration process is successful, this message is displayed"""
        return jsonify(user=user, message="Registered Successfully", status=201), 201
    except requests.exceptions.HTTPError as e:
        error_body = json.loads(e.args[1])
        error_code = error_body.get('error', {}).get('message', 'UNKNOWN_ERROR')

        error_messages = {
            "EMAIL_EXISTS": "That email address is already registered to an account.",
            "INVALID_EMAIL": "Check that your email address is correctly formatted.",
            "WEAK_PASSWORD : Password should be at least 6 characters": "Your password must be at least 6 characters long.",
        }

        message = error_messages.get(error_code, "Registration failed. Please try again.")

        return jsonify(message=message, firebase_error=error_code, status=400), 400
    except Exception as _:
        """if the registration process is not successful, this message is displayed"""
        return jsonify(message="Registration failed. Please try again.", status=400), 400


@auth_bp.route("/login", methods=["POST"])
@cross_origin(supports_credentials=True)
def login():
    """this method is used by registered users to sign in to their account

    POST /login [email, password]
    payload: { email: “string”, password: “string” }
    """
    try:
        data = request.get_json()
        email = data["email"]
        password = data["password"]

        user = auth.sign_in_with_email_and_password(email, password)
        """if login is successful, this message is displayed"""
        return jsonify(user=user, message="Login Successful", status=200), 200
    except Exception as _:
        """if login is not successful, this message is displayed"""
        return jsonify(message="Login Failed", status=400), 400


if __name__ == "__main__":
    app.debug = True
    app.run()
