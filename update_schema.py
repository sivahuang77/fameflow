
import sqlite3

DB_PATH = 'influencers.db'

def add_telegram_id_column():
    """
    Adds a 'telegram_id' column to the 'influencers' table if it doesn't already exist.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Use PRAGMA to check if the column already exists
        cursor.execute("PRAGMA table_info(influencers)")
        columns = [info[1] for info in cursor.fetchall()]
        
        if 'telegram_id' not in columns:
            print("Column 'telegram_id' not found. Adding it to the table...")
            cursor.execute("ALTER TABLE influencers ADD COLUMN telegram_id INTEGER")
            # Create a unique index on the new column separately
            cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_telegram_id ON influencers (telegram_id)")
            conn.commit()
            print("Successfully added the 'telegram_id' column and created a unique index on it.")
        else:
            print("Column 'telegram_id' already exists.")
            
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        conn.close()

if __name__ == '__main__':
    add_telegram_id_column()
