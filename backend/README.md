# Backend Installation Guide

1. Clone the repository using the following command:

```bash
git clone https://github.com/CSC510-510/FlashCards
```

2. Create a virtual environment using the following command:

```bash
conda create -n flashcards python=3.12.2
conda activate flashcards
```

3. Install the backend dependencies, navigate to `FlashCards/backend` and run the following command:
```bash
pip install -r requirements.txt
```

4. Make a copy of the `__init__.sample` file and name the new file `__init__.py`

5. Set up [Firebase](https://firebase.google.com/):
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
                        ".read": true,  // Adjust if needed
                        ".write": true, // Adjust if needed
                        ".indexOn": ["deckId", "correct", "lastAttempt"]  // Suitable for sorting
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
                        ".indexOn" : ["deckId", "userId", "attemptId"]
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
                    }
                }
            }
            ```

     - From the left-side menu, select `Project Settings`, copy the `apiKey`, `authDomain`, `databaseURL`, `projectId`, `storageBucket`, `messagingSenderId`, `appId`, and `measurementId` values and paste them into the corresponding fields in `__init__.py`
     - Enable email/password sign-in
       - Return to the Firebase console
       - Click on `Authentication` in the left-side bar
       - Click on `Sign-in Method`
       - Enable `Email/Password Sign In`
      
6. Start the backend API server
   - Navigate to `FlashCards/backend/src`
   - Run the following command:
     - ```bash
       python api.py
       ```

## Heroku Deployment Steps (optional)
1. ```heroku login```

2. ```heroku create flashcards-server-api```

3. ```heroku create --buildpack https://github.com/heroku/heroku-buildpack-python.git```

4. ```heroku ps:scale web=1```

5. ```git remote add heroku https://git.heroku.com/flashcards-server-api.git```

6. ```git subtree push --prefix backend heroku local_branch:main```


