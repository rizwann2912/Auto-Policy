import sqlite3
import os
from datetime import datetime

DATABASE_NAME = "policies.db"
DB_PATH = os.path.join(os.path.dirname(__file__), os.pardir, DATABASE_NAME)

def init_db():
    """Initializes the SQLite database and creates the policies table if it doesn't exist."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS policies (
            website_name TEXT PRIMARY KEY,
            policy_text TEXT NOT NULL,
            date_saved TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()
    print(f"Database initialized at {DB_PATH}")

def save_policy_to_db(website_name: str, policy_text: str):
    """Saves a privacy policy to the database. Updates if website_name exists, inserts otherwise."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    date_saved = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        cursor.execute(
            "INSERT INTO policies (website_name, policy_text, date_saved) VALUES (?, ?, ?)",
            (website_name, policy_text, date_saved)
        )
    except sqlite3.IntegrityError:
        # If website_name already exists, update the existing record
        cursor.execute(
            "UPDATE policies SET policy_text = ?, date_saved = ? WHERE website_name = ?",
            (policy_text, date_saved, website_name)
        )
    conn.commit()
    conn.close()
    print(f"Policy for {website_name} saved/updated in database.")

def load_policies_from_db():
    """Loads all saved policies from the database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT website_name, policy_text, date_saved FROM policies")
    policies = cursor.fetchall()
    conn.close()
    
    # Convert list of tuples to dictionary for easier use in app.py
    loaded_policies = {}
    for website_name, policy_text, date_saved in policies:
        loaded_policies[website_name] = {
            'text': policy_text,
            'date': date_saved
        }
    print("Policies loaded from database.")
    return loaded_policies

if __name__ == "__main__":
    init_db()
    # Example usage:
    # save_policy_to_db("Test Website", "This is a test policy.")
    # policies = load_policies_from_db()
    # print(policies) 