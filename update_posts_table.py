import sqlite3

DB_PATH = 'influencers.db'

def add_ai_columns_to_posts():
    """
    Connects to the SQLite database and adds AI-related columns to the 'posts' table
    if they don't already exist.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Get the list of columns from the posts table
        cursor.execute("PRAGMA table_info(posts)")
        columns = [info[1] for info in cursor.fetchall()]

        # Add 'image_text_ai' column if it doesn't exist
        if 'image_text_ai' not in columns:
            cursor.execute("ALTER TABLE posts ADD COLUMN image_text_ai TEXT")
            print("Column 'image_text_ai' added to 'posts' table.")
        else:
            print("Column 'image_text_ai' already exists.")

        # Add 'image_description_ai' column if it doesn't exist
        if 'image_description_ai' not in columns:
            cursor.execute("ALTER TABLE posts ADD COLUMN image_description_ai TEXT")
            print("Column 'image_description_ai' added to 'posts' table.")
        else:
            print("Column 'image_description_ai' already exists.")

        conn.commit()

    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        if conn:
            conn.close()
            print("Database connection closed.")

if __name__ == '__main__':
    add_ai_columns_to_posts()
