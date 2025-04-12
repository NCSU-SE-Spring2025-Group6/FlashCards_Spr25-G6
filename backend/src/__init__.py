import pyrebase

config = {
    # Firebase configuration
    # Replace with your actual Firebase project configuration
    # "apiKey": 
    # "authDomain": 
    # "databaseURL": 
    # "projectId": 
    # "storageBucket": 
    # "messagingSenderId":
    # "appId": 
    # "measurementId":
    "apiKey": "AIzaSyA7v6-wPN87g-0SGXVMCV3oanOIkfpGvdU",
    "authDomain": "flashcards-2ccd7.firebaseapp.com",
    "databaseURL": "https://flashcards-2ccd7-default-rtdb.firebaseio.com",
    "projectId": "flashcards-2ccd7",
    "storageBucket": "flashcards-2ccd7.firebasestorage.app",
    "messagingSenderId": "642654331718",
    "appId": "1:642654331718:web:734e147c53aeec66fffb47",
    "measurementId": "G-X9XFJP58PX"
}
firebase = pyrebase.initialize_app(config)
