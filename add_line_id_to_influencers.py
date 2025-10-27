import sqlite3

def add_line_id_column():
    """Connects to the database and adds the 'line_id' column to the 'influencers' table if it doesn't exist."""
    db_path = 'influencers.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Check if the line_id column already exists
        cursor.execute("PRAGMA table_info(influencers);")
        columns = [column[1] for column in cursor.fetchall()]
        if 'line_id' not in columns:
            # SQL statement to add the line_id column
            alter_table_query = "ALTER TABLE influencers ADD COLUMN line_id TEXT;"
            cursor.execute(alter_table_query)
            print("Column 'line_id' added to 'influencers' table.")
        else:
            print("Column 'line_id' already exists in 'influencers' table.")

        conn.commit()
    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
    finally:
        conn.close()
        print(f"Database '{db_path}' updated.")

if __name__ == '__main__':
    add_line_id_column()