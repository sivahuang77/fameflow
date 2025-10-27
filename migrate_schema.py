import sqlite3
import json

DB_PATH = 'influencers.db'

def migrate_schema():
    """
    Performs a schema migration for the influencers table:
    1. Creates a new influencers_new table with the desired schema.
    2. Migrates data from the old influencers table to influencers_new.
    3. Parses the old social_media JSON blob and moves it to the new social_accounts table.
    4. Drops the old influencers table and renames influencers_new to influencers.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Access columns by name
    cursor = conn.cursor()

    try:
        print("Starting schema migration...")

        # 1. Create the new influencers_new table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS influencers_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            real_name TEXT,
            phone TEXT,
            email TEXT,
            compensation_preference TEXT,
            personal_preference TEXT,
            notes TEXT,
            tone_prompt TEXT,
            personality_analysis TEXT,
            business_history TEXT,
            recent_report TEXT
        )
        """)
        print("Temporary 'influencers_new' table created.")

        # 2. Fetch all records from the old influencers table
        cursor.execute("SELECT * FROM influencers")
        old_influencers = cursor.fetchall()
        print(f"Found {len(old_influencers)} records to migrate.")

        # 3. Iterate and migrate each record
        for old_influencer in old_influencers:
            old_influencer_dict = dict(old_influencer)
            influencer_id = old_influencer_dict['id']
            
            # --- Migrate social media data to social_accounts table ---
            try:
                social_media_json = old_influencer_dict.get('social_media')
                if social_media_json:
                    social_media = json.loads(social_media_json)
                    for platform, url in social_media.items():
                        if url:
                            # Simple parsing for display name from URL if possible
                            display_name = old_influencer_dict.get('name', '').split('(')[0].strip()
                            account_id = url.split('/')[-1] or url.split('/')[-2]
                            cursor.execute("""
                                INSERT INTO social_accounts (influencer_id, platform_name, url, display_name, account_id)
                                VALUES (?, ?, ?, ?, ?)
                            """, (influencer_id, platform, url, display_name, account_id))
            except (json.JSONDecodeError, TypeError) as e:
                print(f"Could not parse social_media JSON for influencer {influencer_id}: {e}")

            # --- Prepare data for the new influencers_new table ---
            real_name = old_influencer_dict.get('name', '')
            if '(' in real_name and ')' in real_name:
                parts = real_name.split('(')
                real_name = parts[1].replace(')', '').strip()
            
            new_data = {
                "id": influencer_id,
                "real_name": real_name,
                "phone": None, # No clear source in old schema
                "email": old_influencer_dict.get('contact_info'),
                "compensation_preference": None, # New field
                "personal_preference": None, # New field
                "notes": old_influencer_dict.get('notes'),
                "tone_prompt": old_influencer_dict.get('tone_prompt'),
                "personality_analysis": old_influencer_dict.get('personality_analysis'),
                "business_history": old_influencer_dict.get('business_history'),
                "recent_report": old_influencer_dict.get('recent_report')
            }

            cursor.execute("""
                INSERT INTO influencers_new (id, real_name, phone, email, compensation_preference, personal_preference, notes, tone_prompt, personality_analysis, business_history, recent_report)
                VALUES (:id, :real_name, :phone, :email, :compensation_preference, :personal_preference, :notes, :tone_prompt, :personality_analysis, :business_history, :recent_report)
            """, new_data)

        print("Data migration to temporary tables complete.")

        # 4. Drop the old table and rename the new one
        cursor.execute("PRAGMA foreign_keys=off;")
        cursor.execute("DROP TABLE influencers;")
        cursor.execute("ALTER TABLE influencers_new RENAME TO influencers;")
        cursor.execute("PRAGMA foreign_keys=on;")
        print("Old 'influencers' table replaced with new schema.")

        conn.commit()
        print("Schema migration committed successfully!")

    except Exception as e:
        print(f"An error occurred during migration: {e}")
        conn.rollback()
        print("Migration rolled back.")
    finally:
        conn.close()
        print("Database connection closed.")

if __name__ == '__main__':
    migrate_schema()
