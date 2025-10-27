
import sqlite3
import json

def setup_database():
    """
    Connects to the SQLite database, creates the 'influencers' table if it doesn't exist,
    and adds some initial example data.
    """
    db_path = 'influencers.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # SQL statement to create the influencers table
    create_table_query = """
    CREATE TABLE IF NOT EXISTS influencers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        social_media TEXT,
        contact_info TEXT,
        tone_prompt TEXT,
        recent_report TEXT,
        business_history TEXT,
        personality_analysis TEXT,
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """

    cursor.execute(create_table_query)
    print("Table 'influencers' created or already exists.")

    # --- Optional: Add some example data for demonstration ---
    
    # Check if the table is empty before inserting data
    cursor.execute("SELECT COUNT(*) FROM influencers")
    count = cursor.fetchone()[0]

    if count == 0:
        print("Table is empty. Inserting example data...")
        
        # Example data for two influencers
        example_influencers = [
            {
                "name": "小花 (Flora)",
                "social_media": json.dumps({
                    "instagram": "https://instagram.com/flora_test",
                    "youtube": "https://youtube.com/florachannel"
                }),
                "contact_info": "flora.h@example.com",
                "tone_prompt": "使用活潑、開朗、充滿正能量的語氣，多用可愛的 emoji (像是 ✨🌸💖)，像好閨蜜一樣關心對方。",
                "recent_report": "最近一週發了 3 篇 Instagram 貼文，主題是秋季穿搭，粉絲反應熱烈。",
                "business_history": "2024 Q3: 美妝品牌A合作案. 2024 Q4: 服飾品牌B合作案.",
                "personality_analysis": "個性外向、樂於分享生活、對時尚和美妝有高度敏銳度。",
                "notes": "貓奴，有兩隻貓。不喜歡吃香菜。"
            },
            {
                "name": "阿文 (A-Wen)",
                "social_media": json.dumps({
                    "tiktok": "https://tiktok.com/@awen_tech",
                    "twitter": "https://twitter.com/awen_tech"
                }),
                "contact_info": "awen.tech@example.com",
                "tone_prompt": "使用專業、簡潔、有條理的語氣。可以適度使用科技相關的梗或術語，展現專業度。",
                "recent_report": "上週發布了一支關於最新手機評測的 TikTok 影片，觀看數超過 50 萬。",
                "business_history": "2024 Q4: 3C 品牌C評測合作案。",
                "personality_analysis": "邏輯清晰、對科技產品有深入研究、喜歡挖掘產品細節。與粉絲互動直接、有問必答。",
                "notes": "是個咖啡愛好者。"
            }
        ]

        for influencer in example_influencers:
            cursor.execute("""
                INSERT INTO influencers (
                    name, social_media, contact_info, tone_prompt, recent_report, 
                    business_history, personality_analysis, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                influencer["name"],
                influencer["social_media"],
                influencer["contact_info"],
                influencer["tone_prompt"],
                influencer["recent_report"],
                influencer["business_history"],
                influencer["personality_analysis"],
                influencer["notes"]
            ))
        print(f"Inserted {len(example_influencers)} example records.")
    else:
        print("Database already contains data. Skipping example data insertion.")


    # Commit the changes and close the connection
    conn.commit()
    conn.close()
    print(f"Database '{db_path}' is set up and ready.")

if __name__ == '__main__':
    setup_database()
