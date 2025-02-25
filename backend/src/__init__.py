import pyrebase

config = {
    "apiKey": "AIzaSyDxfVzHaoppp5RM_MwxWJjkZUAA-3iqKhM",
    "authDomain": "flashcardsv-2.firebaseapp.com",
    "databaseURL": "https://flashcardsv-2-default-rtdb.firebaseio.com/",
    "projectId": "flashcardsv-2",
    "storageBucket": "flashcardsv-2.appspot.com",
    "messagingSenderId": "202182151892",
    "appId": "1:202182151892:web:c72d2f4960a321381f7541",
    "measurementId": "G-GFCSP4EZEZ",
}
firebase = pyrebase.initialize_app(config)
