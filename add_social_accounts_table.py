import sqlite3

DB_PATH = 'influencers.db'

def create_social_accounts_table():
    """
    Connects to the SQLite database and creates the 'social_accounts' table
    if it doesn't already exist.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        create_table_query = """
        CREATE TABLE IF NOT EXISTS social_accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            influencer_id INTEGER NOT NULL,
            platform_name TEXT NOT NULL,
            account_id TEXT, -- User handle or ID
            display_name TEXT, -- The name shown on the platform
            url TEXT, -- Full URL to the profile
            FOREIGN KEY (influencer_id) REFERENCES influencers (id) ON DELETE CASCADE
        );
        """

        cursor.execute(create_table_query)
        print("'social_accounts' table created or already exists.")

        # Add an index for faster lookups by influencer
        create_index_query = "CREATE INDEX IF NOT EXISTS idx_sa_influencer_id ON social_accounts (influencer_id);"
        cursor.execute(create_index_query)
        print("Index on 'influencer_id' in 'social_accounts' table created or already exists.")

        conn.commit()

    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        if conn:
            conn.close()
            print("Database connection closed.")

if __name__ == '__main__':
    create_social_accounts_table()
