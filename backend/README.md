# Backend Installation Guide

This application uses Firebase as a database, meaning while the application can be ran locally, a connection to the internet is still required for functionality. Heroku can be used if the user wishes to deploy the website online.

1. Make a copy of the `__init__.sample` file and name the new file `__init__.py`

2. Set up [Firebase](https://firebase.google.com/):
   - Go to the website
   - Login/register an account
   - Click on `Add Project`
     - Optional: Add Google Analytics to the project
   - Press `Create Project`
   - Under the _Get Started by Adding Firebase to your App_, click on `Web App`
   - Name the web app as you like
   - Set up the Realtime Database
     - On the left-side menu, select `All Products`
     - Select `Realtime Database` and follow the prompts to enable the database for the project
       - When prompted, select `Start in Locked Mode`
     - Set up rules for the database
       - Navigate to the `Rules` tab
       - Replace the existing ruleset with the below ruleset
       - Press `Publish`
         - Ruleset:
         
            ```
            {
                "rules": {
                    "folder_deck": {
                        ".read": true,
                        ".write": true,
                        ".indexOn": ["folderId"]
                    },
                    "add-deck": {
                        ".read": true,
                        ".write": true
                    },
                    "addToFolder": {
                        ".read": true,
                        ".write": true
                    },
                    "folder": {
                        ".read": true,
                        ".write": true,
                        ".indexOn": ["userId"]
                    },
                    "folders": {
                        ".read": true,
                        ".write": true
                    },
                    "deck": {
                        ".indexOn": ["id", "userId", "visibility"],
                        ".read": true,
                        ".write": true
                    },
                    "card": {
                        ".indexOn": ["deckId", "front"],
                        ".read": true,
                        ".write": true
                    },
                    "leaderboard": {
                        ".read": true,
                        ".write": true,
                        ".indexOn": ["deckId", "correct", "lastAttempt"]
                    },
                    "group": {
                        ".read": true,
                        ".write": true
                    },
                    "sharing": {
                        ".read": true,
                        ".write": true
                    },
                    "quizAttempts": {
                        ".read": true,
                        ".write": true,
                        ".indexOn": ["deckId", "userId", "attemptId"]
                    },
                    "streaks": {
                        ".read": true,
                        ".write": true
                    },
                    "messages": {
                        ".read": true,
                        ".write": true
                    },
                    "notifications": {
                        ".read": true,
                        ".write": true
                    },
                    "user_card_progress": {
                        ".read": true,
                        ".write": true
                    },
                    "user_gamification": {
                        ".read": true,
                        ".write": true,
                        ".indexOn": ["userId", "xp"]
                    }
                }
            }
            ```

     - From the left-side menu, select `Project Settings`, copy the `apiKey`, `authDomain`, `databaseURL`, `projectId`, `storageBucket`, `messagingSenderId`, `appId`, and `measurementId` values and paste them into a `.env` file at project root, like this:
  
    ```
    FIREBASE_API_KEY=AIzaSyDxfVzHaoppp5RM_MwxWJjkZUAA-3iqKhM
    FIREBASE_AUTH_DOMAIN=flashwcardsv-2.firebaseapp.com
    FIREBASE_DATABASE_URL=https://flashcardsv-2-default-rtdb.firebaseio.com/
    FIREBASE_PROJECT_ID=flashcardsv-1
    FIREBASE_STORAGE_BUCKET=flashcardsv-2.appspot.com
    FIREBASE_MESSAGING_SENDER_ID=202982151892
    FIREBASE_APP_ID=1:202182151892:web:c72d2f4960a321381f7541
    FIREBASE_MEASUREMENT_ID=G-GFCSP4EZEZ
    ```
     - Enable email/password sign-in
       - Return to the Firebase console
       - Click on `Authentication` in the left-side bar
       - Click on `Sign-in Method`
       - Enable `Email/Password Sign In`
      
3. Start the backend API server
   - Navigate to `FlashCards/backend/src`
   - Run the following command:
     - ```bash
       python api.py
       ```
    
    To serve the backend in production mode with high-performance WSGI server gunicorn, run:
    - ```bash
      # in project root
      make serve-backend
      ```

## Heroku Deployment Steps (optional)
1. ```heroku login```

2. ```heroku create flashcards-server-api```

3. ```heroku create --buildpack https://github.com/heroku/heroku-buildpack-python.git```

4. ```heroku ps:scale web=1```

5. ```git remote add heroku https://git.heroku.com/flashcards-server-api.git```

6. ```git subtree push --prefix backend heroku local_branch:main```


