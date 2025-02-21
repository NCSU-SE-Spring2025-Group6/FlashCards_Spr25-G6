import pyrebase

config = {
  'apiKey': "AIzaSyActLE7dqVJxJ0lzhpxvupmWAYHy45AmKU",
  'authDomain': "flashcards-4917d.firebaseapp.com",
  'databaseURL': "https://flashcards-4917d-default-rtdb.firebaseio.com",
  'projectId': "flashcards-4917d",
  'storageBucket': "flashcards-4917d.firebasestorage.app",
  'messagingSenderId': "472315504098",
  'appId': "1:472315504098:web:5effa3e1458ddd716945bb",
  'measurementId': "G-GFCSP4EZEZ",
}

firebase = pyrebase.initialize_app(config)
