import sqlite3

DB_PATH = 'influencers.db'

def add_sentiment_column():
    """
    Connects to the SQLite database and adds the 'ai_sentiment' column to the 'posts' table
    if it doesn't already exist.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Get the list of columns from the posts table
        cursor.execute("PRAGMA table_info(posts)")
        columns = [info[1] for info in cursor.fetchall()]

        # Add 'ai_sentiment' column if it doesn't exist
        if 'ai_sentiment' not in columns:
            cursor.execute("ALTER TABLE posts ADD COLUMN ai_sentiment TEXT")
            print("Column 'ai_sentiment' added to 'posts' table.")
        else:
            print("Column 'ai_sentiment' already exists.")

        conn.commit()

    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        if conn:
            conn.close()
            print("Database connection closed.")

if __name__ == '__main__':
    add_sentiment_column()
