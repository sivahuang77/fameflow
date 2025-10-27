import sqlite3

DB_PATH = 'influencers.db'

def create_posts_table():
    """
    Connects to the SQLite database and creates the 'posts' table
    if it doesn't already exist.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # SQL statement to create the posts table
        # This table will store all scraped posts from influencers.
        create_table_query = """
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            influencer_id INTEGER NOT NULL,
            post_url TEXT,
            post_content TEXT,
            image_urls TEXT, -- Storing as a JSON array or comma-separated string
            scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (influencer_id) REFERENCES influencers (id)
        );
        """

        cursor.execute(create_table_query)
        print("'posts' table created or already exists.")

        # Optional: Add an index for faster lookups by influencer
        create_index_query = "CREATE INDEX IF NOT EXISTS idx_influencer_id ON posts (influencer_id);"
        cursor.execute(create_index_query)
        print("Index on 'influencer_id' created or already exists.")

        conn.commit()

    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        if conn:
            conn.close()
            print("Database connection closed.")

if __name__ == '__main__':
    create_posts_table()
