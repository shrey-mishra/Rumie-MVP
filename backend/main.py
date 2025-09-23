
from fastapi import FastAPI, HTTPException
import sqlite3
import os
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
import logging
import json


# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load secrets
load_dotenv()


# Initialize FastAPI
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# SQLite connection
def get_db_connection():
    try:
        conn = sqlite3.connect(os.getenv('SQLITE_DB_PATH', 'rumie.db'))
        conn.row_factory = sqlite3.Row
        logger.info("SQLite connection established")
        return conn
    except sqlite3.Error as e:
        logger.error(f"SQLite error: {e}")
        raise

# Mock Redis (in-memory dict for Day 1)
mock_redis = {}

# Mock integration data (Google Workspace: Gmail/Calendar, Notion)
mock_integrations = {
    "1": {
        "gmail": [{"subject": "Urgent: Project Update", "sender": "bob@company.com", "urgent": True}],
        "calendar": [{"title": "Team Meeting", "time": "2025-09-24 15:00", "duration": "1h"}],
        "notion": [{"task": "Finish MVP Plan", "due": "2025-09-24", "priority": "High"}]
    }
}

# Initialize DB schema
try:
    with get_db_connection() as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                mode_pref TEXT DEFAULT 'work',
                personality_trait TEXT
            )
        ''')
        conn.execute('INSERT OR IGNORE INTO users (email, mode_pref, personality_trait) VALUES (?, ?, ?)',
                    ('test@rumie.ai', 'work', 'efficient_organizer'))
        conn.commit()
        logger.info("SQLite schema initialized")
except sqlite3.Error as e:
    logger.error(f"Schema init error: {e}")
    raise

@app.get("/users/{user_id}")
async def get_user(user_id: int):
    try:
        with get_db_connection() as conn:
            user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
            if not user:
                logger.warning(f"User {user_id} not found")
                raise HTTPException(status_code=404, detail="User not found")
            user_dict = dict(user)
            mock_redis[f"user:{user_id}"] = json.dumps(user_dict)
            logger.info(f"User {user_id} fetched and cached")
            return user_dict
    except Exception as e:
        logger.error(f"Get user error: {e}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.get("/test_redis")
async def test_redis():
    try:
        mock_redis["test_key"] = "test_value"
        value = mock_redis.get("test_key")
        logger.info("Mock Redis test successful")
        return {"value": value}
    except Exception as e:
        logger.error(f"Mock Redis error: {e}")
        raise HTTPException(status_code=500, detail=f"Mock Redis error: {str(e)}")

@app.get("/mode_response/{user_id}")
async def mode_response(user_id: int):
    try:
        with get_db_connection() as conn:
            user = conn.execute('SELECT mode_pref FROM users WHERE id = ?', (user_id,)).fetchone()
            if not user:
                logger.warning(f"User {user_id} not found")
                raise HTTPException(status_code=404, detail="User not found")
            mode = user['mode_pref']
            integrations = mock_integrations.get(str(user_id), {"gmail": [], "calendar": [], "notion": []})
            gmail = integrations["gmail"]
            calendar = integrations["calendar"]
            notion = integrations["notion"]
            response = ""
            if mode == 'work':
                if gmail:
                    response += f"Urgent email from {gmail[0]['sender']} ('{gmail[0]['subject']}'). Draft a reply?"
                if calendar:
                    response += f" Your {calendar[0]['title']} is at {calendar[0]['time'][:16]}. Prep needed?"
                if notion:
                    response += f" Notion task '{notion[0]['task']}' (due {notion[0]['due'][:10]}) is {notion[0]['priority']} priority."
            else:  # relax
                if calendar:
                    response += f"Busy day with a {calendar[0]['title']} at {calendar[0]['time'][:16]}. Try a 5-min breathing exercise to stay calm?"
                if gmail:
                    response += f" That email from {gmail[0]['sender']} can wait—let’s focus on your well-being."
                if notion:
                    response += f" Your Notion task '{notion[0]['task']}' is due {notion[0]['due'][:10]}. We’ll tackle it calmly."
                if not response:
                    response = "All clear—time to relax!"

                # Manually enhanced response for mindfulness
                enhanced_response = "Feeling a little overwhelmed? Let's take a moment to breathe. Find a comfortable position, close your eyes if you like, and just focus on your breath for a few minutes. Inhale deeply, exhale slowly. Everything else can wait."

                # Combine the original response with the mindfulness suggestion
                if response:
                     response = f"{response.strip()} {enhanced_response}"
                else:
                     response = enhanced_response


            if not response:
                response = "No tasks or emails to worry about—let’s plan your day!" if mode == 'work' else "All clear—time to relax!"


            logger.info(f"Mode response for user {user_id}: {mode}")
            return {"user_id": user_id, "mode": mode, "response": response.strip()}
    except Exception as e:
        logger.error(f"Mode response error: {e}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.get("/chat/context/{user_id}")
async def get_chat_context(user_id: int):
    try:
        context = mock_redis.get(f"chat:{user_id}")
        if not context:
            logger.warning(f"Chat context for user {user_id} not found")
            return {"chat_history": []}
        logger.info(f"Chat context for user {user_id} fetched")
        return {"chat_history": json.loads(context)}
    except Exception as e:
        logger.error(f"Get chat context error: {e}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.post("/chat/context/{user_id}")
async def set_chat_context(user_id: int, chat_history: list):
    try:
        mock_redis[f"chat:{user_id}"] = json.dumps(chat_history)
        logger.info(f"Chat context for user {user_id} updated")
        return {"status": "updated"}
    except Exception as e:
        logger.error(f"Set chat context error: {e}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
